import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app


TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_book(client, **overrides):
    payload = {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "978-0000000000",
        "total_copies": 3,
        "genre": "Fiction",
    }
    payload.update(overrides)
    response = client.post("/books/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_member(client, **overrides):
    payload = {
        "name": "Test Member",
        "email": "test@example.com",
    }
    payload.update(overrides)
    response = client.post("/members/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_loan(client, member_id, book_id):
    response = client.post("/loans/borrow", json={"member_id": member_id, "book_id": book_id})
    assert response.status_code == 201, response.text
    return response.json()
