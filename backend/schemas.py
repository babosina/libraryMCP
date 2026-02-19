from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date
import re


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


# ========== MEMBER SCHEMAS ==========
class MemberBase(BaseModel):
    name: str = Field(..., examples=["Bob Smith"])
    email: str = Field(..., examples=["bob@example.com"])

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email address')
        return v


class MemberCreate(MemberBase):
    pass


class MemberResponse(MemberBase):
    id: int
    joined_date: date
    is_active: bool
    loans: Optional[List["LoanResponse"]] = Field(default=None,
                                                  description="Loan history (only included in detail view)")
    active_loans_count: Optional[int] = Field(default=None, description="Number of currently active loans")
    total_fines: Optional[float] = Field(default=None, description="Total outstanding fines")

    class Config:
        from_attributes = True


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email address')
        return v


# ========== LOAN SCHEMAS ==========
class LoanBase(BaseModel):
    book_id: int
    member_id: int


class LoanCreate(LoanBase):
    pass


class LoanResponse(LoanBase):
    id: int
    borrowed_date: date
    due_date: date
    returned_date: Optional[date] = None
    fine_amount: Optional[float] = None

    class Config:
        from_attributes = True
