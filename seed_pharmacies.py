import requests

API = "http://127.0.0.1:8000"

pharmacies = [
    {
        "name": "Pharmacie Driss Khodja Bouziane",
        "location": "Cité Refafa Miloud Saida",
        "latitude": 34.8335,
        "longitude": 0.1512
    },
    {
        "name": "Pharmacie Khaled Assia",
        "location": "Ilot K N03 Saida",
        "latitude": 34.8351,
        "longitude": 0.1498
    },
    {
        "name": "Pharmacie Benzerga",
        "location": "Cité Bourdj 2 Saida",
        "latitude": 34.8289,
        "longitude": 0.1553
    },
    {
        "name": "Pharmacie Zitouni",
        "location": "Cité SALM 2 Saida",
        "latitude": 34.8317,
        "longitude": 0.1475
    },
    {
        "name": "Pharmacie Boukouria Mustapha",
        "location": "Proche centre ville Saida",
        "latitude": 34.8402,
        "longitude": 0.1459
    },
    {
        "name": "Pharmacie Bettahar Khaled",
        "location": "Avenue de l'Independance Saida",
        "latitude": 34.8415,
        "longitude": 0.1438
    },
    {
        "name": "Pharmacie Amrani Ali",
        "location": "Rue Base Saida",
        "latitude": 34.8368,
        "longitude": 0.1467
    },
    {
        "name": "Pharmacie Daoudi Abdelaziz",
        "location": "Centre ville Saida",
        "latitude": 34.8409,
        "longitude": 0.1446
    },
    {
        "name": "Pharmacie El Nour",
        "location": "Cité Khater Abdelkader Saida",
        "latitude": 34.8297,
        "longitude": 0.1504
    },
]

for p in pharmacies:
    r = requests.post(f"{API}/pharmacies/", json=p)
    if r.status_code == 200:
        print(f"✅ Added: {p['name']}")
    else:
        print(f"❌ Failed: {p['name']} → {r.text}")