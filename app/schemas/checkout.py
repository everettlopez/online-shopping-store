from pydantic import BaseModel

class CheckoutRequest(BaseModel):
    total_amount: float
    shipping_address_id: int
    billing_address_id: int
