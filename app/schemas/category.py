from pydantic import BaseModel

class Metadata(BaseModel):
    count: int
    sort: str | None = None


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None

class CategoryRead(BaseModel):
    category_id: int
    name: str
    description: str | None
    sort_order: int

    class Config:
        from_attributes = True

class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class CategoryReorder(BaseModel):
    category_ids: list[int]

class CategoryResponse(BaseModel):
    metadata: Metadata
    categories: list[CategoryRead]