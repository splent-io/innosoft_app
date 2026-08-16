# Recovering every past edition of InnoSoft Days from the Wayback Machine

One-off tooling for this migration (not a SPLENT feature). It rebuilds the
history of the event that the 2025 redesign of innosoftdays.com dropped and
loads it into the product's editions, events, team, media and news.

Pipeline, one script per phase, each resumable and working from local files
after the first run:

| Phase | Script | Output |
|-------|--------|--------|
| 1 discovery | `cdx_index.py` | `data/index.jsonl`, `data/index_summary.md` (every capture the CDX API knows, all hosts the event has used) |
| 2 collection | `fetch.py` | `data/raw/<kind>/<sha>/<timestamp>.<ext>` + `data/raw/manifest.jsonl` (raw bytes, one file per URL version) |
| 3a survey | `survey.py` | `data/survey.jsonl`, `data/survey_summary.md` (template family per capture) |
| 3b extraction | `parse/*.py` | `data/extracted/*.json` (see schema below) + `data/extracted/REPORT.md` |
| 4 import | `import_wayback.py` | rows in the product database, media in the library |

`data/raw/` and the logs are not versioned (re-downloadable from the index);
the index, the survey and the extracted JSON are, so the import stays
reproducible after the archive changes or goes away.

Python for phases 3 lives in `.venv/` (`python3 -m venv .venv && .venv/bin/pip
install beautifulsoup4 lxml`). Phase 4 runs inside the product's web
container (`docker exec -w /workspace/innosoft_app innosoft_app_web python
migration/wayback/import_wayback.py`).

## Sources

- `innosoftdays.com` (WordPress since 2018; posts dated 2018 to 2025, event
  pages from three different event plugins, an Elementor site for the XIII
  edition in 2025). Captured by the archive mostly in 2024 and 2025, when
  the whole post history was still online.
- `institucional.us.es/innosoft/` (not `/innosoftdays/`): the university-hosted
  WordPress used until 2021, found through the image URLs the 2018-2020
  posts still embed. Sparse but valuable captures: home 2020, the 2019
  programme, the IX (2021) programme by day, one 2020 event page.
  Editions I to IV (2013 to 2016) exist in no archive we could reach.

## Result (import of 2026-08-16)

Editions V (2017) to XIII (2025), all with dates and venue; 253 events from
2017 to 2024 added to the product (2025 was already curated), 155 speakers
and 294 organisers (XI, XII) into team, 130 news posts with their original
permalinks, 16 informative pages folded into the edition descriptions, and
the 63 archived images that survive (986 of the 1049 images the pages
referenced were never captured by the archive; the importer drops them so
no page shows a broken box). The 151 "posts" of 2025 were SEO spam
published through a compromised author account and were left out. See
`data/extracted/REPORT.md` and `AUDIT.md` for the details and every
conflict resolution.

## Extracted JSON schema (`data/extracted/`)

All dates ISO 8601, naive Europe/Madrid. All HTML cleaned to semantic markup
(no Elementor/plugin wrappers, no inline styles), image URLs pointing at the
ORIGINAL site URL (the importer resolves them through the raw captures).

- `editions.json`: `[{"year", "number", "roman", "name", "starts_on",
  "ends_on", "venue", "summary", "description_html", "registration_url",
  "sources": [urls], "confidence": "high|medium|low", "notes"}]`
- `events.json`: `[{"edition_year", "title", "kind"
  (talk|workshop|competition|ceremony|social|stand|mentoring|other),
  "starts_at", "ends_at", "room", "modality" (in_person|online), "speaker",
  "company", "summary", "description_html", "poster_url", "link", "lang",
  "source_url", "source_timestamp"}]`
- `speakers.json`: `[{"name", "affiliation", "position", "bio_html",
  "photo_url", "links": [{"label","url"}], "edition_years": [], "source_url"}]`
- `organisers.json`: `[{"edition_year", "name", "role", "photo_url",
  "source_url"}]`
- `posts.json`: `[{"date", "title", "slug", "excerpt", "content_html",
  "featured_image_url", "lang", "edition_year", "categories": [],
  "source_url", "source_timestamp"}]`
- `pages.json`: `[{"edition_year", "title", "url", "content_html", "kind"
  (about|sustainability|how_to_get|organization|other)}]`
- `media.json`: `[{"url", "kind" (poster|photo|logo|other), "edition_year",
  "caption", "used_by": [source urls]}]`
- `REPORT.md`: coverage per family and year, conflicts and how they were
  resolved, gaps.

## Mapping into the product

| Extracted | Product |
|-----------|---------|
| edition | `Edition` (editions feature); the latest becomes current only if none is flagged |
| event | `Event` with `edition_id` (events feature); poster into media, `source_key=wayback://<url>` |
| speaker | `TeamMember` with role "Ponentes" (team feature), deduplicated by name across editions |
| organiser | `TeamMember` with role "Organización <roman>" per edition |
| post | `Post` (post feature) with a category per edition; permalinks keep `/YYYY/MM/DD/slug` |
| page | folded into the edition `description_html` (about, sustainability) or into posts (kind other) |
| media | media library, public, titled by edition and activity |
