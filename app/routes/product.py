from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.auth.dependencies import admin_required

router = APIRouter(prefix="/products", tags=["Products"])


# -----------------------------------------
# POST /products → create a new product
# -----------------------------------------
@router.post("/", response_model=ProductRead, dependencies=[Depends(admin_required)])
def create_product(
    data: ProductCreate,
    session: Session = Depends(get_session)
):
    # Validate category exists
    category = session.get(Category, data.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")

    product = Product(**data.dict())
    session.add(product)
    session.commit()
    session.refresh(product)

    return product


# -----------------------------------------
# GET /products → list all products
# -----------------------------------------
@router.get("/", response_model=list[ProductRead])
def list_products(session: Session = Depends(get_session)):
    statement = select(Product)
    return session.exec(statement).all()


# -----------------------------------------
# GET /products/{product_id} → get one
# -----------------------------------------
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# -----------------------------------------
# PUT /products/{product_id} → update
# -----------------------------------------
@router.put("/{product_id}", response_model=ProductRead, dependencies=[Depends(admin_required)])
def update_product(
    product_id: int,
    data: ProductUpdate,
    session: Session = Depends(get_session)
):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(product, key, value)

    session.add(product)
    session.commit()
    session.refresh(product)

    return product


# -----------------------------------------
# DELETE /products/{product_id} → delete
# -----------------------------------------
@router.delete("/{product_id}", dependencies=[Depends(admin_required)])
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    session.delete(product)
    session.commit()

    return {"message": "Product deleted"}
