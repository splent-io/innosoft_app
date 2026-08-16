"""Family "institucional": the university-hosted WordPress (ColorMag theme)
at institucional.us.es/innosoft/ that InnoSoft Days used before
innosoftdays.com.

Captures in scope: every manifest row whose host is institucional.us.es.
They document four editions:

- VI  (2018): /programa/ captured 2019-06-21 still shows the 2018 programme
  (three HTML tables, one per day) and the 2018 header/footer.
- VII (2019): the home page captured 2020-11-04 (welcome text, dates,
  poster on imgur, sponsors).
- VIII (2020): one Modern Events Calendar event page (keynote by Veronica
  Dahl on Twitch) whose header carries the 2020 dates.
- IX  (2021): /programa-ix-edicion/ (MEC monthly calendar, two captures:
  the full month on 2021-11-07 and a later one, ?event-day=20211115, that
  hides the past days but has the corrected programme for 15 and 17 Nov).

Deterministic, no network. Writes data/extracted/parts/institucional.*.json
and the notes file. Run: .venv/bin/python parse/institucional.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import (  # noqa: E402
    EXTRACTED,
    clean_html,
    dump_part,
    edition_number_for_year,
    manifest_rows,
    norm_media_url,
    norm_url,
    parse_spanish_date,
    parse_time,
    roman,
    soup_of,
    text_of,
)

FAMILY = "institucional"
HOST = "institucional.us.es"

MONTHS = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}

# 2018 programme: parenthesised names that are companies, not people.
COMPANIES_2018 = {"Abatic", "Bitnami", "atSistemas", "Sngular", "Geographica"}
# Trailing company names glued to the cell text ("...(David Borrego y Ana Aparicio)atSistemas").
TRAILING_COMPANIES = ("Bitnami", "atSistemas", "Abatic")
# Speakers only visible in the Eventbrite slug (no name in the cell text);
# keyed by the Eventbrite event id, accents restored by hand.
EVENTBRITE_SPEAKERS = {
    "52197348675": "Jesús Utrera y Joaquín Salguero",  # taller YOLO
    "52196865229": "Emilio Pérez y José Segovia",  # PostgreSQL (Abatic)
}
# Kind evidence outside the cell label (innosoftdays.com 2018-11-09 post
# "Material necesario para 'Testing de aplicaciones en Kubernetes'" calls it a taller).
KIND_OVERRIDES_2018 = {"Testing de aplicaciones en Kubernetes": "workshop"}

# 2021 MEC calendar: category colour -> kind, refined by title keywords.
COLOR_KIND = {"#fdd700": "ceremony", "#00a0d2": "talk", "#a3b745": "other"}


def is_in_scope(row: dict) -> bool:
    return HOST in row["url"]


def cap_id(row: dict) -> str:
    return f"{row['url']} @{row['timestamp']}"


def site_header(soup) -> dict:
    """Tagline (#site-description) and the dates line of the header widget."""
    tag = soup.select_one("#site-description")
    dates = None
    for p in soup.select("#header-right-sidebar .textwidget p"):
        t = text_of(p)
        if re.search(r"\d{4}", t) and "noviembre" in t.lower():
            dates = t
    return {"tagline": text_of(tag) if tag else None, "dates_line": dates}


def dates_from_line(line: str | None):
    """'12, 13 y 16 de noviembre de 2018 en la ETSII (Sevilla)' -> (list of dates, venue text)."""
    if not line:
        return [], None
    m = re.search(r"((?:\d{1,2}\s*[,y]\s*)*\d{1,2})\s+de\s+(\w+)\s+(?:de\s+)?(\d{4})(?:\s+en\s+(.+))?", line, re.I)
    if not m:
        return [], None
    days = [int(d) for d in re.findall(r"\d{1,2}", m.group(1))]
    mon = MONTHS.get(m.group(2).lower())
    year = int(m.group(3))
    if not mon:
        return [], None
    return [date(year, mon, d) for d in days], (m.group(4).strip() if m.group(4) else None)


def iso_dt(d: date, hm: str | None) -> str | None:
    if d is None:
        return None
    if not hm:
        return d.isoformat()
    return f"{d.isoformat()}T{hm}:00"


def footer_logos(soup, url: str) -> list[dict]:
    """Sponsor / collaborator logos of the footer widgets."""
    out = []
    foot = soup.find("footer")
    if not foot:
        return out
    for w in foot.select(".widget"):
        title = text_of(w.find(class_="widget-title"))
        if not re.search(r"patrocinador|colaborador|colabolador", title, re.I):
            continue
        label = "Patrocinador" if "atrocinador" in title else "Colaborador"
        for img in w.find_all("img"):
            src = img.get("src")
            if not src:
                continue
            a = img.find_parent("a")
            href = a.get("href") if a else None
            out.append({"url": norm_media_url(src) if HOST in src or src.startswith("/") else norm_url(src), "kind": "logo", "caption": f"{label}" + (f" ({href})" if href else ""), "used_by": [url]})
    return out


def site_logo_media(soup, url: str) -> list[dict]:
    out = []
    logo = soup.select_one("#header-logo-image img")
    if logo and logo.get("src"):
        out.append({"url": norm_media_url(logo["src"]), "kind": "logo", "caption": "Logotipo InnoSoft Days (cabecera)", "used_by": [url]})
    foot = soup.find("footer")
    if foot:
        for img in foot.select("#text-3 img"):
            if img.get("src"):
                out.append({"url": norm_media_url(img["src"] if not img["src"].startswith("/") else "https://" + HOST + img["src"]), "kind": "logo", "caption": "Logotipo InnoSoft Days (pie, versión blanca)", "used_by": [url]})
    return out


# ---------------------------------------------------------------- 2018 (VI)

def split_speakers(s: str | None) -> list[str]:
    if not s:
        return []
    parts = re.split(r"\s*,\s*|\s+y\s+|\s+e\s+(?=I)", s)
    return [p.strip(" .") for p in parts if p.strip(" .")]


def cell_description(td) -> str | None:
    """Cleaned inner HTML of a programme cell (before parse_cell_2018 mutates
    it), without the 'Reserva tu plaza' registration link (kept in `link`)."""
    from bs4 import BeautifulSoup
    frag = BeautifulSoup("<div>" + td.decode_contents() + "</div>", "lxml")
    for a in frag.find_all("a"):
        if "reserva" in text_of(a).lower():
            a.decompose()
    html = clean_html(frag.div)
    html = re.sub(r"^(\s*<br/>\s*)+", "", html)
    html = re.sub(r"\s*<br/>\s*", " ", html)
    html = re.sub(r"\n+", " ", html).strip()
    return html or None


def parse_cell_2018(td) -> dict | None:
    """One programme cell -> {kind, title, speaker, company, link, room_override}."""
    raw_text = text_of(td)
    if not raw_text or raw_text.upper() == "N/A":
        return None
    low = raw_text.lower()
    if low.startswith("descanso") or low.startswith("fin de "):
        return None
    kind = None
    label = td.find(["strong", "b"])
    label_text = text_of(label) if label else ""
    if re.match(r"^conferencia\b", label_text, re.I):
        kind = "talk"
    elif re.match(r"^taller\b", label_text, re.I):
        kind = "workshop"
    elif re.match(r"^proyecci", label_text, re.I):
        kind = "social"
    elif re.match(r"^mesa redonda", label_text, re.I):
        kind = "talk"
    elif re.match(r"^competici", label_text, re.I):
        kind = "competition"
    link = None
    for a in td.find_all("a"):
        if "reserva" in text_of(a).lower():
            link = a.get("href")
            a.decompose()
    if label is not None and kind is not None and re.match(r"^(conferencia|taller|proyecci\w+|mesa redonda)\s*$", label_text.strip(), re.I):
        label.decompose()  # pure kind label; a longer <strong> is the title itself
    body = text_of(td)
    body = re.sub(r"\s+", " ", body).strip(" .")
    unlabeled = kind is None
    if kind is None:
        # unlabeled cells: reception, networking, raffle, plain talks
        if re.match(r"^recepci", body, re.I):
            kind = "other"
        elif re.match(r"^networking", body, re.I):
            kind = "social"
        elif re.search(r"sorteo", body, re.I):
            kind = "other"
        else:
            kind = "talk"
    company = None
    room_override = None
    # 'Mesa redonda: ... (Lugar de esta actividad: CITIUS)'
    m = re.search(r"\(Lugar de esta actividad:\s*([^)]+)\)", body)
    if m:
        room_override = m.group(1).strip()
        body = (body[: m.start()] + body[m.end():]).strip()
    # company glued or in a following <p> right after the closing parenthesis:
    # '(David Borrego y Ana Aparicio)atSistemas', '(Juan Ariza ...). Bitnami'
    m = re.search(r"\)\.?\s*(" + "|".join(TRAILING_COMPANIES) + r")$", body)
    if m:
        company = m.group(1)
        body = body[: m.start() + 1].strip(" .")
    speaker = None
    m = re.search(r"\(([^()]+)\)\s*$", body)
    if m:
        inner = m.group(1).strip()
        if inner in COMPANIES_2018:
            company = inner
        elif unlabeled and kind in ("social", "other"):
            room_override = inner  # 'Networking / Desayuno (CITIUS Celestino Mutis)'
        else:
            speaker = inner
        body = body[: m.start()].strip()
    # 'Introducción a Sngular – Inmaculada Rodríguez Vizcaína Introducción a Sass – María del Carmen García Peral'
    if speaker is None and " – " in body:
        pieces = [p.strip() for p in re.split(r"\s+–\s+", body)]
        # alternate title/speaker; the second title starts with a capital word after the speaker name
        titles, names = [], []
        # Split by known pattern 'Introducción a X – Name' twice
        mm = re.findall(r"(Introducción a [^–]+?) – ([A-ZÁÉÍÓÚ][^–]+?)(?=\s+Introducción a |$)", body)
        if mm:
            titles = [t.strip() for t, _ in mm]
            names = [n.strip() for _, n in mm]
            body = " / ".join(titles)
            speaker = " y ".join(names)
        elif len(pieces) == 2:
            body, speaker = pieces
    if link and speaker is None:
        m = re.search(r"-(\d{9,})/?$", link)
        if m and m.group(1) in EVENTBRITE_SPEAKERS:
            speaker = EVENTBRITE_SPEAKERS[m.group(1)]
    body = re.sub(r"\s+", " ", body).strip(" .:")
    if not body:
        return None
    if body in KIND_OVERRIDES_2018:
        kind = KIND_OVERRIDES_2018[body]
    return {"kind": kind, "title": body, "speaker": speaker, "company": company, "link": link, "room_override": room_override}


def parse_programme_2018(row: dict, out: dict) -> None:
    soup = soup_of(row)
    url, ts = row["url"], row["timestamp"]
    hdr = site_header(soup)
    days, venue_txt = dates_from_line(hdr["dates_line"])
    year = days[0].year if days else 2018
    content = soup.select_one(".entry-content")
    events = []
    offschedule_html = ""
    for cont in content.select(".schedule-container"):
        h = cont.find("h1")
        day = parse_spanish_date(text_of(h), default_year=year)
        # off-schedule activities (13 Nov 2018): a <ul> before the table
        ul = cont.find("ul")
        if ul is not None and day is not None:
            offschedule_html = clean_html(cont.find("p")) + clean_html(ul)
            for li in ul.find_all("li"):
                b = li.find("b")
                name = text_of(b).strip(" :") if b else text_of(li).split(":")[0]
                rest = text_of(li)[len(text_of(b)):].strip(" :") if b else text_of(li)
                start, end = parse_time(rest)
                room = None
                m = re.search(r"en (?:el |la )?(Aula [A-Z]\d\.\d+|Sala de estudios)", rest)
                if m:
                    room = m.group(1).replace("Aula ", "")
                low = name.lower()
                if "torneo" in low or "gymkhana" in low or "trivia" in low:
                    kind = "competition"
                elif "software room" in low:
                    kind = "other"
                elif "museo" in low:
                    kind = "stand"
                else:
                    kind = "other"
                events.append({
                    "edition_year": year, "title": name, "kind": kind,
                    "starts_at": iso_dt(day, start), "ends_at": iso_dt(day, end) if end else None,
                    "room": room, "modality": "in_person", "speaker": None, "company": None,
                    "summary": rest, "description_html": clean_html(li), "poster_url": None,
                    "link": None, "lang": "es", "source_url": url, "source_timestamp": ts,
                })
        table = cont.find("table")
        if table is None or day is None:
            continue
        rows = table.find_all("tr")
        header = [text_of(th) for th in rows[0].find_all(["th", "td"])]
        rooms = header[1:]
        ncols = len(rooms)
        # grid fill with rowspans: occupied[col] = rows remaining
        occupied = [0] * ncols
        slots = []  # (start, end) per data row
        pending = []  # events with rowspan awaiting end time: (event, rows_left)
        for tr in rows[1:]:
            tds = tr.find_all("td")
            if not tds:
                continue
            first = tds[0]
            if first.get("colspan") and int(first.get("colspan")) >= ncols + 1:
                continue  # 'Fin de las actividades del día'
            start, end = parse_time(text_of(first))
            occupied = [max(0, o - 1) for o in occupied]
            for ev, left in pending:
                if left > 0:
                    ev["ends_at"] = iso_dt(day, end) if end else ev["ends_at"]
            pending = [(ev, left - 1) for ev, left in pending if left - 1 > 0]
            col = 0
            for td in tds[1:]:
                while col < ncols and occupied[col] > 0:
                    col += 1
                if col >= ncols:
                    break
                span = int(td.get("colspan") or 1)
                rspan = int(td.get("rowspan") or 1)
                desc = cell_description(td)
                cell = parse_cell_2018(td)
                if cell:
                    room = cell.pop("room_override") or (rooms[col] if span == 1 else " / ".join(rooms[col:col + span]))
                    ev = {
                        "edition_year": year, "title": cell["title"], "kind": cell["kind"],
                        "starts_at": iso_dt(day, start), "ends_at": iso_dt(day, end) if end else None,
                        "room": room, "modality": "in_person", "speaker": cell["speaker"], "company": cell["company"],
                        "summary": None, "description_html": desc, "poster_url": None,
                        "link": cell["link"], "lang": "es", "source_url": url, "source_timestamp": ts,
                    }
                    events.append(ev)
                    if rspan > 1:
                        pending.append((ev, rspan - 1))
                else:
                    cell = None
                for c in range(col, min(ncols, col + span)):
                    occupied[c] = rspan
                col += span
        # unlabeled speaker for the round table lives only in the Eventbrite slug; keep as note
    out["events"].extend(events)
    ed_year = year
    out["editions"].append({
        "year": ed_year, "number": edition_number_for_year(ed_year), "roman": roman(edition_number_for_year(ed_year)),
        "name": f"InnoSoft Days {ed_year}",
        "starts_on": min(days).isoformat() if days else None, "ends_on": max(days).isoformat() if days else None,
        "venue": "ETSII, Universidad de Sevilla (Av. Reina Mercedes, Sevilla)",
        "summary": f"{hdr['tagline']}. {hdr['dates_line']}." if hdr["tagline"] else hdr["dates_line"],
        "description_html": f"<p>{hdr['tagline']}</p><p>{hdr['dates_line']}</p>" + (f"<h3>Actividades fuera de horario (13 de noviembre)</h3>{offschedule_html}" if offschedule_html else ""),
        "registration_url": None,
        "sources": [url], "confidence": "high",
        "notes": f"Header tagline and dates line of the institutional site as captured on {ts[:8]} (the site still showed the 2018 edition). Programme tables give the per-day schedule; venue is the footer address.",
    })
    for m in site_logo_media(soup, url) + footer_logos(soup, url):
        m["edition_year"] = ed_year if "Patrocinador" in m["caption"] or "Colaborador" in m["caption"] else None
        out["media"].append(m)
    out["log"].append(f"- {cap_id(row)} | programme VI (2018): {len(events)} events, edition, {hdr['dates_line']}")


# ---------------------------------------------------------------- 2019 (VII) home

def parse_home_2019(row: dict, out: dict) -> None:
    soup = soup_of(row)
    url, ts = row["url"], row["timestamp"]
    hdr = site_header(soup)
    days, venue_txt = dates_from_line(hdr["dates_line"])
    year = days[0].year if days else 2019
    content = soup.select_one("#content")
    desc_parts = []
    poster = None
    video = None
    for sec in content.select("section.widget"):
        title = text_of(sec.find(class_="widget-title"))
        if sec.select_one("video"):
            src = sec.select_one("video source")
            v = (src.get("src") if src else None) or (sec.find("a").get("href") if sec.find("a") else None)
            if v:
                video = re.sub(r"&_=\d+$", "", v)
        elif title.lower() == "cartel":
            img = sec.find("img")
            if img and img.get("src"):
                poster = norm_url(img["src"])
        elif sec.select_one(".textwidget"):
            desc_parts.append(clean_html(sec.select_one(".textwidget")))
    desc = "".join(desc_parts)
    if video:
        desc += f'<p><a href="{video}">Vídeo de presentación (YouTube)</a></p>'
    if poster:
        desc += f'<figure><img src="{poster}" alt="Cartel InnoSoft Days {year}"/><figcaption>Cartel</figcaption></figure>'
    text = text_of(BeautifulSoupSafe(desc))
    m = re.search(r"harán hincapié en el ([^.]+)\.", text)
    theme = hdr["tagline"]
    out["editions"].append({
        "year": year, "number": edition_number_for_year(year), "roman": roman(edition_number_for_year(year)),
        "name": f"InnoSoft Days {year}",
        "starts_on": min(days).isoformat() if days else None, "ends_on": max(days).isoformat() if days else None,
        "venue": "ETSII, Universidad de Sevilla (Av. Reina Mercedes, Sevilla)",
        "summary": f"{theme}. {hdr['dates_line']}." + (f" Las jornadas hacen hincapié en el {m.group(1).strip()}." if m else ""),
        "description_html": desc,
        "registration_url": None,
        "sources": [url], "confidence": "high",
        "notes": f"Home page of the institutional site captured {ts[:8]}, still showing the {year} edition (welcome text 'InnoSoft Days {year}', tagline, dates line, poster on imgur, YouTube video). The 'INSCRIPCIONES' menu link (institucional.us.es/innosoft/inscipciones/) is not kept as registration_url (dead, 404 in 2024).",
    })
    if poster:
        out["media"].append({"url": poster, "kind": "poster", "edition_year": year, "caption": f"Cartel InnoSoft Days {year} (imagen externa, imgur)", "used_by": [url]})
    for mm in site_logo_media(soup, url) + footer_logos(soup, url):
        mm["edition_year"] = year if "Patrocinador" in mm["caption"] or "Colaborador" in mm["caption"] else None
        out["media"].append(mm)
    out["log"].append(f"- {cap_id(row)} | home showing VII ({year}): edition, poster, {hdr['dates_line']}")


def BeautifulSoupSafe(html: str):
    from bs4 import BeautifulSoup
    return BeautifulSoup(html or "", "lxml")


# ---------------------------------------------------------------- 2020 (VIII) MEC event

MONTHS_EN_ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def parse_mec_event_2020(row: dict, out: dict) -> None:
    soup = soup_of(row)
    url, ts = row["url"], row["timestamp"]
    hdr = site_header(soup)
    days, _ = dates_from_line(hdr["dates_line"])
    title = text_of(soup.select_one(".mec-single-title") or soup.find("h1"))
    d = None
    dl = soup.select_one(".mec-start-date-label")
    if dl:
        m = re.match(r"([A-Za-z]{3})\w*\s+(\d{1,2})\s+(\d{4})", text_of(dl))
        if m and m.group(1).lower() in MONTHS_EN_ABBR:
            d = date(int(m.group(3)), MONTHS_EN_ABBR[m.group(1).lower()], int(m.group(2)))
    tm = soup.select_one(".mec-single-event-time abbr")
    start, end = parse_time(text_of(tm))
    loc = soup.select_one(".mec-single-event-location .mec-address")
    loc_url = soup.select_one(".mec-single-event-location .mec-location-url a")
    org = soup.select_one(".mec-single-event-organizer .mec-organizer h6")
    org_url = soup.select_one(".mec-single-event-organizer .mec-organizer-url a")
    img = soup.select_one(".mec-events-event-image img")
    poster = norm_media_url(img["src"]) if img and img.get("src") else None
    desc = clean_html(soup.select_one(".mec-single-event-description")) or None
    cat = text_of(soup.select_one(".mec-events-event-categories a"))
    year = d.year if d else (int(cat) if cat.isdigit() else 2020)
    location = text_of(loc)
    online = "twitch" in location.lower() or (loc_url is not None and "twitch" in (loc_url.get("href") or ""))
    speaker = text_of(org) or None
    ev = {
        "edition_year": year, "title": title, "kind": "talk",
        "starts_at": iso_dt(d, start), "ends_at": iso_dt(d, end) if end else None,
        "room": None if online else location, "modality": "online" if online else "in_person",
        "speaker": speaker, "company": None,
        "summary": None, "description_html": desc, "poster_url": poster,
        "link": (loc_url.get("href") if loc_url else None), "lang": "es",
        "source_url": url, "source_timestamp": ts,
    }
    out["events"].append(ev)
    if speaker:
        links = []
        if org_url is not None and org_url.get("href"):
            links.append({"label": "Web", "url": org_url["href"]})
        out["speakers"].append({"name": speaker, "affiliation": None, "position": None, "bio_html": None, "photo_url": None, "links": links, "edition_years": [year], "source_url": url})
    if poster:
        out["media"].append({"url": poster, "kind": "poster", "edition_year": year, "caption": f"Cartel: {title}", "used_by": [url]})
    for mm in site_logo_media(soup, url) + footer_logos(soup, url):
        mm["edition_year"] = year if "Patrocinador" in mm["caption"] or "Colaborador" in mm["caption"] else None
        out["media"].append(mm)
    out["editions"].append({
        "year": year, "number": edition_number_for_year(year), "roman": roman(edition_number_for_year(year)),
        "name": f"InnoSoft Days {year}",
        "starts_on": min(days).isoformat() if days else None, "ends_on": max(days).isoformat() if days else None,
        "venue": "Online (Twitch, https://www.twitch.tv/innosoftdays)" if online else "ETSII, Universidad de Sevilla",
        "summary": f"{hdr['tagline']} {hdr['dates_line']}." if hdr["tagline"] else hdr["dates_line"],
        "description_html": f"<p>{hdr['tagline']}</p><p>{hdr['dates_line']}</p>",
        "registration_url": None,
        "sources": [url], "confidence": "medium",
        "notes": f"Only the header (tagline + dates line) of an event page captured {ts[:8]} documents the edition; the keynote ran on 'Twitch Innosoft', hence online. The footer still lists the ETSII address as 'Localización'.",
    })
    out["log"].append(f"- {cap_id(row)} | MEC event VIII ({year}): '{title}' {ev['starts_at']}-{end}, speaker {speaker}")


# ---------------------------------------------------------------- 2021 (IX) MEC calendar

def kind_2021(title: str, color: str) -> str:
    base = COLOR_KIND.get(color.lower(), "other")
    low = title.lower()
    if base == "other":
        if "torneo" in low or "programación competitiva" in low or "programacion competitiva" in low:
            return "competition"
        if "quedada" in low:
            return "social"
        if "introducción al hacking" in low or "introduccion al hacking" in low:
            return "workshop"
        return "other"
    return base


def calendar_events_2021(row: dict) -> dict[str, list[dict]]:
    """day 'YYYYMMDD' -> events listed for that day in this capture."""
    soup = soup_of(row)
    url, ts = row["url"], row["timestamp"]
    per_day: dict[str, list[dict]] = {}
    for sec in soup.select(".mec-calendar-events-sec"):
        cell = sec.get("data-mec-cell")
        arts = sec.select("article.mec-event-article")
        evs = []
        for a in arts:
            t = a.select_one(".mec-event-title a")
            if not t:
                continue
            title = text_of(t)
            col = a.select_one(".event-color")
            color = ""
            if col is not None:
                m = re.search(r"#[0-9a-fA-F]{6}", col.get("style") or "")
                color = m.group(0) if m else ""
            start, end = parse_time(text_of(a.select_one(".mec-event-time")))
            room = text_of(a.select_one(".mec-event-loc-place")) or None
            d = date(int(cell[:4]), int(cell[4:6]), int(cell[6:8]))
            evs.append({
                "edition_year": d.year, "title": title, "kind": kind_2021(title, color),
                "starts_at": iso_dt(d, start), "ends_at": iso_dt(d, end) if end else None,
                "room": room, "modality": "in_person", "speaker": None, "company": None,
                "summary": None, "description_html": None, "poster_url": None,
                "link": norm_url(t.get("href")), "lang": "es",
                "source_url": url, "source_timestamp": ts,
            })
        if evs:
            per_day[cell] = evs
    return per_day, soup


def parse_calendar_2021(rows: list[dict], out: dict) -> None:
    """Merge the captures of the IX calendar: the later capture hides days
    already past, so each day comes from the LATEST capture that lists it."""
    rows = sorted(rows, key=lambda r: r["timestamp"])
    merged: dict[str, list[dict]] = {}
    origin: dict[str, str] = {}
    hdr = None
    soups = {}
    for r in rows:
        per_day, soup = calendar_events_2021(r)
        soups[r["timestamp"]] = soup
        h = site_header(soup)
        if h["dates_line"]:
            hdr = h
        for day, evs in per_day.items():
            merged[day] = evs
            origin[day] = cap_id(r)
        out["log"].append(f"- {cap_id(r)} | IX calendar: days with events {sorted(per_day)} ({sum(len(v) for v in per_day.values())} events)")
    events = [e for day in sorted(merged) for e in merged[day]]
    out["events"].extend(events)
    days, _ = dates_from_line(hdr["dates_line"] if hdr else None)
    year = days[0].year if days else 2021
    last = rows[-1]
    out["editions"].append({
        "year": year, "number": edition_number_for_year(year), "roman": roman(edition_number_for_year(year)),
        "name": f"InnoSoft Days {year}",
        "starts_on": min(days).isoformat() if days else None, "ends_on": max(days).isoformat() if days else None,
        "venue": "ETSII, Universidad de Sevilla (Av. Reina Mercedes, Sevilla)",
        "summary": f"{hdr['tagline']} {hdr['dates_line']}." if hdr and hdr["tagline"] else (hdr["dates_line"] if hdr else None),
        "description_html": (f"<p>{hdr['tagline']}</p><p>{hdr['dates_line']}</p>" if hdr else ""),
        "registration_url": None,
        "sources": [r["url"] for r in rows], "confidence": "high",
        "notes": "Tagline and dates line of the IX-edition header; the MEC calendar lists the programme per day (8, 10, 15, 17 Nov 2021). Days 15 and 17 come from the later ?event-day capture (corrected programme), days 8 and 10 from the 2021-11-07 capture. Speaker names live on /ponentes-ix-edicion/, not captured.",
    })
    for r in rows:
        soup = soups[r["timestamp"]]
        for mm in site_logo_media(soup, r["url"]) + footer_logos(soup, r["url"]):
            mm["edition_year"] = year if "Patrocinador" in mm["caption"] or "Colaborador" in mm["caption"] else None
            out["media"].append(mm)
    out["merge_2021"] = {d: origin[d] for d in sorted(origin)}


# ---------------------------------------------------------------- speakers from 2018 events

def speakers_from_events(events: list[dict], year: int) -> list[dict]:
    seen = {}
    for e in events:
        if e["edition_year"] != year or not e["speaker"]:
            continue
        for name in split_speakers(e["speaker"]):
            if len(name.split()) < 2:
                continue
            sp = seen.setdefault(name, {"name": name, "affiliation": e["company"], "position": None, "bio_html": None, "photo_url": None, "links": [], "edition_years": [year], "source_url": e["source_url"]})
            if not sp["affiliation"] and e["company"]:
                sp["affiliation"] = e["company"]
    return list(seen.values())


def dedupe_media(items: list[dict]) -> list[dict]:
    by = {}
    for m in items:
        k = (m["url"], m.get("edition_year"))
        if k in by:
            for u in m["used_by"]:
                if u not in by[k]["used_by"]:
                    by[k]["used_by"].append(u)
            if not by[k]["caption"] and m["caption"]:
                by[k]["caption"] = m["caption"]
        else:
            by[k] = {"url": m["url"], "kind": m["kind"], "edition_year": m.get("edition_year"), "caption": m["caption"], "used_by": list(m["used_by"])}
    return list(by.values())


def main() -> None:
    rows = [r for r in manifest_rows() if is_in_scope(r)]
    rows.sort(key=lambda r: (r["url"], r["timestamp"]))
    out = {"editions": [], "events": [], "speakers": [], "media": [], "log": [], "skipped": []}
    by_url = defaultdict(list)
    for r in rows:
        by_url[r["url"]].append(r)

    for url, caps in by_url.items():
        path = url.split(HOST, 1)[1]
        if path.startswith("/innosoft/wp-content/plugins/"):
            for c in caps:
                out["skipped"].append(f"- {cap_id(c)}: plugin asset (theme/plugin image), not site content")
            continue
        if path.startswith("/innosoft/wp-content/uploads/"):
            for c in caps:
                out["log"].append(f"- {cap_id(c)} | upload binary (site logo): listed in media.json as kind logo under its www.innosoftdays.com path, nothing to parse")
            continue
        if path == "/innosoft/":
            for c in caps:
                if c.get("bytes", 0) == 0:
                    out["skipped"].append(f"- {cap_id(c)}: empty capture (0 bytes)")
                else:
                    parse_home_2019(c, out)
            continue
        if path.startswith("/innosoft/programa/"):
            for c in caps:
                parse_programme_2018(c, out)
            continue
        if path.startswith("/innosoft/programa-ix-edicion/"):
            continue  # merged below
        if path.startswith("/innosoft/events/"):
            latest = max(caps, key=lambda c: c["timestamp"])
            latest_text = text_of(soup_of(latest).select_one("#main"))
            for c in caps:
                if c is latest:
                    parse_mec_event_2020(c, out)
                elif text_of(soup_of(c).select_one("#main")) == latest_text:
                    out["skipped"].append(f"- {cap_id(c)}: older capture, main content text identical to the latest capture @{latest['timestamp']}")
                else:
                    parse_mec_event_2020(c, out)
            continue
        for c in caps:
            out["skipped"].append(f"- {cap_id(c)}: URL not handled by this parser")

    cal_rows = [r for r in rows if "/innosoft/programa-ix-edicion/" in r["url"]]
    if cal_rows:
        parse_calendar_2021(cal_rows, out)

    out["speakers"] = speakers_from_events(out["events"], 2018) + out["speakers"]
    out["media"] = dedupe_media(out["media"])
    out["editions"].sort(key=lambda e: e["year"])
    out["events"].sort(key=lambda e: (e["edition_year"], e["starts_at"] or "", e["room"] or "", e["title"]))

    dump_part(f"{FAMILY}.editions.json", out["editions"])
    dump_part(f"{FAMILY}.events.json", out["events"])
    dump_part(f"{FAMILY}.speakers.json", out["speakers"])
    dump_part(f"{FAMILY}.media.json", out["media"])
    write_notes(rows, out)
    print(f"captures in scope {len(rows)}; editions {len(out['editions'])}, events {len(out['events'])}, speakers {len(out['speakers'])}, media {len(out['media'])}, skipped {len(out['skipped'])}")


def write_notes(rows: list[dict], out: dict) -> None:
    ev_by_year = Counter(e["edition_year"] for e in out["events"])
    kinds = Counter((e["edition_year"], e["kind"]) for e in out["events"])
    lines = [
        f"# {FAMILY}", "",
        "Captures of the university-hosted WordPress (institucional.us.es/innosoft/, ColorMag theme, WordPress 4.8) used before",
        "innosoftdays.com. Every manifest row whose host is institucional.us.es is in scope.",
        f"Captures in scope: {len(rows)}. Extracted: {len(rows) - len(out['skipped'])}. Skipped: {len(out['skipped'])} (listed below with the reason).", "",
        "## Years documented by the institutional captures", "",
        "The captured pages carry the site header of the edition that was current when the archive visited, so the",
        "captures document four editions (not only the capture years):", "",
        "- VI (2018): /programa/ captured 2019-06-21 still shows '50 años de la Ingeniería del Software', '12, 13 y 16 de noviembre de 2018 en la ETSII (Sevilla)' and the three programme tables of 2018.",
        "- VII (2019): the home page captured 2020-11-04 still shows the 2019 edition ('La Web cumple 30 años', '4, 5 y 6 de noviembre de 2019 en la ETSII (Sevilla)', welcome text 'InnoSoft Days 2019', poster on imgur, YouTube video).",
        "- VIII (2020): the MEC event page (keynote of Verónica Dahl, 27 Nov 2020 20:30-21:30 on Twitch) with the 2020 header '¡Ok Google, apúntame a Innosoft!', '24, 26 y 27 de noviembre 2020'.",
        "- IX (2021): /programa-ix-edicion/ (MEC monthly calendar) with the header '¡Ponencias sobre ciberseguridad!', '8, 10, 15 y 17 de noviembre 2021'.", "",
        "## Outputs", "",
        f"- editions.json: {len(out['editions'])} editions ({', '.join(str(e['year']) + ' ' + e['confidence'] for e in out['editions'])})",
        f"- events.json: {len(out['events'])} events ({', '.join(f'{y}: {n}' for y, n in sorted(ev_by_year.items()))})",
        f"- speakers.json: {len(out['speakers'])} speakers (2018 names parsed from the programme cells; 2020 Verónica Dahl from the MEC 'Organizador' field)",
        f"- media.json: {len(out['media'])} images (site logos, sponsor/collaborator logos of the footer, the 2019 poster on imgur, the 2020 keynote image)",
        "- posts.json / organisers.json / pages.json: not written (see skipped and gaps)", "",
        "Kinds per year: " + "; ".join(f"{y} {k}={n}" for (y, k), n in sorted(kinds.items())), "",
        "## Extracted captures", "",
        *out["log"], "",
        "## Skipped captures", "",
        *out["skipped"], "",
        "## Not fetched (in the CDX index but not in the manifest)", "",
        "- https://institucional.us.es/innosoft/category/noticias/ @20211115123930 (200, 12681 bytes): the news listing was classified 'noise' by cdx_index.py and never fetched, so no post teasers could be extracted (posts.json not written by this family). Rerun fetch.py with that URL if the teasers are wanted.",
        "- The 2024 and 2026 captures of the institutional URLs are 404/302 (site gone), not fetched.", "",
        "## How the data was read", "",
        "- Header: '#site-description' is the edition tagline (theme); the last <p> of '#header-right-sidebar' is the dates line ('12, 13 y 16 de noviembre de 2018 en la ETSII (Sevilla)'); starts_on/ends_on are the min/max of the listed days. Venue is the footer 'Localización' (ETSII, Av. Reina Mercedes, Sevilla), except 2020 (Twitch).",
        "- 2018 programme: three <table class='schedule'> (one per day, day in the preceding <h1>). Header row = 'Hora' + rooms; cells are placed on a grid honouring colspan/rowspan, and a rowspan extends ends_at to the end of the last covered row (Blockchain 15:30-17:20, taller YOLO 17:30-19:00, competición Bitnami 18:30-19:30). The <strong> label of the cell gives the kind (Conferencia=talk, Taller=workshop, Proyección=social, Mesa Redonda=talk, Competición=competition); unlabeled cells: Recepción/sorteo=other, Networking=social, otherwise talk. 'Descanso' and 'Fin de ...' rows are not events. Off-schedule activities (Software Room, TOURNAMETSII, Gymkhana, Trivia, Museo interactivo) come from the <ul> above the 13 Nov table (times/rooms parsed from the text when stated).",
        "- 2018 speakers: the parenthesised names at the end of the cell ('Los estudios de Ingeniería de Software... (Amador Durán y José Luis Sevillano)'); parenthesised company names (Abatic) and trailing glued company names ('...(David Borrego y Ana Aparicio)atSistemas', '<p>Bitnami</p>') go to company. Two cells have no name in the text; their Eventbrite slug does (taller YOLO -> Jesús Utrera y Joaquín Salguero; PostgreSQL/Abatic -> Emilio Pérez y José Segovia), accents restored by hand in the parser. The mesa redonda slug says 'mesa-redonda-con-david-benavides' (kept out of speaker, moderator not stated in the page). The 'Reserva tu plaza' Eventbrite/registration URL is the event link.",
        "- 2020 event: MEC single-event template; date from .mec-start-date-label ('Nov 27 2020'), time from .mec-single-event-time (20:30 - 21:30, displayed local time; the Google Calendar link writes the same digits with a Z suffix, MEC does not convert), location 'Twitch Innosoft' with URL twitch.tv/innosoftdays (modality online, link), category '2020', 'Organizador' = Verónica Dahl with her web page (used as speaker; MEC has no speaker module here). Description is empty in the capture. The featured image IA-regenarativa-min.jpg is the poster.",
        "- 2021 calendar: .mec-calendar-events-sec[data-mec-cell] per day, article.mec-event-article with time, title/link, room and a category colour (#fdd700 ceremony, #00a0d2 talk, #a3b745 activities -> competition/social/workshop by title keywords). Merge of the two captures: each day is taken from the LATEST capture that lists it (the ?event-day=20211115 capture hides past days). Days 8 and 10 Nov: 2021-11-07 capture; days 15 and 17 Nov: 2021-11-14 capture, which splits 'Introducción al hacking' (08:30-12:30) into four hourly slots, moves 'Ciberseguridad, ¿qué esperan los alumnos...' from A3.11 to H1.10, drops 'De que hablamos cuando hablamos de ciberseguridad' (17:30 H1.10) and fixes the title 'Identificación de ciber-inseguridades'. Speakers are not on the calendar (the /ponentes-ix-edicion/ page was not captured); event links point at institucional.us.es/innosoft/events/... (not captured either).",
        "- Media URLs: uploads under institucional.us.es/innosoft/wp-content/ are mapped to www.innosoftdays.com/wp-content/ by norm_media_url() (same paths after the move, as the other families do); the site logo logo_2_negro-e1540204473260.png exists in the raw uploads under both hosts. IA-regenarativa-min.jpg (2020/11) is not in the CDX index. Sponsor logos hosted elsewhere (bitnami.com, imgur, elpatriarca.com...) keep their external URL.",
        "", "## Oddities", "",
        "- The 2020-11-04 home capture is NOT the 2020 edition: on that date the site still served the 2019 home (widget 'InnoSoft Days 2019', copyright 2018); the 2020 site had its own header by 2020-11-23 (event page).",
        "- The 2019 programme (VII) is not captured: /programa/ was archived in June 2019 and still showed 2018; the 2020 programme page (/programa-viii-edicion/) and the 2019/2020/2021 speakers pages were never archived.",
        "- 2018 tables use inconsistent markup (title in <p> or bare text after <br>, speaker sometimes in the next <p>, 'Reserva tu plaza' inside or outside <p>); the parser works on the cell text after removing the label and the link.",
        "- 2018 cell 'Introducción a Sngular – Inmaculada Rodríguez Vizcaína / Introducción a Sass – María del Carmen García Peral' is one 15:30-16:20 slot with one Eventbrite link: kept as one event with both titles and both speakers (company left null; Sngular only appears inside the first title).",
        "- The 2019 poster is an external image (i.imgur.com/IaHdCku.png), so is the OpenWebinars sponsor logo; the importer cannot resolve them from raw uploads.",
        "- The 2019 home menu had 'INSCRIPCIONES' -> /innosoft/inscipciones/ (sic); not used as registration_url (dead link).",
        "- The two captures of the 2020 event page differ only in nonces/timestamps in scripts; the earlier one is skipped as identical.",
        "- IX calendar day 15: the 2021-11-07 capture listed a single 4-hour 'Introducción al hacking' (A3.11); the later capture lists 'Introducción al hacking 1..4' as hourly slots. Only the later version is kept (no duplicates).",
    ]
    if out.get("merge_2021"):
        lines += ["", "## IX calendar merge (day -> capture used)", ""] + [f"- {d}: {c}" for d, c in out["merge_2021"].items()]
    (EXTRACTED / "parts" / f"{FAMILY}.notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
