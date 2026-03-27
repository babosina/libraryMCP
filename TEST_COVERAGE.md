# Test Coverage Plan — LibraryMCP

This document defines a layered testing strategy from the lowest level (data validation, DB) up to the MCP tool layer. Each level builds on the previous one. Tests should be implemented in this order.

---

## What's Actually Missing for Phase 6

The `ProjectPlan.md` lists `tests/test_books.py`, `tests/test_loans.py`, and `tests/conftest.py` as the deliverables for Phase 6. Here is the full honest gap analysis:

| File | Status | Notes |
|------|--------|-------|
| `tests/conftest.py` | **Done** | In-memory SQLite engine, `db` fixture, `client` fixture with `get_db` override, `make_book`/`make_member`/`make_loan` factory helpers |
| `tests/test_schemas.py` | **Done** | All 22 tests pass — covers `BookCreate`, `BookUpdate`, `MemberCreate`, `MemberUpdate`, `LoanCreate`, `LoanResponse` |
| `tests/test_crud.py` | Missing | No unit tests for the CRUD/DB layer |
| `tests/test_books.py` | Missing | No API-level tests for any book endpoint |
| `tests/test_members.py` | Missing | Not in the plan, but members have the most complex business rules |
| `tests/test_loans.py` | Missing | No workflow tests for borrow/return/fines |
| `tests/test_mcp_tools.py` | Missing | Not in the plan, but it's the top-level goal of the whole project |

Two things the plan did not anticipate but are necessary:
- A `test_members.py` file — members have more business rules than books (deactivation guard, fines guard, email uniqueness)
- An MCP tool test file — the entire point of the project is teaching MCP, so the tools themselves need to be verified

One technical complication: `crud.close_loan` and `check_fines` in `routers/loans.py` both call `date.today()` internally. Fine calculation tests require mocking `date.today`, otherwise the test result depends on when the test runs.

---

## Test Infrastructure — `tests/conftest.py`

**Status: Complete.**

- `StaticPool` in-memory SQLite engine — isolated from `library.db`
- `db` fixture — function-scoped; creates all tables before each test, drops them after
- `client` fixture — `TestClient` with `get_db` overridden to use the test session
- Factory helpers: `make_book(client, **overrides)`, `make_member(client, **overrides)`, `make_loan(client, member_id, book_id)`

---

## Level 1 — Schema Unit Tests (`tests/test_schemas.py`)

**What's tested:** Pydantic model validation in isolation. No DB, no HTTP, no side effects.

**Status: Complete — 22 tests, all passing.**

- `BookCreate` — valid data, `total_copies < 1` rejected
- `BookUpdate` — optional fields are truly optional
- `MemberCreate` — valid email, 10 invalid email formats rejected
- `MemberUpdate` — name-only update, invalid email rejected, `None` email passes validator
- `LoanCreate` — valid creation, missing `book_id` rejected, missing `member_id` rejected
- `LoanResponse` — optional fields default to `None`, `from_attributes=True` works with ORM objects

---

## Level 2 — CRUD / DB Unit Tests (`tests/test_crud.py`)

**What's tested:** `crud.py` functions called directly against the in-memory DB. No HTTP, no routers, no business-rule guards — only the data access layer.

**Fixtures needed:** `db` session from `conftest.py`.

### Books
- `create_book` sets `available_copies = total_copies`
- `get_book` returns `None` for a non-existent ID
- `get_book_by_isbn` finds by exact ISBN; returns `None` for unknown ISBN
- `get_books` with `title` filter uses case-insensitive partial match
- `get_books` with `available_only=True` excludes books with `available_copies = 0`
- `update_book` persists only the fields passed in `update_data`
- `delete_book` removes the record; subsequent `get_book` returns `None`
- `count_active_loans_for_book` returns 0 when no loans exist

### Members
- `create_member` sets `joined_date` to today and `is_active = True` by default
- `get_member_by_email` is case-sensitive (important: the uniqueness constraint is on the raw value)
- `get_members` filters by partial name and email matches
- `get_members` filters by `is_active` correctly
- `count_active_loans_for_member` returns 0 for a new member
- `calculate_member_fines` with an empty loan list returns `0.0`
- `calculate_member_fines` with only on-time returned loans returns `0.0`
- `calculate_member_fines` with an overdue returned loan (non-zero `fine_amount`) returns that amount
- `calculate_member_fines` with an active overdue loan calculates `0.50 * overdue_days` — **requires mocking `date.today`**

### Loans
- `create_loan` decrements `book.available_copies` by 1 atomically
- `create_loan` sets `due_date = borrowed_date + 14 days`
- `get_active_loan` returns `None` after the loan is closed
- `get_active_loans_for_member` returns only loans with `returned_date = None`
- `close_loan` sets `returned_date` to today, increments `book.available_copies`, and sets `fine_amount = 0.0` when returned on time
- `close_loan` calculates `fine_amount = overdue_days * 0.50` when returned late — **requires mocking `date.today`**

---

## Level 3 — API Integration Tests

These tests call the FastAPI endpoints via `TestClient` and verify HTTP status codes, response bodies, and state changes in the DB. They use `client` and the factory fixtures.

### `tests/test_books.py`

**Happy paths:**
- `POST /books/` returns 201 and the created book; `available_copies` equals `total_copies`
- `GET /books/` returns a list that includes the created book
- `GET /books/?title=partial` returns only matching books
- `GET /books/?available_only=true` excludes books with `available_copies = 0`
- `GET /books/{id}` returns the full book record
- `PUT /books/{id}` with a new title updates only that field
- `DELETE /books/{id}` returns 200 and removes the book

**Error paths:**
- `POST /books/` with a duplicate ISBN returns 409
- `GET /books/{id}` with a non-existent ID returns 404
- `PUT /books/{id}` with a non-existent ID returns 404
- `PUT /books/{id}` with a duplicate ISBN returns 409
- `DELETE /books/{id}` with a non-existent ID returns 404
- `DELETE /books/{id}` when the book has an active loan returns 400

### `tests/test_members.py`

**Happy paths:**
- `POST /members/` returns 201 with `is_active = True` and today's `joined_date`
- `GET /members/` lists all members; filters by `name`, `email`, `is_active` work
- `GET /members/{id}` includes `loans`, `active_loans_count`, and `total_fines` in the response
- `PUT /members/{id}` updates name only; `PUT /members/{id}` updates email only
- `DELETE /members/{id}` removes a member with no loans and no fines

**Error paths:**
- `POST /members/` with a duplicate email returns 409
- `POST /members/` with an invalid email format returns 422
- `GET /members/{id}` with a non-existent ID returns 404
- `PUT /members/{id}` with `is_active = false` while member has active loans returns 400
- `PUT /members/{id}` changing email to one already taken returns 409
- `DELETE /members/{id}` while member has an active loan returns 400
- `DELETE /members/{id}` while member has unpaid fines returns 400

### `tests/test_loans.py`

**Happy paths:**
- `POST /loans/borrow` creates a loan; `available_copies` decreases by 1
- `POST /loans/return` closes the loan; `available_copies` increases by 1; `fine_amount = 0` when on time
- `GET /loans/{member_id}` returns only active loans (returned loans are excluded)
- `GET /loans/{member_id}/fines` returns `total_fines = 0` for a member with no overdue loans
- Full happy-path workflow: borrow → return → confirm zero active loans

**Error paths (business rules):**
- Borrow with a non-existent member returns 404
- Borrow with a non-existent book returns 404
- Borrow for an inactive member returns 400
- Borrow when `available_copies = 0` returns 409
- Borrow the same book twice by the same member returns 409
- Return a book that was not borrowed returns 400
- Return a book that was already returned returns 400

**Fine calculation (requires mocking `date.today`):**
- Returning a book 3 days late produces `fine_amount = 1.50`
- Returning a book on the due date produces `fine_amount = 0.0`
- `GET /loans/{member_id}/fines` shows non-zero `total_fines` for an overdue active loan
- `GET /loans/{member_id}/fines` correctly separates `unpaid_returned_fines` from active overdue amounts

---

## Level 4 — MCP Tool Tests (`tests/test_mcp_tools.py`)

**What's tested:** The functions in `mcp_server/server.py` — the formatted string output and correct HTTP calls made to the backend. These are the top-level user-facing behaviors of the project.

**Approach:** The MCP tool functions make bare `httpx.get` / `httpx.post` calls. The cleanest way to test them is with [`pytest-httpx`](https://pypi.org/project/pytest-httpx/) (add to dev dependencies), which intercepts outgoing `httpx` requests and lets you return controlled responses. This keeps tests fast and independent of the backend being live.

An alternative is a full end-to-end approach: spin up the FastAPI `TestClient`, mount it behind a real HTTP server in the test session, point `BACKEND_URL` at it, and call the tool functions directly. This is slower but tests the full stack including serialization.

**New dependencies needed:** `pytest-httpx` (or `respx`) for request mocking.

### `search_books`
- Returns a formatted list when books are found
- Returns the "No books found" message when the API returns an empty list
- Passes `title`, `author`, `genre`, `available_only` as query params

### `get_book`
- Returns formatted book details on 200
- Returns the "not found" message on 404

### `add_book`
- Returns the success message with book details on 201
- Returns the "already exists" message on 409

### `update_book`
- Returns success message on 200
- Returns "not found" on 404
- Returns conflict message on 409
- Returns "No fields provided" when called with no optional arguments

### `delete_book`
- Returns success message on 200
- Returns "not found" on 404
- Returns "has active loans" message on 400

### `list_members`
- Returns formatted member list
- Returns "No members found" on empty list

### `register_member`
- Returns success message on 201
- Returns "already exists" on 409
- Returns validation error message on 422

### `get_member`
- Returns member profile with loan history section when loans exist
- Returns member profile without loan history section when no loans
- Returns "not found" on 404

### `delete_member`
- Returns success on 200
- Returns "not found" on 404
- Returns "has active loans or unpaid fines" on 400

### `borrow_book`
- Returns success message with loan ID and due date on 201
- Returns "not found" message on 404
- Returns "cannot borrow" message on 400 (inactive member)
- Returns "cannot borrow" message on 409 (no copies / duplicate loan)

### `return_book`
- Returns success with no fine when on time
- Returns success with fine amount when overdue
- Returns error on 400 (no active loan)

### `get_loans`
- Returns formatted active loans list
- Returns "no active loans" message when list is empty
- Returns "not found" on 404

### `check_fines`
- Returns correctly formatted fine breakdown on 200
- Returns "not found" on 404

---

## Suggested File Structure After Full Implementation

```
tests/
├── conftest.py          # DB engine, TestClient, factory fixtures
├── test_schemas.py      # Level 1 — schema validation (expand existing)
├── test_crud.py         # Level 2 — CRUD functions against in-memory DB
├── test_books.py        # Level 3 — /books/ API
├── test_members.py      # Level 3 — /members/ API
├── test_loans.py        # Level 3 — /loans/ API + fine calculation
└── test_mcp_tools.py    # Level 4 — MCP tool output and HTTP calls
```

## Summary of Additional Dependencies

| Package | Purpose | Required for |
|---------|---------|-------------|
| `pytest` | Test runner | All levels |
| `httpx` | FastAPI `TestClient` transport | Level 3 |
| `pytest-httpx` | Mock outgoing `httpx` calls | Level 4 |