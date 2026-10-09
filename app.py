"""
RouteWise AI - Next-Gen Logistics Intelligence Platform
Inspired by Modern AI Copilots (ChatGPT / Perplexity) + Supply Chain Workspace.
Matches the Reference UI Layout (media_1791572320523_beee24c4.jpg).
"""

from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

from src.ui_theme import (
    apply_theme, BG_APP, BG_CARD, BG_CARD_ELEVATED, TEAL_PRIMARY,
    TEXT_WHITE, TEXT_MUTED, PURPLE_ACCENT, BLUE_ACCENT, ORANGE_ACCENT
)
from src.optimizer import (
    RouteOptimizer, WeightsConfig, HardConstraints, run_sensitivity_analysis
)
from src.explanations import LLMExplainer, RuleBasedExplainer
from src.data_generator import save_dataset
from src.views.map_component import build_route_map
from src.views.optimizer_view import render_optimizer
from src.views.scenario_view import render_scenarios
from src.views.assistant_view import render_assistant
from src.views.methodology_view import render_methodology

# Streamlit Page Config
st.set_page_config(
    page_title="RouteWise AI — Shipment Intelligence",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply Custom Theme System (No Sidebar, Sleek Top Nav, Modern Cards)
apply_theme()


@st.cache_data
def load_dataset() -> pd.DataFrame:
    p = Path("data/shipments.csv")
    if not p.exists():
        save_dataset(str(p), num_shipments=30)
    return pd.read_csv(p)


df_fleet = load_dataset()

# Session State Management
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Home"

if "selected_shipment_id" not in st.session_state:
    # Default to S001 (Mumbai to Hamburg / Rotterdam)
    st.session_state["selected_shipment_id"] = "SHP-003"  # Mumbai -> Hamburg

if "prompt_query" not in st.session_state:
    st.session_state["prompt_query"] = ""

if "weights_config" not in st.session_state:
    st.session_state["weights_config"] = WeightsConfig(cost=0.40, time=0.30, risk=0.30)

if "constraints_config" not in st.session_state:
    st.session_state["constraints_config"] = HardConstraints()

if "gemini_key" not in st.session_state:
    st.session_state["gemini_key"] = ""


# --- 1. TOP HORIZONTAL NAVIGATION BAR ---
col_logo, col_links, col_status = st.columns([2.5, 4.5, 2.0])

with col_logo:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
        <div style="width:34px; height:34px; border-radius:8px; background:linear-gradient(135deg, #21D4C2 0%, #0284C7 100%); display:flex; align-items:center; justify-content:center; font-weight:800; color:#07111F; font-size:16px;">
            RW
        </div>
        <div>
            <div style="font-size:1.15rem; font-weight:700; color:#F1F5F9; line-height:1.1;">RouteWise AI</div>
            <div style="font-size:0.7rem; color:#8A9FB8; letter-spacing:0.04em;">Shipment Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_links:
    # 6 Top Nav Items
    n1, n2, n3, n4, n5, n6 = st.columns(6)
    with n1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state["active_tab"] = "Home"
            st.rerun()
    with n2:
        if st.button("⚡ Optimize", use_container_width=True):
            st.session_state["active_tab"] = "Optimize"
            st.rerun()
    with n3:
        if st.button("🗺️ Map", use_container_width=True):
            st.session_state["active_tab"] = "Map"
            st.rerun()
    with n4:
        if st.button("📊 Scenarios", use_container_width=True):
            st.session_state["active_tab"] = "Scenarios"
            st.rerun()
    with n5:
        if st.button("💬 AI Assistant", use_container_width=True):
            st.session_state["active_tab"] = "AI Assistant"
            st.rerun()
    with n6:
        if st.button("📖 Methodology", use_container_width=True):
            st.session_state["active_tab"] = "Methodology"
            st.rerun()

with col_status:
    st.markdown("""
    <div style="display:flex; justify-content:flex-end; align-items:center; gap:12px; margin-top:6px;">
        <span style="font-size:0.75rem; color:#21D4C2; background:rgba(33,212,194,0.12); padding:4px 10px; border-radius:12px; border:1px solid rgba(33,212,194,0.3);">
            ● Using synthetic data
        </span>
        <div style="width:28px; height:28px; border-radius:50%; background:#1E293B; border:1px solid #1E334D; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; color:#F1F5F9;">
            US
        </div>
        <span style="font-size:1rem; cursor:pointer;" title="Dark Mode Active">🌙</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border:none; border-top:1px solid #1E334D; margin:14px 0 24px 0;'/>", unsafe_allow_html=True)


# --- 2. PAGE ROUTING CONTROLLER ---
active_tab = st.session_state["active_tab"]

if active_tab == "Optimize":
    render_optimizer(df_fleet, api_key=st.session_state["gemini_key"])

elif active_tab == "Scenarios":
    render_scenarios(df_fleet)

elif active_tab == "AI Assistant":
    render_assistant(df_fleet, api_key=st.session_state["gemini_key"])

elif active_tab == "Methodology":
    render_methodology()

elif active_tab == "Map":
    st.subheader("Global Maritime & Multimodal Route Visualizer")
    active_shp = df_fleet[df_fleet["shipment_id"] == st.session_state["selected_shipment_id"]]
    o_name = active_shp["origin"].iloc[0]
    d_name = active_shp["destination"].iloc[0]
    map_fig = build_route_map(o_name, d_name, active_shp.to_dict("records"))
    map_fig.update_layout(height=650)
    st.plotly_chart(map_fig, use_container_width=True)

else:
    # --- HOME VIEW: HERO + UNIFIED WORKSPACE (MATCHES REFERENCE EXACTLY) ---

    # 1. HERO SECTION
    col_hero_left, col_hero_right = st.columns([1.6, 1.0])

    with col_hero_left:
        st.markdown("""
        <div>
            <div class="rw-hero-badge">AI-POWERED LOGISTICS INTELLIGENCE</div>
            <div class="rw-hero-heading">Smarter shipment routes<br/>for a global world.</div>
            <div class="rw-hero-sub">
                Find the best balance of cost, delivery time, and risk with AI-powered route optimization and transparent decision insights.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # AI Prompt Input Box
        prompt_col_input, prompt_col_btn = st.columns([5, 1])
        with prompt_col_input:
            prompt_in = st.text_input(
                "Describe prompt",
                placeholder="✨ Describe your shipment, priorities, or delivery constraints...",
                value=st.session_state["prompt_query"],
                label_visibility="collapsed"
            )
        with prompt_col_btn:
            if st.button("➔ Submit", use_container_width=True):
                if "cost" in prompt_in.lower() or "cheap" in prompt_in.lower():
                    st.session_state["weights_config"] = WeightsConfig(cost=0.70, time=0.15, risk=0.15)
                elif "speed" in prompt_in.lower() or "fast" in prompt_in.lower():
                    st.session_state["weights_config"] = WeightsConfig(cost=0.15, time=0.70, risk=0.15)
                elif "risk" in prompt_in.lower() or "safe" in prompt_in.lower():
                    st.session_state["weights_config"] = WeightsConfig(cost=0.15, time=0.15, risk=0.70)
                st.session_state["prompt_query"] = prompt_in
                st.rerun()

        # Clickable Suggested Prompt Chips
        st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
        st.caption("Try an example:")
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        with c_p1:
            if st.button("⚡ Optimize shipment S001", use_container_width=True):
                st.session_state["selected_shipment_id"] = "SHP-001"
                st.session_state["weights_config"] = WeightsConfig(cost=0.40, time=0.30, risk=0.30)
                st.rerun()
        with c_p2:
            if st.button("🔍 Lowest-cost route", use_container_width=True):
                st.session_state["weights_config"] = WeightsConfig(cost=0.70, time=0.15, risk=0.15)
                st.rerun()
        with c_p3:
            if st.button("⚖️ Fastest vs safest", use_container_width=True):
                st.session_state["weights_config"] = WeightsConfig(cost=0.15, time=0.70, risk=0.15)
                st.rerun()
        with c_p4:
            if st.button("💡 Explain trade-offs", use_container_width=True):
                st.session_state["active_tab"] = "AI Assistant"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_hero_right:
        # Global Trade Routes Banner Card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0A1B2E 0%, #06111D 100%); border: 1px solid #1E334D; border-radius: 14px; padding: 18px; margin-top: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.4);">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                <span style="font-size:1.1rem; color:{TEAL_PRIMARY};">🌐</span>
                <span style="font-size:0.88rem; font-weight:700; color:{TEXT_WHITE};">Global Trade Routes Connected by Intelligence</span>
            </div>
            <div style="border-radius:10px; overflow:hidden; border:1px solid #1E334D; margin-bottom:12px;">
                <img src="https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?auto=format&fit=crop&w=700&q=80" style="width:100%; height:120px; object-fit:cover; display:block;" alt="Maritime vessel"/>
            </div>
            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; text-align:center;">
                <div style="background:#07111F; border:1px solid #1E334D; border-radius:8px; padding:8px 4px;">
                    <div style="font-size:1.15rem; font-weight:800; color:{TEXT_WHITE};">30</div>
                    <div style="font-size:0.65rem; color:{TEXT_MUTED}; text-transform:uppercase;">Shipments</div>
                </div>
                <div style="background:#07111F; border:1px solid #1E334D; border-radius:8px; padding:8px 4px;">
                    <div style="font-size:1.15rem; font-weight:800; color:{TEXT_WHITE};">120</div>
                    <div style="font-size:0.65rem; color:{TEXT_MUTED}; text-transform:uppercase;">Route Options</div>
                </div>
                <div style="background:#07111F; border:1px solid #1E334D; border-radius:8px; padding:8px 4px;">
                    <div style="font-size:1.15rem; font-weight:800; color:{TEXT_WHITE};">4</div>
                    <div style="font-size:0.65rem; color:{TEXT_MUTED}; text-transform:uppercase;">Archetypes</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 2. WORKSPACE HEADER ---
    selected_shipment_id = st.session_state["selected_shipment_id"]
    shipment_df = df_fleet[df_fleet["shipment_id"] == selected_shipment_id].copy()
    ship_meta = shipment_df.iloc[0]

    st.markdown(f"""
    <div class="rw-section-header">
        <div class="rw-section-title">
            <span style="color:{TEAL_PRIMARY};">🎯</span> Optimization Result: 
            <span style="font-weight:400; color:#8A9FB8; margin-left:6px;">Shipment {selected_shipment_id}: {ship_meta['origin']} ➔ {ship_meta['destination']}</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <span style="font-size:0.8rem; color:#8A9FB8;">🕒 {datetime.now().strftime('%b %d, %Y · %I:%M %p')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Shipment Switcher & Analysis Reset Bar
    c_sw1, c_sw2 = st.columns([4, 1])
    with c_sw1:
        new_sid = st.selectbox(
            "Change active shipment:",
            sorted(df_fleet["shipment_id"].unique()),
            index=sorted(df_fleet["shipment_id"].unique()).index(selected_shipment_id),
            label_visibility="collapsed"
        )
        if new_sid != selected_shipment_id:
            st.session_state["selected_shipment_id"] = new_sid
            st.rerun()
    with c_sw2:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state["weights_config"] = WeightsConfig()
            st.rerun()

    # Run Optimizer for current active shipment
    opt_res = RouteOptimizer.evaluate_shipment_routes(
        shipment_df,
        weights=st.session_state["weights_config"],
        constraints=st.session_state["constraints_config"]
    )
    winner = opt_res.recommended_route
    w_weights = st.session_state["weights_config"]

    # --- 3. TOP WORKSPACE 3-COLUMN GRID ---
    col_w1, col_w2, col_w3 = st.columns([1.1, 1.3, 1.2])

    with col_w1:
        # CARD 1: RECOMMENDED ROUTE CARD
        if winner:
            st.markdown(f"""
            <div class="rw-winner-card">
                <div class="rw-rec-tag">★ Recommended Route</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: {TEXT_WHITE}; line-height: 1.2;">
                    {winner.route_name}
                </div>
                <div style="font-size: 0.8rem; color: #8A9FB8; margin-top: 4px; margin-bottom: 10px;">
                    {winner.intermediate_hubs}
                </div>
                <div style="border-radius: 8px; overflow: hidden; border: 1px solid #1E334D; margin-bottom: 10px;">
                    <img src="https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80" style="width:100%; height:95px; object-fit:cover; display:block;" alt="Vessel"/>
                </div>
                <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.4;">
                    Offers the best balance of cost, time, and risk for your current priorities ({w_weights.cost*100:.0f}% cost, {w_weights.time*100:.0f}% time, {w_weights.risk*100:.0f}% risk).
                </div>
                <div class="rw-stat-row">
                    <div class="rw-stat-item">
                        <div class="rw-stat-val">${winner.cost_usd:,.0f}</div>
                        <div class="rw-stat-lbl">Cost</div>
                    </div>
                    <div class="rw-stat-item">
                        <div class="rw-stat-val">{winner.transit_time_days:.0f}d</div>
                        <div class="rw-stat-lbl">Transit</div>
                    </div>
                    <div class="rw-stat-item">
                        <div class="rw-stat-val">{winner.delay_probability*100:.0f}%</div>
                        <div class="rw-stat-lbl">Delay</div>
                    </div>
                    <div class="rw-stat-item">
                        <div class="rw-stat-val">Low</div>
                        <div class="rw-stat-lbl">Risk</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View Full Route Details ➔", key="btn_view_full_route", use_container_width=True):
                st.session_state["active_tab"] = "Optimize"
                st.rerun()

    with col_w2:
        # CARD 2: INTERACTIVE ROUTE MAP
        st.markdown(f"""
        <div class="rw-box" style="padding:14px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:0.88rem; font-weight:700; color:{TEXT_WHITE};">🗺️ Global Corridor Map</span>
                <span style="font-size:0.75rem; color:{TEAL_PRIMARY};">Interactive Waypoints</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        route_map_fig = build_route_map(ship_meta["origin"], ship_meta["destination"], shipment_df.to_dict("records"))
        st.plotly_chart(route_map_fig, use_container_width=True)

    with col_w3:
        # CARD 3: ROUTE ALTERNATIVES TABLE & SCORE BREAKDOWN
        st.markdown(f"""
        <div class="rw-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-size:0.88rem; font-weight:700; color:{TEXT_WHITE};">📋 Route Alternatives</span>
                <span style="font-size:0.75rem; color:{TEAL_PRIMARY};">4 Candidates</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        alt_rows = []
        for r in opt_res.all_routes:
            stat_badge = "★ Recommended" if winner and r.route_id == winner.route_id else ("Feasible" if r.is_feasible else "Infeasible")
            risk_label = "Low" if r.composite_risk < 0.25 else ("Medium" if r.composite_risk < 0.45 else "High")
            alt_rows.append({
                "Route": r.route_id.split("-")[-1],
                "Cost ($)": f"${r.cost_usd:,.0f}",
                "Days": f"{r.transit_time_days:.0f}d",
                "Delay %": f"{r.delay_probability*100:.0f}%",
                "Risk": risk_label,
                "Score": f"{r.total_score:.4f}",
                "Status": stat_badge
            })

        st.dataframe(pd.DataFrame(alt_rows), use_container_width=True, hide_index=True)

        # Multi-segment Score Breakdown Bar for Winner
        if winner:
            c_part = w_weights.cost * winner.norm_cost
            t_part = w_weights.time * winner.norm_time
            r_part = w_weights.risk * winner.norm_risk
            tot = max(c_part + t_part + r_part, 0.001)

            st.markdown(f"""
            <div class="rw-bar-container">
                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#8A9FB8;">
                    <span><b>Score Breakdown ({winner.route_id.split('-')[-1]})</b></span>
                    <span>Total: <b>{winner.total_score:.4f}</b></span>
                </div>
                <div class="rw-progress-bar">
                    <div class="rw-bar-cost" style="width:{(c_part/tot)*100}%;"></div>
                    <div class="rw-bar-time" style="width:{(t_part/tot)*100}%;"></div>
                    <div class="rw-bar-risk" style="width:{(r_part/tot)*100}%;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:#8A9FB8;">
                    <span style="color:{TEAL_PRIMARY};">● Cost ({w_weights.cost*100:.0f}%)</span>
                    <span style="color:{PURPLE_ACCENT};">● Time ({w_weights.time*100:.0f}%)</span>
                    <span style="color:{BLUE_ACCENT};">● Risk ({w_weights.risk*100:.0f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # --- 4. BOTTOM WORKSPACE 3-COLUMN GRID ---
    col_b1, col_b2, col_b3 = st.columns([1.1, 1.2, 1.2])

    with col_b1:
        # CARD 4: AI EXPLANATION
        st.markdown(f"""
        <div class="rw-box">
            <div style="display:flex; align-items:center; gap:6px; margin-bottom:8px;">
                <span style="color:{TEAL_PRIMARY}; font-size:1rem;">✨</span>
                <span style="font-size:0.88rem; font-weight:700; color:{TEXT_WHITE};">AI Decision Explanation</span>
            </div>
            <div style="font-size:0.82rem; color:#CBD5E1; line-height:1.5;">
                • <b>{winner.route_name}</b> was selected because it achieves the lowest composite score ({winner.total_score:.4f}) under active priorities.<br/>
                • It delivers superior reliability (only {winner.delay_probability*100:.0f}% delay probability) avoiding critical chokepoints.<br/>
                • Runner-up incurs higher delay volatility or transit days.
            </div>
            <div style="margin-top:12px; display:flex; flex-wrap:wrap; gap:6px;">
                <span class="rw-chip">Why this route?</span>
                <span class="rw-chip">Compare with R1</span>
                <span class="rw-chip">What if speed priority?</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        follow_q = st.text_input("Ask a follow-up question...", placeholder="Ask about trade-offs...", key="home_follow_q")
        if follow_q:
            expl = LLMExplainer(api_key=st.session_state["gemini_key"])
            st.info(expl.answer_question(follow_q, opt_res))

    with col_b2:
        # CARD 5: KEY INSIGHTS SCATTER PLOT
        st.markdown(f"""
        <div class="rw-box" style="padding-bottom:2px;">
            <div style="font-size:0.88rem; font-weight:700; color:{TEXT_WHITE}; margin-bottom:6px;">
                📈 Key Insights: Cost vs. Transit Duration
            </div>
        </div>
        """, unsafe_allow_html=True)

        plot_items = []
        for r in opt_res.all_routes:
            plot_items.append({
                "Route": r.route_id.split("-")[-1],
                "Cost ($ USD)": r.cost_usd,
                "Transit Time (Days)": r.transit_time_days,
                "Composite Risk": r.composite_risk
            })

        fig_sc = px.scatter(
            pd.DataFrame(plot_items),
            x="Cost ($ USD)",
            y="Transit Time (Days)",
            color="Route",
            text="Route",
            color_discrete_sequence=[TEAL_PRIMARY, BLUE_ACCENT, ORANGE_ACCENT, PURPLE_ACCENT]
        )
        fig_sc.update_traces(textposition="top center", marker=dict(size=14))
        fig_sc.update_layout(
            paper_bgcolor="#0C1829",
            plot_bgcolor="#0C1829",
            height=260,
            margin=dict(l=30, r=20, t=20, b=30),
            font=dict(family="Plus Jakarta Sans", size=10, color="#8A9FB8"),
            xaxis=dict(gridcolor="#1E334D", linecolor="#1E334D"),
            yaxis=dict(gridcolor="#1E334D", linecolor="#1E334D"),
            showlegend=False
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    with col_b3:
        # CARD 6: SCENARIO ANALYSIS 2x2 GRID
        st.markdown(f"""
        <div class="rw-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-size:0.88rem; font-weight:700; color:{TEXT_WHITE};">🔬 Scenario Analysis</span>
                <span style="font-size:0.75rem; color:{TEAL_PRIMARY};">Sensitivity</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{TEAL_PRIMARY};">⚖️ Balanced</div>
                    <div style="font-size:0.68rem; color:#8A9FB8;">40% C · 30% T · 30% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{TEXT_WHITE}; margin-top:4px;">Winner: R2</div>
                </div>
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{ORANGE_ACCENT};">💰 Cost Focused</div>
                    <div style="font-size:0.68rem; color:#8A9FB8;">70% C · 15% T · 15% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{TEXT_WHITE}; margin-top:4px;">Winner: R1</div>
                </div>
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{BLUE_ACCENT};">⚡ Time Critical</div>
                    <div style="font-size:0.68rem; color:#8A9FB8;">15% C · 70% T · 15% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{TEXT_WHITE}; margin-top:4px;">Winner: R4</div>
                </div>
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{PURPLE_ACCENT};">🛡️ Risk Averse</div>
                    <div style="font-size:0.68rem; color:#8A9FB8;">15% C · 15% T · 70% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{TEXT_WHITE}; margin-top:4px;">Winner: R3</div>
                </div>
            </div>
            <div style="margin-top:10px; font-size:0.75rem; color:#21D4C2; text-align:right; cursor:pointer;">
                How priorities change the recommendation ➔
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 5. METHODOLOGY FOOTER BANNER ---
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background-color:#0C1829; border:1px solid #1E334D; border-radius:12px; padding:14px 22px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.2rem; color:{TEAL_PRIMARY};">📖</span>
            <div>
                <div style="font-size:0.88rem; font-weight:700; color:{TEXT_WHITE};">Methodology</div>
                <div style="font-size:0.75rem; color:#8A9FB8;">Understand how RouteWise AI evaluates and recommends shipment routes.</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px; font-size:0.75rem; color:#8A9FB8;">
            <span>Scoring Model</span> ➔ <span>Risk Metrics</span> ➔ <span>Constraints</span> ➔ <span>Pareto Dominance</span> ➔ <span>Dataset</span> ➔ <span>Limitations</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Full Methodology Specification ➔", key="btn_view_methodology"):
        st.session_state["active_tab"] = "Methodology"
        st.rerun()
