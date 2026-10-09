"""
UI Design System and Styling Utilities for RouteWise AI.
Implements the Dark Premium Navy + Teal Enterprise SaaS Aesthetic.
"""

import plotly.graph_objects as go
import streamlit as st

# Color Palette Constants
BG_MAIN = "#07111F"
BG_SIDEBAR = "#0A1626"
BG_CARD = "#101F32"
BG_ELEVATED = "#14263B"
PRIMARY_TEAL = "#21D4C2"
SECONDARY_TEAL = "#76E4D4"
TEXT_PRIMARY = "#F1F5F9"
TEXT_SECONDARY = "#93A4B8"
BORDER_COLOR = "#22344A"
COLOR_SUCCESS = "#34D399"
COLOR_WARNING = "#FBBF24"
COLOR_ERROR = "#FB7185"

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {TEXT_PRIMARY};
    }}

    /* Global Streamlit App Background */
    .stApp {{
        background-color: {BG_MAIN};
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {BG_SIDEBAR};
        border-right: 1px solid {BORDER_COLOR};
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}

    /* Custom Header Wordmark */
    .brand-container {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 1rem;
        border-bottom: 1px solid {BORDER_COLOR};
        margin-bottom: 1.5rem;
    }}
    .brand-icon {{
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, {PRIMARY_TEAL} 0%, #0D9488 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #07111F;
        font-size: 18px;
    }}
    .brand-title {{
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: {TEXT_PRIMARY};
        margin: 0;
        line-height: 1.2;
    }}
    .brand-subtitle {{
        font-size: 0.75rem;
        font-weight: 500;
        color: {PRIMARY_TEAL};
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin: 0;
    }}

    /* Navigation Radio Styling */
    div[data-testid="stRadio"] > label {{
        display: none;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] {{
        gap: 6px;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] label {{
        background-color: transparent;
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid transparent;
        transition: all 0.15s ease-in-out;
        color: {TEXT_SECONDARY};
        font-weight: 500;
        font-size: 0.9rem;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
    }}

    /* General Cards */
    .rw-card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }}
    .rw-card-elevated {{
        background-color: {BG_ELEVATED};
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }}

    /* Metric Cards */
    .rw-kpi-card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        border-radius: 10px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .rw-kpi-label {{
        font-size: 0.75rem;
        font-weight: 600;
        color: {TEXT_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }}
    .rw-kpi-value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    .rw-kpi-subtext {{
        font-size: 0.75rem;
        color: {PRIMARY_TEAL};
        margin-top: 4px;
    }}

    /* Hero Recommendation Banner */
    .rw-winner-banner {{
        background-color: {BG_ELEVATED};
        border: 1px solid {PRIMARY_TEAL};
        border-left: 4px solid {PRIMARY_TEAL};
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
    }}
    .rw-winner-tag {{
        display: inline-flex;
        align-items: center;
        background-color: rgba(33, 212, 194, 0.15);
        color: {PRIMARY_TEAL};
        border: 1px solid rgba(33, 212, 194, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }}
    .rw-infeasible-banner {{
        background-color: {BG_ELEVATED};
        border: 1px solid {COLOR_WARNING};
        border-left: 4px solid {COLOR_WARNING};
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
    }}

    /* Badges */
    .rw-badge-feasible {{
        background-color: rgba(52, 211, 153, 0.15);
        color: {COLOR_SUCCESS};
        border: 1px solid rgba(52, 211, 153, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .rw-badge-infeasible {{
        background-color: rgba(251, 113, 133, 0.15);
        color: {COLOR_ERROR};
        border: 1px solid rgba(251, 113, 133, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .rw-badge-dominated {{
        background-color: rgba(251, 191, 36, 0.15);
        color: {COLOR_WARNING};
        border: 1px solid rgba(251, 191, 36, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {PRIMARY_TEAL} !important;
        color: #07111F !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.2s ease !important;
    }}
    .stButton > button:hover {{
        background-color: {SECONDARY_TEAL} !important;
        color: #07111F !important;
        box-shadow: 0 4px 12px rgba(33, 212, 194, 0.25) !important;
    }}

    /* Streamlit Metric Overrides */
    div[data-testid="stMetric"] {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        border-radius: 10px;
        padding: 14px 16px;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {TEXT_SECONDARY} !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
    }}
    div[data-testid="stMetricValue"] {{
        color: {TEXT_PRIMARY} !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }}

    /* Streamlit DataFrame / Table */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
        background-color: {BG_CARD};
    }}

    /* Form Inputs */
    div[data-testid="stSelectbox"] > div, div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input {{
        background-color: {BG_CARD} !important;
        color: {TEXT_PRIMARY} !important;
        border-color: {BORDER_COLOR} !important;
        border-radius: 8px !important;
    }}

    /* Footer Status Pill */
    .rw-footer-pill {{
        margin-top: 2rem;
        padding: 10px 14px;
        border-radius: 8px;
        background-color: {BG_CARD};
        border: 1px solid {BORDER_COLOR};
        font-size: 0.75rem;
        color: {TEXT_SECONDARY};
    }}
</style>
"""


def apply_theme():
    """Injects custom CSS design system into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_plotly_layout(title: str = "", height: int = 380) -> dict:
    """Returns standardized layout configuration matching the dark navy/teal aesthetic."""
    return dict(
        title=dict(
            text=title,
            font=dict(family="Inter, sans-serif", size=14, color=TEXT_PRIMARY),
            x=0.02,
            y=0.96
        ),
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_CARD,
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
        font=dict(family="Inter, sans-serif", color=TEXT_SECONDARY, size=11),
        xaxis=dict(
            gridcolor=BORDER_COLOR,
            linecolor=BORDER_COLOR,
            zerolinecolor=BORDER_COLOR,
            tickfont=dict(color=TEXT_SECONDARY)
        ),
        yaxis=dict(
            gridcolor=BORDER_COLOR,
            linecolor=BORDER_COLOR,
            zerolinecolor=BORDER_COLOR,
            tickfont=dict(color=TEXT_SECONDARY)
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_SECONDARY, size=10)
        )
    )
