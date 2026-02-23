from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List

from ..database import get_db
from ..schemas import MemberCreate, MemberResponse, MemberUpdate, LoanResponse
from .. import crud

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
    return crud.get_members(db, skip=skip, limit=limit, name=name, email=email, is_active=is_active)


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def register_member(member: MemberCreate, db: Session = Depends(get_db)):
    """Creates a new member

    - **name**: The name of the member.
    - **email**: The email address of the member (must be valid format).
    - **joined_date**: The date the member joined. Defaults to today's date.
    - **is_active**: Whether the member is active. Defaults to True.
    """
    if crud.get_member_by_email(db, member.email):
        raise HTTPException(status_code=409, detail=f"Member with email {member.email} already exists")
    try:
        return crud.create_member(db, member)
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
    member = crud.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    loans = crud.get_member_loans(db, member_id)
    loan_responses = [LoanResponse.model_validate(loan) for loan in loans]
    active_loans_count = crud.count_active_loans_for_member(db, member_id)
    total_fines = crud.calculate_member_fines(loans)

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
    member = crud.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member_update.is_active is False and member.is_active:
        active_loans_count = crud.count_active_loans_for_member(db, member_id)
        if active_loans_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deactivate member with {active_loans_count} active loan(s). Please return all books first."
            )

    if member_update.email and member_update.email != member.email:
        if crud.get_member_by_email(db, member_update.email):
            raise HTTPException(status_code=409, detail=f"Member with email {member_update.email} already exists")

    try:
        return crud.update_member(db, member, member_update.model_dump(exclude_unset=True))
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
    member = crud.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    active_loans_count = crud.count_active_loans_for_member(db, member_id)
    if active_loans_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete member with {active_loans_count} active loan(s). Please return all books first."
        )

    all_loans = crud.get_member_loans(db, member_id)
    total_fines = crud.calculate_member_fines(all_loans)
    if total_fines > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete member with unpaid fines of ${total_fines:.2f}. Please clear all fines first."
        )

    try:
        crud.delete_member(db, member)
        return {"message": "Member deleted successfully", "member_id": member_id}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Database constraint violation. {e}")
