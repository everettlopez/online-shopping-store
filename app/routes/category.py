from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from app.db.session import get_session
from app.models.category import Category
from app.models.product import Product
from app.auth.dependencies import admin_required
from app.schemas.category import (
    Metadata as CategoryMetadata,
    CategoryResponse,
    CategoryCreate,
    CategoryRead,
    CategoryReorder,
    CategoryUpdate
)
from app.database.category import database_get_categories

router = APIRouter(prefix="/categories", tags=["Categories"])


def ensure_unique_name(session: Session, name: str, category_id: int | None = None):
    existing = session.exec(select(Category).where(func.lower(Category.name) == name.strip().lower())).first()
    if existing and existing.category_id != category_id:
        raise HTTPException(status_code=409, detail=f"A category named '{name}' already exists")


# -----------------------------------------
# POST /categories → create a new category
# -----------------------------------------
@router.post("/", response_model=CategoryRead, dependencies=[Depends(admin_required)])
def create_category(
    data: CategoryCreate,
    session: Session = Depends(get_session)
):
    ensure_unique_name(session, data.name)

    # New categories go to the end of the nav
    last_position = session.exec(select(func.max(Category.sort_order))).one() or 0

    category = Category(**data.model_dump(), sort_order=last_position + 1)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


# -----------------------------------------
# GET /categories → list all categories
# -----------------------------------------
@router.get("/", response_model=CategoryResponse)
def list_categories(session: Session = Depends(get_session), sort: str | None = None):
    categories = database_get_categories(session, sort)

    category_reads = [CategoryRead.model_validate(c.__dict__) for c in categories]

    return CategoryResponse(
        metadata = CategoryMetadata(count = len(categories), sort = sort),
        categories = category_reads
    )

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
# PUT /categories/reorder → set nav order
# (declared before /{category_id} so "reorder" isn't parsed as an id)
# -----------------------------------------
@router.put("/reorder", response_model=CategoryResponse, dependencies=[Depends(admin_required)])
def reorder_categories(data: CategoryReorder, session: Session = Depends(get_session)):
    categories = {c.category_id: c for c in session.exec(select(Category)).all()}

    if len(data.category_ids) != len(set(data.category_ids)) or set(data.category_ids) != set(categories):
        raise HTTPException(status_code=400, detail="category_ids must list every category exactly once")

    for position, category_id in enumerate(data.category_ids, start=1):
        categories[category_id].sort_order = position
        session.add(categories[category_id])

    session.commit()

    return list_categories(session=session, sort="order")


# -----------------------------------------
# PUT /categories/{category_id} → update
# -----------------------------------------
@router.put("/{category_id}", response_model=CategoryRead, dependencies=[Depends(admin_required)])
def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: Session = Depends(get_session)
):
    category = session.get(Category, category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("name"):
        ensure_unique_name(session, update_data["name"], category_id)

    for key, value in update_data.items():
        setattr(category, key, value)

    session.add(category)
    session.commit()
    session.refresh(category)

    return category


# -----------------------------------------
# DELETE /categories/{category_id} → delete
# -----------------------------------------
@router.delete("/{category_id}", dependencies=[Depends(admin_required)])
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    product_count = session.exec(select(func.count()).select_from(Product).where(Product.category_id == category_id)).one()
    if product_count:
        raise HTTPException(status_code=409, detail=f"Category is used by {product_count} product(s). Reassign or delete them first")

    session.delete(category)
    session.commit()

    return {"message": "Category deleted"}

