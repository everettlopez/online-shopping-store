from pydantic import BaseModel

class CheckoutRequest(BaseModel):
    # The amount charged is always worked out on the server from the cart, so the
    # client sends only the addresses (anything else, like an old total_amount, is ignored)
    shipping_address_id: int
    billing_address_id: int
