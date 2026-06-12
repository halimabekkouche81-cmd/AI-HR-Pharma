# -*- coding: utf-8 -*-
from pathlib import Path
import streamlit as st

from ui_kit import get_theme_tokens


LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.png"


def render_sidebar():
    tokens = get_theme_tokens()

    is_admin = st.session_state.get("is_admin", 0)
    email = st.session_state.get("email", "")
    pharm_id = st.session_state.get("pharmacy_id", "")

    st.markdown(
        f"""
        <style>
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"] {{
            display: none !important;
        }}

        [data-testid="stSidebar"] {{
            background:
                radial-gradient(circle at top, rgba(14,165,233,0.14), transparent 30%),
                linear-gradient(180deg, {tokens["brand_dark"]} 0%, #0D1A2F 48%, #0A1426 100%) !important;
            border-right: 1px solid rgba(59,130,246,0.14) !important;
        }}

        [data-testid="stSidebar"] * {{
            font-family: 'Inter', sans-serif !important;
        }}

        [data-testid="stSidebar"] .block-container {{
            padding-top: 1rem;
            padding-bottom: 1.2rem;
        }}

        .sb-shell {{
            padding: 0 6px 10px;
        }}

        .sb-brand-card {{
            background: linear-gradient(180deg, rgba(15,23,42,0.84), rgba(15,23,42,0.56));
            border: 1px solid rgba(125,211,252,0.16);
            border-radius: 22px;
            padding: 16px 14px;
            box-shadow: 0 18px 40px rgba(2,6,23,0.28);
            margin-bottom: 14px;
        }}

        .sb-brand-title {{
            font-size: 1rem;
            font-weight: 800;
            color: #F8FAFC;
            margin-top: 10px;
            letter-spacing: -0.02em;
        }}

        .sb-brand-subtitle {{
            color: #BFDBFE;
            font-size: 0.82rem;
            line-height: 1.55;
            margin-top: 4px;
        }}

        .sb-user {{
            background: rgba(15,23,42,0.62);
            border: 1px solid rgba(96,165,250,0.14);
            border-radius: 18px;
            padding: 12px 14px;
            margin-bottom: 14px;
        }}

        .sb-role {{
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }}

        .sb-email {{
            color: #E2E8F0;
            font-size: 0.86rem;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .sb-meta {{
            color: #93C5FD;
            font-size: 0.78rem;
            margin-top: 6px;
        }}

        .sb-label {{
            color: #7C93B7;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            padding: 6px 8px 8px;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink"] a {{
            display: flex;
            align-items: center;
            min-height: 44px;
            border-radius: 14px;
            color: #FFFFFF !important;
            font-size: 0.94rem !important;
            padding: 0 12px;
            margin-bottom: 6px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.03);
            font-weight: 700;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
            background: linear-gradient(135deg, rgba(37,99,235,0.20), rgba(14,165,233,0.14));
            border-color: rgba(125,211,252,0.18);
            color: #FFFFFF !important;
        }}

        [data-testid="stSidebar"] .stButton > button {{
            width: 100%;
            min-height: 44px;
            border-radius: 14px !important;
            background: rgba(220,38,38,0.08) !important;
            box-shadow: none !important;
            border: 1px solid rgba(248,113,113,0.18) !important;
            color: #FCA5A5 !important;
            font-weight: 800 !important;
        }}

        [data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(220,38,38,0.14) !important;
            transform: none !important;
        }}

        .sb-spacer {{
            height: 6px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("<div class='sb-shell'>", unsafe_allow_html=True)

        st.markdown("<div class='sb-brand-card'>", unsafe_allow_html=True)
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=175)
        st.markdown(
            """
            <div class='sb-brand-title'>AI-HR Pharma</div>
            <div class='sb-brand-subtitle'>Medical operations platform for network coordination, stock intelligence and AI-assisted pharmacy workflows.</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if email:
            role_color = "#FBBF24" if is_admin else "#67E8F9"
            role_label = "ADMINISTRATOR" if is_admin else f"PHARMACY {pharm_id}"
            st.markdown(
                f"""
                <div class='sb-user'>
                    <div class='sb-role' style='color:{role_color};'>{role_label}</div>
                    <div class='sb-email'>{email}</div>
                    <div class='sb-meta'>Connected to the AI-HR operational network</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if is_admin:
            st.markdown("<div class='sb-label'>🛠️ Administration</div>", unsafe_allow_html=True)
            st.page_link("pages/admin_dashboard.py", label="🧭 Admin Dashboard")
            st.page_link("pages/ai_monitoring.py", label="🤖 AI Monitoring")
            st.page_link("pages/model_comparison.py", label="⚖️ Model Comparison")
            st.markdown("<div class='sb-spacer'></div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-label'>🌐 Network</div>", unsafe_allow_html=True)
            st.page_link("pages/pharmacy_map.py", label="🗺️ Network Map")
        else:
            st.markdown("<div class='sb-label'>💼 Workspace</div>", unsafe_allow_html=True)
            st.page_link("pages/dashboard.py", label="🌐 Operational Dashboard")
            st.page_link("pages/operations.py", label="⚙️ Operations")
            st.page_link("pages/smart_search.py", label="🔎 Medicine Search")
            st.page_link("pages/pharmacy_map.py", label="🗺️ Network Map")
            st.markdown("<div class='sb-spacer'></div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-label'>🧠 AI & Analytics</div>", unsafe_allow_html=True)
            st.page_link("pages/ai_monitoring.py", label="🖲️ AI Monitoring")
            st.page_link("pages/model_comparison.py", label="📈 Model Comparison")

        st.markdown("<div class='sb-spacer'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", key="sb_logout", use_container_width=True):
            for key in ["token", "pharmacy_id", "email", "pharmacy_name", "is_admin"]:
                st.session_state[key] = None
            st.switch_page("login.py")

        st.markdown("</div>", unsafe_allow_html=True)

