"""
Overview View for RouteWise AI.
Executive dashboard presenting high-level fleet metrics, trade-off landscape, and active status.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.ui_theme import (
    PRIMARY_TEAL, SECONDARY_TEAL, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER_COLOR, BG_CARD, get_plotly_layout
)
from src.optimizer import RouteOptimizer, WeightsConfig, HardConstraints


def render_overview(df_fleet: pd.DataFrame, on_navigate_optimizer):
    # Hero Title & Subtitle
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2.25rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.025em; margin-bottom: 0.5rem;">
            Shipment decisions, made intelligently.
        </h1>
        <p style="font-size: 1.05rem; color: #93A4B8; max-width: 780px; line-height: 1.5; margin-bottom: 1.25rem;">
            A multi-objective intelligence system balancing freight cost, transit velocity, and logistics risk under uncertainty.
            Powered by deterministic mathematical optimization with a grounded explainable AI layer.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Primary Call-To-Action Button
    col_cta, _ = st.columns([1, 3])
    with col_cta:
        if st.button("Launch Route Optimizer →", use_container_width=True):
            on_navigate_optimizer()

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Calculate real dataset KPIs
    total_shipments = df_fleet["shipment_id"].nunique()
    total_routes = len(df_fleet)
    avg_transit = df_fleet["transit_time_days"].mean()
    
    # Evaluate default shipment 1 for representative optimal score
    first_shipment_data = df_fleet[df_fleet["shipment_id"] == "SHP-001"]
    default_opt = RouteOptimizer.evaluate_shipment_routes(first_shipment_data, WeightsConfig())
    best_score = default_opt.recommended_route.total_score if default_opt.recommended_route else 0.0

    # 4 Real KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="rw-kpi-card">
            <div class="rw-kpi-label">Active Trade Corridors</div>
            <div class="rw-kpi-value">{total_shipments}</div>
            <div class="rw-kpi-subtext">Global Origin-Destination pairs</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="rw-kpi-card">
            <div class="rw-kpi-label">Candidate Routes Evaluated</div>
            <div class="rw-kpi-value">{total_routes}</div>
            <div class="rw-kpi-subtext">4 distinct archetypes per lane</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="rw-kpi-card">
            <div class="rw-kpi-label">Mean Global Transit</div>
            <div class="rw-kpi-value">{avg_transit:.1f} <span style="font-size: 1rem; color: #93A4B8;">days</span></div>
            <div class="rw-kpi-subtext">Ocean, Direct & Multimodal mix</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="rw-kpi-card">
            <div class="rw-kpi-label">Benchmark Optimal Score</div>
            <div class="rw-kpi-value">{best_score:.4f}</div>
            <div class="rw-kpi-subtext">Under balanced baseline (40/30/30)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Visual Trade-off Landscape across the entire fleet
    st.markdown("<h3 style='font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>Global Route Trade-Off Landscape</h3>", unsafe_allow_html=True)

    scatter_fleet = px.scatter(
        df_fleet,
        x="transit_time_days",
        y="cost_usd",
        color="transport_mode",
        hover_name="route_name",
        hover_data=["origin", "destination", "cost_usd", "transit_time_days", "carrier"],
        labels={"transit_time_days": "Transit Time (Days)", "cost_usd": "Cost ($ USD)", "transport_mode": "Transport Mode"},
        color_discrete_map={
            "Ocean": "#3B82F6",
            "Ocean-Express": PRIMARY_TEAL,
            "Ocean-Resilient": "#10B981",
            "Multimodal / Air-Sea": "#F59E0B"
        }
    )
    layout = get_plotly_layout(title="Landed Cost vs. Transit Duration Across All 120 Route Candidates", height=400)
    scatter_fleet.update_layout(layout)
    st.plotly_chart(scatter_fleet, use_container_width=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Recent Shipments Summary Table
    st.markdown("<h3 style='font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>Trade Corridor Catalog Sample</h3>", unsafe_allow_html=True)
    
    sample_df = df_fleet.groupby("shipment_id").first().reset_index()
    display_sample = sample_df[["shipment_id", "origin", "destination", "corridor", "cargo_type", "urgency"]].head(8)
    
    st.dataframe(
        display_sample,
        column_config={
            "shipment_id": "Shipment ID",
            "origin": "Origin Port",
            "destination": "Destination Port",
            "corridor": "Global Corridor",
            "cargo_type": "Cargo Classification",
            "urgency": "Urgency SLA"
        },
        use_container_width=True,
        hide_index=True
    )
