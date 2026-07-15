from fastapi import APIRouter, Depends, HTTPException
from fastapi import Form, File, UploadFile
from sqlmodel import Session, select
from datetime import datetime
from app.db.session import get_session
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, ProductResponse, Metadata as ProductMetadata
from app.auth.dependencies import admin_required
from app.database.products import database_get_products

router = APIRouter(prefix="/products", tags=["Products"])


# -----------------------------------------
# POST /products → create a new product
# -----------------------------------------
@router.post("/", response_model=ProductRead, dependencies=[Depends(admin_required)])
def create_product(
    category_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    size: str = Form(""),
    color: str = Form(""),
    image_url: str = Form(""),
    stock_quantity: int = Form(0),
    is_active: bool = Form(True),
    image: UploadFile | None = File(None),
    session: Session = Depends(get_session)
):
    # Validate category exists
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")

    product = Product(
        category_id=category_id,
        name=name,
        description=description,
        price=price,
        size=size,
        color=color,
        image_url=image_url,
        stock_quantity=stock_quantity,
        is_active=is_active,
    )
    
    session.add(product)
    session.commit()
    session.refresh(product)

    return product


# -----------------------------------------
# GET /products → list all products
# -----------------------------------------
@router.get("/", response_model=ProductResponse)
def list_products(session: Session = Depends(get_session), category: int | None = None,
    size: str | None = None,
    color: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    sort: str | None = None):

    statement = select(Product)

    if category is not None:
        statement = statement.where(Product.category_id == category)
    
    if size is not None:
        statement = statement.where(Product.size == size)

    if color is not None:
        statement = statement.where(Product.color == color)

    if price_min is not None:
        statement = statement.where(Product.price >= price_min)
    
    if price_max is not None:
        statement = statement.where(Product.price <= price_max)


    filtered_products = session.exec(statement).all()

    sorted_products = database_get_products(session=session, sort=sort)

    products_read = [ProductRead.model_validate(p.__dict__) for p in filtered_products]

    return ProductResponse(metadata = ProductMetadata(count = len(products_read), sort = sort), products = products_read)


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
    name: str = Form(None),
    category_id: int | None = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    size: str = Form(None),
    color: str = Form(None),
    image_url: str = Form(None),
    stock_quantity: int = Form(None),
    is_active: bool = Form(None),
    image: UploadFile | None = File(None),
    session: Session = Depends(get_session)
):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if name is not None: product.name = name
    if description is not None: product.description = description
    if price is not None: product.price = price
    if size is not None: product.size = size
    if color is not None: product.color = color
    if image_url is not None: product.image_url = image_url
    if stock_quantity is not None: product.stock_quantity = stock_quantity
    if is_active is not None: product.is_active = is_active

    if category_id is not None:
        product.category_id = category_id


    if image is not None:
        product.image_url = f"/uploads/{image.filename}"

    product.updated_at = datetime.utcnow();

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
