"""posts_2021: the blog posts of InnoSoft Days IX (2021, cybersecurity edition).

Scope: every capture of kind=post whose URL date is in 2021 (32 URLs, 51
captures). The site published one announcement post per talk (title,
speaker, bio, date/time/room, Eventbrite + Twitch links) and, after the
talk, a "[RESUMEN]" post with the write-up. This parser writes:

- posts.json      one row per URL (latest capture; content is identical across versions)
- events.json     one row per talk, announcement + resumen merged
- speakers.json   one row per named speaker
- editions.json   the 2021 edition, derived from the posts

Deterministic, no network. Run: .venv/bin/python parse/posts_2021.py
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import *  # noqa: E402,F401,F403

FAMILY = "posts_2021"
YEAR = 2021
PARTS = EXTRACTED / "parts"
MADRID = ZoneInfo("Europe/Madrid")

# ---------------------------------------------------------------------------
# Curated facts that the prose does not state in a machine-readable way.
# Keyed by the announcement post slug. Every value is quoted from the
# announcement or the resumen post of the same talk (see notes.md).
# ---------------------------------------------------------------------------
TALKS = {
    "hablemos-ciberseguridad-hablemos-frameworkd-ciberseguridad-dolbuck-s-l": {
        "speakers": [("Adrián Ramírez", "Dolbuck S.L.", "CEO")],
        "company": "Dolbuck S.L.",
    },
    "lo-nadie-me-conto-la-universidad": {
        "speakers": [("Alberto Fernández Valiente", None, "Ingeniero Técnico en Informática de Sistemas (Universidad de Sevilla)")],
        "company": None,
    },
    "mayor-quiero-pentester-david-sanchez": {
        "speakers": [("David Sánchez", "Sputnik Ciberseguridad", "CEO")],
        "company": "Sputnik Ciberseguridad",
    },
    "ciberseguridad-retos-necesidades-francisco-valencia": {
        "speakers": [("Francisco Valencia", "Secure&IT", "CEO")],
        "company": "Secure&IT",
    },
    "futuro-sin-contrasenas-daniel-garcia": {
        "speakers": [("Daniel García", "PRiSE", "Director tecnológico")],
        "company": "PRiSE",
    },
    "identificacion-preservacion-evidencias-digitales-alberto-castro": {
        "speakers": [("Alberto Castro Ortiz", "OnRetrieval", "Responsable técnico del área forense")],
        "company": "OnRetrieval",
    },
    "introduccion-la-computacion-cuantica-jose-martinez-garcia": {
        "speakers": [("José Martínez García", None, None)],
        "company": None,
    },
    "introduccion-owasp-herramientas-pentesting-paula-garrido-lerma-jesus-manuel-sanchez-alanis": {
        "speakers": [
            ("Paula Garrido Lerma", "BeOneSec", "Estudiante de Ingeniería de Tecnologías Informáticas (Universidad de Sevilla)"),
            ("Jesús Manuel Sánchez Alanís", "BeOneSec", "Estudiante de Ingeniería de Tecnologías Informáticas (Universidad de Sevilla)"),
        ],
        "company": "BeOneSec",
    },
    "seguridad-cloud-native-alba-ferri": {
        "speakers": [("Alba Ferri", "Sysdig", "Product Marketing Manager")],
        "company": "Sysdig",
    },
    "ciberseguridad-esperan-los-alumnos-donde-estudiar-lo-esperan-angel-jesus-varela-vaca": {
        "speakers": [("Ángel Jesús Varela Vaca", "Universidad de Sevilla", "Profesor de Ingeniería Informática, doctor en Ingeniería Informática y del Software")],
        "company": "Universidad de Sevilla",
    },
    "ciberseguridad-hacking-etico-francisco-ramirez": {
        "speakers": [("Francisco José Ramírez López", "Deloitte", "Consultor de seguridad senior")],
        "company": "Deloitte",
        # The announcement says "14 de Noviembre de 2021" (a Sunday) although
        # the post was published that same Sunday for the coming week; the
        # rest of the programme runs on Mon 8, Wed 10, Mon 15 and Wed 17, and
        # the 18:30 slot exists on Mon 15. Treated as a typo for 15 Nov.
        "date_fix": "2021-11-15",
    },
    "comienzo-la-ciberseguridad-donde-empiezo-manuel-jesus-flores-montano": {
        "speakers": [("Manuel Jesús Flores Montaño", "Universidad Pablo de Olavide", "Técnico de administración de sistemas informáticos, estudiante de Ingeniería Informática, Microsoft Student Ambassador")],
        "company": "Universidad Pablo de Olavide",
    },
    "seguridad-los-servicios-la-nube-andres-marchante-tirado": {
        "speakers": [("Andrés Marchante Tirado", "Dell", "Ingeniero Senior de Sistemas")],
        "company": "Dell",
    },
    "ahora-estoy-acabando-la-carrera-maria-jose-escalona": {
        "speakers": [("María José Escalona", "Universidad de Sevilla", "Catedrática, Departamento de Lenguajes y Sistemas Informáticos")],
        "company": "Universidad de Sevilla",
    },
    "becario-ciberseguridad-no-morir-intento-francisco-perez-fernandez": {
        "speakers": [("Francisco Pérez Fernández", "NTT DATA", "Ingeniero informático especializado en seguridad informática")],
        "company": "NTT DATA",
    },
    "firma-digital-e-identidad-digital-jesus-lopez": {
        "speakers": [
            ("Jesús López", "Viafirma", "Departamento de desarrollo"),
            ("Benito Galán Algora", "Viafirma", "Departamento de desarrollo"),
        ],
        "company": "Viafirma",
    },
    "identificacion-ciber-inseguridades-rafael-martinez": {
        "speakers": [("Rafael Martínez Gasca", "Universidad de Sevilla", "Catedrático de Universidad, doctor en Informática")],
        "company": "Universidad de Sevilla",
    },
}

CATEGORY_NAMES = {"noticias": "Noticias", "sin-categoria": "Sin categoría"}
QUOTES = "“”\"«»"
LOGISTICS_RE = re.compile(r"eventbrite|twitch|tendr[áa] lugar|se realizar[áa]|os esperamos|el evento tendr", re.I)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def esc(t: str) -> str:
    return html.escape(t or "", quote=False)


def when_es(starts_at: str | None, ends_at: str | None) -> str:
    """'2021-11-10T11:30:00', '2021-11-10T12:30:00' -> '10 de noviembre, de 11:30 a 12:30'."""
    if not starts_at:
        return "fecha sin confirmar"
    day = int(starts_at[8:10])
    out = f"{day} de noviembre"
    if "T" in starts_at:
        out += f", {starts_at[11:16]}"
        if ends_at:
            out = f"{day} de noviembre, de {starts_at[11:16]} a {ends_at[11:16]}"
    return out


def demote_h1(html_text: str) -> str:
    """Post bodies must not carry h1 (the title is the h1); h1 -> h2."""
    return re.sub(r"<(/?)h1(\s|>)", r"<\1h2\2", html_text)


def content_sig(html_text: str) -> str:
    """Whitespace-insensitive signature to compare captures of the same post."""
    return re.sub(r"\s*(<[^>]+>)\s*", r"\1", re.sub(r"\s+", " ", html_text)).strip()


def slug_of(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def norm_key(s: str) -> str:
    """Accent/punctuation-insensitive key to pair announcement and resumen."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def split_title(h1: str) -> tuple[bool, str, str]:
    """'[RESUMEN] “Talk”, por Speaker' -> (is_resumen, 'Talk', 'Speaker')."""
    t = re.sub(r"\s+", " ", h1).strip()
    is_res = bool(re.match(r"^\[resumen\]", t, re.I))
    t = re.sub(r"^\[resumen\]\s*", "", t, flags=re.I)
    m = re.match(rf"^[{QUOTES}]\s*(.+?)\s*[{QUOTES}]\s*,?\s*(?:por\s+)?(.*?)\s*\.?\s*$", t)
    if not m:
        return is_res, t.strip(" .“”"), ""
    talk = m.group(1).strip().rstrip(".").strip()
    speaker = m.group(2).strip()
    return is_res, talk, speaker


def local_iso(published: str | None) -> str | None:
    """'2021-11-09T15:42:20+00:00' -> '2021-11-09T16:42:20' (Europe/Madrid)."""
    if not published:
        return None
    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
    return dt.astimezone(MADRID).replace(tzinfo=None).isoformat(timespec="seconds")


def excerpt_of(text: str, limit: int = 300) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    m = list(re.finditer(r"[.!?…](?=\s)", cut))
    if m and m[-1].end() > limit // 2:
        return cut[: m[-1].end()].strip()
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + "…"


def talk_datetime(text: str, date_fix: str | None):
    """(date, start, end, room) as stated in the announcement prose."""
    t = text.replace("\xa0", " ")
    date = date_fix or None
    if not date:
        m = re.search(r"\b(\d{1,2})\s*(?:de\s+)?(noviembre|octubre|diciembre)\b", t, re.I)
        d = parse_spanish_date(m.group(0), YEAR) if m else None
        date = d.isoformat() if d else None
    times = re.findall(r"\b(\d{1,2}):(\d{2})\b", t)  # never 'A0.11' style room codes
    times = [f"{int(h):02d}:{mm}" for h, mm in times]
    start = times[0] if times else None
    end = times[1] if len(times) > 1 else None
    room = None
    m = re.search(r"aula\s+([A-Z]\d\.\d{2})\b", t)
    if m:
        room = m.group(1)
    elif re.search(r"sal[oó]n de grados", t, re.I):
        room = "Salón de Grados"
    return date, start, end, room


def parse_post(row: dict) -> dict:
    soup = soup_of(row)
    art = soup.find("article")
    h1 = art.find(class_="entry-title")
    content = art.find(class_="entry-content")
    metas = {m.get("property") or m.get("name"): m.get("content") for m in soup.find_all("meta")}
    cats = [c[len("category-"):] for c in art.get("class", []) if c.startswith("category-")]
    paragraphs = [text_of(p) for p in content.find_all("p", recursive=False)] or [text_of(content)]
    is_res, talk, speaker = split_title(text_of(h1))
    og_image = metas.get("og:image")
    return {
        "date": local_iso(metas.get("article:published_time")) or datetime.strptime(text_of(art.find(class_="published")), "%d/%m/%Y").isoformat(),
        "title": re.sub(r"\s+", " ", text_of(h1)).strip(),
        "slug": slug_of(row["url"]),
        "excerpt": excerpt_of(paragraphs[0]),
        "content_html": demote_h1(clean_html(content)),
        "featured_image_url": norm_url(og_image) if og_image else None,
        "lang": "es",
        "edition_year": YEAR,
        "categories": [CATEGORY_NAMES.get(c, c) for c in cats],
        "source_url": row["url"],
        "source_timestamp": row["timestamp"],
        # private helpers (stripped before dump)
        "_is_resumen": is_res,
        "_talk": talk,
        "_speaker_in_title": speaker,
        "_paragraphs": paragraphs,
        "_content_node": content,
        "_text": text_of(content),
    }


def bio_html(content_node) -> str:
    """Announcement paragraphs about the speaker (logistics paragraphs dropped)."""
    keep = [p for p in content_node.find_all("p", recursive=False) if not LOGISTICS_RE.search(text_of(p))]
    return clean_html("".join(str(p) for p in keep)) if keep else clean_html(content_node)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    rows = [r for r in manifest_rows("post") if re.search(rf"/{YEAR}/\d\d/\d\d/", r["url"])]
    by_url: dict[str, list[dict]] = {}
    for r in rows:
        by_url.setdefault(r["url"], []).append(r)
    for v in by_url.values():
        v.sort(key=lambda r: r["timestamp"])

    posts: list[dict] = []
    version_notes: list[str] = []
    for url in sorted(by_url):
        versions = by_url[url]
        parsed = [(r, parse_post(r)) for r in versions]
        # prefer the latest capture unless an older one has more content
        # (captures differ only in whitespace between tags, hence the signature)
        best_row, best = max(parsed, key=lambda rp: (len(content_sig(rp[1]["content_html"])), rp[0]["timestamp"]))
        same = len({content_sig(p["content_html"]) for _, p in parsed}) == 1
        version_notes.append(
            f"| {slug_of(url)} | {len(versions)} | {', '.join(r['timestamp'] for r in versions)} | {best_row['timestamp']} | {'identical' if same else 'DIFFERENT, longest kept'} |"
        )
        posts.append(best)

    # pair announcement + resumen by normalised talk title
    announcements = {p["slug"]: p for p in posts if not p["_is_resumen"]}
    resumenes = [p for p in posts if p["_is_resumen"]]
    ann_by_key = {norm_key(p["_talk"]): p for p in announcements.values()}
    pairs: dict[str, dict | None] = {slug: None for slug in announcements}
    unpaired: list[str] = []
    for r in resumenes:
        a = ann_by_key.get(norm_key(r["_talk"]))
        if a is None:
            unpaired.append(r["slug"])
            continue
        pairs[a["slug"]] = r

    events: list[dict] = []
    speakers: dict[str, dict] = {}
    for slug, ann in sorted(announcements.items(), key=lambda kv: kv[1]["date"]):
        facts = TALKS.get(slug, {})
        res = pairs.get(slug)
        date, start, end, room = talk_datetime(ann["_text"], facts.get("date_fix"))
        names = [s[0] for s in facts.get("speakers", [])] or [ann["_speaker_in_title"]]
        link = None
        m = re.search(r"https?://www\.eventbrite\.[a-z]+/e/[^\s\"<]+", ann["_text"])
        if m:
            link = m.group(0).rstrip(".,")
        starts_at = f"{date}T{start}:00" if date and start else date
        ends_at = f"{date}T{end}:00" if date and end else None
        events.append({
            "edition_year": YEAR,
            "title": ann["_talk"],
            "kind": "talk",
            "starts_at": starts_at,
            "ends_at": ends_at,
            "room": room,
            "modality": "in_person",
            "speaker": " y ".join(names),
            "company": facts.get("company"),
            "summary": excerpt_of(ann["_paragraphs"][0], 400),
            "description_html": (res or ann)["content_html"],
            "poster_url": None,
            "link": link,
            "lang": "es",
            "source_url": ann["source_url"],
            "source_timestamp": ann["source_timestamp"],
        })
        for name, affiliation, position in facts.get("speakers", []) or [(ann["_speaker_in_title"], facts.get("company"), None)]:
            if name in speakers:
                continue
            speakers[name] = {
                "name": name,
                "affiliation": affiliation,
                "position": position,
                "bio_html": bio_html(ann["_content_node"]),
                "photo_url": None,
                "links": [],
                "edition_years": [YEAR],
                "source_url": ann["source_url"],
            }

    events.sort(key=lambda e: (e["starts_at"] or "", e["title"]))
    talk_dates = sorted({e["starts_at"][:10] for e in events if e["starts_at"]})
    programme = "".join(
        f"<li><strong>{esc(e['title'])}</strong>, {esc(e['speaker'])}"
        + (f" ({esc(e['company'])})" if e["company"] else "")
        + f". {when_es(e['starts_at'], e['ends_at'])}" + (f", {esc(e['room']) if e['room'].startswith('Sal') else 'aula ' + esc(e['room'])}" if e["room"] else "")
        + "</li>"
        for e in events
    )
    edition = {
        "year": YEAR,
        "number": edition_number_for_year(YEAR),
        "roman": roman(edition_number_for_year(YEAR)),
        "name": f"InnoSoft Days {roman(edition_number_for_year(YEAR))}",
        "starts_on": talk_dates[0] if talk_dates else None,
        "ends_on": talk_dates[-1] if talk_dates else None,
        "venue": "ETSII, Universidad de Sevilla",
        "summary": (
            "Novena edición de InnoSoft Days, dedicada a la ciberseguridad. "
            f"{len(events)} charlas presenciales en la ETSII los días "
            + ", ".join(d[8:].lstrip("0") for d in talk_dates[:-1]) + f" y {talk_dates[-1][8:].lstrip('0')} de noviembre de 2021, "
            "con entradas gratuitas por Eventbrite para la comunidad universitaria y retransmisión por Twitch para el público general."
        ),
        "description_html": (
            "<p>Novena edición de InnoSoft Days, celebrada en la ETSII (Universidad de Sevilla) en noviembre de 2021 "
            "y dedicada a la ciberseguridad: pentesting, hacking ético, identidad digital, seguridad cloud, "
            "informática forense y salidas profesionales del sector, además de charlas sobre computación cuántica "
            "y sobre la vida tras la carrera.</p>"
            "<p>Las charlas fueron presenciales, con entrada gratuita por Eventbrite para miembros de la Universidad de Sevilla, "
            "y se retransmitieron en directo por los canales oficiales de Twitch (innosoftdays1 e innosoftdays2).</p>"
            f"<h3>Programa</h3><ul>{programme}</ul>"
        ),
        "registration_url": None,
        "sources": sorted(by_url),
        "confidence": "medium",
        "notes": (
            "Derived only from the 2021 blog posts (announcement + resumen per talk); starts_on/ends_on are the first and "
            "last talk days. The edition page /ix-edicion/ exists in the CDX index but was not fetched, so the official "
            "programme, poster and organisers are not in this family."
        ),
    }

    clean_posts = [{k: v for k, v in p.items() if not k.startswith("_")} for p in posts]
    PARTS.mkdir(parents=True, exist_ok=True)
    (PARTS / f"{FAMILY}.posts.json").write_text(json.dumps(clean_posts, ensure_ascii=False, indent=1), encoding="utf-8")
    (PARTS / f"{FAMILY}.events.json").write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
    (PARTS / f"{FAMILY}.speakers.json").write_text(json.dumps(list(speakers.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    (PARTS / f"{FAMILY}.editions.json").write_text(json.dumps([edition], ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- notes ----------------------------------------------------------
    n_ann = len(announcements)
    n_res = len(resumenes)
    pair_lines = []
    ann_by_url = {a["source_url"]: a for a in announcements.values()}
    for e in events:
        slug = ann_by_url[e["source_url"]]["slug"]
        res = pairs.get(slug)
        pair_lines.append(
            f"| {e['starts_at'] or '?'}{(' – ' + e['ends_at'][11:16]) if e['ends_at'] else ''} | {e['room'] or '?'} | {e['title']} | {e['speaker']} | {e['company'] or ''} | {slug} | {res['slug'] if res else 'no resumen'} |"
        )
    missing = [e for e in events if not e["starts_at"] or "T" not in (e["starts_at"] or "") or not e["room"]]
    notes = f"""# posts_2021 (InnoSoft Days IX, 2021)

Parser: `parse/posts_2021.py`. Inputs: manifest rows of kind=post with a `/2021/MM/DD/` URL.

## Coverage

- Captures in scope: {len(rows)} (URLs: {len(by_url)}). Every URL extracted; nothing skipped.
- Posts written: {len(clean_posts)} ({n_ann} announcements, {n_res} "[RESUMEN]" write-ups). All are 2021, Spanish, category
  "Noticias" except two in "Sin categoría" (computación cuántica announcement + resumen).
- Events written: {len(events)} talks (one per announcement; the resumen of the same talk is merged into
  `description_html`; {sum(1 for v in pairs.values() if v)} talks have a resumen, {sum(1 for v in pairs.values() if not v)} do not).
- Speakers written: {len(speakers)}.
- Editions written: 1 (2021, IX), derived from the posts; confidence medium.
- No pages, organisers or media in this family: none of the 32 posts contains an image, gallery, iframe or featured image.
- Unpaired resumen posts: {unpaired or 'none'}.

## Versions per URL

Where a URL has two captures (2024-11 and 2025-01/02) the cleaned `entry-content` is identical up to whitespace
between tags (five posts differ only in newlines around tags in the raw HTML); the latest capture is kept and
its timestamp goes to `source_timestamp`.

| slug | captures | timestamps | kept | content |
|---|---|---|---|---|
{chr(10).join(version_notes)}

## Talks (events)

Date/time/room parsed from the announcement prose ("La ponencia tendrá lugar el día 10 de Noviembre de 2021, de
11:30 a 12:30, en el aula A0.11 de la ETSII"). Speaker full names, company and position come from a curated table
in the parser, quoting the announcement or the resumen (e.g. Dolbuck's speaker Adrián Ramírez, CEO, is only named
in the resumen; Francisco Pérez Fernández's employer NTT DATA likewise). `link` is the Eventbrite ticket URL.
`source_url` is the announcement post; the resumen URL is in the last column.

| starts_at | room | title | speaker | company | announcement slug | resumen slug |
|---|---|---|---|---|---|---|
{chr(10).join(pair_lines)}

## Oddities

- "Ciberseguridad y hacking ético" (Francisco José Ramírez López): the announcement says "14 de Noviembre de 2021,
  de 18:30 a 19:30, aula A3.10". 14 Nov 2021 was a Sunday (the post itself was published that Sunday) and every
  other talk falls on Mon 8, Wed 10, Mon 15 or Wed 17; the parser corrects it to 2021-11-15 (`date_fix`).
  The resumen slug also misnames him ("francisco-jimenez").
- "Hablemos de ciberseguridad, hablemos de framework de ciberseguridad" (Dolbuck S.L.): only the day (Mon 8 Nov,
  "la última del primer día") and the room (A2.16) are stated, no time. `starts_at` is the date only.
- "De mayor quiero ser pentester" (David Sánchez): start time 10:30 on Mon 8 Nov, no end time and no room stated.
- Two talks have two speakers: OWASP (Paula Garrido Lerma + Jesús Manuel Sánchez Alanís, students at BeOneSec) and
  Firma digital (Jesús López + Benito Galán Algora, Viafirma); `speaker` joins them with " y " and speakers.json
  has one row each sharing the announcement bio.
- Speaker names differ between announcement and resumen (Rafael Martínez / Rafael Martínez Gasca, Alberto Castro /
  Alberto Castro Ortiz, Alberto Fernández / Alberto Fernández Valiente, Francisco Ramírez / Francisco José Ramírez
  López); the fullest form is used everywhere.
- Talks were hybrid: in person at ETSII (Eventbrite ticket for US members) and streamed on Twitch for everyone else.
  `modality` is `in_person`; the Twitch channels are mentioned in the description.
- `clean_html` rewrites the Twitch links from http to https (the host contains "innosoftdays"), harmless.
- Post `date` is `article:published_time` converted from UTC to Europe/Madrid (matches the visible dd/mm/yyyy).
- Three resumen posts use h1/h2 headings inside the body; h1 is demoted to h2 in `content_html` so the post title
  stays the only h1.
- Events are sorted by `starts_at`; the edition `description_html` carries a generated programme list.
- Events with missing time or room: {len(missing)} (listed above).

## Per-year counts

| year | captures | posts | events | speakers |
|---|---|---|---|---|
| 2021 | {len(rows)} | {len(clean_posts)} | {len(events)} | {len(speakers)} |
"""
    (PARTS / f"{FAMILY}.notes.md").write_text(notes, encoding="utf-8")
    print(f"posts={len(clean_posts)} events={len(events)} speakers={len(speakers)} captures={len(rows)} unpaired={unpaired}")


if __name__ == "__main__":
    main()
