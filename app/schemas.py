from pydantic import BaseModel
from typing import Optional

class PharmacyCreate(BaseModel):
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class MedicineCreate(BaseModel):
    trade_name: str
    active_ingredient: str
    dosage: str
    form: str

class InventoryCreate(BaseModel):
    pharmacy_id: int
    medicine_id: int
    quantity: int