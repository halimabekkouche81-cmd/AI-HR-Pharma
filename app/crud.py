# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from . import models, schemas
from .models import StockMovement, Inventory
from datetime import datetime, timedelta
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

def create_pharmacy(db: Session, pharmacy: schemas.PharmacyCreate):
    db_pharmacy = models.Pharmacy(**pharmacy.dict())
    db.add(db_pharmacy)
    db.commit()
    db.refresh(db_pharmacy)
    return db_pharmacy

def create_medicine(db: Session, medicine: schemas.MedicineCreate):
    db_medicine = models.Medicine(**medicine.dict())
    db.add(db_medicine)
    db.commit()
    db.refresh(db_medicine)
    return db_medicine

def create_inventory(db: Session, inventory: schemas.InventoryCreate):
    existing = db.query(models.Inventory).filter_by(
        pharmacy_id=inventory.pharmacy_id,
        medicine_id=inventory.medicine_id
    ).first()

    if existing:
        existing.quantity += inventory.quantity
        db.commit()
        db.refresh(existing)
    else:
        existing = models.Inventory(**inventory.dict())
        db.add(existing)
        db.commit()
        db.refresh(existing)

    medicine = db.query(models.Medicine).filter(
        models.Medicine.id == inventory.medicine_id
    ).first()

    if medicine:

        pending = db.query(models.MedicineRequest).filter(
            models.MedicineRequest.fulfilled == 0
        ).all()

        notifications = []
        notified = set()

        for r in pending:

            req_name = r.medicine_name.strip().lower()
            med_name = medicine.trade_name.strip().lower()
            active_ing = (medicine.active_ingredient or "").strip().lower()

            # مقارنة مرنة بالاسم التجاري أو المادة الفعالة
            if (
                req_name in med_name
                or med_name in req_name
                or req_name in active_ing
                or active_ing in req_name
            ):

                notifications.append({
                    "pharmacy_id": r.pharmacy_id,
                    "message": f"✅ {medicine.trade_name} is now available in pharmacy {inventory.pharmacy_id}"
                })

                r.fulfilled = 1

                # إشعار واحد فقط لكل صيدلية
                if r.pharmacy_id not in notified:

                    existing = db.query(models.Notification).filter(
                        models.Notification.pharmacy_id == r.pharmacy_id,
                        models.Notification.type == "medicine_available",
                        models.Notification.message.contains(medicine.trade_name)
                    ).first()

                    if not existing:
                        create_notification(
                            db,
                            pharmacy_id=r.pharmacy_id,
                            message=f"✅ {medicine.trade_name} is now available in the network",
                            type="medicine_available"
                        )

                        notified.add(r.pharmacy_id)

        db.commit()

        return {
            "inventory": {
                "id": existing.id,
                "pharmacy_id": existing.pharmacy_id,
                "medicine_id": existing.medicine_id,
                "quantity": existing.quantity
            },
            "notifications": notifications
        }

    return existing

def get_medicines(db: Session):
    return db.query(models.Medicine).all()

def search_medicine(db: Session, name: str):
    return db.query(models.Medicine).filter(
        models.Medicine.trade_name.ilike(f"%{name}%")
    ).all()

def network_search(db: Session, name: str, pharmacy_id: int = None):
    results = db.query(
        models.Medicine.trade_name,
        models.Medicine.active_ingredient,
        models.Pharmacy.id.label("pharmacy_id"),
        models.Pharmacy.name.label("pharmacy_name"),
        models.Pharmacy.location,
        models.Pharmacy.latitude,
        models.Pharmacy.longitude,
        models.Inventory.quantity
    ).join(
        models.Inventory, models.Medicine.id == models.Inventory.medicine_id
    ).join(
        models.Pharmacy, models.Pharmacy.id == models.Inventory.pharmacy_id
    ).filter(
        or_(
            models.Medicine.trade_name.ilike(f"%{name}%"),
            models.Medicine.active_ingredient.ilike(f"%{name}%")
        ),
        models.Inventory.quantity > 0
    ).all()

    requesting_pharmacy = None
    if pharmacy_id:
        requesting_pharmacy = db.query(models.Pharmacy).filter(
            models.Pharmacy.id == pharmacy_id
        ).first()

    response = []
    for r in results:
        item = {
            "trade_name": r.trade_name,
            "active_ingredient": r.active_ingredient,
            "pharmacy_id": r.pharmacy_id,
            "pharmacy_name": r.pharmacy_name,
            "location": r.location,
            "quantity": r.quantity,
            "distance_km": None
        }

        if requesting_pharmacy and r.latitude and r.longitude:
            if requesting_pharmacy.latitude and requesting_pharmacy.longitude:
                item["distance_km"] = calculate_distance(
                    requesting_pharmacy.latitude,
                    requesting_pharmacy.longitude,
                    r.latitude,
                    r.longitude
                )

        response.append(item)

    response.sort(key=lambda x: x["distance_km"] or 999)
    return response

def get_current_stock(db: Session, pharmacy_id: int, medicine_id: int):
    movements = db.query(StockMovement).filter(
        StockMovement.pharmacy_id == pharmacy_id,
        StockMovement.medicine_id == medicine_id
    ).all()
    total = sum(m.quantity for m in movements)
    return total

def create_stock_movement(db: Session, pharmacy_id: int, medicine_id: int, quantity: int, created_at: str = None):
    
    current_stock = get_current_stock(db, pharmacy_id, medicine_id)

    if current_stock + quantity < 0:
        return {"error": "Not enough stock"}

    if created_at:
        try:
            movement_date = datetime.fromisoformat(created_at)
        except:
            movement_date = datetime.utcnow()
    else:
        movement_date = datetime.utcnow()

    # ✅ 1: تسجيل الحركة في stock_movements
    movement = StockMovement(
        pharmacy_id=pharmacy_id,
        medicine_id=medicine_id,
        quantity=quantity,
        created_at=movement_date
    )
    db.add(movement)

    # ✅ 2: تحديث inventory مباشرة
    inv = db.query(Inventory).filter(
        Inventory.pharmacy_id == pharmacy_id,
        Inventory.medicine_id == medicine_id
    ).first()

    if inv:
        inv.quantity += quantity
    else:
        inv = Inventory(
            pharmacy_id=pharmacy_id,
            medicine_id=medicine_id,
            quantity=max(0, current_stock + quantity)
        )
        db.add(inv)

    # ✅ تحقق من طلبات الدواء عند إضافة مخزون فقط
    if quantity > 0:
        medicine = db.query(models.Medicine).filter(
            models.Medicine.id == medicine_id
        ).first()

        if medicine:

            pending = db.query(models.MedicineRequest).filter(
                models.MedicineRequest.fulfilled == 0
            ).all()

            notified = set()

            for req in pending:

                req_name = req.medicine_name.strip().lower()
                med_name = medicine.trade_name.strip().lower()
                active_ing = (medicine.active_ingredient or "").strip().lower()

                # مقارنة مرنة بالاسم التجاري أو المادة الفعالة
                if (
                    req_name in med_name
                    or med_name in req_name
                    or req_name in active_ing
                    or active_ing in req_name
                ):

                    # إرسال إشعار واحد فقط لكل صيدلية
                    if req.pharmacy_id not in notified:

                        existing = db.query(models.Notification).filter(
                            models.Notification.pharmacy_id == req.pharmacy_id,
                            models.Notification.type == "medicine_available",
                            models.Notification.message.contains(medicine.trade_name)
                        ).first()

                        if not existing:
                            notif = models.Notification(
                                pharmacy_id=req.pharmacy_id,
                                message=f"✅ {medicine.trade_name} is now available in the network — Pharmacy {pharmacy_id}",
                                type="medicine_available"
                            )

                            db.add(notif)
                            notified.add(req.pharmacy_id)

                    req.fulfilled = 1

    db.commit()
    db.refresh(movement)
    return movement

def predict_stock_out(db, pharmacy_id: int, medicine_id: int):
    inventory = db.query(Inventory).filter_by(
        pharmacy_id=pharmacy_id,
        medicine_id=medicine_id
    ).first()

    if not inventory:
        return {"error": "Inventory not found"}

    current_stock = inventory.quantity

    sales = db.query(func.sum(StockMovement.quantity)).filter(
        StockMovement.pharmacy_id == pharmacy_id,
        StockMovement.medicine_id == medicine_id,
        StockMovement.quantity < 0
    ).scalar()

    if not sales:
        return {"message": "Not enough sales data for prediction"}

    total_sold = abs(sales)

    first_movement = db.query(StockMovement).filter_by(
        pharmacy_id=pharmacy_id,
        medicine_id=medicine_id
    ).order_by(StockMovement.created_at.asc()).first()

    days_passed = (datetime.utcnow() - first_movement.created_at).days

    if days_passed == 0:
        return {"message": "Not enough time data"}

    daily_average = total_sold / days_passed

    if daily_average == 0:
        return {"message": "No sales detected"}

    days_remaining = current_stock / daily_average
    predicted_date = datetime.utcnow() + timedelta(days=days_remaining)

    return {
        "current_stock": current_stock,
        "daily_average_sales": round(daily_average, 2),
        "daily_sales": round(daily_average, 2),
        "estimated_days_remaining": round(days_remaining, 1),
        "predicted_stock_out_date": predicted_date
    }

def get_low_stock_alerts(db, days_threshold: int = 7):
    alerts = []
    inventories = db.query(Inventory).all()

    for inv in inventories:
        prediction = predict_stock_out(
            db,
            pharmacy_id=inv.pharmacy_id,
            medicine_id=inv.medicine_id
        )

        if "estimated_days_remaining" in prediction:
            if prediction["estimated_days_remaining"] <= days_threshold:
                alerts.append({
                    "pharmacy_id": inv.pharmacy_id,
                    "medicine_id": inv.medicine_id,
                    "current_stock": prediction["current_stock"],
                    "days_remaining": prediction["estimated_days_remaining"],
                    "predicted_stock_out_date": prediction["predicted_stock_out_date"]
                })

                # ✅ إنشاء إشعار تلقائي
                medicine = db.query(models.Medicine).get(inv.medicine_id)
                med_name = medicine.trade_name if medicine else f"Medicine {inv.medicine_id}"

                existing = db.query(models.Notification).filter(
                    models.Notification.pharmacy_id == inv.pharmacy_id,
                    models.Notification.type == "low_stock",
                    models.Notification.message.contains(med_name)
                ).first()

                if not existing:
                    create_notification(
                        db,
                        pharmacy_id=inv.pharmacy_id,
                        message=f"⚠️ {med_name} stock is low — only {prediction['estimated_days_remaining']} days remaining",
                        type="low_stock"
                    )

    return alerts

def top_selling_medicines(db):
    results = db.query(
        StockMovement.medicine_id,
        func.sum(StockMovement.quantity).label("total_sold")
    ).filter(
        StockMovement.quantity < 0
    ).group_by(
        StockMovement.medicine_id
    ).order_by(
        func.sum(StockMovement.quantity)
    ).all()

    response = []
    for r in results:
        medicine = db.query(models.Medicine).get(r.medicine_id)
        response.append({
            "medicine_name": medicine.trade_name,
            "total_sold": abs(r.total_sold)
        })

    return response

def recommend_reorder(db: Session, pharmacy_id: int, medicine_id: int, days_cover: int):
    prediction = predict_stock_out(db, pharmacy_id, medicine_id)

    if "error" in prediction or "message" in prediction:
        return prediction

    daily_sales = prediction["daily_sales"]
    current_stock = prediction["current_stock"]

    needed_stock = daily_sales * days_cover
    reorder_quantity = max(0, int(needed_stock - current_stock))

    return {
        "pharmacy_id": pharmacy_id,
        "medicine_id": medicine_id,
        "daily_sales": daily_sales,
        "current_stock": current_stock,
        "days_cover_target": days_cover,
        "recommended_order": reorder_quantity
    }

def find_alternative_medicines(db: Session, medicine_name: str):
    medicine = db.query(models.Medicine).filter(
        models.Medicine.trade_name.ilike(f"%{medicine_name}%")
    ).first()

    if not medicine:
        return []

    alternatives = db.query(models.Medicine).filter(
        models.Medicine.active_ingredient == medicine.active_ingredient,
        models.Medicine.dosage == medicine.dosage,
        models.Medicine.id != medicine.id
    ).all()

    response = []
    for alt in alternatives:
        response.append({
            "trade_name": alt.trade_name,
            "active_ingredient": alt.active_ingredient,
            "dosage": alt.dosage,
            "form": alt.form
        })

    return response

def get_pharmacies_with_stock(db):
    results = db.query(
        models.Pharmacy.id,
        models.Pharmacy.name,
        models.Pharmacy.latitude,
        models.Pharmacy.longitude,
        models.Medicine.trade_name,
        models.Inventory.quantity
    ).join(
        models.Inventory, models.Pharmacy.id == models.Inventory.pharmacy_id
    ).join(
        models.Medicine, models.Medicine.id == models.Inventory.medicine_id
    ).all()

    pharmacies = []
    for r in results:
        pharmacies.append({
            "pharmacy_name": r.name,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "medicine": r.trade_name,
            "quantity": r.quantity
        })
    return pharmacies

def create_request(db, pharmacy_id: int, medicine_name: str):
    req = models.MedicineRequest(
        pharmacy_id=pharmacy_id,
        medicine_name=medicine_name
    )
    db.add(req)
    db.commit()
    return {"message": "Request saved"}

def get_sales_data(db, medicine_id: int, pharmacy_id: int = None):
    query = db.query(
        StockMovement.created_at,
        StockMovement.quantity
    ).filter(
        StockMovement.medicine_id == medicine_id,
        StockMovement.quantity < 0
    )

    if pharmacy_id:
        query = query.filter(StockMovement.pharmacy_id == pharmacy_id)

    data = query.order_by(StockMovement.created_at.asc()).all()

    return [(row.created_at, row.quantity) for row in data]

def get_feedback_score(db, pharmacy_id, medicine_id):
    feedbacks = db.query(models.RecommendationFeedback).filter(
        models.RecommendationFeedback.recommended_pharmacy_id == pharmacy_id,
        models.RecommendationFeedback.medicine_id == medicine_id
    ).all()

    if not feedbacks:
        return 0.5

    total_weight = 0
    score = 0

    for f in feedbacks:
        days_old = (datetime.utcnow() - f.created_at).days
        weight = 1 / (1 + days_old)
        score += f.accepted * weight
        total_weight += weight

    return score / total_weight

def smart_recommendation(db, pharmacy_id: int, medicine_id: int):

    from app.ai_model import train_model, predict_future

    requesting = db.query(models.Pharmacy).get(pharmacy_id)
    if not requesting:
        return {"error": "Pharmacy not found"}

    medicine = db.query(models.Medicine).get(medicine_id)
    if not medicine:
        return {"error": "Medicine not found"}

    network = network_search(db, name=medicine.trade_name, pharmacy_id=pharmacy_id)

    data = get_sales_data(db, medicine_id)
    model, df = train_model(data)

    predicted_demand = 0
    if model is not None:
        predictions = predict_future(model, df, days_ahead=7)
        predicted_demand = sum(predictions)

    best_option = None
    best_score = float("inf")

    for p in network:

        if p["pharmacy_id"] == pharmacy_id:
            continue

        if not p.get("distance_km"):
            continue

        stock = p["quantity"]
        distance = p["distance_km"]

        if stock <= 0:
            continue

        feedback_score = get_feedback_score(db, p["pharmacy_id"], medicine_id)

        score = (
            distance * 0.5
            - stock * 0.3
            + predicted_demand * 0.6
            - feedback_score * 2
        )

        if score < best_score:
            best_score = score
            best_option = p

    if best_option is None:
        return {
            "action": "NO_SOLUTION",
            "message": "No pharmacy available with stock"
        }

    # ✅ إشعار توصية AI
    create_notification(
        db,
        pharmacy_id=pharmacy_id,
        message=f"🤖 AI recommends transferring from {best_option['pharmacy_name']} — {best_option['distance_km']} km away",
        type="ai_recommendation"
    )

    return {
        "action": "TRANSFER",
        "from_pharmacy": best_option["pharmacy_name"],
        "recommended_pharmacy_id": best_option["pharmacy_id"],
        "distance_km": best_option["distance_km"],
        "quantity": min(best_option["quantity"], max(1, int(predicted_demand))),
        "predicted_demand": round(predicted_demand, 2),
        "score": round(best_score, 2),
        "reason": "Best balance between distance, stock, predicted demand and feedback history"
    }

def save_feedback(db, pharmacy_id, medicine_id, recommended_pharmacy_id, accepted):
    fb = models.RecommendationFeedback(
        pharmacy_id=pharmacy_id,
        medicine_id=medicine_id,
        recommended_pharmacy_id=recommended_pharmacy_id,
        accepted=accepted
    )
    db.add(fb)
    db.commit()
    return {"message": "Feedback saved"}

def ai_metrics(db):
    total = db.query(models.RecommendationFeedback).count()

    accepted = db.query(models.RecommendationFeedback).filter(
        models.RecommendationFeedback.accepted == 1
    ).count()

    rejected = db.query(models.RecommendationFeedback).filter(
        models.RecommendationFeedback.accepted == 0
    ).count()

    acceptance_rate = (accepted / total * 100) if total > 0 else 0
    confidence = (accepted / total * 100) if total > 0 else 0

    return {
        "total_recommendations": total,
        "accepted": accepted,
        "rejected": rejected,
        "acceptance_rate": round(acceptance_rate, 2),
        "confidence": round(confidence, 2)
    }

def ai_metrics_over_time(db):
    data = db.query(
        models.RecommendationFeedback.created_at,
        models.RecommendationFeedback.accepted
    ).all()

    results = {}

    for d in data:
        date = d.created_at.date()
        if date not in results:
            results[date] = {"accepted": 0, "total": 0}
        results[date]["total"] += 1
        results[date]["accepted"] += d.accepted

    final = []
    for date, values in results.items():
        rate = values["accepted"] / values["total"] if values["total"] > 0 else 0
        final.append({
            "date": str(date),
            "acceptance_rate": round(rate * 100, 2)
        })

    return final

def top_medicines_demand(db):
    data = db.query(
        StockMovement.medicine_id,
        func.count().label("count")
    ).filter(
        StockMovement.quantity < 0
    ).group_by(StockMovement.medicine_id).all()

    response = []
    for d in data:
        medicine = db.query(models.Medicine).get(d.medicine_id)
        if medicine:
            response.append({
                "medicine_name": medicine.trade_name,
                "demand": d.count
            })

    return sorted(response, key=lambda x: x["demand"], reverse=True)

last_training_time = None

def should_retrain(db):
    metrics = ai_metrics(db)

    total = metrics["total_recommendations"]
    acceptance = metrics["acceptance_rate"]

    performance_drop = total > 20 and acceptance < 60

    global last_training_time

    if last_training_time:
        time_condition = datetime.utcnow() - last_training_time > timedelta(hours=24)
    else:
        time_condition = True

    if performance_drop and time_condition:
        return {
            "retrain": True,
            "reason": "Low performance + time passed",
            "acceptance_rate": acceptance,
            "total_decisions": total
        }

    return {
        "retrain": False,
        "reason": "Model stable",
        "acceptance_rate": acceptance,
        "total_decisions": total
    }

def retrain_model(db, medicine_id: int):
    from app.ai_model import train_model

    global last_training_time

    data = get_sales_data(db, medicine_id)

    if len(data) < 5:
        return {
            "status": "Not enough data",
            "medicine_id": medicine_id,
            "data_points": len(data)
        }

    model, df = train_model(data)

    last_training_time = datetime.utcnow()

    log = models.ModelTrainingLog(
        medicine_id=medicine_id,
        data_points=len(data),
        status="success"
    )
    db.add(log)
    db.commit()

    return {
        "status": "Model retrained successfully",
        "medicine_id": medicine_id,
        "data_points": len(data),
        "trained_at": str(last_training_time)
    }

def get_training_logs(db):
    logs = db.query(models.ModelTrainingLog).order_by(
        models.ModelTrainingLog.trained_at.desc()
    ).all()

    return [
        {
            "id": log.id,
            "medicine_id": log.medicine_id,
            "data_points": log.data_points,
            "status": log.status,
            "trained_at": str(log.trained_at)
        }
        for log in logs
    ]

def create_notification(db, pharmacy_id: int, message: str, type: str):
    notif = models.Notification(
        pharmacy_id=pharmacy_id,
        message=message,
        type=type
    )
    db.add(notif)
    db.commit()
    return notif

def get_notifications_for_pharmacy(db, pharmacy_id: int):
    return db.query(models.Notification).filter(
        models.Notification.pharmacy_id == pharmacy_id
    ).order_by(models.Notification.created_at.desc()).all()

def mark_notification_read(db, notification_id: int):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id
    ).first()
    if notif:
        notif.is_read = 1
        db.commit()
    return notif

def get_unread_count(db, pharmacy_id: int):
    return db.query(models.Notification).filter(
        models.Notification.pharmacy_id == pharmacy_id,
        models.Notification.is_read == 0
    ).count()

def log_search(db, medicine_name: str, pharmacy_id: int, found: bool):
    log = models.SearchLog(
        medicine_name=medicine_name.strip().lower(),
        pharmacy_id=pharmacy_id,
        found=1 if found else 0
    )
    db.add(log)
    db.commit()
    return log

def get_market_scarcity(db, limit: int = 10):
    from sqlalchemy import func

    total = db.query(
        models.SearchLog.medicine_name,
        func.count(models.SearchLog.id).label("total_searches"),
        func.sum(models.SearchLog.found).label("total_found")
    ).group_by(
        models.SearchLog.medicine_name
    ).all()

    results = []
    for row in total:
        total_s  = row.total_searches
        found_s  = int(row.total_found or 0)
        failed_s = total_s - found_s
        rate     = round((failed_s / total_s) * 100, 1) if total_s > 0 else 0

        if failed_s == 0:
            continue

        if rate >= 70:
            status = "RARE"
            color  = "#FF4D6A"
            icon   = "🔴"
        elif rate >= 40:
            status = "LIMITED"
            color  = "#FFB800"
            icon   = "🟡"
        else:
            status = "NORMAL"
            color  = "#00E5A0"
            icon   = "🟢"

        results.append({
            "medicine_name":  row.medicine_name.title(),
            "total_searches": total_s,
            "failed_searches": failed_s,
            "found_searches": found_s,
            "scarcity_rate":  rate,
            "status":         status,
            "color":          color,
            "icon":           icon
        })

    results.sort(key=lambda x: x["failed_searches"], reverse=True)
    return results[:limit]