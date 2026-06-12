import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from sidebar import render_sidebar
from ui_kit import apply_theme, empty_state, metric_card, render_page_header, render_section_header, style_plotly

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Monitoring", layout="wide")
if not st.session_state.get("token"):
    st.warning("Please sign in first.")
    st.page_link("login.py", label="Go to Sign In")
    st.stop()

apply_theme()
render_sidebar()

# Fetch medicine list for name lookup
try:
    medicines_list = requests.get(f"{API_URL}/medicines/", timeout=8).json()
    med_options = {m["trade_name"]: m["id"] for m in medicines_list}
except Exception:
    medicines_list = []
    med_options = {}


def fetch_json(endpoint, method="get", **kwargs):
    try:
        response = getattr(requests, method)(f"{API_URL}{endpoint}", timeout=8, **kwargs)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None


metrics = fetch_json("/ai-metrics/") or {}
time_data = fetch_json("/ai-metrics-over-time/") or []
market = fetch_json("/top-medicines-demand/") or []
check = fetch_json("/ai/retrain/check") or {}
logs = fetch_json("/ai/training-logs") or []

render_page_header(
    "AI Monitoring",
    "Operational view of recommendation quality, model confidence, learning progression and retraining readiness.",
    chips=["Model quality", "Retraining readiness", "Operational AI trust"],
    stats=[
        ("Total Decisions", metrics.get("total_recommendations", 0)),
        ("Acceptance", f"{metrics.get('acceptance_rate', 0)}%"),
        ("Confidence", f"{metrics.get('confidence', 0)}%"),
    ],
)

cols = st.columns(4)
with cols[0]:
    metric_card("Total decisions", metrics.get("total_recommendations", 0), "All AI recommendations generated", "blue")
with cols[1]:
    metric_card("Accepted", metrics.get("accepted", 0), "Validated by pharmacist feedback", "green")
with cols[2]:
    metric_card("Rejected", metrics.get("rejected", 0), "Recommendations declined", "red")
with cols[3]:
    metric_card("Acceptance rate", f"{metrics.get('acceptance_rate', 0)}%", "Overall AI usefulness", "cyan")

render_section_header("Model Confidence", "Use confidence and retraining logic to assess model reliability.")
left, right = st.columns([1, 1], gap="large")

confidence = int(metrics.get("confidence", 0) or 0)
confidence_label = "System is performing well" if confidence >= 70 else ("System needs more data" if confidence >= 40 else "System needs improvement")
confidence_tone = "green" if confidence >= 70 else ("amber" if confidence >= 40 else "red")
confidence_bg = "#DCFCE7" if confidence >= 70 else ("#FEF3C7" if confidence >= 40 else "#FEE2E2")
confidence_color = "#166534" if confidence >= 70 else ("#92400E" if confidence >= 40 else "#991B1B")

with left:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Confidence Level")
    st.markdown(
        f"<div style='padding:18px; border-radius:18px; background:{confidence_bg}; color:{confidence_color}; border:1px solid {confidence_color}22;'>"
        f"<div style='font-size:1.4rem; font-weight:800;'>{confidence}%</div>"
        f"<div style='margin-top:6px; font-weight:600;'>{confidence_label}</div></div>",
        unsafe_allow_html=True,
    )
    st.progress(confidence)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Retraining Status")
    if check:
        retrain = check.get("retrain", False)
        bg = "#FEF3C7" if retrain else "#DCFCE7"
        color = "#92400E" if retrain else "#166534"
        title = "Retraining needed" if retrain else "Model stable"
        st.markdown(
            f"<div style='padding:20px; border-radius:18px; background:{bg}; color:{color}; border:1px solid {color}22;'>"
            f"<div style='font-size:1.2rem; font-weight:800;'>{title}</div>"
            f"<div style='margin-top:8px;'>Status: <b>{check.get('reason', '—')}</b></div>"
            f"<div>Acceptance rate: <b>{check.get('acceptance_rate', 0)}%</b></div>"
            f"<div>Total decisions: <b>{check.get('total_decisions', 0)}</b></div></div>",
            unsafe_allow_html=True,
        )
        # Use medicine name instead of ID for retraining
        if med_options:
            retrain_med_name = st.selectbox("Medicine to retrain", list(med_options.keys()), key="retrain_med")
            if st.button("Run Manual Retraining", use_container_width=True):
                retrain_medicine_id = med_options[retrain_med_name]
                result = fetch_json("/ai/retrain", method="post", params={"medicine_id": retrain_medicine_id}) or {}
                if result.get("status") == "Model retrained successfully":
                    st.success(f"{result['status']} — {result.get('data_points', 0)} data points used for {retrain_med_name}")
                else:
                    st.warning(result.get("status", "Retraining request could not be completed."))
        else:
            st.info("Loading medicine catalog...")
    else:
        empty_state("Retraining rule unavailable", "The retraining decision engine did not return data.")
    st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Learning Trends", "Track acceptance over time and monitor demand pressure.")
trend_left, trend_right = st.columns([1.1, 0.9], gap="large")

with trend_left:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Acceptance Trend")
    if time_data:
        df_time = pd.DataFrame(time_data)
        fig = px.line(
            df_time,
            x="date",
            y="acceptance_rate",
            markers=True,
            color_discrete_sequence=["#2563EB"],
            title="Acceptance rate trend",
        )
        fig.update_traces(line_width=4)
        fig.update_yaxes(title="Acceptance rate (%)")
        st.plotly_chart(style_plotly(fig, 370), use_container_width=True)
    else:
        empty_state("Not enough data yet", "Acceptance trend will appear after more feedback is collected.")
    st.markdown("</div>", unsafe_allow_html=True)

with trend_right:
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    st.subheader("Market Intelligence")
    if market:
        df_market = pd.DataFrame(market)
        fig2 = px.bar(
            df_market,
            x="medicine_name",
            y="demand",
            color="demand",
            color_continuous_scale=["#DBEAFE", "#60A5FA", "#1D4ED8"],
            title="Medicine demand in network",
        )
        fig2.update_coloraxes(showscale=False)
        st.plotly_chart(style_plotly(fig2, 370), use_container_width=True)
    else:
        empty_state("No market data available", "Demand ranking will display here once usage data is available.")
    st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Decision Distribution", "Review the split between accepted and rejected recommendations.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if metrics.get("total_recommendations", 0) > 0:
    df_pie = pd.DataFrame(
        {
            "Decision": ["Accepted", "Rejected"],
            "Count": [metrics.get("accepted", 0), metrics.get("rejected", 0)],
        }
    )
    fig3 = px.pie(df_pie, values="Count", names="Decision", color_discrete_sequence=["#2563EB", "#EF4444"])
    st.plotly_chart(style_plotly(fig3, 360), use_container_width=True)
else:
    empty_state("No decision feedback", "The breakdown will appear once AI recommendations start receiving responses.")
st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Retraining History", "Maintain a readable audit trail of retraining operations.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if logs:
    df_logs = pd.DataFrame(logs)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
else:
    empty_state("No training history yet", "Retrain a model to start building the history log.")
st.markdown("</div>", unsafe_allow_html=True)