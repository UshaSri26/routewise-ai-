"""
RouteWise AI - Advanced UI Theme & Layout Engine
Implements the Top Navigation, AI Copilot Hero, Glowing Map, and Multi-Column Workspace.
Matches the Reference Design (media_1791572320523_beee24c4.jpg).
"""

import plotly.graph_objects as go

# Color Palette Constants from Reference Image
BG_APP = "#07111F"
BG_MAIN = "#07111F"
BG_SIDEBAR = "#0A1626"
BG_CARD = "#0C1829"
BG_CARD_ELEVATED = "#112238"
BG_ELEVATED = "#112238"
BG_INPUT = "#0A1728"
BORDER_DARK = "#1E334D"
BORDER_COLOR = "#1E334D"
BORDER_ACCENT = "rgba(33, 212, 194, 0.4)"
TEAL_PRIMARY = "#21D4C2"
PRIMARY_TEAL = "#21D4C2"
TEAL_HOVER = "#1ABC9C"
SECONDARY_TEAL = "#76E4D4"
TEAL_MUTED = "rgba(33, 212, 194, 0.15)"
TEXT_WHITE = "#F1F5F9"
TEXT_PRIMARY = "#F1F5F9"
TEXT_MUTED = "#8A9FB8"
TEXT_SECONDARY = "#8A9FB8"
PURPLE_ACCENT = "#8B5CF6"
BLUE_ACCENT = "#38BDF8"
ORANGE_ACCENT = "#FB923C"
COLOR_SUCCESS = "#34D399"
COLOR_WARNING = "#FBBF24"
COLOR_ERROR = "#FB7185"


def get_plotly_layout(title: str = "", height: int = 380) -> dict:
    """Returns standardized layout configuration matching the dark navy/teal aesthetic."""
    return dict(
        title=dict(
            text=title,
            font=dict(family="Plus Jakarta Sans, sans-serif", size=13, color=TEXT_WHITE),
            x=0.02,
            y=0.96
        ),
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_CARD,
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
        font=dict(family="Plus Jakarta Sans, sans-serif", color=TEXT_MUTED, size=11),
        xaxis=dict(
            gridcolor=BORDER_COLOR,
            linecolor=BORDER_COLOR,
            zerolinecolor=BORDER_COLOR,
            tickfont=dict(color=TEXT_MUTED)
        ),
        yaxis=dict(
            gridcolor=BORDER_COLOR,
            linecolor=BORDER_COLOR,
            zerolinecolor=BORDER_COLOR,
            tickfont=dict(color=TEXT_MUTED)
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_MUTED, size=10)
        )
    )


CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Streamlit Overrides */
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        color: {TEXT_WHITE};
    }}
    .stApp {{
        background-color: {BG_APP};
    }}
    /* Hide the permanent default sidebar completely */
    section[data-testid="stSidebar"] {{
        display: none !important;
    }}
    header[data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px !important;
    }}

    /* Top Navigation Bar */
    .rw-top-navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: {BG_CARD};
        border: 1px solid {BORDER_DARK};
        border-radius: 12px;
        padding: 10px 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }}
    .rw-nav-brand {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .rw-brand-logo {{
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, #0284C7 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #07111F;
        font-size: 15px;
    }}
    .rw-brand-name {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {TEXT_WHITE};
        letter-spacing: -0.01em;
        line-height: 1;
    }}
    .rw-brand-sub {{
        font-size: 0.72rem;
        color: {TEXT_MUTED};
        letter-spacing: 0.04em;
    }}

    /* Top Nav Links */
    .rw-nav-links {{
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .rw-nav-pill {{
        background-color: transparent;
        color: {TEXT_MUTED};
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 0.86rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
    }}
    .rw-nav-pill:hover {{
        color: {TEXT_WHITE};
        background-color: {BG_CARD_ELEVATED};
    }}
    .rw-nav-pill.active {{
        background-color: rgba(33, 212, 194, 0.12);
        color: {TEAL_PRIMARY};
        border-color: rgba(33, 212, 194, 0.35);
        font-weight: 600;
    }}

    /* Nav Right Status */
    .rw-nav-status {{
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.8rem;
        color: {TEXT_MUTED};
    }}
    .rw-badge-dot {{
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: {TEAL_PRIMARY};
        margin-right: 5px;
        box-shadow: 0 0 8px {TEAL_PRIMARY};
    }}
    .rw-avatar {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background-color: #1E293B;
        border: 1px solid {BORDER_DARK};
        color: {TEXT_WHITE};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 600;
    }}

    /* Hero Section */
    .rw-hero-badge {{
        display: inline-block;
        background-color: rgba(33, 212, 194, 0.1);
        border: 1px solid rgba(33, 212, 194, 0.3);
        color: {TEAL_PRIMARY};
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 12px;
        border-radius: 6px;
        margin-bottom: 12px;
    }}
    .rw-hero-heading {{
        font-size: 2.5rem;
        font-weight: 800;
        color: {TEXT_WHITE};
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin-bottom: 8px;
    }}
    .rw-hero-sub {{
        font-size: 1.02rem;
        color: {TEXT_MUTED};
        line-height: 1.5;
        max-width: 680px;
        margin-bottom: 20px;
    }}

    /* AI Prompt Bar */
    .rw-composer-box {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_DARK};
        border-radius: 12px;
        padding: 6px 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
        transition: border-color 0.2s ease;
    }}
    .rw-composer-box:focus-within {{
        border-color: {TEAL_PRIMARY};
        box-shadow: 0 0 16px rgba(33, 212, 194, 0.15);
    }}

    /* Quick Prompt Chips */
    .rw-chip {{
        display: inline-flex;
        align-items: center;
        background-color: {BG_CARD};
        border: 1px solid {BORDER_DARK};
        border-radius: 8px;
        padding: 5px 12px;
        font-size: 0.8rem;
        color: {TEXT_MUTED};
        margin-right: 8px;
        margin-bottom: 8px;
        transition: all 0.15s ease;
        cursor: pointer;
    }}
    .rw-chip:hover {{
        color: {TEXT_WHITE};
        border-color: {TEAL_PRIMARY};
        background-color: {BG_CARD_ELEVATED};
    }}

    /* Section Workspace Header */
    .rw-section-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 28px;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid {BORDER_DARK};
    }}
    .rw-section-title {{
        font-size: 1.2rem;
        font-weight: 700;
        color: {TEXT_WHITE};
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    /* Clean Card */
    .rw-box {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_DARK};
        border-radius: 12px;
        padding: 18px;
        height: 100%;
    }}

    /* Highlighted Winner Card */
    .rw-winner-card {{
        background-color: {BG_CARD_ELEVATED};
        border: 1px solid {TEAL_PRIMARY};
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        position: relative;
    }}
    .rw-rec-tag {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background-color: rgba(33, 212, 194, 0.18);
        color: {TEAL_PRIMARY};
        border: 1px solid rgba(33, 212, 194, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}

    /* Metric Grid inside Card */
    .rw-stat-row {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-top: 14px;
        margin-bottom: 14px;
        background-color: {BG_APP};
        border: 1px solid {BORDER_DARK};
        border-radius: 8px;
        padding: 10px;
    }}
    .rw-stat-item {{
        text-align: center;
    }}
    .rw-stat-val {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {TEXT_WHITE};
        line-height: 1.1;
    }}
    .rw-stat-lbl {{
        font-size: 0.68rem;
        color: {TEXT_MUTED};
        text-transform: uppercase;
        margin-top: 3px;
    }}

    /* Multi-segment Score Breakdown Bar */
    .rw-bar-container {{
        background-color: {BG_APP};
        border: 1px solid {BORDER_DARK};
        border-radius: 8px;
        padding: 12px;
        margin-top: 12px;
    }}
    .rw-progress-bar {{
        display: flex;
        height: 10px;
        border-radius: 5px;
        overflow: hidden;
        margin-top: 6px;
        margin-bottom: 6px;
    }}
    .rw-bar-cost {{ background-color: {TEAL_PRIMARY}; }}
    .rw-bar-time {{ background-color: {PURPLE_ACCENT}; }}
    .rw-bar-risk {{ background-color: {BLUE_ACCENT}; }}

    /* Scenario Card */
    .rw-scenario-card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER_DARK};
        border-radius: 10px;
        padding: 14px;
        transition: all 0.2s ease;
    }}
    .rw-scenario-card:hover {{
        border-color: {TEAL_PRIMARY};
        background-color: {BG_CARD_ELEVATED};
    }}

    /* Custom Buttons */
    div.stButton > button {{
        background-color: {TEAL_PRIMARY} !important;
        color: #07111F !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.45rem 1rem !important;
        font-size: 0.88rem !important;
        transition: all 0.2s ease !important;
    }}
    div.stButton > button:hover {{
        background-color: {TEAL_HOVER} !important;
        box-shadow: 0 4px 14px rgba(33, 212, 194, 0.3) !important;
    }}
</style>
"""


def apply_theme():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
