"""
Explainability Layer for RouteWise AI.
Generates audit-ready, human-understandable explanations for logistics planners.
Provides dual modes:
1. Grounded Rule-Based Deterministic Explainer (always works, 0 dependencies)
2. Grounded LLM Explainer (uses Gemini / OpenAI API if available, falls back safely)
"""

import os
import json
from typing import Dict, Any, Optional
from src.optimizer import OptimizationResult, EvaluatedRoute


class RuleBasedExplainer:
    """
    Deterministic explanation generator.
    Translates raw scores and trade-off deltas into a crisp logistics rationale.
    """

    @classmethod
    def generate_explanation(cls, result: OptimizationResult) -> str:
        winner = result.recommended_route
        if not winner:
            return "No route could be evaluated for this shipment."

        if result.all_infeasible:
            reasons = "; ".join(winner.invalidation_reasons)
            return (
                f"⚠️ **ATTENTION - INFEASIBLE CONSTRAINTS DETECTED**\n\n"
                f"All candidate routes violate the specified constraints. "
                f"**{winner.route_name}** (`{winner.route_id}`) is presented as the **best-effort option** "
                f"with a composite score of `{winner.total_score:.4f}`.\n\n"
                f"**Violation:** {reasons}. Consider relaxing the budget limit or transit day requirements."
            )

        runner_up = result.runner_up_route
        weights = result.weights
        tradeoff = result.tradeoff_summary

        lines = []
        lines.append(f"### 🏆 Recommendation: **{winner.route_name}** (`{winner.route_id}`)")
        lines.append(
            f"**Carrier:** {winner.carrier} | **Mode:** {winner.transport_mode} | **Via:** {winner.intermediate_hubs}"
        )
        lines.append(
            f"**Key Metrics:** ${winner.cost_usd:,.2f} | {winner.transit_time_days:.1f} days | "
            f"Delay Risk: {winner.delay_probability*100:.1f}% | Composite Risk: {winner.composite_risk:.3f}"
        )
        lines.append("")

        # Rationale based on weights
        primary_driver = "balanced multi-criteria performance"
        if weights.cost >= 0.5:
            primary_driver = "aggressive cost efficiency"
        elif weights.time >= 0.5:
            primary_driver = "rapid delivery speed"
        elif weights.risk >= 0.5:
            primary_driver = "maximum supply chain resilience and low geopolitical exposure"

        lines.append(
            f"**Strategic Rationale:** Under your **{primary_driver}** profile "
            f"(Cost: {weights.cost*100:.0f}%, Time: {weights.time*100:.0f}%, Risk: {weights.risk*100:.0f}%), "
            f"`{winner.route_name}` achieved the best composite score of **{winner.total_score:.4f}**."
        )

        # Comparison with Runner-up
        if runner_up and tradeoff:
            cost_diff = tradeoff["cost_delta_usd"]
            time_diff = tradeoff["time_delta_days"]
            risk_diff = tradeoff["risk_delta"]

            lines.append("\n**Trade-off vs. Runner-up** (`" + runner_up.route_name + "`):")
            if cost_diff < 0:
                lines.append(f"- Saves **${abs(cost_diff):,.2f}** ({abs(tradeoff['cost_pct_diff'])}%) in freight charges.")
            elif cost_diff > 0:
                lines.append(f"- Costs **${cost_diff:,.2f}** ({tradeoff['cost_pct_diff']}%) more, justified by performance gains.")
            else:
                lines.append("- Cost is identical.")

            if time_diff < 0:
                lines.append(f"- Arrives **{abs(time_diff):.1f} days faster**.")
            elif time_diff > 0:
                lines.append(f"- Incurs **{time_diff:.1f} additional transit days**.")

            if risk_diff < 0:
                lines.append(f"- Reduces composite risk index by **{abs(risk_diff):.3f}** (lower delay & congestion).")
            elif risk_diff > 0:
                lines.append(f"- Has slightly higher composite risk (+{risk_diff:.3f}).")

        # Infeasible routes excluded
        infeasible_routes = [r for r in result.all_routes if not r.is_feasible]
        if infeasible_routes:
            lines.append("\n**Excluded Alternatives (Constraint Violations):**")
            for inf in infeasible_routes:
                lines.append(f"- `{inf.route_id}` ({inf.route_name}): {', '.join(inf.invalidation_reasons)}")

        # Dominated routes
        dominated_routes = [r for r in result.all_routes if r.is_pareto_dominated]
        if dominated_routes:
            lines.append("\n**Pareto Inefficiency Alert:**")
            for dom in dominated_routes:
                dominators = ", ".join(dom.dominated_by)
                lines.append(f"- `{dom.route_id}` is strictly dominated by `{dominators}` (inferior across cost, time, and risk).")

        return "\n".join(lines)


class LLMExplainer:
    """
    LLM-powered explanation and Q&A layer.
    Grounds LLM responses strictly in numerical facts produced by RouteOptimizer.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_explanation(self, result: OptimizationResult) -> str:
        """
        Generates an executive-level memo via LLM, falling back to rule-based explainer.
        """
        # Always compute rule-based explanation as baseline / fallback
        fallback = RuleBasedExplainer.generate_explanation(result)

        if not self.is_available():
            return fallback

        try:
            # Prepare grounded prompt
            payload = self._build_grounded_context(result)
            prompt = (
                "You are RouteWise AI, a principal supply chain optimization consultant. "
                "Write a professional, concise executive decision briefing (3 short paragraphs) "
                "for a logistics operations director explaining why the winning route was selected. "
                "Rules:\n"
                "1. Cite EXACT numbers from the verified data below (costs, days, risks, scores).\n"
                "2. Explicitly explain why the runner-up lost.\n"
                "3. Mention any excluded/infeasible routes or Pareto-dominated options.\n"
                "4. Do NOT hallucinate any numbers or assumptions outside the provided context.\n\n"
                f"VERIFIED OPTIMIZATION DATA:\n{json.dumps(payload, indent=2)}"
            )

            # Try calling Google GenAI SDK if installed
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            # Safe degradation with log note
            return f"{fallback}\n\n*(Note: LLM API notice: {str(e)[:80]}. Generated via grounded deterministic explainer)*"

        return fallback

    def answer_question(self, question: str, result: OptimizationResult) -> str:
        """
        Answers a user question grounded strictly in the current optimization result.
        """
        if not self.is_available():
            winner = result.recommended_route
            return (
                f"**Offline Mode Assistant:**\n"
                f"Currently viewing Shipment `{result.shipment_id}` ({result.origin} -> {result.destination}).\n"
                f"Recommended route is `{winner.route_name}` (${winner.cost_usd:,.2f}, {winner.transit_time_days:.1f} days, score {winner.total_score:.4f}).\n"
                f"To enable generative natural language Q&A, provide a valid GEMINI_API_KEY in the sidebar."
            )

        try:
            payload = self._build_grounded_context(result)
            prompt = (
                "You are RouteWise AI. Answer the user's specific question regarding the shipment routes. "
                "Ground your answer STRICTLY in the provided data. If data is insufficient, state so clearly.\n\n"
                f"SHIPMENT DATA:\n{json.dumps(payload, indent=2)}\n\n"
                f"USER QUESTION: {question}"
            )
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            return f"Error contacting AI model: {str(e)}. Please check your API key."

        return "Could not process question."

    def _build_grounded_context(self, result: OptimizationResult) -> Dict[str, Any]:
        """Creates a clean JSON serializable representation of optimization facts."""
        routes_data = []
        for r in result.all_routes:
            routes_data.append({
                "route_id": r.route_id,
                "route_name": r.route_name,
                "carrier": r.carrier,
                "mode": r.transport_mode,
                "cost_usd": r.cost_usd,
                "transit_days": r.transit_time_days,
                "delay_probability": r.delay_probability,
                "congestion_risk": r.congestion_risk,
                "geopolitical_risk": r.geopolitical_risk,
                "composite_risk": r.composite_risk,
                "normalized_score": r.total_score,
                "is_feasible": r.is_feasible,
                "invalidation_reasons": r.invalidation_reasons,
                "is_pareto_dominated": r.is_pareto_dominated,
                "dominated_by": r.dominated_by,
                "rank": r.rank
            })

        return {
            "shipment_id": result.shipment_id,
            "origin": result.origin,
            "destination": result.destination,
            "cargo_type": result.cargo_type,
            "urgency": result.urgency,
            "weights": {
                "cost": result.weights.cost,
                "time": result.weights.time,
                "risk": result.weights.risk
            },
            "hard_constraints": {
                "max_budget_usd": result.constraints.max_budget_usd,
                "max_transit_days": result.constraints.max_transit_days,
                "max_acceptable_risk": result.constraints.max_acceptable_risk
            },
            "winner_route_id": result.recommended_route.route_id if result.recommended_route else None,
            "all_routes": routes_data,
            "tradeoff_vs_runner_up": result.tradeoff_summary
        }
