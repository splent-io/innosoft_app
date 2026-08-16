"""Family events_eventos_etn: the XII edition (2024) programme as published by
two WordPress event plugins that coexisted on innosoftdays.com in 2024/25.

- /event/<slug>/   The Events Calendar (tribe): dated schedule with categories,
                   posters as featured image, venue = the ETSII.
- /eventos/<slug>/ Eventin (etn_*): the same activities with rooms, 12h times,
                   speaker photos and longer descriptions.
- /etn_category/<slug>/ Eventin archive listings (ponente, taller, torneo):
                   used for the /eventos/ pages that were never fetched
                   (title, excerpt, image only, undated).
- /etn_category-N/ and /mec-category/<year>/: empty archives (skipped).

Both plugins describe the same real activities, so ETN pages are merged into
their TEC counterpart through an explicit slug map (MERGE) instead of emitting
the same talk twice. Every capture in scope is either extracted or listed as
skipped in the notes file.

Run: .venv/bin/python parse/events_eventos_etn.py
Writes data/extracted/parts/events_eventos_etn.{editions,events,speakers,media}.json
and data/extracted/parts/events_eventos_etn.notes.md
"""

from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import (  # noqa: E402
    EXTRACTED, best_srcset_url, clean_html, dump_part, edition_number_for_year,
    fix_lazy_images, latest_per_url, manifest_rows, norm_url, roman, soup_of, text_of,
)

FAMILY = "events_eventos_etn"
SITE = "https://www.innosoftdays.com"
CONTEXT_YEAR = 2024  # every page in scope belongs to InnoSoft Days XII
TEC_RE = re.compile(r"^https://www\.innosoftdays\.com/event/([^/]+)/$")
ETN_RE = re.compile(r"^https://www\.innosoftdays\.com/eventos/([^/]+)/$")
ETN_CAT_RE = re.compile(r"^https://www\.innosoftdays\.com/etn_category/([^/]+)/$")
EMPTY_CAT_RE = re.compile(r"^https://www\.innosoftdays\.com/(etn_category-\d+|mec-category/\d{4})/$")

# ETN slug -> TEC slug: the same activity published by both plugins (matched by
# person / date / start time by hand, see notes). Merged into one event.
MERGE = {
    "conectando-personas-y-empresas-a-traves-de-valores-carlos-sanchis-pedregosa": "charla-emprendimiento-carlos-sanchis-pedregosa",
    "david-lopez-carrascal-y-juan-antonio-cabeza-sousa": "charla-inteligencia-artificial-david-lopez-carrascal-y-juan-antonio-cabeza-sousa",
    "emprendimiento-javier-maria-de-domingo-morales": "charla-emprendimiento-javier-maria-de-domingo",
    "ignasi-labastida-i-juan": "charla-emprendimiento-ignasi-labastida-i-juan",
    "introduccion-a-la-ciberseguridad": "taller-de-introduccion-a-la-cibersegurirdad",
    "raul-lopez-garcia": "charla-laboral-raul-lopez-garcia",
    "rrhh-nttdata": "charla-laboral-rrhh-nttdata",
    "volum-pablo-perez-y-alberto-olmo": "charla-investigacion-pablo-perez-y-alberto-olmo",
    "ceremonia-de-clausura": "ceremonia-clausura",
    "torneo-cs2-cuartos-y-semis": "torneo-cs2-primera-ronda",
    "torneo-lol-cuartos-y-semis": "torneo-lol-primera-ronda",
    "yincana-turno-manana": "yincana-inauguracion-innosoft-days",
    # listing-only ETN slugs (no single page fetched)
    "yincana-turno-tarde": "yincana-inauguracion-innosoft-days-2",
    "pensamiento-computacional": "taller-pensamiento-computacional",
    "rafael-m-guitart": "charla-sostenibilidad-rafael-m-guitart",
    "jose-antonio-perez": "charla-iguldad-jose-antonio-perez",
    "sol-y-ciberseguridad-anabel-carmona-gutierrez": "charla-sostenibilidad-anabel-carmona-gutierrez",
    "toneo-lol-final": "final-torneo-lol",
    "torneo-pokemon-showdown-final": "final-torneo-pokemon-showdown",
    "torneo-pokemon-showdown": "torneo-pokemon-showdown",
    "torneo-rocket-league": "torneo-rocket-league",
}

# Typos in the TEC titles, fixed for the product (originals kept in notes).
TITLE_FIXES = {"Cibersegurirdad": "Ciberseguridad", "Iguldad": "Igualdad"}

# Spelling variants of the same person across the two plugins.
NAME_ALIASES = {
    "Carlos Sanchis Pedregosa": "Carlos Sanchís Pedregosa",
    "Raul López García": "Raúl López García",
    "Jose Antonio Pérez": "José Antonio Pérez",
    "Javier María de Domingo": "Javier María de Domingo Morales",
    "Jose Luis Fontenla": "José Luis Fontenla",
}

# Affiliation / position stated in the pages themselves (ETN bios, TEC blurbs).
SPEAKER_INFO = {
    "Anabel Carmona Gutiérrez": ("Maxeon Solar Technologies", None),
    "Carlos Sanchís Pedregosa": (None, "Emprendedor, spin-off de la Universidad de Sevilla"),
    "David López Carrascal": ("Sevilla FC", "Head of Software Development"),
    "Juan Antonio Cabeza Sousa": ("Sevilla FC", "Analista"),
    "Ignasi Labastida i Juan": ("Creative Commons España / SPARC Europe", "Líder del proyecto Creative Commons España"),
    "Javier María de Domingo Morales": (None, None),
    "José Luis Fontenla": ("Rewoox", "CTO"),
    "María Mendoza": ("Rewoox", "Directora de Innovación"),
    "Pablo Pérez": ("Universidad de Sevilla (DTE)", "Profesor"),
    "Alberto Olmo": ("Universidad de Sevilla (DTE)", "Profesor"),
    "Raúl López García": ("NTT Data", "Digital Transformation Executive"),
    "Pablo Pino": (None, "Exalumno de la ETSII, creador de los CTF de 2023"),
    "José Antonio Pérez": (None, "Psicólogo especialista en gestión de emociones"),
    "Rafael M Guitart": (None, "Profesor, ex director de la reserva científica de Doñana"),
    "Irene M Morgado": (None, "Experta en perfiles informáticos"),
    "Andrés y Adolfo": ("4i.ai", None),
}
# Talks given on behalf of a company (no named person).
COMPANY_TALKS = {"RRHH NttData": "NTT Data", "NttData": "NTT Data", "4i.ai": "4i.ai"}
NOT_A_PERSON = {"RRHH NttData", "NttData"}

KIND_ORDER = [
    ("ceremony", ("ceremonia",)),
    ("stand", ("stand",)),
    ("mentoring", ("mentor",)),
    ("competition", ("torneo", "yincana", "gymkana", "final ", "ctf")),
    ("workshop", ("taller", "seminario")),
    ("social", ("photocall", "pizza", "desayuno", "barrilada", "comida", "almuerzo")),
    ("talk", ("charla", "conferencia", "ponencia")),
]
CAT_KIND = {"ceremonia": "ceremony", "stand": "stand", "torneos": "competition", "torneo": "competition",
            "talleres": "workshop", "taller": "workshop", "yincana": "competition", "comidas": "social",
            "ponente": "talk"}

# ---------------------------------------------------------------------------


def slug_of(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def norm_title(t: str) -> str:
    t = html.unescape(t or "").replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+[–—-]\s+", " – ", t)  # unify the spaced dash of 'Charla X – Name' 
    for bad, good in TITLE_FIXES.items():
        t = t.replace(bad, good)
    return t


def kind_for(title: str, cats: list[str]) -> str:
    t = f" {title.lower()} "
    for kind, needles in KIND_ORDER:
        if any(n in t for n in needles):
            return kind
    for c in cats:
        k = CAT_KIND.get(c.lower())
        if k:
            return k
    return "other"


def hhmm_12(txt: str) -> str | None:
    """'5:40 pm' -> '17:40'."""
    m = re.match(r"\s*(\d{1,2})[:.](\d{2})\s*([ap])\.?m", txt.strip().lower())
    if not m:
        return None
    h, mm, ap = int(m.group(1)), m.group(2), m.group(3)
    if ap == "p" and h != 12:
        h += 12
    if ap == "a" and h == 12:
        h = 0
    return f"{h:02d}:{mm}"


def person_from_title(title: str, plugin: str) -> tuple[str | None, str | None]:
    """(speaker, company) derived from the title convention of each plugin:
    TEC 'Charla X – Name', ETN 'Topic: Name' or bare 'Name' (Ponente)."""
    name = None
    if plugin == "tec":
        if " – " in title and title.lower().startswith("charla"):
            name = title.split(" – ", 1)[1].strip()
    else:
        name = title.split(":", 1)[1].strip() if ":" in title else title.strip()
    if not name:
        return None, None
    name = NAME_ALIASES.get(name, name)
    if name in NOT_A_PERSON:
        return None, COMPANY_TALKS.get(name)
    company = None
    if plugin == "etn" and ":" in title:
        prefix = title.split(":", 1)[0].strip()
        if prefix in COMPANY_TALKS:
            company = COMPANY_TALKS[prefix]
    return name, company


def split_people(name: str) -> list[str]:
    if name in SPEAKER_INFO:  # keep 'Andrés y Adolfo' together (first names only)
        return [name]
    parts = [p.strip() for p in re.split(r"\s+y\s+|,\s*", name) if p.strip()]
    return [NAME_ALIASES.get(p, p) for p in parts]


def content_of(row):
    s = soup_of(row)
    return s, (s.find(id="content") or s.body)


def image_url(img) -> str:
    if img is None:
        return ""
    real = best_srcset_url(img.get("data-srcset") or img.get("srcset")) or img.get("data-src") or img.get("src") or ""
    if real.startswith("data:"):
        real = ""
    return norm_url(real)


def strip_size(url: str) -> str:
    """'.../foo-819x1024.png' -> '.../foo.png' (the original upload)."""
    return re.sub(r"-\d{2,4}x\d{2,4}(\.[a-z]{3,4})$", r"\1", url)


def cleaned(node) -> str:
    if node is None:
        return ""
    fix_lazy_images(node)
    return clean_html(node)


def imgs_in(node) -> list[str]:
    if node is None:
        return []
    fix_lazy_images(node)
    out = []
    for img in node.find_all("img"):
        u = image_url(img)
        if u and u not in out:
            out.append(u)
    return out


def summary_of(html_: str, limit=280) -> str | None:
    from bs4 import BeautifulSoup
    if not html_:
        return None
    t = BeautifulSoup(html_, "lxml").get_text(" ", strip=True)
    t = re.sub(r"\s+", " ", t)
    if len(t) > limit:
        cut = t[:limit].rsplit(" ", 1)[0]
        t = cut + "…"
    return t or None


# --- The Events Calendar (/event/) -----------------------------------------


def parse_tec(row) -> dict:
    s, c = content_of(row)
    title = norm_title(text_of(c.select_one(".tribe-events-single-event-title")))
    starts = ends = None
    for a in c.select("a[href*='google.com/calendar']"):
        q = parse_qs(urlparse(a["href"]).query)
        d = q.get("dates", [""])[0]
        m = re.match(r"(\d{8}T\d{6})/(\d{8}T\d{6})", d)
        if m:
            starts = datetime.strptime(m.group(1), "%Y%m%dT%H%M%S").isoformat(timespec="minutes")
            ends = datetime.strptime(m.group(2), "%Y%m%dT%H%M%S").isoformat(timespec="minutes")
            break
    if not starts:  # fallback: abbr title + time text
        sd = c.select_one(".tribe-events-start-date, .tribe-events-start-datetime")
        st = text_of(c.select_one(".tribe-events-start-time"))
        if sd is not None and sd.get("title"):
            times = re.findall(r"(\d{1,2}):(\d{2})", st + " " + text_of(sd))
            starts = sd["title"] + (f"T{int(times[0][0]):02d}:{times[0][1]}" if times else "T00:00")
            if len(times) > 1:
                ends = sd["title"] + f"T{int(times[1][0]):02d}:{times[1][1]}"
    cats = [text_of(a) for a in c.select(".tribe-events-event-categories a")]
    tags = [text_of(a) for a in c.select(".tribe-event-tags a")]
    venue = text_of(c.select_one(".tribe-venue"))
    desc_node = c.select_one(".tribe-events-single-event-description")
    body_imgs = imgs_in(desc_node)
    desc = cleaned(desc_node)
    poster = image_url(c.select_one(".tribe-events-event-image img"))
    if not poster and body_imgs:
        poster = body_imgs[0]
    speaker, company = person_from_title(title, "tec")
    online = "online" in (text_of(desc_node) or "").lower() and "jugará" in (text_of(desc_node) or "").lower()
    return {
        "plugin": "tec", "slug": slug_of(row["url"]), "title": title,
        "starts_at": starts, "ends_at": ends, "cats": cats, "tags": tags,
        "venue": venue, "room": None, "description_html": desc, "poster": poster,
        "body_imgs": body_imgs, "featured": poster, "speaker": speaker, "company": company,
        "modality": "online" if online else "in_person",
        "source_url": row["url"], "source_timestamp": row["timestamp"],
    }


# --- Eventin (/eventos/) ----------------------------------------------------


def parse_etn(row) -> dict:
    s, c = content_of(row)
    title = norm_title(text_of(c.select_one(".etn-event-entry-title")))
    cats = [text_of(a) for a in c.select(".etn-event-category a")]
    date = start = end = None
    venue = None
    for li in c.select(".etn-event-meta-info li"):
        label = text_of(li.find("span"))
        val = text_of(li).replace(label, "", 1).strip()
        val = re.sub(r"\(Europe/Madrid\)", "", val).strip()
        if label.lower().startswith("date"):
            m = re.match(r"(\d{2})/(\d{2})/(\d{4})", val)
            if m:
                date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        elif label.lower().startswith("time"):
            parts = [p.strip() for p in val.split(" - ")]
            start = hhmm_12(parts[0]) if parts else None
            end = hhmm_12(parts[1]) if len(parts) > 1 else None
        elif label.lower().startswith("venue"):
            venue = val
    starts = f"{date}T{start}" if date and start else (f"{date}T00:00" if date else None)
    ends = f"{date}T{end}" if date and end and end != start else None
    desc_node = c.select_one(".etn-event-content-body")
    body_imgs = imgs_in(desc_node)
    desc = cleaned(desc_node)
    featured = image_url(c.select_one(".etn-single-event-media img"))
    speaker, company = person_from_title(title, "etn") if "ponente" in [x.lower() for x in cats] else (None, None)
    online = (venue or "").strip().lower() == "online"
    room = None
    if venue and not online:
        room = venue.strip()
    return {
        "plugin": "etn", "slug": slug_of(row["url"]), "title": title,
        "starts_at": starts, "ends_at": ends, "cats": cats, "tags": [],
        "venue": venue, "room": room, "description_html": desc, "poster": None,
        "body_imgs": body_imgs, "featured": featured, "speaker": speaker, "company": company,
        "modality": "online" if online else "in_person",
        "source_url": row["url"], "source_timestamp": row["timestamp"],
    }


def parse_etn_listing(row) -> list[dict]:
    """Stubs for the /eventos/ pages linked from an etn_category archive."""
    s, c = content_of(row)
    cat = text_of(c.select_one("h1.page-title")) or slug_of(row["url"]).title()
    out = []
    for art in c.select("article.etn"):
        a = art.select_one(".entry-title a")
        if a is None or not ETN_RE.match(norm_url(a.get("href", ""))):
            continue
        url = norm_url(a["href"])
        title = norm_title(text_of(a))
        ex_node = art.select_one(".ast-excerpt-container")
        excerpt = cleaned(ex_node)
        truncated = "[…]" in (text_of(ex_node) or "") or (text_of(ex_node) or "").endswith("de")
        featured = image_url(art.select_one("img"))
        speaker, company = person_from_title(title, "etn") if cat.lower() == "ponente" else (None, None)
        out.append({
            "plugin": "etn-listing", "slug": slug_of(url), "title": title,
            "starts_at": None, "ends_at": None, "cats": [cat], "tags": [],
            "venue": None, "room": None,
            "description_html": "" if truncated else excerpt,
            "excerpt": summary_of(excerpt), "poster": None, "body_imgs": [], "featured": featured,
            "speaker": speaker, "company": company, "modality": "in_person",
            "source_url": url, "listing_url": row["url"], "source_timestamp": row["timestamp"],
        })
    return out


# --- merge + output ---------------------------------------------------------


def looks_like_poster(url: str) -> bool:
    n = url.lower().rsplit("/", 1)[-1]
    return any(k in n for k in ("cartel", "poster", "charla-", "torneos-", "gymkana", "captura", "-02-", "page-0001", "seguridad-ofensiva"))


def build_event(tec: dict | None, etn: dict | None) -> dict:
    """One product event out of the TEC record, the ETN record, or both."""
    base = tec or etn
    other = etn if tec else None
    # title: TEC (dated schedule) unless the ETN title carries a topic prefix
    title = base["title"]
    if tec and etn and ":" in etn["title"] and etn["plugin"] != "etn-listing":
        title = etn["title"]
    if tec and etn and etn["plugin"] == "etn-listing" and ":" in etn["title"] and not tec["speaker"]:
        title = etn["title"]
    cats = list(dict.fromkeys((tec["cats"] if tec else []) + (etn["cats"] if etn else [])))
    kind = kind_for(title, cats)
    # times/room: ETN is the later, room-level source; TEC when ETN is a stub
    starts = (etn or {}).get("starts_at") or base["starts_at"]
    ends = (etn or {}).get("ends_at") or base["ends_at"]
    if etn and etn["starts_at"] and tec and tec["starts_at"] and etn["starts_at"][:10] != tec["starts_at"][:10]:
        starts, ends = tec["starts_at"], tec["ends_at"]  # never trust a date mismatch, keep the schedule
    room = (etn or {}).get("room") or base.get("room")
    modality = "online" if (base["modality"] == "online" or (other and other["modality"] == "online")) else "in_person"
    # description: ETN first, TEC appended when it adds text
    from bs4 import BeautifulSoup
    parts = []
    for rec in ([etn, tec] if etn else [tec]):
        if rec and rec["description_html"]:
            txt = BeautifulSoup(rec["description_html"], "lxml").get_text(" ", strip=True)
            if not any(txt in BeautifulSoup(p, "lxml").get_text(" ", strip=True) for p in parts):
                parts.append(rec["description_html"])
    description = "\n".join(parts)
    summary = summary_of(description) or (etn or {}).get("excerpt")
    # poster: TEC featured (they are the posters) else an ETN body poster
    poster = None
    if tec and tec["poster"]:
        poster = tec["poster"]
    if not poster and etn:
        for u in etn["body_imgs"]:
            if looks_like_poster(u):
                poster = u
                break
        if not poster and etn["featured"] and (looks_like_poster(etn["featured"]) or kind not in ("talk",)):
            poster = etn["featured"]
    if not poster and tec and tec["body_imgs"]:
        poster = tec["body_imgs"][0]
    speaker = (etn or {}).get("speaker") or base.get("speaker")
    company = (etn or {}).get("company") or base.get("company") or (tec or {}).get("company")
    if speaker:
        canon = NAME_ALIASES.get(speaker, speaker)
        if canon in SPEAKER_INFO and SPEAKER_INFO[canon][0] and not company:
            company = SPEAKER_INFO[canon][0]
        elif not company:
            for p in split_people(canon):
                if p in SPEAKER_INFO and SPEAKER_INFO[p][0]:
                    company = SPEAKER_INFO[p][0]
                    break
        speaker = " y ".join(split_people(canon))
    # registration / info link (Google Form of the tournaments, external site of a talk)
    link = None
    for rec in (etn, tec):
        if not rec:
            continue
        for u in re.findall(r'href="(https?://[^"]+)"', rec["description_html"] or ""):
            if "innosoftdays" in u:
                continue
            if "docs.google.com/forms" in u or "eventbrite" in u or "forms.gle" in u:
                link = u
                break
        if link:
            break
    # description that is only the poster we already expose as poster_url
    if description and poster:
        rest = BeautifulSoup(description, "lxml")
        if not rest.get_text(" ", strip=True) and all(norm_url(i.get("src", "")) == poster for i in rest.find_all("img")):
            description = ""
            summary = None
    if description:
        description = description.replace("<p>Write with AI ", "<p>")
        summary = summary_of(description) if summary else summary
    if "se jugará online" in (summary or "").lower() or "se jugará online" in BeautifulSoup(description, "lxml").get_text(" ", strip=True).lower():
        modality = "online"
    year = int(starts[:4]) if starts else CONTEXT_YEAR
    return {
        "edition_year": year,
        "title": title,
        "kind": kind,
        "starts_at": starts,
        "ends_at": ends,
        "room": room,
        "modality": modality,
        "speaker": speaker,
        "company": company,
        "summary": summary,
        "description_html": description,
        "poster_url": poster,
        "link": link,
        "lang": "es",
        "source_url": base["source_url"],
        "source_timestamp": base["source_timestamp"],
        "_tec": tec, "_etn": etn, "_cats": cats,
    }


def main() -> None:
    rows = manifest_rows()
    tec_rows = [r for r in rows if TEC_RE.match(r["url"])]
    etn_rows = [r for r in rows if ETN_RE.match(r["url"])]
    cat_rows = [r for r in rows if ETN_CAT_RE.match(r["url"])]
    empty_rows = [r for r in rows if EMPTY_CAT_RE.match(r["url"])]
    in_scope = tec_rows + etn_rows + cat_rows + empty_rows

    tec = {slug_of(u): parse_tec(r) for u, r in latest_per_url(tec_rows).items()}
    etn = {slug_of(u): parse_etn(r) for u, r in latest_per_url(etn_rows).items()}
    listing_stubs: dict[str, dict] = {}
    listing_seen: dict[str, list[str]] = defaultdict(list)
    for u, r in latest_per_url(cat_rows).items():
        for stub in parse_etn_listing(r):
            listing_seen[stub["slug"]].append(u)
            if stub["slug"] not in etn and stub["slug"] not in listing_stubs:
                listing_stubs[stub["slug"]] = stub
    # ETN featured photos from listings for pages we do have (listing has the same image)
    etn_all = dict(etn)
    etn_all.update(listing_stubs)

    events, used_etn = [], set()
    for tslug, t in sorted(tec.items(), key=lambda kv: (kv[1]["starts_at"] or "", kv[0])):
        eslug = next((e for e, ts in MERGE.items() if ts == tslug and e in etn_all), None)
        e = etn_all.get(eslug) if eslug else None
        if e:
            used_etn.add(eslug)
        events.append(build_event(t, e))
    for eslug, e in sorted(etn_all.items(), key=lambda kv: (kv[1]["starts_at"] or "9", kv[0])):
        if eslug in used_etn:
            continue
        if eslug in MERGE and MERGE[eslug] not in tec:
            pass  # TEC counterpart not captured, keep the ETN record on its own
        events.append(build_event(None, e))
    events.sort(key=lambda ev: (ev["starts_at"] or "9999", ev["title"]))

    # --- speakers ---------------------------------------------------------
    speakers: dict[str, dict] = {}
    for ev in events:
        if not ev["speaker"] or ev["kind"] != "talk":
            continue
        e, t = ev["_etn"], ev["_tec"]
        photo = (e or {}).get("featured") or None
        if photo and looks_like_poster(photo):
            photo = None
        from bs4 import BeautifulSoup as _BS
        bio = ""
        for cand in ((e or {}).get("description_html"), (t or {}).get("description_html")):
            if cand and _BS(cand, "lxml").get_text(" ", strip=True):
                bio = cand
                break
        if not bio and e and e.get("excerpt"):
            bio = f"<p>{html.escape(e['excerpt'])}</p>"
        if bio:  # a bio is text, drop the poster figures
            _b = _BS(bio, "lxml")
            for fig in _b.find_all(["figure", "img"]):
                fig.decompose()
            bio = clean_html(_b)
        links = []
        if e:
            for u in re.findall(r'href="(https?://[^"]+)"', e["description_html"] or ""):
                if "innosoftdays" not in u and "google.com/forms" not in u:
                    links.append({"label": urlparse(u).netloc, "url": u})
        for name in split_people(ev["speaker"]):
            aff, pos = SPEAKER_INFO.get(name, (None, None))
            sp = speakers.setdefault(name, {
                "name": name, "affiliation": aff, "position": pos, "bio_html": bio,
                "photo_url": photo, "links": links, "edition_years": [ev["edition_year"]],
                "source_url": (e or t)["source_url"],
            })
            if not sp["bio_html"] and bio:
                sp["bio_html"] = bio
            if not sp["photo_url"] and photo:
                sp["photo_url"] = photo
            if ev["edition_year"] not in sp["edition_years"]:
                sp["edition_years"].append(ev["edition_year"])

    # --- media ------------------------------------------------------------
    media: dict[str, dict] = {}

    def add_media(url, kind, caption, used_by):
        if not url:
            return
        m = media.setdefault(url, {"url": url, "kind": kind, "edition_year": CONTEXT_YEAR, "caption": caption, "used_by": []})
        if used_by not in m["used_by"]:
            m["used_by"].append(used_by)

    for ev in events:
        srcs = [r["source_url"] for r in (ev["_tec"], ev["_etn"]) if r]
        for src in srcs:
            add_media(ev["poster_url"], "poster", ev["title"], src)
        for rec in (ev["_tec"], ev["_etn"]):
            if not rec:
                continue
            for u in rec["body_imgs"]:
                add_media(u, "poster", ev["title"], rec["source_url"])  # inline images of both plugins are the posters
            f = rec.get("featured")
            if f:
                n = f.lower().rsplit("/", 1)[-1]
                if "logo" in n:
                    k = "logo"
                elif rec["plugin"] == "tec" or looks_like_poster(f):
                    k = "poster"
                elif rec["plugin"].startswith("etn") and ev["kind"] == "talk" and ev["speaker"]:
                    k = "photo"
                else:
                    k = "other"
                add_media(f, k, ev["title"], rec["source_url"])
    for sp in speakers.values():
        if sp["photo_url"] and sp["photo_url"] in media:
            media[sp["photo_url"]]["kind"] = "photo"
            media[sp["photo_url"]]["caption"] = sp["name"]

    # --- edition ----------------------------------------------------------
    main_days = [ev["starts_at"][:10] for ev in events if ev["starts_at"] and ev["starts_at"][:7] == "2024-11" and int(ev["starts_at"][8:10]) <= 10]
    edition = {
        "year": CONTEXT_YEAR,
        "number": edition_number_for_year(CONTEXT_YEAR),
        "roman": roman(edition_number_for_year(CONTEXT_YEAR)),
        "name": f"InnoSoft Days {roman(edition_number_for_year(CONTEXT_YEAR))}",
        "starts_on": min(main_days),
        "ends_on": max(main_days),
        "venue": "Escuela Técnica Superior de Ingeniería Informática, Universidad de Sevilla (Av. de la Reina Mercedes, s/n, 41012 Sevilla)",
        "summary": "XII edición, del 5 al 8 de noviembre de 2024 en la ETSII, con el lema \"Compilemos un futuro sostenible\". Charlas, talleres, torneos de videojuegos, yincana, stands de igualdad, sostenibilidad y finanzas, mentoría y seminarios posteriores (SPL, Pipeline, Futuro) en noviembre y diciembre.",
        "description_html": "",
        "registration_url": None,
        "sources": sorted({ev["source_url"] for ev in events} | {r["url"] for r in cat_rows}),
        "confidence": "high",
        "notes": "Dates from the event pages of the two 2024 plugins (The Events Calendar /event/ and Eventin /eventos/); the seminars extend to 2024-12-13.",
    }

    # --- write ------------------------------------------------------------
    clean_events = [{k: v for k, v in ev.items() if not k.startswith("_")} for ev in events]
    dump_part(f"{FAMILY}.events.json", clean_events)
    dump_part(f"{FAMILY}.speakers.json", sorted(speakers.values(), key=lambda s: s["name"]))
    dump_part(f"{FAMILY}.media.json", sorted(media.values(), key=lambda m: m["url"]))
    dump_part(f"{FAMILY}.editions.json", [edition])
    write_notes(in_scope, tec_rows, etn_rows, cat_rows, empty_rows, tec, etn, listing_stubs, events, speakers, media, used_etn, listing_seen)


def write_notes(in_scope, tec_rows, etn_rows, cat_rows, empty_rows, tec, etn, stubs, events, speakers, media, used_etn, listing_seen) -> None:
    L = []
    L.append(f"# {FAMILY}\n")
    L.append("Two 2024 event plugins on innosoftdays.com (Astra theme), both describing InnoSoft Days XII (5-8 Nov 2024) plus the follow-up seminars (Nov/Dec 2024).\n")
    L.append("- `/event/<slug>/` = The Events Calendar (tribe): dated schedule, categories, posters as featured image, venue = ETSII. Body class `single-tribe_events`.")
    L.append("- `/eventos/<slug>/` = Eventin (etn_*): rooms, 12h times, speaker photo as featured image, longer descriptions, posters inside the body. Body class `single-etn`.")
    L.append("- `/etn_category/<slug>/` = Eventin archive listings (ponente, taller, torneo): title, excerpt, image, link. Used as stubs for the `/eventos/` pages that were never fetched.")
    L.append("- `/etn_category-N/` and `/mec-category/<year>/` = empty archives (\"Etn Category\" / \"¡No hay eventos!\").\n")
    L.append("## Coverage\n")
    L.append(f"- Captures in scope: {len(in_scope)} = {len(tec_rows)} /event/ ({len(tec)} URLs) + {len(etn_rows)} /eventos/ ({len(etn)} URLs) + {len(cat_rows)} /etn_category/ listings ({len(latest_per_url(cat_rows))} URLs) + {len(empty_rows)} empty category archives.")
    L.append(f"- Events written: {len(events)} (all edition_year 2024). Speakers: {len(speakers)}. Media: {len(media)}. Editions: 1 (2024, XII).")
    L.append(f"- Listing-only stubs (no single page captured, undated unless merged): {len(stubs)}: " + ", ".join(sorted(stubs)) + ".")
    L.append("- Every URL with several captures (2024 vs 2025 versions) describes the same 2024 event; the latest capture is used, so no event is duplicated across versions.\n")
    L.append("## Merge of the two plugins\n")
    L.append("Both plugins published the same activities. ETN records were merged into their TEC counterpart with an explicit slug map (matched by person, date and start time). Merged event: title = TEC (typos fixed: Cibersegurirdad, Iguldad) unless the ETN title has a topic prefix; date/time/room from ETN (later, room-level) unless the ETN date differs from TEC; description = ETN plus TEC when it adds text; poster = TEC featured image, else the ETN body poster; source_url = TEC page. Secondary (ETN) URL per merged event:\n")
    L.append("| event | TEC source_url | ETN url merged in |")
    L.append("|---|---|---|")
    for ev in events:
        if ev["_tec"] and ev["_etn"]:
            L.append(f"| {ev['title']} | {ev['_tec']['source_url']} | {ev['_etn']['source_url']}{' (listing stub)' if ev['_etn']['plugin']=='etn-listing' else ''} |")
    L.append("")
    conflicts = []
    for ev in events:
        t, e = ev["_tec"], ev["_etn"]
        if t and e and t["starts_at"] and e["starts_at"] and (t["starts_at"] != e["starts_at"] or t["ends_at"] != e["ends_at"]):
            conflicts.append(f"- {ev['title']}: TEC {t['starts_at']}..{t['ends_at']} vs ETN {e['starts_at']}..{e['ends_at']} -> kept {ev['starts_at']}..{ev['ends_at']}")
    if conflicts:
        L.append("Time conflicts between the plugins (ETN kept when same day, it was edited later and carries the room):\n")
        L.extend(conflicts)
        L.append("")
    L.append("Not merged on purpose (different granularity, both kept): TEC multi-day umbrellas `Stand Sostenibilidad` / `Stand Igualdad` (5-8 Nov) vs ETN per-day `Stand de Sostenibilidad|Igualdad|Finanzas DD/11`; TEC `Mentoría` (6-8 Nov) vs ETN `Mentoría Turno Mañana/Tarde` slots. `Torneo CS2 (Final)` (ETN listing) has no TEC page.\n")
    L.append("## Per year\n")
    cnt = Counter(ev["edition_year"] for ev in events)
    for y, n in sorted(cnt.items()):
        L.append(f"- {y}: {n} events, kinds " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(ev['kind'] for ev in events if ev['edition_year']==y).items())))
    L.append("")
    L.append("## Skipped captures\n")
    L.append("Older captures of a URL that has a newer one (same 2024 event, the 2025 version only adds \"Este evento ha pasado\" and the year in the date):\n")
    for group in (tec_rows, etn_rows, cat_rows):
        latest = latest_per_url(group)
        for r in sorted(group, key=lambda r: (r["url"], r["timestamp"])):
            if latest[r["url"]]["timestamp"] != r["timestamp"]:
                L.append(f"- {r['timestamp']} {r['url']} (superseded by {latest[r['url']]['timestamp']})")
    L.append("\nEmpty archive pages (no events listed):\n")
    for r in sorted(empty_rows, key=lambda r: (r["url"], r["timestamp"])):
        L.append(f"- {r['timestamp']} {r['url']}")
    L.append("\n## Oddities\n")
    L.append("- The site advertised /event/ pages with tribe markup although the survey signature also says eventon; the etn_* classes belong to Eventin, not EventON.")
    L.append("- ETN listing pages `ponente` and `taller` have a page 2 that was not captured, so a few 2024 talks/workshops may be missing entirely.")
    L.append("- ETN `Pizza` events have end time equal to start time (kept as ends_at null). `Torneo CS2/LOL (Cuartos y semis)` are held online (modality online).")
    L.append("- TEC `Ignasi Labastida i Juan` at 16:00 vs ETN 11:00 the same day (kept ETN). TEC titles carry typos fixed in the output (`Cibersegurirdad`, `Iguldad`).")
    L.append("- The `/etn_category/ponente/` listing is tagged kind=speaker in the manifest and may also be used by the speakers family; speakers here come from the event pages and that listing (photo, bio excerpt).")
    L.append("- The same 2024 activities also exist under `/events/<slug>/` (third plugin, out of scope, same slugs as `/event/`), so the report phase should dedupe 2024 by TEC slug.")
    L.append("- The `Yincana Coles` events (7 and 8 Nov, aula F0.31) are the schools gymkhana; classified as competition.")
    L.append("- ETN listing stubs also appear in the listings we did fetch as: " + ", ".join(f"{s} ({len(v)})" for s, v in sorted(listing_seen.items()) if s in stubs) + ".")
    (EXTRACTED / "parts" / f"{FAMILY}.notes.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
