from pydantic import BaseModel, Field
from typing import Literal, Optional

class AddressCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    line1: str = Field(min_length=1, max_length=200)
    line2: Optional[str] = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    county: Optional[str] = Field(default=None, max_length=100)
    country: str = Field(default="US", pattern="^[A-Z]{2}$")   # ISO 3166-1 alpha-2
    address_type: Literal["shipping", "billing"]

class AddressRead(BaseModel):
    address_id: int
    user_id: int
    full_name: str
    phone: Optional[str]
    line1: str
    line2: Optional[str]
    city: str
    state: str
    postal_code: str
    county: Optional[str]
    country: str
    address_type: str

    class Config:
        from_attributes = True

class OrderAddress(BaseModel):
    """The copy of an address kept on an order, so editing or deleting the saved
    address later doesn't change where a past order went."""
    full_name: str
    phone: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    county: Optional[str] = None
    country: str

    class Config:
        from_attributes = True

def address_snapshot(address) -> dict | None:
    """The OrderAddress copy of an Address row, as stored in an order's JSON column."""
    return OrderAddress.model_validate(address).model_dump() if address else None
