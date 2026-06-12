import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from sidebar import render_sidebar
from ui_kit import apply_theme, empty_state, metric_card, render_page_header, render_section_header, style_plotly

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Model Comparison", layout="wide")
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

render_page_header(
    "Model Comparison",
    "Compare forecasting models with readable metrics, performance charts and decision-ready interpretation.",
    chips=["Model diagnostics", "Readable comparisons", "Decision-ready visuals"],
)

st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
left, right = st.columns([2.2, 1], gap="large")
with left:
    if med_options:
        med_name = st.selectbox("Select medicine", list(med_options.keys()), key="eval_med")
    else:
        st.info("Loading medicine catalog...")
        med_name = None
with right:
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    eval_btn = st.button("Run Comparison", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if not eval_btn or not med_name:
    empty_state("Ready to evaluate", "Choose a medicine and run the evaluation to compare forecasting models.")
    st.stop()

medicine_id = med_options[med_name]

with st.spinner("Running model evaluation..."):
    try:
        response = requests.get(
            f"{API_URL}/ai/evaluate/",
            params={"medicine_id": medicine_id},
            timeout=20,
        ).json()
    except Exception as exc:
        st.error(f"Unable to run evaluation: {exc}")
        st.stop()

if "error" in response:
    st.error(f"{response['error']} — {response.get('data_points', 0)} points available")
    st.stop()

models = response["models"]
render_section_header("Evaluation Summary", f"Review date coverage, dataset size and model selection for {med_name}.")
cols = st.columns(4)
with cols[0]:
    metric_card("Winner", response.get("winner", "—"), "Model with the best error profile", "green")
with cols[1]:
    metric_card("Data points", response.get("data_points", 0), "Daily records used for evaluation", "blue")
with cols[2]:
    metric_card("Start date", response.get("date_range", {}).get("start", "—"), "Dataset coverage begins", "cyan")
with cols[3]:
    metric_card("End date", response.get("date_range", {}).get("end", "—"), "Dataset coverage ends", "violet")

render_section_header("Performance Comparison", "Compare error profile and train-test split for each model.")
card_cols = st.columns(2, gap="large")
for i, model in enumerate(models[:2]):
    is_winner = model["model"] == response["winner"]
    bg = "#DCFCE7" if is_winner else "#EFF6FF"
    border = "#16A34A" if is_winner else "#2563EB"
    with card_cols[i]:
        st.markdown(
            f"<div class='ui-panel' style='background:{bg}; border-color:{border}44;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;'>"
            f"<div style='font-size:1.2rem; font-weight:800; color:#0F172A;'>{model['model']}</div>"
            f"<div style='padding:6px 12px; border-radius:999px; background:white; color:{border}; font-weight:800;'>{'Winner' if is_winner else 'Compared'}</div></div>"
            f"<div style='display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px; margin-top:16px;'>"
            f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>MAE</div><div style='font-size:1.5rem; font-weight:800; color:#0F172A;'>{model['mae']}</div></div>"
            f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>RMSE</div><div style='font-size:1.5rem; font-weight:800; color:#0F172A;'>{model['rmse']}</div></div>"
            f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>Train size</div><div style='font-size:1.1rem; font-weight:700; color:#0F172A;'>{model['train_size']}</div></div>"
            f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>Test size</div><div style='font-size:1.1rem; font-weight:700; color:#0F172A;'>{model['test_size']}</div></div></div>"
            f"<div style='margin-top:14px; color:#334155; line-height:1.65;'>{model['interpretation']}</div></div>",
            unsafe_allow_html=True,
        )

render_section_header("Error Analysis", "Compare MAE and RMSE to assess consistency.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
df_metrics = pd.DataFrame(
    {
        "Model": [m["model"] for m in models],
        "MAE": [m["mae"] for m in models],
        "RMSE": [m["rmse"] for m in models],
    }
)
fig = go.Figure()
fig.add_trace(go.Bar(name="MAE", x=df_metrics["Model"], y=df_metrics["MAE"], marker_color=["#2563EB", "#06B6D4"]))
fig.add_trace(go.Bar(name="RMSE", x=df_metrics["Model"], y=df_metrics["RMSE"], marker_color=["#93C5FD", "#A5F3FC"]))
fig.update_layout(barmode="group", title="MAE and RMSE comparison", yaxis_title="Error value")
st.plotly_chart(style_plotly(fig, 360), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Actual vs Predicted", "Inspect how each model tracks the test set.")
pred_cols = st.columns(2, gap="large")
for i, key in enumerate(["lr_details", "prophet_details"]):
    details = response[key]
    with pred_cols[i]:
        st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
        st.subheader(details["model"])
        if "y_test" in details and "y_pred" in details:
            df_pred = pd.DataFrame(
                {
                    "Index": range(len(details["y_test"])),
                    "Actual": details["y_test"],
                    "Predicted": [round(p, 2) for p in details["y_pred"]],
                }
            )
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_pred["Index"], y=df_pred["Actual"], mode="lines+markers", name="Actual", line=dict(color="#1E40AF", width=3)))
            fig2.add_trace(go.Scatter(x=df_pred["Index"], y=df_pred["Predicted"], mode="lines+markers", name="Predicted", line=dict(color="#EF4444", width=3, dash="dash")))
            fig2.update_layout(title=f"{details['model']} — actual vs predicted", yaxis_title="Sales")
            st.plotly_chart(style_plotly(fig2, 340), use_container_width=True)
        else:
            empty_state("Prediction details unavailable", "The evaluation response did not include test predictions.")
        st.markdown("</div>", unsafe_allow_html=True)

render_section_header("7-Day Forecast", "Compare short-term projections side by side.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
df_forecast = pd.DataFrame(
    {
        "Day": [f"Day {i + 1}" for i in range(7)],
        "Linear Regression": models[0]["forecast_7_days"],
        "Prophet": models[1]["forecast_7_days"],
    }
)
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=df_forecast["Day"], y=df_forecast["Linear Regression"], mode="lines+markers", name="Linear Regression", line=dict(color="#2563EB", width=3)))
fig3.add_trace(go.Scatter(x=df_forecast["Day"], y=df_forecast["Prophet"], mode="lines+markers", name="Prophet", line=dict(color="#10B981", width=3)))
fig3.update_layout(title="7-day sales forecast", yaxis_title="Predicted sales")
st.plotly_chart(style_plotly(fig3, 360), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Summary Table", "Use the final table for validation, reporting and model selection.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
df_summary = pd.DataFrame(
    {
        "Model": [m["model"] for m in models],
        "MAE": [m["mae"] for m in models],
        "RMSE": [m["rmse"] for m in models],
        "Train Size": [m["train_size"] for m in models],
        "Test Size": [m["test_size"] for m in models],
        "Interpretation": [m["interpretation"] for m in models],
        "Selection": ["Selected" if m["model"] == response["winner"] else "Compared" for m in models],
    }
)
st.dataframe(df_summary, use_container_width=True, hide_index=True)
st.success(f"Best model for {med_name}: {response['winner']} with the strongest error performance on this dataset.")
st.markdown("</div>", unsafe_allow_html=True)