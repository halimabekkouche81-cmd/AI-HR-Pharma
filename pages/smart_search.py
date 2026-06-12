import requests
import streamlit as st

from sidebar import render_sidebar
from ui_kit import apply_theme, badge, empty_state, metric_card, render_page_header, render_section_header

API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide", page_title="Smart Medicine Search", page_icon="🔎")
if not st.session_state.get("token"):
    st.warning("🔵 Please login first.")
    st.page_link("login.py", label="Go to Login →", icon="🔐")
    st.stop()
if st.session_state.get("is_admin"):
    st.error("⛔ This page is for pharmacists only.")
    st.stop()

apply_theme()
render_sidebar()

try:
    token = st.session_state.get("token", "")
    notif_response = requests.get(
        f"{API_URL}/my/notifications/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=8,
    )
    notif_response.raise_for_status()
    notifications = notif_response.json() if notif_response.status_code == 200 else []
except requests.RequestException:
    st.error("Unable to connect to the server.")
    notifications = []

render_page_header(
    "Smart Medicine Search",
    "Find medicine availability across the network, discover alternatives and automatically log scarcity signals.",
    chips=["Network-wide lookup", "Alternative suggestions", "Scarcity-aware workflow"],
    stats=[("Notifications", len(notifications)), ("Current pharmacy", st.session_state.get("pharmacy_id", "—"))],
)

if notifications:
    render_section_header("Network notifications", "Recent updates that matter before searching.")
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    for n in notifications[:5]:
        type_icon = "✅" if n.get("type") == "medicine_available" else "⚠️" if n.get("type") == "low_stock" else "🤖"
        st.markdown(
            f"<div style='padding:14px 16px; border-radius:16px; background:#FFF7ED; border:1px solid #FED7AA; margin-bottom:10px;'>"
            f"<b>{type_icon} {n.get('message')}</b></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Search the network", "Designed for rapid medicine lookup with less visual noise.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
col1, col2 = st.columns([4, 1], gap="large")
with col1:
    medicine_name = st.text_input("Medicine name", placeholder="Ex: Doliprane, Amoxicilline...")
with col2:
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    search_btn = st.button("Search network", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

pharmacy_id = st.session_state.get("pharmacy_id", 6)
results = None
alternatives = None

if search_btn and medicine_name:
    with st.spinner("Searching pharmacy network..."):
        try:
            response = requests.get(
                f"{API_URL}/network-search/",
                params={"name": medicine_name, "pharmacy_id": pharmacy_id},
                timeout=12,
            )
            response.raise_for_status()
            results = response.json()
        except requests.RequestException:
            st.error("Unable to connect to the server.")
            results = []

        try:
            alt_response = requests.get(
                f"{API_URL}/alternative-medicines/",
                params={"medicine_name": medicine_name},
                timeout=12,
            )
            alt_response.raise_for_status()
            alternatives = alt_response.json()
        except requests.RequestException:
            st.error("Unable to connect to the server.")
            alternatives = []

    found = isinstance(results, list) and len(results) > 0
    requests.post(
        f"{API_URL}/log-search/",
        params={"medicine_name": medicine_name, "pharmacy_id": pharmacy_id, "found": 1 if found else 0},
        timeout=6,
    )

    if not found:
        requests.post(
            f"{API_URL}/request-medicine/",
            params={"pharmacy_id": pharmacy_id, "medicine_name": medicine_name},
            timeout=6,
        )

if search_btn and not medicine_name:
    st.warning("🔵 Please enter a medicine name first.")

if results is not None:
    count_results = len(results) if isinstance(results, list) else 0
    count_alts = len(alternatives) if isinstance(alternatives, list) else 0
    k1, k2, k3 = st.columns(3)
    with k1:
        metric_card("Pharmacies found", count_results, "Search results across network", "blue")
    with k2:
        metric_card("Alternatives found", count_alts, "Substitute medicine suggestions", "cyan")
    with k3:
        metric_card("Search origin", pharmacy_id, "Current pharmacy context", "violet")

    left_col, right_col = st.columns([1.35, 0.85], gap="large")

    with left_col:
        render_section_header("Network search results", "Availability cards optimized for quick operational reading.")
        st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
        if results and isinstance(results, list):
            for pharmacy in results:
                distance_text = f"{pharmacy.get('distance_km')} km away" if pharmacy.get("distance_km") is not None else "Distance unavailable"
                st.markdown(
                    f"<div style='padding:18px; border-radius:18px; background:rgba(255,255,255,0.78); border:1px solid #DBEAFE; margin-bottom:12px;'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:flex-start; gap:14px; flex-wrap:wrap;'>"
                    f"<div><div style='font-size:1.05rem; font-weight:800; color:#1E3A8A;'>🏢 {pharmacy.get('pharmacy_name')}</div>"
                    f"<div style='margin-top:6px; color:#64748B;'>📍 {pharmacy.get('location', 'Location unavailable')}</div></div>"
                    f"<div style='display:flex; gap:10px; flex-wrap:wrap;'>{badge('Available', 'green')}{badge(distance_text, 'blue')}</div></div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.error(f"✖️ {medicine_name} not found in the pharmacy network")
            st.info("🔔 A medicine request was logged. You will be notified when it becomes available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        render_section_header("Alternative medicines", "Fallback options when the requested medicine is unavailable.")
        st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
        if alternatives and isinstance(alternatives, list):
            for alt in alternatives:
                st.markdown(
                    f"<div style='padding:16px; border-radius:18px; background:linear-gradient(135deg,#EFF6FF,#F0FDFF); border:1px solid #BFDBFE; margin-bottom:12px;'>"
                    f"<div style='font-size:1rem; font-weight:800; color:#1D4ED8;'> {alt.get('trade_name')}</div>"
                    f"<div style='margin-top:6px; color:#334155;'>🧪 {alt.get('active_ingredient')}</div>"
                    f"<div style='margin-top:4px; color:#334155;'>💊 {alt.get('dosage')} — {alt.get('form')}</div></div>",
                    unsafe_allow_html=True,
                )
        else:
            empty_state("No alternatives found", "The system did not return substitute medicines for this query.")
        st.markdown("</div>", unsafe_allow_html=True)