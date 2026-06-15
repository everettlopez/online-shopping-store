from __future__ import annotations
from sqlmodel import SQLModel, Field
from datetime import datetime

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    category_id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
