"""Brand tokens and Streamlit presentation helpers."""

from __future__ import annotations

import streamlit as st

NAVY = "#062B54"
BLUE = "#0878E8"
CYAN = "#10BFE0"
TEAL = "#10B8A6"
GREEN = "#16A34A"
AMBER = "#F59E0B"
ORANGE = "#F97316"
RED = "#EF233C"
INK = "#132238"
MUTED = "#5F7085"
SURFACE = "#F4F8FC"


def apply_brand_theme() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at 92% 4%, rgba(16,191,224,.10), transparent 24rem),
                linear-gradient(180deg, #ffffff 0%, {SURFACE} 100%);
            color: {INK};
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {NAVY} 0%, #041D38 100%);
        }}
        [data-testid="stSidebar"] * {{ color: #F7FBFF; }}
        [data-testid="stSidebar"] input {{ color: {INK}; }}
        [data-testid="stMetric"] {{
            background: rgba(255,255,255,.94);
            border: 1px solid #D7E4EF;
            border-radius: 16px;
            padding: .7rem 1rem;
            box-shadow: 0 8px 28px rgba(6,43,84,.07);
        }}
        .hero-kicker {{
            color: {BLUE}; font-weight: 800; letter-spacing: .12em;
            text-transform: uppercase; font-size: .78rem;
        }}
        .hero-title {{
            color: {NAVY}; font-size: clamp(1.8rem, 3vw, 3rem);
            font-weight: 850; line-height: 1.04; margin: .2rem 0 .5rem;
        }}
        .hero-copy {{ color: {MUTED}; max-width: 58rem; font-size: 1.02rem; }}
        .scope-banner {{
            border-left: 5px solid {TEAL}; background: #EAFBF8; color: {NAVY};
            border-radius: 10px; padding: .75rem 1rem; margin: .7rem 0 1rem;
        }}
        .safety-banner {{
            border-left: 5px solid {RED}; background: #FFF1F3; color: #74111E;
            border-radius: 10px; padding: .75rem 1rem; margin: .4rem 0 1rem;
        }}
        div[data-testid="stButton"] > button {{
            border-radius: 10px; border: 1px solid {BLUE}; font-weight: 700;
        }}
        div[data-testid="stButton"] > button[kind="primary"] {{
            background: linear-gradient(90deg, {BLUE}, #075FC2); color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_product_header(role_label: str) -> None:
    st.image("assets/branding/patienttriage-logo.png", width=560)
    st.markdown(
        f"""
        <div class="hero-kicker">District emergency coordination · {role_label}</div>
        <div class="hero-title">The score does not move. The queue does.</div>
        <div class="hero-copy">
          Safety-constrained CDM ranking, live waiting-room monitoring, operational
          bed projection, and role-specific readiness signals for synthetic cases.
        </div>
        <div class="scope-banner">
          <b>Focused scope:</b> emergency prioritization and coordination only.
          No billing, procurement, stock ledger, dispensing, admission master,
          or hospital ERP source-of-truth functions.
        </div>
        <div class="safety-banner">
          <b>Prototype safety notice:</b> synthetic data only; not clinically
          validated, not a diagnosis, and never a substitute for clinician judgement.
        </div>
        """,
        unsafe_allow_html=True,
    )
