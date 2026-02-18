# LibraryMCP

LibraryMCP is a FastAPI-based backend server designed to serve as a Model Context Protocol (MCP) tool invocation source for library management. It provides a set of API endpoints to manage books, members, and loans in a library system.

## Features

- **Books Management**: List books with filtering by title, author, genre, and availability.
- **SQLite Database**: Lightweight storage using SQLAlchemy ORM.
- **FastAPI**: High-performance web framework for building APIs with Python.
- **Seeding Tool**: Built-in script to populate the database with initial sample data.

## Project Structure

```text
libraryMCP/
├── backend/                # Application source code
│   ├── routers/            # API route handlers
│   │   ├── books.py        # Book-related endpoints
│   │   ├── loans.py        # Loan-related endpoints (TODO)
│   │   └── members.py      # Member-related endpoints (TODO)
│   ├── crud.py             # CRUD operations
│   ├── database.py         # Database configuration and session management
│   ├── main.py             # FastAPI application entry point
│   ├── models.py           # SQLAlchemy database models
│   ├── schemas.py          # Pydantic models for request/response validation
│   └── seed.py             # Database seeding script
├── library.db              # SQLite database file
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

## Usage

### Running the Server

Start the FastAPI server using `uvicorn`:

```bash
uv run uvicorn backend.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Seeding the Database

To populate the database with sample data, run the seed script:

```bash
uv run python backend/seed.py
```

## API Endpoints Overview

### Books
- `GET /books/`: List all books.
  - Query Parameters: `title`, `author`, `genre`, `available_only`.

*Note: Loan and Member endpoints are currently under development.*

## License

[MIT License](LICENSE)
