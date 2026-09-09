from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.session import get_session
from app.auth.dependencies import admin_required

from app.models.user import User
from app.schemas.user import UserRead, UserResponse, Metadata as UserMetadata
from app.models.product import Product
from app.models.category import Category
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

from app.database.users import database_get_users



router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(admin_required)]
)

@router.get("/")
def admin_home():
    return {"message": "Welcome to the admin dashboard"}

@router.post("/products")
def create_product(product: ProductCreate):
    # logic here
    return {"message": "Product created"}

@router.put("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    # logic here
    return {"message": "Product updated"}

@router.post("/categories")
def create_category(category: CategoryCreate):
    return {"message": "Category created"}

@router.get("/users", response_model=UserResponse)
def get_all_users(session: Session = Depends(get_session), sort: str | None = None):
    users = database_get_users(session, sort)

    user_reads = [UserRead.model_validate(u.__dict__) for u in users]


    return UserResponse(
        metadata = UserMetadata(count=len(users), sort=sort),
        users = user_reads
    )
