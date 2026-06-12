import requests

API = "http://127.0.0.1:8000"

medicines = [
    # Paracetamol group
    {"trade_name": "Doliprane",       "active_ingredient": "Paracetamol",    "dosage": "500mg", "form": "Tablet"},
    {"trade_name": "Efferalgan",      "active_ingredient": "Paracetamol",    "dosage": "500mg", "form": "Tablet"},
    {"trade_name": "Dafalgan",        "active_ingredient": "Paracetamol",    "dosage": "500mg", "form": "Tablet"},
    # Amoxicillin group
    {"trade_name": "Amoxicilline",    "active_ingredient": "Amoxicillin",    "dosage": "500mg", "form": "Capsule"},
    {"trade_name": "Augmentin",       "active_ingredient": "Amoxicillin",    "dosage": "500mg", "form": "Tablet"},
    # Azithromycin group
    {"trade_name": "Zithromax",       "active_ingredient": "Azithromycin",   "dosage": "500mg", "form": "Tablet"},
    # Clarithromycin group
    {"trade_name": "Clarithromycine", "active_ingredient": "Clarithromycin", "dosage": "500mg", "form": "Tablet"},
]

print("💊 Adding medicines...")

for m in medicines:
    r = requests.post(f"{API}/medicines/", json=m)
    if r.status_code == 200:
        data = r.json()
        print(f"✅ Added: {m['trade_name']} (ID: {data.get('id', '?')})")
    else:
        print(f"⚠️  {m['trade_name']} → {r.json()}")

print("\n🎉 Done!")