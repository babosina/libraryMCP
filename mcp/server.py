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