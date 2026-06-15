from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate
)

router = APIRouter(prefix="/categories", tags=["Categories"])


# -----------------------------------------
# POST /categories → create a new category
# -----------------------------------------
@router.post("/", response_model=CategoryRead)
def create_category(
    data: CategoryCreate,
    session: Session = Depends(get_session)
):
    category = Category(**data.dict())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


# -----------------------------------------
# GET /categories → list all categories
# -----------------------------------------
@router.get("/", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)):
    statement = select(Category)
    return session.exec(statement).all()


# -----------------------------------------
# GET /categories/{category_id} → get one
# -----------------------------------------
@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


# -----------------------------------------
# PUT /categories/{category_id} → update
# -----------------------------------------
@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: Session = Depends(get_session)
):
    category = session.get(Category, category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(category, key, value)

    session.add(category)
    session.commit()
    session.refresh(category)

    return category


# -----------------------------------------
# DELETE /categories/{category_id} → delete
# -----------------------------------------
@router.delete("/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    session.delete(category)
    session.commit()

    return {"message": "Category deleted"}

