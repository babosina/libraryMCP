"""
Main entry point for the LibraryMCP FastAPI application.
Initializes the database, sets up middleware, and includes all routers.
"""

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import get_current_user
from backend.database import engine, Base
from backend.routers import books, members, loans
from backend.routers import auth as auth_router

app = FastAPI(title="LibraryMCP")

# Create database tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router is public (no token required to log in)
app.include_router(auth_router.router)

# All other routers require a valid JWT bearer token
_auth = [Depends(get_current_user)]
app.include_router(books.router, dependencies=_auth)
app.include_router(members.router, dependencies=_auth)
app.include_router(loans.router, dependencies=_auth)
