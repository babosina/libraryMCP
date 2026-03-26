# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
uv sync
```

**Run the server:**
```bash
uv run uvicorn backend.main:app --reload
```

**Seed the database with sample data:**
```bash
uv run python backend/seed.py
```

There is no test suite configured. API endpoints can be tested via:
- Swagger UI at `http://127.0.0.1:8000/docs` when server is running
- `LibraryMCP.postman_collection.json` (import into Postman)
- `test_main.http` (REST client file)

## Architecture

The backend follows a four-layer architecture:

1. **Routers** (`backend/routers/`): HTTP handlers for books, members, and loans. Each router enforces business rules (e.g., blocking deletion when active loans exist, preventing duplicate borrows) before delegating to CRUD.

2. **CRUD** (`backend/crud.py`): All database queries and write operations. Contains fine calculation logic ($0.50/day overdue). This is the single place for data access—routers never query the DB directly.

3. **Models** (`backend/models.py`): SQLAlchemy ORM models: `Book`, `Member`, `Loan`. `Loan` has FK relationships to both `Book` and `Member`. `Book.available_copies` is decremented/incremented on borrow/return.

4. **Schemas** (`backend/schemas.py`): Pydantic models for request/response validation. Email validation uses a regex pattern defined here.

**Database** (`backend/database.py`): SQLAlchemy session factory with FastAPI dependency injection (`get_db`). SQLite file (`library.db`) is auto-created on startup via `Base.metadata.create_all()` in `main.py`.

**Key business rules enforced in routers:**
- Books cannot be deleted if they have active loans
- Members cannot be deactivated or deleted if they have active loans or unpaid fines
- A member cannot borrow the same book twice simultaneously
- Fine rate: $0.50/day for overdue loans (calculated in `crud.py`)

**Frontend** (`frontend/index.html`): Minimal vanilla JS/HTML demo page; not the primary interface. Backend runs at `http://localhost:8000` with CORS open to all origins.