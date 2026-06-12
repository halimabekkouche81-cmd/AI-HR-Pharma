import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from sidebar import render_sidebar
from ui_kit import apply_theme, badge, empty_state, metric_card, render_page_header, render_section_header, style_plotly

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Admin Dashboard", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please sign in first.")
    st.stop()
if not st.session_state.get("is_admin"):
    st.error("Access restricted to administrators.")
    st.stop()

apply_theme()
render_sidebar()

# Fetch medicine list for name lookup
try:
    medicines_list = requests.get(f"{API_URL}/medicines/", timeout=8).json()
    med_lookup = {m["id"]: m["trade_name"] for m in medicines_list}
except Exception:
    medicines_list = []
    med_lookup = {}


def fetch_json(endpoint, method="get", **kwargs):
    try:
        response = getattr(requests, method)(f"{API_URL}{endpoint}", timeout=8, **kwargs)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None


pharmacies = fetch_json("/pharmacy-map") or []
medicines = fetch_json("/medicines/") or []
metrics = fetch_json("/ai-metrics/") or {}
logs = fetch_json("/ai/training-logs") or []
eval_data = fetch_json("/ai/evaluate/", params={"medicine_id": 1}) or {}
top = fetch_json("/analytics/top-selling/") or []
scarcity = fetch_json("/market-scarcity/") or {}

network_count = len(set(p.get("pharmacy_name") for p in pharmacies if p.get("pharmacy_name")))
render_page_header(
    "Admin Dashboard",
    "Executive workspace for network visibility, stock distribution, AI performance and scarcity monitoring.",
    chips=["Network overview", "Executive analytics", "Backend preserved"],
    stats=[
        ("Pharmacies", network_count),
        ("Medicines", len(medicines)),
        ("AI Decisions", metrics.get("total_recommendations", 0)),
    ],
)

kpi_cols = st.columns(5)
with kpi_cols[0]:
    metric_card("Connected pharmacies", network_count, "Mapped branches in the network", "blue")
with kpi_cols[1]:
    metric_card("Medicine catalog", len(medicines), "Products registered in the system", "cyan")
with kpi_cols[2]:
    metric_card("AI decisions", metrics.get("total_recommendations", 0), "Recorded recommendation events", "violet")
with kpi_cols[3]:
    metric_card("Acceptance rate", f"{metrics.get('acceptance_rate', 0)}%", "Quality of AI decisions", "green")
with kpi_cols[4]:
    metric_card("Retraining runs", len(logs), "Historical model retraining operations", "amber")

render_section_header("Executive Overview", "Review model performance and medicine movement at network level.")
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("AI Model Status")
    if "winner" in eval_data and eval_data.get("models"):
        models_data = eval_data["models"]
        lr = next((m for m in models_data if m.get("model") == "Linear Regression"), {})
        prp = next((m for m in models_data if m.get("model") == "Prophet"), {})
        st.markdown(
            f"<div style='padding:18px; border-radius:18px; background:linear-gradient(135deg,#0F172A,#1D4ED8); color:white; margin-bottom:14px;'>"
            f"<div style='font-size:1.25rem; font-weight:800;'>Best Model: {eval_data.get('winner')}</div>"
            f"<div style='margin-top:8px;'>Linear Regression MAE: <b>{lr.get('mae', '—')}</b></div>"
            f"<div>Prophet MAE: <b>{prp.get('mae', '—')}</b></div></div>",
            unsafe_allow_html=True,
        )
        if models_data:
            df_models = pd.DataFrame(
                {
                    "Model": [m.get("model") for m in models_data],
                    "MAE": [m.get("mae") for m in models_data],
                    "RMSE": [m.get("rmse") for m in models_data],
                }
            )
            fig = px.bar(df_models, x="Model", y=["MAE", "RMSE"], barmode="group", title="Error comparison")
            st.plotly_chart(style_plotly(fig, 320), use_container_width=True)
    else:
        empty_state("Model comparison unavailable", "More data is needed before the system can determine the best model.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Top-Selling Medicines")
    if top:
        df_top = pd.DataFrame(top)
        fig = px.bar(
            df_top,
            x="medicine_name",
            y="total_sold",
            color="total_sold",
            color_continuous_scale=["#C4B5FD", "#3B82F6", "#1D4ED8"],
            title="Total units sold per medicine",
        )
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(style_plotly(fig, 380), use_container_width=True)
    else:
        empty_state("No sales data yet", "Once medicines begin moving through the network, this chart will appear here.")
    st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Network Stock Distribution", "Review stock allocation across pharmacy branches.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if pharmacies:
    df_map = pd.DataFrame(pharmacies)
    df_summary = df_map.groupby("pharmacy_name")["quantity"].sum().reset_index()
    df_summary.columns = ["Pharmacy", "Total Stock"]
    df_summary = df_summary.sort_values("Total Stock", ascending=False)
    fig2 = px.bar(
        df_summary,
        x="Pharmacy",
        y="Total Stock",
        color="Total Stock",
        color_continuous_scale=["#DCFCE7", "#22C55E", "#15803D"],
        title="Total stock per pharmacy",
    )
    fig2.update_coloraxes(showscale=False)
    fig2.update_xaxes(tickangle=-24)
    st.plotly_chart(style_plotly(fig2, 420), use_container_width=True)
else:
    empty_state("Map data unavailable", "Pharmacy stock data could not be loaded.")
st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Retraining Audit", "Review recent retraining activity for governance and traceability.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if logs:
    df_logs = pd.DataFrame(logs)
    # Replace medicine_id with name if present
    if "medicine_id" in df_logs.columns:
        df_logs["medicine_name"] = df_logs["medicine_id"].map(lambda x: med_lookup.get(x, f"Medicine {x}"))
        # Reorder columns to show name first if it exists
        cols = ["medicine_name"] + [c for c in df_logs.columns if c != "medicine_name"]
        df_logs = df_logs[cols]
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
else:
    empty_state("No training history", "Retraining events will appear here once models are updated.")
st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Scarcity Signals", "Monitor medicines repeatedly searched but unavailable in the network.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if scarcity:
    rare = [s for s in scarcity if s.get("status") == "RARE"]
    limited = [s for s in scarcity if s.get("status") == "LIMITED"]
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Rare medicines", len(rare), "Highest urgency items", "red")
    with c2:
        metric_card("Limited medicines", len(limited), "Availability pressure", "amber")
    with c3:
        metric_card("Tracked products", len(scarcity), "Monitored from search demand", "blue")

    for item in scarcity:
        tone = "red" if item.get("status") == "RARE" else "amber"
        st.markdown(
            f"<div style='margin-top:12px; padding:18px; border-radius:18px; background:rgba(255,255,255,0.76); border:1px solid #DBEAFE;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;'>"
            f"<div><div style='font-weight:800; color:#0F172A;'>{item.get('medicine_name')}</div>"
            f"<div style='margin-top:8px; color:#64748B;'>Scarcity rate <b>{item.get('scarcity_rate')}%</b> · Failed searches <b>{item.get('failed_searches')}</b></div></div>"
            f"<div>{badge(item.get('status', 'Tracked'), tone)}</div></div></div>",
            unsafe_allow_html=True,
        )
else:
    empty_state("No scarcity signals", "Scarcity monitoring starts once medicine searches are logged across the network.")
st.markdown("</div>", unsafe_allow_html=True)