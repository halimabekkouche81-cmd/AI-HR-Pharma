# -*- coding: utf-8 -*-
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from sidebar import render_sidebar
from ui_kit import apply_theme, badge, empty_state, metric_card, render_page_header, render_section_header, style_plotly

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Operational Dashboard", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please sign in first.")
    st.page_link("login.py", label="Go to Sign In")
    st.stop()
if st.session_state.get("is_admin"):
    st.error("This workspace is available to pharmacists only.")
    st.stop()

apply_theme()
render_sidebar()

pharmacy_id = st.session_state.get("pharmacy_id", 1)


def fetch_json(endpoint, method="get", **kwargs):
    try:
        response = getattr(requests, method)(f"{API_URL}{endpoint}", timeout=8, **kwargs)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None


# Fetch medicine list for name lookup
try:
    medicines_list = requests.get(f"{API_URL}/medicines/", timeout=8).json()
    med_lookup = {m["id"]: m["trade_name"] for m in medicines_list}
except Exception:
    medicines_list = []
    med_lookup = {}

# ── FETCH ──
token   = st.session_state["token"]
headers = {"Authorization": f"Bearer {token}"}

# بيانات الشبكة (عامة)
top_selling = fetch_json("/analytics/top-selling/") or []
scarcity    = fetch_json("/market-scarcity/")        or []
metrics     = fetch_json("/ai-metrics/")             or {}

# بيانات الصيدلية فقط
all_alerts  = fetch_json("/low-stock-alerts/")       or []
low_stock   = [a for a in all_alerts
               if a.get("pharmacy_id") == pharmacy_id]

try:
    restock_resp = requests.get(
        f"{API_URL}/my/recommend-restock",
        headers=headers, timeout=8
    )
    restock_data = restock_resp.json() \
        if restock_resp.status_code == 200 else []
except Exception:
    restock_data = []

critical_count      = sum(1 for item in low_stock    if item.get("days_remaining", 999) < 5)
high_priority_count = sum(1 for item in restock_data if item.get("priority") == "HIGH")

render_page_header(
    "Operational Dashboard",
    "Central workspace for pharmacy performance, replenishment priorities, stock risk monitoring and AI-assisted recommendations.",
    chips=["Pharmacist workspace", "Operational clarity", "Backend preserved"],
    stats=[
        ("Top Sellers",    len(top_selling)),
        ("Restock Alerts", high_priority_count or len(restock_data)),
        ("Critical Risks", critical_count),
    ],
)

# ══════════════════════════════
# SECTION 1: KPIs الشبكة
# ══════════════════════════════
row = st.columns(4)
with row[0]:
    metric_card("Top selling medicines",     len(top_selling),  "Products with visible sales activity",              "blue")
with row[1]:
    metric_card("Restock recommendations",   len(restock_data), "AI-detected reorder opportunities",                 "cyan")
with row[2]:
    metric_card("Low-stock alerts",          len(low_stock),    "Projected stockout signals for your pharmacy",      "amber")
with row[3]:
    metric_card("Scarcity tracked",          len(scarcity) if isinstance(scarcity, list) else 0,
                "Network search failures being monitored", "violet")

# ══════════════════════════════
# SECTION 2: تحليلات الشبكة
# ══════════════════════════════
render_section_header(
    "Network Analytics",
    "Sales performance and market intelligence across all pharmacies"
)
left, right = st.columns([1.4, 1], gap="large")

with left:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Top-Selling Medicines")
    if top_selling:
        df_top = pd.DataFrame(top_selling)
        fig = px.bar(
            df_top,
            x="medicine_name",
            y="total_sold",
            color="total_sold",
            color_continuous_scale=["#BFDBFE", "#3B82F6", "#1D4ED8"],
            title="Units sold by medicine",
        )
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(style_plotly(fig, 420), use_container_width=True)
    else:
        empty_state("No sales data available", "As soon as sales data arrives, the ranking will appear here.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Market Scarcity Signals")
    if scarcity and isinstance(scarcity, list):
        rare    = [s for s in scarcity if s.get("status") == "RARE"]
        limited = [s for s in scarcity if s.get("status") == "LIMITED"]
        k1, k2, k3 = st.columns(3)
        with k1:
            metric_card("Rare medicines",    len(rare),     "High scarcity across searches",       "red")
        with k2:
            metric_card("Limited medicines", len(limited),  "Moderate availability pressure",      "amber")
        with k3:
            metric_card("Tracked products",  len(scarcity), "Network intelligence scope",          "blue")

        for item in scarcity:
            tone = "red" if item.get("status") == "RARE" else "amber"
            st.markdown(
                f"<div style='margin-top:12px; padding:16px 18px; border-radius:18px; background:rgba(255,255,255,0.74); border:1px solid #DBEAFE;'>"
                f"<div style='display:flex; justify-content:space-between; gap:16px; align-items:center; flex-wrap:wrap;'>"
                f"<div><div style='font-weight:800; color:#0F172A;'>{item.get('medicine_name')}</div>"
                f"<div style='margin-top:6px; color:#64748B;'>Scarcity rate: <b>{item.get('scarcity_rate')}%</b> · Failed searches: <b>{item.get('failed_searches')}</b></div></div>"
                f"<div>{badge(item.get('status', 'Tracked'), tone)}</div></div></div>",
                unsafe_allow_html=True,
            )
    else:
        empty_state("No scarcity signals yet", "Search logs will populate this panel when rare medicines start emerging.")
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════
# SECTION 3: AI Tools (الشبكة)
# ══════════════════════════════
render_section_header(
    "AI Intelligence",
    "Demand forecast and transfer recommendations"
)
ai_left, ai_right = st.columns([1.05, 0.95], gap="large")

with ai_left:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Demand Forecast")

    if medicines_list:
        med_options = {m["trade_name"]: m["id"] for m in medicines_list}
        med_name    = st.selectbox("Select medicine", list(med_options.keys()), key="forecast_med")
        forecast_btn = st.button("Run 7-Day Forecast", use_container_width=True)

        if forecast_btn:
            medicine_id_selected = med_options[med_name]
            pred = fetch_json("/predict-demand/", params={"medicine_id": medicine_id_selected}) or {}
            if "forecast_next_7_days" in pred:
                st.markdown(
                    f"<div style='margin-bottom:14px; padding:18px; border-radius:18px; background:linear-gradient(135deg,#0F172A,#1D4ED8); color:white;'>"
                    f"<div style='font-size:1.2rem; font-weight:800;'>{pred['trend']} demand trend</div>"
                    f"<div style='margin-top:8px;'>Total 7-day demand: <b>{pred['total_predicted_demand']}</b></div>"
                    f"<div>Daily average: <b>{pred['average_daily_demand']}</b></div></div>",
                    unsafe_allow_html=True,
                )
                df_forecast = pd.DataFrame({"day": list(range(1, 8)), "forecast": pred["forecast_next_7_days"]})
                fig = px.line(df_forecast, x="day", y="forecast", markers=True, color_discrete_sequence=["#0EA5E9"])
                fig.update_traces(line_width=4)
                st.plotly_chart(style_plotly(fig, 300), use_container_width=True)
            else:
                st.warning(pred.get("message", "No forecast available for this medicine."))
    else:
        st.info("Medicine catalog loading...")
    st.markdown("</div>", unsafe_allow_html=True)

with ai_right:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Smart Transfer Recommendation")

    if medicines_list:
        med_options = {m["trade_name"]: m["id"] for m in medicines_list}
        form_left, form_right = st.columns([1, 1])
        with form_left:
            rec_pharmacy_id = st.number_input("Pharmacy ID", min_value=1, value=int(pharmacy_id), key="rec_pharmacy")
        with form_right:
            rec_med_name = st.selectbox("Medicine", list(med_options.keys()), key="rec_medicine")
        rec_btn = st.button("Generate Recommendation", use_container_width=True)

        if rec_btn:
            rec_medicine_id = med_options[rec_med_name]
            res = fetch_json(
                "/smart-recommendation/",
                params={"pharmacy_id": rec_pharmacy_id, "medicine_id": rec_medicine_id},
            ) or {}
            st.session_state["rec_result"]      = res
            st.session_state["rec_pharmacy_id"] = rec_pharmacy_id
            st.session_state["rec_medicine_id"] = rec_medicine_id
            st.session_state["rec_med_name"]    = rec_med_name

        if "rec_result" in st.session_state:
            res = st.session_state["rec_result"]
            if res.get("action") == "TRANSFER":
                st.markdown(
                    f"""
                    <div style='margin-top:10px; padding:22px; border-radius:22px; background:linear-gradient(135deg, rgba(30,64,175,0.96), rgba(14,165,233,0.92)); color:white;'>
                        <div style='font-size:1.2rem; font-weight:800;'>Recommended Action: {res['action']}</div>
                        <div style='display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:12px; margin-top:16px;'>
                            <div><b>Source Pharmacy</b><br>{res['from_pharmacy']}</div>
                            <div><b>Distance</b><br>{res['distance_km']} km</div>
                            <div><b>Suggested Quantity</b><br>{res['quantity']}</div>
                            <div><b>Predicted Demand</b><br>{res['predicted_demand']}</div>
                        </div>
                        <div style='margin-top:16px; padding:14px; border-radius:16px; background:rgba(255,255,255,0.12);'><b>Rationale</b><br>{res['reason']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Accept Recommendation", key="accept_btn", use_container_width=True):
                        requests.post(
                            f"{API_URL}/feedback/",
                            params={
                                "pharmacy_id":            st.session_state["rec_pharmacy_id"],
                                "medicine_id":            st.session_state["rec_medicine_id"],
                                "recommended_pharmacy_id": res["recommended_pharmacy_id"],
                                "accepted": 1,
                            },
                            timeout=5,
                        )
                        st.success("Feedback saved. The AI will learn from this accepted recommendation.")
                with col_b:
                    if st.button("Reject Recommendation", key="reject_btn", use_container_width=True):
                        requests.post(
                            f"{API_URL}/feedback/",
                            params={
                                "pharmacy_id":            st.session_state["rec_pharmacy_id"],
                                "medicine_id":            st.session_state["rec_medicine_id"],
                                "recommended_pharmacy_id": res["recommended_pharmacy_id"],
                                "accepted": 0,
                            },
                            timeout=5,
                        )
                        st.warning("Feedback saved. The AI will avoid similar recommendations next time.")
            else:
                st.warning(res.get("message", "No recommendation available."))
    else:
        st.info("Loading medicine catalog...")
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════
# SECTION 4: صيدليتي فقط
# ══════════════════════════════
st.markdown("""
<div style='background:linear-gradient(135deg,#1E3A8A,#2563EB);
            border-radius:14px; padding:16px 24px; margin:24px 0 16px;'>
    <div style='color:white; font-size:16px; font-weight:800;'>
        🏥 My Pharmacy — Private Section
    </div>
    <div style='color:#BFDBFE; font-size:13px; margin-top:4px;'>
        Data exclusive to Pharmacy {pharmacy_id}
    </div>
</div>
""".format(pharmacy_id=pharmacy_id), unsafe_allow_html=True)

render_section_header(
    "Auto Restock Recommendations",
    f"Specific reorder suggestions for Pharmacy {pharmacy_id}"
)
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if restock_data:
    df_restock = pd.DataFrame(restock_data)
    if "priority" in df_restock.columns:
        df_restock["priority"] = df_restock["priority"].map(
            lambda p: "High" if p == "HIGH" else ("Medium" if p == "MEDIUM" else "Low")
        )
    st.dataframe(df_restock, use_container_width=True, hide_index=True)
else:
    empty_state("Inventory stable", "No medicines currently require urgent replenishment.")
st.markdown("</div>", unsafe_allow_html=True)

render_section_header(
    "⚠️ Medicines About to Run Out",
    f"Stockout risk for Pharmacy {pharmacy_id} only"
)
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if low_stock:
    df_low = pd.DataFrame(low_stock)
    if "medicine_id" in df_low.columns:
        df_low["medicine_name"] = df_low["medicine_id"].map(lambda x: med_lookup.get(x, f"Medicine {x}"))
        df_low = df_low.drop(columns=["medicine_id"], errors="ignore")
    st.dataframe(df_low, use_container_width=True, hide_index=True)
    for row_item in low_stock:
        days     = row_item.get("days_remaining", 0)
        tone     = "red" if days < 5 else "amber"
        status   = badge("Critical" if days < 5 else "Watch", tone)
        med_name = med_lookup.get(row_item.get("medicine_id"), f"Medicine {row_item.get('medicine_id')}")
        st.markdown(
            f"<div style='margin-top:10px; padding:14px 16px; background:rgba(255,255,255,0.72); border:1px solid #DBEAFE; border-radius:16px;'>"
            f"<b>{med_name}</b> · {days} days remaining · {status}</div>",
            unsafe_allow_html=True,
        )
else:
    empty_state("No projected shortages", "Current data indicates safe stock levels across your pharmacy.")
st.markdown("</div>", unsafe_allow_html=True)