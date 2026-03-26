"""Level 4 — MCP tool tests for mcp_server/server.py.

Uses pytest-httpx to intercept outgoing httpx calls made by each tool
function and assert on the formatted string output.
"""

import re

import pytest

from mcp_server.server import search_books

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

BOOK_1 = {
    "id": 1,
    "title": "Clean Code",
    "author": "Robert Martin",
    "isbn": "9780132350884",
    "genre": "Programming",
    "available_copies": 2,
    "total_copies": 3,
}

BOOK_2 = {
    "id": 2,
    "title": "The Pragmatic Programmer",
    "author": "David Thomas",
    "isbn": "9780135957059",
    "genre": None,
    "available_copies": 1,
    "total_copies": 1,
}

BOOKS_URL = re.compile(r"http://localhost:8000/books/.*")


# ---------------------------------------------------------------------------
# search_books
# ---------------------------------------------------------------------------


class TestSearchBooks:
    def test_returns_formatted_list_single_book(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[BOOK_1])

        result = search_books(title="Clean")

        assert "[ID: 1] Clean Code by Robert Martin" in result
        assert "ISBN: 9780132350884" in result
        assert "Genre: Programming" in result
        assert "2/3 copies available" in result

    def test_returns_formatted_list_multiple_books(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[BOOK_1, BOOK_2])

        result = search_books()

        assert "[ID: 1] Clean Code by Robert Martin" in result
        assert "[ID: 2] The Pragmatic Programmer by David Thomas" in result
        assert result.count("\n") == 1

    def test_omits_genre_when_none(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[BOOK_2])

        result = search_books()

        assert "Genre:" not in result
        assert "[ID: 2] The Pragmatic Programmer by David Thomas" in result
        assert "1/1 copies available" in result

    def test_returns_no_books_message_on_empty_list(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[])

        result = search_books()

        assert result == "No books found matching the search criteria."

    def test_passes_title_param(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[BOOK_1])

        search_books(title="Clean")

        request = httpx_mock.get_request()
        assert "title=Clean" in str(request.url)

    def test_passes_author_param(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[BOOK_1])

        search_books(author="Martin")

        request = httpx_mock.get_request()
        assert "author=Martin" in str(request.url)

    def test_passes_genre_param(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[BOOK_1])

        search_books(genre="Programming")

        request = httpx_mock.get_request()
        assert "genre=Programming" in str(request.url)

    def test_passes_available_only_true_param(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[BOOK_1])

        search_books(available_only=True)

        request = httpx_mock.get_request()
        assert "available_only=true" in str(request.url)

    def test_available_only_defaults_to_false(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[])

        search_books()

        request = httpx_mock.get_request()
        assert "available_only=false" in str(request.url)

    def test_omits_none_params_from_request(self, httpx_mock):
        httpx_mock.add_response(method="GET", url=BOOKS_URL, json=[])

        search_books()

        request = httpx_mock.get_request()
        url = str(request.url)
        assert "title=" not in url
        assert "author=" not in url
        assert "genre=" not in url
