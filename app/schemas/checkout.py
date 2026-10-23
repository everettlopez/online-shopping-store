from pydantic import BaseModel, Field

from app.schemas.cart_item import CartLine, MAX_CART_LINES

class CheckoutRequest(BaseModel):
    # The amount charged is always worked out on the server, so the client sends only
    # what to buy and where it goes (anything else, like an old total_amount, is ignored).
    # Logged-in shoppers check out their account cart with saved addresses
    shipping_address_id: int | None = None
    billing_address_id: int | None = None
    # Guests send their browser cart; Stripe collects their email and addresses
    items: list[CartLine] | None = Field(default=None, max_length=MAX_CART_LINES)
