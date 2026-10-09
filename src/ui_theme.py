"""
RouteWise AI - Advanced UI Theme & Layout Engine
Implements the Top Navigation, AI Copilot Hero, Glowing Map, and Multi-Column Workspace.
Supports Dynamic Theme Toggling: Dark Navy/Teal & Clean Executive Light SaaS.
"""

import streamlit as st
import plotly.graph_objects as go

# Dark Theme Constants
DARK_PALETTE = {
    "bg_app": "#07111F",
    "bg_card": "#0C1829",
    "bg_card_elevated": "#112238",
    "bg_input": "#0A1728",
    "border": "#1E334D",
    "border_accent": "rgba(33, 212, 194, 0.4)",
    "primary": "#21D4C2",
    "primary_hover": "#1ABC9C",
    "text_primary": "#F1F5F9",
    "text_muted": "#8A9FB8",
    "stat_row_bg": "#07111F"
}

# Light Theme Constants
LIGHT_PALETTE = {
    "bg_app": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "bg_card_elevated": "#F1F5F9",
    "bg_input": "#FFFFFF",
    "border": "#E2E8F0",
    "border_accent": "rgba(13, 148, 136, 0.4)",
    "primary": "#0D9488",
    "primary_hover": "#0F766E",
    "text_primary": "#0F172A",
    "text_muted": "#64748B",
    "stat_row_bg": "#F8FAFC"
}

# Aliases for views
BG_APP = DARK_PALETTE["bg_app"]
BG_MAIN = DARK_PALETTE["bg_app"]
BG_SIDEBAR = "#0A1626"
BG_CARD = DARK_PALETTE["bg_card"]
BG_CARD_ELEVATED = DARK_PALETTE["bg_card_elevated"]
BG_ELEVATED = DARK_PALETTE["bg_card_elevated"]
BORDER_DARK = DARK_PALETTE["border"]
BORDER_COLOR = DARK_PALETTE["border"]
TEAL_PRIMARY = DARK_PALETTE["primary"]
PRIMARY_TEAL = DARK_PALETTE["primary"]
SECONDARY_TEAL = "#76E4D4"
TEXT_WHITE = DARK_PALETTE["text_primary"]
TEXT_PRIMARY = DARK_PALETTE["text_primary"]
TEXT_MUTED = DARK_PALETTE["text_muted"]
TEXT_SECONDARY = DARK_PALETTE["text_muted"]
PURPLE_ACCENT = "#8B5CF6"
BLUE_ACCENT = "#38BDF8"
ORANGE_ACCENT = "#FB923C"
COLOR_SUCCESS = "#34D399"
COLOR_WARNING = "#FBBF24"
COLOR_ERROR = "#FB7185"


def get_plotly_layout(title: str = "", height: int = 380, theme_mode: str = "dark") -> dict:
    pal = DARK_PALETTE if theme_mode == "dark" else LIGHT_PALETTE
    return dict(
        title=dict(
            text=title,
            font=dict(family="Plus Jakarta Sans, sans-serif", size=13, color=pal["text_primary"]),
            x=0.02,
            y=0.96
        ),
        paper_bgcolor=pal["bg_card"],
        plot_bgcolor=pal["bg_card"],
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
        font=dict(family="Plus Jakarta Sans, sans-serif", color=pal["text_muted"], size=11),
        xaxis=dict(
            gridcolor=pal["border"],
            linecolor=pal["border"],
            zerolinecolor=pal["border"],
            tickfont=dict(color=pal["text_muted"])
        ),
        yaxis=dict(
            gridcolor=pal["border"],
            linecolor=pal["border"],
            zerolinecolor=pal["border"],
            tickfont=dict(color=pal["text_muted"])
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=pal["text_muted"], size=10)
        )
    )


def apply_theme(mode: str = "dark"):
    pal = DARK_PALETTE if mode == "dark" else LIGHT_PALETTE
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            color: {pal["text_primary"]};
        }}
        .stApp {{
            background-color: {pal["bg_app"]} !important;
        }}
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

        /* Clean Card */
        .rw-box {{
            background-color: {pal["bg_card"]};
            border: 1px solid {pal["border"]};
            border-radius: 12px;
            padding: 18px;
            height: 100%;
        }}
        .rw-card {{
            background-color: {pal["bg_card"]};
            border: 1px solid {pal["border"]};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }}

        /* Winner Card */
        .rw-winner-card {{
            background-color: {pal["bg_card_elevated"]};
            border: 1px solid {pal["primary"]};
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
            color: {pal["primary"]};
            border: 1px solid rgba(33, 212, 194, 0.4);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}

        /* Hero */
        .rw-hero-badge {{
            display: inline-block;
            background-color: rgba(33, 212, 194, 0.1);
            border: 1px solid rgba(33, 212, 194, 0.3);
            color: {pal["primary"]};
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
            color: {pal["text_primary"]};
            letter-spacing: -0.03em;
            line-height: 1.15;
            margin-bottom: 8px;
        }}
        .rw-hero-sub {{
            font-size: 1.02rem;
            color: {pal["text_muted"]};
            line-height: 1.5;
            max-width: 680px;
            margin-bottom: 20px;
        }}

        /* Metric Grid */
        .rw-stat-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-top: 14px;
            margin-bottom: 14px;
            background-color: {pal["stat_row_bg"]};
            border: 1px solid {pal["border"]};
            border-radius: 8px;
            padding: 10px;
        }}
        .rw-stat-item {{
            text-align: center;
        }}
        .rw-stat-val {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {pal["text_primary"]};
            line-height: 1.1;
        }}
        .rw-stat-lbl {{
            font-size: 0.68rem;
            color: {pal["text_muted"]};
            text-transform: uppercase;
            margin-top: 3px;
        }}

        /* Chips */
        .rw-chip {{
            display: inline-flex;
            align-items: center;
            background-color: {pal["bg_card"]};
            border: 1px solid {pal["border"]};
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 0.8rem;
            color: {pal["text_muted"]};
            margin-right: 8px;
            margin-bottom: 8px;
            transition: all 0.15s ease;
        }}

        /* Scenario Cards */
        .rw-scenario-card {{
            background-color: {pal["bg_card"]};
            border: 1px solid {pal["border"]};
            border-radius: 10px;
            padding: 14px;
            transition: all 0.2s ease;
        }}
        .rw-scenario-card:hover {{
            border-color: {pal["primary"]};
            background-color: {pal["bg_card_elevated"]};
        }}

        /* Table & DataFrame Overrides */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {pal["border"]} !important;
            border-radius: 8px;
            background-color: {pal["bg_card"]} !important;
        }}

        /* Buttons */
        div.stButton > button {{
            background-color: {pal["primary"]} !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.45rem 1rem !important;
            font-size: 0.88rem !important;
            transition: all 0.2s ease !important;
        }}
        div.stButton > button:hover {{
            background-color: {pal["primary_hover"]} !important;
            box-shadow: 0 4px 14px rgba(33, 212, 194, 0.3) !important;
        }}

        /* Input Elements */
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] > div {{
            background-color: {pal["bg_card"]} !important;
            color: {pal["text_primary"]} !important;
            border: 1px solid {pal["border"]} !important;
            border-radius: 8px !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
