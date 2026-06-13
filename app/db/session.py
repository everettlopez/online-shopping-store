from sqlmodel import SQLModel
from sqlmodel import Session as SQLModelSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

DATABASE_URL = "mysql+pymysql://root:%40RjpN4675is@localhost:3306/online_store"

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
    SQLModel.metadata.create_all(bind=engine)

def get_session() -> Generator:
    with SQLModelSession(engine) as session:
        yield session
