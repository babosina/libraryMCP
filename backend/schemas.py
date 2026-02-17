from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date


# ========== BOOK SCHEMAS ==========
class BookBase(BaseModel):
    title: str = Field(..., examples=["1984"])
    author: str = Field(..., examples=["George Orwell"])
    isbn: str = Field(..., examples=["978-0451524935"])
    total_copies: int = Field(default=1, ge=1)
    genre: Optional[str] = Field(None, examples=["Fiction"])


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    total_copies: Optional[int] = Field(None, ge=1)
    available_copies: Optional[int] = Field(None, ge=0)
    genre: Optional[str] = None


class BookResponse(BookBase):
    id: int
    available_copies: int

    class Config:
        from_attributes = True
