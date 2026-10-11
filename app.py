"""
RouteWise AI - Next-Gen Logistics Intelligence Platform
Inspired by Modern AI Copilots (ChatGPT / Perplexity) + Supply Chain Workspace.
Matches the Reference UI Layout (media_1791572320523_beee24c4.jpg).
Fully Functional Submit Button, Custom Corridors, Dynamic Offline Q&A, and Theme Toggle.
"""

from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

from src.ui_theme import (
    apply_theme, get_plotly_layout, DARK_PALETTE, LIGHT_PALETTE,
    PURPLE_ACCENT, BLUE_ACCENT, ORANGE_ACCENT
)
from src.optimizer import (
    RouteOptimizer, WeightsConfig, HardConstraints, run_sensitivity_analysis
)
from src.explanations import LLMExplainer, RuleBasedExplainer
from src.data_generator import save_dataset
from src.custom_shipment import parse_and_generate_corridor
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

# Initialize Session State
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Home"

if "selected_shipment_id" not in st.session_state:
    st.session_state["selected_shipment_id"] = "SHP-001"

if "custom_corridor_df" not in st.session_state:
    st.session_state["custom_corridor_df"] = None

if "ai_feedback_msg" not in st.session_state:
    st.session_state["ai_feedback_msg"] = None

if "prompt_query" not in st.session_state:
    st.session_state["prompt_query"] = ""

if "weights_config" not in st.session_state:
    st.session_state["weights_config"] = WeightsConfig(cost=0.40, time=0.30, risk=0.30)

if "constraints_config" not in st.session_state:
    st.session_state["constraints_config"] = HardConstraints()

if "gemini_key" not in st.session_state:
    st.session_state["gemini_key"] = ""

if "qna_response" not in st.session_state:
    st.session_state["qna_response"] = None

# Apply Selected Theme (Dark Navy/Teal vs Light Executive SaaS)
apply_theme(mode=st.session_state["theme_mode"])
pal = DARK_PALETTE if st.session_state["theme_mode"] == "dark" else LIGHT_PALETTE


@st.cache_data
def load_dataset() -> pd.DataFrame:
    p = Path("data/shipments.csv")
    if not p.exists():
        save_dataset(str(p), num_shipments=30)
    return pd.read_csv(p)


df_fleet = load_dataset()

# --- 1. TOP HORIZONTAL NAVIGATION BAR ---
col_logo, col_links, col_status = st.columns([2.2, 5.0, 2.8])

with col_logo:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
        <div style="width:34px; height:34px; border-radius:8px; background:linear-gradient(135deg, {pal['primary']} 0%, #0284C7 100%); display:flex; align-items:center; justify-content:center; font-weight:800; color:#07111F; font-size:16px;">
            RW
        </div>
        <div>
            <div style="font-size:1.15rem; font-weight:700; color:{pal['text_primary']}; line-height:1.1;">RouteWise AI</div>
            <div style="font-size:0.7rem; color:{pal['text_muted']}; letter-spacing:0.04em;">Shipment Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_links:
    # 6 Top Nav Items with full clean labels
    nav_tabs = ["Home", "Optimize", "Map", "Scenarios", "AI Assistant", "Methodology"]
    selected_nav = st.radio(
        "Navigation",
        nav_tabs,
        index=nav_tabs.index(st.session_state["active_tab"]) if st.session_state["active_tab"] in nav_tabs else 0,
        horizontal=True,
        label_visibility="collapsed"
    )
    if selected_nav != st.session_state["active_tab"]:
        st.session_state["active_tab"] = selected_nav
        st.rerun()

with col_status:
    c_stat1, c_theme_toggle = st.columns([2, 1])
    with c_stat1:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
            <span style="font-size:0.72rem; color:{pal['primary']}; background:rgba(33,212,194,0.12); padding:3px 8px; border-radius:12px; border:1px solid rgba(33,212,194,0.3);">
                ● Using synthetic data
            </span>
            <div style="width:26px; height:26px; border-radius:50%; background:#1E293B; border:1px solid {pal['border']}; display:flex; align-items:center; justify-content:center; font-size:0.72rem; font-weight:700; color:#F1F5F9;">
                US
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c_theme_toggle:
        theme_label = "☀️ Light" if st.session_state["theme_mode"] == "dark" else "🌙 Dark"
        if st.button(theme_label, use_container_width=True):
            st.session_state["theme_mode"] = "light" if st.session_state["theme_mode"] == "dark" else "dark"
            st.rerun()

st.markdown(f"<hr style='border:none; border-top:1px solid {pal['border']}; margin:10px 0 20px 0;'/>", unsafe_allow_html=True)


# --- 2. ROUTE DETERMINATION & PAGE RENDERING ---
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
    active_shp = st.session_state["custom_corridor_df"] if st.session_state["custom_corridor_df"] is not None else df_fleet[df_fleet["shipment_id"] == st.session_state["selected_shipment_id"]]
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
        st.markdown(f"""
        <div>
            <div class="rw-hero-badge">AI-POWERED LOGISTICS INTELLIGENCE</div>
            <div class="rw-hero-heading" style="color:{pal['text_primary']};">Smarter shipment routes<br/>for a global world.</div>
            <div class="rw-hero-sub" style="color:{pal['text_muted']};">
                Find the best balance of cost, delivery time, and risk with AI-powered route optimization and transparent decision insights.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # AI Prompt Composer Form (Guarantees working submit on Enter or Button Click)
        with st.form("hero_prompt_form", clear_on_submit=False):
            c_input, c_btn = st.columns([5, 1.2])
            with c_input:
                user_prompt = st.text_input(
                    "Shipment prompt",
                    placeholder="✨ Describe your shipment, priorities, or delivery constraints (e.g. ship package from Hyderabad to Warangal with less time)...",
                    value=st.session_state["prompt_query"],
                    label_visibility="collapsed"
                )
            with c_btn:
                submitted = st.form_submit_button("➔ Submit", use_container_width=True)

            if submitted and user_prompt:
                st.session_state["prompt_query"] = user_prompt
                # Parse natural language query dynamically
                parsed_df, parsed_weights, parsed_constraints, feedback_msg = parse_and_generate_corridor(user_prompt, df_fleet)
                st.session_state["custom_corridor_df"] = parsed_df
                st.session_state["weights_config"] = parsed_weights
                st.session_state["hard_constraints"] = parsed_constraints
                st.session_state["ai_feedback_msg"] = feedback_msg
                st.session_state["selected_shipment_id"] = parsed_df["shipment_id"].iloc[0]
                st.rerun()

        # Clickable Suggested Prompt Chips
        st.caption("Try an example:")
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        with c_p1:
            if st.button("⚡ Optimize shipment S001", use_container_width=True):
                st.session_state["selected_shipment_id"] = "SHP-001"
                st.session_state["custom_corridor_df"] = None
                st.session_state["weights_config"] = WeightsConfig(cost=0.40, time=0.30, risk=0.30)
                st.session_state["ai_feedback_msg"] = "⚡ Loaded benchmark corridor **SHP-001 (Hyderabad ➔ Warangal)** with Balanced (40/30/30) weights."
                st.rerun()
        with c_p2:
            if st.button("🔍 Lowest-cost route", use_container_width=True):
                st.session_state["weights_config"] = WeightsConfig(cost=0.70, time=0.15, risk=0.15)
                st.session_state["ai_feedback_msg"] = "💰 Applied Cost-Focused Priority (70% Cost) across route alternatives."
                st.rerun()
        with c_p3:
            if st.button("⚖️ Fastest vs safest", use_container_width=True):
                st.session_state["weights_config"] = WeightsConfig(cost=0.15, time=0.70, risk=0.15)
                st.session_state["ai_feedback_msg"] = "⚡ Applied Time-Critical Priority (70% Time) to highlight speed trade-offs."
                st.rerun()
        with c_p4:
            if st.button("💡 Explain trade-offs", use_container_width=True):
                st.session_state["qna_response"] = "tradeoffs"
                st.rerun()

    with col_hero_right:
        # Global Trade Routes Banner Card
        st.markdown(f"""
        <div style="background: {pal['bg_card_elevated']}; border: 1px solid {pal['border']}; border-radius: 14px; padding: 18px; margin-top: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                <span style="font-size:1.1rem; color:{pal['primary']};">🌐</span>
                <span style="font-size:0.88rem; font-weight:700; color:{pal['text_primary']};">Global Trade Routes Connected by Intelligence</span>
            </div>
            <div style="border-radius:10px; overflow:hidden; border:1px solid {pal['border']}; margin-bottom:12px;">
                <img src="https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?auto=format&fit=crop&w=700&q=80" style="width:100%; height:120px; object-fit:cover; display:block;" alt="Maritime vessel"/>
            </div>
            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; text-align:center;">
                <div style="background:{pal['bg_app']}; border:1px solid {pal['border']}; border-radius:8px; padding:8px 4px;">
                    <div style="font-size:1.15rem; font-weight:800; color:{pal['text_primary']};">30</div>
                    <div style="font-size:0.65rem; color:{pal['text_muted']}; text-transform:uppercase;">Shipments</div>
                </div>
                <div style="background:{pal['bg_app']}; border:1px solid {pal['border']}; border-radius:8px; padding:8px 4px;">
                    <div style="font-size:1.15rem; font-weight:800; color:{pal['text_primary']};">120</div>
                    <div style="font-size:0.65rem; color:{pal['text_muted']}; text-transform:uppercase;">Route Options</div>
                </div>
                <div style="background:{pal['bg_app']}; border:1px solid {pal['border']}; border-radius:8px; padding:8px 4px;">
                    <div style="font-size:1.15rem; font-weight:800; color:{pal['text_primary']};">4</div>
                    <div style="font-size:0.65rem; color:{pal['text_muted']}; text-transform:uppercase;">Archetypes</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Feedback Toast if user executed natural language prompt
    if st.session_state["ai_feedback_msg"]:
        st.markdown(f"""
        <div style="background: rgba(33, 212, 194, 0.12); border: 1px solid {pal['primary']}; border-radius: 8px; padding: 10px 16px; margin: 16px 0; color: {pal['text_primary']}; font-size: 0.9rem;">
            {st.session_state["ai_feedback_msg"]}
        </div>
        """, unsafe_allow_html=True)

    # --- 2. WORKSPACE HEADER ---
    if st.session_state["custom_corridor_df"] is not None:
        shipment_df = st.session_state["custom_corridor_df"]
        selected_shipment_id = shipment_df["shipment_id"].iloc[0]
    else:
        selected_shipment_id = st.session_state["selected_shipment_id"]
        shipment_df = df_fleet[df_fleet["shipment_id"] == selected_shipment_id].copy()

    ship_meta = shipment_df.iloc[0]

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:24px; margin-bottom:14px; padding-bottom:8px; border-bottom:1px solid {pal['border']};">
        <div style="font-size:1.15rem; font-weight:700; color:{pal['text_primary']}; display:flex; align-items:center; gap:8px;">
            <span style="color:{pal['primary']};">🎯</span> Optimization Result: 
            <span style="font-weight:400; color:{pal['text_muted']}; margin-left:6px;">Shipment {selected_shipment_id}: {ship_meta['origin']} ➔ {ship_meta['destination']}</span>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <span style="font-size:0.8rem; color:{pal['text_muted']};">🕒 {datetime.now().strftime('%b %d, %Y · %I:%M %p')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Switcher & Reset
    c_sw1, c_sw2 = st.columns([4, 1])
    with c_sw1:
        shipment_options = sorted(df_fleet["shipment_id"].unique())
        cur_idx = shipment_options.index(selected_shipment_id) if selected_shipment_id in shipment_options else 0
        new_sid = st.selectbox(
            "Change active benchmark shipment:",
            shipment_options,
            index=cur_idx,
            label_visibility="collapsed"
        )
        if new_sid != selected_shipment_id and st.session_state["custom_corridor_df"] is None:
            st.session_state["selected_shipment_id"] = new_sid
            st.rerun()
    with c_sw2:
        if st.button("🔄 Reset / Default", use_container_width=True):
            st.session_state["custom_corridor_df"] = None
            st.session_state["selected_shipment_id"] = "SHP-001"
            st.session_state["weights_config"] = WeightsConfig()
            st.session_state["ai_feedback_msg"] = None
            st.session_state["qna_response"] = None
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
                <div style="font-size: 1.25rem; font-weight: 800; color: {pal['text_primary']}; line-height: 1.2;">
                    {winner.route_name}
                </div>
                <div style="font-size: 0.8rem; color: {pal['text_muted']}; margin-top: 4px; margin-bottom: 10px;">
                    {winner.intermediate_hubs}
                </div>
                <div style="border-radius: 8px; overflow: hidden; border: 1px solid {pal['border']}; margin-bottom: 10px;">
                    <img src="https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80" style="width:100%; height:95px; object-fit:cover; display:block;" alt="Vessel"/>
                </div>
                <div style="font-size: 0.82rem; color: {pal['text_primary']}; line-height: 1.4;">
                    Offers optimal balance of cost, transit velocity, and reliability under active priorities ({w_weights.cost*100:.0f}% cost, {w_weights.time*100:.0f}% time, {w_weights.risk*100:.0f}% risk).
                </div>
                <div class="rw-stat-row">
                    <div class="rw-stat-item">
                        <div class="rw-stat-val" style="color:{pal['text_primary']};">${winner.cost_usd:,.0f}</div>
                        <div class="rw-stat-lbl">Cost</div>
                    </div>
                    <div class="rw-stat-item">
                        <div class="rw-stat-val" style="color:{pal['text_primary']};">{winner.transit_time_days:.1f}d</div>
                        <div class="rw-stat-lbl">Transit</div>
                    </div>
                    <div class="rw-stat-item">
                        <div class="rw-stat-val" style="color:{pal['text_primary']};">{winner.delay_probability*100:.0f}%</div>
                        <div class="rw-stat-lbl">Delay</div>
                    </div>
                    <div class="rw-stat-item">
                        <div class="rw-stat-val" style="color:{pal['text_primary']};">Low</div>
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
                <span style="font-size:0.88rem; font-weight:700; color:{pal['text_primary']};">🗺️ Global Corridor Map</span>
                <span style="font-size:0.75rem; color:{pal['primary']};">Interactive Waypoints</span>
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
                <span style="font-size:0.88rem; font-weight:700; color:{pal['text_primary']};">📋 Route Alternatives</span>
                <span style="font-size:0.75rem; color:{pal['primary']};">4 Candidates</span>
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
                "Days": f"{r.transit_time_days:.1f}d",
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
            <div style="background:{pal['stat_row_bg']}; border:1px solid {pal['border']}; border-radius:8px; padding:12px; margin-top:12px;">
                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:{pal['text_muted']};">
                    <span><b>Score Breakdown ({winner.route_id.split('-')[-1]})</b></span>
                    <span>Total: <b>{winner.total_score:.4f}</b></span>
                </div>
                <div style="display:flex; height:10px; border-radius:5px; overflow:hidden; margin:6px 0;">
                    <div style="background-color:{pal['primary']}; width:{(c_part/tot)*100}%;"></div>
                    <div style="background-color:{PURPLE_ACCENT}; width:{(t_part/tot)*100}%;"></div>
                    <div style="background-color:{BLUE_ACCENT}; width:{(r_part/tot)*100}%;"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:{pal['text_muted']};">
                    <span style="color:{pal['primary']};">● Cost ({w_weights.cost*100:.0f}%)</span>
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
                <span style="color:{pal['primary']}; font-size:1rem;">✨</span>
                <span style="font-size:0.88rem; font-weight:700; color:{pal['text_primary']};">AI Decision Explanation</span>
            </div>
            <div style="font-size:0.82rem; color:{pal['text_primary']}; line-height:1.5;">
                • <b>{winner.route_name}</b> achieves the optimal score ({winner.total_score:.4f}) balancing cost, velocity, and reliability.<br/>
                • Demonstrates lower operational risk ({winner.delay_probability*100:.0f}% delay probability) bypassing congested transshipment bottlenecks.<br/>
                • Competing options trade velocity for freight rate premiums.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Follow-up interactive Q&A form (Always works with offline numbers)
        with st.form("qna_followup_form", clear_on_submit=False):
            f_col_in, f_col_btn = st.columns([4, 1])
            with f_col_in:
                follow_q = st.text_input("Ask a follow-up question...", placeholder="e.g. what are the tradeoffs, or why was this route chosen?", label_visibility="collapsed")
            with f_col_btn:
                f_submit = st.form_submit_button("Ask ➔", use_container_width=True)

            if f_submit and follow_q:
                st.session_state["qna_response"] = follow_q

        if st.session_state["qna_response"]:
            expl = LLMExplainer(api_key=st.session_state["gemini_key"])
            ans = expl.answer_question(st.session_state["qna_response"], opt_res)
            st.info(ans)

    with col_b2:
        # CARD 5: KEY INSIGHTS SCATTER PLOT
        st.markdown(f"""
        <div class="rw-box" style="padding-bottom:2px;">
            <div style="font-size:0.88rem; font-weight:700; color:{pal['text_primary']}; margin-bottom:6px;">
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
            color_discrete_sequence=[pal['primary'], BLUE_ACCENT, ORANGE_ACCENT, PURPLE_ACCENT]
        )
        fig_sc.update_traces(textposition="top center", marker=dict(size=14))
        layout_sc = get_plotly_layout(theme_mode=st.session_state["theme_mode"], height=260)
        fig_sc.update_layout(layout_sc)
        fig_sc.update_layout(showlegend=False)
        st.plotly_chart(fig_sc, use_container_width=True)

    with col_b3:
        # CARD 6: SCENARIO ANALYSIS 2x2 GRID
        st.markdown(f"""
        <div class="rw-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-size:0.88rem; font-weight:700; color:{pal['text_primary']};">🔬 Scenario Analysis</span>
                <span style="font-size:0.75rem; color:{pal['primary']};">Sensitivity</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{pal['primary']};">⚖️ Balanced</div>
                    <div style="font-size:0.68rem; color:{pal['text_muted']};">40% C · 30% T · 30% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{pal['text_primary']}; margin-top:4px;">Winner: R2</div>
                </div>
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{ORANGE_ACCENT};">💰 Cost Focused</div>
                    <div style="font-size:0.68rem; color:{pal['text_muted']};">70% C · 15% T · 15% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{pal['text_primary']}; margin-top:4px;">Winner: R1</div>
                </div>
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{BLUE_ACCENT};">⚡ Time Critical</div>
                    <div style="font-size:0.68rem; color:{pal['text_muted']};">15% C · 70% T · 15% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{pal['text_primary']}; margin-top:4px;">Winner: R4</div>
                </div>
                <div class="rw-scenario-card">
                    <div style="font-size:0.75rem; font-weight:700; color:{PURPLE_ACCENT};">🛡️ Risk Averse</div>
                    <div style="font-size:0.68rem; color:{pal['text_muted']};">15% C · 15% T · 70% R</div>
                    <div style="font-size:0.82rem; font-weight:700; color:{pal['text_primary']}; margin-top:4px;">Winner: R3</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("How priorities change the recommendation ➔", use_container_width=True):
            st.session_state["active_tab"] = "Scenarios"
            st.rerun()

    # --- 5. METHODOLOGY FOOTER BANNER ---
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background-color:{pal['bg_card']}; border:1px solid {pal['border']}; border-radius:12px; padding:14px 22px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.2rem; color:{pal['primary']};">📖</span>
            <div>
                <div style="font-size:0.88rem; font-weight:700; color:{pal['text_primary']};">Methodology</div>
                <div style="font-size:0.75rem; color:{pal['text_muted']};">Understand how RouteWise AI evaluates and recommends shipment routes.</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px; font-size:0.75rem; color:{pal['text_muted']};">
            <span>Scoring Model</span> ➔ <span>Risk Metrics</span> ➔ <span>Constraints</span> ➔ <span>Pareto Dominance</span> ➔ <span>Dataset</span> ➔ <span>Limitations</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Full Methodology Specification ➔", key="btn_view_methodology"):
        st.session_state["active_tab"] = "Methodology"
        st.rerun()
