# Urdu Bible API

REST API for the **Urdu Geo Version** Bible (کتابِ مقدس), module `ur_geo`.

This project contains **no Bible text**. Verse data is loaded at runtime from a separate public GitHub repository, which keeps your office laptop and network free of the JSON files.

## Architecture

```text
GitHub: urdu-bible-data     -->  chapter JSON files (public)
GitHub: urdu-bible-api      -->  FastAPI code only
Vercel                      -->  hosts the API
```

## Step 1: Prepare the data (on a personal machine)

Do this once on a home PC, not your office laptop.

1. Copy `ur_geo.json` to your personal machine.
2. Clone or download this API repo on that machine.
3. Run the split script:

```powershell
python scripts/split_bible.py path\to\ur_geo.json path\to\urdu-bible-data
```

4. Copy the data repo readme:

```powershell
copy scripts\DATA_REPO_README.md path\to\urdu-bible-data\README.md
```

5. Delete `ur_geo.json` from your personal machine after verifying the output.

## Step 2: Push data to GitHub

1. Create a new public repo on GitHub, for example `urdu-bible-data`.
2. Upload the generated folder contents:

```text
metadata.json
books.json
chapters/
README.md
```

3. Commit and push. Your files will be available at:

```text
https://raw.githubusercontent.com/YOUR_USERNAME/urdu-bible-data/main/metadata.json
https://raw.githubusercontent.com/YOUR_USERNAME/urdu-bible-data/main/chapters/1/1.json
```

## Step 3: Push API code to GitHub

1. Create another repo, for example `urdu-bible-api`.
2. Push this project (code only, no Bible JSON).
3. Do not commit `.env` or any local data files.

## Step 4: Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and import the `urdu-bible-api` repo.
2. In **Project Settings → General**:
   - **Framework Preset:** `FastAPI` (or `Other`)
   - **Root Directory:** leave empty (project root)
   - **Build Command:** leave empty
   - **Output Directory:** leave empty
3. Vercel loads the app from root `app.py` via `pyproject.toml` (`entrypoint = "app:app"`).
4. Add an environment variable in **Settings → Environment Variables**:

| Name | Value |
|------|-------|
| `BIBLE_DATA_BASE_URL` | `https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main` |

5. **Redeploy** the latest `main` commit (Deployments → ... → Redeploy).
6. If you still see `FUNCTION_INVOCATION_FAILED`, open **Deployments → Logs → Runtime Logs** and check the Python traceback.
7. Test:

```text
GET https://your-project.vercel.app/health
GET https://your-project.vercel.app/books/1/chapters/1/verses/1
GET https://your-project.vercel.app/docs
```

## Local development (optional)

You only need the API code locally. Set the GitHub raw URL in `.env`:

```powershell
pip install -r requirements-dev.txt
uvicorn app:app --app-dir src --reload --host 0.0.0.0 --port 8000
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API overview |
| GET | `/info` | Translation metadata and license |
| GET | `/books` | List all 66 books |
| GET | `/books/{book_id}` | Book details |
| GET | `/books/{book_id}/chapters/{chapter}` | Full chapter |
| GET | `/books/{book_id}/chapters/{chapter}/verses/{verse}` | Single verse |
| GET | `/search?q=...&book=1&limit=50` | Search within one book |

Search requires a `book` parameter because the API fetches chapters on demand from GitHub instead of loading the full Bible into memory.

## Why Vercel + GitHub?

- **Vercel**: simple deploy from GitHub, free tier, HTTPS, good for read-only APIs.
- **GitHub raw URLs**: free static hosting for JSON, no Bible data on your laptop.
- **Chapter files**: each request fetches only one small JSON file, which works well on serverless.

## Book IDs

Standard Protestant order: `1` = Genesis (پَیدائش), `40` = Matthew (متی), `66` = Revelation (مکاشفہ).

## License

The Bible text is Copyright © 2019 Urdu Geo Version, licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/). See `/info` for full copyright details.
