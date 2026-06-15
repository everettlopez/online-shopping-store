from datetime import datetime
from pydantic import BaseModel

class CartRead(BaseModel):
    cart_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
