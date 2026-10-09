"""
Scenario Analysis View for RouteWise AI.
Multi-scenario sensitivity matrix evaluating decision shifts across operational priority profiles.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.ui_theme import (
    PRIMARY_TEAL, SECONDARY_TEAL, TEXT_PRIMARY, TEXT_SECONDARY,
    BORDER_COLOR, BG_CARD, COLOR_WARNING, get_plotly_layout
)
from src.optimizer import RouteOptimizer, WeightsConfig, HardConstraints, run_sensitivity_analysis


def render_scenarios(df_fleet: pd.DataFrame):
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.02em; margin-bottom: 0.25rem;">
            Scenario & Sensitivity Analysis
        </h1>
        <p style="font-size: 0.95rem; color: #93A4B8; margin: 0;">
            Stress-test routing recommendations across divergent strategic priorities: Balanced, Cost-Focused, Time-Critical, and Risk-Averse.
        </p>
    </div>
    """, unsafe_allow_html=True)

    shipment_ids = sorted(df_fleet["shipment_id"].unique())
    selected_id = st.selectbox(
        "Select Shipment for Scenario Simulation:",
        shipment_ids,
        index=0,
        format_func=lambda s: f"{s} — {df_fleet[df_fleet['shipment_id'] == s]['origin'].iloc[0]} ➔ {df_fleet[df_fleet['shipment_id'] == s]['destination'].iloc[0]}"
    )

    shipment_df = df_fleet[df_fleet["shipment_id"] == selected_id].copy()

    # Re-run sensitivity dynamically via optimizer backend
    sens_df = run_sensitivity_analysis(shipment_df)

    # Check if winning route pivots across profiles
    unique_winners = sens_df["Recommended Route"].nunique()
    pivot_msg = (
        f"**Decision Volatility:** Routing choice **pivots across {unique_winners} distinct options** depending on whether time, cost, or geopolitical risk is prioritized."
        if unique_winners > 1 else
        "**Decision Stability:** A single dominant route wins across all priority profiles due to overall superior trade-off metrics."
    )

    st.markdown(f"""
    <div class="rw-card" style="padding: 14px 20px; border-left: 4px solid {PRIMARY_TEAL}; margin-bottom: 1.5rem;">
        <span style="font-size: 0.9rem; color: #F1F5F9;">{pivot_msg}</span>
    </div>
    """, unsafe_allow_html=True)

    # Sensitivity Results Table
    st.markdown("<h3 style='font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 0.75rem;'>Priority Profile Sensitivity Table</h3>", unsafe_allow_html=True)
    st.dataframe(
        sens_df,
        column_config={
            "Profile": "Operational Profile",
            "Recommended Route": "Winning Route Archetype",
            "Route ID": "Route ID",
            "Carrier": "Lead Carrier",
            "Cost ($)": st.column_config.NumberColumn("Freight Cost", format="$%.2f"),
            "Transit Time (days)": st.column_config.NumberColumn("Transit Window", format="%.1f days"),
            "Composite Risk": st.column_config.NumberColumn("Risk Index", format="%.3f"),
            "Score": st.column_config.NumberColumn("Weighted Score", format="%.4f")
        },
        use_container_width=True,
        hide_index=True
    )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # Comparative Visualization across Scenarios
    c_s1, c_s2 = st.columns(2)

    with c_s1:
        fig_score = px.bar(
            sens_df,
            x="Profile",
            y="Score",
            color="Recommended Route",
            title="Composite Optimization Score per Scenario (Lower is Better)",
            color_discrete_sequence=[PRIMARY_TEAL, "#3B82F6", "#F59E0B", "#10B981"]
        )
        layout_sc = get_plotly_layout(title="Composite Optimization Score per Scenario")
        fig_score.update_layout(layout_sc)
        st.plotly_chart(fig_score, use_container_width=True)

    with c_s2:
        fig_cost_time = px.scatter(
            sens_df,
            x="Transit Time (days)",
            y="Cost ($)",
            color="Profile",
            size=[24, 24, 24, 24],
            hover_name="Recommended Route",
            title="Winning Solution Space: Cost vs. Transit Time Shifts",
            color_discrete_sequence=[PRIMARY_TEAL, "#F59E0B", "#EF4444", "#3B82F6"]
        )
        layout_ct = get_plotly_layout(title="Winning Solution Space: Cost vs. Transit Time")
        fig_cost_time.update_layout(layout_ct)
        st.plotly_chart(fig_cost_time, use_container_width=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Detailed Analytical Takeaway
    st.markdown("""
    <div class="rw-card" style="padding: 18px;">
        <h4 style="font-size: 0.95rem; font-weight: 600; color: #F1F5F9; margin-bottom: 8px;">Strategic Takeaways from Sensitivity Analysis:</h4>
        <ul style="color: #93A4B8; font-size: 0.88rem; line-height: 1.6; margin: 0; padding-left: 20px;">
            <li><b>Cost-Focused Profile (70/15/15):</b> Selects high-capacity standard ocean routing; absorbs higher intermediate hub congestion and 7–10 additional days in return for maximum freight dollar efficiency.</li>
            <li><b>Time-Critical Profile (15/70/15):</b> Pivots toward direct express or air-sea multimodal corridors, trading freight rate premiums for emergency delivery SLA compliance.</li>
            <li><b>Risk-Averse Profile (15/15/70):</b> Disqualifies routes passing through volatile chokepoints (e.g. Red Sea / Malacca bottlenecks), selecting resilient bypass corridors (Cape of Good Hope) with minimum delay probability variance.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
