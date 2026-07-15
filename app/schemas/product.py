from pydantic import BaseModel
from datetime import datetime

class Metadata(BaseModel):
    count: int
    sort: str | None = None

class ProductCreate(BaseModel):
    category_id: int
    name: str
    description: str | None = None
    price: float

    size: str | None = None
    color: str | None = None
    image_url: str | None = None

    stock_quantity: int = 1
    is_active: bool = True

class ProductRead(BaseModel):
    product_id: int
    category_id: int
    name: str
    description: str | None
    price: float

    size: str | None = None
    color: str | None = None
    image_url: str | None = None

    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: list[str] | None = None

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    description: str | None = None
    price: float | None = None

    size: str | None = None
    color: str | None = None
    image_url: str | None = None

    stock_quantity: int | None = None
    is_active: bool | None = None

class ProductResponse(BaseModel):
    metadata: Metadata
    products: list[ProductRead]