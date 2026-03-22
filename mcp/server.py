import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

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
    params: dict[str, str | bool] = {"available_only": available_only}
    if title:
        params["title"] = title
    if author:
        params["author"] = author
    if genre:
        params["genre"] = genre

    response = httpx.get(f"{BACKEND_URL}/books/", params=params)
    response.raise_for_status()
    books = response.json()

    if not books:
        return "No books found matching the search criteria."

    lines = []
    for book in books:
        availability = f"{book['available_copies']}/{book['total_copies']} copies available"
        genre_str = f", Genre: {book['genre']}" if book.get("genre") else ""
        lines.append(
            f"[ID: {book['id']}] {book['title']} by {book['author']} | ISBN: {book['isbn']}{genre_str} | {availability}"
        )
    return "\n".join(lines)


@mcp.tool(name="get_book",
          description="Retrieves full details of a single book by its ID.")
def get_book(book_id: int) -> str:
    response = httpx.get(f"{BACKEND_URL}/books/{book_id}")
    if response.status_code == 404:
        return f"Book with ID {book_id} not found."
    response.raise_for_status()
    book = response.json()

    availability = f"{book['available_copies']}/{book['total_copies']} copies available"
    genre_str = f"\nGenre: {book['genre']}" if book.get("genre") else ""
    return (
        f"ID: {book['id']}\n"
        f"Title: {book['title']}\n"
        f"Author: {book['author']}\n"
        f"ISBN: {book['isbn']}{genre_str}\n"
        f"Availability: {availability}"
    )


@mcp.tool(name="add_book",
          description="Adds a new book to the library catalog. ISBN must be unique.")
def add_book(
        title: str,
        author: str,
        isbn: str,
        total_copies: int = 1,
        genre: Optional[str] = None,
) -> str:
    payload: dict = {
        "title": title,
        "author": author,
        "isbn": isbn,
        "total_copies": total_copies,
    }
    if genre:
        payload["genre"] = genre

    response = httpx.post(f"{BACKEND_URL}/books/", json=payload)
    if response.status_code == 409:
        return f"A book with ISBN {isbn} already exists."
    response.raise_for_status()
    book = response.json()

    return (
        f"Book added successfully.\n"
        f"ID: {book['id']} | {book['title']} by {book['author']} | ISBN: {book['isbn']} | "
        f"Copies: {book['available_copies']}/{book['total_copies']}"
    )


@mcp.tool(name="update_book",
          description="Updates book metadata or copy count by book ID. Only provided fields are updated.")
def update_book(
        book_id: int,
        title: Optional[str] = None,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        total_copies: Optional[int] = None,
        available_copies: Optional[int] = None,
        genre: Optional[str] = None,
) -> str:
    payload: dict = {}
    if title is not None:
        payload["title"] = title
    if author is not None:
        payload["author"] = author
    if isbn is not None:
        payload["isbn"] = isbn
    if total_copies is not None:
        payload["total_copies"] = total_copies
    if available_copies is not None:
        payload["available_copies"] = available_copies
    if genre is not None:
        payload["genre"] = genre

    if not payload:
        return "No fields provided to update."

    response = httpx.put(f"{BACKEND_URL}/books/{book_id}", json=payload)
    if response.status_code == 404:
        return f"Book with ID {book_id} not found."
    if response.status_code == 409:
        return f"Update failed: {response.json().get('detail', 'conflict')}"
    response.raise_for_status()
    book = response.json()

    return (
        f"Book updated successfully.\n"
        f"ID: {book['id']} | {book['title']} by {book['author']} | ISBN: {book['isbn']} | "
        f"Copies: {book['available_copies']}/{book['total_copies']}"
    )


@mcp.tool(name="delete_book",
          description="Removes a book from the catalog by book ID. Fails if the book has active loans.")
def delete_book(book_id: int) -> str:
    response = httpx.delete(f"{BACKEND_URL}/books/{book_id}")
    if response.status_code == 404:
        return f"Book with ID {book_id} not found."
    if response.status_code == 400:
        return f"Cannot delete book: {response.json().get('detail', 'book has active loans')}"
    response.raise_for_status()
    return f"Book with ID {book_id} deleted successfully."