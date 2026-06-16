from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_DATA_BASE_URL = (
    "https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main"
)

_json_cache: dict[str, Any] = {}


def _fetch_json(base_url: str, path: str) -> Any:
    cache_key = f"{base_url}/{path}"
    if cache_key in _json_cache:
        return _json_cache[cache_key]

    request = urllib.request.Request(
        cache_key,
        headers={"User-Agent": "urdu-bible-api/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
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
