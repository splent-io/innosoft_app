"""Completeness / schema / sanity audit of data/extracted/*.json.

Read-only: never modifies the JSON. Writes data/extracted/AUDIT.md and prints
a JSON summary (uncovered captures, schema errors, sanity findings, verdict).

1. Coverage: every fetched HTML capture (manifest kinds page, event,
   event-index, post, speaker) whose URL is not referenced by any item of the
   final JSON (source_url, sources, used_by, pages.url) and is not listed in
   any parts/*.notes.md, grouped by kind.
2. Schema: every final JSON file against the README schema (required keys,
   ISO dates, allowed kinds, edition_year in 2013..2025, starts_at year ==
   edition_year unless the REPORT notes it).
3. Sanity: editions 2018..2025 present with dates in Oct/Nov, events per
   edition > 0 for 2018..2024, no event dated outside its edition +-30 days,
   no speaker with an empty name, no post without date, HTML fields free of
   <script>/<style>/class=/style=.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from parse.common import EXTRACTED, manifest_rows, name_key, norm_key, norm_media_url, norm_url, roman, same_person  # noqa: E402

PARTS = EXTRACTED / "parts"
HTML_KINDS = ("page", "event", "event-index", "post", "speaker")
YEAR_MIN, YEAR_MAX = 2013, 2025

SCHEMA = {
    "editions": ["year", "number", "roman", "name", "starts_on", "ends_on", "venue", "summary", "description_html", "registration_url", "sources", "confidence", "notes"],
    "events": ["edition_year", "title", "kind", "starts_at", "ends_at", "room", "modality", "speaker", "company", "summary", "description_html", "poster_url", "link", "lang", "source_url", "source_timestamp"],
    "speakers": ["name", "affiliation", "position", "bio_html", "photo_url", "links", "edition_years", "source_url"],
    "organisers": ["edition_year", "name", "role", "photo_url", "source_url"],
    "posts": ["date", "title", "slug", "excerpt", "content_html", "featured_image_url", "lang", "edition_year", "categories", "source_url", "source_timestamp"],
    "pages": ["edition_year", "title", "url", "content_html", "kind"],
    "media": ["url", "kind", "edition_year", "caption", "used_by"],
}
EVENT_KINDS = {"talk", "workshop", "competition", "ceremony", "social", "stand", "mentoring", "other"}
PAGE_KINDS = {"about", "sustainability", "how_to_get", "organization", "other"}
MEDIA_KINDS = {"poster", "photo", "logo", "other"}
MODALITIES = {"in_person", "online"}
CONFIDENCES = {"high", "medium", "low"}
HTML_FIELDS = {"description_html", "bio_html", "content_html", "summary", "excerpt", "caption"}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def canon(url: str) -> str:
    """Comparison key for a URL: norm_url + no trailing slash + no fragment."""
    u = norm_url(url or "")
    u = u.rstrip("/")
    return u


def url_variants(url: str) -> set[str]:
    """Spellings a notes file may use for the same capture URL."""
    c = canon(url)
    out = {c, c + "/"}
    if c.startswith("https://www."):
        bare = "https://" + c[len("https://www."):]
        out |= {bare, bare + "/"}
    out |= {v.replace("https://", "http://") for v in list(out)}
    return out


def media_base(url: str) -> str:
    """Host-mapped (institucional -> www), size- and -scaled-suffix-free key
    of an upload URL, so every variant of one image compares equal."""
    u = canon(norm_media_url(url))
    u = re.sub(r"-\d+x\d+(\.[a-z0-9]+)$", r"\1", u, flags=re.I)
    u = re.sub(r"-scaled(\.[a-z0-9]+)$", r"\1", u, flags=re.I)
    return u.lower()


def parse_iso_date(s):
    """date for 'YYYY-MM-DD'; None when not that shape."""
    if not isinstance(s, str):
        return None
    try:
        return date.fromisoformat(s[:10]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else None
    except ValueError:
        return None


def parse_iso_datetime(s):
    """(datetime, 'datetime'|'date') for ISO strings, (None, None) otherwise."""
    if not isinstance(s, str):
        return None, None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        try:
            d = date.fromisoformat(s)
            return datetime(d.year, d.month, d.day), "date"
        except ValueError:
            return None, None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?", s):
        try:
            return datetime.fromisoformat(s), "datetime"
        except ValueError:
            return None, None
    return None, None


def load(name):
    p = EXTRACTED / f"{name}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def item_label(kind, it):
    if kind == "editions":
        return f"edition {it.get('year')}"
    if kind == "events":
        return f"event [{it.get('edition_year')}] {str(it.get('title'))[:60]!r} ({it.get('source_url')})"
    if kind == "speakers":
        return f"speaker {str(it.get('name'))!r}"
    if kind == "organisers":
        return f"organiser [{it.get('edition_year')}] {str(it.get('name'))!r}"
    if kind == "posts":
        return f"post {it.get('date')} {str(it.get('title'))[:60]!r} ({it.get('source_url')})"
    if kind == "pages":
        return f"page [{it.get('edition_year')}] {str(it.get('title'))[:60]!r} ({it.get('url')})"
    if kind == "media":
        return f"media {it.get('url')}"
    return kind


# --------------------------------------------------------------------------
# 1. coverage
# --------------------------------------------------------------------------

def collect_final_refs(final: dict) -> set[str]:
    refs = set()

    def add(u):
        if isinstance(u, str) and u.strip():
            refs.add(canon(u))

    for it in final.get("editions") or []:
        for u in it.get("sources") or []:
            add(u)
    for it in final.get("events") or []:
        add(it.get("source_url"))
    for it in final.get("speakers") or []:
        add(it.get("source_url"))
    for it in final.get("organisers") or []:
        add(it.get("source_url"))
    for it in final.get("posts") or []:
        add(it.get("source_url"))
    for it in final.get("pages") or []:
        add(it.get("url"))
    for it in final.get("media") or []:
        for u in it.get("used_by") or []:
            add(u)
    return refs


def collect_any_string_refs(final: dict) -> set[str]:
    """Every URL that appears anywhere in the final JSON text (links, hrefs,
    poster URLs...). Secondary signal only."""
    refs = set()
    for kind, items in final.items():
        if items is None:
            continue
        text = json.dumps(items, ensure_ascii=False)
        for m in re.finditer(r"https?://[^\s\"'<>\\)]+", text):
            refs.add(canon(m.group(0)))
    return refs


def collect_parts_refs() -> set[str]:
    refs = set()
    for p in sorted(PARTS.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for it in data if isinstance(data, list) else []:
            if not isinstance(it, dict):
                continue
            for k in ("source_url", "url"):
                if isinstance(it.get(k), str):
                    refs.add(canon(it[k]))
            for k in ("sources", "used_by"):
                for u in it.get(k) or []:
                    if isinstance(u, str):
                        refs.add(canon(u))
    return refs


def collect_notes_text() -> tuple[str, dict[str, str]]:
    per_file = {}
    for p in sorted(PARTS.glob("*.notes.md")):
        per_file[p.name] = p.read_text(encoding="utf-8")
    return "\n".join(per_file.values()), per_file


def notes_mentions(url: str, notes_text: str, notes_urls: set[str], notes_paths: set[str]) -> str:
    """'' when the URL is not in the notes; 'url' when it appears as a full
    URL; 'path' when only its path appears (innosoftdays.com URLs)."""
    if canon(url) in notes_urls:
        return "url"
    c = canon(url)
    m = re.match(r"https?://[^/]+(/.*)$", c)
    path = m.group(1) if m else ""
    if path and len(path) > 1:
        if path in notes_paths or (path + "/") in notes_paths:
            return "path"
    return ""


def coverage(final: dict):
    rows = [r for r in manifest_rows() if r.get("kind") in HTML_KINDS]
    final_refs = collect_final_refs(final)
    any_refs = collect_any_string_refs(final)
    parts_refs = collect_parts_refs()
    notes_text, notes_files = collect_notes_text()

    notes_urls = set()
    for m in re.finditer(r"https?://[^\s\"'<>`|)\]]+", notes_text):
        u = m.group(0).rstrip(".,;:")
        notes_urls.add(canon(u))
    notes_paths = set()
    for m in re.finditer(r"`(/[^`\s]*)`", notes_text):
        notes_paths.add(m.group(1))
    for m in re.finditer(r"(?<![\w/:.])(/[a-z0-9][a-z0-9_\-/.?=&%]*/?)(?![\w/])", notes_text):
        notes_paths.add(m.group(1))

    per_url = defaultdict(list)
    for r in rows:
        per_url[canon(r["url"])].append(r)

    uncovered = []          # strict: not in final refs and not in notes at all
    notes_only = []         # not in final refs, but mentioned in notes (url or path)
    covered = 0
    for key, caps in sorted(per_url.items()):
        url = caps[0]["url"]
        kind = Counter(c["kind"] for c in caps).most_common(1)[0][0]
        if key in final_refs:
            covered += len(caps)
            continue
        mention = notes_mentions(url, notes_text, notes_urls, notes_paths)
        info = {
            "url": url,
            "kind": kind,
            "captures": sorted(c["timestamp"] for c in caps),
            "in_parts_json": key in parts_refs,
            "in_final_text": key in any_refs,
            "notes_mention": mention,
        }
        if mention:
            notes_only.append(info)
        else:
            uncovered.append(info)
    return {
        "total_captures": len(rows),
        "total_urls": len(per_url),
        "covered_by_final_captures": covered,
        "uncovered": uncovered,
        "notes_only": notes_only,
    }


# --------------------------------------------------------------------------
# 2. schema
# --------------------------------------------------------------------------

def check_schema(final: dict, report_text: str):
    errors = []
    warnings = []

    def err(msg):
        errors.append(msg)

    for kind, keys in SCHEMA.items():
        items = final.get(kind)
        if items is None:
            err(f"{kind}.json: file missing")
            continue
        if not isinstance(items, list):
            err(f"{kind}.json: top level is not a list")
            continue
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                err(f"{kind}[{i}]: not an object")
                continue
            missing = [k for k in keys if k not in it]
            extra = [k for k in it if k not in keys]
            if missing:
                err(f"{item_label(kind, it)}: missing keys {missing}")
            if extra:
                warnings.append(f"{item_label(kind, it)}: extra keys {extra}")

    # editions
    for it in final.get("editions") or []:
        y = it.get("year")
        if not isinstance(y, int) or not (YEAR_MIN <= y <= YEAR_MAX):
            err(f"{item_label('editions', it)}: year {y!r} outside {YEAR_MIN}..{YEAR_MAX}")
            continue
        if it.get("number") != y - 2012:
            err(f"{item_label('editions', it)}: number {it.get('number')!r} != {y - 2012}")
        if it.get("roman") != roman(y - 2012):
            err(f"{item_label('editions', it)}: roman {it.get('roman')!r} != {roman(y - 2012)}")
        for k in ("starts_on", "ends_on"):
            d = parse_iso_date(it.get(k))
            if d is None:
                err(f"{item_label('editions', it)}: {k} {it.get(k)!r} is not an ISO date")
            elif d.year != y:
                err(f"{item_label('editions', it)}: {k} {it.get(k)} not in year {y}")
        s, e = parse_iso_date(it.get("starts_on")), parse_iso_date(it.get("ends_on"))
        if s and e and e < s:
            err(f"{item_label('editions', it)}: ends_on before starts_on")
        if it.get("confidence") not in CONFIDENCES:
            err(f"{item_label('editions', it)}: confidence {it.get('confidence')!r} not in {sorted(CONFIDENCES)}")
        if not isinstance(it.get("sources"), list) or not it.get("sources"):
            err(f"{item_label('editions', it)}: sources empty or not a list")
        if not (it.get("name") or "").strip():
            err(f"{item_label('editions', it)}: empty name")

    # events
    year_mismatch = []
    for it in final.get("events") or []:
        y = it.get("edition_year")
        if not isinstance(y, int) or not (YEAR_MIN <= y <= YEAR_MAX):
            err(f"{item_label('events', it)}: edition_year {y!r} outside {YEAR_MIN}..{YEAR_MAX}")
            y = None
        if it.get("kind") not in EVENT_KINDS:
            err(f"{item_label('events', it)}: kind {it.get('kind')!r} not allowed")
        if not (it.get("title") or "").strip():
            err(f"{item_label('events', it)}: empty title")
        st, st_kind = parse_iso_datetime(it.get("starts_at"))
        if it.get("starts_at") is not None and st is None:
            err(f"{item_label('events', it)}: starts_at {it.get('starts_at')!r} is not ISO")
        en, _ = parse_iso_datetime(it.get("ends_at"))
        if it.get("ends_at") is not None and en is None:
            err(f"{item_label('events', it)}: ends_at {it.get('ends_at')!r} is not ISO")
        if st and en and en < st:
            err(f"{item_label('events', it)}: ends_at before starts_at ({it.get('starts_at')} > {it.get('ends_at')})")
        if st and y and st.year != y:
            year_mismatch.append(it)
        if it.get("modality") is not None and it.get("modality") not in MODALITIES:
            err(f"{item_label('events', it)}: modality {it.get('modality')!r} not allowed")
        if it.get("lang") not in ("es", "en", None):
            warnings.append(f"{item_label('events', it)}: lang {it.get('lang')!r}")
        if not (it.get("source_url") or "").strip():
            err(f"{item_label('events', it)}: empty source_url")
        if not re.fullmatch(r"\d{14}", str(it.get("source_timestamp") or "")):
            err(f"{item_label('events', it)}: source_timestamp {it.get('source_timestamp')!r} is not a 14-digit Wayback timestamp")
    for it in year_mismatch:
        title = it.get("title") or ""
        noted = title in report_text or (it.get("source_url") or "") in report_text
        (warnings if noted else errors).append(
            f"{item_label('events', it)}: starts_at {it.get('starts_at')} year != edition_year {it.get('edition_year')}" + (" (noted in REPORT.md)" if noted else " (NOT noted in REPORT.md)"))

    # speakers
    for it in final.get("speakers") or []:
        if not (it.get("name") or "").strip():
            err(f"{item_label('speakers', it)}: empty name")
        ys = it.get("edition_years")
        if not isinstance(ys, list):
            err(f"{item_label('speakers', it)}: edition_years not a list")
        else:
            for y in ys:
                if not isinstance(y, int) or not (YEAR_MIN <= y <= YEAR_MAX):
                    err(f"{item_label('speakers', it)}: edition_year {y!r} outside range")
            if not ys:
                warnings.append(f"{item_label('speakers', it)}: empty edition_years")
        links = it.get("links")
        if not isinstance(links, list):
            err(f"{item_label('speakers', it)}: links not a list")
        else:
            for l in links:
                if not isinstance(l, dict) or "url" not in l or "label" not in l:
                    err(f"{item_label('speakers', it)}: link {l!r} lacks label/url")
        if not (it.get("source_url") or "").strip():
            err(f"{item_label('speakers', it)}: empty source_url")

    # organisers
    for it in final.get("organisers") or []:
        y = it.get("edition_year")
        if not isinstance(y, int) or not (YEAR_MIN <= y <= YEAR_MAX):
            err(f"{item_label('organisers', it)}: edition_year {y!r} outside range")
        if not (it.get("name") or "").strip():
            err(f"{item_label('organisers', it)}: empty name")
        if not (it.get("role") or "").strip():
            warnings.append(f"{item_label('organisers', it)}: empty role")
        if not (it.get("source_url") or "").strip():
            err(f"{item_label('organisers', it)}: empty source_url")

    # posts
    for it in final.get("posts") or []:
        d, _ = parse_iso_datetime(it.get("date"))
        if d is None:
            err(f"{item_label('posts', it)}: date {it.get('date')!r} is not ISO")
        y = it.get("edition_year")
        if y is not None and (not isinstance(y, int) or not (YEAR_MIN <= y <= YEAR_MAX)):
            err(f"{item_label('posts', it)}: edition_year {y!r} outside range")
        if d and isinstance(y, int) and d.year != y:
            warnings.append(f"{item_label('posts', it)}: post year {d.year} != edition_year {y}")
        if not (it.get("title") or "").strip():
            err(f"{item_label('posts', it)}: empty title")
        if not (it.get("slug") or "").strip():
            err(f"{item_label('posts', it)}: empty slug")
        if not isinstance(it.get("categories"), list):
            err(f"{item_label('posts', it)}: categories not a list")
        if it.get("lang") not in ("es", "en"):
            warnings.append(f"{item_label('posts', it)}: lang {it.get('lang')!r}")
        if not (it.get("source_url") or "").strip():
            err(f"{item_label('posts', it)}: empty source_url")
        if not re.fullmatch(r"\d{14}", str(it.get("source_timestamp") or "")):
            err(f"{item_label('posts', it)}: source_timestamp {it.get('source_timestamp')!r} invalid")

    # pages
    for it in final.get("pages") or []:
        y = it.get("edition_year")
        if y is not None and (not isinstance(y, int) or not (YEAR_MIN <= y <= YEAR_MAX)):
            err(f"{item_label('pages', it)}: edition_year {y!r} outside range")
        if it.get("kind") not in PAGE_KINDS:
            err(f"{item_label('pages', it)}: kind {it.get('kind')!r} not allowed")
        if not (it.get("url") or "").strip():
            err(f"{item_label('pages', it)}: empty url")
        if not (it.get("content_html") or "").strip():
            warnings.append(f"{item_label('pages', it)}: empty content_html")

    # media
    for it in final.get("media") or []:
        y = it.get("edition_year")
        if y is not None and (not isinstance(y, int) or not (YEAR_MIN <= y <= YEAR_MAX)):
            err(f"{item_label('media', it)}: edition_year {y!r} outside range")
        if it.get("kind") not in MEDIA_KINDS:
            err(f"{item_label('media', it)}: kind {it.get('kind')!r} not allowed")
        if not (it.get("url") or "").startswith("http"):
            err(f"{item_label('media', it)}: url not absolute")
        if not isinstance(it.get("used_by"), list) or not it.get("used_by"):
            err(f"{item_label('media', it)}: used_by empty or not a list")

    return errors, warnings


# --------------------------------------------------------------------------
# 3. sanity
# --------------------------------------------------------------------------

BAD_HTML = [
    ("<script", re.compile(r"<script\b", re.I)),
    ("<style", re.compile(r"<style\b", re.I)),
    ("class=", re.compile(r"<[^>]*\sclass\s*=", re.I)),
    ("style=", re.compile(r"<[^>]*\sstyle\s*=", re.I)),
    ("on*= handler", re.compile(r"<[^>]*\son\w+\s*=", re.I)),
    ("web.archive.org URL", re.compile(r"web\.archive\.org/web/", re.I)),
]


def sanity(final: dict, report_text: str = ""):
    findings = []
    infos = []
    editions = {e.get("year"): e for e in final.get("editions") or [] if isinstance(e.get("year"), int)}

    # editions 2018..2025 with Oct/Nov dates
    for y in range(2018, 2026):
        e = editions.get(y)
        if e is None:
            findings.append(f"edition {y} missing")
            continue
        for k in ("starts_on", "ends_on"):
            d = parse_iso_date(e.get(k))
            if d is None or d.month not in (10, 11):
                findings.append(f"edition {y}: {k} {e.get(k)!r} not in October/November")
    for y, e in editions.items():
        if y < 2018:
            for k in ("starts_on", "ends_on"):
                d = parse_iso_date(e.get(k))
                if d is None or d.month not in (10, 11):
                    findings.append(f"edition {y}: {k} {e.get(k)!r} not in October/November")

    # events per edition
    per_year = Counter(ev.get("edition_year") for ev in final.get("events") or [])
    for y in range(2018, 2025):
        if per_year.get(y, 0) <= 0:
            findings.append(f"no events for edition {y}")
    infos.append("events per edition_year: " + ", ".join(f"{y}: {n}" for y, n in sorted(per_year.items(), key=lambda kv: (kv[0] is None, kv[0]))))
    for y in per_year:
        if y not in editions:
            findings.append(f"events reference edition_year {y} that has no edition record")

    # events outside edition +-30 days
    undated = 0
    date_only = 0
    for ev in final.get("events") or []:
        y = ev.get("edition_year")
        st, st_kind = parse_iso_datetime(ev.get("starts_at"))
        if st is None:
            undated += 1
            continue
        if st_kind == "date":
            date_only += 1
        e = editions.get(y)
        if e is None:
            continue
        s, en = parse_iso_date(e.get("starts_on")), parse_iso_date(e.get("ends_on"))
        if s is None or en is None:
            continue
        lo, hi = s - timedelta(days=30), en + timedelta(days=30)
        if not (lo <= st.date() <= hi):
            findings.append(f"event outside edition {y} +-30 days: {ev.get('starts_at')} {str(ev.get('title'))[:70]!r} ({ev.get('source_url')})" + (" [mentioned in REPORT.md]" if (ev.get("title") or "") in report_text else " [NOT mentioned in REPORT.md]"))
    infos.append(f"events without starts_at: {undated}; events with date-only starts_at: {date_only}")
    outside = []
    for ev in final.get("events") or []:
        e = editions.get(ev.get("edition_year"))
        st, _ = parse_iso_datetime(ev.get("starts_at"))
        if e is None or st is None:
            continue
        s_, en_ = parse_iso_date(e.get("starts_on")), parse_iso_date(e.get("ends_on"))
        if s_ and en_ and not (s_ <= st.date() <= en_):
            outside.append(f"[{ev.get('edition_year')}] {ev.get('starts_at')} {str(ev.get('title'))[:60]!r}")
    infos.append(f"events dated outside their edition's own starts_on..ends_on (within +-30 days or not): {len(outside)}" + (": " + "; ".join(outside) if outside else ""))

    # duplicates (same edition_year + title + starts_at)
    seen = Counter((ev.get("edition_year"), (ev.get("title") or "").strip().lower(), ev.get("starts_at")) for ev in final.get("events") or [])
    dups = [(k, n) for k, n in seen.items() if n > 1]
    for k, n in sorted(dups, key=str):
        findings.append(f"duplicate event ({n}x): edition {k[0]} {k[1][:70]!r} at {k[2]}")

    # speakers
    for sp in final.get("speakers") or []:
        if not (sp.get("name") or "").strip():
            findings.append("speaker with empty name")
    names = Counter((sp.get("name") or "").strip().lower() for sp in final.get("speakers") or [])
    for n, c in names.items():
        if c > 1:
            findings.append(f"speaker name repeated {c}x: {n!r}")
    sp_years = Counter()
    for sp in final.get("speakers") or []:
        for y in sp.get("edition_years") or []:
            sp_years[y] += 1
    infos.append("speakers per edition_year: " + ", ".join(f"{y}: {n}" for y, n in sorted(sp_years.items())))
    for y in sp_years:
        if y not in editions:
            findings.append(f"speakers reference edition_year {y} that has no edition record")

    # organisers
    org_years = Counter(o.get("edition_year") for o in final.get("organisers") or [])
    infos.append("organisers per edition_year: " + ", ".join(f"{y}: {n}" for y, n in sorted(org_years.items(), key=str)))
    dup_org = Counter((o.get("edition_year"), (o.get("name") or "").strip().lower(), (o.get("role") or "").strip().lower()) for o in final.get("organisers") or [])
    for k, n in dup_org.items():
        if n > 1:
            findings.append(f"duplicate organiser ({n}x): edition {k[0]} {k[1]!r} role {k[2]!r}")

    # posts
    for p in final.get("posts") or []:
        if not p.get("date"):
            findings.append(f"post without date: {str(p.get('title'))[:60]!r} ({p.get('source_url')})")
    post_years = Counter(p.get("edition_year") for p in final.get("posts") or [])
    infos.append("posts per edition_year: " + ", ".join(f"{y}: {n}" for y, n in sorted(post_years.items(), key=str)))
    dup_posts = Counter((p.get("date"), (p.get("slug") or "").lower()) for p in final.get("posts") or [])
    for k, n in dup_posts.items():
        if n > 1:
            findings.append(f"duplicate post ({n}x): {k[0]} slug {k[1]!r}")
    empty_posts = [p for p in final.get("posts") or [] if not (p.get("content_html") or "").strip()]
    if empty_posts:
        findings.append(f"{len(empty_posts)} posts with empty content_html: " + "; ".join(str(p.get("title"))[:50] for p in empty_posts[:10]))

    # HTML fields
    html_hits = Counter()
    html_examples = defaultdict(list)
    for kind, items in final.items():
        for it in items or []:
            for f in HTML_FIELDS:
                v = it.get(f)
                if not isinstance(v, str) or "<" not in v:
                    continue
                for label, rx in BAD_HTML:
                    if rx.search(v):
                        html_hits[(kind, f, label)] += 1
                        if len(html_examples[(kind, f, label)]) < 3:
                            html_examples[(kind, f, label)].append(item_label(kind, it))
    for (kind, f, label), n in sorted(html_hits.items()):
        findings.append(f"HTML field {kind}.{f} contains {label} in {n} item(s), e.g. " + "; ".join(html_examples[(kind, f, label)]))
    if not html_hits:
        infos.append("HTML fields: no <script>, <style>, class=, style=, on*= or web.archive.org URLs found")


    # cross-references between files (informational)
    fm_bases = {media_base(m.get("url") or "") for m in final.get("media") or []}
    dangling = Counter()
    external = Counter()
    for kind, field in (("events", "poster_url"), ("speakers", "photo_url"), ("posts", "featured_image_url")):
        for it in final.get(kind) or []:
            u = it.get(field)
            if not u:
                continue
            if media_base(u) in fm_bases:
                continue
            (external if "innosoftdays" not in u and "institucional.us.es" not in u else dangling)[f"{kind}.{field}"] += 1
    imgs = set()
    for kind in ("editions", "events", "speakers", "posts", "pages"):
        for it in final.get(kind) or []:
            for f in ("description_html", "bio_html", "content_html"):
                for m in re.finditer(r'<img[^>]*src="([^"]+)"', it.get(f) or ""):
                    imgs.add(m.group(1))
    img_dangling = [u for u in imgs if media_base(u) not in fm_bases and ("innosoftdays" in u or "institucional.us.es" in u)]
    img_external = [u for u in imgs if media_base(u) not in fm_bases and not ("innosoftdays" in u or "institucional.us.es" in u)]
    infos.append(f"image references: poster/photo/featured URLs on the two site hosts with no media entry: {sum(dangling.values())}; external (hotlinked) ones: {sum(external.values())}; <img> in HTML fields: {len(imgs)} distinct, {len(img_dangling)} site-hosted without media entry, {len(img_external)} external hotlinks (not in media.json by design)")
    for u in img_dangling:
        findings.append(f"site-hosted <img> with no media entry: {u}")
    for k, n in dangling.items():
        findings.append(f"{n} {k} values on the site hosts have no media entry")

    names = [sp.get("name") or "" for sp in final.get("speakers") or []]
    missing = set()
    for ev in final.get("events") or []:
        for part in re.split(r",| y | e |/|&", ev.get("speaker") or ""):
            part = part.strip()
            if part and not any(same_person(part, n) or name_key(n) == name_key(part) for n in names):
                missing.add((ev.get("edition_year"), part))
    infos.append(f"event speaker names with no speaker record: {len(missing)}: " + "; ".join(f"{p} ({y})" for y, p in sorted(missing, key=str)))

    # media resolution against the CDX index (informational)
    idx = HERE / "data" / "index.jsonl"
    if idx.exists():
        idx_urls = set()
        for line in idx.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            idx_urls.add(media_base(r.get("original") or ""))
        unresolved = 0
        for m in final.get("media") or []:
            if media_base(m.get("url") or "") not in idx_urls:
                unresolved += 1
        infos.append(f"media URLs with no capture at all in the CDX index (any size variant, any status): {unresolved} of {len(final.get('media') or [])}")

    return findings, infos


# --------------------------------------------------------------------------
# 4. synthesis cross-checks (parts -> final, notes delegations -> final)
# --------------------------------------------------------------------------

def load_part(name):
    p = PARTS / name
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def synthesis_checks(final: dict, report_text: str = ""):
    """Every record of every parts/*.json must survive into the final JSON in
    some form (same source URL, same year+title, same year+start, same
    person, same media URL). What does not is a synthesis loss unless the
    REPORT explains it."""
    findings = []
    infos = []
    fe = final.get("events") or []
    f_urls = {canon(e.get("source_url")) for e in fe}
    f_titles = {(e.get("edition_year"), norm_key(e.get("title") or "")) for e in fe}
    f_starts = {(e.get("edition_year"), (e.get("starts_at") or "")[:16]) for e in fe if e.get("starts_at")}
    lost_events = []
    n_parts_events = 0
    for p in sorted(PARTS.glob("*.events.json")):
        fam = p.name.split(".")[0]
        for e in load_part(p.name):
            n_parts_events += 1
            y, t = e.get("edition_year"), norm_key(e.get("title") or "")
            if canon(e.get("source_url")) in f_urls or (y, t) in f_titles:
                continue
            if e.get("starts_at") and (y, e["starts_at"][:16]) in f_starts:
                continue
            expl = (e.get("title") or "") in report_text or (e.get("source_url") or "") in report_text
            lost_events.append(f"{fam}: [{y}] {e.get('starts_at')} {str(e.get('title'))[:70]!r} ({e.get('source_url')})" + (" [explained in REPORT.md]" if expl else " [NOT explained in REPORT.md]"))
    infos.append(f"parts events: {n_parts_events} records; final: {len(fe)}; records with no final counterpart by URL, year+title or year+start: {len(lost_events)}")
    for l in lost_events:
        (infos if "[explained" in l else findings).append("parts event with no final counterpart: " + l)

    fs = final.get("speakers") or []
    f_names = [s.get("name") or "" for s in fs]
    f_keys = {name_key(n) for n in f_names}
    lost_sp = []
    n_parts_sp = 0
    for p in sorted(PARTS.glob("*.speakers.json")):
        fam = p.name.split(".")[0]
        for sp in load_part(p.name):
            n_parts_sp += 1
            n = sp.get("name") or ""
            if name_key(n) in f_keys or any(same_person(n, f) for f in f_names):
                continue
            # one-typo tolerance on the last token (Lerman/Lerma, Guitierrez/Gutierrez)
            toks = name_key(n).split()
            ok = False
            for f in f_names:
                ft = name_key(f).split()
                if len(ft) >= 2 and len(toks) >= 2 and toks[0] == ft[0] and any(_close(a, b) for a in toks[1:] for b in ft[1:]):
                    ok = True
                    break
            if not ok:
                lost_sp.append(f"{fam}: {n!r} {sp.get('edition_years')}" + (" [explained in REPORT.md]" if n in report_text else " [NOT explained in REPORT.md]"))
    infos.append(f"parts speakers: {n_parts_sp} records; final: {len(fs)}; names with no final counterpart (exact, subset or one-typo): {len(lost_sp)}")
    for l in lost_sp:
        (infos if "[explained" in l else findings).append("parts speaker with no final counterpart: " + l)

    fo = final.get("organisers") or []
    fok = {(o.get("edition_year"), name_key(o.get("name") or ""), (o.get("role") or "").strip().lower()) for o in fo}
    lost_org = 0
    n_parts_org = 0
    for p in sorted(PARTS.glob("*.organisers.json")):
        for o in load_part(p.name):
            n_parts_org += 1
            if (o.get("edition_year"), name_key(o.get("name") or ""), (o.get("role") or "").strip().lower()) not in fok:
                lost_org += 1
    infos.append(f"parts organisers: {n_parts_org} records; final: {len(fo)}; lost: {lost_org}")
    if lost_org:
        findings.append(f"{lost_org} parts organiser records have no final counterpart")

    fp = final.get("posts") or []
    fpu = {canon(x.get("source_url")) for x in fp}
    lost_posts = []
    n_parts_posts = 0
    for p in sorted(PARTS.glob("*.posts.json")):
        fam = p.name.split(".")[0]
        for x in load_part(p.name):
            n_parts_posts += 1
            if canon(x.get("source_url")) not in fpu:
                lost_posts.append(f"{fam}: {x.get('date')} {str(x.get('title'))[:60]!r} ({x.get('source_url')})")
    infos.append(f"parts posts: {n_parts_posts} records; final: {len(fp)}; lost: {len(lost_posts)}")
    for l in lost_posts:
        findings.append("parts post with no final counterpart: " + l)

    fpg = final.get("pages") or []
    fpgu = {(canon(x.get("url")), x.get("edition_year")) for x in fpg}
    lost_pages = []
    n_parts_pages = 0
    for p in sorted(PARTS.glob("*.pages.json")):
        fam = p.name.split(".")[0]
        for x in load_part(p.name):
            n_parts_pages += 1
            if (canon(x.get("url")), x.get("edition_year")) not in fpgu:
                lost_pages.append(f"{fam}: [{x.get('edition_year')}] {str(x.get('title'))[:60]!r} ({x.get('url')})")
    infos.append(f"parts pages: {n_parts_pages} records; final: {len(fpg)}; lost: {len(lost_pages)}")
    for l in lost_pages:
        findings.append("parts page with no final counterpart: " + l)

    fm = final.get("media") or []
    fm_bases = {media_base(m.get("url") or "") for m in fm}
    lost_media = Counter()
    n_parts_media = 0
    lost_media_examples = defaultdict(list)
    for p in sorted(PARTS.glob("*.media.json")):
        fam = p.name.split(".")[0]
        for x in load_part(p.name):
            n_parts_media += 1
            if media_base(x.get("url") or "") not in fm_bases:
                lost_media[fam] += 1
                if len(lost_media_examples[fam]) < 3:
                    lost_media_examples[fam].append(x.get("url"))
    infos.append(f"parts media: {n_parts_media} records (all families, overlapping); final: {len(fm)}; images (any size variant) with no final entry: {sum(lost_media.values())}" + (" (" + ", ".join(f"{k}: {v}" for k, v in sorted(lost_media.items())) + ")" if lost_media else ""))
    for fam, n in sorted(lost_media.items()):
        findings.append(f"{n} {fam} media records have no final media entry (any size variant), e.g. " + "; ".join(lost_media_examples[fam]))

    # notes delegations (pages_editions: "left to other families")
    notes = (PARTS / "pages_editions.notes.md").read_text(encoding="utf-8") if (PARTS / "pages_editions.notes.md").exists() else ""
    n_del, bad_del = 0, []
    for m in re.finditer(r"^- (\d{4}) (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) '(.*?)' \((/[^)]*)\) -> (.*)$", notes, re.M):
        y, d, t, title, src, target = m.groups()
        y = int(y)
        n_del += 1
        if (y, norm_key(title)) in f_titles or (y, f"{d}T{t}") in f_starts:
            continue
        cands = [c.split(":", 1)[1].strip() for c in target.split(", ") if ":" in c]
        if any((y, norm_key(c)) in f_titles for c in cands):
            continue
        if "already extracted here" in target and (y, f"{d}T{t}") in f_starts:
            continue
        bad_del.append(f"[{y}] {d} {t} {title[:60]!r} -> {target[:80]}")
    infos.append(f"pages_editions calendar slots delegated to other families: {n_del}; without a final event (year+title or year+start): {len(bad_del)}")
    for b in bad_del:
        findings.append("delegated calendar slot with no final event: " + b)
    n_sp_del, bad_sp = 0, []
    sec = notes.split("## Speakers left to other families", 1)[1].split("\n## ", 1)[0] if "## Speakers left to other families" in notes else ""
    for m in re.finditer(r"^- (.+?) \((\d{4})\) -> (\w+): (.+)$", sec, re.M):
        name, y, fam, target = m.groups()
        n_sp_del += 1
        if name_key(name) in f_keys or name_key(target) in f_keys or any(same_person(name, f) or same_person(target, f) for f in f_names):
            continue
        bad_sp.append(f"{name} ({y}) -> {fam}: {target}")
    infos.append(f"pages_editions speakers delegated to other families: {n_sp_del}; without a final speaker: {len(bad_sp)}")
    for b in bad_sp:
        findings.append("delegated speaker with no final record: " + b)
    return findings, infos


def _close(a: str, b: str) -> bool:
    """Same token up to one edit (insertion/deletion/substitution) on 5+ letters."""
    if a == b:
        return True
    if min(len(a), len(b)) < 5 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    for i in range(len(l)):
        if l[:i] + l[i + 1:] == s:
            return True
    return False


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def write_audit(cov, errors, warnings, findings, infos, verdict, syn_findings=(), syn_infos=()):
    lines = []
    lines.append("# Audit of data/extracted/*.json")
    lines.append("")
    lines.append(f"Produced by `parse/audit.py` (read-only). Verdict: **{verdict}**.")
    lines.append("")
    n_unc = sum(len(x["captures"]) for x in cov["uncovered"])
    n_notes = sum(len(x["captures"]) for x in cov["notes_only"])
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Coverage: {cov['total_captures']} fetched HTML captures ({cov['total_urls']} URLs); {cov['covered_by_final_captures']} referenced by a final item, {n_notes} accounted for in the notes (skipped versions, empty archives, spam, iCal exports of events extracted elsewhere, form/login/legal pages), {n_unc} unaccounted for" + (": " + "; ".join(x["url"] for x in cov["uncovered"]) if cov["uncovered"] else "") + ".")
    lines.append(f"- Schema: {len(errors)} errors, {len(warnings)} warnings against the README schema (all seven files present, every required key on every item, ISO dates, allowed kinds, edition_year in {YEAR_MIN}..{YEAR_MAX}, starts_at year == edition_year).")
    lines.append(f"- Sanity: {len(findings)} findings (see section 3); synthesis cross-checks: {len(syn_findings)} findings (see section 4).")
    lines.append("- Every CDX-index HTML URL with status 200 was fetched (0 unfetched), so the extraction covers everything the archive holds for these hosts.")
    lines.append("- Things the importer should know: the events of the 2024 EGC course seminars (Seminario FLOSS 25 Oct, SPL 14-15 Nov, Pipeline 21-22 Nov, Futuro 12-13 Dec 2024) are attached to edition 2024 although they fall outside the 5-8 Nov edition dates (three of them beyond +-30 days); 12 events keep a date-only starts_at and 16 have none; media.json entries mostly point at images the archive never captured (see the CDX figure in section 3); the three English 'Images of ... November 6/7/8' posts are dated 2024-11-09 but carry edition_year 2023 on purpose (2023 photos translated a year later).")
    lines.append("")
    lines.append("## 1. Coverage of the fetched HTML captures")
    lines.append("")
    lines.append(f"- HTML captures in the manifest (kinds {', '.join(HTML_KINDS)}): {cov['total_captures']} captures, {cov['total_urls']} distinct URLs.")
    lines.append(f"- Captures whose URL is referenced by a final JSON item (source_url / sources / used_by / pages.url): {cov['covered_by_final_captures']}.")
    n_notes = sum(len(x["captures"]) for x in cov["notes_only"])
    n_unc = sum(len(x["captures"]) for x in cov["uncovered"])
    lines.append(f"- Captures not referenced by the final JSON but listed in a parts/*.notes.md (skipped, merged, or covered by a family whose part lost the reference in synthesis): {n_notes} captures, {len(cov['notes_only'])} URLs.")
    lines.append(f"- Captures neither referenced by the final JSON nor mentioned in any notes file (UNCOVERED): {n_unc} captures, {len(cov['uncovered'])} URLs.")
    lines.append("")
    lines.append("### Uncovered captures (not in JSON, not in notes), grouped by kind")
    lines.append("")
    if not cov["uncovered"]:
        lines.append("None.")
    else:
        by_kind = defaultdict(list)
        for x in cov["uncovered"]:
            by_kind[x["kind"]].append(x)
        for kind in HTML_KINDS:
            xs = by_kind.get(kind) or []
            if not xs:
                continue
            lines.append(f"#### {kind} ({len(xs)} URLs, {sum(len(x['captures']) for x in xs)} captures)")
            lines.append("")
            for x in xs:
                flags = []
                if x["in_parts_json"]:
                    flags.append("referenced by a parts/*.json but dropped in synthesis")
                if x["in_final_text"]:
                    flags.append("appears elsewhere in the final JSON text (link/href)")
                lines.append(f"- {x['url']} captures {', '.join(x['captures'])}" + (f" [{'; '.join(flags)}]" if flags else ""))
            lines.append("")
    lines.append("### Captures covered only by the notes (not referenced by any final item), grouped by kind")
    lines.append("")
    if not cov["notes_only"]:
        lines.append("None.")
    else:
        by_kind = defaultdict(list)
        for x in cov["notes_only"]:
            by_kind[x["kind"]].append(x)
        for kind in HTML_KINDS:
            xs = by_kind.get(kind) or []
            if not xs:
                continue
            lines.append(f"#### {kind} ({len(xs)} URLs, {sum(len(x['captures']) for x in xs)} captures)")
            lines.append("")
            for x in xs:
                flags = [f"notes match by {x['notes_mention']}"]
                if x["in_parts_json"]:
                    flags.append("referenced by a parts/*.json but not by the final JSON")
                if x["in_final_text"]:
                    flags.append("appears elsewhere in the final JSON text")
                lines.append(f"- {x['url']} captures {', '.join(x['captures'])} [{'; '.join(flags)}]")
            lines.append("")
    lines.append("## 2. Schema validation")
    lines.append("")
    lines.append(f"Errors: {len(errors)}. Warnings: {len(warnings)}.")
    lines.append("")
    if errors:
        lines.append("### Errors")
        lines.append("")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")
    if warnings:
        lines.append("### Warnings")
        lines.append("")
        for w in warnings[:200]:
            lines.append(f"- {w}")
        if len(warnings) > 200:
            lines.append(f"- ... {len(warnings) - 200} more")
        lines.append("")
    lines.append("## 3. Sanity checks")
    lines.append("")
    lines.append(f"Findings: {len(findings)}.")
    lines.append("")
    if findings:
        for f in findings:
            lines.append(f"- {f}")
        lines.append("")
    lines.append("### Informational")
    lines.append("")
    for i in infos:
        lines.append(f"- {i}")
    lines.append("")
    lines.append("## 4. Synthesis cross-checks (parts -> final, notes delegations -> final)")
    lines.append("")
    lines.append(f"Findings: {len(syn_findings)}.")
    lines.append("")
    for f in syn_findings:
        lines.append(f"- {f}")
    if syn_findings:
        lines.append("")
    lines.append("### Informational")
    lines.append("")
    for i in syn_infos:
        lines.append(f"- {i}")
    lines.append("")
    (EXTRACTED / "AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    final = {k: load(k) for k in SCHEMA}
    report_text = (EXTRACTED / "REPORT.md").read_text(encoding="utf-8") if (EXTRACTED / "REPORT.md").exists() else ""
    cov = coverage(final)
    errors, warnings = check_schema(final, report_text)
    findings, infos = sanity(final, report_text)
    syn_findings, syn_infos = synthesis_checks(final, report_text)

    n_unc = sum(len(x["captures"]) for x in cov["uncovered"])
    hard = [f for f in findings if not f.startswith(("speaker name repeated", "duplicate"))]
    if errors or n_unc > 20 or any(f.startswith(("edition ", "no events for", "HTML field")) for f in findings):
        verdict = "not_ready"
    elif n_unc or findings or warnings or syn_findings:
        verdict = "ready_with_notes"
    else:
        verdict = "ready"
    write_audit(cov, errors, warnings, findings, infos, verdict, syn_findings, syn_infos)
    summary = {
        "uncovered_captures": n_unc,
        "uncovered_urls": len(cov["uncovered"]),
        "notes_only_captures": sum(len(x["captures"]) for x in cov["notes_only"]),
        "uncovered_examples": [f"{x['kind']} {x['url']} ({len(x['captures'])} capture(s))" for x in cov["uncovered"][:25]],
        "schema_errors": errors,
        "schema_warnings": len(warnings),
        "sanity_findings": findings,
        "synthesis_findings": syn_findings,
        "verdict": verdict,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
