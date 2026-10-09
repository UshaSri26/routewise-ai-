"""
Optimization Engine for RouteWise AI.
Implements deterministic multi-criteria decision analysis (MCDA), hard constraint enforcement,
Pareto dominance checks, and sensitivity analysis for global shipment routing.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class WeightsConfig:
    """Weight configuration for multi-criteria scoring. Must sum to 1.0."""
    cost: float = 0.40
    time: float = 0.30
    risk: float = 0.30

    def validate(self) -> None:
        total = self.cost + self.time + self.risk
        if not np.isclose(total, 1.0, atol=1e-3):
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")
        if any(w < 0 for w in [self.cost, self.time, self.risk]):
            raise ValueError("Weights cannot be negative.")


@dataclass
class HardConstraints:
    """Hard business and operational constraints."""
    max_budget_usd: Optional[float] = None
    max_transit_days: Optional[float] = None
    max_acceptable_risk: Optional[float] = None  # Scale 0 to 1.0


@dataclass
class EvaluatedRoute:
    """Structured evaluation outcome for a single route."""
    route_id: str
    route_name: str
    carrier: str
    transport_mode: str
    intermediate_hubs: str
    cost_usd: float
    transit_time_days: float
    delay_probability: float
    congestion_risk: float
    geopolitical_risk: float
    composite_risk: float
    expected_delay_days: float
    expected_landed_cost: float
    
    # Normalized scores [0, 1] (0 = best, 1 = worst)
    norm_cost: float = 0.0
    norm_time: float = 0.0
    norm_risk: float = 0.0
    
    # Final composite score
    total_score: float = 0.0
    
    # Feasibility and dominance
    is_feasible: bool = True
    invalidation_reasons: List[str] = field(default_factory=list)
    is_pareto_dominated: bool = False
    dominated_by: List[str] = field(default_factory=list)
    rank: int = 0


@dataclass
class OptimizationResult:
    """Complete decision outcome for a shipment."""
    shipment_id: str
    origin: str
    destination: str
    cargo_type: str
    urgency: str
    weights: WeightsConfig
    constraints: HardConstraints
    all_routes: List[EvaluatedRoute]
    recommended_route: Optional[EvaluatedRoute]
    all_infeasible: bool = False
    runner_up_route: Optional[EvaluatedRoute] = None
    tradeoff_summary: Dict[str, Any] = field(default_factory=dict)


class RouteOptimizer:
    """
    Deterministic multi-objective route optimization engine.
    Applies hard constraints, computes composite risk, normalizes metrics,
    checks Pareto dominance, and ranks routes.
    """

    EPSILON = 1e-6
    COST_PER_DELAY_DAY_DEFAULT = 150.0  # Assumed demurrage / inventory holding cost per day

    # Sub-weights for composite risk calculation (sum to 1.0)
    RISK_WEIGHT_DELAY = 0.40
    RISK_WEIGHT_CONGESTION = 0.30
    RISK_WEIGHT_GEOPOLITICAL = 0.30

    @classmethod
    def calculate_composite_risk(cls, delay_prob: float, congestion: float, geopol: float) -> float:
        """
        Calculates a normalized composite risk index between 0.0 and 1.0.
        delay_prob is [0, 1], congestion is [0, 100], geopol is [0, 100].
        """
        c_norm = congestion / 100.0
        g_norm = geopol / 100.0
        return round(
            cls.RISK_WEIGHT_DELAY * delay_prob +
            cls.RISK_WEIGHT_CONGESTION * c_norm +
            cls.RISK_WEIGHT_GEOPOLITICAL * g_norm,
            4
        )

    @classmethod
    def check_pareto_dominance(cls, routes: List[EvaluatedRoute]) -> None:
        """
        Identifies routes strictly dominated across Cost, Transit Time, and Composite Risk.
        Route A dominates Route B if A is <= B on all metrics and strictly < on at least one.
        """
        n = len(routes)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                a = routes[i]
                b = routes[j]
                
                # Minimization problem: lower is better
                c_better = a.cost_usd <= b.cost_usd
                t_better = a.transit_time_days <= b.transit_time_days
                r_better = a.composite_risk <= b.composite_risk

                c_strict = a.cost_usd < b.cost_usd
                t_strict = a.transit_time_days < b.transit_time_days
                r_strict = a.composite_risk < b.composite_risk

                if c_better and t_better and r_better and (c_strict or t_strict or r_strict):
                    b.is_pareto_dominated = True
                    if a.route_id not in b.dominated_by:
                        b.dominated_by.append(a.route_id)

    @classmethod
    def evaluate_shipment_routes(
        cls,
        shipment_routes: pd.DataFrame,
        weights: WeightsConfig = WeightsConfig(),
        constraints: Optional[HardConstraints] = None,
        cost_per_delay_day: float = COST_PER_DELAY_DAY_DEFAULT
    ) -> OptimizationResult:
        """
        Evaluates and ranks all candidate routes for a given shipment.
        """
        weights.validate()
        if constraints is None:
            constraints = HardConstraints()

        if shipment_routes.empty:
            raise ValueError("No route options provided for optimization.")

        shipment_id = str(shipment_routes["shipment_id"].iloc[0])
        origin = str(shipment_routes["origin"].iloc[0])
        destination = str(shipment_routes["destination"].iloc[0])
        cargo_type = str(shipment_routes["cargo_type"].iloc[0]) if "cargo_type" in shipment_routes.columns else "General"
        urgency = str(shipment_routes["urgency"].iloc[0]) if "urgency" in shipment_routes.columns else "Medium"

        evaluated_list: List[EvaluatedRoute] = []

        # Step 1: Pre-compute base metrics and hard constraints
        for _, row in shipment_routes.iterrows():
            cost = float(row["cost_usd"])
            days = float(row["transit_time_days"])
            delay_p = float(row["delay_probability"])
            congestion = float(row["congestion_risk"])
            geopol = float(row["geopolitical_risk"])

            comp_risk = cls.calculate_composite_risk(delay_p, congestion, geopol)
            
            # Expected delay days = transit_days * delay_prob * factor (e.g. 0.25 of total duration)
            exp_delay_days = round(days * delay_p * 0.25, 2)
            exp_landed_cost = round(cost + (exp_delay_days * cost_per_delay_day), 2)

            invalidation: List[str] = []
            if constraints.max_budget_usd is not None and cost > constraints.max_budget_usd:
                invalidation.append(f"Exceeds max budget (${cost:,.2f} > ${constraints.max_budget_usd:,.2f})")
            
            if constraints.max_transit_days is not None and days > constraints.max_transit_days:
                invalidation.append(f"Exceeds max transit time ({days:.1f}d > {constraints.max_transit_days:.1f}d)")

            if constraints.max_acceptable_risk is not None and comp_risk > constraints.max_acceptable_risk:
                invalidation.append(f"Exceeds max risk threshold ({comp_risk:.2f} > {constraints.max_acceptable_risk:.2f})")

            is_feasible = len(invalidation) == 0

            er = EvaluatedRoute(
                route_id=str(row["route_id"]),
                route_name=str(row["route_name"]),
                carrier=str(row["carrier"]),
                transport_mode=str(row["transport_mode"]),
                intermediate_hubs=str(row["intermediate_hubs"]),
                cost_usd=cost,
                transit_time_days=days,
                delay_probability=delay_p,
                congestion_risk=congestion,
                geopolitical_risk=geopol,
                composite_risk=comp_risk,
                expected_delay_days=exp_delay_days,
                expected_landed_cost=exp_landed_cost,
                is_feasible=is_feasible,
                invalidation_reasons=invalidation
            )
            evaluated_list.append(er)

        # Step 2: Pareto Dominance Check
        cls.check_pareto_dominance(evaluated_list)

        # Step 3: Relative Normalization across candidate options
        costs = [r.cost_usd for r in evaluated_list]
        times = [r.transit_time_days for r in evaluated_list]
        risks = [r.composite_risk for r in evaluated_list]

        min_c, max_c = min(costs), max(costs)
        min_t, max_t = min(times), max(times)
        min_r, max_r = min(risks), max(risks)

        for r in evaluated_list:
            # Handle edge case where all options have equal values (avoid division by 0)
            r.norm_cost = 0.0 if np.isclose(max_c, min_c) else (r.cost_usd - min_c) / (max_c - min_c + cls.EPSILON)
            r.norm_time = 0.0 if np.isclose(max_t, min_t) else (r.transit_time_days - min_t) / (max_t - min_t + cls.EPSILON)
            r.norm_risk = 0.0 if np.isclose(max_r, min_r) else (r.composite_risk - min_r) / (max_r - min_r + cls.EPSILON)

            # Composite Multi-Criteria Score (lower is better)
            score = (weights.cost * r.norm_cost) + (weights.time * r.norm_time) + (weights.risk * r.norm_risk)
            r.total_score = round(score, 4)

        # Step 4: Feasibility-aware Ranking
        feasible_routes = [r for r in evaluated_list if r.is_feasible]
        all_infeasible = len(feasible_routes) == 0

        if all_infeasible:
            # Fallback: Sort all routes by total score, but flag as infeasible
            sorted_routes = sorted(evaluated_list, key=lambda x: (len(x.invalidation_reasons), x.total_score))
        else:
            # Feasible routes ranked first by score; infeasible routes placed at bottom
            feasible_sorted = sorted(feasible_routes, key=lambda x: x.total_score)
            infeasible_sorted = sorted([r for r in evaluated_list if not r.is_feasible], key=lambda x: x.total_score)
            sorted_routes = feasible_sorted + infeasible_sorted

        for rank_idx, r in enumerate(sorted_routes, start=1):
            r.rank = rank_idx

        winner = sorted_routes[0] if sorted_routes else None
        runner_up = sorted_routes[1] if len(sorted_routes) > 1 else None

        # Step 5: Trade-off delta metrics
        tradeoff: Dict[str, Any] = {}
        if winner and runner_up:
            tradeoff = {
                "winner_id": winner.route_id,
                "winner_name": winner.route_name,
                "runner_up_id": runner_up.route_id,
                "runner_up_name": runner_up.route_name,
                "cost_delta_usd": round(winner.cost_usd - runner_up.cost_usd, 2),
                "cost_pct_diff": round(((winner.cost_usd - runner_up.cost_usd) / (runner_up.cost_usd + cls.EPSILON)) * 100, 1),
                "time_delta_days": round(winner.transit_time_days - runner_up.transit_time_days, 1),
                "risk_delta": round(winner.composite_risk - runner_up.composite_risk, 3),
                "score_delta": round(winner.total_score - runner_up.total_score, 4)
            }

        return OptimizationResult(
            shipment_id=shipment_id,
            origin=origin,
            destination=destination,
            cargo_type=cargo_type,
            urgency=urgency,
            weights=weights,
            constraints=constraints,
            all_routes=sorted_routes,
            recommended_route=winner,
            all_infeasible=all_infeasible,
            runner_up_route=runner_up,
            tradeoff_summary=tradeoff
        )


def run_sensitivity_analysis(
    shipment_routes: pd.DataFrame,
    constraints: Optional[HardConstraints] = None
) -> pd.DataFrame:
    """
    Computes route rankings across 4 standard operational profiles:
    Balanced, Cost-Focused, Time-Critical, and Risk-Averse.
    """
    profiles = {
        "Balanced (40/30/30)": WeightsConfig(cost=0.40, time=0.30, risk=0.30),
        "Cost-Focused (70/15/15)": WeightsConfig(cost=0.70, time=0.15, risk=0.15),
        "Time-Critical (15/70/15)": WeightsConfig(cost=0.15, time=0.70, risk=0.15),
        "Risk-Averse (15/15/70)": WeightsConfig(cost=0.15, time=0.15, risk=0.70)
    }

    results = []
    for profile_name, weights in profiles.items():
        res = RouteOptimizer.evaluate_shipment_routes(shipment_routes, weights=weights, constraints=constraints)
        if res.recommended_route:
            w = res.recommended_route
            results.append({
                "Profile": profile_name,
                "Recommended Route": w.route_name,
                "Route ID": w.route_id,
                "Carrier": w.carrier,
                "Cost ($)": w.cost_usd,
                "Transit Time (days)": w.transit_time_days,
                "Composite Risk": w.composite_risk,
                "Score": w.total_score
            })
    return pd.DataFrame(results)
