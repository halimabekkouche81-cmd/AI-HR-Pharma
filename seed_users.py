import requests

API = "http://127.0.0.1:8000"

users = [
    {"email": "benali@pharma-saida.dz",      "password": "pass123", "pharmacy_id": 6},
    {"email": "khaled@pharma-saida.dz",       "password": "pass123", "pharmacy_id": 7},
    {"email": "benzerga@pharma-saida.dz",     "password": "pass123", "pharmacy_id": 8},
    {"email": "zitouni@pharma-saida.dz",      "password": "pass123", "pharmacy_id": 9},
    {"email": "boukouria@pharma-saida.dz",    "password": "pass123", "pharmacy_id": 10},
    {"email": "bettahar@pharma-saida.dz",     "password": "pass123", "pharmacy_id": 11},
    {"email": "amrani@pharma-saida.dz",       "password": "pass123", "pharmacy_id": 12},
    {"email": "daoudi@pharma-saida.dz",       "password": "pass123", "pharmacy_id": 13},
    {"email": "elnour@pharma-saida.dz",       "password": "pass123", "pharmacy_id": 14},
]

for u in users:
    r = requests.post(f"{API}/register/", params=u)
    if r.status_code == 200:
        print(f"✅ {u['email']} → Pharmacy {u['pharmacy_id']}")
    else:
        print(f"❌ {u['email']} → {r.json()}")

print("\n🎉 All users registered!")