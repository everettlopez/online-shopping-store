from fastapi import APIRouter, Depends, HTTPException
from fastapi import Form, File, UploadFile
from sqlmodel import Session, select
from datetime import datetime
from app.db.session import get_session
from app.models.product import Product
from app.models.category import Category
from app.schemas.category import CategoryRead
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, ProductResponse, Metadata as ProductMetadata
from app.auth.dependencies import admin_required
from app.database.products import database_get_products
from fastapi import Request

import os

# Get the directory of this file: app/routes/product.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up one folder: app/
APP_DIR = os.path.dirname(BASE_DIR)

# Point to: app/uploads
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")

# Make sure the folder exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


router = APIRouter(prefix="/products", tags=["Products"])


# -----------------------------------------
# POST /products → create a new product
# -----------------------------------------
@router.post("/", response_model=ProductRead, dependencies=[Depends(admin_required)])
async def create_product(
    request: Request,
    category_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    size: str = Form(""),
    color: str = Form(""),
    thumbnail: UploadFile | None = File(None),
    stock_quantity: int = Form(0),
    is_active: bool = Form(True),
    session: Session = Depends(get_session)
):
    thumbnail_path = None

    if thumbnail:
        contents = await thumbnail.read()
        file_path = f"app/uploads/{thumbnail.filename}"



        with open(file_path, "wb") as f:
            f.write(contents)

        thumbnail_path = f"{request.base_url}uploads/{thumbnail.filename}"

    
    product_data = ProductCreate(
        category_id=category_id,
        title=title,
        description=description,
        price=price,
        size=size,
        color=color,
        thumbnail=thumbnail_path,
        stock_quantity=stock_quantity,
        is_active=is_active
    )

    product = Product.model_validate(product_data)
    session.add(product)
    session.commit()
    session.refresh(product)

    category_data = session.exec(select(Category).where(Category.category_id == category_id)).first()
    category = CategoryRead(
        category_id=category_data.category_id,
        name=category_data.name,
        description=category_data.description
    )

    return ProductRead(
        product_id=product.product_id,
        category=category,
        title=product.title,
        description=product.description,
        price=product.price,
        size=product.size,
        color=product.color,
        thumbnail=product.thumbnail,
        images=product.images,
        stock_quantity=product.stock_quantity,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at
    )



# -----------------------------------------
# GET /products → list all products
# -----------------------------------------
@router.get("/", response_model=list[ProductRead])
def list_products(session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    enriched_products = []

    for product in products:

        category = session.exec(select(Category).where(Category.category_id == product.category_id)).first()

        enriched_products.append(ProductRead(
            product_id=product.product_id,
            category=category,
            title=product.title,
            description=product.description,
            price=product.price,
            size=product.size,
            color=product.color,
            thumbnail=product.thumbnail,
            stock_quantity=product.stock_quantity,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            images=product.images
        ))
    return enriched_products


@router.get("/active", response_model=list[ProductRead])
def list_active_products(session: Session = Depends(get_session)):
    products = session.exec(select(Product).where(Product.is_active == True)).all()
    enriched_products = []

    for product in products:

        category = session.exec(select(Category).where(Category.category_id == product.category_id)).first()

        enriched_products.append(ProductRead(
            product_id=product.product_id,
            category=category,
            title=product.title,
            description=product.description,
            price=product.price,
            size=product.size,
            color=product.color,
            thumbnail=product.thumbnail,
            stock_quantity=product.stock_quantity,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            images=product.images
        ))
    return enriched_products


# -----------------------------------------
# GET /products/{product_id} → get one
# -----------------------------------------
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.exec(select(Product).where(Product.product_id == product_id)).first()

    if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    
    category = session.exec(select(Category).where(Category.category_id == product.category_id)).first()

    return ProductRead(
        product_id=product.product_id,
        category=category,
        title=product.title,
        description=product.description,
        price=product.price,
        size=product.size,
        color=product.color,
        thumbnail=product.thumbnail,
        stock_quantity=product.stock_quantity,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        images=product.images
    )


# -----------------------------------------
# PUT /products/{product_id} → update
# -----------------------------------------
@router.put("/{product_id}", response_model=ProductRead, dependencies=[Depends(admin_required)])
async def update_product(
    product_id: int,
    title: str = Form(None),
    category_id: int | None = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    size: str = Form(None),
    color: str = Form(None),
    thumbnail: str | None = Form(None),
    stock_quantity: int = Form(None),
    is_active: bool = Form(None),

    # ⭐ Add these
    images_files: list[UploadFile] = File(None),
    images_urls: str = Form("[]"),

    session: Session = Depends(get_session)
):
    product = session.exec(select(Product).where(Product.product_id == product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update simple fields
    if title is not None: product.title = title
    if description is not None: product.description = description
    if price is not None: product.price = price
    if size is not None: product.size = size
    if color is not None: product.color = color
    if thumbnail is not None: product.thumbnail = thumbnail
    if stock_quantity is not None: product.stock_quantity = stock_quantity
    if is_active is not None: product.is_active = is_active
    if category_id is not None: product.category_id = category_id

    # ⭐ Save uploaded files
    saved_files = []
    if images_files:
        for file in images_files:
            filepath = os.path.join(UPLOAD_DIR, file.filename)

            with open(filepath, "wb") as f:
                f.write(await file.read())

            saved_files.append(f"uploads/{file.filename}")   # relative path for frontend


    # ⭐ Merge URL images
    import json
    url_list = json.loads(images_urls)

    # ⭐ Merge old + new
    product.images = (product.images or []) + saved_files + url_list

    product.updated_at = datetime.now()

    category = session.exec(select(Category).where(Category.category_id == product.category_id)).first()

    session.add(product)
    session.commit()
    session.refresh(product)

    return ProductRead(
        product_id=product.product_id,
        category=category,
        title=product.title,
        description=product.description,
        price=product.price,
        size=product.size,
        color=product.color,
        thumbnail=product.thumbnail,
        stock_quantity=product.stock_quantity,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        images=product.images
    )



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
