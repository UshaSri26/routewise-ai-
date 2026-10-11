"""
AI Assistant View for RouteWise AI.
Interactive decision-support assistant grounded in verified optimization data.
Supports structured analytical queries and natural-language Q&A with offline fallback.
"""

import streamlit as st
import pandas as pd
from src.ui_theme import PRIMARY_TEAL, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, BG_CARD
from src.optimizer import RouteOptimizer, WeightsConfig, HardConstraints
from src.explanations import LLMExplainer, RuleBasedExplainer
from src.money import format_money


def handle_grounded_intent(query: str, opt_result, shipment_df: pd.DataFrame) -> str:
    """Provides deterministic, mathematically exact answers for key operational queries."""
    winner = opt_result.recommended_route
    runner_up = opt_result.runner_up_route
    q_lower = query.lower()

    if "why" in q_lower and "selected" in q_lower:
        return RuleBasedExplainer.generate_explanation(opt_result)

    if "lowest-cost" in q_lower or "lowest cost" in q_lower or "cheapest" in q_lower:
        feasible = [r for r in opt_result.all_routes if r.is_feasible]
        if not feasible:
            return "All routes are currently marked infeasible under the active constraints."
        sorted_by_cost = sorted(feasible, key=lambda x: x.cost_usd)
        r1 = sorted_by_cost[0]
        if len(sorted_by_cost) > 1:
            r2 = sorted_by_cost[1]
            diff = r2.cost_usd - r1.cost_usd
            time_diff = r1.transit_time_days - r2.transit_time_days
            return (
                f"**Lowest-Cost Feasible Route Comparison:**\n\n"
                f"1. **{r1.route_name}** (`{r1.route_id}`): **{format_money(r1.cost_usd)}** | {r1.transit_time_days:.1f} days | Delay Risk: {r1.delay_probability*100:.1f}%\n"
                f"2. **{r2.route_name}** (`{r2.route_id}`): **{format_money(r2.cost_usd)}** | {r2.transit_time_days:.1f} days | Delay Risk: {r2.delay_probability*100:.1f}%\n\n"
                f"**Trade-off:** `{r1.route_id}` saves **{format_money(diff)}**, but takes **{time_diff:+.1f} days** relative to `{r2.route_id}`."
            )
        return f"Only one feasible route available: `{r1.route_id}` at **{format_money(r1.cost_usd)}**."

    if "speed" in q_lower or "delivery speed" in q_lower or "faster" in q_lower:
        fast_weights = WeightsConfig(cost=0.15, time=0.70, risk=0.15)
        fast_res = RouteOptimizer.evaluate_shipment_routes(shipment_df, weights=fast_weights)
        w_fast = fast_res.recommended_route
        return (
            f"**Impact of Prioritizing Delivery Speed (Time Weight = 70%):**\n\n"
            f"Under an emergency speed priority, the optimal choice shifts to **{w_fast.route_name}** (`{w_fast.route_id}`).\n"
            f"- **Transit Time:** {w_fast.transit_time_days:.1f} days (compared to {winner.transit_time_days:.1f} days for current baseline)\n"
            f"- **Freight Cost:** {format_money(w_fast.cost_usd)} (delta vs current: {format_money(abs(w_fast.cost_usd - winner.cost_usd))})\n"
            f"- **Score:** `{w_fast.total_score:.4f}`\n\n"
            f"*Summary:* Switching to time-critical saves **{winner.transit_time_days - w_fast.transit_time_days:.1f} days** at a freight cost delta of **{format_money(abs(w_fast.cost_usd - winner.cost_usd))}**."
        )

    if "violate" in q_lower or "constraint" in q_lower or "infeasible" in q_lower:
        infeasible = [r for r in opt_result.all_routes if not r.is_feasible]
        if not infeasible:
            return "✅ **All 4 candidate routes satisfy the active constraints.** None are currently disqualified."
        lines = ["**Routes Violating Active Constraints:**\n"]
        for inf in infeasible:
            reasons = "; ".join(inf.invalidation_reasons)
            lines.append(f"- **{inf.route_name}** (`{inf.route_id}`): Disqualified due to: *{reasons}*")
        return "\n".join(lines)

    return ""


def render_assistant(df_fleet: pd.DataFrame, api_key: str = None):
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.02em; margin-bottom: 0.25rem;">
            AI Logistics Decision Assistant
        </h1>
        <p style="font-size: 0.95rem; color: #93A4B8; margin: 0;">
            Ask questions about routing trade-offs, constraint breaches, and scenario shifts. Responses are grounded strictly in optimizer calculations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Active Shipment Scope
    shipment_ids = sorted(df_fleet["shipment_id"].unique())
    selected_id = st.selectbox(
        "Active Shipment Scope:",
        shipment_ids,
        index=0,
        format_func=lambda s: f"{s} — {df_fleet[df_fleet['shipment_id'] == s]['origin'].iloc[0]} ➔ {df_fleet[df_fleet['shipment_id'] == s]['destination'].iloc[0]}"
    )
    shipment_df = df_fleet[df_fleet["shipment_id"] == selected_id].copy()
    opt_result = RouteOptimizer.evaluate_shipment_routes(shipment_df, WeightsConfig())

    # Suggested Prompts Section
    st.markdown("<h4 style='font-size: 0.95rem; font-weight: 600; color: #F1F5F9; margin-top: 1rem; margin-bottom: 0.5rem;'>Suggested Operational Queries:</h4>", unsafe_allow_html=True)
    
    col_q1, col_q2 = st.columns(2)
    col_q3, col_q4 = st.columns(2)

    active_query = None
    with col_q1:
        if st.button("💬 Why was this route selected?", use_container_width=True):
            active_query = "Why was this route selected?"
    with col_q2:
        if st.button("💰 Compare the two lowest-cost feasible routes.", use_container_width=True):
            active_query = "Compare the two lowest-cost feasible routes."
    with col_q3:
        if st.button("⚡ What changes if I prioritize delivery speed?", use_container_width=True):
            active_query = "What changes if I prioritize delivery speed?"
    with col_q4:
        if st.button("🚫 Which routes violate my constraints?", use_container_width=True):
            active_query = "Which routes violate my constraints?"

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Freeform Question Input
    user_input = st.text_input(
        "Or enter a custom question:",
        value=active_query if active_query else "",
        placeholder="e.g. Compare the trade-offs between Route 1 and Route 2..."
    )

    if user_input:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"**Query:** *{user_input}*")

        # Try deterministic intent first
        deterministic_resp = handle_grounded_intent(user_input, opt_result, shipment_df)

        if deterministic_resp:
            st.markdown(f"""
            <div class="rw-card" style="padding: 20px; border-left: 4px solid {PRIMARY_TEAL};">
                <div style="font-size: 0.75rem; color: {PRIMARY_TEAL}; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">
                    Verified Deterministic Decision Engine
                </div>
                <div style="color: #F1F5F9; line-height: 1.6;">
                    {deterministic_resp}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Fall back to LLMExplainer
            with st.spinner("Analyzing verified shipment metrics..."):
                explainer = LLMExplainer(api_key=api_key)
                llm_resp = explainer.answer_question(user_input, opt_result)
                st.markdown(f"""
                <div class="rw-card" style="padding: 20px; border-left: 4px solid {PRIMARY_TEAL};">
                    <div style="font-size: 0.75rem; color: {PRIMARY_TEAL}; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">
                        Grounded AI Response
                    </div>
                    <div style="color: #F1F5F9; line-height: 1.6;">
                        {llm_resp}
                    </div>
                </div>
                """, unsafe_allow_html=True)
