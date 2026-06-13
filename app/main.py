from fastapi import FastAPI
from app.db.session import create_db_and_tables
from app.routes.auth import router as auth_router
from fastapi.openapi.utils import get_openapi

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"message": "API is running"}

app.include_router(auth_router)
