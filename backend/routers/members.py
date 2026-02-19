from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Optional, List, Any
from datetime import date

from ..database import get_db
from ..models import Member, Loan
from ..schemas import MemberCreate, MemberResponse, MemberUpdate, LoanResponse

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("/", response_model=List[MemberResponse])
def list_members(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
        name: Optional[str] = Query(None, description="Filter by name (partial match)"),
        email: Optional[str] = Query(None, description="Filter by email (partial match)"),
        is_active: Optional[bool] = Query(None, description="Filter by active status"),
        db: Session = Depends(get_db)
):
    """List all members with optional filters

    - **skip**: Number of records to skip for pagination
    - **limit**: Maximum number of records to return (1-500)
    - **name**: Filter by member name (case-insensitive partial match)
    - **email**: Filter by email address (case-insensitive partial match)
    - **is_active**: Filter by active status (true/false)

    Note: This endpoint returns basic member info without loan history for performance.
    Use GET /members/{id} to get detailed information with loans and fines.
    """
    query = db.query(Member)

    if name:
        query = query.filter(Member.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(Member.email.ilike(f"%{email}%"))
    if is_active is not None:
        query = query.filter(Member.is_active == is_active)

    members = query.offset(skip).limit(limit).all()
    return members


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def register_member(member: MemberCreate, db: Session = Depends(get_db)):
    """Creates a new member

    - **name**: The name of the member.
    - **email**: The email address of the member (must be valid format).
    - **joined_date**: The date the member joined. Defaults to today's date.
    - **is_active**: Whether the member is active. Defaults to True.
    """

    # Check if the member already exists
    existing_member = db.query(Member).filter(Member.email == member.email).first()
    if existing_member:
        raise HTTPException(
            status_code=409,
            detail=f"Member with email {member.email} already exists"
        )

    new_member = Member(**member.model_dump())
    try:
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        return new_member
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Database constraint violation. {e}")


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    """Returns a member by ID with complete loan history and fines

    - **member_id**: The unique identifier of the member to retrieve.

    Returns:
    - Member profile
    - All loans (active and historical)
    - Active loans count
    - Total outstanding fines
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get all loans for this member
    loans = db.query(Loan).filter(Loan.member_id == member_id).all()
    loan_responses = [LoanResponse.model_validate(loan) for loan in loans]

    # Calculate active loans count
    active_loans_count = db.query(func.count(Loan.id)).filter(
        Loan.member_id == member_id,
        Loan.returned_date == None
    ).scalar()

    total_fines = calculate_member_fines(loans)

    # Build response with optional fields populated
    return MemberResponse(
        id=member.id,
        name=member.name,
        email=member.email,
        joined_date=member.joined_date,
        is_active=member.is_active,
        loans=loan_responses,
        active_loans_count=active_loans_count or 0,
        total_fines=round(total_fines, 2)
    )


def calculate_member_fines(loans: list[Any]) -> float:
    # Calculate total fines from unreturned loans
    total_fines = 0.0
    today = date.today()

    for loan in loans:
        if loan.returned_date is None and loan.due_date < today:
            # Calculate overdue days and fine ($0.50 per day)
            overdue_days = (today - loan.due_date).days
            total_fines += overdue_days * 0.50
        elif loan.returned_date and loan.fine_amount:
            # Add existing unpaid fines from returned books
            total_fines += loan.fine_amount
    return total_fines


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(
        member_id: int,
        member_update: MemberUpdate,
        db: Session = Depends(get_db)
):
    """Update member information

    - **member_id**: The unique identifier of the member to update.
    - **name**: New name (optional)
    - **email**: New email (optional, must be valid and unique)
    - **is_active**: New active status (optional)

    Business rules:
    - Cannot deactivate member with active loans
    - Email must be unique if changed
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # If trying to deactivate, check for active loans
    if member_update.is_active is False and member.is_active:
        active_loans_count = db.query(func.count(Loan.id)).filter(
            Loan.member_id == member_id,
            Loan.returned_date == None
        ).scalar()

        if active_loans_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deactivate member with {active_loans_count} active loan(s). Please return all books first."
            )

    # Check email uniqueness if being changed
    if member_update.email and member_update.email != member.email:
        existing_member = db.query(Member).filter(Member.email == member_update.email).first()
        if existing_member:
            raise HTTPException(
                status_code=409,
                detail=f"Member with email {member_update.email} already exists"
            )

    # Update fields
    update_data = member_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    try:
        db.commit()
        db.refresh(member)
        return member
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Database constraint violation. {e}")


@router.delete("/{member_id}", status_code=status.HTTP_200_OK)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    """Deletes a member by ID

    - **member_id**: The unique identifier of the member to delete.

    Business rules:
    - Cannot delete member with active loans
    - Cannot delete member with unpaid fines
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Check for active loans (using count for proper validation)
    active_loans_count = db.query(func.count(Loan.id)).filter(
        Loan.member_id == member_id,
        Loan.returned_date == None
    ).scalar()

    if active_loans_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete member with {active_loans_count} active loan(s). Please return all books first."
        )

    # Check for unpaid fines
    all_loans = db.query(Loan).filter(Loan.member_id == member_id).all()
    total_fines = calculate_member_fines(all_loans)

    if total_fines > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete member with unpaid fines of ${total_fines:.2f}. Please clear all fines first."
        )

    try:
        db.delete(member)
        db.commit()
        return {"message": "Member deleted successfully", "member_id": member_id}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Database constraint violation. {e}")
