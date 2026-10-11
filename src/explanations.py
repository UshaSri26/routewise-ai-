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
from src.money import format_money


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
            f"**Key Metrics:** {format_money(winner.cost_usd)} | {winner.transit_time_days:.1f} days | "
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
                lines.append(f"- Saves **{format_money(abs(cost_diff))}** ({abs(tradeoff['cost_pct_diff'])}%) in freight charges.")
            elif cost_diff > 0:
                lines.append(f"- Costs **{format_money(cost_diff)}** ({tradeoff['cost_pct_diff']}%) more, justified by performance gains.")
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

            from google import genai

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
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
        # If offline or no API key, use comprehensive grounded analytical engine
        if not self.is_available():
            return self._offline_grounded_answer(question, result)

        try:
            payload = self._build_grounded_context(result)
            prompt = (
                "You are RouteWise AI. Answer the user's specific question regarding the shipment routes. "
                "Ground your answer STRICTLY in the provided data. If data is insufficient, state so clearly.\n\n"
                f"SHIPMENT DATA:\n{json.dumps(payload, indent=2)}\n\n"
                f"USER QUESTION: {question}"
            )
            from google import genai

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            return f"Error contacting AI model: {str(e)}. Please check your API key."

        return "Could not process question."

    def _offline_grounded_answer(self, question: str, result: OptimizationResult) -> str:
        """Generates comprehensive, numbers-verified answers for common logistics queries in offline mode."""
        q_lower = question.lower()
        winner = result.recommended_route
        runner_up = result.runner_up_route
        tradeoff = result.tradeoff_summary
        routes = result.all_routes

        if not winner:
            return "No route could be evaluated for this shipment."

        # 1. Trade-off questions
        if "tradeoff" in q_lower or "trade-off" in q_lower or "trade off" in q_lower or "compare" in q_lower:
            lines = [
                f"### ⚖️ Trade-Off Analysis for Shipment `{result.shipment_id}` ({result.origin} ➔ {result.destination}):\n",
                f"**Optimal Winner:** **{winner.route_name}** (`{winner.route_id}`) at **{format_money(winner.cost_usd)}**, **{winner.transit_time_days:.1f} days**, Risk: **{winner.composite_risk:.3f}** (Score: `{winner.total_score:.4f}`).\n"
            ]
            if runner_up and tradeoff:
                lines.append(f"**Key Trade-offs vs Runner-Up (`{runner_up.route_name}`):**")
                c_diff = tradeoff.get("cost_delta_usd", 0)
                t_diff = tradeoff.get("time_delta_days", 0)
                r_diff = tradeoff.get("risk_delta", 0)
                pct_diff = tradeoff.get("cost_pct_diff", 0)

                if c_diff > 0:
                    lines.append(f"- 💰 **Cost:** Premium of **+{format_money(c_diff)}** (+{pct_diff}%) over `{runner_up.route_id}`.")
                else:
                    lines.append(f"- 💰 **Cost:** Saves **{format_money(abs(c_diff))}** ({abs(pct_diff)}%) in freight charges.")

                if t_diff < 0:
                    lines.append(f"- ⏱️ **Speed:** Arrives **{abs(t_diff):.1f} days faster** than `{runner_up.route_id}`.")
                else:
                    lines.append(f"- ⏱️ **Speed:** Adds **{t_diff:.1f} days** in transit time.")

                if r_diff < 0:
                    lines.append(f"- 🛡️ **Risk:** Cuts composite risk index by **{abs(r_diff):.3f}** (lower delay and congestion).")
                else:
                    lines.append(f"- 🛡️ **Risk:** Incurs slight risk adjustment of **+{r_diff:.3f}**.")

            # Summary across the fleet candidates
            cheapest = min(routes, key=lambda x: x.cost_usd)
            fastest = min(routes, key=lambda x: x.transit_time_days)
            lines.append("\n**Corridor Spectrum:**")
            lines.append(f"- **Cheapest Option:** `{cheapest.route_id}` ({format_money(cheapest.cost_usd)}, {cheapest.transit_time_days:.1f} days)")
            lines.append(f"- **Fastest Option:** `{fastest.route_id}` ({format_money(fastest.cost_usd)}, {fastest.transit_time_days:.1f} days)")
            return "\n".join(lines)

        # 2. Why questions
        if "why" in q_lower:
            return RuleBasedExplainer.generate_explanation(result)

        # 3. Cost / Price questions
        if "cost" in q_lower or "cheap" in q_lower or "price" in q_lower:
            sorted_cost = sorted([r for r in routes if r.is_feasible], key=lambda x: x.cost_usd)
            if not sorted_cost:
                return "All routes are currently marked infeasible under the active budget/time constraints."
            best_c = sorted_cost[0]
            lines = [f"**Cost Ranking for Feasible Routes:**\n"]
            for idx, r in enumerate(sorted_cost, 1):
                star = "⭐ " if r.route_id == winner.route_id else ""
                lines.append(f"{idx}. {star}**{r.route_name}** (`{r.route_id}`): **{format_money(r.cost_usd)}** | {r.transit_time_days:.1f} days | Delay: {r.delay_probability*100:.1f}%")
            return "\n".join(lines)

        # 4. Speed / Transit questions
        if "speed" in q_lower or "fast" in q_lower or "time" in q_lower:
            sorted_time = sorted([r for r in routes if r.is_feasible], key=lambda x: x.transit_time_days)
            best_t = sorted_time[0]
            lines = [
                f"**Fastest Delivery Option:** **{best_t.route_name}** (`{best_t.route_id}`) at **{best_t.transit_time_days:.1f} days** ({format_money(best_t.cost_usd)}).",
                f"- Saves **{winner.transit_time_days - best_t.transit_time_days:.1f} days** compared to the current recommendation ({winner.transit_time_days:.1f} days).",
                f"- Incurs a freight cost difference of **{format_money(abs(best_t.cost_usd - winner.cost_usd))}**."
            ]
            return "\n".join(lines)

        # 5. Risk / Safety questions
        if "risk" in q_lower or "safe" in q_lower or "delay" in q_lower:
            sorted_risk = sorted([r for r in routes if r.is_feasible], key=lambda x: x.composite_risk)
            safest = sorted_risk[0]
            return (
                f"**Safest & Most Resilient Option:** **{safest.route_name}** (`{safest.route_id}`)\n"
                f"- Composite Risk: **{safest.composite_risk:.3f}** | Delay Probability: **{safest.delay_probability*100:.1f}%**\n"
                f"- Congestion Index: **{safest.congestion_risk:.0f}/100** | Geopolitical Exposure: **{safest.geopolitical_risk:.0f}/100**\n"
                f"- Hubs: *{safest.intermediate_hubs}*"
            )

        # Default fallback: structured executive overview
        return (
            f"**Decision Intelligence Summary (Shipment `{result.shipment_id}`):**\n\n"
            f"• **Recommended Choice:** **{winner.route_name}** (`{winner.route_id}`) with an overall score of **{winner.total_score:.4f}**.\n"
            f"• **Operational Profile:** Freight: **{format_money(winner.cost_usd)}** | Transit: **{winner.transit_time_days:.1f} days** | Delay Risk: **{winner.delay_probability*100:.1f}%**.\n"
            f"• **Trade-off:** Chosen by the weighted cost, transit-time, and synthetic risk score among feasible options.\n\n"
            f"*(Tip: Ask 'what are the tradeoffs', 'why was this chosen', or 'which is fastest')*"
        )

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
