import requests
import random
from datetime import datetime, timedelta
import time

API = "http://127.0.0.1:8000"

# ===============================
# إعدادات البيانات
# ===============================
pharmacies = [6, 7, 8, 9, 10, 11, 12, 13, 14]
medicines = [1, 2, 3, 4, 5, 6, 7]
DAYS = 90
ENABLE_INVENTORY = True # شغّليه True مرة واحدة فقط

print(" Starting data generation with realistic Trend + Seasonality + Noise...")

# ===============================
# 1️⃣ إضافة مخزون (مرة واحدة فقط)
# ===============================
if ENABLE_INVENTORY:
    print("\n📦 Adding inventory...")
    for pharmacy_id in pharmacies:
        for medicine_id in medicines:
            quantity = random.randint(500, 800)
            r = requests.post(
                f"{API}/stock-movement/",
                params={
                    "pharmacy_id": pharmacy_id,
                    "medicine_id": medicine_id,
                    "quantity": quantity
                }
            )
            if r.status_code == 200:
                print(f"✅ Pharmacy {pharmacy_id} | Medicine {medicine_id} | +{quantity}")
            time.sleep(0.02)
else:
    print("\n⚠️ Inventory skipped (already initialized)")

# ===============================
# 2️⃣ محاكاة مبيعات واقعية
# ===============================
print(f"\n Simulating {DAYS} days of sales (Trend + Seasonality + Noise)...")

start_date = datetime.utcnow() - timedelta(days=DAYS)

for day in range(DAYS):
    current_date = start_date + timedelta(days=day)

    #  Trend (تصاعدي تدريجي)
    trend_boost = day * 0.1

    for pharmacy_id in pharmacies:
        for medicine_id in medicines:

            #  Base demand
            base = random.randint(3, 8)

            #  Seasonality (نهاية الأسبوع)
            weekday = current_date.weekday()  # 0=Monday, 6=Sunday
            if weekday in [4, 5]:  # الجمعة والسبت
                seasonal_boost = random.randint(3, 6)
            else:
                seasonal_boost = 0

            #  Noise (واقعية)
            noise = random.randint(-2, 2)

            # ⚡ Spike (حدث نادر)
            spike = random.randint(5, 10) if random.random() < 0.05 else 0

            # 📦 Final sale
            sale = base + trend_boost + seasonal_boost + spike + noise
            sale = max(1, int(sale))  # ضمان عدم وجود قيم سالبة

            # إرسال الطلب
            r = requests.post(
                f"{API}/stock-movement/",
                params={
                    "pharmacy_id": pharmacy_id,
                    "medicine_id": medicine_id,
                    "quantity": -sale,
                    "created_at": current_date.isoformat()  # ⚠️ تأكدي أن API يدعمها
                }
            )

            if r.status_code == 200:
                print(f"✅ {current_date.date()} | Pharm {pharmacy_id} | Med {medicine_id} | -{sale}")
            else:
                try:
                    print(f"⚠️ Error: {r.json()}")
                except:
                    print(f"⚠️ Error: {r.status_code}")

            time.sleep(0.005)

# ===============================
# 3️⃣ محاكاة Feedback ذكي
# ===============================
print("\n🧠 Simulating intelligent feedback...")

for i in range(40):
    pharmacy_id = random.choice(pharmacies)
    medicine_id = random.choice(medicines)
    recommended = random.choice(pharmacies)

    # ❗ نفس الصيدلية = رفض غالبًا
    if recommended == pharmacy_id:
        accepted = 0
    else:
        accepted = random.choice([1, 1, 1, 0])  # 75% قبول

    r = requests.post(
        f"{API}/feedback/",
        params={
            "pharmacy_id": pharmacy_id,
            "medicine_id": medicine_id,
            "recommended_pharmacy_id": recommended,
            "accepted": accepted
        }
    )

    if r.status_code == 200:
        status = "✅ Accepted" if accepted == 1 else "❌ Rejected"
        print(f"{status} | Pharm {pharmacy_id} | Med {medicine_id}")
    else:
        print("⚠️ Feedback error")

    time.sleep(0.01)

# ===============================
# النهاية
# ===============================
print("\n Data generation complete!")
print(" Now test:")
print(" /ai/evaluate/")
print(" AI Monitoring Dashboard")
print(" Smart Recommendation")
print(" Auto-Retraining System")