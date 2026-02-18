import uvicorn
from fastapi import FastAPI
from backend.database import engine, Base
from backend.models import Book, Member, Loan
from backend.routers import books

app = FastAPI(title="LibraryMCP")

Base.metadata.create_all(bind=engine)

app.include_router(books.router)
