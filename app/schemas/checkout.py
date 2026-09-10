from pydantic import BaseModel

class CheckoutRequest(BaseModel):
    shipping_address_id: int
    billing_address_id: int
