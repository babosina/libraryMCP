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


@mcp.tool(name="list_members",
          description="Lists all library members with optional filters by name, email, or active status.")
def list_members(
        name: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
) -> str:
    params: dict = {}
    if name:
        params["name"] = name
    if email:
        params["email"] = email
    if is_active is not None:
        params["is_active"] = is_active

    response = httpx.get(f"{BACKEND_URL}/members/", params=params)
    response.raise_for_status()
    members = response.json()

    if not members:
        return "No members found matching the criteria."

    lines = []
    for m in members:
        status = "Active" if m["is_active"] else "Inactive"
        lines.append(
            f"[ID: {m['id']}] {m['name']} | Email: {m['email']} | Joined: {m['joined_date']} | {status}"
        )
    return "\n".join(lines)


@mcp.tool(name="register_member",
          description="Registers a new library member with a name and email address. Email must be unique.")
def register_member(name: str, email: str) -> str:
    payload = {"name": name, "email": email}
    response = httpx.post(f"{BACKEND_URL}/members/", json=payload)
    if response.status_code == 409:
        return f"A member with email {email} already exists."
    if response.status_code == 422:
        detail = response.json().get("detail", "Invalid input")
        return f"Registration failed: {detail}"
    response.raise_for_status()
    member = response.json()
    return (
        f"Member registered successfully.\n"
        f"ID: {member['id']} | Name: {member['name']} | Email: {member['email']} | "
        f"Joined: {member['joined_date']} | Active: {member['is_active']}"
    )


@mcp.tool(name="get_member",
          description="Retrieves a member's profile, loan history, and outstanding fines by member ID.")
def get_member(member_id: int) -> str:
    response = httpx.get(f"{BACKEND_URL}/members/{member_id}")
    if response.status_code == 404:
        return f"Member with ID {member_id} not found."
    response.raise_for_status()
    member = response.json()

    status_str = "Active" if member["is_active"] else "Inactive"
    lines = [
        f"ID: {member['id']}",
        f"Name: {member['name']}",
        f"Email: {member['email']}",
        f"Joined: {member['joined_date']}",
        f"Status: {status_str}",
        f"Active Loans: {member['active_loans_count']}",
        f"Outstanding Fines: ${member['total_fines']:.2f}",
    ]

    loans = member.get("loans", [])
    if loans:
        lines.append(f"\nLoan History ({len(loans)} record(s)):")
        for loan in loans:
            returned = loan.get("returned_date")
            loan_status = f"Returned: {returned}" if returned else "Active"
            fine_str = f" | Fine: ${loan['fine_amount']:.2f}" if loan.get("fine_amount") else ""
            lines.append(
                f"  - Book ID {loan['book_id']} | Borrowed: {loan['borrowed_date']} | "
                f"Due: {loan['due_date']} | {loan_status}{fine_str}"
            )

    return "\n".join(lines)


@mcp.tool(name="delete_member",
          description="Deletes a member account by member ID. Fails if the member has active loans or unpaid fines.")
def delete_member(member_id: int) -> str:
    response = httpx.delete(f"{BACKEND_URL}/members/{member_id}")
    if response.status_code == 404:
        return f"Member with ID {member_id} not found."
    if response.status_code == 400:
        return f"Cannot delete member: {response.json().get('detail', 'member has active loans or unpaid fines')}"
    response.raise_for_status()
    return f"Member with ID {member_id} deleted successfully."


@mcp.tool(name="borrow_book",
          description="Borrows a book for a member, creating a loan record. "
                      "Fails if the book has no available copies or the member already has an active loan for it.")
def borrow_book(member_id: int, book_id: int) -> str:
    payload = {"member_id": member_id, "book_id": book_id}
    response = httpx.post(f"{BACKEND_URL}/loans/borrow", json=payload)
    if response.status_code == 404:
        return f"Not found: {response.json().get('detail', 'member or book not found')}"
    if response.status_code == 400:
        return f"Cannot borrow: {response.json().get('detail', 'member account is not active')}"
    if response.status_code == 409:
        return f"Cannot borrow: {response.json().get('detail', 'conflict')}"
    response.raise_for_status()
    loan = response.json()
    return (
        f"Book borrowed successfully.\n"
        f"Loan ID: {loan['id']} | Member ID: {loan['member_id']} | Book ID: {loan['book_id']}\n"
        f"Borrowed: {loan['borrowed_date']} | Due: {loan['due_date']}"
    )


@mcp.tool(name="return_book",
          description="Returns a borrowed book for a member, closing the loan and calculating any overdue fines "
                      "($0.50/day). Fails if no active loan exists for the member and book.")
def return_book(member_id: int, book_id: int) -> str:
    payload = {"member_id": member_id, "book_id": book_id}
    response = httpx.post(f"{BACKEND_URL}/loans/return", json=payload)
    if response.status_code == 400:
        return f"Cannot return: {response.json().get('detail', 'no active loan found')}"
    response.raise_for_status()
    loan = response.json()
    fine_str = f"\nFine: ${loan['fine_amount']:.2f}" if loan.get("fine_amount") else "\nNo fine."
    return (
        f"Book returned successfully.\n"
        f"Loan ID: {loan['id']} | Member ID: {loan['member_id']} | Book ID: {loan['book_id']}\n"
        f"Borrowed: {loan['borrowed_date']} | Due: {loan['due_date']} | Returned: {loan['returned_date']}"
        f"{fine_str}"
    )


@mcp.tool(name="get_loans",
          description="Lists all active (not yet returned) loans for a member by member ID.")
def get_loans(member_id: int) -> str:
    response = httpx.get(f"{BACKEND_URL}/loans/{member_id}")
    if response.status_code == 404:
        return f"Member with ID {member_id} not found."
    response.raise_for_status()
    loans = response.json()

    if not loans:
        return f"Member {member_id} has no active loans."

    lines = [f"Active loans for member {member_id} ({len(loans)} loan(s)):"]
    for loan in loans:
        lines.append(
            f"  - Loan ID: {loan['id']} | Book ID: {loan['book_id']} | "
            f"Borrowed: {loan['borrowed_date']} | Due: {loan['due_date']}"
        )
    return "\n".join(lines)


@mcp.tool(name="check_fines",
          description="Returns the total outstanding fines for a member, including overdue active loans "
                      "and unpaid fines from returned books.")
def check_fines(member_id: int) -> str:
    response = httpx.get(f"{BACKEND_URL}/loans/{member_id}/fines")
    if response.status_code == 404:
        return f"Member with ID {member_id} not found."
    response.raise_for_status()
    data = response.json()
    return (
        f"Fines for member {member_id}:\n"
        f"Total outstanding fines: ${data['total_fines']:.2f}\n"
        f"Active overdue loans: {data['active_overdue_loans']}\n"
        f"Unpaid fines from returned books: ${data['unpaid_returned_fines']:.2f}"
    )
