from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Optional


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
