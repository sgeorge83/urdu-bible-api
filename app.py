from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

DEFAULT_DATA_BASE_URL = (
    "https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main"
)
API_BASE_URL = os.environ.get(
    "API_PUBLIC_URL", "https://urdu-bible-api.vercel.app"
).rstrip("/")
API_DOCS_URL = f"{API_BASE_URL}/docs"

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


app = FastAPI(
    title="Urdu Bible API",
    description=(
        "REST API for the Urdu Geo Version Bible (کتابِ مقدس).\n\n"
        f"**Developer docs:** [{API_DOCS_URL}]({API_DOCS_URL})\n\n"
        "Use the interactive docs to explore endpoints, view schemas, "
        "and try requests directly in the browser."
    ),
    version="1.0.0",
    servers=[
        {"url": API_BASE_URL, "description": "Production"},
        {"url": "http://localhost:8000", "description": "Local development"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_bible: BibleData | None = None


def get_bible() -> BibleData:
    global _bible
    if _bible is None:
        _bible = BibleData()
    return _bible


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/")
def root() -> dict:
    bible = get_bible()
    return {
        "name": "Urdu Bible API",
        "translation": bible.metadata.get("name"),
        "module": bible.metadata.get("module"),
        "data_source": bible.base_url,
        "docs": API_DOCS_URL,
        "docs_path": "/docs",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/info")
def info() -> dict:
    return get_bible().metadata


@app.get("/books")
def list_books() -> list[dict]:
    return get_bible().list_books()


@app.get("/books/{book_id}")
def get_book(book_id: int) -> dict:
    book = get_bible().get_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.get("/books/{book_id}/chapters/{chapter}")
def get_chapter(book_id: int, chapter: int) -> dict:
    chapter_data = get_bible().get_chapter(book_id, chapter)
    if chapter_data is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter_data


@app.get("/books/{book_id}/chapters/{chapter}/verses/{verse}")
def get_verse(book_id: int, chapter: int, verse: int) -> dict:
    verse_data = get_bible().get_verse(book_id, chapter, verse)
    if verse_data is None:
        raise HTTPException(status_code=404, detail="Verse not found")
    return verse_data


@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Urdu text to search for"),
    book: int = Query(..., ge=1, le=66, description="Book ID to search within"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
) -> dict:
    results = get_bible().search(q, book_id=book, limit=limit)
    return {
        "query": q,
        "book": book,
        "count": len(results),
        "results": results,
    }
