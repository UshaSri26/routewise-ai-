"""
Route Optimizer View for RouteWise AI.
The primary operational page for configuring priorities, enforcing constraints,
and analyzing mathematically verified route recommendations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ui_theme import (
    PRIMARY_TEAL, SECONDARY_TEAL, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER_COLOR, BG_CARD, BG_ELEVATED, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR,
    get_plotly_layout
)
from src.optimizer import RouteOptimizer, WeightsConfig, HardConstraints
from src.explanations import LLMExplainer, RuleBasedExplainer
from src.money import format_money


def render_optimizer(df_fleet: pd.DataFrame, api_key: str = None):
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.02em; margin-bottom: 0.25rem;">
            Route Optimizer
        </h1>
        <p style="font-size: 0.95rem; color: #93A4B8; margin: 0;">
            Configure shipment SLA constraints, tune multi-criteria weights, and inspect mathematically grounded route rankings.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. SHIPMENT SELECTION BAR
    shipment_ids = sorted(df_fleet["shipment_id"].unique())
    selected_id = st.selectbox(
        "Select Active Shipment:",
        shipment_ids,
        index=0,
        format_func=lambda s: f"{s} — {df_fleet[df_fleet['shipment_id'] == s]['origin'].iloc[0]} ➔ {df_fleet[df_fleet['shipment_id'] == s]['destination'].iloc[0]}"
    )

    shipment_df = df_fleet[df_fleet["shipment_id"] == selected_id].copy()
    ship_info = shipment_df.iloc[0]

    # Context Card
    st.markdown(f"""
    <div class="rw-card" style="margin-top: 0.5rem; margin-bottom: 1.5rem; padding: 14px 20px;">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;">
            <div>
                <span style="font-size: 0.75rem; color: #93A4B8; text-transform: uppercase; font-weight: 600;">Trade Corridor:</span>
                <span style="font-size: 0.95rem; color: #F1F5F9; font-weight: 600; margin-left: 6px;">{ship_info['origin']} ➔ {ship_info['destination']}</span>
            </div>
            <div style="display: flex; gap: 16px;">
                <div><span style="font-size: 0.75rem; color: #93A4B8; font-weight: 600;">CARGO:</span> <span style="font-size: 0.85rem; color: {PRIMARY_TEAL}; font-weight: 600;">{ship_info['cargo_type']}</span></div>
                <div><span style="font-size: 0.75rem; color: #93A4B8; font-weight: 600;">SLA URGENCY:</span> <span style="font-size: 0.85rem; color: #F59E0B; font-weight: 600;">{ship_info['urgency']}</span></div>
                <div><span style="font-size: 0.75rem; color: #93A4B8; font-weight: 600;">CANDIDATES:</span> <span style="font-size: 0.85rem; color: #F1F5F9; font-weight: 600;">{len(shipment_df)} Routes</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. CONFIGURATION CONTROLS (Priorities & Constraints)
    col_priorities, col_constraints = st.columns([1, 1])

    with col_priorities:
        st.markdown("<h4 style='font-size: 1rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>1. Multi-Objective Priority Weights</h4>", unsafe_allow_html=True)
        
        preset = st.radio(
            "Priority Profile Preset",
            ["Balanced (40/30/30)", "Cost-Focused (70/15/15)", "Time-Critical (15/70/15)", "Risk-Averse (15/15/70)", "Custom Sliders"],
            horizontal=True,
            index=0
        )

        if preset == "Balanced (40/30/30)":
            w_c, w_t, w_r = 0.40, 0.30, 0.30
        elif preset == "Cost-Focused (70/15/15)":
            w_c, w_t, w_r = 0.70, 0.15, 0.15
        elif preset == "Time-Critical (15/70/15)":
            w_c, w_t, w_r = 0.15, 0.70, 0.15
        elif preset == "Risk-Averse (15/15/70)":
            w_c, w_t, w_r = 0.15, 0.15, 0.70
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                rc = st.slider("Cost Weight", 0.0, 1.0, 0.4, 0.05)
            with c2:
                rt = st.slider("Time Weight", 0.0, 1.0, 0.3, 0.05)
            with c3:
                rr = st.slider("Risk Weight", 0.0, 1.0, 0.3, 0.05)
            rtot = rc + rt + rr
            if rtot == 0:
                w_c, w_t, w_r = 0.4, 0.3, 0.3
            else:
                w_c, w_t = round(rc / rtot, 3), round(rt / rtot, 3)
                w_r = round(1.0 - w_c - w_t, 3)

        st.caption(f"Active Weights: 💰 Cost: **{w_c*100:.0f}%** | ⏱️ Transit Time: **{w_t*100:.0f}%** | 🛡️ Risk: **{w_r*100:.0f}%**")

    with col_constraints:
        st.markdown("<h4 style='font-size: 1rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>2. Hard Operational Constraints</h4>", unsafe_allow_html=True)
        
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            en_budget = st.checkbox("Enforce Max Budget", value=False)
            max_b_val = None
            if en_budget:
                def_b = float(max(5.0, round(shipment_df["cost_usd"].mean() * 1.35, 2)))
                max_b_val = st.number_input("Max Budget (USD)", min_value=1.0, max_value=2000.0, value=def_b, step=5.0)

        with c_b2:
            en_time = st.checkbox("Enforce Max Transit Days", value=False)
            max_t_val = None
            if en_time:
                def_t = float(round(shipment_df["transit_time_days"].mean() * 1.1, 1))
                max_t_val = st.number_input("Max Days Window", min_value=1.0, max_value=60.0, value=def_t, step=1.0)

        en_risk = st.checkbox("Enforce Max Risk Cutoff", value=False)
        max_r_val = None
        if en_risk:
            max_r_val = st.slider("Max Acceptable Risk Index", 0.1, 1.0, 0.65, 0.05)

    weights = WeightsConfig(cost=w_c, time=w_t, risk=w_r)
    constraints = HardConstraints(
        max_budget_usd=max_b_val,
        max_transit_days=max_t_val,
        max_acceptable_risk=max_r_val
    )

    # 3. RUN OPTIMIZER
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    opt_btn = st.button("⚡ Optimize Routes", use_container_width=True)

    result = RouteOptimizer.evaluate_shipment_routes(shipment_df, weights=weights, constraints=constraints)
    winner = result.recommended_route

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 4. RECOMMENDATION HERO CARD
    if winner:
        if result.all_infeasible:
            st.markdown(f"""
            <div class="rw-infeasible-banner">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size: 1.25rem; font-weight:700; color: {COLOR_WARNING};">
                        ⚠️ Infeasible Constraints Detected — Best-Effort Recommendation: {winner.route_name}
                    </div>
                    <span class="rw-badge-dominated">BEST-EFFORT FALLBACK</span>
                </div>
                <p style="margin-top:8px; color: #F1F5F9; font-size: 0.9rem;">
                    All routes breach the specified limits. Showing route with lowest penalty violation.
                    <b>Violation:</b> {'; '.join(winner.invalidation_reasons)}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="rw-winner-banner">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div class="rw-winner-tag">Optimal Recommendation</div>
                        <div style="font-size: 1.45rem; font-weight:700; color: #F1F5F9; letter-spacing: -0.02em;">
                            {winner.route_name} <span style="font-size: 1.05rem; color: {PRIMARY_TEAL};">({winner.route_id})</span>
                        </div>
                    </div>
                    <span class="rw-badge-feasible">FEASIBLE WINNER</span>
                </div>
                <div style="margin-top: 10px; font-size: 0.88rem; color: #93A4B8;">
                    Carrier: <b style="color:#F1F5F9;">{winner.carrier}</b> &nbsp;|&nbsp; 
                    Mode: <b style="color:#F1F5F9;">{winner.transport_mode}</b> &nbsp;|&nbsp; 
                    Hubs: <b style="color:#F1F5F9;">{winner.intermediate_hubs}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # KPI Metrics Row
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Freight Cost", format_money(winner.cost_usd),
                      delta=f"{result.tradeoff_summary.get('cost_pct_diff', 0):+.1f}% vs runner-up" if result.tradeoff_summary else None,
                      delta_color="inverse")
        with m2:
            st.metric("Transit Duration", f"{winner.transit_time_days:.1f} Days",
                      delta=f"{result.tradeoff_summary.get('time_delta_days', 0):+.1f} d" if result.tradeoff_summary else None,
                      delta_color="inverse")
        with m3:
            st.metric("Delay Probability", f"{winner.delay_probability*100:.1f}%")
        with m4:
            st.metric("Composite Risk", f"{winner.composite_risk:.3f}")
        with m5:
            st.metric("Optimizer Score", f"{winner.total_score:.4f}", help="Lower is better")

    # 5. GROUNDED AI EXPLANATION
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>Grounded Decision Rationale</h3>", unsafe_allow_html=True)

    explainer = LLMExplainer(api_key=api_key)
    with st.container():
        st.markdown(f"""
        <div class="rw-card" style="padding: 20px;">
        """, unsafe_allow_html=True)
        explanation_text = explainer.generate_explanation(result)
        st.markdown(explanation_text)
        st.markdown("</div>", unsafe_allow_html=True)

    # 6. ROUTE COMPARISON TABLE
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>Route Alternatives Comparison Matrix</h3>", unsafe_allow_html=True)

    table_data = []
    for r in result.all_routes:
        status_text = "Feasible" if r.is_feasible else f"Infeasible ({'; '.join(r.invalidation_reasons)})"
        pareto_text = f"Dominated by {', '.join(r.dominated_by)}" if r.is_pareto_dominated else "Pareto-Efficient"
        
        table_data.append({
            "Rank": f"#{r.rank}" if r.is_feasible else "Excluded",
            "Route ID": r.route_id,
            "Route Name": r.route_name,
            "Carrier": r.carrier,
            "Mode": r.transport_mode,
            "Cost": format_money(r.cost_usd),
            "Transit (Days)": f"{r.transit_time_days:.1f}",
            "Delay Prob": f"{r.delay_probability*100:.1f}%",
            "Congestion": f"{r.congestion_risk:.0f}/100",
            "Geopolitical": f"{r.geopolitical_risk:.0f}/100",
            "Weighted Score": f"{r.total_score:.4f}",
            "Feasibility": status_text,
            "Efficiency": pareto_text
        })

    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # 7. TRADE-OFF VISUALIZATIONS
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>Trade-Off Visualizations</h3>", unsafe_allow_html=True)

    c_v1, c_v2 = st.columns(2)

    with c_v1:
        # Scatter Plot: Cost vs Transit Days (Bubble size = Risk)
        scatter_items = []
        for r in result.all_routes:
            cat = "Optimal Winner" if winner and r.route_id == winner.route_id else ("Infeasible" if not r.is_feasible else "Feasible Alternative")
            scatter_items.append({
                "Route": r.route_name,
                "Route ID": r.route_id,
                "Cost ($ USD)": r.cost_usd,
                "Transit Time (Days)": r.transit_time_days,
                "Composite Risk": r.composite_risk,
                "Risk Bubble": max(r.composite_risk * 32, 10),
                "Category": cat
            })
        
        fig_scatter = px.scatter(
            pd.DataFrame(scatter_items),
            x="Transit Time (Days)",
            y="Cost ($ USD)",
            size="Risk Bubble",
            color="Category",
            hover_name="Route",
            hover_data=["Cost ($ USD)", "Transit Time (Days)", "Composite Risk"],
            color_discrete_map={
                "Optimal Winner": PRIMARY_TEAL,
                "Feasible Alternative": "#3B82F6",
                "Infeasible": COLOR_ERROR
            }
        )
        layout_sc = get_plotly_layout(title="Trade-Off Landscape: Cost vs. Transit Duration (Size = Risk)")
        fig_scatter.update_layout(layout_sc)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c_v2:
        # Bar Chart comparing attributes
        bar_items = []
        for r in result.all_routes:
            bar_items.append({
                "Route ID": r.route_id,
                "Cost (₹)": r.cost_usd * 84.0,
                "Transit Hours": r.transit_time_days * 24.0,
                "Risk (x100)": r.composite_risk * 100.0,
            })
        df_bar = pd.DataFrame(bar_items)
        
        fig_bar = px.bar(
            df_bar,
            x="Route ID",
            y=["Cost (₹)", "Transit Hours", "Risk (x100)"],
            barmode="group",
            color_discrete_sequence=[PRIMARY_TEAL, "#3B82F6", "#F59E0B"]
        )
        layout_bar = get_plotly_layout(title="Normalized Metric Comparison Across Candidates")
        fig_bar.update_layout(layout_bar)
        st.plotly_chart(fig_bar, use_container_width=True)
