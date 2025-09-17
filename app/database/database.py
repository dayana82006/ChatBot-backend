# app/database/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base  # importa desde models.base

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    Base.metadata.create_all(bind=engine)
