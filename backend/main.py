import uvicorn
from fastapi import FastAPI
from backend.database import engine, Base
from backend.models import Book, Member, Loan
from backend.routers import books, members, loans
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LibraryMCP")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router)
app.include_router(members.router)
app.include_router(loans.router)
