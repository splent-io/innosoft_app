"""People family: speakers and organising teams.

Scope (see notes file for the capture list):
- /ponentes-xi-edicion/ (XI edition, 2023): schedule table with speakers,
  talk, time, room and a "Más info" link.
- "Información sobre la ponencia ..." pages of the X edition (2022): one page
  per talk, content = infographic cards (images); speaker name from the
  title, company from the MEC event that embeds the page (JSON-LD in the
  /x-edicion/ page and in the /events/charla-* captures).
- /manuel-jesus-flores-montano/ (attachment page used as speaker page, 2022).
- the two 2023 posts "Información sobre la ponencia ..." (posters only,
  speakers come from the XI table that links them).
- /etn_category/ponente/ (Eventin listing of the XII edition talks, 2024):
  speaker names, excerpts and photos.
- /organizacion-{ix,xi,xii}-edicion/ and /en/xii-edition-organization/:
  organising teams (roles + names).
- kind=speaker captures with no data (taxonomy pages, spam forum topic, css)
  are listed as skipped.

Outputs data/extracted/parts/people.{speakers,organisers,events}.json and
people.notes.md. Deterministic, no network.
"""

from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from parse.common import (  # noqa: E402
    EXTRACTED, capture_year, clean_html, dump_part, edition_number_for_year,
    fix_lazy_images, manifest_rows, name_key, name_phrase_in_text, norm_url,
    parse_spanish_date, parse_time, read_html, same_person, soup_of,
    survey_rows, text_of, unwrap_nested_figures,
)

FAMILY = "people"
SITE = "https://www.innosoftdays.com"

# URLs (normalised, without query string) that belong to this family. The
# regex covers the explicit scope plus the speaker pages that live under a
# company slug (their title is "Información sobre la ponencia ...").
SCOPE_URL_RE = re.compile(
    r"^https://www\.innosoftdays\.com/("
    r"ponentes-xi-edicion|etn-speaker-category(/[a-z-]+)?|etn_category/ponente|"
    r"en/xii-edition-organization|organizacion-[a-z]+-edicion|"
    r"carlos-perez|libnamic|maria-jose-escalona|prise|red-hat|tragsatec|manuel-jesus-flores-montano|"
    r"informacion-sobre-la-ponencia[a-z0-9-]*(/embed)?|"
    r"2023/10/30/informacion-sobre-la-ponencia[a-z0-9-]*"
    r")/$"
)

# Small, documented corrections (typos in the source, facts read from the
# raw uploads that the parser cannot OCR).
NAME_ALIASES = {
    "Israel Blancas Álvares": "Israel Blancas Álvarez",   # slug typo, /red-hat/ spells it right
}
COMPANY_ALIASES = {
    "CoverMananger": "CoverManager",
    "MapTools Project Manager": "MapTool",
    "Pandora": "Ártica (Pandora FMS)",
}
# Position read by hand from the infographic card of the only 2022 speaker
# page whose images were fetched (uploads/2022/11/1-22.png: "CEO y fundador
# de Ártica").
SPEAKER_FACTS = {
    "https://www.innosoftdays.com/informacion-sobre-la-ponencia-del-sr/": {
        "affiliation": "Ártica (Pandora FMS)", "position": "CEO y fundador"},
}
# XI table cells whose "name, role" text is too irregular for the generic
# splitter (exact cell text -> list of (name, position)).
XI_CELL_OVERRIDES = {
    "Soraya Peceño, Ingeniera con 15 años de experiencia, Carlos Müller, Profesor de la ETSII, Isabel y Mathew galardonados con el premio nacional al mejor TFG": [
        ("Soraya Peceño", "Ingeniera con 15 años de experiencia"),
        ("Carlos Müller", "Profesor de la ETSII"),
    ],
}
# Eventin listing (2024) titles -> people. Titles mix company prefixes and
# first names; only entries with a full personal name become speakers.
ETN_TITLE_OVERRIDES = {
    "Jose Luis Fontenla y María Mendoza": [
        ("Jose Luis Fontenla", "Rewoox", "CTO"),
        ("María Mendoza", "Rewoox", "Directora de Innovación"),
    ],
    "VOLUM: Pablo Pérez y Alberto Olmo": [
        ("Pablo Pérez", "Universidad de Sevilla", "Profesor (proyecto de investigación VOLUM)"),
        ("Alberto Olmo", "Universidad de Sevilla", "Profesor (proyecto de investigación VOLUM)"),
    ],
    "Raul López García": [("Raul López García", "NTT Data", "Digital Transformation Executive")],
    "Jose Antonio Pérez": [("Jose Antonio Pérez", None, "Psicólogo especialista en gestión de emociones")],
    "Rafael M Guitart": [("Rafael M Guitart", None, "Profesor, informático (ICTS-Doñana)")],
    "Irene M Morgado": [("Irene M Morgado", None, "Experta en perfiles informáticos")],
    "Sol y Ciberseguridad: Anabel Carmona Gutiérrez": [("Anabel Carmona Gutiérrez", None, None)],
    "Emprendimiento: Javier María de Domingo Morales": [("Javier María de Domingo Morales", None, None)],
    "RRHH: NttData": [],          # no person named
    "4i.ai: Andrés y Adolfo": [],  # first names only
}

ORG_YEAR_BY_ROMAN = {"ix": 2021, "x": 2022, "xi": 2023, "xii": 2024, "xiii": 2025}


# ---------------------------------------------------------------- utilities

def base_url(u: str) -> str:
    return u.split("?")[0]


def entry_content(soup):
    node = soup.select_one(".entry-content") or soup.select_one("article .entry-content") or soup.select_one("article")
    if node is not None:
        fix_lazy_images(node)
    return node


def page_h1(soup) -> str:
    h = soup.select_one("h1.entry-title") or soup.select_one("h1")
    t = text_of(h)
    if not t:
        t = text_of(soup.title).split(" - InnoSoft")[0]
    return t.replace("“", '"').replace("”", '"').strip()


def names_from_ponencia_title(title: str) -> list[str]:
    """'Información sobre la ponencia del Sr. X' -> ['X'];
    '... de los Srs. X y Y' -> ['X', 'Y']. [] when the title names no one."""
    m = re.search(r"ponencia\s+(?:del?\s+(?:la\s+)?|de\s+los\s+)?(?:Sr\.|Sra\.|Srs\.)\s*(.+)$", title, re.I)
    if not m:
        return []
    rest = m.group(1).strip().rstrip(".")
    if " y " in rest:
        return [p.strip() for p in rest.split(" y ") if p.strip()]
    return [rest]


def looks_like_name(segment: str) -> bool:
    """'Carlos Pérez y José Ignacio Morales' yes; 'diseñadora UX/UI' no."""
    words = segment.split()
    if not words:
        return False
    for w in words:
        if w.lower() in ("y", "e", "de", "del", "la", "los", "las"):
            continue
        if not w[0].isupper() or (len(w) > 2 and w.isupper()):
            return False
    return True


def split_names_and_role(cell: str) -> list[tuple[str, str | None]]:
    """XI table cell 'A, B y C, role' / 'A, role' / '– A, role\n– B, role'.
    Leading comma-separated segments that look like names are the people,
    the rest of the segments form the shared position."""
    cell = cell.replace("\u200b", "").strip()
    if cell in XI_CELL_OVERRIDES:
        return XI_CELL_OVERRIDES[cell]
    out = []
    lines = [l.strip(" –-\t") for l in re.split(r"\n|(?:^|\s)–\s", cell) if l.strip(" –-\t")]
    for line in lines:
        parts = [p.strip() for p in line.split(",") if p.strip()]
        name_parts = []
        while parts and looks_like_name(parts[0]):
            name_parts.append(parts.pop(0))
        if not name_parts:
            continue
        role = ", ".join(parts).strip() or None
        for seg in name_parts:
            for n in re.split(r"\s+y\s+", seg):
                if n.strip():
                    out.append((n.strip(), role))
    return out


def talk_kind(title: str) -> str:
    t = title.lower()
    if t.startswith("taller"):
        return "workshop"
    return "talk"


# ------------------------------------------------------------ cross sources

def embed_map(rows: list[dict]) -> dict[str, dict]:
    """speaker page URL -> {'event': name, 'date': 'YYYY-MM-DD'} from the
    MEC JSON-LD Event objects of the /x-edicion/ page and the /events/*
    captures whose description embeds the speaker page."""
    out: dict[str, dict] = {}
    cands = [r for r in rows if r["url"] == SITE + "/x-edicion/" or r["kind"] == "event"]
    for r in sorted(cands, key=lambda r: r["timestamp"]):
        html = read_html(r)
        if "[embed]" not in html:
            continue
        for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S):
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            items = data if isinstance(data, list) else [data]
            for it in items:
                if not isinstance(it, dict) or it.get("@type") != "Event":
                    continue
                m = re.search(r"\[embed\](.*?)\[/embed\]", it.get("description") or "")
                if not m:
                    continue
                url = norm_url(m.group(1).replace("&amp;", "&")).rstrip("/") + "/"
                out.setdefault(url, {"event": it.get("name") or "", "date": (it.get("startDate") or "")[:10], "source": r["url"]})
    return out


def company_from_event_name(name: str) -> str | None:
    m = re.match(r"Charla de (.+)$", name or "")
    if not m:
        return None
    c = m.group(1).strip()
    if re.match(r"(la\s+)?(Sra?\.|Srs\.)|del\s+Sr\.|Mesa Redonda|cl[aá]usura", c, re.I):
        return None
    return COMPANY_ALIASES.get(c, c)


def load_other_parts() -> tuple[list[dict], list[dict]]:
    """Speakers and events written by the other families (if present)."""
    speakers, events = [], []
    parts = EXTRACTED / "parts"
    if parts.exists():
        for p in sorted(parts.glob("*.speakers.json")):
            if p.name.startswith(FAMILY + "."):
                continue
            try:
                speakers += json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        for p in sorted(parts.glob("*.events.json")):
            if p.name.startswith(FAMILY + "."):
                continue
            try:
                events += json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
    return speakers, events


def split_people(text: str) -> list[str]:
    return [p.strip() for p in re.split(r",|\s+y\s+|;|/", text or "") if p.strip()]


def cross_years(name: str, survey_index: list[tuple[str, dict]], other_speakers, other_events, year_cache: dict) -> set[int]:
    years: set[int] = set()
    if len(name_key(name).split()) < 2:
        return years
    for text, row in survey_index:
        if name_phrase_in_text(name, text):
            if row["url"] not in year_cache:
                year_cache[row["url"]] = capture_year(row)
            y = year_cache[row["url"]]
            if y:
                years.add(y)
    for s in other_speakers:
        if same_person(name, s.get("name", "")):
            years.update(int(y) for y in (s.get("edition_years") or []))
    for e in other_events:
        if e.get("edition_year") and any(same_person(name, p) for p in split_people(e.get("speaker") or "")):
            years.add(int(e["edition_year"]))
    return {y for y in years if 2013 <= y <= 2025}


# --------------------------------------------------------------- extractors

def extract_xi_ponentes(row: dict, rows_by_url: dict) -> tuple[list[dict], list[dict], list[str]]:
    """Speakers and events from the XI edition schedule table."""
    soup = soup_of(row)
    content = entry_content(soup)
    speakers, events, notes = [], [], []
    current_date = None
    for el in content.find_all(["h2", "h3", "h4", "table"]):
        if el.name != "table":
            d = parse_spanish_date(text_of(el))
            if d:
                current_date = d
            continue
        for tr in el.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 4:
                continue
            first = text_of(cells[0])
            if re.match(r"Ponen?e?te", first, re.I) or first.lower().startswith("ponente"):
                continue  # header row
            who = cells[0].get_text("\n", strip=True)
            title = text_of(cells[1]).replace("​", "").strip()
            start, end = parse_time(text_of(cells[2]))
            room = text_of(cells[3]) or None
            link_el = cells[4].find("a", href=True) if len(cells) > 4 else None
            link = norm_url(link_el["href"]) if link_el else None
            people = split_names_and_role(who)
            year = current_date.year if current_date else 2023
            # poster / bio from the linked "Más info" post when captured
            poster, bio_html, link_row = None, "", None
            if link and link in rows_by_url:
                link_row = rows_by_url[link]
                lc = entry_content(soup_of(link_row))
                bio_html = unwrap_nested_figures(clean_html(lc))
                img = lc.find("img") if lc else None
                if img is not None and img.get("src"):
                    poster = norm_url(img["src"])
            for name, position in people:
                speakers.append({
                    "name": name,
                    "affiliation": None,
                    "position": position,
                    "bio_html": bio_html,
                    "photo_url": None,
                    "links": [{"label": "Más info", "url": link}] if link else [],
                    "edition_years": [year],
                    "source_url": row["url"],
                    "source_timestamp": row["timestamp"],
                    "_talk": title,
                })
            events.append({
                "edition_year": year,
                "title": title,
                "kind": talk_kind(title),
                "starts_at": f"{current_date.isoformat()}T{start}:00" if current_date and start else (current_date.isoformat() if current_date else None),
                "ends_at": f"{current_date.isoformat()}T{end}:00" if current_date and end else None,
                "room": room,
                "modality": "in_person",
                "speaker": ", ".join(n for n, _ in people) or None,
                "company": None,
                "summary": None,
                "description_html": bio_html or None,
                "poster_url": poster,
                "link": link,
                "lang": "es",
                "source_url": row["url"],
                "source_timestamp": row["timestamp"],
            })
    return speakers, events, notes


def extract_ponencia_page(row: dict, embeds: dict) -> list[dict]:
    """One 2022 'Información sobre la ponencia ...' page (or the attachment
    page of Manuel Jesús Flores Montaño) -> speaker records."""
    soup = soup_of(row)
    h1 = page_h1(soup)
    names = names_from_ponencia_title(h1)
    if not names and row["url"].endswith("/manuel-jesus-flores-montano/"):
        names = ["Manuel Jesús Flores Montaño"]
    content = entry_content(soup)
    bio_html = unwrap_nested_figures(clean_html(content))
    emb = embeds.get(row["url"], {})
    company = company_from_event_name(emb.get("event", ""))
    year = int(emb["date"][:4]) if emb.get("date") else None
    facts = SPEAKER_FACTS.get(row["url"], {})
    out = []
    for n in names:
        n = NAME_ALIASES.get(n, n)
        photo = None
        if row["url"].endswith("/manuel-jesus-flores-montano/"):
            a = content.find("a", href=True) if content else None
            img = content.find("img") if content else None
            photo = norm_url(a["href"]) if a and re.search(r"\.(png|jpe?g|webp)$", a["href"], re.I) else (norm_url(img["src"]) if img else None)
        out.append({
            "name": n,
            "affiliation": facts.get("affiliation") or company,
            "position": facts.get("position"),
            "bio_html": bio_html,
            "photo_url": photo,
            "links": [],
            "edition_years": [year] if year else [],
            "source_url": row["url"],
            "source_timestamp": row["timestamp"],
            "_talk": emb.get("event"),
        })
    return out


def extract_etn_listing(row: dict) -> list[dict]:
    soup = soup_of(row)
    out = []
    for art in soup.find_all("article"):
        fix_lazy_images(art)
        h = art.find(["h2", "h3"])
        title = text_of(h)
        link = h.find("a", href=True) if h else None
        link = norm_url(link["href"]) if link else None
        img = art.find("img")
        photo = norm_url(img["src"]) if img is not None and img.get("src") and not img["src"].startswith("data:") else None
        excerpt = art.select_one(".ast-excerpt-container")
        bio = clean_html(excerpt) if excerpt else ""
        people = ETN_TITLE_OVERRIDES.get(title)
        if people is None:
            n = title.split(":", 1)[-1].strip()
            people = [(p.strip(), None, None) for p in re.split(r"\s+y\s+", n)] if len(name_key(n).split()) >= 2 else []
        for name, aff, pos in people:
            out.append({
                "name": name,
                "affiliation": aff,
                "position": pos,
                "bio_html": bio,
                "photo_url": photo,
                "links": [{"label": "Evento", "url": link}] if link else [],
                "edition_years": [2024],
                "source_url": row["url"],
                "source_timestamp": row["timestamp"],
                "_talk": title,
            })
    return out


def extract_organisation(row: dict, year: int) -> tuple[list[dict], str]:
    """(role heading + <ul> of names) pairs -> organiser rows; roles of a
    person listed several times are merged with ' / '."""
    soup = soup_of(row)
    content = entry_content(soup)
    roles: "OrderedDict[str, list[str]]" = OrderedDict()
    current = None
    for el in content.find_all(["p", "h2", "h3", "h4", "ul", "strong"]):
        if el.name == "ul":
            if not current:
                continue
            for li in el.find_all("li"):
                n = re.sub(r"\s+", " ", text_of(li)).strip()
                if not n or len(name_key(n).split()) < 2 or re.search(r"\d|\.\w|^[a-z]", n) or " " not in n:
                    continue  # usernames such as 'santizdr', 'peperez.17', 'bogdan.stefan'
                roles.setdefault(n, [])
                role = current
                if role not in roles[n]:
                    roles[n].append(role)
        elif el.name in ("p", "h2", "h3", "h4", "strong"):
            if el.name == "strong" and el.find_parent(["p", "h2", "h3", "h4"]) is not None:
                continue
            t = text_of(el).strip().rstrip(":").strip()
            if not t or len(t) > 60 or el.find("ul"):
                continue
            if re.search(r"organizad[ao]s por|organized by|Organizaci[oó]n\s+[XVI]+|Edition Organization|DIFERENTES COMIT|DIFFERENT COMMITTEES", t, re.I):
                current = None if re.search(r"COMIT|organizad|organized", t, re.I) else current
                continue
            if re.match(r"(Miembros? de|.* Committee Members?)", t, re.I):
                m = re.match(r"Miembros? de (.+)", t, re.I)
                t = ("Miembro de " + m.group(1)) if m else re.sub(r"\s*Committee Members?$", " committee member", t)
            current = t
    out = [{"edition_year": year, "name": n, "role": " / ".join(rs), "photo_url": None,
            "source_url": row["url"], "source_timestamp": row["timestamp"]} for n, rs in roles.items()]
    return out, ""


# -------------------------------------------------------------------- main

def main() -> None:
    all_rows = manifest_rows()
    survey = {(norm_url(s["url"]), s["timestamp"]): s for s in survey_rows()}
    rows_by_url = {}
    for r in sorted(all_rows, key=lambda r: r["timestamp"]):
        rows_by_url[r["url"]] = r  # latest capture per URL

    in_scope = [r for r in all_rows if r["kind"] == "speaker" or SCOPE_URL_RE.match(base_url(r["url"]))]
    in_scope.sort(key=lambda r: (r["url"], r["timestamp"]))

    embeds = embed_map(all_rows)
    other_speakers, other_events = load_other_parts()
    survey_index = [((s.get("title") or "") + " " + (s.get("h1") or ""), r)
                    for r in all_rows if r["kind"] in ("post", "event")
                    for s in [survey.get((r["url"], r["timestamp"]), {})]]
    year_cache: dict = {}

    speakers: list[dict] = []
    organisers: list[dict] = []
    events: list[dict] = []
    covered: list[tuple[dict, str]] = []   # (row, what)
    skipped: list[tuple[dict, str]] = []

    # group captures by base URL, decide per URL
    by_url: dict[str, list[dict]] = defaultdict(list)
    for r in in_scope:
        by_url[base_url(r["url"])].append(r)

    for url, versions in sorted(by_url.items()):
        versions.sort(key=lambda r: r["timestamp"])
        latest = versions[-1]
        # non-canonical duplicates: query strings, /embed/
        dupes = [r for r in versions if r["url"] != url]
        for r in dupes:
            skipped.append((r, "query-string duplicate of " + url))
        canonical = [r for r in versions if r["url"] == url]
        if not canonical:
            continue
        latest = canonical[-1]
        older = canonical[:-1]

        if url.endswith("/embed/"):
            for r in canonical:
                skipped.append((r, "WordPress oEmbed stub of " + url[:-len("embed/")]))
            continue
        if url.endswith(".css") or "/forums/" in url:
            for r in canonical:
                skipped.append((r, "not a people page (asset / bbPress spam topic wrongly classified as kind=speaker)"))
            continue
        if url.startswith(SITE + "/etn-speaker-category"):
            for r in canonical:
                skipped.append((r, "Eventin speaker taxonomy archive with no entries (only term names / 'nothing found')"))
            continue

        if url == SITE + "/ponentes-xi-edicion/":
            sp, ev, _ = extract_xi_ponentes(latest, rows_by_url)
            speakers += sp
            events += ev
            covered.append((latest, f"XI schedule table: {len(sp)} speakers, {len(ev)} talks"))
            for r in older:
                skipped.append((r, "older version, identical content to " + latest["timestamp"]))
            continue

        if url == SITE + "/etn_category/ponente/":
            sp = extract_etn_listing(latest)
            speakers += sp
            covered.append((latest, f"Eventin 'Ponente' listing (page 1 of 2): {len(sp)} speakers"))
            continue

        m = re.search(r"/organizacion-([a-z]+)-edicion/$", url) or re.search(r"/en/([a-z]+)-edition-organization/$", url)
        if m:
            year = ORG_YEAR_BY_ROMAN.get(m.group(1))
            if "/en/" in url:
                skipped.append((latest, "English translation of /organizacion-xii-edicion/ (same names, roles in English)"))
                continue
            org, _ = extract_organisation(latest, year)
            if not org:
                skipped.append((latest, "placeholder page, no team listed ('aún no están disponibles')"))
                continue
            organisers += org
            covered.append((latest, f"organising team {year}: {len(org)} people"))
            for r in older:
                skipped.append((r, "older version, same names as " + latest["timestamp"]))
            continue

        if re.search(r"/2023/10/30/informacion-sobre-la-ponencia", url):
            covered.append((latest, "2023 talk poster post; speakers taken from the XI table row linking it"))
            continue

        # X edition speaker pages (and the attachment page). The title of a
        # page may change between captures (/libnamic/ lost its "Información
        # sobre la ponencia del Sr. Jesús Bocanegra" title in 2025), so names
        # are taken from any version and content from the newest non-empty one.
        sp = extract_ponencia_page(latest, embeds)
        if not sp:
            for r in reversed(older):
                alt = extract_ponencia_page(r, embeds)
                if alt:
                    for a in alt:
                        a["bio_html"] = a["bio_html"] or unwrap_nested_figures(clean_html(entry_content(soup_of(latest))))
                    sp = alt
                    covered.append((r, "title names the speaker (newer capture lost the title)"))
                    older = [o for o in older if o is not r]
                    break
        if not sp:
            skipped.append((latest, "no speaker name in title"))
            continue
        for r in older:
            skipped.append((r, "older version of the same page (same cards, smaller thumbnails)"))
        speakers += sp
        covered.append((latest, f"speaker page: {', '.join(s['name'] for s in sp)}"))

    # ------------------------------------------------------------ dedupe
    merged: "OrderedDict[str, dict]" = OrderedDict()
    for s in speakers:
        k = name_key(s["name"])
        if k in merged:
            m = merged[k]
            for f in ("affiliation", "position", "photo_url"):
                if not m.get(f) and s.get(f):
                    m[f] = s[f]
            if not m.get("bio_html") and s.get("bio_html"):
                m["bio_html"] = s["bio_html"]
                m["source_url"], m["source_timestamp"] = s["source_url"], s["source_timestamp"]
            for l in s["links"]:
                if l not in m["links"]:
                    m["links"].append(l)
            m["edition_years"] = sorted(set(m["edition_years"]) | set(s["edition_years"]))
            m["_talks"] = sorted(set(m.get("_talks", [])) | ({s["_talk"]} if s.get("_talk") else set()))
            m["_sources"] = sorted(set(m.get("_sources", [])) | {s["source_url"]})
        else:
            s = dict(s)
            s["_talks"] = [s.pop("_talk")] if s.get("_talk") else []
            s.pop("_talk", None)
            s["_sources"] = [s["source_url"]]
            merged[k] = s

    # ------------------------------------------------- cross-check years
    cross_report = []
    for s in merged.values():
        extra = cross_years(s["name"], survey_index, other_speakers, other_events, year_cache)
        own = set(s["edition_years"])
        added = sorted(extra - own)
        s["edition_years"] = sorted(own | extra)
        if added:
            cross_report.append((s["name"], sorted(own), added))

    final_speakers = []
    talks_by_name = {}
    for s in merged.values():
        talks_by_name[s["name"]] = (s.pop("_talks"), s.pop("_sources"))
        final_speakers.append(s)

    # dedupe organisers on (year, name)
    org_seen = {}
    for o in organisers:
        k = (o["edition_year"], name_key(o["name"]))
        if k in org_seen:
            if o["role"] not in org_seen[k]["role"]:
                org_seen[k]["role"] += " / " + o["role"]
            # keep the best spelt variant ('Rocío López Moyano' over 'Rocio ...',
            # 'María de la Salud ...' over 'María Salud ...')
            if (len(o["name"]) - len(o["name"].encode("ascii", "ignore")), len(o["name"])) > \
               (len(org_seen[k]["name"]) - len(org_seen[k]["name"].encode("ascii", "ignore")), len(org_seen[k]["name"])):
                org_seen[k]["name"] = o["name"]
        else:
            org_seen[k] = o
    final_org = list(org_seen.values())

    dump_part(f"{FAMILY}.speakers.json", final_speakers)
    dump_part(f"{FAMILY}.organisers.json", final_org)
    dump_part(f"{FAMILY}.events.json", events)
    write_notes(in_scope, covered, skipped, final_speakers, final_org, events, talks_by_name, cross_report, embeds)
    print(f"captures in scope {len(in_scope)}, covered {len(covered)}, skipped {len(skipped)}; "
          f"speakers {len(final_speakers)}, organisers {len(final_org)}, events {len(events)}")


def write_notes(in_scope, covered, skipped, speakers, organisers, events, talks_by_name, cross_report, embeds) -> None:
    L = []
    L.append("# people family notes\n")
    L.append("Parser: parse/people.py. Sources: WordPress pages that describe people "
             "(speaker info pages of the X edition, the XI schedule table, the Eventin "
             "'Ponente' listing of the XII edition and the organising-team pages).\n")
    L.append(f"Captures in scope: {len(in_scope)} (kind=speaker plus URL patterns of the scope). "
             f"Extracted from {len(covered)}, skipped {len(skipped)} (all listed below).\n")
    L.append("## Outputs\n")
    L.append(f"- people.speakers.json: {len(speakers)} speakers (deduplicated by accent-insensitive name).")
    L.append(f"- people.organisers.json: {len(organisers)} organiser rows (one per edition_year + name, roles merged with ' / ').")
    L.append(f"- people.events.json: {len(events)} talks of the XI edition (2023) taken from the schedule table "
             "of /ponentes-xi-edicion/ (times and rooms are only there; the posts family has the same talks "
             "without times, dedupe on edition_year + title).\n")

    def cnt(items, key):
        c = defaultdict(int)
        for it in items:
            for y in (it[key] if isinstance(it[key], list) else [it[key]]):
                c[y] += 1
        return dict(sorted(c.items()))
    L.append("## Per-year counts\n")
    L.append(f"- speakers by edition_year (a speaker counts in every year): {cnt(speakers, 'edition_years')}")
    L.append(f"- speakers with no edition year: {sum(1 for s in speakers if not s['edition_years'])}")
    L.append(f"- organisers by edition_year: {cnt(organisers, 'edition_year')}")
    L.append(f"- events by edition_year: {cnt(events, 'edition_year')}\n")

    L.append("## Covered captures\n")
    for r, what in sorted(covered, key=lambda x: (x[0]['url'], x[0]['timestamp'])):
        L.append(f"- {r['timestamp']} {r['url']} : {what}")
    L.append("\n## Skipped captures (with reason)\n")
    for r, why in sorted(skipped, key=lambda x: (x[0]['url'], x[0]['timestamp'])):
        L.append(f"- {r['timestamp']} {r['url']} : {why}")

    L.append("\n## Speakers extracted\n")
    L.append("| name | affiliation | position | years | talk(s) | sources |")
    L.append("|---|---|---|---|---|---|")
    for s in speakers:
        talks, srcs = talks_by_name.get(s["name"], ([], []))
        L.append(f"| {s['name']} | {s.get('affiliation') or ''} | {s.get('position') or ''} | {','.join(map(str, s['edition_years']))} | {'; '.join(talks)} | {' '.join(srcs)} |")

    L.append("\n## Edition years added by cross-checking posts/events captures and other families' parts\n")
    if cross_report:
        for name, own, added in cross_report:
            L.append(f"- {name}: own {own} + {added}")
    else:
        L.append("- none")

    L.append("\n## Oddities and decisions\n")
    L.extend([
        "- The X edition (2022) speaker pages contain only infographic cards (PNG images, 2 or 3 per page: portrait+title, talk, date). "
        "The text of the cards is not in the HTML, so bio_html keeps the images (original URLs) and affiliation comes from the MEC event "
        "that embeds each page ('Charla de <company>' in the JSON-LD of /x-edicion/ and /events/charla-*). Only Sancho Lerena's cards were "
        "fetched (uploads/2022/11/1-22.png ...); his position was read from the image by hand ('CEO y fundador de Ártica').",
        "- Not fetched by the collector, so no cards to read for the other 2022 speakers: uploads/2022/11/1-7, 1-18, 1-20, 1-1, ACCENTURE, deloitte(only html), 1-17, 1-15, 1-14, 1-16, 1-8, 1-10, 1-11, 1-12.png.",
        "- 'Israel Blancas Álvares' (slug typo of /informacion-sobre-la-ponencia-del-sr-israel-blancas-alvares/) and 'Israel Blancas Álvarez' (/red-hat/) are the same Red Hat speaker; merged under the correct spelling.",
        "- 'Frank \"Azhrei\" Edwars' is kept as written on the site (real name Frank Edwards, MapTool project). 'CoverMananger' normalised to CoverManager, 'Pandora' to 'Ártica (Pandora FMS)'.",
        "- /manuel-jesus-flores-montano/ is an attachment page (image uploaded 2021/10) that the 2022 MEC event 'Charla del Sr. Manuel Jesús Flores Montaño' (2022-11-11) embeds; the image is used as photo_url.",
        "- The two 2023 posts 'Información sobre la ponencia ...' hold only a poster; their speakers come from the XI table row that links them and the poster becomes bio_html/description.",
        "- XI table cell 'Soraya Peceño, Ingeniera ..., Carlos Müller, Profesor de la ETSII, Isabel y Mathew galardonados ...' is split by an explicit override; 'Isabel' and 'Mathew' (no surname there) are not emitted from this family (posts family has Isabel Arrans Vega and Matthew Bwye Lera).",
        "- Eventin listing /etn_category/ponente/ is page 1 of 2 (page 2 not captured). Titles mixing company and first names ('4i.ai: Andrés y Adolfo', 'RRHH: NttData') produce no speaker. Affiliation/position for those rows come from the excerpt text (see ETN_TITLE_OVERRIDES).",
        "- /en/xii-edition-organization/ is the English copy of /organizacion-xii-edicion/ (same 182 list entries, 157 distinct people); Spanish roles are kept. /organizacion-ix-edicion/ is a placeholder ('aún no están disponibles'). Both XI organisation captures list the same 160 names.",
        "- Organisation lists contain usernames ('santizdr', 'peperez.17', 'bogdan.stefan'); entries with fewer than two name tokens, digits, dotted handles or a lowercase start are dropped.",
        "- 'Daniel García' (PRiSE, 2021 and 2022) and 'Daniel García Moreno' (SUSE, 2022, page not captured) are different people; the two-token name makes the year cross-check accept any 'Daniel García' title, so his years may include a SUSE talk.",
        "- Sources of edition years: XI table headings (2023), MEC JSON-LD dates (2022), Eventin listing (2024), plus cross-check by name over post/event capture titles (year from post URL, JSON-LD startDate, Eventin 'Date :', published meta) and over the other families' speakers/events parts when present.",
        "- /informacion-sobre-la-ponencia-de-la-sra-maria-del-carmen-romero-ternero/ is embedded by no captured MEC event (the 2022 round table event points at a preview URL), so her 2022 comes only from the cross-check (posts_2022 names her as Directora de la ETSII).",
        "- photo_url of the 2024 Eventin rows is the event's featured image, which is a portrait for most speakers but a poster/screenshot for Rewoox (Fontenla, Mendoza) and VOLUM (Pérez, Olmo).",
        f"- MEC embed map resolved {len(embeds)} speaker-page URLs to a dated 2022 talk.",
    ])
    (EXTRACTED / "parts").mkdir(parents=True, exist_ok=True)
    (EXTRACTED / "parts" / f"{FAMILY}.notes.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
