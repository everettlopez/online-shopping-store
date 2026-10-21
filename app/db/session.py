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

def seed_database():
    # The schema is managed by Alembic (run `alembic upgrade head`); startup only seeds data
    from app.database.category import database_seed_categories

    with SQLModelSession(engine) as session:
        database_seed_categories(session)

def get_session() -> Generator:
    with SQLModelSession(engine) as session:
        yield session
