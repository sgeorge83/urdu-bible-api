# Urdu Geo Version Bible data (ur_geo)

**API:** [urdu-bible-api.vercel.app](https://urdu-bible-api.vercel.app)  
**Developer docs:** [urdu-bible-api.vercel.app/docs](https://urdu-bible-api.vercel.app/docs)  
**API repo:** [github.com/sgeorge83/urdu-bible-api](https://github.com/sgeorge83/urdu-bible-api)  
**Raw base URL:** `https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main`

## About

This repository hosts the **Urdu Geo Version** Bible (کتابِ مقدس) as structured JSON files for use by apps, websites, and the [Urdu Bible API](https://github.com/sgeorge83/urdu-bible-api).

**Contents**

- `metadata.json` — translation info, publisher, license
- `books.json` — 66 books with Urdu names and chapter counts
- `chapters/{book}/{chapter}.json` — 1,189 chapter files (30,668 verses total)

**Translation:** Urdu Geo Version (`ur_geo`), 2019  
**Script:** Urdu  
**Format:** Split from Bible SuperSearch JSON; text and punctuation unchanged

## Structure

```text
urdu-bible-data/
├── README.md
├── metadata.json
├── books.json
└── chapters/
    ├── 1/                 # Genesis (50 chapters)
    │   ├── 1.json
    │   └── ...
    ├── 40/                # Matthew
    └── 66/                # Revelation (22 chapters)
```

### Example URLs

```text
https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main/metadata.json
https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main/books.json
https://raw.githubusercontent.com/sgeorge83/urdu-bible-data/main/chapters/1/1.json
```

## License

Copyright © 2019 Urdu Geo Version.

This Bible is made available under the [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)](https://creativecommons.org/licenses/by-nc-nd/4.0/) license.

You may share and redistribute this Bible translation or extracts from it in any format, provided that:

- You include the above copyright and source information.
- You do not sell this work for a profit.
- You do not change any of the words or punctuation of the Scriptures.

## Source

Urdu Geo Version (`ur_geo`), reformatted for Bible SuperSearch. No changes were made to the text or punctuation.
