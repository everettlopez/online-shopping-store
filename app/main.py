from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import create_db_and_tables
from app.routes.auth import router as auth_router
from app.routes.address import router as address_router
from app.routes.order import router as order_router
from app.routes.cart import router as cart_router
from app.routes.product import router as product_router
from app.routes.category import router as category_router
from app.routes.admin import router as admin_router
from fastapi.openapi.utils import get_openapi

from fastapi.staticfiles import StaticFiles

import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# -----------------------------
# CORS FIX (this is what you need)
# -----------------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,   # REQUIRED for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/api")
def root():
    return {"message": "API is running"}

app.include_router(auth_router, prefix="/api")
app.include_router(address_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(cart_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(category_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
