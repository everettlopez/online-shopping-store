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
