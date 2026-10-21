from pydantic import BaseModel
from typing import Literal, Optional

class AddressCreate(BaseModel):
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    county: Optional[str] = None
    address_type: Literal["shipping", "billing"]

class AddressRead(BaseModel):
    address_id: int
    user_id: int
    line1: str
    line2: Optional[str]
    city: str
    state: str
    postal_code: str
    county: Optional[str]
    address_type: str

    class Config:
        from_attributes = True
