from sqlmodel import SQLModel, Field

class CartItem(SQLModel, table=True):
    __tablename__ = "cart_Items"

    cart_item_id: int | None = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="carts.cart_id")
    product_id: int = Field(foreign_key="products.product_id")
    quantity: int = Field(default=1)
