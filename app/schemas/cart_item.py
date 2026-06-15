from pydantic import BaseModel

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemRead(BaseModel):
    cart_item_id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True

class CartItemUpdate(BaseModel):
    quantity: int
