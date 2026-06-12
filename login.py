# -*- coding: utf-8 -*-
"""
AI-HR Pharma - Login Page
Premium Streamlit UI refresh without backend changes.
"""
from pathlib import Path
import requests
import streamlit as st

from ui_kit import get_logo_path

API_URL = "http://127.0.0.1:8000"
LOGO_PATH = Path(get_logo_path())

st.set_page_config(
    page_title="AI-HR Pharma — Sign In",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', sans-serif; }
    #MainMenu, header, footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(37,99,235,0.16), transparent 26%),
            radial-gradient(circle at bottom right, rgba(6,182,212,0.14), transparent 28%),
            linear-gradient(135deg, #F8FBFF 0%, #EEF4FF 48%, #E7EEF8 100%);
    }

    .main .block-container {
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .login-shell {
        min-height: calc(100vh - 4rem);
        display: flex;
        align-items: center;
    }

    .brand-panel {
        position: relative;
        overflow: hidden;
        border-radius: 32px;
        padding: 34px 34px 30px;
        color: white;
        min-height: 620px;
        background:
            linear-gradient(145deg, rgba(8,17,32,0.98) 0%, rgba(13,26,47,0.96) 40%, rgba(29,78,216,0.90) 100%);
        box-shadow: 0 32px 80px rgba(15,23,42,0.24);
        border: 1px solid rgba(125,211,252,0.12);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }

    .brand-panel::before,
    .brand-panel::after {
        content: '';
        position: absolute;
        border-radius: 999px;
        background: rgba(255,255,255,0.07);
    }

    .brand-panel::before {
        width: 280px;
        height: 280px;
        top: -120px;
        right: -90px;
    }

    .brand-panel::after {
        width: 180px;
        height: 180px;
        bottom: -80px;
        left: -60px;
    }

    .logo-container {
        width: 100%;
        display: flex;
        justify-content: center;
        margin-bottom: 24px;
    }

    .logo-container img {
        max-width: 320px !important;
        width: 100% !important;
        height: auto !important;
    }

    .brand-title {
        font-size: 3.2rem;
        line-height: 1.02;
        margin: 12px 0 8px;
        letter-spacing: -0.04em;
        font-weight: 800;
        color: white;
    }

    .brand-subtitle {
        color: #D6E8FF;
        font-size: 1.1rem;
        line-height: 1.6;
        max-width: 480px;
        margin-bottom: 28px;
    }

    .brand-footer {
        margin-top: auto;
        padding-top: 28px;
        color: rgba(255,255,255,0.78);
        font-size: 0.83rem;
    }

    .login-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(191,219,254,0.9);
        border-radius: 30px;
        padding: 28px 28px 24px;
        box-shadow: 0 28px 70px rgba(15,23,42,0.10);
        backdrop-filter: blur(14px);
    }

    .login-card h2 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
    }

    .login-card p {
        margin: 10px 0 0;
        color: #64748B;
        line-height: 1.7;
    }

    .mini-note {
        margin-top: 18px;
        padding: 14px 16px;
        border-radius: 18px;
        background: linear-gradient(135deg, #EFF6FF 0%, #F0FDFF 100%);
        border: 1px solid #CFE5FF;
        color: #1E3A8A;
        font-size: 0.92rem;
        line-height: 1.65;
    }

    .login-status-card {
        background: rgba(255,255,255,0.88);
        border: 1px solid rgba(191,219,254,0.9);
        border-radius: 28px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 24px 60px rgba(15,23,42,0.10);
    }

    .login-status-card .icon {
        font-size: 3.8rem;
        margin-bottom: 12px;
    }

    .login-status-card .title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 8px;
    }

    .login-status-card .text {
        color: #64748B;
        line-height: 1.7;
        margin-bottom: 18px;
    }

    .stTextInput > div > div > input {
        border-radius: 16px !important;
        min-height: 50px !important;
        border: 1px solid #D6E4FF !important;
        background: white !important;
        box-shadow: 0 8px 16px rgba(15,23,42,0.04);
    }

    .stTextInput > div > div > input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 4px rgba(59,130,246,0.10) !important;
    }

    .stFormSubmitButton > button,
    .stButton > button {
        width: 100% !important;
        min-height: 50px !important;
        border-radius: 16px !important;
        border: none !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 55%, #1E40AF 100%) !important;
        color: white !important;
        box-shadow: 0 18px 34px rgba(37,99,235,0.22);
    }

    .stFormSubmitButton > button:hover,
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

for key, default in {
    "token": None,
    "pharmacy_id": None,
    "email": None,
    "pharmacy_name": None,
    "is_admin": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

left, right = st.columns([1.2, 0.9], gap="large")

with left:
    st.markdown("<div class='login-shell'><div class='brand-panel'>", unsafe_allow_html=True)

    # Large centered logo
    if LOGO_PATH.exists():
        st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
        st.image(str(LOGO_PATH), width=320)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class='brand-title'>AI-HR Pharma</div>
        <div class='brand-subtitle'>Medical operations platform for pharmacy coordination, stock visibility and AI-assisted decision support.</div>
        <div class='brand-footer'>Enterprise medical SaaS interface · Secure access workspace</div>

        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div></div>", unsafe_allow_html=True)

with right:
    if st.session_state["token"]:
        st.markdown("<div class='login-shell'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='login-status-card'>
                <div class='icon' style='width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#DBEAFE,#E0F2FE);display:flex;align-items:center;justify-content:center;margin:0 auto 12px;'>
                    <div style='width:18px;height:18px;border-radius:50%;background:#16A34A;box-shadow:0 0 0 8px rgba(22,163,74,0.12);'></div>
                </div>
                <div class='title'>Session Active</div>
                <div class='text'>You are signed in as <b>{st.session_state['email']}</b><br>Pharmacy ID: <b>{st.session_state['pharmacy_id']}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.get("is_admin"):
                if st.button("Open Admin Workspace", use_container_width=True):
                    st.switch_page("pages/admin_dashboard.py")
            else:
                if st.button("Open Workspace", use_container_width=True):
                    st.switch_page("pages/dashboard.py")
        with col2:
            if st.button("Sign Out", use_container_width=True):
                for key in ("token", "pharmacy_id", "email", "pharmacy_name", "is_admin"):
                    st.session_state[key] = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='login-shell'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='login-card'>
                <h2>Secure Sign In</h2>
                <p>Access the AI-HR Pharma workspace for pharmacy operations, analytics and monitoring.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email address", placeholder="pharmacy@pharma-saida.dz")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign in to platform")

        if submitted:
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                with st.spinner("Authenticating..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/token",
                            data={
                                "username": email,
                                "password": password,
                                "grant_type": "password",
                            },
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                            timeout=5,
                        )

                        if response.status_code == 200:
                            data = response.json()
                            st.session_state["token"] = data["access_token"]
                            st.session_state["pharmacy_id"] = data["pharmacy_id"]
                            st.session_state["email"] = data["email"]
                            st.session_state["is_admin"] = data.get("is_admin", 0)
                            st.success("Sign-in successful. Redirecting...")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")
                    except Exception:
                        st.error("Connection error: unable to reach the server.")
        st.markdown("</div>", unsafe_allow_html=True)