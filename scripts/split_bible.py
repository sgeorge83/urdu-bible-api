#!/usr/bin/env python3
"""Split a Bible SuperSearch JSON file into chapter files for GitHub hosting.

Run this once on a personal machine (not your office laptop), then upload the
output folder to a public GitHub repository.

Usage:
    python scripts/split_bible.py path/to/ur_geo.json path/to/output-dir
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def split_bible(source_path: Path, output_dir: Path) -> None:
    with source_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    metadata = payload["metadata"]
    verses: list[dict] = payload["verses"]

    books: dict[int, dict] = {}
    chapters: dict[tuple[int, int], list[dict]] = {}

    for verse in verses:
        book_id = verse["book"]
        chapter = verse["chapter"]

        if book_id not in books:
            books[book_id] = {
                "id": book_id,
                "name": verse["book_name"],
                "chapters": set(),
            }

        books[book_id]["chapters"].add(chapter)
        chapters.setdefault((book_id, chapter), []).append(verse)

    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)

    book_list = [
        {
            "id": book["id"],
            "name": book["name"],
            "chapter_count": len(book["chapters"]),
        }
        for book in sorted(books.values(), key=lambda item: item["id"])
    ]

    with (output_dir / "books.json").open("w", encoding="utf-8") as handle:
        json.dump(book_list, handle, ensure_ascii=False, indent=2)

    chapters_dir = output_dir / "chapters"
    for (book_id, chapter_num), chapter_verses in sorted(chapters.items()):
        chapter_dir = chapters_dir / str(book_id)
        chapter_dir.mkdir(parents=True, exist_ok=True)

        chapter_payload = {
            "book": book_id,
            "book_name": chapter_verses[0]["book_name"],
            "chapter": chapter_num,
            "verse_count": len(chapter_verses),
            "verses": chapter_verses,
        }

        chapter_path = chapter_dir / f"{chapter_num}.json"
        with chapter_path.open("w", encoding="utf-8") as handle:
            json.dump(chapter_payload, handle, ensure_ascii=False, indent=2)

    print(f"Created {len(book_list)} books and {len(chapters)} chapter files in {output_dir}")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python scripts/split_bible.py path/to/ur_geo.json path/to/output-dir")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not source_path.is_file():
        print(f"Source file not found: {source_path}")
        sys.exit(1)

    split_bible(source_path, output_dir)


if __name__ == "__main__":
    main()
