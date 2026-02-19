from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import List

from ..database import get_db
from ..models import Book, Member, Loan
from ..schemas import LoanCreate, LoanResponse

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/borrow", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def borrow_book(
        loan: LoanCreate,
        db: Session = Depends(get_db)
):
    """
    Borrow a book (creates a loan record).

    - **book_id**: The ID of the book to borrow
    - **member_id**: The ID of the member borrowing the book

    Business rules:
    - Book must exist and have available copies > 0
    - Member must exist and be active
    - Member cannot borrow the same book twice simultaneously
    """
    # Check if member exists and is active
    member = db.query(Member).filter(Member.id == loan.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if not member.is_active:
        raise HTTPException(status_code=400, detail="Member account is not active")

    # Check if book exists
    book = db.query(Book).filter(Book.id == loan.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if book has available copies
    if book.available_copies <= 0:
        raise HTTPException(
            status_code=409,
            detail=f"Book '{book.title}' has no available copies"
        )

    # Check if member already has an active loan for this book
    existing_loan = db.query(Loan).filter(
        and_(
            Loan.member_id == loan.member_id,
            Loan.book_id == loan.book_id,
            Loan.returned_date.is_(None)
        )
    ).first()

    if existing_loan:
        raise HTTPException(
            status_code=409,
            detail="Member already has an active loan for this book"
        )

    # Create the loan
    new_loan = Loan(
        book_id=loan.book_id,
        member_id=loan.member_id
    )

    # Decrement available copies
    book.available_copies -= 1

    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)

    return new_loan


@router.post("/return", response_model=LoanResponse)
def return_book(
        loan: LoanCreate,
        db: Session = Depends(get_db)
):
    """
    Return a borrowed book.

    - **book_id**: The ID of the book being returned
    - **member_id**: The ID of the member returning the book

    Business rules:
    - Loan must exist and be active (not already returned)
    - Fine is calculated if book is overdue ($0.50 per day)
    - Book's available_copies is incremented
    """
    # Find the active loan
    active_loan = db.query(Loan).filter(
        and_(
            Loan.member_id == loan.member_id,
            Loan.book_id == loan.book_id,
            Loan.returned_date.is_(None)
        )
    ).first()

    if not active_loan:
        raise HTTPException(
            status_code=400,
            detail="No active loan found for this book and member"
        )

    # Set return date
    today = date.today()
    active_loan.returned_date = today

    # Calculate fine if overdue
    if today > active_loan.due_date:
        overdue_days = (today - active_loan.due_date).days
        active_loan.fine_amount = overdue_days * 0.50
    else:
        active_loan.fine_amount = 0.0

    # Increment available copies
    book = db.query(Book).filter(Book.id == loan.book_id).first()
    if book:
        book.available_copies += 1

    db.commit()
    db.refresh(active_loan)

    return active_loan


@router.get("/{member_id}", response_model=List[LoanResponse])
def get_loans(
        member_id: int,
        db: Session = Depends(get_db)
):
    """
    Get all active loans for a member.

    - **member_id**: The ID of the member

    Returns only loans where returned_date is NULL (active loans).
    """
    # Check if member exists
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get active loans
    active_loans = db.query(Loan).filter(
        and_(
            Loan.member_id == member_id,
            Loan.returned_date.is_(None)
        )
    ).all()

    return active_loans


@router.get("/{member_id}/fines", response_model=dict)
def check_fines(
        member_id: int,
        db: Session = Depends(get_db)
):
    """
    Calculate overdue fines for a member.

    - **member_id**: The ID of the member

    Returns:
    - **member_id**: The member's ID
    - **total_fines**: Total outstanding fines (includes overdue active loans and unpaid fines from returned books)
    - **active_overdue_loans**: Number of currently overdue active loans
    - **unpaid_returned_fines**: Total fines from returned books that haven't been paid

    Fine calculation:
    - $0.50 per day overdue for active loans
    - Includes fine_amount from returned books (if not paid)
    """
    # Check if member exists
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get all loans for the member
    all_loans = db.query(Loan).filter(Loan.member_id == member_id).all()

    total_fines = 0.0
    active_overdue_loans = 0
    unpaid_returned_fines = 0.0
    today = date.today()

    for loan in all_loans:
        # Active loans that are overdue
        if loan.returned_date is None and loan.due_date < today:
            overdue_days = (today - loan.due_date).days
            total_fines += overdue_days * 0.50
            active_overdue_loans += 1
        # Returned books with unpaid fines
        elif loan.returned_date and loan.fine_amount:
            total_fines += loan.fine_amount
            unpaid_returned_fines += loan.fine_amount

    return {
        "member_id": member_id,
        "total_fines": round(total_fines, 2),
        "active_overdue_loans": active_overdue_loans,
        "unpaid_returned_fines": round(unpaid_returned_fines, 2)
    }
