from database import SessionLocal, engine
from models import Book, Member, Loan, Base
from datetime import date, timedelta


def seed_database():
    """Seed the database with initial data"""

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(Book).count() > 0:
            print("Database already seeded. Skipping...")
            return

        # Seed Books
        books = [
            Book(
                title="The Great Gatsby",
                author="F. Scott Fitzgerald",
                isbn="978-0-7432-7356-5",
                total_copies=3,
                available_copies=3,
                genre="Fiction"
            ),
            Book(
                title="To Kill a Mockingbird",
                author="Harper Lee",
                isbn="978-0-06-112008-4",
                total_copies=2,
                available_copies=2,
                genre="Fiction"
            ),
            Book(
                title="1984",
                author="George Orwell",
                isbn="978-0-452-28423-4",
                total_copies=4,
                available_copies=3,
                genre="Dystopian"
            ),
            Book(
                title="Pride and Prejudice",
                author="Jane Austen",
                isbn="978-0-14-143951-8",
                total_copies=2,
                available_copies=2,
                genre="Romance"
            ),
            Book(
                title="The Catcher in the Rye",
                author="J.D. Salinger",
                isbn="978-0-316-76948-0",
                total_copies=3,
                available_copies=2,
                genre="Fiction"
            ),
        ]

        db.add_all(books)
        db.commit()
        print(f"Seeded {len(books)} books")

        # Seed Members
        members = [
            Member(
                name="Alice Johnson",
                email="alice.johnson@example.com",
                joined_date=date.today() - timedelta(days=180),
                is_active=True
            ),
            Member(
                name="Bob Smith",
                email="bob.smith@example.com",
                joined_date=date.today() - timedelta(days=90),
                is_active=True
            ),
            Member(
                name="Carol Williams",
                email="carol.williams@example.com",
                joined_date=date.today() - timedelta(days=60),
                is_active=True
            ),
            Member(
                name="David Brown",
                email="david.brown@example.com",
                joined_date=date.today() - timedelta(days=30),
                is_active=True
            ),
        ]

        db.add_all(members)
        db.commit()
        print(f"Seeded {len(members)} members")

        # Seed some active loans
        loans = [
            Loan(
                book_id=3,  # 1984
                member_id=1,  # Alice
                borrowed_date=date.today() - timedelta(days=5),
                due_date=date.today() + timedelta(days=9),
                returned_date=None,
                fine_amount=None
            ),
            Loan(
                book_id=5,  # The Catcher in the Rye
                member_id=2,  # Bob
                borrowed_date=date.today() - timedelta(days=3),
                due_date=date.today() + timedelta(days=11),
                returned_date=None,
                fine_amount=None
            ),
        ]

        db.add_all(loans)
        db.commit()
        print(f"Seeded {len(loans)} loans")

        print("Database seeding completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
