from fastapi import FastAPI
from app.db.session import create_db_and_tables
from app.routes.auth import router as auth_router
from app.routes.address import router as address_router
from app.routes.order import router as order_router
from app.routes.cart import router as cart_router
from app.routes.product import router as product_router
from app.routes.category import router as category_router
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"message": "API is running"}

app.include_router(auth_router, prefix="/api")
app.include_router(address_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(category_router, prefix="/api")
