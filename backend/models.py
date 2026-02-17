from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Optional
from sqlalchemy import Date
from datetime import date


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    author: Mapped[str]
    isbn: Mapped[str] = mapped_column(unique=True)
    total_copies: Mapped[int] = mapped_column(default=1)
    available_copies: Mapped[int]
    genre: Mapped[Optional[str]]


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    joined_date: Mapped[date] = mapped_column(Date, default=date.today)
    is_active: Mapped[bool] = mapped_column(default=True)
