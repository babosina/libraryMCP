# Library Management System
## MCP Server Teaching Project
### Full Project Plan & Folder Structure

**Stack:** FastAPI · SQLite · Swagger UI · MCP Python SDK

## 1. Project Overview

This project builds a Library Management System as a teaching tool for QA Automation engineers learning MCP (Model Context Protocol) servers. The system consists of three independent components that share the same FastAPI backend.

The two components are:
- **FastAPI Backend** — the REST API that manages all business logic and the SQLite database. Swagger UI is included automatically at /docs — no extra frontend code required.
- **MCP Server** — exposes the same API as a set of tools that AI assistants (Claude, etc.) can call.

Key teaching points this project demonstrates:
- How an MCP server is just another API client — not magic, not special integration.
- How to map REST endpoints to MCP tools with proper input/output schemas.
- How Swagger UI allows full manual and exploratory testing of the API with zero frontend code.
- How to write QA tests for both the REST API and the MCP tool layer.
- Stateful workflow testing: a book cannot be borrowed twice, fines accumulate over time.

## 2. Architecture

Both components are independent processes. The Swagger UI is served directly by FastAPI at /docs and /redoc — it requires no separate server and no extra code. The MCP Server calls the same FastAPI backend over HTTP, making it a pure API consumer just like any other client.

### Architecture Diagram

```
┌──────────────────┐         ┌──────────────────┐
│                  │  built- │                  │
│   Swagger UI     │   in    │  FastAPI Backend │
│  (/docs, /redoc) │◀────────│  (port 8000)     │
└──────────────────┘         └────────┬─────────┘
                                      │
┌──────────────────┐         ┌────────▼─────────┐
│                  │  HTTP   │                  │
│   MCP Server     │────────▶│   SQLite DB      │
│  (stdio/SSE)     │         │   library.db     │
└──────────────────┘         └──────────────────┘
```

## 3. Folder Structure

The project is organized as a monorepo with three top-level folders, one per component. Each folder has its own requirements.txt and can be run independently.

| Path | Description |
|------|-------------|
| `library-mcp-project/` | Root project directory |
| `├── backend/` | FastAPI REST API application |
| `│   ├── main.py` | FastAPI app entry point (Swagger auto-enabled) |
| `│   ├── models.py` | SQLAlchemy ORM models (Book, Member, Loan) |
| `│   ├── schemas.py` | Pydantic request/response schemas |
| `│   ├── crud.py` | Database CRUD operations |
| `│   ├── database.py` | SQLite connection & session setup |
| `│   ├── routers/` | API route handlers grouped by domain |
| `│   │   ├── books.py` | Book endpoints (search, add, update, delete) |
| `│   │   ├── members.py` | Member endpoints (register, profile, delete) |
| `│   │   └── loans.py` | Loan endpoints (borrow, return, status, fines) |
| `│   ├── seed.py` | Script to populate DB with sample data |
| `│   ├── requirements.txt` | Python dependencies for the backend |
| `│   └── library.db` | SQLite database file (auto-generated) |
| `├── mcp_server/` | MCP server application |
| `│   ├── server.py` | MCP server entry point & tool definitions |
| `│   ├── tools/` | MCP tool implementations |
| `│   │   ├── book_tools.py` | Tools: search_books, get_book, add_book |
| `│   │   ├── member_tools.py` | Tools: register_member, get_member |
| `│   │   └── loan_tools.py` | Tools: borrow_book, return_book, check_fines |
| `│   ├── api_client.py` | Shared HTTP client to call FastAPI backend |
| `│   └── requirements.txt` | Python dependencies for the MCP server |
| `├── tests/` | QA test suites (for teaching) |
| `│   ├── test_books.py` | Unit & integration tests for book endpoints |
| `│   ├── test_loans.py` | Workflow tests for borrow/return/fines logic |
| `│   └── conftest.py` | Pytest fixtures and test DB setup |
| `├── .env` | Environment variables (API base URL, etc.) |
| `├── docker-compose.yml` | Optional: run backend & MCP server together |
| `└── README.md` | Setup instructions and project overview |

## 4. Database Models

The SQLite database has three tables. SQLAlchemy ORM is used in the backend; Pydantic schemas define the request/response shapes.

### 4.1 Book
- **id** — Integer, primary key, auto-increment
- **title** — String, required
- **author** — String, required
- **isbn** — String, unique
- **total_copies** — Integer, default 1
- **available_copies** — Integer, computed/tracked on borrow/return
- **genre** — String, optional

### 4.2 Member
- **id** — Integer, primary key, auto-increment
- **name** — String, required
- **email** — String, unique, required
- **joined_date** — Date, auto-set on creation
- **is_active** — Boolean, default True

### 4.3 Loan
- **id** — Integer, primary key, auto-increment
- **book_id** — ForeignKey → Book
- **member_id** — ForeignKey → Member
- **borrowed_date** — Date, auto-set on creation
- **due_date** — Date, borrowed_date + 14 days
- **returned_date** — Date, nullable (null = still borrowed)
- **fine_amount** — Float, calculated on return if overdue

## 5. API Endpoints & MCP Tool Mapping

Every FastAPI endpoint has a corresponding MCP tool. This 1-to-1 mapping is intentional — it makes the teaching comparison clear.

| Method | Endpoint | Description | MCP Tool |
|--------|----------|-------------|----------|
| GET | `/books` | List all books with filters | `search_books` |
| GET | `/books/{id}` | Get a single book by ID | `get_book` |
| POST | `/books` | Add a new book to catalog | `add_book` |
| PUT | `/books/{id}` | Update book information | `update_book` |
| DELETE | `/books/{id}` | Remove book from catalog | `delete_book` |
| POST | `/members` | Register a new member | `register_member` |
| GET | `/members/{id}` | Get member profile & history | `get_member` |
| DELETE | `/members/{id}` | Delete a member account | `delete_member` |
| POST | `/loans/borrow` | Borrow a book (creates loan) | `borrow_book` |
| POST | `/loans/return` | Return a borrowed book | `return_book` |
| GET | `/loans/{member_id}` | Get all active loans for a member | `get_loans` |
| GET | `/loans/{member_id}/fines` | Calculate overdue fines | `check_fines` |

### 5.1 Key Business Rules (Edge Cases for QA)
- A book with `available_copies = 0` cannot be borrowed → 409 Conflict
- A member cannot borrow the same book twice simultaneously → 409 Conflict
- Returning a book that isn't borrowed → 400 Bad Request
- Fine = $0.50 per day overdue, calculated at return time
- Deleting a member with active loans → 400 Bad Request (or cascade, your choice)
- ISBN must be unique → 422 Unprocessable Entity on duplicate

## 6. MCP Server Details

The MCP server is built with the official MCP Python SDK. It exposes tools that mirror the API endpoints. Each tool handles the HTTP call to FastAPI and formats the response for the AI assistant.

### 6.1 Tool Structure Pattern

Every tool follows the same pattern:
- Define the tool with `@mcp.tool()` decorator
- Accept typed input parameters
- Call the FastAPI backend via the shared `api_client`
- Return a structured string or dict result

### 6.2 MCP Tools List

#### Book Tools (book_tools.py)
- `search_books(query, genre, available_only)` — searches catalog with filters
- `get_book(book_id)` — retrieves full book details
- `add_book(title, author, isbn, copies, genre)` — adds a new book
- `update_book(book_id, ...)` — updates book metadata or copy count
- `delete_book(book_id)` — removes book from catalog

#### Member Tools (member_tools.py)
- `register_member(name, email)` — creates a new library member
- `get_member(member_id)` — gets member profile and loan history
- `delete_member(member_id)` — removes a member account

#### Loan Tools (loan_tools.py)
- `borrow_book(member_id, book_id)` — creates a loan record
- `return_book(member_id, book_id)` — closes the loan, calculates fines
- `get_loans(member_id)` — lists all active loans for a member
- `check_fines(member_id)` — returns total outstanding fines

## 7. Implementation Phases

The recommended build order ensures the backend is stable before the UI and MCP server are built on top of it.

| Phase | Name | Key Deliverables | Est. Time |
|-------|------|------------------|-----------|
| 1 | Backend — Core Setup | FastAPI app, SQLite DB, models, schemas | 1–2 hours |
| 2 | Backend — API Endpoints | All book, member & loan routes working | 2–3 hours |
| 3 | Backend — Business Logic | Availability checks, fine calculation, validations | 1–2 hours |
| 4 | Swagger UI — Verification | Schema tuning, descriptions, example values | 30–60 min |
| 5 | MCP Server — Tools | All MCP tools defined & connected to API | 2–3 hours |
| 6 | Testing & Polish | Test suite, seed data, README | 1–2 hours |

### 7.1 Phase 1 — Backend Core Setup
- Create the FastAPI project in the `backend/` folder
- Set up `database.py` with SQLite connection and session factory
- Define SQLAlchemy models in `models.py` (Book, Member, Loan)
- Define Pydantic schemas in `schemas.py` for all request/response shapes
- Verify the DB is created correctly on first run

### 7.2 Phase 2 — API Endpoints
- Implement books router with all 5 CRUD endpoints
- Implement members router with register, get, delete
- Implement loans router with borrow, return, list, fines
- Test all endpoints manually with FastAPI's built-in Swagger UI at `/docs`

### 7.3 Phase 3 — Business Logic
- Add availability check before allowing a borrow
- Add duplicate loan check per member
- Implement fine calculation (14-day loan period, $0.50/day overdue)
- Add `available_copies` increment/decrement on borrow/return

### 7.4 Phase 4 — Swagger UI Verification
- Start the backend and open http://localhost:8000/docs in the browser
- Verify all endpoints appear correctly with their expected request/response schemas
- Add `description=` parameters to FastAPI routes and Pydantic fields for cleaner docs
- Add example values to Pydantic schemas using `Field(example=...)` for better UX
- Use `/redoc` at http://localhost:8000/redoc as an alternative read-only API reference
- Run through the full borrow → return → fine workflow manually via Swagger to validate business logic

### 7.5 Phase 5 — MCP Server
- Install the MCP Python SDK (`pip install mcp`)
- Create `server.py` and register all tools
- Implement each tool in its respective `tools/` file
- Test by connecting the MCP server to Claude Desktop or a test client

### 7.6 Phase 6 — Testing & Polish
- Write pytest tests in `tests/` covering happy paths and edge cases
- Create a seed script to populate the DB with sample books and members
- Write the `README.md` with setup and run instructions
- Optional: add a `docker-compose.yml` to spin up backend and frontend together

## 8. Dependencies

### 8.1 Backend (backend/requirements.txt)
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

**Note:** Swagger UI (`/docs`) and ReDoc (`/redoc`) are bundled with FastAPI — no additional packages needed.

### 8.2 MCP Server (mcp_server/requirements.txt)
```
mcp>=1.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### 8.3 Tests (tests/)
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

## 9. Running the Project

### 9.1 Start the Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 9.2 Access Swagger UI
```
# Interactive API docs (Swagger UI)
http://localhost:8000/docs

# Alternative read-only reference (ReDoc)
http://localhost:8000/redoc
```

### 9.3 Start the MCP Server
```bash
cd mcp_server
pip install -r requirements.txt
python server.py
```

Swagger UI is available the moment the backend starts — no separate process, no extra configuration. Use it to manually explore and test every endpoint before connecting the MCP server.

---

Happy building! 🚀
