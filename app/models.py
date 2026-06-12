# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Pharmacy(Base):
    __tablename__ = "pharmacies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    trade_name = Column(String, index=True)
    active_ingredient = Column(String, index=True)
    dosage = Column(String)
    form = Column(String)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    quantity = Column(Integer)

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    quantity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
class MedicineRequest(Base):
    __tablename__ = "medicine_requests"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer)
    medicine_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    fulfilled = Column(Integer, default=0)
class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer)
    medicine_id = Column(Integer)
    recommended_pharmacy_id = Column(Integer)
    accepted = Column(Integer)  # 1 = yes, 0 = no
    created_at = Column(DateTime, default=datetime.utcnow)
class ModelTrainingLog(Base):
    __tablename__ = "model_training_log"

    id = Column(Integer, primary_key=True, index=True)
    medicine_id = Column(Integer)
    trained_at = Column(DateTime, default=datetime.utcnow)
    data_points = Column(Integer)
    status = Column(String)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True)
    is_active = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)  # 👈 جديد
    created_at = Column(DateTime, default=datetime.utcnow)
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"))
    message = Column(String)
    type = Column(String)  # low_stock / medicine_available / ai_recommendation
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    medicine_name = Column(String, nullable=False)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True)
    found = Column(Integer, default=0)  # 0 = not found, 1 = found
    created_at = Column(DateTime, default=datetime.utcnow)