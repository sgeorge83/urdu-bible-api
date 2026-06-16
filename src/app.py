from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from bible_data import BibleData

app = FastAPI(
    title="Urdu Bible API",
    description="REST API for the Urdu Geo Version Bible (کتابِ مقدس)",
    version="1.0.0",
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


@app.get("/")
def root() -> dict:
    bible = get_bible()
    return {
        "name": "Urdu Bible API",
        "translation": bible.metadata.get("name"),
        "module": bible.metadata.get("module"),
        "data_source": bible.base_url,
        "docs": "/docs",
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
