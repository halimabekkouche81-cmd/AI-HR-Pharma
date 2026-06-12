import requests

API = "http://127.0.0.1:8000"

movements = [
    # Ajouter un inventaire
    (6, 1, 50), (7, 2, 40), (8, 3, 30),
    (9, 1, 25), (10, 4, 35), (11, 2, 20),
    (12, 3, 45), (13, 1, 60), (14, 4, 15),
    # ventes
    (6, 1, -10), (7, 2, -8), (8, 3, -5),
    (9, 1, -7), (10, 4, -6), (11, 2, -4),
    (12, 3, -9), (13, 1, -12), (14, 4, -3),
]

for pharmacy_id, medicine_id, quantity in movements:
    r = requests.post(
        f"{API}/stock-movement/",
        params={
            "pharmacy_id": pharmacy_id,
            "medicine_id": medicine_id,
            "quantity": quantity
        }
    )
    print(f"{'✅' if r.status_code == 200 else '❌'} pharmacy={pharmacy_id} medicine={medicine_id} qty={quantity} → {r.json()}")