from datetime import date
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .models import Book, Member, Loan
from .schemas import BookCreate, MemberCreate


# ── Books ──────────────────────────────────────────────────────────────────────

def get_books(
        db: Session,
        title: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        available_only: bool = False,
) -> list[type[Book]]:
    """Retrieve books from the database with optional filtering."""
    query = db.query(Book)
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(Book.genre.ilike(f"%{genre}%"))
    if available_only:
        query = query.filter(Book.available_copies > 0)
    return query.all()


def get_book(db: Session, book_id: int) -> Book | None:
    """Retrieve a single book by its ID."""
    return db.query(Book).filter(Book.id == book_id).first()


def get_book_by_isbn(db: Session, isbn: str) -> Book | None:
    """Retrieve a single book by its ISBN."""
    return db.query(Book).filter(Book.isbn == isbn).first()


def create_book(db: Session, book: BookCreate) -> Book:
    """Create a new book record in the database."""
    new_book = Book(**book.model_dump(), available_copies=book.total_copies)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


def update_book(db: Session, book: Book, update_data: dict) -> Book:
    """Update an existing book's attributes with the provided dictionary of changes."""
    for key, value in update_data.items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    """Delete a book record from the database."""
    db.delete(book)
    db.commit()


def count_active_loans_for_book(db: Session, book_id: int) -> int:
    """Count the number of currently active loans for a specific book."""
    return db.query(Loan).filter(
        Loan.book_id == book_id,
        Loan.returned_date.is_(None)
    ).count()


# ── Members ────────────────────────────────────────────────────────────────────

def get_members(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
) -> list[Member]:
    """Retrieve library members from the database with pagination and optional filtering."""
    query = db.query(Member)
    if name:
        query = query.filter(Member.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(Member.email.ilike(f"%{email}%"))
    if is_active is not None:
        query = query.filter(Member.is_active == is_active)
    return query.offset(skip).limit(limit).all()


def get_member(db: Session, member_id: int) -> Member | None:
    """Retrieve a single member by their ID."""
    return db.query(Member).filter(Member.id == member_id).first()


def get_member_by_email(db: Session, email: str) -> Member | None:
    """Retrieve a single member by their email address."""
    return db.query(Member).filter(Member.email == email).first()


def create_member(db: Session, member: MemberCreate) -> Member:
    """Create a new member record in the database."""
    new_member = Member(**member.model_dump())
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


def update_member(db: Session, member: Member, update_data: dict) -> Member:
    """Update an existing member's attributes with the provided dictionary of changes."""
    for field, value in update_data.items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member


def delete_member(db: Session, member: Member) -> None:
    """Delete a member record from the database."""
    db.delete(member)
    db.commit()


def get_member_loans(db: Session, member_id: int) -> list[type[Loan]]:
    """Retrieve all loans associated with a specific member."""
    return db.query(Loan).filter(Loan.member_id == member_id).all()


def count_active_loans_for_member(db: Session, member_id: int) -> int:
    """Count the number of currently active loans for a specific member."""
    return db.query(func.count(Loan.id)).filter(
        Loan.member_id == member_id,
        Loan.returned_date.is_(None)
    ).scalar()


def calculate_member_fines(loans: list[Loan]) -> float:
    """Calculate total outstanding fines for a member.

    Considers:
    - $0.50/day overdue for active loans (not yet returned).
    - Recorded fine_amount on returned loans.
    """
    return calculate_detailed_member_fines(loans)["total_fines"]


def calculate_detailed_member_fines(loans: list[Loan]) -> dict:
    """Calculate total outstanding fines: $0.50/day overdue for active loans
    plus any recorded fine_amount on returned loans.

    Returns a dictionary with details for reporting.
    """
    total_fines = 0.0
    active_overdue_loans = 0
    unpaid_returned_fines = 0.0
    today = date.today()

    for loan in loans:
        if loan.returned_date is None and loan.due_date < today:
            overdue_days = (today - loan.due_date).days
            total_fines += overdue_days * 0.50
            active_overdue_loans += 1
        elif loan.returned_date and loan.fine_amount:
            total_fines += loan.fine_amount
            unpaid_returned_fines += loan.fine_amount

    return {
        "total_fines": round(total_fines, 2),
        "active_overdue_loans": active_overdue_loans,
        "unpaid_returned_fines": round(unpaid_returned_fines, 2)
    }


# ── Loans ──────────────────────────────────────────────────────────────────────

def get_active_loan(db: Session, member_id: int, book_id: int) -> Loan | None:
    """Retrieve an active loan (not yet returned) for a specific member and book."""
    return db.query(Loan).filter(
        and_(
            Loan.member_id == member_id,
            Loan.book_id == book_id,
            Loan.returned_date.is_(None)
        )
    ).first()


def get_active_loans_for_member(db: Session, member_id: int) -> list[Loan]:
    """Retrieve all active loans (not yet returned) for a specific member."""
    return db.query(Loan).filter(
        and_(
            Loan.member_id == member_id,
            Loan.returned_date.is_(None)
        )
    ).all()


def create_loan(db: Session, book: Book, member_id: int) -> Loan:
    """Create a loan record and decrement the book's available copies atomically."""
    book.available_copies -= 1
    new_loan = Loan(book_id=book.id, member_id=member_id)
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan


def close_loan(db: Session, loan: Loan, book: Book) -> Loan:
    """Mark a loan as returned, calculate any fine, and restore available copies."""
    today = date.today()
    loan.returned_date = today
    loan.fine_amount = max(0.0, (today - loan.due_date).days * 0.50) if today > loan.due_date else 0.0
    book.available_copies += 1
    db.commit()
    db.refresh(loan)
    return loan
