import uvicorn
from fastapi import FastAPI
from backend.database import engine, Base
from backend.models import Book, Member, Loan
from backend.routers import books, members, loans

app = FastAPI(title="LibraryMCP")

Base.metadata.create_all(bind=engine)

app.include_router(books.router)
app.include_router(members.router)
app.include_router(loans.router)
