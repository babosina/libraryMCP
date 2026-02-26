import pytest
from pydantic import ValidationError
from backend.schemas import BookCreate, MemberCreate, BookUpdate

# ========== BOOK SCHEMA TESTS ==========

def test_book_create_valid():
    """Test creating a BookCreate schema with valid data."""
    data = {
        "title": "1984",
        "author": "George Orwell",
        "isbn": "978-0451524935",
        "total_copies": 5,
        "genre": "Dystopian"
    }
    book = BookCreate(**data)
    assert book.title == "1984"
    assert book.total_copies == 5

def test_book_create_invalid_copies():
    """Test that total_copies must be at least 1."""
    data = {
        "title": "1984",
        "author": "George Orwell",
        "isbn": "978-0451524935",
        "total_copies": 0
    }
    with pytest.raises(ValidationError) as exc_info:
        BookCreate(**data)
    
    # Verify the error message for total_copies
    errors = exc_info.value.errors()
    assert any(error['loc'] == ('total_copies',) and error['type'] == 'greater_than_equal' for error in errors)

def test_book_update_optional_fields():
    """Test that BookUpdate fields are truly optional."""
    book_update = BookUpdate(title="New Title")
    assert book_update.title == "New Title"
    assert book_update.author is None
    assert book_update.isbn is None

# ========== MEMBER SCHEMA TESTS ==========

def test_member_create_valid_email():
    """Test creating a MemberCreate schema with a valid email."""
    data = {
        "name": "Bob Smith",
        "email": "bob@example.com"
    }
    member = MemberCreate(**data)
    assert member.email == "bob@example.com"

@pytest.mark.parametrize("invalid_email", [
    "plainaddress",
    "#@%^%#$@#$@#.com",
    "@example.com",
    "Joe Smith <email@example.com>",
    "email.example.com",
    "email@example@example.com",
    "あいうえお@example.com",
    "email@example.com (Joe Smith)",
    "email@example",
    "email@111.222.333.44444"
])
def test_member_create_invalid_email(invalid_email):
    """Test that invalid emails are caught by the field_validator."""
    data = {
        "name": "Bob Smith",
        "email": invalid_email
    }
    with pytest.raises(ValidationError) as exc_info:
        MemberCreate(**data)
    
    errors = exc_info.value.errors()
    assert any(error['loc'] == ('email',) and 'Invalid email address' in error['msg'] for error in errors)
