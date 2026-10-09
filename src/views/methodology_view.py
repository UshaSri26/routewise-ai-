"""
Methodology View for RouteWise AI.
Complete technical and mathematical documentation of the decision framework,
formulas, constraints, and operational limitations.
"""

import streamlit as st
from src.ui_theme import PRIMARY_TEAL, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR, BG_CARD


def render_methodology():
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-size: 1.85rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.02em; margin-bottom: 0.25rem;">
            Methodology & Technical Architecture
        </h1>
        <p style="font-size: 0.95rem; color: #93A4B8; margin: 0;">
            Mathematical formulation, multi-objective scoring rules, and production constraints powering RouteWise AI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Problem Formulation
    st.markdown("""
    <div class="rw-card">
        <h3 style="font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 8px;">1. Problem Formulation</h3>
        <p style="color: #93A4B8; font-size: 0.9rem; line-height: 1.6;">
            Container routing is formulated as a <b>constrained Multi-Criteria Decision Analysis (MCDA)</b> problem. 
            For each shipment corridor with origin <i>O</i> and destination <i>D</i>, candidate routes <i>R = {r₁, r₂, ..., rₖ}</i> 
            are evaluated across three competing dimensions: Landed Freight Cost (<i>C</i>), Transit Velocity (<i>T</i>), and Composite Supply Chain Risk (<i>R</i>).
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Mathematical Scoring Model
    st.markdown("""
    <div class="rw-card">
        <h3 style="font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 12px;">2. Mathematical Scoring Model</h3>
        <div style="color: #93A4B8; font-size: 0.9rem; line-height: 1.6;">
            <p><b>Relative Min-Max Normalization:</b> Attributes are dynamically normalized within each candidate set to ensure scale independence:</p>
            <div style="background-color: #07111F; border: 1px solid #22344A; padding: 12px 16px; border-radius: 8px; font-family: monospace; color: #21D4C2; margin: 10px 0;">
                C_norm, i = (Cost_i - Cost_min) / max(Cost_max - Cost_min, ε)<br/>
                T_norm, i = (Time_i - Time_min) / max(Time_max - Time_min, ε)
            </div>
            <p style="font-size: 0.82rem; color: #64748B;">*where ε = 10⁻⁶ prevents division-by-zero when alternative options share identical values.</p>
            
            <p style="margin-top: 14px;"><b>Composite Risk Index:</b> Synthesizes multi-factor operational and geopolitical hazards:</p>
            <div style="background-color: #07111F; border: 1px solid #22344A; padding: 12px 16px; border-radius: 8px; font-family: monospace; color: #21D4C2; margin: 10px 0;">
                Risk_comp = 0.40 · P(delay) + 0.30 · (Congestion / 100) + 0.30 · (Geopolitical / 100)<br/>
                R_norm, i = (Risk_comp - Risk_min) / max(Risk_max - Risk_min, ε)
            </div>

            <p style="margin-top: 14px;"><b>Total Multi-Criteria Score:</b> Continuous minimization score (lower is better):</p>
            <div style="background-color: #07111F; border: 1px solid #22344A; padding: 12px 16px; border-radius: 8px; font-family: monospace; color: #21D4C2; margin: 10px 0;">
                Score_total = w_c · C_norm + w_t · T_norm + w_r · R_norm<br/>
                subject to: w_c + w_t + w_r = 1.0  (w_c, w_t, w_r ≥ 0)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Hard Constraints & Pareto Dominance
    st.markdown("""
    <div class="rw-card">
        <h3 style="font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 12px;">3. Hard Constraints & Pareto Dominance</h3>
        <div style="color: #93A4B8; font-size: 0.9rem; line-height: 1.6;">
            <p><b>Hard Constraint Elimination:</b> Routes breaching SLA thresholds (<i>Cost > Max Budget</i>, <i>Time > Max Days</i>, or <i>Risk > Cutoff</i>) are quarantined with explicit invalidation reasons.</p>
            <p><b>Graceful Infeasible Handling:</b> If all routes violate active constraints, the engine returns a <code>STATUS: INFEASIBLE_BEST_EFFORT</code> recommendation ranked by minimal penalty distance rather than crashing.</p>
            <p><b>Pareto Dominance:</b> Route <i>A</i> strictly dominates Route <i>B</i> (<i>A ≻ B</i>) if:</p>
            <div style="background-color: #07111F; border: 1px solid #22344A; padding: 12px 16px; border-radius: 8px; font-family: monospace; color: #21D4C2; margin: 10px 0;">
                Cost_A ≤ Cost_B  AND  Time_A ≤ Time_B  AND  Risk_A ≤ Risk_B<br/>
                AND (at least one strict inequality < exists)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Limitations & Production Roadmap
    st.markdown("""
    <div class="rw-card">
        <h3 style="font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 12px;">4. Real-World Limitations & Production Roadmap</h3>
        <ul style="color: #93A4B8; font-size: 0.9rem; line-height: 1.6; margin: 0; padding-left: 20px;">
            <li><b>Static vs. Live Telemetry:</b> The benchmark dataset uses simulated risk indices. Production implementation would ingest real-time AIS vessel coordinates (Spire / MarineTraffic) and meteorological feeds.</li>
            <li><b>Piecewise Non-Linear Demurrage:</b> Port storage and container detention incur steep non-linear penalties once free-time limits expire; future iterations will model piecewise demurrage step functions.</li>
            <li><b>Stochastic Optimization:</b> Maritime delays exhibit right-skewed log-normal tails. Upgrading from deterministic MCDA to Monte Carlo chance-constrained programming will model tail disruption risks.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
