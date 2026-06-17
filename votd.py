from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Protocol

from book_names import ENGLISH_BOOK_NAMES, english_book_to_id

VOTD_API_URL = "https://labs.bible.org/api/?passage=votd&type=json&formatting=plain"

_votd_cache: dict[str, Any] = {"date": None, "payload": None}


class BibleReader(Protocol):
    def get_book(self, book_id: int) -> dict | None: ...
    def get_verse(self, book_id: int, chapter: int, verse: int) -> dict | None: ...


def _fetch_url(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "urdu-bible-api/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_verse_numbers(raw_verse: str) -> list[int]:
    numbers: list[int] = []
    for part in raw_verse.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text.strip())
            end = int(end_text.strip())
            numbers.extend(range(start, end + 1))
        else:
            numbers.append(int(part))
    return numbers


def _format_reference(
    book_name_english: str, chapter: int, verse_numbers: list[int]
) -> str:
    if len(verse_numbers) == 1:
        return f"{book_name_english} {chapter}:{verse_numbers[0]}"

    if verse_numbers == list(range(verse_numbers[0], verse_numbers[-1] + 1)):
        return f"{book_name_english} {chapter}:{verse_numbers[0]}-{verse_numbers[-1]}"

    joined = ",".join(str(number) for number in verse_numbers)
    return f"{book_name_english} {chapter}:{joined}"


def _collect_votd_items(
    votd_payload: list[dict],
) -> tuple[str, int, int, list[int], list[dict]]:
    if not votd_payload:
        raise ValueError("Empty VOTD response from labs.bible.org")

    first = votd_payload[0]
    book_name_english = first["bookname"]
    book_id = english_book_to_id(book_name_english)
    if book_id is None:
        raise ValueError(f"Unknown English book name: {book_name_english}")

    chapter = int(first["chapter"])
    verse_numbers: list[int] = []
    english_verses: list[dict] = []

    for item in votd_payload:
        item_book_id = english_book_to_id(item["bookname"])
        item_chapter = int(item["chapter"])
        if item_book_id != book_id or item_chapter != chapter:
            raise ValueError("VOTD spans multiple books or chapters, which is not supported")

        for verse_number in _parse_verse_numbers(str(item["verse"])):
            if verse_number not in verse_numbers:
                verse_numbers.append(verse_number)
            english_verses.append(
                {
                    "bookname": item["bookname"],
                    "chapter": item_chapter,
                    "verse": verse_number,
                    "text": item.get("text", ""),
                }
            )

    verse_numbers.sort()
    return book_name_english, book_id, chapter, verse_numbers, english_verses


def get_verse_of_the_day(
    bible: BibleReader,
    include_english: bool = False,
) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if _votd_cache["date"] == today and _votd_cache["payload"] is not None:
        cached = dict(_votd_cache["payload"])
        if not include_english:
            cached.pop("english_verses", None)
        return cached

    try:
        votd_payload = _fetch_url(VOTD_API_URL)
    except urllib.error.URLError as error:
        raise RuntimeError(f"Failed to fetch VOTD from labs.bible.org: {error}") from error

    if not isinstance(votd_payload, list):
        raise ValueError("Unexpected VOTD response format")

    book_name_english, book_id, chapter, verse_numbers, english_verses = _collect_votd_items(
        votd_payload
    )

    book = bible.get_book(book_id)
    if book is None:
        raise ValueError(f"Book not found for id {book_id}")

    urdu_verses: list[dict] = []
    for verse_number in verse_numbers:
        verse_data = bible.get_verse(book_id, chapter, verse_number)
        if verse_data is None:
            raise ValueError(
                f"Urdu verse not found for {book_name_english} {chapter}:{verse_number}"
            )
        urdu_verses.append(verse_data)

    canonical_english = ENGLISH_BOOK_NAMES.get(book_id, book_name_english)
    payload = {
        "date": today,
        "reference": {
            "english": _format_reference(canonical_english, chapter, verse_numbers),
            "book_id": book_id,
            "book_name_english": canonical_english,
            "book_name_urdu": book["name"],
            "chapter": chapter,
            "verses": verse_numbers,
        },
        "source": {
            "reference_provider": "labs.bible.org",
            "text_provider": "urdu-bible-data",
        },
        "verses": urdu_verses,
        "english_verses": english_verses,
    }

    _votd_cache["date"] = today
    _votd_cache["payload"] = payload

    if not include_english:
        payload = dict(payload)
        payload.pop("english_verses", None)
    return payload
