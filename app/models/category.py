from __future__ import annotations
from sqlmodel import SQLModel, Field

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    category_id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None

    # Position in the storefront nav (lowest first); admins change it with the reorder arrows
    sort_order: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
