# -*- coding: utf-8 -*-
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from . import models, schemas, crud
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/pharmacies/")
def add_pharmacy(pharmacy: schemas.PharmacyCreate, db: Session = Depends(get_db)):
    return crud.create_pharmacy(db, pharmacy)

@app.post("/medicines/")
def add_medicine(medicine: schemas.MedicineCreate, db: Session = Depends(get_db)):
    return crud.create_medicine(db, medicine)

@app.post("/inventory/")
def add_inventory(inventory: schemas.InventoryCreate, db: Session = Depends(get_db)):
    return crud.create_inventory(db, inventory)

@app.get("/medicines/")
def list_medicines(db: Session = Depends(get_db)):
    return crud.get_medicines(db)

@app.get("/search/")
def search(name: str, db: Session = Depends(get_db)):
    return crud.search_medicine(db, name)

@app.get("/network-search/")
def network_search(name: str, pharmacy_id: int = None, db: Session = Depends(get_db)):
    return crud.network_search(db, name, pharmacy_id)

@app.post("/stock-movement/")
def stock_movement(
    pharmacy_id: int,
    medicine_id: int,
    quantity: int,
    created_at:   str = None,
    db: Session = Depends(get_db)
):
    return crud.create_stock_movement(db, pharmacy_id, medicine_id, quantity, created_at)

@app.get("/predict-stock/")
def predict_stock(pharmacy_id: int, medicine_id: int, db: Session = Depends(get_db)):
    return crud.predict_stock_out(db, pharmacy_id, medicine_id)

@app.get("/low-stock-alerts/")
def low_stock_alerts(days_threshold: int = 7, db: Session = Depends(get_db)):
    return crud.get_low_stock_alerts(db, days_threshold)

@app.get("/analytics/top-selling/")
def top_selling(db: Session = Depends(get_db)):
    return crud.top_selling_medicines(db)

@app.get("/alerts/")
def get_alerts(db: Session = Depends(get_db)):
    predictions = crud.get_low_stock_alerts(db)
    alerts = []
    for item in predictions:
        if item["days_remaining"] <= 5:
            alerts.append({
                "pharmacy_id": item["pharmacy_id"],
                "medicine_id": item["medicine_id"],
                "current_stock": item["current_stock"],
                "days_remaining": item["days_remaining"],
                "predicted_stock_out_date": item["predicted_stock_out_date"],
                "alert": "⚠️ Stock Running Low"
            })
    return alerts

@app.get("/recommend-reorder/")
def recommend_reorder(
    pharmacy_id: int,
    medicine_id: int,
    days_cover: int = 30,
    db: Session = Depends(get_db)
):
    return crud.recommend_reorder(db, pharmacy_id, medicine_id, days_cover)

@app.get("/recommend-restock")
def recommend_restock(db: Session = Depends(get_db)):
    inventories = db.query(models.Inventory).all()
    recommendations = []
    LEAD_TIME = 5
    SAFETY_BUFFER = 3
    for inv in inventories:
        prediction = crud.predict_stock_out(db, inv.pharmacy_id, inv.medicine_id)
        if "daily_average_sales" not in prediction:
            continue
        daily_avg = prediction["daily_average_sales"]
        current_stock = prediction["current_stock"]
        days_remaining = prediction["estimated_days_remaining"]
        ideal_stock = daily_avg * (LEAD_TIME + SAFETY_BUFFER)
        recommended_qty = max(0, round(ideal_stock - current_stock))
        if recommended_qty > 0:
            if days_remaining <= 5:
                priority = "HIGH"
            elif days_remaining <= 10:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            medicine = db.query(models.Medicine).get(inv.medicine_id)
            recommendations.append({
                "medicine_name": medicine.trade_name,
                "current_stock": current_stock,
                "daily_average_sales": daily_avg,
                "days_remaining": days_remaining,
                "recommended_order_quantity": recommended_qty,
                "priority": priority
            })
    return recommendations

@app.get("/search-medicine-network")
def search_medicine_network(
    medicine_name: str,
    requesting_pharmacy_id: int,
    db: Session = Depends(get_db)
):
    medicine = db.query(models.Medicine).filter(
        models.Medicine.trade_name == medicine_name
    ).first()

    if not medicine:
        return {"message": "Medicine not found"}

    results = []

    pharmacies = db.query(models.Pharmacy).filter(
        models.Pharmacy.id != requesting_pharmacy_id
    ).all()

    for pharmacy in pharmacies:
        inventory = db.query(models.Inventory).filter(
            models.Inventory.medicine_id == medicine.id,
            models.Inventory.pharmacy_id == pharmacy.id
        ).first()

        if inventory and inventory.quantity > 0:
            results.append({
                "pharmacy_id": pharmacy.id,
                "pharmacy_name": pharmacy.name,
                "available_stock": inventory.quantity
            })

    results.sort(key=lambda x: x["available_stock"], reverse=True)

    return results

@app.get("/search-medicine-network-smart")
def search_medicine_network_smart(
    medicine_name: str,
    requesting_pharmacy_id: int,
    db: Session = Depends(get_db)
):
    SAFE_THRESHOLD = 10

    # ✅ trade_name بدل name
    medicine = db.query(models.Medicine).filter(
        models.Medicine.trade_name == medicine_name
    ).first()

    if not medicine:
        return {"message": "Medicine not found"}

    results = []

    pharmacies = db.query(models.Pharmacy).filter(
        models.Pharmacy.id != requesting_pharmacy_id
    ).all()

    for pharmacy in pharmacies:

        movements = db.query(models.StockMovement).filter(
            models.StockMovement.medicine_id == medicine.id,
            models.StockMovement.pharmacy_id == pharmacy.id
        ).all()

        if not movements:
            continue

        current_stock = sum(m.quantity for m in movements)

        if current_stock <= 0:
            continue

        total_sold = abs(sum(m.quantity for m in movements if m.quantity < 0))
        first_movement_date = min(m.created_at for m in movements)
        days_passed = (datetime.utcnow() - first_movement_date).days or 1

        daily_average = total_sold / days_passed if days_passed > 0 else 0

        if daily_average == 0:
            continue

        days_remaining = current_stock / daily_average

        if days_remaining > SAFE_THRESHOLD:
            results.append({
                "pharmacy_id": pharmacy.id,
                "pharmacy_name": pharmacy.name,
                "available_stock": current_stock,
                "daily_average_sales": round(daily_average, 2),
                "days_remaining": round(days_remaining, 1)
            })

    results.sort(key=lambda x: x["days_remaining"], reverse=True)

    return results
@app.get("/alternative-medicines/")
def alternative_medicines(medicine_name: str, db: Session = Depends(get_db)):
    return crud.find_alternative_medicines(db, medicine_name)
@app.get("/pharmacy-map")
def pharmacy_map(db: Session = Depends(get_db)):
    return crud.get_pharmacies_with_stock(db)
@app.post("/request-medicine/")
def request_medicine(pharmacy_id: int, medicine_name: str, db: Session = Depends(get_db)):
    return crud.create_request(db, pharmacy_id, medicine_name)
@app.get("/notifications/")
def get_notifications(db: Session = Depends(get_db)):
    notifications = db.query(models.MedicineRequest).filter(
        models.MedicineRequest.fulfilled == 1
    ).all()
    return [
        {
            "pharmacy_id": n.pharmacy_id,
            "medicine_name": n.medicine_name,
            "message": f"✅ {n.medicine_name} is now available!",
            "created_at": n.created_at
        }
        for n in notifications
    ]

@app.get("/pending-requests/")
def get_pending_requests(db: Session = Depends(get_db)):
    pending = db.query(models.MedicineRequest).filter(
        models.MedicineRequest.fulfilled == 0
    ).all()
    return [
        {
            "pharmacy_id": p.pharmacy_id,
            "medicine_name": p.medicine_name,
            "created_at": p.created_at
        }
        for p in pending
    ]
@app.get("/predict-demand/")
def predict_demand(medicine_id: int, db: Session = Depends(get_db)):

    data = crud.get_sales_data(db, medicine_id)

    if not data or len(data) < 2:
        return {"message": "Not enough data for prediction"}

    from app.ai_model import train_model, predict_future, get_trend

    model, df = train_model(data)
    predictions = predict_future(model, df)
    trend = get_trend(model)

    return {
        "medicine_id": medicine_id,
        "trend": trend,
        "forecast_next_7_days": predictions,
        "total_predicted_demand": round(sum(predictions), 2),
        "average_daily_demand": round(sum(predictions) / 7, 2)
    }
@app.get("/smart-recommendation/")
def get_smart_recommendation(
    pharmacy_id: int,
    medicine_id: int,
    db: Session = Depends(get_db)
):
    return crud.smart_recommendation(db, pharmacy_id, medicine_id)
@app.post("/feedback/")
def feedback(
    pharmacy_id: int,
    medicine_id: int,
    recommended_pharmacy_id: int,
    accepted: int,
    db: Session = Depends(get_db)
):
    return crud.save_feedback(
        db, pharmacy_id, medicine_id,
        recommended_pharmacy_id, accepted
    )
@app.get("/ai-metrics/")
def get_ai_metrics(db: Session = Depends(get_db)):
    return crud.ai_metrics(db)

@app.get("/ai-metrics-over-time/")
def get_ai_metrics_over_time(db: Session = Depends(get_db)):
    return crud.ai_metrics_over_time(db)

@app.get("/top-medicines-demand/")
def get_top_medicines_demand(db: Session = Depends(get_db)):
    return crud.top_medicines_demand(db)
@app.get("/ai/retrain/check")
def check_retrain(db: Session = Depends(get_db)):
    return crud.should_retrain(db)

@app.post("/ai/retrain")
def retrain(medicine_id: int, db: Session = Depends(get_db)):
    return crud.retrain_model(db, medicine_id)

@app.get("/ai/training-logs")
def get_training_logs(db: Session = Depends(get_db)):
    return crud.get_training_logs(db)
@app.get("/ai/evaluate/")
def evaluate_models(medicine_id: int, pharmacy_id: int = None, db: Session = Depends(get_db)):

    data = crud.get_sales_data(db, medicine_id, pharmacy_id)

    if not data or len(data) < 10:
        return {
            "error": "Not enough data",
            "data_points": len(data) if data else 0,
            "required": 10
        }

    from app.evaluation import prepare_data, compare_models

    df = prepare_data(data)

    if len(df) < 5:
        return {
            "error": "Not enough daily data points",
            "daily_points": len(df),
            "required": 5
        }

    results = compare_models(df)
    return results
# ===============================
# Authentication Endpoints
# ===============================

@app.post("/register/")
def register(
    email: str,
    password: str,
    pharmacy_id: int = None,  # 👈 اختياري
    db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if pharmacy_id:
        pharmacy = db.query(models.Pharmacy).filter(
            models.Pharmacy.id == pharmacy_id
        ).first()
        if not pharmacy:
            raise HTTPException(status_code=404, detail="Pharmacy not found")

    hashed = get_password_hash(password)
    user = models.User(
        email=email,
        hashed_password=hashed,
        pharmacy_id=pharmacy_id  # None للـ admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "email": user.email,
        "pharmacy_id": user.pharmacy_id
    }

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "pharmacy_id": user.pharmacy_id,
        "email": user.email,
        "is_admin": user.is_admin  # 👈 جديد
    }

@app.get("/me/")
def get_me(current_user: models.User = Depends(get_current_active_user)):
    return {
        "email": current_user.email,
        "pharmacy_id": current_user.pharmacy_id,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin  # 👈 جديد
    }
# ===============================
# Multi-Tenant Endpoints
# ===============================

@app.get("/my/inventory/")
def my_inventory(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    inventories = db.query(models.Inventory).filter(
        models.Inventory.pharmacy_id == current_user.pharmacy_id
    ).all()
    return inventories

@app.get("/my/predict-stock/")
def my_predict_stock(
    medicine_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.predict_stock_out(db, current_user.pharmacy_id, medicine_id)

@app.get("/my/alerts/")
def my_alerts(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    all_alerts = crud.get_low_stock_alerts(db)
    return [a for a in all_alerts if a["pharmacy_id"] == current_user.pharmacy_id]

@app.get("/my/recommendation/")
def my_recommendation(
    medicine_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.smart_recommendation(db, current_user.pharmacy_id, medicine_id)
# ===============================
# Notification Endpoints
# ===============================

@app.get("/my/notifications/")
def my_notifications(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    notifications = crud.get_notifications_for_pharmacy(db, current_user.pharmacy_id)
    return [
        {
            "id": n.id,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at
        }
        for n in notifications
    ]

@app.post("/my/notifications/read/{notification_id}")
def mark_read(
    notification_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.mark_notification_read(db, notification_id)

@app.get("/my/notifications/unread-count/")
def unread_count(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    count = crud.get_unread_count(db, current_user.pharmacy_id)
    return {"unread": count}
@app.get("/market-scarcity/")
def market_scarcity(limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_market_scarcity(db, limit)
@app.post("/log-search/")
def log_search(
    medicine_name: str,
    pharmacy_id: int,
    found: int,
    db: Session = Depends(get_db)
):
    return crud.log_search(db, medicine_name, pharmacy_id, bool(found))
@app.get("/my/recommend-restock")
def my_recommend_restock(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    inventories = db.query(models.Inventory).filter(
        models.Inventory.pharmacy_id == current_user.pharmacy_id
    ).all()

    recommendations = []
    LEAD_TIME = 5
    SAFETY_BUFFER = 3

    for inv in inventories:
        prediction = crud.predict_stock_out(
            db, inv.pharmacy_id, inv.medicine_id
        )
        if "daily_average_sales" not in prediction:
            continue

        daily_avg    = prediction["daily_average_sales"]
        current_stock = prediction["current_stock"]
        days_remaining = prediction["estimated_days_remaining"]
        ideal_stock  = daily_avg * (LEAD_TIME + SAFETY_BUFFER)
        recommended  = max(0, round(ideal_stock - current_stock))

        if recommended > 0:
            priority = "HIGH" if days_remaining <= 5 else "MEDIUM" if days_remaining <= 10 else "LOW"
            medicine = db.query(models.Medicine).get(inv.medicine_id)
            recommendations.append({
                "medicine_name": medicine.trade_name if medicine else f"Medicine {inv.medicine_id}",
                "current_stock": current_stock,
                "daily_average_sales": daily_avg,
                "days_remaining": days_remaining,
                "recommended_order_quantity": recommended,
                "priority": priority
            })

    return recommendations