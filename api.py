"""
FastAPI bridge between the React frontend and the Python optimizer backend.
All optimization logic stays in src/optimizer.py — this file only translates
HTTP requests into Python calls and serializes the results.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── backend imports ──────────────────────────────────────────────────────────
from src.data_generator import generate_shipments_dataset
from src.optimizer import (
    RouteOptimizer,
    WeightsConfig,
    HardConstraints,
    OptimizationResult as PyOptResult,
    run_sensitivity_analysis,
)
from src.explanations import LLMExplainer, RuleBasedExplainer
from src.custom_shipment import parse_and_generate_corridor

# ── app setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="RouteWise AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── shared data (loaded once) ────────────────────────────────────────────────
_df = generate_shipments_dataset()
_optimizer = RouteOptimizer()
_explainer = RuleBasedExplainer()

# ── pydantic models ──────────────────────────────────────────────────────────

class WeightsIn(BaseModel):
    cost: float = Field(0.40, ge=0, le=1)
    time: float = Field(0.30, ge=0, le=1)
    risk: float = Field(0.30, ge=0, le=1)

class ConstraintsIn(BaseModel):
    max_budget: Optional[float] = None
    max_days: Optional[float] = None
    max_risk: Optional[float] = None

class OptimizeRequest(BaseModel):
    shipment_id: str
    weights: WeightsIn = WeightsIn()
    constraints: ConstraintsIn = ConstraintsIn()

class CustomOptimizeRequest(BaseModel):
    prompt: str

class AskRequest(BaseModel):
    question: str
    shipment_id: Optional[str] = None
    weights: WeightsIn = WeightsIn()

# ── helpers ──────────────────────────────────────────────────────────────────

def _normalize_weights(w: WeightsIn) -> WeightsConfig:
    """Normalize so weights sum to 1.0, then create WeightsConfig."""
    total = w.cost + w.time + w.risk or 1.0
    return WeightsConfig(cost=w.cost / total, time=w.time / total, risk=w.risk / total)


def _result_to_dict(result: PyOptResult, explanation: str = "") -> Dict[str, Any]:
    """Convert OptimizationResult (dataclasses) to a JSON-serializable dict."""

    def route_dict(r) -> Dict[str, Any]:
        return {
            "route_id": str(r.route_id),
            "hubs": str(r.intermediate_hubs),
            "mode": str(r.transport_mode),
            "cost": float(r.cost_usd),
            "transit_days": float(r.transit_time_days),
            "delay_probability": float(r.delay_probability),
            "composite_risk": float(r.composite_risk),
            "score": float(r.total_score),
            "feasible": bool(r.is_feasible),
            "pareto_dominant": bool(not r.is_pareto_dominated),
            "carrier": str(r.carrier),
            "route_name": str(r.route_name),
            "invalidation_reasons": r.invalidation_reasons,
        }

    rec = result.recommended_route
    all_routes = result.all_routes

    feasible_count = sum(1 for r in all_routes if r.is_feasible)

    infeasible_reason: Optional[str] = None
    if result.all_infeasible and rec:
        infeasible_reason = "; ".join(rec.invalidation_reasons) if rec.invalidation_reasons else "All routes violate hard constraints"

    return {
        "recommended": route_dict(rec) if rec is not None else None,
        "all_routes": [route_dict(r) for r in all_routes],
        "feasible_count": feasible_count,
        "total_routes": len(all_routes),
        "infeasible_reason": infeasible_reason,
        "explanation": explanation,
    }

# ── endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/shipments")
def list_shipments():
    """Return unique shipment IDs with their origin/destination."""
    df = _df.copy()
    seen: Dict[str, Any] = {}
    for _, row in df.iterrows():
        sid = str(row["shipment_id"])
        if sid not in seen:
            seen[sid] = {
                "shipment_id": sid,
                "origin": str(row.get("origin", "—")),
                "destination": str(row.get("destination", "—")),
            }
    return {"shipments": list(seen.values())}


@app.post("/api/optimize")
def optimize(req: OptimizeRequest):
    """Run the MCDA optimizer for a given shipment and weights."""
    try:
        weights = _normalize_weights(req.weights)
        constraints = HardConstraints(
            max_budget_usd=req.constraints.max_budget,
            max_transit_days=req.constraints.max_days,
            max_acceptable_risk=req.constraints.max_risk,
        )

        shipment_df = _df[_df["shipment_id"] == req.shipment_id].copy()
        if shipment_df.empty:
            raise HTTPException(status_code=404, detail=f"Shipment {req.shipment_id!r} not found")

        result = RouteOptimizer.evaluate_shipment_routes(shipment_df, weights, constraints)
        explanation = _explainer.generate_explanation(result)

        return _result_to_dict(result, explanation)

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/custom-optimize")
def custom_optimize(req: CustomOptimizeRequest):
    """Parse a natural-language prompt and run the optimizer."""
    try:
        custom_df, weights, constraints, _msg = parse_and_generate_corridor(req.prompt, _df)
        weights.validate()

        result = RouteOptimizer.evaluate_shipment_routes(custom_df, weights, constraints)
        explanation = _explainer.generate_explanation(result)

        payload = _result_to_dict(result, explanation)
        # Extract origin/destination if available
        if not custom_df.empty:
            payload["parsed_origin"] = str(custom_df["origin"].iloc[0]) if "origin" in custom_df.columns else ""
            payload["parsed_destination"] = str(custom_df["destination"].iloc[0]) if "destination" in custom_df.columns else ""
        payload["corridor_note"] = _msg
        return payload

    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/scenarios/{shipment_id}")
def get_scenarios(shipment_id: str):
    """Run sensitivity analysis across 4 weight profiles."""
    try:
        shipment_df = _df[_df["shipment_id"] == shipment_id].copy()
        if shipment_df.empty:
            raise HTTPException(status_code=404, detail=f"Shipment {shipment_id!r} not found")

        sa_df = run_sensitivity_analysis(shipment_df)

        # Rename columns for camelCase-friendly frontend consumption
        scenarios = []
        for _, row in sa_df.iterrows():
            scenarios.append({
                "profile": str(row.get("Profile", "")),
                "recommended_route": str(row.get("Recommended Route", "")),
                "route_id": str(row.get("Route ID", "")),
                "carrier": str(row.get("Carrier", "")),
                "cost": float(row.get("Cost ($)", 0)),
                "transit_days": float(row.get("Transit Time (days)", 0)),
                "composite_risk": float(row.get("Composite Risk", 0)),
                "score": float(row.get("Score", 0)),
                "feasible": True,  # sensitivity analysis only returns feasible winners
            })
        return {"scenarios": scenarios}

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/ask")
def ask(req: AskRequest):
    """Answer a natural-language question grounded in optimizer results."""
    try:
        weights = _normalize_weights(req.weights)
        constraints = HardConstraints()

        if req.shipment_id:
            shipment_df = _df[_df["shipment_id"] == req.shipment_id].copy()
            if shipment_df.empty:
                raise HTTPException(status_code=404, detail="Shipment not found")
        else:
            first_id = _df["shipment_id"].iloc[0]
            shipment_df = _df[_df["shipment_id"] == first_id].copy()

        result = RouteOptimizer.evaluate_shipment_routes(shipment_df, weights, constraints)

        try:
            explainer = LLMExplainer(api_key=None)
            answer = explainer._offline_grounded_answer(req.question, result)
        except Exception:
            answer = _explainer.generate_explanation(result)

        return {"answer": answer}

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/health")
def health():
    return {"status": "ok", "shipments_loaded": int(len(_df["shipment_id"].unique()))}
