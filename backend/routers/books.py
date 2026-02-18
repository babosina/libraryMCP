from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional

from sqlalchemy.sql.coercions import expect

from ..database import get_db
from ..models import Book, Loan
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


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a book by its ID.

    - **book_id**: The unique identifier of the book to retrieve.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
        book: BookCreate,
        db: Session = Depends(get_db)
):
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
    # Check if the book with same ISBN already exists
    existing_book = db.query(Book).filter(Book.isbn == book.isbn).first()
    if existing_book:
        raise HTTPException(status_code=409,
                            detail=f"Book with ISBN {book.isbn} already exists"
                            )

    # Create a new book
    # Set available_copies equal to total_copies initially
    new_book = Book(
        **book.model_dump(),
        available_copies=book.total_copies
    )

    try:
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return new_book
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database constraint violation. {e}"
        )


@router.put("/{book_id}", response_model=BookResponse,
            status_code=status.HTTP_200_OK)
def update_book(book_id: int,
                book_update: BookUpdate,
                db: Session = Depends(get_db)):
    """
    Update an existing book in the database by book_id.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    update_data = book_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)
    try:
        db.commit()
        db.refresh(book)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database constraint violation. {e}")
    return book


@router.delete("/{book_id}",
               status_code=status.HTTP_200_OK)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """
    Delete a book from the database by book_id.
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Book with ID {book_id} not found")

    active_loans = db.query(Loan).filter(
        Loan.book_id == book_id,
        Loan.returned_date.is_(None)
    ).count()

    if active_loans > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Cannot delete book with active loans")

    try:
        db.delete(book)
        db.commit()
        return {
            "message": "Book deleted successfully"
        }
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Database constraint violation. {e}")
