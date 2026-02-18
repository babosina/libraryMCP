from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models import Book
from ..schemas import BookCreate, BookUpdate, BookResponse

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("/", response_model=list[BookResponse])
def list_books(
        title: Optional[str] = Query(None, description="Filter by book title (partial match)"),
        author: Optional[str] = Query(None, description="Filter by author name (partial match)"),
        genre: Optional[str] = Query(None, description="Filter by genre (partial match)"),
        available_only: bool = Query(False, description="Show only books with available copies"),
        db: Session = Depends(get_db)
):
    """
    List all books with optional filters.

    - **title**: Filter books by title (case-insensitive partial match)
    - **author**: Filter books by author (case-insensitive partial match)
    - **genre**: Filter books by genre (case-insensitive partial match)
    - **available_only**: If True, only return books with available_copies > 0
    """
    query = db.query(Book)

    # Apply filters conditionally
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))

    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))

    if genre:
        query = query.filter(Book.genre.ilike(f"%{genre}%"))

    if available_only:
        query = query.filter(Book.available_copies > 0)

    books = query.all()
    return books
