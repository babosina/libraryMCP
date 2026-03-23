import pytest
from datetime import date
from pydantic import ValidationError
from backend.schemas import BookCreate, MemberCreate, BookUpdate, MemberUpdate, LoanCreate, LoanResponse

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


# ========== MEMBER UPDATE SCHEMA TESTS ==========

def test_member_update_name_only():
    """Updating only name leaves email and is_active as None."""
    update = MemberUpdate(name="Alice")
    assert update.name == "Alice"
    assert update.email is None
    assert update.is_active is None


def test_member_update_invalid_email():
    """Invalid email in MemberUpdate raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        MemberUpdate(email="not-an-email")
    errors = exc_info.value.errors()
    assert any(error['loc'] == ('email',) and 'Invalid email address' in error['msg'] for error in errors)


def test_member_update_none_email_passes():
    """None email in MemberUpdate passes through without error."""
    update = MemberUpdate(email=None)
    assert update.email is None


# ========== LOAN CREATE SCHEMA TESTS ==========

def test_loan_create_valid():
    """Valid book_id and member_id creates schema correctly."""
    loan = LoanCreate(book_id=1, member_id=2)
    assert loan.book_id == 1
    assert loan.member_id == 2


def test_loan_create_missing_book_id():
    """Missing book_id raises ValidationError."""
    with pytest.raises(ValidationError):
        LoanCreate(member_id=1)


def test_loan_create_missing_member_id():
    """Missing member_id raises ValidationError."""
    with pytest.raises(ValidationError):
        LoanCreate(book_id=1)


# ========== LOAN RESPONSE SCHEMA TESTS ==========

def test_loan_response_optional_fields_default_to_none():
    """returned_date and fine_amount are optional and default to None."""
    loan = LoanResponse(
        id=1,
        book_id=1,
        member_id=2,
        borrowed_date=date(2026, 3, 1),
        due_date=date(2026, 3, 15),
    )
    assert loan.returned_date is None
    assert loan.fine_amount is None


def test_loan_response_from_attributes():
    """from_attributes=True allows construction from ORM-like attribute objects."""
    class FakeLoan:
        id = 10
        book_id = 3
        member_id = 4
        borrowed_date = date(2026, 3, 1)
        due_date = date(2026, 3, 15)
        returned_date = date(2026, 3, 14)
        fine_amount = 0.0

    loan = LoanResponse.model_validate(FakeLoan())
    assert loan.id == 10
    assert loan.returned_date == date(2026, 3, 14)
    assert loan.fine_amount == 0.0
