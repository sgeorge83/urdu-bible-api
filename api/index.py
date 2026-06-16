from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from flask import Flask, abort, jsonify, request

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


app = Flask(__name__)
_bible: BibleData | None = None


def get_bible() -> BibleData:
    global _bible
    if _bible is None:
        _bible = BibleData()
    return _bible


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.get("/favicon.ico")
def favicon():
    return ("", 204)


@app.get("/")
def root():
    bible = get_bible()
    return jsonify(
        {
            "name": "Urdu Bible API",
            "translation": bible.metadata.get("name"),
            "module": bible.metadata.get("module"),
            "data_source": bible.base_url,
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/info")
def info():
    return jsonify(get_bible().metadata)


@app.get("/books")
def list_books():
    return jsonify(get_bible().list_books())


@app.get("/books/<int:book_id>")
def get_book(book_id: int):
    book = get_bible().get_book(book_id)
    if book is None:
        abort(404, description="Book not found")
    return jsonify(book)


@app.get("/books/<int:book_id>/chapters/<int:chapter>")
def get_chapter(book_id: int, chapter: int):
    chapter_data = get_bible().get_chapter(book_id, chapter)
    if chapter_data is None:
        abort(404, description="Chapter not found")
    return jsonify(chapter_data)


@app.get("/books/<int:book_id>/chapters/<int:chapter>/verses/<int:verse>")
def get_verse(book_id: int, chapter: int, verse: int):
    verse_data = get_bible().get_verse(book_id, chapter, verse)
    if verse_data is None:
        abort(404, description="Verse not found")
    return jsonify(verse_data)


@app.get("/search")
def search():
    query = request.args.get("q", "").strip()
    book_raw = request.args.get("book")
    limit_raw = request.args.get("limit", "50")

    if not query:
        abort(400, description="Query parameter 'q' is required")
    if not book_raw:
        abort(400, description="Query parameter 'book' is required")

    try:
        book_id = int(book_raw)
        limit = int(limit_raw)
    except ValueError:
        abort(400, description="Invalid book or limit parameter")

    if book_id < 1 or book_id > 66:
        abort(400, description="Book must be between 1 and 66")
    if limit < 1 or limit > 200:
        abort(400, description="Limit must be between 1 and 200")

    results = get_bible().search(query, book_id=book_id, limit=limit)
    return jsonify(
        {
            "query": query,
            "book": book_id,
            "count": len(results),
            "results": results,
        }
    )
