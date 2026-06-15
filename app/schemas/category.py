from pydantic import BaseModel

class CategoryCreate(BaseModel):
    name: str
    description: str | None = None

class CategoryRead(BaseModel):
    category_id: int
    name: str
    description: str | None

    class Config:
        from_attributes = True

class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
