# Urdu Bible API

**Live API:** [urdu-bible-api.vercel.app](https://urdu-bible-api.vercel.app)  
**Interactive docs:** [urdu-bible-api.vercel.app/docs](https://urdu-bible-api.vercel.app/docs)  
**Data repo:** [github.com/sgeorge83/urdu-bible-data](https://github.com/sgeorge83/urdu-bible-data)

## About

**Urdu Bible API** is a free, read-only REST API for the **Urdu Geo Version** of the Holy Bible (کتابِ مقدس, module `ur_geo`, 2019).

The API is built with **FastAPI**, deployed on **Vercel**, and includes interactive OpenAPI docs at `/docs`. It does **not** store Bible text in this repo — verse data is loaded at runtime from the companion [urdu-bible-data](https://github.com/sgeorge83/urdu-bible-data) repository via GitHub raw URLs.

**Features**

- List all 66 books
- Read any chapter or single verse
- Search Urdu text within a book
- Translation metadata and license info at `/info`
- CORS enabled for web and mobile apps

**Tech stack:** Python 3.12 · FastAPI · Vercel · GitHub (data CDN)

## Architecture

```text
GitHub: urdu-bible-data  -->  chapter JSON files (public)
GitHub: urdu-bible-api   -->  FastAPI code only
Vercel                   -->  hosts the API
```

## Project structure

```text
urdu-bible-api/
├── app.py                 # Production app (Vercel entrypoint)
├── pyproject.toml         # Vercel entrypoint = "app:app"
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Local dev (includes uvicorn)
├── .vercelignore
├── .env.example
├── README.md
└── scripts/
    ├── split_bible.py     # One-time tool to split ur_geo.json
    └── DATA_REPO_README.md
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API overview |
| GET | `/health` | Health check |
| GET | `/info` | Translation metadata and license |
| GET | `/books` | List all 66 books |
| GET | `/books/{book_id}` | Book details |
| GET | `/books/{book_id}/chapters/{chapter}` | Full chapter |
| GET | `/books/{book_id}/chapters/{chapter}/verses/{verse}` | Single verse |
| GET | `/search?q=...&book=1&limit=50` | Search within one book |

Search requires a `book` parameter because the API fetches chapters on demand from GitHub instead of loading the full Bible into memory.

### Examples

```text
GET https://urdu-bible-api.vercel.app/books
GET https://urdu-bible-api.vercel.app/books/1/chapters/1/verses/1
GET https://urdu-bible-api.vercel.app/search?q=اللہ&book=1&limit=10
```

## Book IDs

Standard Protestant order: `1` = Genesis (پَیدائش), `40` = Matthew (متی), `66` = Revelation (مکاشفہ).

## Deploy on Vercel

1. Import this repo at [vercel.com](https://vercel.com).
2. In **Project Settings → General**:
   - **Framework Preset:** `FastAPI` (or `Other`)
   - **Root Directory:** leave empty
   - **Build Command:** leave empty
   - **Output Directory:** leave empty
3. Vercel loads the app from root `app.py` via `pyproject.toml`.
4. Add this environment variable under **Settings → Environment Variables**:

| Name | Value |
|------|-------|
| `BIBLE_DATA_BASE_URL` | `https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main` |

5. Deploy and test `/health`, `/docs`, and `/books/1/chapters/1/verses/1`.

## Local development

```powershell
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs).

## Regenerating data (optional)

If you need to rebuild the data repo from a source `ur_geo.json` file:

```powershell
python scripts/split_bible.py path\to\ur_geo.json path\to\urdu-bible-data
copy scripts\DATA_REPO_README.md path\to\urdu-bible-data\README.md
```

Then push the output to [urdu-bible-data](https://github.com/sgeorge83/urdu-bible-data).

## License

The Bible text is Copyright © 2019 Urdu Geo Version, licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/). See `/info` for full copyright details.
