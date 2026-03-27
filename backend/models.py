"""
Database models for the LibraryMCP application.
This module defines the SQLAlchemy ORM models for Books, Members, and Loans.
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Book(Base):
    """
    Represents a book in the library system.
    """
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    author: Mapped[str]
    isbn: Mapped[str] = mapped_column(unique=True)
    total_copies: Mapped[int] = mapped_column(default=1)
    available_copies: Mapped[int]
    genre: Mapped[Optional[str]]


class Member(Base):
    """
    Represents a library member.
    """
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    joined_date: Mapped[date] = mapped_column(Date, default=date.today)
    is_active: Mapped[bool] = mapped_column(default=True)

    loans: Mapped[list["Loan"]] = relationship(back_populates="member")


class Loan(Base):
    """
    Represents a book loan record.
    """
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    borrowed_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date] = mapped_column(Date, default=lambda: date.today() + timedelta(days=14))
    returned_date: Mapped[Optional[date]] = mapped_column(Date)
    fine_amount: Mapped[Optional[float]]

    member: Mapped["Member"] = relationship(back_populates="loans")
