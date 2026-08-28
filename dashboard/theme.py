"""Brand tokens and Streamlit presentation helpers."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

NAVY = "#062B54"
BLUE = "#0878E8"
CYAN = "#10BFE0"
TEAL = "#10B8A6"
GREEN = "#16A34A"
AMBER = "#F59E0B"
ORANGE = "#F97316"
RED = "#EF233C"
GRAY = "#718096"
INK = "#132238"
MUTED = "#5F7085"
SURFACE = "#F4F8FC"

HOSPITAL_LOGO_PATH = "assets/branding/hospital logo.png"
PATIENTTRIAGE_LOGO_PATH = "assets/branding/patienttriage-logo.png"
HOSPITAL_NAME = "Etinimtsal Hospital"
DEPARTMENT_NAME = "Emergency Department"


def apply_brand_theme() -> None:
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 1.4rem; padding-bottom: 1.5rem;
        }}
        [data-testid="stImage"] {{ margin: 0; }}
        [data-testid="stImage"] img {{ display: block; }}
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
            border-radius: 14px;
            padding: .6rem .9rem;
            box-shadow: 0 6px 18px rgba(6,43,84,.06);
        }}
        div[data-testid="stButton"] > button {{
            border-radius: 10px; border: 1px solid {BLUE}; font-weight: 700;
        }}
        div[data-testid="stButton"] > button[kind="primary"] {{
            background: linear-gradient(90deg, {BLUE}, #075FC2); color: white;
        }}

        /* ---- header bar ---- */
        .pt-header-mid {{ text-align: center; line-height: 1.4; }}
        .pt-header-sub {{ color: {MUTED}; font-size: 1.1rem; font-weight: 600; }}
        .pt-role {{ color: {NAVY}; font-weight: 800; font-size: 1.3rem; }}
        .pt-live {{ color: {GREEN}; font-weight: 700; font-size: 1rem; letter-spacing: .04em; }}
        .pt-dot {{
            display: inline-block; width: .6rem; height: .6rem; border-radius: 50%;
            background: {GREEN}; margin-right: .35rem; vertical-align: middle;
            box-shadow: 0 0 0 3px rgba(22,163,74,.18);
        }}
        .pt-time {{ color: {MUTED}; font-size: 1rem; }}

        /* ---- badges ---- */
        .pt-badge {{
            border-radius: 999px; padding: .16rem .6rem; font-weight: 700;
            font-size: .7rem; letter-spacing: .03em; text-transform: uppercase;
            display: inline-block; color: white; white-space: nowrap;
        }}

        /* ---- attention panel ---- */
        .pt-attention-card {{
            border-left: 4px solid {RED}; background: #FFF6F5;
            border-radius: 10px; padding: .55rem .85rem; margin-bottom: .5rem;
        }}
        .pt-attention-head {{ font-weight: 800; color: {NAVY}; }}
        .pt-attention-sub {{ color: {MUTED}; font-size: .85rem; }}

        /* ---- queue rows ---- */
        .pt-queue-row {{
            border: 1px solid #E1E9F1; background: rgba(255,255,255,.92);
            border-radius: 12px; padding: .6rem .9rem; margin-bottom: .45rem;
        }}
        .pt-queue-reason {{ color: {MUTED}; font-size: .87rem; }}
        .pt-movement {{ color: {BLUE}; font-weight: 700; font-size: .78rem; }}

        /* ---- status boxes ---- */
        .pt-safety-status {{
            border-left: 4px solid {TEAL}; background: #EAFBF8;
            border-radius: 10px; padding: .6rem .9rem; color: {NAVY};
        }}
        .pt-limited-mode {{
            border-left: 5px solid {AMBER}; background: #FFF8E8; color: #6B4400;
            border-radius: 10px; padding: .7rem 1rem; margin: .4rem 0 .8rem;
        }}
        .pt-limited-mode b {{ color: #6B4400; }}
        .pt-recommendation {{
            border: 1px solid #D7E4EF; background: #F7FBFF;
            border-radius: 12px; padding: .7rem 1rem; margin-bottom: .6rem;
        }}
        .pt-surge-banner {{
            border-left: 5px solid {ORANGE}; background: #FFF1E6; color: #7A2E00;
            border-radius: 10px; padding: .7rem 1rem; margin: .4rem 0 .9rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge_html(text: str, color: str, *, text_color: str = "white") -> str:
    return f'<span class="pt-badge" style="background:{color};color:{text_color}">{text}</span>'


def render_header(role_label: str) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    left, mid, right = st.columns([1.6, 1.4, 1.6], vertical_alignment="center")
    with left:
        st.image(HOSPITAL_LOGO_PATH, width=300)
    with mid:
        st.markdown(
            f"""
            <div class="pt-header-mid">
              <div class="pt-header-sub">{DEPARTMENT_NAME}</div>
              <div class="pt-role">{role_label}</div>
              <div class="pt-live"><span class="pt-dot"></span>LIVE
                <span class="pt-time">&nbsp;&middot;&nbsp;{now}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.image(PATIENTTRIAGE_LOGO_PATH, width=300)
