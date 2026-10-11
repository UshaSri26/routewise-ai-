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
            Small-shipment route choice is formulated as a <b>constrained Multi-Criteria Decision Analysis (MCDA)</b> problem.
            For each shipment corridor with origin <i>O</i> and destination <i>D</i>, candidate routes <i>R = {r₁, r₂, ..., rₖ}</i> 
            are evaluated across three competing dimensions: indicative freight cost (<i>C</i>), transit time (<i>T</i>), and a synthetic composite risk index (<i>R</i>). This demo does not optimize validated total landed cost.
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
            <p style="font-size:0.82rem; color:#64748B;">*where ε = 10⁻⁶ stabilizes normalization; if all candidates share an identical value for a metric, that normalized metric is zero for all.</p>
            
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
            <p>The default weights are 40% cost, 30% time, and 30% risk. Scenario analysis also evaluates cost-focused (70/15/15), time-critical (15/70/15), and risk-averse (15/15/70) profiles.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Hard Constraints & Pareto Dominance
    st.markdown("""
    <div class="rw-card">
        <h3 style="font-size: 1.15rem; font-weight: 600; color: #F1F5F9; margin-bottom: 12px;">3. Hard Constraints & Pareto Dominance</h3>
        <div style="color: #93A4B8; font-size: 0.9rem; line-height: 1.6;">
            <p><b>Hard Constraint Evaluation:</b> Routes breaching user thresholds (<i>Cost > Max Budget</i>, <i>Time > Max Days</i>, or <i>Risk > Cutoff</i>) are marked infeasible with explicit reasons and rank below feasible routes.</p>
            <p><b>Graceful Infeasible Handling:</b> If all routes violate active constraints, the engine returns a clearly flagged best-effort recommendation, preferring the fewest violated limits and then the lowest weighted score.</p>
            <p><b>Pareto Dominance:</b> Route <i>A</i> strictly dominates Route <i>B</i> (<i>A ≻ B</i>) if:</p>
            <div style="background-color: #07111F; border: 1px solid #22344A; padding: 12px 16px; border-radius: 8px; font-family: monospace; color: #21D4C2; margin: 10px 0;">
                Cost_A ≤ Cost_B  AND  Time_A ≤ Time_B  AND  Risk_A ≤ Risk_B<br/>
                    AND (at least one strict inequality exists)
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
            <li><b>Freight estimate limitations:</b> Current formulas model a 10 kg domestic carton or a 15 kg / 0.1 CBM international sample. Replace them with carrier quotes and package-specific surcharges before operational use.</li>
            <li><b>Uncalibrated risk:</b> Delay, congestion and geopolitical inputs are synthetic point estimates, not measured or forecast probabilities. Validate them against historical outcomes before operational use.</li>
            <li><b>Expected cost and map:</b> Expected landed cost is diagnostic only and does not affect ranking; the map curves are schematic, not live carrier routes.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
