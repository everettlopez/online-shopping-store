from sqlmodel import SQLModel
from sqlmodel import Session as SQLModelSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    echo=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def create_db_and_tables():
    from app.models.user import User
    from app.models.product import Product
    from app.models.category import Category
    from app.models.cart import CartItem
    from app.models.cart import Cart
    from app.models.user import User
    from app.models.address import Address
    from app.models.order import Order

    SQLModel.metadata.create_all(bind=engine)

    from app.database.category import database_seed_categories

    with SQLModelSession(engine) as session:
        database_seed_categories(session)

def get_session() -> Generator:
    with SQLModelSession(engine) as session:
        yield session
