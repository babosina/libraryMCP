from typing import Optional

from mcp.server.fastmcp import FastMCP

from backend.crud import get_books
from backend.database import SessionLocal

mcp = FastMCP()


@mcp.tool(name="search_books",
          description="Searches for books in the library by title, author, or genre. "
                      "Returns matching books with their availability status.")
def search_books(
        title: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        available_only: bool = False,
) -> str:
    db = SessionLocal()
    try:
        books = get_books(db, title=title, author=author, genre=genre, available_only=available_only)
    finally:
        db.close()

    if not books:
        return "No books found matching the search criteria."

    lines = []
    for book in books:
        availability = f"{book.available_copies}/{book.total_copies} copies available"
        genre_str = f", Genre: {book.genre}" if book.genre else ""
        lines.append(
            f"[ID: {book.id}] {book.title} by {book.author} | ISBN: {book.isbn}{genre_str} | {availability}"
        )
    return "\n".join(lines)