import requests
import streamlit as st

from sidebar import render_sidebar
from ui_kit import apply_theme, badge, empty_state, metric_card, render_page_header, render_section_header

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Operations", layout="wide")

if not st.session_state.get("token"):
    st.warning("Please sign in first. Use the sidebar to access the sign-in page.")
    st.stop()
if st.session_state.get("is_admin"):
    st.error("This workspace is available to pharmacists only.")
    st.stop()

apply_theme()
render_sidebar()

token = st.session_state["token"]
pharmacy_id = st.session_state["pharmacy_id"]
headers = {"Authorization": f"Bearer {token}"}


def get_json(url, **kwargs):
    try:
        response = requests.get(url, timeout=8, **kwargs)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None


try:
    medicines_list = requests.get(f"{API_URL}/medicines/", timeout=8).json()
    med_options = {m["trade_name"]: m["id"] for m in medicines_list}
    med_lookup = {m["id"]: m["trade_name"] for m in medicines_list}
except Exception:
    medicines_list = []
    med_options = {}
    med_lookup = {}

inventory = get_json(f"{API_URL}/my/inventory/", headers=headers) or []
notifications = get_json(f"{API_URL}/my/notifications/", headers=headers) or []

critical_items = sum(1 for item in inventory if item.get("quantity", 0) < 20)
render_page_header(
    "Operations Center",
    "Execution workspace for stock updates, sales registration, transfer requests, forecasting and operational notifications.",
    chips=["Pharmacist workspace", "Task-focused layout", "Backend preserved"],
    stats=[
        ("Pharmacy ID", pharmacy_id),
        ("Inventory Lines", len(inventory)),
        ("Critical Items", critical_items),
    ],
)

kpis = st.columns(4)
with kpis[0]:
    metric_card("Inventory lines", len(inventory), "Products currently visible in stock", "blue")
with kpis[1]:
    metric_card("Critical stock", critical_items, "Items under 20 units", "red")
with kpis[2]:
    metric_card("Unread notifications", sum(1 for n in notifications if not n.get("is_read")), "Messages still requiring attention", "amber")
with kpis[3]:
    metric_card("Catalog size", len(medicines_list), "Medicines available in the system", "cyan")

render_section_header("Inventory Snapshot", "Review current stock health and priority items.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if inventory:
    grid_cols = st.columns(4)
    for i, item in enumerate(inventory[:12]):
        qty = item.get("quantity", 0)
        med_name = med_lookup.get(item.get("medicine_id"), f"Medicine {item.get('medicine_id')}")
        tone = "green" if qty >= 50 else ("amber" if qty >= 20 else "red")
        caption = "Healthy stock" if qty >= 50 else ("Monitor soon" if qty >= 20 else "Action required")
        with grid_cols[i % 4]:
            metric_card(med_name, qty, caption, tone)
else:
    empty_state("No inventory data", "Inventory cards will populate as soon as stock data becomes available.")
st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Operational Workflows", "Grouped workflows for day-to-day pharmacy execution.")
action_tabs = st.tabs(["Stock & Sales", "Transfer & Forecast", "Notifications", "Catalog"])

with action_tabs[0]:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
        st.subheader("Add Stock")
        if med_options:
            with st.form("add_stock_form"):
                med_name_add = st.selectbox("Medicine", list(med_options.keys()), key="add_med")
                qty_add = st.number_input("Quantity to add", min_value=1, value=50, key="add_qty")
                add_submit = st.form_submit_button("Add Stock")

            if add_submit:
                med_id = med_options[med_name_add]
                try:
                    r = requests.post(
                        f"{API_URL}/stock-movement/",
                        params={"pharmacy_id": pharmacy_id, "medicine_id": med_id, "quantity": qty_add},
                        timeout=20,
                    )
                    if r.status_code == 200:
                        st.success(f"Added {qty_add} units of {med_name_add}.")
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", "Unknown error while adding stock."))
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            empty_state("Medicine catalog unavailable", "Load medicines first to enable stock operations.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
        st.subheader("Record Patient Sale")
        st.markdown(
            "<div style='padding:12px 14px; border-radius:14px; background:#FFF7ED; border:1px solid #FED7AA; color:#9A3412; margin-bottom:14px;'>"
            "Stock is deducted automatically and AI signals update from this movement."
            "</div>",
            unsafe_allow_html=True,
        )
        if med_options:
            with st.form("sell_stock_form"):
                med_name_sell = st.selectbox("Medicine", list(med_options.keys()), key="sell_med")
                qty_sell = st.number_input("Quantity sold", min_value=1, value=1, key="sell_qty")
                sell_submit = st.form_submit_button("Record Sale")

            if sell_submit:
                med_id = med_options[med_name_sell]
                try:
                    r = requests.post(
                        f"{API_URL}/stock-movement/",
                        params={"pharmacy_id": pharmacy_id, "medicine_id": med_id, "quantity": -qty_sell},
                        timeout=20,
                    )
                    if r.status_code == 200:
                        st.success(f"Sale recorded: -{qty_sell} units of {med_name_sell}.")
                        st.rerun()
                    else:
                        err = r.json().get("detail", r.json().get("error", "Unknown error"))
                        st.error(err)
                except Exception as e:
                    st.error(f"Connection error: {e}")
        else:
            empty_state("Medicine catalog unavailable", "Load medicines first to enable sales recording.")
        st.markdown("</div>", unsafe_allow_html=True)

with action_tabs[1]:
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
        st.subheader("Request Transfer Recommendation")
        if med_options:
            med_name_transfer = st.selectbox("Medicine needed", list(med_options.keys()), key="transfer_med")
            if st.button("Generate Recommendation", key="btn_transfer", use_container_width=True):
                med_id = med_options[med_name_transfer]
                try:
                    rec = requests.get(
                        f"{API_URL}/smart-recommendation/",
                        params={"pharmacy_id": pharmacy_id, "medicine_id": med_id},
                        timeout=20,
                    ).json()
                    st.session_state["op_transfer_result"] = rec
                    st.session_state["op_transfer_med_id"] = med_id
                    st.session_state["op_transfer_med_name"] = med_name_transfer
                except Exception as e:
                    st.error(f"Error: {e}")

            rec = st.session_state.get("op_transfer_result")
            if rec:
                if rec.get("action") == "TRANSFER":
                    st.markdown(
                        f"<div style='margin-top:14px; padding:18px; border-radius:18px; background:linear-gradient(135deg,#EFF6FF,#DBEAFE); border:1px solid #BFDBFE;'>"
                        f"<div style='font-size:1.1rem; font-weight:800; color:#1E3A8A;'>Recommended Transfer</div>"
                        f"<div style='margin-top:12px; color:#1E3A8A; line-height:1.8;'>"
                        f"<b>Source Pharmacy:</b> {rec['from_pharmacy']}<br>"
                        f"<b>Distance:</b> {rec['distance_km']} km<br>"
                        f"<b>Suggested Quantity:</b> {rec['quantity']} units<br>"
                        f"<b>Predicted Demand:</b> {rec['predicted_demand']} units/7d<br>"
                        f"<b>Score:</b> {rec.get('score', '—')}"
                        f"</div><div style='margin-top:12px; padding:12px; border-radius:14px; background:white; color:#334155;'><b>Rationale</b><br>{rec['reason']}</div></div>",
                        unsafe_allow_html=True,
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Accept Recommendation", key="accept_transfer", use_container_width=True):
                            requests.post(
                                f"{API_URL}/feedback/",
                                params={
                                    "pharmacy_id": pharmacy_id,
                                    "medicine_id": st.session_state["op_transfer_med_id"],
                                    "recommended_pharmacy_id": rec["recommended_pharmacy_id"],
                                    "accepted": 1,
                                },
                                timeout=5,
                            )
                            st.success("Feedback saved.")
                    with c2:
                        if st.button("Reject Recommendation", key="reject_transfer", use_container_width=True):
                            requests.post(
                                f"{API_URL}/feedback/",
                                params={
                                    "pharmacy_id": pharmacy_id,
                                    "medicine_id": st.session_state["op_transfer_med_id"],
                                    "recommended_pharmacy_id": rec["recommended_pharmacy_id"],
                                    "accepted": 0,
                                },
                                timeout=5,
                            )
                            st.warning("Feedback saved.")
                else:
                    st.warning(rec.get("message", "No pharmacy available with stock."))
        else:
            empty_state("Medicine catalog unavailable", "Transfer recommendation requires the medicine list.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
        st.subheader("Stock Forecast")
        if med_options:
            med_predict = st.selectbox("Select medicine", list(med_options.keys()), key="pred_med")
            if st.button("Run Stock Forecast", key="btn_predict", use_container_width=True):
                med_id = med_options[med_predict]
                try:
                    prediction = requests.get(
                        f"{API_URL}/my/predict-stock/",
                        params={"medicine_id": med_id},
                        headers=headers,
                        timeout=8,
                    ).json()
                    st.session_state["op_prediction"] = (med_predict, prediction)
                except Exception as e:
                    st.error(f"Error: {e}")

            if "op_prediction" in st.session_state:
                med_predict_name, prediction = st.session_state["op_prediction"]
                if "estimated_days_remaining" in prediction:
                    days = prediction["estimated_days_remaining"]
                    tone = "green" if days > 14 else ("amber" if days > 7 else "red")
                    label = "Safe" if days > 14 else ("Warning" if days > 7 else "Critical")
                    st.markdown(
                        f"<div style='margin-top:14px; padding:18px; border-radius:18px; background:white; border:1px solid #DBEAFE;'>"
                        f"<div style='font-size:1.1rem; font-weight:800; color:#0F172A;'>{med_predict_name} — stock forecast</div>"
                        f"<div style='display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px; margin-top:14px;'>"
                        f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>Current stock</div><div style='font-size:1.4rem; font-weight:800;'>{prediction['current_stock']}</div></div>"
                        f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>Daily average sales</div><div style='font-size:1.4rem; font-weight:800;'>{prediction['daily_average_sales']}</div></div>"
                        f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>Days remaining</div><div style='font-size:1.4rem; font-weight:800;'>{days}</div></div>"
                        f"<div><div style='color:#64748B; font-size:0.8rem; text-transform:uppercase;'>Status</div><div style='margin-top:6px;'>{badge(label, tone)}</div></div></div>"
                        f"<div style='margin-top:14px; color:#64748B;'>Estimated stockout date: <b>{prediction.get('predicted_stock_out_date', 'N/A')}</b></div></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.info(prediction.get("message", "Not enough data for prediction."))
        else:
            empty_state("Medicine catalog unavailable", "Prediction requires a medicine selection.")
        st.markdown("</div>", unsafe_allow_html=True)

with action_tabs[2]:
    render_section_header("Notifications", "Review operational events and mark them as processed.")
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    if notifications:
        for n in notifications[:8]:
            tone = "amber" if n.get("type") == "low_stock" else ("cyan" if n.get("type") == "ai_recommendation" else "green")
            st.markdown(
                f"<div style='padding:15px 16px; border-radius:16px; background:rgba(255,255,255,0.72); border:1px solid #DBEAFE; margin-bottom:10px;'>"
                f"<div style='display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:center;'>"
                f"<div><b>[{str(n.get('type', 'info')).upper()}]</b> {n.get('message')}</div>"
                f"<div>{badge('Unread' if not n.get('is_read') else 'Read', tone)}</div></div>"
                f"<div style='margin-top:8px; color:#64748B; font-size:0.9rem;'>Created: {str(n.get('created_at', ''))[:10]}</div></div>",
                unsafe_allow_html=True,
            )
            if not n.get("is_read"):
                if st.button(f"Mark notification {n['id']} as read", key=f"read_{n['id']}", use_container_width=True):
                    requests.post(f"{API_URL}/my/notifications/read/{n['id']}", headers=headers, timeout=5)
                    st.rerun()
    else:
        empty_state("No notifications", "You have no operational notifications at the moment.")
    st.markdown("</div>", unsafe_allow_html=True)

with action_tabs[3]:
    render_section_header("Catalog Management", "Register a new medicine without affecting backend logic.")
    st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
    with st.form("add_new_medicine"):
        col1, col2 = st.columns(2)
        with col1:
            new_trade_name = st.text_input("Trade name", placeholder="Ex: Paracetamol 500mg")
            new_dosage = st.text_input("Dosage", placeholder="Ex: 500mg")
        with col2:
            new_active = st.text_input("Active ingredient", placeholder="Ex: Paracetamol")
            new_form = st.selectbox("Form", ["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Drops", "Suppository"])
        add_med_btn = st.form_submit_button("Add medicine to system")

    if add_med_btn:
        if not new_trade_name or not new_active or not new_dosage:
            st.error("Please fill all fields.")
        else:
            try:
                r = requests.post(
                    f"{API_URL}/medicines/",
                    json={
                        "trade_name": new_trade_name,
                        "active_ingredient": new_active,
                        "dosage": new_dosage,
                        "form": new_form,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=8,
                )
                if r.status_code == 200:
                    data = r.json()
                    st.success(f"{new_trade_name} added successfully. ID: {data.get('id')}")
                    st.rerun()
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)