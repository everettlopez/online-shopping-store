from pydantic import BaseModel
from datetime import datetime

class OrderCreate(BaseModel):
    shipping_address_id: int
    billing_address_id: int
    total_amount: float

class OrderRead(BaseModel):
    order_id: int
    order_number: str
    status: str
    order_date: datetime
    total_amount: float

    class Config:
        from_attributes = True
