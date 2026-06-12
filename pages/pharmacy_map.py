import folium
from folium.plugins import MarkerCluster
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

from sidebar import render_sidebar
from ui_kit import apply_theme, empty_state, metric_card, render_page_header, render_section_header

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Network Map", layout="wide")
if not st.session_state.get("token"):
    st.warning("Please sign in first.")
    st.page_link("login.py", label="Go to Sign In")
    st.stop()

apply_theme()
render_sidebar()

try:
    data = requests.get(f"{API_URL}/pharmacy-map", timeout=8).json()
except Exception:
    data = []

unique_pharmacies = len(set(p.get("pharmacy_name") for p in data if p.get("pharmacy_name")))
available_count = sum(1 for p in data if p.get("quantity", 0) > 0)
unavailable_count = sum(1 for p in data if p.get("quantity", 0) <= 0)

render_page_header(
    "Network Map",
    "Geographic view of pharmacy branches and medicine availability across the network.",
    chips=["Location intelligence", "Availability visualization", "Fast map scanning"],
    stats=[
        ("Branches", unique_pharmacies),
        ("Available", available_count),
        ("Unavailable", unavailable_count),
    ],
)

cols = st.columns(3)
with cols[0]:
    metric_card("Mapped branches", unique_pharmacies, "Distinct pharmacies in the network", "blue")
with cols[1]:
    metric_card("Available entries", available_count, "Medicine records with stock > 0", "green")
with cols[2]:
    metric_card("Unavailable entries", unavailable_count, "Medicine records without stock", "red")

render_section_header("Network Coverage", "Inspect and compare medicine availability across the network.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if data:
    coords = [(p.get("latitude"), p.get("longitude")) for p in data if p.get("latitude") and p.get("longitude")]
    center = [34.8303, 0.1517]
    if coords:
        center = [sum(c[0] for c in coords) / len(coords), sum(c[1] for c in coords) / len(coords)]

    m = folium.Map(location=center, zoom_start=13, tiles="CartoDB positron")
    cluster = MarkerCluster().add_to(m)

    for p in data:
        if p.get("latitude") and p.get("longitude"):
            in_stock = p.get("quantity", 0) > 0
            popup_text = f"""
            <div style='min-width:220px;'>
                <b>{p.get('pharmacy_name', 'Unknown')}</b><br>
                <span style='color:#475569;'>{p.get('medicine', 'Unknown medicine')}</span><br>
                <span style='color:{'#16A34A' if in_stock else '#DC2626'}; font-weight:700;'>
                    {'Available' if in_stock else 'Not Available'}
                </span>
            </div>
            """
            folium.Marker(
                location=[p["latitude"], p["longitude"]],
                popup=popup_text,
                tooltip=p.get("pharmacy_name", "Pharmacy"),
                icon=folium.Icon(color="green" if in_stock else "red", icon="plus-sign"),
            ).add_to(cluster)

    st_folium(m, width=None, height=620, use_container_width=True)
else:
    empty_state("No pharmacy data available", "The map will appear once the API returns geolocated pharmacy data.")
st.markdown("</div>", unsafe_allow_html=True)

render_section_header("Availability List", "Use the table for quick operational lookup.")
st.markdown("<div class='ui-panel'>", unsafe_allow_html=True)
if data:
    df = pd.DataFrame(data)
    # Remove quantity and coordinates from display - show only pharmacy and medicine names
    display_cols = [c for c in ["pharmacy_name", "medicine"] if c in df.columns]
    if display_cols:
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
else:
    empty_state("Nothing to list", "No rows were returned by the map endpoint.")
st.markdown("</div>", unsafe_allow_html=True)