import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

"""
Database configuration and session management.
"""

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./library.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy declarative models.
    """
    pass


# Dependency for FastAPI routes
def get_db():
    """
    Yields a database session to be used in FastAPI dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
