"""Family posts_2018_2020: blog posts (kind=post, WordPress astra theme) whose
URL date is 2018, 2019 or 2020. They are the only trace of editions VI (2018),
VII (2019) and VIII (2020).

Outputs (data/extracted/parts/posts_2018_2020.*):
  posts.json     every post (latest capture of each URL; the older captures are
                 byte-different but text-identical, listed as skipped)
  events.json    every talk / workshop / activity announced or summarised in
                 the posts (programme facts are anchored to the paragraph that
                 states them; the paragraph text becomes the summary)
  editions.json  2018, 2019, 2020 with what the posts state
  media.json     images hosted by the site that the posts embed
  notes.md       coverage, skips, oddities, per-year counts

Deterministic, no network. Run: .venv/bin/python parse/posts_2018_2020.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import (  # noqa: E402
    EXTRACTED, clean_html, dump, edition_number_for_year, fix_lazy_images,
    latest_per_url, manifest_rows, norm_media_url, norm_url, parse_spanish_date,
    roman, soup_of, text_of,
)

FAMILY = "posts_2018_2020"
YEARS = (2018, 2019, 2020)
URL_RE = re.compile(r"^https://www\.innosoftdays\.com/(2018|2019|2020)/(\d\d)/(\d\d)/([^/]+)/?$")
TWITCH = "https://www.twitch.tv/innosoftdays"

CATEGORY_NAMES = {"noticias": "Noticias", "cronica": "Crónica"}


# --------------------------------------------------------------------------
# Programme facts. Each rule is anchored to the source paragraph through
# `anchor` (a substring of the paragraph's text); the parser asserts that the
# anchor, the title and every speaker are literally in that paragraph, so a
# rule can never describe something the captured page does not say.
# --------------------------------------------------------------------------
EVENT_RULES: dict[str, list[dict]] = {
    # ---- 2018 (VI) ---------------------------------------------------------
    "bienvenidos-innosoft-days": [
        dict(title="Escape Room", kind="social", anchor="Escape Room", sentence=True,
             note="announced in the welcome post, no date given"),
        dict(title="Gymkhana", kind="social", anchor="Gymkhana", sentence=True,
             note="announced in the welcome post, no date given"),
        dict(title="Proyección del capítulo “Toda tu historia” de Black Mirror", kind="social",
             anchor="Toda tu historia", check_title=False, sentence=True,
             note="announced in the welcome post, no date given"),
    ],
    "competicion-ideas-open-source-modelos-negocio-bitnami": [
        dict(title="Competición de ideas open source y modelos de negocio de Bitnami", kind="competition",
             anchor="competición patrocinada por Bitnami", check_title=False,
             company="Bitnami", date="2018-11-13", time="18:30", end_time="19:30", room="Aula A2.16",
             link="https://institucional.us.es/innosoft/torneo-ideas-negocio-bitnami/",
             speaker="Jurado: Daniel Liszka, Pablo Trinidad, Jesús González",
             description_from="content"),
    ],
    "material-necesario-taller-clasificacion-imagenes-deteccion-objetos-yolo": [
        dict(title="Taller “Clasificación de imágenes y detección de objetos con YOLO”", kind="workshop",
             anchor="Los asistentes deberán tener preparado", check_title=False,
             speaker="Jesús Utrera, Joaquín Salguero",
             link="https://www.eventbrite.es/e/entradas-innosoft-days-jesus-utrera-y-joaquin-salguero-52197348675",
             description_from="content",
             note="speakers taken from the Eventbrite slug and the GitHub repo jutrera/InnoSoft-2018 linked in the post; date not stated"),
    ],
    "material-necesario-testing-aplicaciones-kubernetes": [
        dict(title="Testing de aplicaciones en Kubernetes", kind="workshop",
             anchor="Los asistentes deberán tener instalado", check_title=False,
             speaker="Javier Aguadero, Carlos Rodríguez, Juan Ariza",
             link="https://www.eventbrite.es/e/entradas-innosoft-days-javier-aguadero-carlos-rodriguez-y-juan-ariza-52102979414",
             description_from="content",
             note="speakers taken from the Eventbrite slug linked in the post; date not stated"),
    ],
    "equipos-del-concurso-programacion-tournametsii": [
        dict(title="Concurso de programación TOURNAMETSII", kind="competition",
             anchor="TOURNAMETSII", check_title=False, description_from="content",
             note="date not stated"),
    ],
    # ---- 2020 (VIII), online ------------------------------------------------
    "ponencias-definitivas-24112020": [
        dict(title="Inauguración de InnoSoft Days 2020", kind="ceremony",
             anchor="inauguración de InnoSoft Days 2020", check_title=False, date="2020-11-24"),
        dict(title="Experiencia inteligente en Everis", kind="talk", anchor="experiencia inteligente en Everis",
             speaker="Jorge Avendaño, Sergio Martín", company="Everis", date="2020-11-24"),
        dict(title="Universidad Empresarial: El binomio perfecto", kind="talk",
             anchor="Universidad Empresarial", speaker="María José Escalona", date="2020-11-24"),
        dict(title="Introducción a la clasificación de imágenes utilizando redes convolucionales", kind="talk",
             anchor="redes convolucionales", speaker="Antonio Jesús García Nieto", date="2020-11-24", time="15:30"),
        dict(title="Taller de Hackatón", kind="competition", anchor="taller de Hackatón", date="2020-11-24", time="15:30",
             link="https://institucional.us.es/innosoft/inscripciones/",
             note="runs during the convolutional-networks talk according to the post"),
        dict(title="Desarrollo Impulsado por la Ingeniería del Caos", kind="talk", anchor="Ingeniería del Caos",
             speaker="Nicolás Afonso, Alicia Melgarejo", date="2020-11-24"),
    ],
    "ponencias-definitivas-26112020": [
        dict(title="Presentación del día", kind="ceremony", anchor="Comenzaremos el día con la presentación",
             check_title=False, date="2020-11-26"),
        dict(title="¿Quién es quién en una sociedad digital?", kind="talk", anchor="sociedad digital",
             speaker="Mª Iluminada Baturone, Mª Rosario Arjona", date="2020-11-26"),
        dict(title="Limiting Global Warning by Improving Data-Centre Software", kind="talk",
             anchor="Limiting Global Warning", speaker="Alejandro Fernández", date="2020-11-26"),
        dict(title="Aportaciones de Investigación y Transferencia en Ciencia de Datos", kind="talk",
             anchor="Ciencia de Datos", speaker="Pepe Riquelme, Manuel Carranza", date="2020-11-26", time="11:50"),
        dict(title="Procesos Inteligentes en la Industria 4.0", kind="talk", anchor="Industria 4.0",
             speaker="Mayte Gómez", date="2020-11-26"),
        dict(title="Introducción a la Computación Cuántica", kind="talk", anchor="Computación Cuántica",
             speaker="Rafael Corchuelo", date="2020-11-26", time="15:30"),
        dict(title="Como hacer los equipos data science 10 veces más rápido", kind="talk", anchor="DataRobot",
             speaker="Federico Castanedo", company="DataRobot", date="2020-11-26"),
        dict(title="Scape Room", kind="social", anchor="Scape Room", date="2020-11-26"),
    ],
    "ponencias-definitivas-27112020": [
        dict(title="Presentación del día", kind="ceremony", anchor="presentación del día", date="2020-11-27"),
        dict(title="Introducción a soluciones open-source de “Machine Learning”", kind="talk",
             anchor="soluciones open-source", speaker="Miguel Ángel Cabrera", date="2020-11-27"),
        dict(title="Introducción a Spring Cloud DataFlow", kind="talk", anchor="Spring Cloud DataFlow",
             speaker="Daniel Arteaga", date="2020-11-27"),
        dict(title="Oddo, ERP con alma de framework", kind="talk", anchor="ERP con alma de framework",
             speaker="Fernando La Chica, Francisco Javier Llamas", date="2020-11-27", time="11:40"),
        dict(title="Taller Aprendizaje automático con Swift", kind="workshop", anchor="Aprendizaje automático con Swift",
             check_title=False, speaker="GUMUS (Grupo de Usuarios de Macintosh de la Universidad de Sevilla)",
             company="GUMUS", date="2020-11-27", time="16:00"),
        dict(title="Trading algorítmico con criptomonedas", kind="talk", anchor="Trading algorítmico",
             speaker="Gonzalo Fernández, Antonio García", date="2020-11-27"),
        dict(title="Hacia una Inteligencia Artificial Regenerativa y Redistributiva", kind="talk",
             anchor="Verónica Dahl", check_title=False, speaker="Verónica Dahl", date="2020-11-27",
             note="the post spells it 'Regenarativa'"),
        dict(title="Acto de clausura de InnoSoft Days 2020", kind="ceremony", anchor="acto de clausura",
             check_title=False, date="2020-11-27"),
    ],
}

# Poster of the day announced by each programme post (first site image).
POSTER_KEYS = ("cartel", "martes", "jueves", "viernes")
LOGO_KEYS = ("logo",)


EMPTY_INLINE_RE = re.compile(r"<(i|b|em|strong|u|a)(?:\s[^>]*)?>\s*</\1>")


def tidy_html(html: str) -> str:
    """Post-clean: drop empty inline tags (icon fonts), demote h1 (a post body
    must not carry the page's h1), trim whitespace between block tags."""
    if not html:
        return html
    for _ in range(3):
        html = EMPTY_INLINE_RE.sub("", html)
    html = re.sub(r"<(/?)h1(\s|>)", r"<\1h2\2", html)
    html = re.sub(r"(?:\s|<br\s*/?>)+</p>", "</p>", html)
    html = re.sub(r"<p>\s*(?:<br\s*/?>|&nbsp;|\s)*</p>", "", html)
    html = re.sub(r">\s+<", "><", html)
    return html.strip()


def sentence_with(text: str, anchor: str) -> str:
    """The sentence of `text` that contains `anchor` (falls back to text)."""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if anchor in sent:
            return sent.strip()
    return text


def tidy_text(text: str) -> str:
    """Collapse whitespace and detach punctuation glued to link boundaries."""
    text = re.sub(r"\s+", " ", text or "").strip()
    return re.sub(r"\s+([.,;:!?»”])", r"\1", text)


def excerpt_from_text(text: str, limit: int = 300) -> str:
    text = tidy_text(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # sentence ends, ignoring list numbering like " 1." (but not "A2.16.")
    ends = [m.end() for m in re.finditer(r"(?<![\s(]\d)(?<![\s(]\d\d)[.!?](?=\s)", cut)]
    if ends and ends[-1] > limit // 3:
        return cut[: ends[-1]]
    return cut.rsplit(" ", 1)[0] + "…"


def slug_of(url: str) -> str:
    return URL_RE.match(url).group(4)


def in_scope(rows: list[dict]) -> list[dict]:
    return [r for r in rows if URL_RE.match(r["url"])]


def article_of(soup):
    art = soup.find("article")
    if art is None:
        raise ValueError("no <article>")
    return art


def entry_content(art):
    ec = art.find(class_="entry-content")
    if ec is None:
        raise ValueError("no .entry-content")
    # some captures never close the entry-content div: navigation, comment
    # forms and stray hero titles end up inside it
    for sel in (".comments-area", "nav", ".post-navigation", ".listing-hero-title",
                ".ast-single-post-navigation-wrapper", "#comments", ".sharedaddy"):
        for x in ec.select(sel):
            x.decompose()
    for p in ec.select("p.titulo-noticia"):
        p.name = "h3"
    fix_lazy_images(ec)
    return ec


def meta_content(soup, **attrs):
    tag = soup.find("meta", attrs=attrs)
    return (tag.get("content") or "").strip() if tag else ""


def post_date(art, soup, url) -> str:
    pub = art.find(class_="published")
    d = parse_spanish_date(text_of(pub)) if pub else None
    if not d:
        iso = meta_content(soup, property="article:published_time")
        d = parse_spanish_date(iso[:10]) if iso else None
    if not d:
        m = URL_RE.match(url)
        d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
    return d.isoformat()


def categories_of(art) -> list[str]:
    cats = []
    for c in art.get("class", []):
        if c.startswith("category-"):
            slug = c[len("category-"):]
            cats.append(CATEGORY_NAMES.get(slug, slug.replace("-", " ").title()))
    return cats


def tags_of(art) -> list[str]:
    return [c[len("tag-"):] for c in art.get("class", []) if c.startswith("tag-")]


def site_images(ec) -> list[str]:
    out = []
    for img in ec.find_all("img"):
        u = norm_media_url(img.get("src"))
        if u and "innosoftdays.com/wp-content/" in u and u not in out:
            out.append(u)
    return out


def is_person_photo(img) -> bool:
    """Image inside a speaker/jury card (div.speaker in the 2018 posts)."""
    return img.find_parent(class_="speaker") is not None


def excerpt_of(soup, ec) -> str:
    """First sentences of the body (the page's og:description is cut mid-word)."""
    return excerpt_from_text(text_of(ec))


def poster_of(images: list[str]) -> str | None:
    for u in images:
        name = u.rsplit("/", 1)[-1].lower()
        if any(k in name for k in POSTER_KEYS):
            return u
    return None


def media_kind(url: str, photo: bool = False) -> str:
    name = url.rsplit("/", 1)[-1].lower()
    if any(k in name for k in POSTER_KEYS):
        return "poster"
    if any(k in name for k in LOGO_KEYS):
        return "logo"
    if photo:
        return "photo"
    return "other"


def parse_post(row: dict) -> tuple[dict, list[dict], list[dict], list[str]]:
    """-> (post, events, media, tags)"""
    soup = soup_of(row)
    art = article_of(soup)
    ec = entry_content(art)
    url = row["url"]
    year = int(URL_RE.match(url).group(1))
    slug = slug_of(url)
    h1 = art.find(class_="entry-title") or soup.find("h1")
    title = re.sub(r"\s+", " ", text_of(h1)).strip()
    images = site_images(ec)
    first_img = ec.find("img")
    og_image = meta_content(soup, property="og:image")
    featured = norm_media_url(first_img.get("src")) if first_img is not None and first_img.get("src") else (norm_media_url(og_image) if og_image else None)
    content_html = tidy_html(clean_html(ec))
    if not content_html:
        raise ValueError(f"empty content for {url}")

    post = {
        "date": post_date(art, soup, url),
        "title": title,
        "slug": slug,
        "excerpt": excerpt_of(soup, ec),
        "content_html": content_html,
        "featured_image_url": featured,
        "lang": "es",
        "edition_year": year,
        "categories": categories_of(art),
        "source_url": url,
        "source_timestamp": row["timestamp"],
    }

    events = []
    paragraphs = [p for p in ec.find_all(["p", "li", "div"]) if text_of(p)]
    for rule in EVENT_RULES.get(slug, []):
        para = next((p for p in paragraphs if rule["anchor"] in text_of(p)), None)
        if para is None:
            raise ValueError(f"{slug}: anchor not found: {rule['anchor']!r}")
        ptext = tidy_text(text_of(para))
        norm = lambda s: re.sub(r"\s+", " ", s).lower()  # noqa: E731
        if rule.get("check_title", True) and norm(rule["title"]) not in norm(ptext):
            raise ValueError(f"{slug}: title not in paragraph: {rule['title']!r}")
        for name in re.split(r",\s*", rule.get("speaker") or ""):
            name = re.sub(r"\s*\(.*\)$", "", name).replace("Jurado: ", "")
            if name and rule.get("check_speakers", True) and "note" not in rule and norm(name) not in norm(text_of(ec)):
                raise ValueError(f"{slug}: speaker not in post: {name!r}")
        summary = sentence_with(ptext, rule["anchor"]) if rule.get("sentence") else ptext
        if rule.get("description_from") == "content":
            description_html = content_html
        else:
            description_html = tidy_html(clean_html(para))
        starts_at = rule.get("date")
        ends_at = None
        if starts_at and rule.get("time"):
            starts_at = f"{starts_at}T{rule['time']}:00"
            if rule.get("end_time"):
                ends_at = f"{rule['date']}T{rule['end_time']}:00"
        events.append({
            "edition_year": year,
            "title": rule["title"],
            "kind": rule["kind"],
            "starts_at": starts_at,
            "ends_at": ends_at,
            "room": rule.get("room"),
            "modality": "online" if year == 2020 else "in_person",
            "speaker": rule.get("speaker"),
            "company": rule.get("company"),
            "summary": summary,
            "description_html": description_html,
            "poster_url": poster_of(images),
            "link": rule.get("link") or (TWITCH if year == 2020 and rule["kind"] in ("talk", "ceremony", "workshop") else None),
            "lang": "es",
            "source_url": url,
            "source_timestamp": row["timestamp"],
        })

    media = []
    for u in images:
        caption = None
        img = next((i for i in ec.find_all("img") if norm_media_url(i.get("src")) == u), None)
        if img is not None:
            fig = img.find_parent("figure")
            cap = fig.find("figcaption") if fig else None
            caption = text_of(cap) or (img.get("alt") or None) or None
        media.append({
            "url": u,
            "kind": media_kind(u, img is not None and is_person_photo(img)),
            "edition_year": year,
            "caption": caption,
            "used_by": [url],
        })
    return post, events, media, tags_of(art)


def merge_media(items: list[dict]) -> list[dict]:
    by: dict[str, dict] = {}
    for m in items:
        cur = by.get(m["url"])
        if cur is None:
            by[m["url"]] = dict(m)
        else:
            for u in m["used_by"]:
                if u not in cur["used_by"]:
                    cur["used_by"].append(u)
            cur["caption"] = cur["caption"] or m["caption"]
    return list(by.values())


def build_editions(posts: list[dict], events: list[dict]) -> list[dict]:
    by_year = defaultdict(list)
    for p in posts:
        by_year[p["edition_year"]].append(p)
    out = []
    for year in YEARS:
        srcs = [p["source_url"] for p in sorted(by_year[year], key=lambda p: p["date"])]
        n = edition_number_for_year(year)
        ed = {
            "year": year, "number": n, "roman": roman(n), "name": f"InnoSoft Days {year}",
            "starts_on": None, "ends_on": None, "venue": None, "summary": None,
            "description_html": None, "registration_url": None, "sources": srcs,
            "confidence": "low", "notes": "",
        }
        if year == 2018:
            welcome = next(p for p in by_year[year] if p["slug"] == "bienvenidos-innosoft-days")
            ed.update(
                summary="Edición VI de las Jornadas EGC. Este año se celebra el 50º aniversario de la Ingeniería del Software: tecnologías punteras del sector y un recuerdo de nuestras raíces.",
                description_html=welcome["content_html"],
                venue="ETSII, Universidad de Sevilla",
                confidence="low",
                notes="Posts call it 'Jornadas EGC 2018' / 'Edición VI'. Theme stated in the welcome post (50 years of software engineering). "
                      "No start/end dates in the posts; the Bitnami competition on 2018-11-13 (aula A2.16, an ETSII classroom, hence the venue) "
                      "and posts dated up to 2018-11-11 place the event in mid November 2018. Poster 201819-Cartel-v7-1.png (media) carries the programme.",
            )
        elif year == 2019:
            web30 = next(p for p in by_year[year] if p["slug"] == "aniversario-la-web-30-anos")
            ed.update(
                summary="InnoSoft Days 2019 celebra los 30 años de la World Wide Web; el blog de la edición publica crónicas sobre la historia de la web, la Deep Web, la misión Apolo 11, las webs ecológicas y las mujeres en la informática.",
                description_html=web30["content_html"],
                confidence="low",
                notes="Only blog articles survive for 2019 (posts dated 2019-10-22 to 2019-11-01); they mention 'InnoSoft Days 2019' and the 30th anniversary of the Web "
                      "as something the edition celebrates. No dates, venue or programme in these posts.",
            )
        elif year == 2020:
            ok = next(p for p in by_year[year] if p["slug"] == "ok-google-inicia-innosoft-days-2020")
            ed.update(
                starts_on="2020-11-24", ends_on="2020-11-27",
                venue="Online (YouTube y Twitch, canal innosoftdays)",
                summary="Edición VIII, celebrada online por la crisis sanitaria los días 24, 26 y 27 de noviembre de 2020, centrada en construir servicios software para sistemas inteligentes.",
                description_html=ok["content_html"],
                registration_url="https://institucional.us.es/innosoft/inscripciones/",
                confidence="high",
                notes="Dates, online modality and theme ('Construir servicios software para sistemas inteligentes') stated in the 2020-11-06 post; "
                      "day programmes in the three 'Ponencias definitivas' posts (24, 26, 27 Nov). registration_url is the inscriptions page linked "
                      "for the hackathon. Talk times only when the post states them; the day posters (media) carry the full timetable.",
            )
        out.append(ed)
    return out


def main() -> None:
    rows = in_scope(manifest_rows("post"))
    by_url: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_url[r["url"]].append(r)
    latest = latest_per_url(rows)

    posts, events, media, skipped, tags_by_slug = [], [], [], [], {}
    for url in sorted(latest):
        row = latest[url]
        post, evs, med, tags = parse_post(row)
        posts.append(post)
        events.extend(evs)
        media.extend(med)
        tags_by_slug[post["slug"]] = tags
        # older captures of the same URL: keep only if their text differs
        latest_text = text_of(entry_content(article_of(soup_of(row))))
        for other in sorted(by_url[url], key=lambda r: r["timestamp"]):
            if other["timestamp"] == row["timestamp"]:
                continue
            other_text = text_of(entry_content(article_of(soup_of(other))))
            reason = ("older capture, entry-content text identical to the latest capture"
                      if other_text == latest_text else "older capture, text differs (NOT extracted, review)")
            skipped.append((other["url"], other["timestamp"], reason))

    posts.sort(key=lambda p: (p["date"], p["slug"]))
    editions = build_editions(posts, events)
    media = merge_media(media)

    parts = EXTRACTED / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    dump(f"parts/{FAMILY}.posts.json", posts)
    dump(f"parts/{FAMILY}.events.json", events)
    dump(f"parts/{FAMILY}.editions.json", editions)
    dump(f"parts/{FAMILY}.media.json", media)

    # ---- notes -----------------------------------------------------------
    per_year_posts = Counter(p["edition_year"] for p in posts)
    per_year_events = Counter(e["edition_year"] for e in events)
    per_year_media = Counter(m["edition_year"] for m in media)
    lines = [
        f"# {FAMILY}",
        "",
        "Blog posts of innosoftdays.com (WordPress, Astra theme) whose URL date is 2018, 2019 or 2020.",
        f"Captures in scope: {len(rows)} ({len(latest)} URLs). Extracted: {len(latest)} (latest capture of each URL). Skipped: {len(skipped)}.",
        "",
        "## Outputs",
        "",
        f"- posts.json: {len(posts)} posts (2018: {per_year_posts[2018]}, 2019: {per_year_posts[2019]}, 2020: {per_year_posts[2020]})",
        f"- events.json: {len(events)} events (2018: {per_year_events[2018]}, 2019: {per_year_events[2019]}, 2020: {per_year_events[2020]})",
        f"- editions.json: {len(editions)} editions (2018 low, 2019 low, 2020 high confidence)",
        f"- media.json: {len(media)} site-hosted images (2018: {per_year_media[2018]}, 2019: {per_year_media[2019]}, 2020: {per_year_media[2020]})",
        "",
        "## Extracted captures",
        "",
    ]
    for p in posts:
        lines.append(f"- {p['date']} {p['source_url']} @{p['source_timestamp']} | {p['title']} | cats={p['categories']} tags={tags_by_slug[p['slug']]}")
    lines += ["", "## Skipped captures", ""]
    for u, ts, reason in skipped:
        lines.append(f"- {u} @{ts}: {reason}")
    lines += [
        "",
        "## Events",
        "",
        "Programme facts (title, speakers, kind, day, time, room) come from a rule table in the parser anchored to the paragraph",
        "that states them; the parser asserts anchor, title and speaker names are literally in the captured text, and the",
        "paragraph becomes summary/description_html (whole post for the 2018 material/competition posts). Array order is",
        "programme order within each day. `starts_at` without a time part means the post gives the day but not the hour.",
        "",
        "- 2018 (VI): Bitnami ideas competition (2018-11-13 18:30-19:30, aula A2.16, jury Daniel Liszka / Pablo Trinidad / Jesús González with",
        "  bios and photos inside the post), YOLO workshop (Jesús Utrera, Joaquín Salguero: names from the Eventbrite slug and the linked repo",
        "  jutrera/InnoSoft-2018), Kubernetes testing workshop (Javier Aguadero, Carlos Rodríguez, Juan Ariza: names from the Eventbrite slug),",
        "  TOURNAMETSII programming contest, and the Escape Room / Gymkhana / Black Mirror screening announced in the welcome post. Dates of",
        "  the workshops/contest/social activities are not stated (starts_at null). The '1011' post only links to the speakers page",
        "  (institucional.us.es/innosoft/ponentes/), no names in the text, so no events from it.",
        "- 2019 (VII): the five posts are blog articles (web anniversary, Deep Web, Apollo 11, ecological webs, women in computing); no events.",
        "- 2020 (VIII): 6 + 8 + 8 items for 24, 26 and 27 November (talks, day presentations, inauguration/closing ceremonies, hackathon,",
        "  escape room, Swift workshop by GUMUS). Times only where the post states them (15:30 on the 24th; 11:50 and 15:30 on the 26th;",
        "  11:40 and 16:00 on the 27th). Modality online, link = Twitch channel where the talks were streamed. The 2020-11-09 post shows",
        "  the first poster only (no names in text): no events. Speaker bios live on institucional.us.es/innosoft/ponentes-viii-edicion/,",
        "  not captured in this family.",
        "",
        "## Editions",
        "",
        "- 2018: theme '50º aniversario de la Ingeniería del Software' (welcome post); called 'Jornadas EGC 2018 / Edición VI'; no dates in the",
        "  posts (competition on 2018-11-13); venue inferred from aula A2.16 (ETSII). Confidence low.",
        "- 2019: only 'InnoSoft Days 2019' + 30 years of the Web as something celebrated; no dates/venue. Confidence low.",
        "- 2020: 24, 26, 27 November 2020, online (YouTube + Twitch), theme 'Construir servicios software para sistemas inteligentes'. Confidence high.",
        "",
        "## Oddities",
        "",
        "- Images are lazy-loaded (src=data:svg, real URL in data-src/data-srcset) with a <noscript> duplicate; fix_lazy_images() (added to",
        "  common.py) picks the largest srcset candidate. data-src points at https://institucional.us.es/innosoft/wp-content/... (the pre-2021",
        "  host) while the srcset uses www.innosoftdays.com for the same path; norm_media_url() maps the old host to www.innosoftdays.com so",
        "  the importer can look the file up. None of these uploads (2018/11, 2019/10, 2020/11) is in the CDX index yet.",
        "- Several captures never close .entry-content: post navigation, the comment form and a stray '.listing-hero-title' h1 end up inside;",
        "  they are removed before cleaning.",
        "- Every URL with two captures (2024-11 and 2025-01/02) has byte-different but text-identical content; the latest is used.",
        "- No featured images (Astra 'ast-no-thumb'); featured_image_url is the first image of the body (full-size srcset candidate),",
        "  falling back to the page's og:image; for the 2019 articles that is an external picture (NASA, Wikimedia, treehugger).",
        "- Excerpts are the first sentences of the body (up to 300 chars); the pages' og:description is cut mid-word.",
        "- Categories come from the article classes (category-noticias, category-cronica); tags are listed above per post but not in the schema.",
        "- The 24/11/2020 post writes the year as '2o2o' (letter o); the 27/11/2020 poster file is named viernes_26-min.png.",
        "- The Bitnami jury bios/photos are not emitted as speakers (they are jury, and speakers.json maps to role 'Ponentes'); their photos",
        "  are in media.json as kind photo and the bios stay in the post/event HTML.",
        "- External images (Wikimedia, NASA, treehugger, ecofriend, blackmainstreet, townnews) are kept in content_html but not listed in media.json.",
    ]
    (parts / f"{FAMILY}.notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"posts={len(posts)} events={len(events)} editions={len(editions)} media={len(media)} skipped={len(skipped)}")


if __name__ == "__main__":
    main()
