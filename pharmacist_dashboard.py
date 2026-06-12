import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI-HR Pharma", layout="wide")

st.title("💊 AI-HR Pharma Dashboard")

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Search Medicine",
        "Network Search",
        "Alternative Medicines",
        "Stock Alerts",
        "Restock Recommendation"
    ]
)

# -----------------------------
# Search Medicine
# -----------------------------

if menu == "Search Medicine":

    st.header("🔎 Search Medicine")

    name = st.text_input("Medicine Name")

    if st.button("Search"):

        r = requests.get(f"{API}/search/?name={name}")

        if r.status_code == 200:
            data = r.json()
            st.table(data)


# -----------------------------
# Network Search
# -----------------------------

if menu == "Network Search":

    st.header("🌍 Search Medicine in Pharmacy Network")

    name = st.text_input("Medicine Name")

    if st.button("Find in Network"):

        r = requests.get(
            f"{API}/search-medicine-network",
            params={"medicine_name": name, "requesting_pharmacy_id": 1}
        )

        if r.status_code == 200:
            st.table(r.json())


# -----------------------------
# Alternative Medicines
# -----------------------------

if menu == "Alternative Medicines":

    st.header("🧠 Alternative Medicines")

    name = st.text_input("Medicine")

    if st.button("Find Alternatives"):

        r = requests.get(
            f"{API}/alternative-medicines",
            params={"medicine_name": name}
        )

        if r.status_code == 200:
            st.table(r.json())


# -----------------------------
# Stock Alerts
# -----------------------------

if menu == "Stock Alerts":

    st.header("⚠️ Low Stock Alerts")

    r = requests.get(f"{API}/low-stock-alerts")

    if r.status_code == 200:
        st.table(r.json())


# -----------------------------
# Restock Recommendation
# -----------------------------

if menu == "Restock Recommendation":

    st.header("📦 Restock Recommendation")

    r = requests.get(f"{API}/recommend-restock")

    if r.status_code == 200:
        st.table(r.json())