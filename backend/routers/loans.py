from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from ..database import get_db
from ..schemas import LoanCreate, LoanResponse
from .. import crud

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/borrow", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def borrow_book(loan: LoanCreate, db: Session = Depends(get_db)):
    """
    Borrow a book (creates a loan record).

    - **book_id**: The ID of the book to borrow
    - **member_id**: The ID of the member borrowing the book

    Business rules:
    - Book must exist and have available copies > 0
    - Member must exist and be active
    - Member cannot borrow the same book twice simultaneously
    """
    member = crud.get_member(db, loan.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if not member.is_active:
        raise HTTPException(status_code=400, detail="Member account is not active")

    book = crud.get_book(db, loan.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.available_copies <= 0:
        raise HTTPException(status_code=409, detail=f"Book '{book.title}' has no available copies")

    if crud.get_active_loan(db, loan.member_id, loan.book_id):
        raise HTTPException(status_code=409, detail="Member already has an active loan for this book")

    return crud.create_loan(db, book=book, member_id=loan.member_id)


@router.post("/return", response_model=LoanResponse)
def return_book(loan: LoanCreate, db: Session = Depends(get_db)):
    """
    Return a borrowed book.

    - **book_id**: The ID of the book being returned
    - **member_id**: The ID of the member returning the book

    Business rules:
    - Loan must exist and be active (not already returned)
    - Fine is calculated if book is overdue ($0.50 per day)
    - Book's available_copies is incremented
    """
    active_loan = crud.get_active_loan(db, loan.member_id, loan.book_id)
    if not active_loan:
        raise HTTPException(status_code=400, detail="No active loan found for this book and member")

    book = crud.get_book(db, loan.book_id)
    return crud.close_loan(db, active_loan, book)


@router.get("/{member_id}", response_model=List[LoanResponse])
def get_loans(member_id: int, db: Session = Depends(get_db)):
    """
    Get all active loans for a member.

    - **member_id**: The ID of the member

    Returns only loans where returned_date is NULL (active loans).
    """
    if not crud.get_member(db, member_id):
        raise HTTPException(status_code=404, detail="Member not found")
    return crud.get_active_loans_for_member(db, member_id)


@router.get("/{member_id}/fines", response_model=dict)
def check_fines(member_id: int, db: Session = Depends(get_db)):
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
    if not crud.get_member(db, member_id):
        raise HTTPException(status_code=404, detail="Member not found")

    all_loans = crud.get_member_loans(db, member_id)

    total_fines = 0.0
    active_overdue_loans = 0
    unpaid_returned_fines = 0.0
    today = date.today()

    for loan in all_loans:
        if loan.returned_date is None and loan.due_date < today:
            overdue_days = (today - loan.due_date).days
            total_fines += overdue_days * 0.50
            active_overdue_loans += 1
        elif loan.returned_date and loan.fine_amount:
            total_fines += loan.fine_amount
            unpaid_returned_fines += loan.fine_amount

    return {
        "member_id": member_id,
        "total_fines": round(total_fines, 2),
        "active_overdue_loans": active_overdue_loans,
        "unpaid_returned_fines": round(unpaid_returned_fines, 2)
    }
