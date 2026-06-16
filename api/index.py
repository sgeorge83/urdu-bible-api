from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_DATA_BASE_URL = (
    "https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main"
)

_json_cache: dict[str, Any] = {}


def _fetch_json(base_url: str, path: str) -> Any:
    cache_key = f"{base_url}/{path}"
    if cache_key in _json_cache:
        return _json_cache[cache_key]

    http_request = urllib.request.Request(
        cache_key,
        headers={"User-Agent": "urdu-bible-api/1.0"},
    )
    with urllib.request.urlopen(http_request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    _json_cache[cache_key] = payload
    return payload


class BibleData:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url or os.environ.get("BIBLE_DATA_BASE_URL", DEFAULT_DATA_BASE_URL)
        ).rstrip("/")
        self.metadata = _fetch_json(self.base_url, "metadata.json")
        self._books = {
            book["id"]: book for book in _fetch_json(self.base_url, "books.json")
        }

    def _fetch_chapter(self, book_id: int, chapter: int) -> dict | None:
        try:
            return _fetch_json(self.base_url, f"chapters/{book_id}/{chapter}.json")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise

    def list_books(self) -> list[dict]:
        return [self._books[book_id] for book_id in sorted(self._books)]

    def get_book(self, book_id: int) -> dict | None:
        return self._books.get(book_id)

    def get_chapter(self, book_id: int, chapter: int) -> dict | None:
        if book_id not in self._books:
            return None
        return self._fetch_chapter(book_id, chapter)

    def get_verse(self, book_id: int, chapter: int, verse: int) -> dict | None:
        chapter_data = self.get_chapter(book_id, chapter)
        if chapter_data is None:
            return None

        for item in chapter_data["verses"]:
            if item["verse"] == verse:
                return item
        return None

    def search(self, query: str, book_id: int, limit: int = 50) -> list[dict]:
        book = self.get_book(book_id)
        if book is None:
            return []

        results: list[dict] = []
        for chapter_num in range(1, book["chapter_count"] + 1):
            chapter_data = self.get_chapter(book_id, chapter_num)
            if chapter_data is None:
                continue

            for item in chapter_data["verses"]:
                if query in item["text"]:
                    results.append(item)
                    if len(results) >= limit:
                        return results

        return results


_bible: BibleData | None = None


def get_bible() -> BibleData:
    global _bible
    if _bible is None:
        _bible = BibleData()
    return _bible


def _json_response(http_handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_handler.send_response(status)
    http_handler.send_header("Content-Type", "application/json; charset=utf-8")
    http_handler.send_header("Access-Control-Allow-Origin", "*")
    http_handler.send_header("Content-Length", str(len(body)))
    http_handler.end_headers()
    http_handler.wfile.write(body)


def _empty_response(http_handler: BaseHTTPRequestHandler, status: int = 204) -> None:
    http_handler.send_response(status)
    http_handler.send_header("Access-Control-Allow-Origin", "*")
    http_handler.end_headers()


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        for prefix in ("/api/index", "/api"):
            if path.startswith(prefix):
                path = path[len(prefix):] or "/"
                break

        query = parse_qs(parsed.query)

        try:
            if path == "/favicon.ico":
                return _empty_response(self, 204)

            if path == "/health":
                return _json_response(self, 200, {"status": "ok"})

            if path == "/":
                bible = get_bible()
                return _json_response(
                    self,
                    200,
                    {
                        "name": "Urdu Bible API",
                        "translation": bible.metadata.get("name"),
                        "module": bible.metadata.get("module"),
                        "data_source": bible.base_url,
                    },
                )

            if path == "/info":
                return _json_response(self, 200, get_bible().metadata)

            if path == "/books":
                return _json_response(self, 200, get_bible().list_books())

            parts = [part for part in path.split("/") if part]

            if len(parts) == 2 and parts[0] == "books" and parts[1].isdigit():
                book = get_bible().get_book(int(parts[1]))
                if book is None:
                    return _json_response(self, 404, {"error": "Book not found"})
                return _json_response(self, 200, book)

            if (
                len(parts) == 4
                and parts[0] == "books"
                and parts[2] == "chapters"
                and parts[1].isdigit()
                and parts[3].isdigit()
            ):
                chapter_data = get_bible().get_chapter(int(parts[1]), int(parts[3]))
                if chapter_data is None:
                    return _json_response(self, 404, {"error": "Chapter not found"})
                return _json_response(self, 200, chapter_data)

            if (
                len(parts) == 6
                and parts[0] == "books"
                and parts[2] == "chapters"
                and parts[4] == "verses"
                and all(part.isdigit() for part in (parts[1], parts[3], parts[5]))
            ):
                verse_data = get_bible().get_verse(
                    int(parts[1]), int(parts[3]), int(parts[5])
                )
                if verse_data is None:
                    return _json_response(self, 404, {"error": "Verse not found"})
                return _json_response(self, 200, verse_data)

            if path == "/search":
                q = query.get("q", [""])[0].strip()
                book_raw = query.get("book", [""])[0].strip()
                limit_raw = query.get("limit", ["50"])[0].strip()

                if not q or not book_raw:
                    return _json_response(
                        self,
                        400,
                        {"error": "Query parameters 'q' and 'book' are required"},
                    )

                book_id = int(book_raw)
                limit = int(limit_raw)
                if book_id < 1 or book_id > 66:
                    return _json_response(self, 400, {"error": "Book must be 1-66"})
                if limit < 1 or limit > 200:
                    return _json_response(self, 400, {"error": "Limit must be 1-200"})

                results = get_bible().search(q, book_id=book_id, limit=limit)
                return _json_response(
                    self,
                    200,
                    {"query": q, "book": book_id, "count": len(results), "results": results},
                )

            return _json_response(self, 404, {"error": "Not found"})
        except Exception as error:
            return _json_response(self, 500, {"error": str(error)})
