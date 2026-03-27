# LibraryMCP

> **Demo project** — Intended for local development and learning purposes only. Do not expose it to the public internet or use it to store real data.

LibraryMCP is a FastAPI-based backend server designed to serve as a Model Context Protocol (MCP) tool invocation source for library management. It provides a set of API endpoints to manage books, members, and loans in a library system.

## Features

- **Books Management**: Full CRUD with filtering by title, author, genre, and availability.
- **Members Management**: Register, list (with filters), view details with loan history and fines, update, and delete with business rules.
- **Loans Management**: Borrow/return workflows, active loans listing, and fine calculations.
- **JWT Authentication**: All API endpoints (except `/auth/token`) require a Bearer token. Credentials are configurable via environment variables.
- **SQLite Database**: Lightweight storage using SQLAlchemy ORM.
- **FastAPI**: High-performance web framework for building APIs with Python.
- **CORS Enabled**: Open CORS for easy local development and browser demos.
- **Simple Frontend Demo**: Minimal HTML page to add/list books and members.
- **Seeding Tool**: Built-in script to populate the database with initial sample data.

## Project Structure

```text
libraryMCP/
├── backend/                # Application source code
│   ├── routers/            # API route handlers
│   │   ├── auth.py         # Authentication endpoint (token issuance)
│   │   ├── books.py        # Book-related endpoints
│   │   ├── loans.py        # Loan-related endpoints
│   │   └── members.py      # Member-related endpoints
│   ├── auth.py             # JWT creation, verification, and get_current_user dependency
│   ├── crud.py             # CRUD operations
│   ├── database.py         # Database configuration and session management
│   ├── main.py             # FastAPI application entry point (CORS + routers)
│   ├── models.py           # SQLAlchemy database models
│   ├── schemas.py          # Pydantic models for request/response validation
│   └── seed.py             # Database seeding script
├── frontend/
│   └── index.html          # Simple browser demo (books/members)
├── library.db              # SQLite database file
├── openapi.json            # Generated OpenAPI schema snapshot
├── pyproject.toml          # Project dependencies and configuration
├── uv.lock                 # Lock file for dependencies
└── README.md               # Project documentation
```

## Prerequisites

- [Python](https://www.python.org/downloads/) >= 3.13
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd libraryMCP
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure credentials in `.env` (copy from `.env` and fill in your values):
   ```
   ADMIN_USERNAME="admin"
   ADMIN_PASSWORD="your-password"
   SECRET_KEY="your-secret-key"
   BACKEND_URL=http://localhost:8000
   ```

## Usage

### Running the Server

Start the FastAPI server using `uvicorn`:

```bash
uv run uvicorn backend.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Authentication

All endpoints except `POST /auth/token` require a JWT Bearer token.

**Obtain a token:**
```bash
curl -X POST http://127.0.0.1:8000/auth/token \
  -d "username=admin&password=your-password"
```

Response:
```json
{ "access_token": "<token>", "token_type": "bearer" }
```

**Use the token:**
```bash
curl http://127.0.0.1:8000/books/ \
  -H "Authorization: Bearer <token>"
```

Tokens expire after 30 minutes. Configure credentials via `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `SECRET_KEY` environment variables (or in `.env`).

### API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — click **Authorize**, call `POST /auth/token` first to get a token, then paste it in the Bearer field
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) (a snapshot also lives at `openapi.json`)

### Seeding the Database

To populate the database with sample data, run the seed script:

```bash
uv run python backend/seed.py
```

### Simple Frontend Demo (optional)

You can interact with the API using a tiny frontend:

- Open `frontend/index.html` in your browser
- Ensure the backend runs at `http://localhost:8000` (CORS is enabled)
- Use the UI to add/list books and members

## MCP Server

The MCP server exposes the library's functionality as tools that AI assistants (Claude, etc.) can call directly.

### Running the MCP Server

The MCP server communicates over stdio. Start the FastAPI backend first, then run:

```bash
uv run python mcp_server/main_stdio.py
```

The server reads `BACKEND_URL`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` from the environment (or `.env`). It obtains a JWT token automatically on first use and refreshes it when it expires.

### Connecting to Claude Desktop

Add the following to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "library": {
      "command": "uv",
      "args": ["run", "python", "mcp_server/main_stdio.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/libraryMCP",
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "your-password"
      }
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `search_books` | Search books by title, author, or genre |
| `get_book` | Get full details of a book by ID |
| `add_book` | Add a new book to the catalog |
| `update_book` | Update book metadata or copy count |
| `delete_book` | Remove a book (blocked if active loans exist) |
| `list_members` | List members with optional filters |
| `register_member` | Register a new library member |
| `get_member` | Get member profile, loan history, and fines |
| `delete_member` | Delete a member (blocked if active loans or unpaid fines) |
| `borrow_book` | Borrow a book for a member |
| `return_book` | Return a borrowed book, calculating any overdue fine |
| `get_loans` | List all active loans for a member |
| `check_fines` | Get total outstanding fines for a member |

## API Endpoints Overview

### Authentication
- `POST /auth/token` — Obtain a JWT Bearer token (form fields: `username`, `password`).

### Books
- `GET /books/` — List books with optional filters.
  - Query: `title`, `author`, `genre`, `available_only`
- `GET /books/{id}` — Get a single book by ID.
- `POST /books/` — Create a book (initial `available_copies = total_copies`).
- `PUT /books/{id}` — Update a book.
- `DELETE /books/{id}` — Delete a book (blocked if there are active loans).

### Members
- `GET /members/` — List members with filters and pagination.
  - Query: `skip`, `limit`, `name`, `email`, `is_active`
- `GET /members/{id}` — Get member details with loan history, active loans count, and total fines.
- `POST /members/` — Register a new member (unique email required).
- `PUT /members/{id}` — Update member (cannot deactivate with active loans; email must be unique/valid).
- `DELETE /members/{id}` — Delete member (blocked if active loans or unpaid fines).

### Loans
- `POST /loans/borrow` — Borrow a book (member must be active; book must have available copies; no duplicate active loan).
- `POST /loans/return` — Return a book (increments availability; computes fine if overdue: $0.50/day).
- `GET /loans/{member_id}` — List active loans for a member.
- `GET /loans/{member_id}/fines` — Calculate and return fine breakdown for a member.
