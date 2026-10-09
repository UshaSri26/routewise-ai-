"""
RouteWise AI - Main Enterprise Application
Premium Dark Navy & Teal Logistics Intelligence Platform.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from src.ui_theme import apply_theme
from src.data_generator import save_dataset
from src.views.overview_view import render_overview
from src.views.optimizer_view import render_optimizer
from src.views.scenario_view import render_scenarios
from src.views.assistant_view import render_assistant
from src.views.methodology_view import render_methodology

# Page Configuration
st.set_page_config(
    page_title="RouteWise AI — Logistics Intelligence",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Dark Navy & Teal Theme System
apply_theme()


@st.cache_data
def load_fleet_data() -> pd.DataFrame:
    data_path = Path("data/shipments.csv")
    if not data_path.exists():
        save_dataset(str(data_path), num_shipments=30)
    return pd.read_csv(data_path)


df_fleet = load_fleet_data()

# Initialize Navigation Session State
if "current_nav" not in st.session_state:
    st.session_state["current_nav"] = "Overview"

# Callback to switch navigation programmatically
def navigate_to_optimizer():
    st.session_state["current_nav"] = "Route Optimizer"
    st.rerun()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    # Wordmark Header
    st.markdown("""
    <div class="brand-container">
        <div class="brand-icon">RW</div>
        <div>
            <div class="brand-title">RouteWise AI</div>
            <div class="brand-subtitle">Shipment Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "Overview",
        "Route Optimizer",
        "Scenario Analysis",
        "AI Assistant",
        "Methodology"
    ]

    selected_page = st.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(st.session_state["current_nav"]),
        key="sidebar_nav"
    )

    # Sync state if user clicks directly on radio
    if selected_page != st.session_state["current_nav"]:
        st.session_state["current_nav"] = selected_page
        st.rerun()

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # Optional AI Credentials Expander
    with st.expander("🔑 AI Explainer Key (Optional)", expanded=False):
        st.caption("Runs 100% offline with zero dependencies by default. Enter a Gemini API Key to enable generative natural language mode.")
        api_key_input = st.text_input("Gemini API Key", type="password", key="gemini_api_key_input")

    # Dataset Status & Version Footer
    st.markdown("""
    <div class="rw-footer-pill">
        <div style="font-weight: 600; color: #F1F5F9; margin-bottom: 2px;">Dataset Status:</div>
        <div style="color: #21D4C2; font-size: 0.72rem; margin-bottom: 6px;">● Synthetic Benchmark (120 Routes)</div>
        <div style="border-top: 1px solid #22344A; padding-top: 6px; font-size: 0.68rem; color: #64748B;">
            RouteWise AI v1.0.0 Enterprise
        </div>
    </div>
    """, unsafe_allow_html=True)

# Fetch API key from session
api_key = st.session_state.get("gemini_api_key_input", "")

# --- PAGE ROUTING ---
current_page = st.session_state["current_nav"]

if current_page == "Overview":
    render_overview(df_fleet, on_navigate_optimizer=navigate_to_optimizer)

elif current_page == "Route Optimizer":
    render_optimizer(df_fleet, api_key=api_key)

elif current_page == "Scenario Analysis":
    render_scenarios(df_fleet)

elif current_page == "AI Assistant":
    render_assistant(df_fleet, api_key=api_key)

elif current_page == "Methodology":
    render_methodology()
