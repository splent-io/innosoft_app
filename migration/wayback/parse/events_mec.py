"""Family events_mec: single event pages of the Modern Events Calendar plugin
(/events/<slug>/ on innosoftdays.com, one capture on
institucional.us.es/innosoft/events/) plus the /events/ index page versions
(kind=event-index).

The Astra-era MEC single template shipped with almost no metadata in the DOM
(no date/time/location/organizer blocks): the reliable sources are the
schema.org JSON-LD block (startDate/endDate, location.name, organizer.name and
organizer.url) and the "Add to Google Calendar" link, whose `dates=` parameter
carries the start/end times. MEC builds that parameter with
gmdate(strtotime()) under WordPress' UTC PHP timezone, so the "Z" times are
the naive Europe/Madrid times shown on the site (verified against the only
capture that still renders the MEC date/time blocks, the 2020 institucional
one: "Hora 20:30 - 21:30" vs dates=20201127T203000Z/20201127T213000Z).

Outputs (data/extracted/parts/events_mec.*): events, speakers, editions,
media, notes.
"""

from __future__ import annotations

import collections
import html as htmlmod
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import *  # noqa: E402,F401,F403
from parse.common import (  # noqa: E402
    BeautifulSoup, RAW, clean_html, dump_part, edition_number_for_year, fix_lazy_images,
    latest_per_url, manifest_rows, norm_media_url, norm_url, read_html, roman, text_of,
)

FAMILY = "events_mec"
EVENT_URL_RE = re.compile(r"^https://www\.innosoftdays\.com/events/[^/]+/$")
INSTITUCIONAL_EVENT_RE = re.compile(r"^https://institucional\.us\.es/innosoft/events/[^/]+/$")

# MEC "organizer" values that are not people (used as company/affiliation).
ORGANISATION_NAMES = {
    "mujeres tech", "digitálica salud", "ecapture 3d", "atsistemas", "sevilla guifi",
    "abatic", "gumus", "dolbuck sl", "onretrieval", "ayesa", "viafirma",
    "ping a programadoras", "innosoft",
}
PLACEHOLDER_ORGANISERS = {"organizer name", ""}

# Titles of 2022 ("Charla de <Empresa>") whose subject is a company; a Sr./Sra.
# title means the subject is a person.
PERSON_TITLE_RE = re.compile(r"^Charla\s+(?:de\s+)?(?:la\s+Sra\.|del\s+Sr\.|de\s+la\s+Sra\.|del\s+Sr)\s+(.+)$", re.I)
COMPANY_TITLE_RE = re.compile(r"^Charla\s+de\s+(.+)$", re.I)
DASH_TITLE_RE = re.compile(r"^Charla\s+(.+?)\s+[–-]\s+(.+)$")
INFO_LINK_RE = re.compile(
    r"Información sobre la ponencia (?:de\s+la\s+Sra\.|del\s+Sr\.|de\s+los\s+Srs\.|de\s+las\s+Sras\.|de\s+el\s+Sr\.|de\s+la\s+Sr\.|de\s+la\s+Dra\.|del\s+Dr\.)\s*(.+)$", re.I)
COMPANY_TOPICS_2024 = {"ntt data"}

# Curated speaker/company hints for events whose speaker only appears inside
# the prose (mostly 2023): read from the descriptions, keyed by slug.
SPEAKER_HINTS = {
    "el-uso-de-chat-gpt-para-datos-estructurados-con-insinno": ("José González", "Insinno"),
    "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-1": ("Carlos Müller Cejas, Soraya Peceño Capilla", None),
    "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2": ("Pablo Cala, Carlos Pérez Fernández, José Ignacio Morales Conde", None),
    "la-ia-motor-de-la-transformacion-laboral": ("Ricardo Arjona", "EC2CE"),
    "retos-sociales-y-eticos-de-la-ia": ("Fernando Soler", None),
    "taller-de-ciberseguridad": ("Isabel Cayrasso Buzón", "GeseRisk"),
    "tecnologia-y-arte": ("Rocío García Robles, Olga Albillos Castillo, Helena Hernández Acuaviva, Leila Pontiga Gaytán, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diánez, Guillermo Rodríguez", None),
    "transformando-la-salud-con-inteligencia-artificial": ("Carlos Luis Parra Calderón", "Hospital Universitario Virgen del Rocío"),
    "charla-de-pandora": (None, "Pandora FMS"),
    "charla-del-sr-frank-azhrei-edwards": (None, "MapTool"),
}

# 2021 event descriptions repeat a ticketing notice; it is not event content.
BOILERPLATE_RE = re.compile(
    r"^(entradas:?|aviso:?|-?\s*recuerda llevar las entradas|-?\s*si abandona la charla|"
    r"si quieres asistir a (esta charla|la ceremonia|esta actividad|este taller|este torneo)[^.]*(entrada|enlace)|"
    r"puedes obtener una entrada)", re.I)

ES_STOP = {"de", "la", "el", "y", "en", "con", "para", "los", "las", "del", "un", "una", "por", "que", "al", "se"}
EN_STOP = {"the", "and", "on", "by", "with", "of", "for", "to", "in", "an", "how", "your", "from"}


# --- helpers ---------------------------------------------------------------

def slug_of(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def parse_ld(html: str) -> dict:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def gcal_times(html: str):
    """(start, end) naive datetimes from the Google Calendar export link."""
    m = re.search(r'google\.com/calendar/event\?[^"]*?dates=(\d{8}T\d{6})Z/(\d{8}T\d{6})Z', html)
    if not m:
        return None, None
    fmt = "%Y%m%dT%H%M%S"
    try:
        return datetime.strptime(m.group(1), fmt), datetime.strptime(m.group(2), fmt)
    except ValueError:
        return None, None


def fix_end(start: datetime | None, end: datetime | None):
    """MEC lets an end time earlier than the start slip through; two 2018/2019
    events have 00:30/00:40 ends that are 12:30/12:40 with the wrong AM/PM.
    Returns (end, note)."""
    if start is None or end is None:
        return end, None
    if end > start:
        return end, None
    if end.date() == start.date() and end.hour == 0:
        fixed = end + timedelta(hours=12)
        if fixed > start:
            return fixed, f"end time {end:%H:%M} read as {fixed:%H:%M} (AM/PM slip)"
    return None, f"end time {end:%H:%M} not after start {start:%H:%M}, dropped"


def looks_english(*texts: str) -> bool:
    words = re.findall(r"[a-záéíóúñ]+", " ".join(t for t in texts if t).lower())
    if not words:
        return False
    es = sum(w in ES_STOP for w in words)
    en = sum(w in EN_STOP for w in words)
    return en > es and en >= 2


def classify(title: str, description: str) -> str:
    t = title.lower()
    d = description.lower()
    if re.search(r"\b(taller|workshop)\b", t):
        return "workshop"
    if re.search(r"torneo|competici[óo]n|\bctf\b|hackat|gymk|programaci[óo]n competitiva|s?cape room|brawlhalla|smash bros|rocket league|ajedrez", t):
        return "competition"
    if re.search(r"^stand\b|\bstand de\b", t):
        return "stand"
    if re.search(r"acto de (apertura|clausura)|ceremonia|inauguraci[óo]n|presentaci[óo]n del d[íi]a|charla de apertura de las jornadas|charla de cl[áa]usura|bienvenido a innosoft", t):
        return "ceremony"
    if re.search(r"barrilada|quedada musical|^m[uú]sica$|^grupo$", t):
        return "social"
    if re.search(r"^innosoft days( 20\d\d| d[íi]a \d+)$", t):
        return "other"
    if re.search(r"proyecci[óo]n", t):
        return "other"
    if re.search(r"conferencia|charla|mesa redonda|keynote|ponencia|introducci[óo]n|seguridad|ciberseguridad", t) or d:
        return "talk"
    return "talk"


def split_person_company(raw: str):
    """MEC organizer string -> (speaker, company, position, is_person)."""
    name = htmlmod.unescape(raw or "").strip()
    if name.lower() in PLACEHOLDER_ORGANISERS:
        return None, None, None, False
    if name.lower() in ORGANISATION_NAMES:
        return None, (None if name.lower() == "innosoft" else name), None, False
    m = re.match(r"^(.+?)\s*\((.+)\)$", name)
    if m:
        return m.group(1).strip(), m.group(2).strip(), None, True
    m = re.match(r"^(.+?)\s*\+\s*(.+)$", name)
    if m:
        return m.group(1).strip(), m.group(2).strip(), None, True
    m = re.match(r"^(.+?)\s+-\s+(.+)$", name)
    if m:
        return m.group(1).strip(), None, m.group(2).strip(), True
    return name, None, None, True


def speaker_from_title(title: str, year: int):
    """(speaker, company) from the 2022 'Charla de ...' and 2024
    'Charla <tema> – <nombre>' title conventions."""
    m = PERSON_TITLE_RE.match(title)
    if m:
        return m.group(1).strip(), None
    m = DASH_TITLE_RE.match(title)
    if m and year >= 2024:
        topic, name = m.group(1).strip(), m.group(2).strip()
        company = None
        pm = re.match(r"^(.+?)\s*\((.+)\)$", name)
        if pm:
            name, company = pm.group(1).strip(), pm.group(2).strip()
        if topic.lower() in COMPANY_TOPICS_2024:
            company = topic
        return name, company
    m = COMPANY_TITLE_RE.match(title)
    if m and year == 2022:
        subject = m.group(1).strip()
        if subject.lower() in ("mesa redonda", "cláusura", "clausura", "apertura de las jornadas"):
            return None, None
        return None, subject
    return None, None


def speakers_from_info_link(text: str):
    m = INFO_LINK_RE.search(text or "")
    if not m:
        return None
    names = m.group(1).strip().rstrip(".")
    names = re.sub(r"\s+y\s+", ", ", names)
    return names or None


def split_names(speaker: str) -> list[str]:
    parts = re.split(r",\s*|\s+y\s+", speaker)
    return [p.strip() for p in parts if p.strip()]


def strip_description(desc) -> tuple[str, list[str], list[str]]:
    """Clean the mec-single-event-description node. Returns
    (html, external links found, info-post link texts)."""
    if desc is None:
        return "", [], []
    fix_lazy_images(desc)
    links, info_texts = [], []
    for ifr in desc.find_all("iframe"):
        ifr.decompose()  # WordPress oEmbed of the site's own posts
    for img in desc.find_all("img"):
        src = norm_media_url(img.get("src") or "")
        if "logo-innosoft" in src or not src:
            img.decompose()  # site logo used as placeholder
    for a in desc.find_all("a"):
        href = a.get("href") or ""
        if "eventbrite" in href:
            links.append(href.strip())
        elif "innosoftdays.com" in norm_url(href) or "institucional.us.es" in href:
            links.append(norm_url(href))
            info_texts.append(text_of(a))
    # drop the ticketing boilerplate paragraphs (2021) and bare eventbrite URLs
    for p in list(desc.find_all(["p", "blockquote"])):
        txt = text_of(p)
        if not txt:
            continue
        if BOILERPLATE_RE.match(txt) or re.fullmatch(r"https?://\S+", txt):
            p.decompose()
    html_out = clean_html(desc)
    html_out = html_out.replace("\u200b", "").replace("\ufeff", "")
    html_out = re.sub(r"<p>\s*(?:<br\s*/?>|&nbsp;|\s)*</p>", "", html_out).strip()
    if html_out and not html_out.lstrip().startswith("<"):
        html_out = "<p>" + html_out + "</p>"
    return html_out, links, info_texts


def summary_of(html_str: str, limit: int = 300) -> str | None:
    if not html_str:
        return None
    text = BeautifulSoup(html_str, "lxml").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"


def poster_from(art, html: str) -> str | None:
    box = art.find(class_="mec-events-event-image") if art else None
    if box is not None:
        fix_lazy_images(box)
        for img in box.find_all("img"):
            src = norm_media_url(img.get("src") or "")
            if src and "logo-innosoft" not in src:
                return src
    m = re.search(r'<meta property="og:image" content="([^"]*)"', html)
    if m:
        src = norm_media_url(m.group(1))
        if "/wp-content/uploads/" in src and "logo-innosoft" not in src:
            return src
    return None


# --- main extraction --------------------------------------------------------

def extract_event(row: dict) -> tuple[dict | None, dict]:
    """One capture -> (event dict or None, info for the notes)."""
    html = read_html(row)
    soup = BeautifulSoup(html, "lxml")
    art = soup.find("article", class_="mec-single-event")
    info = {"url": row["url"], "timestamp": row["timestamp"], "notes": []}
    if art is None:
        info["skip"] = "no MEC single-event article in the capture"
        return None, info
    ld = parse_ld(html)
    title = text_of(art.find(class_="mec-single-title")) or htmlmod.unescape(ld.get("name") or "")
    title = re.sub(r"\s+", " ", title).strip()
    if not title:
        info["skip"] = "no title"
        return None, info

    start, end = gcal_times(html)
    if start is None and ld.get("startDate"):
        try:
            start = datetime.fromisoformat(ld["startDate"][:10])
            info["notes"].append("no calendar link, start taken from JSON-LD date (no time)")
        except ValueError:
            start = None
    if start is None:
        info["skip"] = "no date found (no calendar link, no JSON-LD startDate)"
        return None, info
    if ld.get("startDate") and ld["startDate"][:10] != start.strftime("%Y-%m-%d"):
        info["notes"].append(f"JSON-LD startDate {ld['startDate']} differs from calendar link {start:%Y-%m-%d}")
    end, note = fix_end(start, end)
    if note:
        info["notes"].append(note)
    year = start.year

    loc = ld.get("location") if isinstance(ld.get("location"), dict) else {}
    room = htmlmod.unescape((loc.get("name") or "").strip()) or None
    address = htmlmod.unescape((loc.get("address") or "").strip())
    online = bool(room and re.search(r"twitch|online|youtube|zoom|meet", room, re.I) and not re.match(r"^[A-Z]\d\.\d+", room))
    modality = "online" if online else "in_person"

    org = ld.get("organizer") if isinstance(ld.get("organizer"), dict) else {}
    speaker, company, position, is_person = split_person_company(org.get("name") or "")
    org_url = (org.get("url") or "").strip() or None

    desc = art.find(class_="mec-single-event-description")
    description_html, links, info_texts = strip_description(desc)
    if not speaker:
        t_speaker, t_company = speaker_from_title(title, year)
        speaker = speaker or t_speaker
        company = company or t_company
    if not speaker:
        for txt in info_texts:
            found = speakers_from_info_link(txt)
            if found:
                speaker = found
                break
    slug = slug_of(row["url"])
    if slug in SPEAKER_HINTS:
        h_speaker, h_company = SPEAKER_HINTS[slug]
        speaker = speaker or h_speaker
        company = h_company or company
    if speaker:
        speaker = re.sub(r"\s+", " ", speaker).strip()

    link = None
    for lk in links:
        if "eventbrite" in lk:
            link = lk
            break
    if link is None and links:
        link = links[0]

    lang = "en" if looks_english(title, BeautifulSoup(description_html, "lxml").get_text(" ") if description_html else "") else "es"
    kind = classify(title, description_html)
    poster = poster_from(art, html)

    event = {
        "edition_year": year,
        "title": title,
        "kind": kind,
        "starts_at": start.isoformat(timespec="seconds"),
        "ends_at": end.isoformat(timespec="seconds") if end else None,
        "room": room,
        "modality": modality,
        "speaker": speaker or None,
        "company": company or None,
        "summary": summary_of(description_html),
        "description_html": description_html,
        "poster_url": poster,
        "link": link,
        "lang": lang,
        "source_url": row["url"],
        "source_timestamp": row["timestamp"],
    }
    info.update(is_person=is_person, position=position, org_url=org_url, address=address, slug=slug)
    return event, info


def main() -> None:
    event_rows = [r for r in manifest_rows("event") if EVENT_URL_RE.match(r["url"]) or INSTITUCIONAL_EVENT_RE.match(r["url"])]
    index_rows = manifest_rows("event-index")
    by_url = collections.defaultdict(list)
    for r in event_rows:
        by_url[r["url"]].append(r)
    latest = latest_per_url(event_rows)

    events, infos, skipped = [], [], []
    speakers: dict[str, dict] = {}
    media: dict[str, dict] = {}
    seen_keys: dict[tuple, str] = {}
    for url in sorted(latest, key=lambda u: (not u.startswith("https://www.innosoftdays.com/"), u)):
        row = latest[url]
        others = sorted(r["timestamp"] for r in by_url[url] if r["timestamp"] != row["timestamp"])
        ev, info = extract_event(row)
        info["others"] = others
        info["version_diffs"] = []
        for other in by_url[url]:
            if other["timestamp"] == row["timestamp"] or ev is None:
                continue
            ev2, _ = extract_event(other)
            if ev2 is None:
                info["version_diffs"].append(f"{other['timestamp']}: not extractable")
                continue
            for f in ("title", "starts_at", "ends_at", "room", "speaker", "company", "summary", "poster_url", "link"):
                if ev2[f] != ev[f]:
                    info["version_diffs"].append(f"{other['timestamp']}: {f} {ev2[f]!r} vs {ev[f]!r}")
            t1 = BeautifulSoup(ev["description_html"] or "", "lxml").get_text(" ", strip=True)
            t2 = BeautifulSoup(ev2["description_html"] or "", "lxml").get_text(" ", strip=True)
            if t1 != t2:
                info["version_diffs"].append(f"{other['timestamp']}: description text differs ({len(t2)} vs {len(t1)} chars)")
        if ev is None:
            skipped.append(info)
            continue
        key = (ev["title"].lower(), ev["starts_at"])
        if key in seen_keys:
            info["skip"] = f"same title and start as {seen_keys[key]} (mirror of the same event)"
            skipped.append(info)
            continue
        seen_keys[key] = url
        events.append(ev)
        infos.append(info)
        # speakers: only person names from the organizer field, title or hints
        if ev["speaker"]:
            for name in split_names(ev["speaker"]):
                if len(name.split()) < 2 or name.lower() in ORGANISATION_NAMES:
                    continue
                k = name.lower()
                sp = speakers.setdefault(k, {
                    "name": name, "affiliation": ev["company"], "position": info.get("position"),
                    "bio_html": "", "photo_url": None, "links": [], "edition_years": [],
                    "source_url": ev["source_url"],
                })
                if ev["edition_year"] not in sp["edition_years"]:
                    sp["edition_years"].append(ev["edition_year"])
                if not sp["affiliation"] and ev["company"]:
                    sp["affiliation"] = ev["company"]
                if info.get("org_url") and info.get("is_person") and len(split_names(ev["speaker"])) == 1:
                    u = info["org_url"]
                    if u not in [l["url"] for l in sp["links"]]:
                        label = "LinkedIn" if "linkedin" in u else ("Twitter" if "twitter" in u else "Web")
                        sp["links"].append({"label": label, "url": u})
        if ev["poster_url"]:
            m = media.setdefault(ev["poster_url"], {"url": ev["poster_url"], "kind": "poster", "edition_year": ev["edition_year"], "caption": ev["title"], "used_by": []})
            if ev["source_url"] not in m["used_by"]:
                m["used_by"].append(ev["source_url"])
        for img in BeautifulSoup(ev["description_html"] or "", "lxml").find_all("img"):
            src = img.get("src")
            if src and src != ev["poster_url"]:
                m = media.setdefault(src, {"url": src, "kind": "other", "edition_year": ev["edition_year"], "caption": ev["title"], "used_by": []})
                if ev["source_url"] not in m["used_by"]:
                    m["used_by"].append(ev["source_url"])

    events.sort(key=lambda e: (e["starts_at"], e["title"]))
    # events without a location inherit the modality of their year when the
    # year ran on a streaming channel (2020: the umbrella entry has no room)
    for year in {e["edition_year"] for e in events}:
        with_room = [e for e in events if e["edition_year"] == year and e["room"]]
        if with_room and all(e["modality"] == "online" for e in with_room):
            for e in events:
                if e["edition_year"] == year and not e["room"]:
                    e["modality"] = "online"
    for sp in speakers.values():
        sp["edition_years"].sort()

    # editions: min/max of the event dates per year
    per_year = collections.defaultdict(list)
    for ev in events:
        per_year[ev["edition_year"]].append(ev)
    editions = []
    for year in sorted(per_year):
        evs = per_year[year]
        starts = [e["starts_at"][:10] for e in evs]
        ends = [(e["ends_at"] or e["starts_at"])[:10] for e in evs]
        online_only = all(e["modality"] == "online" for e in evs)
        n = edition_number_for_year(year)
        editions.append({
            "year": year, "number": n, "roman": roman(n), "name": f"InnoSoft Days {roman(n)}",
            "starts_on": min(starts), "ends_on": max(ends),
            "venue": "Online (Twitch)" if online_only else "Escuela Técnica Superior de Ingeniería Informática, Universidad de Sevilla",
            "summary": None, "description_html": "", "registration_url": None,
            "sources": sorted({e["source_url"] for e in evs}),
            "confidence": "medium" if len(evs) >= 10 else "low",
            "notes": f"Dates are the min/max of the {len(evs)} MEC event pages of {year}; the edition may extend beyond them.",
        })

    dump_part(f"{FAMILY}.events.json", events)
    dump_part(f"{FAMILY}.speakers.json", sorted(speakers.values(), key=lambda s: s["name"].lower()))
    dump_part(f"{FAMILY}.editions.json", editions)
    dump_part(f"{FAMILY}.media.json", sorted(media.values(), key=lambda m: (m["edition_year"], m["url"])))
    write_notes(events, infos, skipped, speakers, editions, media, event_rows, index_rows)


def write_notes(events, infos, skipped, speakers, editions, media, event_rows, index_rows) -> None:
    lines = [f"# {FAMILY}", ""]
    lines.append("Single event pages of the Modern Events Calendar plugin (`/events/<slug>/`, class `mec-single-event`) and the `/events/` index captures. The Astra-era MEC template renders no date/time/location/organizer blocks, so every field comes from the schema.org JSON-LD block (dates, location.name, organizer) and from the Google Calendar export link (`dates=YYYYMMDDTHHMMSSZ/...`, which MEC builds from the local time under WordPress' UTC PHP timezone, so the values are the naive Europe/Madrid times; verified against the 2020 institucional capture that still renders `Hora 20:30 - 21:30`).")
    lines.append("")
    n_urls = len({r["url"] for r in event_rows})
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Event captures in scope: {len(event_rows)} ({n_urls} distinct URLs); event-index captures: {len(index_rows)} ({len({r['url'] for r in index_rows})} URLs).")
    diffs = [(i["url"], d) for i in infos for d in i.get("version_diffs", [])]
    lines.append(f"- Events extracted: {len(events)} (one per URL, latest capture). Every other capture of the same URL was extracted too and compared field by field (title, dates, room, speaker, company, summary, poster, link, description text): {len(diffs)} differences found" + (" (listed under Version differences)." if diffs else ", so the older captures carry the same event."))
    lines.append(f"- Skipped event URLs: {len(skipped)}. Speakers: {len(speakers)}. Editions: {len(editions)}. Media: {len(media)}.")
    lines.append("- The event pages are not limited to 2023/2024: the MEC calendar held the whole history from 2017 (edition V) to 2024 (edition XII).")
    lines.append("")
    lines.append("## Per year")
    lines.append("")
    per_year = collections.Counter(e["edition_year"] for e in events)
    for y in sorted(per_year):
        ed = next(e for e in editions if e["year"] == y)
        kinds = collections.Counter(e["kind"] for e in events if e["edition_year"] == y)
        lines.append(f"- {y} (edition {ed['roman']}): {per_year[y]} events, {ed['starts_on']} to {ed['ends_on']}, kinds {dict(sorted(kinds.items()))}")
    lines.append("")
    lines.append("## Field rules")
    lines.append("")
    lines.append("- `starts_at`/`ends_at`: Google Calendar link; JSON-LD `startDate` as fallback (date only). Ends earlier than the start: 00:xx ends on the same day are read as 12:xx (AM/PM slip in the MEC form), otherwise `ends_at` is null (listed under Oddities).")
    lines.append("- `room`: JSON-LD `location.name` verbatim (Aula A1.16, A3.10, Salón de Grados, Twitch Innosoft, `A0.11 Online`...). `modality` is `online` only when the location is a streaming channel (Twitch, 2020); the two 2021 rooms tagged `Online` are hybrid and stay `in_person` with the tag kept in `room`. Events without a location inherit `online` when every located event of their year is online (the 2020 umbrella entry).")
    lines.append("- `speaker`/`company`: MEC `organizer.name` (used as speaker in 2017 to 2021; organisation names such as Abatic, atSistemas, Mujeres Tech, Dolbuck SL, Viafirma, Ayesa, OnRetrieval, GUMUS, Ping a Programadoras go to `company`; `Name (Company)`, `Name + Company` and `Name - Position` are split). 2022 titles `Charla de la Sra./del Sr. X` give the speaker and `Charla de <Empresa>` the company, with the speaker taken from the linked post title `Información sobre la ponencia del Sr. X`; 2024 titles `Charla <tema> – <nombre> (<empresa>)` give both. A small curated table (`SPEAKER_HINTS`, mostly 2023) covers speakers only mentioned in the prose. Placeholder `Organizer Name` and `InnoSoft` are ignored.")
    lines.append("- `description_html`: `mec-single-event-description` cleaned; removed the WordPress oEmbed iframes of the site's own posts (the link stays), the `logo-innosoft` placeholder images, the 2021 ticketing boilerplate (Entradas / Aviso / Recuerda llevar las entradas...) and bare Eventbrite URLs, which move to `link`. Hourly-schedule and countdown boxes are noise and are not extracted.")
    lines.append("- `link`: the Eventbrite ticket URL when the description has one (2021, 2024), otherwise the first link to the site itself (2022 events link their `Información sobre la ponencia...` post, Brawlhalla its news post).")
    lines.append("- `poster_url`: featured image (`mec-events-event-image`, lazy `data-src`) or `og:image`, ignoring the site logo. Only the 2020 events had real posters.")
    lines.append("- `kind`: from the title (taller -> workshop; torneo/CTF/gymkhana/hackatón/escape room -> competition; stand -> stand; acto/ceremonia/inauguración/presentación del día/charla de apertura or clausura -> ceremony; barrilada/quedada musical/música/grupo -> social; umbrella entries `Innosoft Days 2020`, `Innosoft Days día 3/4` and screenings -> other; everything else -> talk).")
    lines.append("- `lang`: `en` when the title/description read as English by a stopword count, otherwise `es` (site locale es-ES). Titles are kept verbatim, including the ALL CAPS ones of 2019.")
    lines.append("- Speakers: one entry per person name found in `speaker` (split on commas and ` y `), affiliation from `company`, position from `Name - Position` organizers, links from `organizer.url` (LinkedIn/Web, 2020 events). No photos or bios exist in the MEC pages. Names are kept as written, so `Clara Grima` (2018) and `Clara Grima Ruiz` (2022), or `Maria José Escalona`, are left for the importer's dedupe.")
    lines.append("- Editions: one per year found, dates min/max of the events, venue ETSII (Online (Twitch) for 2020, whose events all ran on Twitch), confidence medium (low when fewer than 10 events, i.e. 2024 with 7 events on 6-7 November).")
    lines.append("")
    lines.append("## Event-index captures")
    lines.append("")
    for r in sorted(index_rows, key=lambda r: (r["url"], r["timestamp"])):
        html = read_html(r)
        if "mec-skin-list" in html or "mec-wrap" in html:
            reason = "MEC calendar shortcode rendering `¡No hay eventos!` (only future events are listed and none existed); nothing to extract"
        elif "tribe-events" in html:
            reason = "The Events Calendar (tribe) month view for December 2024 (three `Seminario Futuro` entries); belongs to the tribe /event/ family, not MEC"
        elif "mec" not in html and "elementor" in html and "/es/eventos/" in r["url"]:
            reason = "2025 Elementor/Blocksy site listing the XIII edition (Andreas Zeller...), not MEC; belongs to the 2025 family"
        else:
            reason = "no MEC markup and no event list (menu-only page)"
        lines.append(f"- {r['url']} capture {r['timestamp']}: skipped, {reason}.")
    lines.append("")
    lines.append("## Skipped event captures")
    lines.append("")
    if not skipped:
        lines.append("- none")
    for s in skipped:
        same = "same content" if not s.get("version_diffs") else "differs: " + "; ".join(s["version_diffs"])
        extra = f" (also {', '.join(s['others'])}, {same})" if s.get("others") else ""
        lines.append(f"- {s['url']} capture {s['timestamp']}{extra}: {s['skip']}")
    lines.append("")
    lines.append("## Version differences")
    lines.append("")
    if not diffs:
        lines.append("- none")
    for u, d in diffs:
        lines.append(f"- {u}: {d}")
    lines.append("")
    lines.append("## Oddities")
    lines.append("")
    odd = [i for i in infos if i["notes"]]
    for i in odd:
        lines.append(f"- {i['url']} ({i['timestamp']}): " + "; ".join(i["notes"]))
    lines.append("- Slugs and titles drifted: `dia-dos-innosoft-days-2` is titled `Innosoft Days día 3`, `innosoft-days-dia-3` is `día 4`, `conferencia-los-estudios-ingenieria-software-pasado-presente-futuro-2` is `La informática en el descubrimiento del escutoide` (Clara Grima), `-2-2` is `Mujeres en ingeniería`, `tema-a-especificar` is `Ciberseguridad, ¿qué esperan los alumnos...`, `de-devops-a-devsecpos` is `Seguridad cloud-native`, `secureit` is `Ciberseguridad: Retos y necesidades`. Titles win.")
    lines.append("- Two 2022 talk pages point at the same company from different angles (`charla-del-sr-fernando-fernandez-mancera` and `redhat` are both `Charla de Red Hat`, on different days); both kept.")
    lines.append("- Umbrella entries kept as kind `other`: `Innosoft Days 2020` (24-27 Nov, whole edition), `Innosoft Days día 3` and `día 4` (2022, 08:00-18:00 day markers).")
    lines.append("- 2022 events have no room and no organizer in MEC; the linked `Información sobre la ponencia...` posts (family posts_2022) hold the speaker bios.")
    lines.append("- The institucional.us.es capture of `hacia-una-inteligencia-artificial-regenerativa-y-redistributiva` is the same event as the innosoftdays.com URL (same title and start); the innosoftdays.com one is kept and the institucional one is listed as skipped. Its poster URL is the institucional host, mapped to www.innosoftdays.com by norm_media_url.")
    lines.append("")
    lines.append("## Events extracted (start, title, capture used, other captures)")
    lines.append("")
    by_url = {i["url"]: i for i in infos}
    for e in events:
        i = by_url[e["source_url"]]
        extra = f" (also {', '.join(i['others'])})" if i["others"] else ""
        lines.append(f"- {e['starts_at']} [{e['edition_year']}] {e['title']} <{e['source_url']}> capture {e['source_timestamp']}{extra}")
    p = RAW.parent / "extracted" / "parts" / f"{FAMILY}.notes.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
