"""
RouteWise AI - Main Streamlit Application
Interactive Decision-Support System for Global Shipment Routing.
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.optimizer import (
    RouteOptimizer,
    WeightsConfig,
    HardConstraints,
    run_sensitivity_analysis
)
from src.explanations import RuleBasedExplainer, LLMExplainer
from src.data_generator import generate_shipments_dataset, save_dataset

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="RouteWise AI | Shipment Route Intelligence",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished enterprise look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .recommendation-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .badge-winner {
        background-color: #10B981;
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_dataset() -> pd.DataFrame:
    data_path = Path("data/shipments.csv")
    if not data_path.exists():
        save_dataset(str(data_path), num_shipments=30)
    return pd.read_csv(data_path)


df_fleet = load_dataset()

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/cargo-ship.png", width=64)
    st.title("RouteWise AI")
    st.caption("AI-Powered Route Decision Engine")
    st.markdown("---")

    st.subheader("1. Select Shipment")
    shipment_ids = sorted(df_fleet["shipment_id"].unique())
    selected_shipment_id = st.selectbox(
        "Shipment ID",
        shipment_ids,
        index=0,
        format_func=lambda sid: f"{sid} ({df_fleet[df_fleet['shipment_id'] == sid]['origin'].iloc[0][:12]} ➔ {df_fleet[df_fleet['shipment_id'] == sid]['destination'].iloc[0][:12]})"
    )

    shipment_data = df_fleet[df_fleet["shipment_id"] == selected_shipment_id].copy()
    shipment_info = shipment_data.iloc[0]

    st.markdown("---")
    st.subheader("2. Optimization Priorities")
    
    preset = st.radio(
        "Priority Profile Preset",
        ["Balanced (40/30/30)", "Cost-Focused (70/15/15)", "Time-Critical (15/70/15)", "Risk-Averse (15/15/70)", "Custom Sliders"],
        index=0
    )

    if preset == "Balanced (40/30/30)":
        w_cost, w_time, w_risk = 0.40, 0.30, 0.30
    elif preset == "Cost-Focused (70/15/15)":
        w_cost, w_time, w_risk = 0.70, 0.15, 0.15
    elif preset == "Time-Critical (15/70/15)":
        w_cost, w_time, w_risk = 0.15, 0.70, 0.15
    elif preset == "Risk-Averse (15/15/70)":
        w_cost, w_time, w_risk = 0.15, 0.15, 0.70
    else:
        st.caption("Adjust sliders (auto-normalized to 1.0):")
        raw_c = st.slider("Cost Weight", 0.0, 1.0, 0.4, 0.05)
        raw_t = st.slider("Transit Time Weight", 0.0, 1.0, 0.3, 0.05)
        raw_r = st.slider("Risk Weight", 0.0, 1.0, 0.3, 0.05)
        raw_total = raw_c + raw_t + raw_r
        if raw_total == 0:
            w_cost, w_time, w_risk = 0.4, 0.3, 0.3
        else:
            w_cost = round(raw_c / raw_total, 3)
            w_time = round(raw_t / raw_total, 3)
            w_risk = round(1.0 - w_cost - w_time, 3)

    weights = WeightsConfig(cost=w_cost, time=w_time, risk=w_risk)
    st.info(f"Active Weights: 💰 Cost: **{w_cost*100:.0f}%** | ⏱️ Time: **{w_time*100:.0f}%** | 🛡️ Risk: **{w_risk*100:.0f}%**")

    st.markdown("---")
    st.subheader("3. Hard Constraints")
    enable_budget = st.checkbox("Enforce Max Budget", value=False)
    max_budget_val = None
    if enable_budget:
        default_budget = float(shipment_data["cost_usd"].mean() * 1.25)
        max_budget_val = st.number_input("Max Budget ($)", min_value=1000.0, max_value=50000.0, value=default_budget, step=250.0)

    enable_time = st.checkbox("Enforce Max Transit Days", value=False)
    max_time_val = None
    if enable_time:
        default_days = float(shipment_data["transit_time_days"].mean() * 1.1)
        max_time_val = st.number_input("Max Transit Days", min_value=1.0, max_value=60.0, value=default_days, step=1.0)

    enable_risk = st.checkbox("Enforce Max Risk Cutoff", value=False)
    max_risk_val = None
    if enable_risk:
        max_risk_val = st.slider("Max Composite Risk", 0.1, 1.0, 0.65, 0.05)

    constraints = HardConstraints(
        max_budget_usd=max_budget_val,
        max_transit_days=max_time_val,
        max_acceptable_risk=max_risk_val
    )

    st.markdown("---")
    st.subheader("4. AI Explainer Key (Optional)")
    api_key_input = st.text_input("Gemini API Key", type="password", help="Leave blank to run 100% offline with deterministic explainability")


# --- RUN OPTIMIZER ---
opt_result = RouteOptimizer.evaluate_shipment_routes(shipment_data, weights=weights, constraints=constraints)
winner = opt_result.recommended_route
explainer = LLMExplainer(api_key=api_key_input if api_key_input else None)

# --- HEADER SECTION ---
st.markdown('<div class="main-header">🚢 RouteWise AI — Shipment Route Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Evaluating multi-objective trade-offs across Cost, Transit Time, and Logistics Risk under uncertainty.</div>', unsafe_allow_html=True)

# Shipment Context Bar
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"**Shipment ID:** `{selected_shipment_id}`")
        st.markdown(f"**Corridor:** {shipment_info['corridor']}")
    with c2:
        st.markdown(f"**Origin:** {shipment_info['origin']}")
        st.markdown(f"**Destination:** {shipment_info['destination']}")
    with c3:
        st.markdown(f"**Cargo:** {shipment_info['cargo_type']}")
        st.markdown(f"**Urgency:** `{shipment_info['urgency']}`")
    with c4:
        st.markdown(f"**Candidates Evaluated:** `{len(shipment_data)} routes`")
        status_label = "⚠️ Infeasible / Best-Effort" if opt_result.all_infeasible else "✅ Feasible Winner Selected"
        st.markdown(f"**Status:** {status_label}")

st.markdown("---")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🎯 Recommendation & Evidence", "🔬 What-If & Sensitivity", "📊 Fleet Dataset Explorer"])

with tab1:
    if winner:
        # Winning Route Highlight Banner
        st.markdown(f"""
        <div class="recommendation-banner">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 1.4rem; font-weight:700;">Recommended: {winner.route_name} ({winner.route_id})</span>
                <span class="badge-winner">OPTIMAL CHOICE</span>
            </div>
            <p style="margin-top:6px; opacity:0.9;">Carrier: <b>{winner.carrier}</b> | Transport Mode: <b>{winner.transport_mode}</b> | Route: <b>{winner.intermediate_hubs}</b></p>
        </div>
        """, unsafe_allow_html=True)

        # KPI Metrics Row
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Total Landed Cost", f"${winner.cost_usd:,.2f}", delta=f"{opt_result.tradeoff_summary.get('cost_pct_diff', 0):+.1f}% vs runner-up" if opt_result.tradeoff_summary else None, delta_color="inverse")
        with m2:
            st.metric("Transit Duration", f"{winner.transit_time_days:.1f} Days", delta=f"{opt_result.tradeoff_summary.get('time_delta_days', 0):+.1f} d" if opt_result.tradeoff_summary else None, delta_color="inverse")
        with m3:
            st.metric("Delay Probability", f"{winner.delay_probability*100:.1f}%")
        with m4:
            st.metric("Composite Risk Score", f"{winner.composite_risk:.3f}", help="Weighted index of delay probability, congestion, and geopolitical risk")
        with m5:
            st.metric("Optimizer Score", f"{winner.total_score:.4f}", help="Multi-criteria weighted score (lower is better)")

        st.markdown("### 🧠 AI Decision Briefing")
        with st.container():
            briefing = explainer.generate_explanation(opt_result)
            st.markdown(briefing)

        st.markdown("---")
        st.subheader("📈 Trade-off Visualizations")

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            # Bar chart comparing routes
            plot_df = pd.DataFrame([
                {
                    "Route": f"{r.route_id}\n({r.carrier})",
                    "Cost ($)": r.cost_usd,
                    "Transit Days": r.transit_time_days,
                    "Composite Risk (x100)": r.composite_risk * 100,
                    "Optimizer Score (x1000)": r.total_score * 1000,
                    "Is Winner": "Winner" if r.route_id == winner.route_id else ("Infeasible" if not r.is_feasible else "Alternative")
                }
                for r in opt_result.all_routes
            ])

            fig_bar = px.bar(
                plot_df,
                x="Route",
                y=["Cost ($)", "Transit Days", "Composite Risk (x100)"],
                barmode="group",
                title="Direct Attribute Comparison Across Candidate Routes",
                color_discrete_sequence=["#2563EB", "#F59E0B", "#EF4444"]
            )
            fig_bar.update_layout(legend_title="Metric", height=420)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            # Trade-off Frontier Scatter Plot (Cost vs Time with bubble size = Risk)
            scatter_df = pd.DataFrame([
                {
                    "Route ID": r.route_id,
                    "Route Name": r.route_name,
                    "Cost ($)": r.cost_usd,
                    "Transit Days": r.transit_time_days,
                    "Composite Risk": r.composite_risk,
                    "Risk Bubble": max(r.composite_risk * 30, 8),
                    "Status": "⭐ Selected Winner" if r.route_id == winner.route_id else ("❌ Infeasible" if not r.is_feasible else "Feasible Alternative")
                }
                for r in opt_result.all_routes
            ])

            fig_scatter = px.scatter(
                scatter_df,
                x="Transit Days",
                y="Cost ($)",
                size="Risk Bubble",
                color="Status",
                hover_name="Route Name",
                hover_data=["Cost ($)", "Transit Days", "Composite Risk"],
                title="Trade-off Landscape: Cost vs. Transit Time (Bubble Size = Risk)",
                color_discrete_map={
                    "⭐ Selected Winner": "#10B981",
                    "Feasible Alternative": "#3B82F6",
                    "❌ Infeasible": "#EF4444"
                }
            )
            fig_scatter.update_layout(height=420)
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("📋 Comprehensive Route Scoring Table")
        table_rows = []
        for r in opt_result.all_routes:
            table_rows.append({
                "Rank": f"#{r.rank}" if r.is_feasible else "Excluded",
                "Route ID": r.route_id,
                "Route Name": r.route_name,
                "Carrier": r.carrier,
                "Mode": r.transport_mode,
                "Cost ($)": f"${r.cost_usd:,.2f}",
                "Transit (days)": f"{r.transit_time_days:.1f}",
                "Delay Prob": f"{r.delay_probability*100:.1f}%",
                "Congestion": f"{r.congestion_risk:.0f}/100",
                "Geopolitical Risk": f"{r.geopolitical_risk:.0f}/100",
                "Total Score": f"{r.total_score:.4f}",
                "Feasible?": "✅ Yes" if r.is_feasible else f"❌ {', '.join(r.invalidation_reasons)}",
                "Pareto Efficient?": "❌ Dominated" if r.is_pareto_dominated else "✅ Efficient"
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


with tab2:
    st.subheader("🔬 Multi-Scenario Sensitivity Analysis")
    st.markdown(
        "Evaluate how the optimal routing decision pivots under varying business scenarios and priority profiles."
    )

    sens_df = run_sensitivity_analysis(shipment_data, constraints=constraints)
    st.dataframe(sens_df, use_container_width=True, hide_index=True)

    # Interactive Radar / Profile comparison
    st.markdown("---")
    st.subheader("💬 Ask RouteWise AI (What-If Assistant)")
    user_query = st.text_input(
        "Ask a question about this shipment's routes:",
        placeholder="e.g. Why did you not select the multimodal air route? Or what happens if transit deadline is 15 days?"
    )
    if user_query:
        with st.spinner("Analyzing decision trade-offs..."):
            ans = explainer.answer_question(user_query, opt_result)
            st.markdown(f"**RouteWise Response:**\n\n{ans}")


with tab3:
    st.subheader("📊 Fleet-Wide Dataset Overview (30 Shipments, 120 Route Options)")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.metric("Total Shipments", f"{df_fleet['shipment_id'].nunique()}")
    with col_f2:
        st.metric("Total Route Candidates", f"{len(df_fleet)}")
    with col_f3:
        st.metric("Average Ocean Transit Time", f"{df_fleet[df_fleet['transport_mode'] == 'Ocean']['transit_time_days'].mean():.1f} Days")

    st.markdown("### Corridor Cost & Time Distribution")
    fig_corridor = px.box(
        df_fleet,
        x="corridor",
        y="cost_usd",
        color="transport_mode",
        title="Cost Distribution Across Global Trade Corridors",
        labels={"cost_usd": "Cost ($ USD)", "corridor": "Trade Corridor"}
    )
    fig_corridor.update_layout(height=450)
    st.plotly_chart(fig_corridor, use_container_width=True)

    st.markdown("### Filter & Search Dataset")
    st.dataframe(df_fleet, use_container_width=True)
