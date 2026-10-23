from pydantic import BaseModel, Field

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemRead(BaseModel):
    cart_item_id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True

# Keeps quantities far below the database's INT limit
MAX_CART_QUANTITY = 99

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=MAX_CART_QUANTITY)

# Limits how many lines a guest cart can send
MAX_CART_LINES = 100

class CartLine(BaseModel):
    """One product of a guest's browser cart."""
    product_id: int
    quantity: int = Field(ge=1, le=MAX_CART_QUANTITY)

class CartMerge(BaseModel):
    # A guest's browser cart, added to the account cart on login
    items: list[CartLine] = Field(max_length=MAX_CART_LINES)
