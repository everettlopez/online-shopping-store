from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Literal
from fastapi import Form, File, UploadFile
from sqlmodel import Session, select, delete
from datetime import datetime
from app.db.session import get_session
from app.models.product import Product
from app.models.category import Category
from app.models.cart import CartItem
from app.models.order import OrderItem
from app.schemas.product import ProductCreate, ProductRead
from app.auth.dependencies import admin_required
from app.database.products import database_get_product_read, database_get_product_reads
from app.settings import public_api_url, upload_dir
from fastapi import Request

import os
import json
import uuid
from decimal import Decimal

# app/uploads locally, or the UPLOAD_DIR volume in production (served at /uploads)
UPLOAD_DIR = upload_dir()

# Make sure the folder exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Uploads are served back from /uploads, so only accept image types
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


router = APIRouter(prefix="/products", tags=["Products"])


def parse_form_bool(value: str | None, default: bool | None) -> bool | None:
    """FastAPI reads a missing bool form field as False (like an unticked HTML
    checkbox), even with a default of True or None. So boolean form fields come in
    as text, and a missing or blank one keeps the default."""
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in ("true", "1", "yes", "on"):
        return True
    if normalized in ("false", "0", "no", "off"):
        return False
    raise HTTPException(status_code=422, detail="is_active must be true or false")


def save_uploads(request: Request, files: list[UploadFile]) -> list[str]:
    """Save uploaded images under random names and return their public URLs. The
    client's filename is only used for its extension, so it can't escape the uploads
    folder, overwrite another image, or upload a page the browser would run. Every
    file is checked before any is written, so a rejected batch leaves nothing behind."""
    checked = []
    for file in files:
        extension = os.path.splitext(file.filename or "")[1].lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Images must be .jpg, .jpeg, .png, .webp or .gif")

        contents = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail="Images must be 5 MB or smaller")

        checked.append((extension, contents))

    urls = []
    for extension, contents in checked:
        filename = f"{uuid.uuid4().hex}{extension}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(contents)
        urls.append(f"{public_api_url(request)}/uploads/{filename}")

    return urls


# -----------------------------------------
# POST /products → create a new product
# -----------------------------------------
# Plain def (not async): FastAPI runs it in a threadpool, so file and database I/O
# don't block other requests
@router.post("/", response_model=ProductRead, dependencies=[Depends(admin_required)])
def create_product(
    request: Request,
    category_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    price: Decimal = Form(..., ge=0, max_digits=10, decimal_places=2),
    size: str = Form(""),
    color: str = Form(""),
    thumbnail: UploadFile | None = File(None),
    stock_quantity: int = Form(0, ge=0),
    is_active: str | None = Form(None),   # true or false; new products are active by default
    session: Session = Depends(get_session)
):
    category_data = session.exec(select(Category).where(Category.category_id == category_id)).first()
    if not category_data:
        raise HTTPException(status_code=400, detail="Category not found")

    thumbnail_path = None

    if thumbnail:
        [thumbnail_path] = save_uploads(request, [thumbnail])
    
    product_data = ProductCreate(
        category_id=category_id,
        title=title,
        description=description,
        price=price,
        size=size,
        color=color,
        thumbnail=thumbnail_path,
        stock_quantity=stock_quantity,
        is_active=parse_form_bool(is_active, default=True)
    )

    product = Product.model_validate(product_data)
    session.add(product)
    session.commit()
    session.refresh(product)

    return database_get_product_read(session, product.product_id)



# -----------------------------------------
# GET /products → list all products
# -----------------------------------------
@router.get("/", response_model=list[ProductRead])
def list_products(session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    reads = database_get_product_reads(session, [p.product_id for p in products])
    return [reads[p.product_id] for p in products]


@router.get("/active", response_model=list[ProductRead])
def list_active_products(
    category_id: int | None = None,
    sort: Literal["newest"] | None = None,
    limit: int | None = Query(None, ge=1, le=100),
    session: Session = Depends(get_session),
):
    query = select(Product).where(Product.is_active == True)

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    if sort == "newest":
        query = query.order_by(Product.created_at.desc())

    if limit is not None:
        query = query.limit(limit)

    products = session.exec(query).all()
    reads = database_get_product_reads(session, [p.product_id for p in products])
    return [reads[p.product_id] for p in products]


# -----------------------------------------
# GET /products/{product_id} → get one
# -----------------------------------------
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = database_get_product_read(session, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# -----------------------------------------
# PUT /products/{product_id} → update
# -----------------------------------------
@router.put("/{product_id}", response_model=ProductRead, dependencies=[Depends(admin_required)])
def update_product(
    request: Request,
    product_id: int,
    title: str = Form(None),
    category_id: int | None = Form(None),
    description: str = Form(None),
    price: Decimal | None = Form(None, ge=0, max_digits=10, decimal_places=2),
    size: str = Form(None),
    color: str = Form(None),
    thumbnail: str | None = Form(None),
    stock_quantity: int = Form(None, ge=0),
    is_active: str | None = Form(None),   # true or false; left out keeps the current value

    # ⭐ Add these
    images_files: list[UploadFile] = File(None),
    images_urls: str = Form("[]"),

    session: Session = Depends(get_session)
):
    product = session.exec(select(Product).where(Product.product_id == product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        url_list = json.loads(images_urls)
    except json.JSONDecodeError:
        url_list = None
    if not isinstance(url_list, list) or not all(isinstance(u, str) for u in url_list):
        raise HTTPException(status_code=400, detail="images_urls must be a JSON list of strings")

    # Update simple fields
    if title is not None: product.title = title
    if description is not None: product.description = description
    if price is not None: product.price = price
    if size is not None: product.size = size
    if color is not None: product.color = color
    if thumbnail is not None: product.thumbnail = thumbnail
    if stock_quantity is not None: product.stock_quantity = stock_quantity
    active = parse_form_bool(is_active, default=None)
    if active is not None: product.is_active = active
    if category_id is not None:
        if not session.get(Category, category_id):
            raise HTTPException(status_code=400, detail="Category not found")
        product.category_id = category_id

    # ⭐ Save uploaded files
    saved_files = save_uploads(request, images_files or [])

    # ⭐ Merge old + new
    product.images = (product.images or []) + saved_files + url_list

    product.updated_at = datetime.now()

    session.add(product)
    session.commit()

    return database_get_product_read(session, product_id)



# -----------------------------------------
# DELETE /products/{product_id} → delete
# -----------------------------------------
@router.delete("/{product_id}", dependencies=[Depends(admin_required)])
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Order history must keep pointing at the product
    if session.exec(select(OrderItem).where(OrderItem.product_id == product_id)).first():
        raise HTTPException(status_code=409, detail="Product appears in orders and cannot be deleted. Set it inactive instead")

    session.exec(delete(CartItem).where(CartItem.product_id == product_id))
    session.delete(product)
    session.commit()

    return {"message": "Product deleted"}
