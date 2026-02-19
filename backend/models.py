from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from typing import Optional
from sqlalchemy import Date, ForeignKey
from datetime import date, timedelta


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

    loans: Mapped[list["Loan"]] = relationship(back_populates="member")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    borrowed_date: Mapped[date] = mapped_column(Date, default=date.today)
    due_date: Mapped[date] = mapped_column(Date, default=lambda: date.today() + timedelta(days=14))
    returned_date: Mapped[Optional[date]] = mapped_column(Date)
    fine_amount: Mapped[Optional[float]]

    member: Mapped["Member"] = relationship(back_populates="loans")
