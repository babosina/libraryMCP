from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..schemas import BookCreate, BookUpdate, BookResponse
from .. import crud

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
    return crud.get_books(db, title=title, author=author, genre=genre, available_only=available_only)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a book by its ID.

    - **book_id**: The unique identifier of the book to retrieve.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    """
    Add a new book to the catalog

    - **title**: The title of the book
    - **author**: The author of the book
    - **isbn**: Unique ISBN identifier
    - **total_copies**: Total number of copies (defaults to 1)
    - **genre**: Optional genre classification

    Returns the created book with its assigned ID and available_copies set to total_copies.
    Raises 409 Error if a book with the same ISBN already exists.
    """
    if crud.get_book_by_isbn(db, book.isbn):
        raise HTTPException(status_code=409, detail=f"Book with ISBN {book.isbn} already exists")
    try:
        return crud.create_book(db, book)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database constraint violation. {e}")


@router.put("/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
def update_book(book_id: int, book_update: BookUpdate, db: Session = Depends(get_db)):
    """
    Update an existing book in the database by book_id.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        return crud.update_book(db, book, book_update.model_dump(exclude_unset=True))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database constraint violation. {e}")


@router.delete("/{book_id}", status_code=status.HTTP_200_OK)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """
    Delete a book from the database by book_id.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with ID {book_id} not found")

    if crud.count_active_loans_for_book(db, book_id) > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete book with active loans")

    try:
        crud.delete_book(db, book)
        return {"message": "Book deleted successfully"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database constraint violation. {e}")
