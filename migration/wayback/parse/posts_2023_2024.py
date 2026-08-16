"""Family posts_2023_2024: blog posts (kind=post) whose URL date year is
2023 or 2024, i.e. editions XI (2023) and XII (2024) of InnoSoft Days.

All captures share the Astra single-post template (WordPress 6.6/6.7,
Yoast schema graph, lazy-loaded images with data-src, wp-carousel-free
galleries in the 2024 photo posts).  Every version of a URL carries the
same content, so the latest capture per URL is used.

Outputs (data/extracted/parts/posts_2023_2024.*):
  posts.json     one entry per non-spam post URL
  events.json    talks / activities described by the posts (hand-curated
                 table keyed by slug; the HTML comes from the posts)
  speakers.json  named speakers, bios and photos from the report posts
  editions.json  what the posts tell about editions 2023 and 2024
  media.json     posters and photo galleries used by the posts
  notes.md       coverage, skips, oddities, per-year counts

Deterministic, rerunnable, no network.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import (  # noqa: E402
    EXTRACTED, BeautifulSoup, clean_html, edition_number_for_year, latest_per_url,
    manifest_rows, norm_url, roman, soup_of, text_of,
)

FAMILY = "posts_2023_2024"
PARTS = EXTRACTED / "parts"
MADRID = ZoneInfo("Europe/Madrid")
SITE = "https://www.innosoftdays.com"

URL_DATE_RE = re.compile(r"^https://www\.innosoftdays\.com/(?:en/)?(\d{4})/(\d{2})/(\d{2})/([^/]+)/?$")

# Posts that are not content of the event: SEO spam injected while the site
# was compromised (Turkish casino texts under user innosoft_manager) and
# empty "New Post" placeholders. Kept out of posts.json, listed in the notes.
SKIP_SLUGS = {
    "turkiye-bolgesinde-tek-pinup-kumarhane-tercih-etme": "SEO spam (Turkish casino text) injected into the site, not InnoSoft content",
    "paribahis-yuksek-oranlar-engin-musabaka-2": "SEO spam (Turkish betting text) injected into the site, not InnoSoft content",
    "new-post": "empty placeholder post (no content, no image)",
    "new-post-2": "empty placeholder post (no content, no image)",
}

# WordPress category slugs (from the article class list) to display names,
# used when the Yoast graph omits articleSection (default category).
CATEGORY_NAMES = {
    "sin-categoria": "Sin categoría", "sin-categoria-es": "Sin categoría", "sin-categoria-en": "Uncategorized",
    "noticias": "Noticias", "fotos": "Fotos", "fotos-en": "Photos",
}

# English posts published in November 2024 whose photos belong to the 2023
# edition (Monday 6, Tuesday 7 and Wednesday 8 November 2023; images live
# under wp-content/uploads/2023/11).
EDITION_OVERRIDE = {
    "images-of-monday-november-6": 2023,
    "images-from-tuesday-november-7": 2023,
    "images-of-wednesday-november-8": 2023,
}


# --------------------------------------------------------------------------
# HTML helpers (local to this family)
# --------------------------------------------------------------------------

def unlazy(node):
    """Give lazy-loaded <img> their real src (data-src) and drop plugin
    placeholders (spinner, preloader) and carousel chrome. Mutates node."""
    for sel in (".wpcp-carousel-preloader", ".swiper-pagination", ".swiper-button-prev",
                ".swiper-button-next", ".wpcp-swiper-dots", "i.fa"):
        for t in node.select(sel):
            t.decompose()
    for img in list(node.find_all("img")):
        real = img.get("data-src") or img.get("data-lazy-src") or ""
        src = img.get("src") or ""
        if not real and src.startswith("data:"):
            # try srcset
            ss = img.get("data-srcset") or img.get("srcset") or ""
            if ss:
                real = ss.split(",")[0].strip().split(" ")[0]
        if real:
            img["src"] = real
        src = img.get("src") or ""
        if not src or src.startswith("data:") or "/wp-content/plugins/" in src:
            img.decompose()
    return node


def prepare(node):
    """Block-level fixes before clean_html: file blocks become paragraphs,
    gallery wrappers (figure inside figure) are unwrapped. Mutates node."""
    for t in node.select(".wp-block-file"):
        t.name = "p"
        links = t.find_all("a")
        for a in links[1:]:
            a.insert_before(" (")
            a.insert_after(")")
    for fig in list(node.find_all("figure")):
        if fig.find("figure") is not None:
            fig.unwrap()
    return node


def content_html(ec) -> str:
    """Cleaned semantic HTML of an Astra entry-content node."""
    if ec is None:
        return ""
    node = BeautifulSoup(str(ec), "lxml")
    unlazy(node)
    prepare(node)
    return clean_html(node)


def image_urls(node) -> list[str]:
    """Distinct real image URLs inside a node, in document order."""
    node = BeautifulSoup(str(node), "lxml")
    unlazy(node)
    out, seen = [], set()
    for img in node.find_all("img"):
        u = norm_url(img.get("src"))
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def sections(ec, tags=("h2", "h3", "h4")):
    """Split entry-content into (heading_text, [sibling nodes]) chunks.
    Nodes before the first heading come under heading ''."""
    out, cur, nodes = [], "", []
    for child in ec.children:
        name = getattr(child, "name", None)
        if name in tags:
            out.append((cur, nodes))
            cur, nodes = text_of(child), []
        else:
            nodes.append(child)
    out.append((cur, nodes))
    return out


def nodes_html(nodes) -> str:
    node = BeautifulSoup("".join(str(n) for n in nodes), "lxml")
    unlazy(node)
    prepare(node)
    return clean_html(node)


def section_by_heading(ec, wanted: str, tags=("h2", "h3", "h4")):
    for h, nodes in sections(ec, tags):
        if h.strip().lower() == wanted.strip().lower():
            return nodes
    return None


def to_madrid(iso: str | None):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(microsecond=0)
    return dt.astimezone(MADRID).replace(tzinfo=None, microsecond=0)


def yoast_article(soup) -> dict:
    sc = soup.find("script", class_="yoast-schema-graph")
    if not sc or not sc.string:
        return {}
    try:
        g = json.loads(sc.string)
    except ValueError:
        return {}
    for n in g.get("@graph", []):
        t = n.get("@type")
        if t == "Article" or (isinstance(t, list) and "Article" in t):
            return n
    return {}


def og(soup, prop: str) -> str:
    m = soup.find("meta", property=prop)
    return (m.get("content") or "").strip() if m else ""


def excerpt_of(soup, ec) -> str:
    """og:description (Yoast) unless it is the auto-generated text of a
    file-only post (bare PDF file name + 'Descarga'); then the readable
    text of the content, at most 200 characters."""
    d = og(soup, "og:description")
    if d and not d.endswith("Descarga") and re.search(r"\s", d):
        return d
    if ec is None:
        return ""
    node = BeautifulSoup(str(ec), "lxml")
    for br in node.find_all("br"):
        br.replace_with(" ")
    for a in node.select(".wp-block-file a"):
        if text_of(a) == "Descarga":
            a.decompose()
    txt = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
    if re.fullmatch(r"[\w.\-]*", txt):  # a bare file name is not an excerpt
        return ""
    if len(txt) > 200:
        txt = txt[:200].rsplit(" ", 1)[0] + "..."
    return txt


# --------------------------------------------------------------------------
# Scope
# --------------------------------------------------------------------------

def in_scope(url: str) -> bool:
    m = URL_DATE_RE.match(url)
    return bool(m) and m.group(1) in ("2023", "2024")


def scope_rows():
    return [r for r in manifest_rows("post") if in_scope(r["url"])]


# --------------------------------------------------------------------------
# Posts
# --------------------------------------------------------------------------

def parse_post(row: dict) -> dict:
    """One post from its latest capture. Returns the JSON entry plus
    working data (soup, entry-content) under key '_'."""
    url = row["url"]
    m = URL_DATE_RE.match(url)
    yyyy, mm, dd, slug = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
    soup = soup_of(row)
    art = soup.find("article") or soup
    ec = art.find(class_="entry-content")
    ya = yoast_article(soup)

    dt = to_madrid(ya.get("datePublished"))
    if dt is None:
        meta = art.find(class_="entry-meta")
        mm2 = re.search(r"(\d{2})/(\d{2})/(\d{4})", text_of(meta)) if meta else None
        if mm2:
            dt = datetime(int(mm2.group(3)), int(mm2.group(2)), int(mm2.group(1)))
        else:
            dt = datetime(yyyy, mm, dd)

    lang = (soup.html.get("lang") or "es").split("-")[0].lower() if soup.html else "es"
    if url.startswith(SITE + "/en/"):
        lang = "en"

    h1 = art.find("h1")
    title = text_of(h1) or og(soup, "og:title").replace(" - InnoSoft Days", "").strip()
    title = title.replace("​", "").strip()

    cats = list(ya.get("articleSection") or [])
    tags = ya.get("keywords") or []
    if not cats:
        for c in art.get("class") or []:
            if c.startswith("category-"):
                cats.append(CATEGORY_NAMES.get(c[len("category-"):], c[len("category-"):]))
    categories = []
    for c in cats + list(tags):
        if c and c not in categories:
            categories.append(c)

    html = content_html(ec)
    imgs = image_urls(ec) if ec is not None else []
    featured = norm_url(og(soup, "og:image")) or (imgs[0] if imgs else "")

    edition_year = EDITION_OVERRIDE.get(slug, yyyy)

    return {
        "date": dt.isoformat(),
        "title": title,
        "slug": slug,
        "excerpt": excerpt_of(soup, ec),
        "content_html": html,
        "featured_image_url": featured,
        "lang": lang,
        "edition_year": edition_year,
        "categories": categories,
        "source_url": url,
        "source_timestamp": row["timestamp"],
        "_": {"soup": soup, "ec": ec, "imgs": imgs, "url": url, "ts": row["timestamp"], "yoast": ya},
    }


# --------------------------------------------------------------------------
# Events, speakers: curated from reading the posts
# --------------------------------------------------------------------------

def P(year: int, mo: int, d: int, hh: int | None = None, mi: int = 0) -> str:
    if hh is None:
        return datetime(year, mo, d).date().isoformat()
    return datetime(year, mo, d, hh, mi).isoformat()


# Each event: which post supplies the HTML/summary ("post"), optionally
# which post supplies the poster ("poster_post"), and fixed metadata.
# "html": "post" -> whole content; "section:<heading>" -> that section only.
EVENTS = [
    # ---------------- 2023 (XI) ----------------
    {"post": "innosoft-days-game-jam", "edition_year": 2023, "title": "Game Jam InnoSoft 2023", "kind": "competition",
     "starts_at": P(2023, 10, 20), "ends_at": P(2023, 11, 3), "modality": "online",
     "link": "https://itch.io/jam/game-jam-innosoft-2023", "html": "post",
     "summary": "Game jam de dos semanas: el tema se desvela el viernes 20 de octubre y los juegos se entregan en itch.io hasta el 3 de noviembre; en solitario o en equipos de hasta 3 personas, cualquier motor y assets libres; premio simbólico y canal de Discord para dudas."},
    {"post": "torneo-smash-bros", "edition_year": 2023, "title": "Torneo Smash Bros", "kind": "competition",
     "starts_at": P(2023, 11, 7, 17, 30), "modality": "in_person",
     "link": "https://docs.google.com/forms/d/e/1FAIpQLSdabH5n2iQ7fjPM-MYaPgYCuaPJXNUuBn8j0tpboc9bKIGoHQ/viewform", "html": "post",
     "summary": "Torneo de Super Smash Bros Ultimate en la ETSII el martes 7 de noviembre a partir de las 17:30: batallas 1 vs 1 de 4 minutos y 3 vidas, sin objetos, con joy-cons de Nintendo Switch; premio para el ganador; inscripción por formulario."},
    {"post": "concurso-imagenes-ia", "edition_year": 2023, "title": "Concurso de imágenes generadas con IA", "kind": "competition",
     "starts_at": P(2023, 10, 23), "ends_at": P(2023, 10, 29, 23, 59), "modality": "online",
     "link": "https://itch.io/jam/concurso-imgenes-ia", "html": "post",
     "summary": "Concurso de generación de imagenes con inteligencia artificial sobre el tema Conciencia Ambiental: entrega del 23 al 29 de octubre en itch.io, votación popular del 30 de octubre al 3 de noviembre y fallo del jurado el 4 y 5 de noviembre."},
    {"post": "gymkana-de-sostenibilidad", "edition_year": 2023, "title": "Gymkana de Sostenibilidad", "kind": "competition",
     "starts_at": P(2023, 11, 7, 10, 30), "ends_at": P(2023, 11, 7, 12, 30), "modality": "in_person", "room": "Stand de Sostenibilidad",
     "html": "post",
     "summary": "Gymkana del stand de Sostenibilidad para encontrar carteles de animales de Doñana escondidos por la ETSII a partir de pistas; el 7 de noviembre de 10:30 a 12:30, individual o en grupo, con premio para quien encuentre todos los carteles."},
    {"post": "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-1", "poster_post": "explorando-el-futuro-laboral-de-los-nuevos-ingenierso-de-software-parte-1",
     "edition_year": 2023, "title": "Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 1", "kind": "talk",
     "starts_at": P(2023, 11, 6), "modality": "in_person", "html": "post",
     "speaker": "Isabel Arrans Vega, Matthew Bwye Lera, Soraya Peceño Capilla, Carlos Guillermo Müller Cejas",
     "summary": "Charla del 6 de noviembre con cuatro ponentes que contaron su experiencia en la ingeniería del software y dieron consejos para crecer en la industria: los ganadores del Premio Nacional al mejor TFG (SCRUM RPG), una ingeniera con 15 años de trayectoria y un profesor de la escuela."},
    {"post": "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2", "poster_post": "informacion-sobre-la-ponencia-del-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2",
     "edition_year": 2023, "title": "Explorando el futuro profesional de los nuevos Ingenieros de Software. Parte 2", "kind": "talk",
     "starts_at": P(2023, 11, 6), "modality": "in_person", "html": "post",
     "speaker": "Pablo Cala, Carlos Pérez, José Ignacio Morales",
     "summary": "Charla del 6 de noviembre sobre emprendimiento en la ingeniería del software, presentada por Juan Antonio Álvarez (subdirector de investigación, transferencia y emprendimiento de la US), con tres emprendedores que contaron su historia y dieron consejos para empezar a emprender."},
    {"post": "informacion-sobre-la-ponencia-de-produccion-y-composicion-musical-con-inteligencia-artificial", "edition_year": 2023,
     "title": "Producción y composición musical con Inteligencia Artificial", "kind": "talk", "modality": "in_person", "html": "post",
     "summary": "Ponencia anunciada mediante cartel (sin texto en el post)."},
    {"post": "taller-ciberseguridad-con-isabel-cayrasso", "edition_year": 2023, "title": "Taller de Ciberseguridad", "kind": "workshop",
     "modality": "in_person", "html": "post", "speaker": "Isabel Cayrasso",
     "summary": "Taller de ciberseguridad impartido por Isabel Cayrasso, anunciado mediante cartel (sin texto en el post)."},
    {"post": "informacion-de-la-charla-la-ia-motor-de-la-transformacion-laboral", "edition_year": 2023,
     "title": "La IA, motor de la transformación laboral", "kind": "talk", "modality": "in_person", "html": "post",
     "summary": "Charla anunciada mediante cartel (sin texto en el post)."},
    {"post": "informacion-de-la-charla-retos-sociales-y-eticos-de-la-ia", "edition_year": 2023,
     "title": "Retos sociales y éticos de la IA", "kind": "talk", "modality": "in_person", "html": "post",
     "summary": "Charla anunciada mediante cartel (sin texto en el post)."},
    {"post": "informacion-de-la-charla-superando-barreras-de-escalado-en-las-large-lenguage-models-llm", "edition_year": 2023,
     "title": "Superando barreras de escalado en las large lenguage models (LLM)", "kind": "talk", "modality": "in_person", "html": "post",
     "summary": "Charla anunciada mediante cartel (sin texto en el post)."},
    {"post": "tecnologia-y-arte", "poster_post": "informacion-de-la-charla-tecnologia-y-arte", "edition_year": 2023,
     "title": "Tecnología y Arte", "kind": "talk", "starts_at": P(2023, 11, 8), "modality": "in_person", "html": "post",
     "speaker": "Rocío García Robles, Olga Albillo, Helena Hernández Acuaviva, Agda Carvalho, Leila Pontiga, Irene Ugolini Sánchez-Barroso, Ana Rosa González Diáñez",
     "summary": "Sesión que abrió el último día de las jornadas con seis intervenciones sobre tecnología e IA aplicadas al arte: proyecto ASTER, instalaciones interactivas, sesgos y traducción automática, aprendizaje de idiomas con IA, cómics más allá de lo impreso y IA para el diseño UX/UI."},
    {"post": "informacion-de-la-charla-transformando-la-salud-con-inteligencia-artificial", "edition_year": 2023,
     "title": "Transformando la salud con inteligencia artificial", "kind": "talk", "modality": "in_person", "html": "post",
     "summary": "Charla anunciada mediante cartel (sin texto en el post)."},
    {"post": "charla-de-apertura-de-las-jornadas", "edition_year": 2023, "title": "Charla de apertura de las jornadas", "kind": "ceremony",
     "starts_at": P(2023, 11, 6), "modality": "in_person", "html": "post", "no_poster": True,
     "summary": "Breve charla introductoria a cargo de los presidentes y los coordinadores de Programa que abrio las jornadas de 2023 (sold out), con la explicación del acceso con entrada y el repaso de todas las actividades, horarios y aulas."},
    # ---------------- 2024 (XII) ----------------
    {"post": "fotos-del-seminario-floss-25-10-2024", "edition_year": 2024, "title": "Seminario FLOSS (free/libre and open-source software)", "kind": "talk",
     "starts_at": P(2024, 10, 25), "modality": "in_person", "html": "post", "no_poster": True,
     "speaker": "David Benavides", "company": "Universidad de Sevilla",
     "link": "https://hdvirtual.us.es/discovirt/index.php/s/BCk7KiP83NWNmPH",
     "summary": "Seminario sobre el software libre y de fuentes abiertas impartido el 25 de octubre de 2024 por David Benavides, coordinador y profesor de teoría de EGC, en horario de clase de la asignatura; definición de FLOSS, ejemplos, historia, tipos de licencias. Marca el comienzo de la programación de InnoSoft Days 2024."},
    {"post": "imagenes-del-5-de-noviembre-de-2024", "edition_year": 2024, "title": "Stands del primer día", "kind": "stand",
     "starts_at": P(2024, 11, 5), "modality": "in_person", "html": "section:Stands", "no_poster": True,
     "summary": "Stands del 5 de noviembre de 2024 (primer día de la XII edición): stand de Igualdad, stand de Cruz Roja y punto de información, según las fotos publicadas."},
    {"post": "imagenes-del-5-de-noviembre-de-2024", "edition_year": 2024, "title": "Yincana", "kind": "competition",
     "starts_at": P(2024, 11, 5), "modality": "in_person", "html": "section:Yincana", "no_poster": True,
     "summary": "Yincana del 5 de noviembre de 2024, documentada solo con fotos."},
    {"post": "imagenes-del-5-de-noviembre-de-2024", "edition_year": 2024, "title": "SofIA e IsaIA", "kind": "stand",
     "starts_at": P(2024, 11, 5), "modality": "in_person", "html": "section:SofIA e IsaIA", "no_poster": True,
     "summary": "SofIA e IsaIA en el primer día de las jornadas (5 de noviembre de 2024), documentadas solo con fotos (stand con Canal Sur presente)."},
    {"post": "imagenes-del-5-de-noviembre-de-2024", "edition_year": 2024, "title": "Charla de Irene Morgado", "kind": "talk",
     "starts_at": P(2024, 11, 5), "modality": "in_person", "html": "section:Charla Irene Morgado", "no_poster": True,
     "speaker": "Irene Morgado",
     "summary": "Charla de Irene Morgado el 5 de noviembre de 2024, documentada solo con fotos."},
    {"post": "imagenes-del-5-de-noviembre-de-2024", "edition_year": 2024, "title": "Charla de Rewoox", "kind": "talk",
     "starts_at": P(2024, 11, 5), "modality": "in_person", "html": "section:Charla de Rewoox", "no_poster": True,
     "company": "Rewoox",
     "summary": "Charla de la empresa Rewoox el 5 de noviembre de 2024, documentada solo con fotos."},
    {"post": "imagenes-del-5-de-noviembre-de-2024", "edition_year": 2024, "title": "Charla de 4i.ai", "kind": "talk",
     "starts_at": P(2024, 11, 5), "modality": "in_person", "html": "section:Charla de 4i.ai", "no_poster": True,
     "company": "4i.ai",
     "summary": "Charla de la empresa 4i.ai el 5 de noviembre de 2024, documentada solo con fotos."},
    {"post": "images-of-november-6-2024", "edition_year": 2024, "title": "Taller de cibervirus", "kind": "workshop",
     "starts_at": P(2024, 11, 6), "modality": "in_person", "html": "section:Cyber Virus Workshop", "no_poster": True,
     "summary": "Taller sobre virus informáticos del 6 de noviembre de 2024 (segundo día), documentado solo con fotos en el post en inglés (Cyber Virus Workshop)."},
    {"post": "images-of-november-6-2024", "edition_year": 2024, "title": "Ceremonia de apertura", "kind": "ceremony",
     "starts_at": P(2024, 11, 6), "modality": "in_person", "html": "section:Opening Ceremony", "no_poster": True,
     "summary": "Ceremonia de apertura de InnoSoft Days 2024 el 6 de noviembre, documentada solo con fotos en el post en inglés (Opening Ceremony)."},
    {"post": "images-of-november-6-2024", "edition_year": 2024, "title": "Charla de Raúl López", "kind": "talk",
     "starts_at": P(2024, 11, 6), "modality": "in_person", "html": "section:Talk by Raúl López", "no_poster": True,
     "speaker": "Raúl López",
     "summary": "Charla de Raúl López el 6 de noviembre de 2024, documentada solo con fotos en el post en inglés."},
    {"post": "images-of-november-6-2024", "edition_year": 2024, "title": "Charla de Ignasi Labastida", "kind": "talk",
     "starts_at": P(2024, 11, 6), "modality": "in_person", "html": "section:Lecture Ignasi Labastida", "no_poster": True,
     "speaker": "Ignasi Labastida",
     "summary": "Charla de Ignasi Labastida el 6 de noviembre de 2024, documentada solo con fotos en el post en inglés."},
    {"post": "images-of-november-6-2024", "edition_year": 2024, "title": "Charla de Rafael Guitart", "kind": "talk",
     "starts_at": P(2024, 11, 6), "modality": "in_person", "html": "section:Rafael Guitart Talk", "no_poster": True,
     "speaker": "Rafael Guitart",
     "summary": "Charla de Rafael Guitart el 6 de noviembre de 2024, documentada solo con fotos en el post en inglés."},
]

# Speaker bios: post slug -> heading in the post -> list of speaker dicts.
# The section under the heading becomes bio_html (or talk summary when the
# post is organised by talk rather than by person), its first image the photo.
SPEAKER_SECTIONS = {
    "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-1": {
        "Isabel Arrans Vega y Matthew Bwye Lera": [
            {"name": "Isabel Arrans Vega", "affiliation": "Light Software", "position": "Desarrolladora de videojuegos; Premio Nacional al mejor TFG (SCRUM RPG)"},
            {"name": "Matthew Bwye Lera", "affiliation": "", "position": "Premio Nacional al mejor TFG (SCRUM RPG)"},
        ],
        "Soraya Peceño Capilla": [{"name": "Soraya Peceño Capilla", "affiliation": "", "position": "Ingeniera informática con más de 15 años de experiencia (Sadiel, Ayesa, Admiral Tech)"}],
        "Carlos Guillermo Müller Cejas": [{"name": "Carlos Guillermo Müller Cejas", "affiliation": "Universidad de Sevilla", "position": "Profesor de la ETSII"}],
    },
    "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2": {
        "": [{"name": "Juan Antonio Álvarez", "affiliation": "Universidad de Sevilla", "position": "Subdirector de investigación, transferencia y emprendimiento", "no_photo": True, "no_bio": True}],
        "Pablo Cala": [{"name": "Pablo Cala", "affiliation": "MCCM Innovations", "position": "Fundador"}],
        "Carlos Pérez": [{"name": "Carlos Pérez", "affiliation": "", "position": "Emprendedor, software de gestión de reservas para restaurantes"}],
        "José Ignacio Morales": [{"name": "José Ignacio Morales", "affiliation": "", "position": "Economista"}],
    },
    "tecnologia-y-arte": {
        "Proyecto ASTER": [{"name": "Rocío García Robles", "affiliation": "Universidad de Sevilla", "position": "Profesora, doctora en Bellas Artes (proyecto ASTER)"}],
        "Instalaciones Interactivas mediante dispositivos electrónicos en el arte moderno": [{"name": "Olga Albillo", "affiliation": "", "position": ""}],
        "Sesgos y Traducción Automática": [
            {"name": "Helena Hernández Acuaviva", "affiliation": "", "position": ""},
            {"name": "Agda Carvalho", "affiliation": "Brasil", "position": ""},
        ],
        "Aprendizaje de idiomas con IA": [{"name": "Leila Pontiga", "affiliation": "", "position": ""}],
        "Cómics más allá de lo impreso": [{"name": "Irene Ugolini Sánchez-Barroso", "affiliation": "", "position": ""}],
        "El uso de la IA para el desarrollo UX/UI": [{"name": "Ana Rosa González Diáñez", "affiliation": "", "position": ""}],
    },
    "taller-ciberseguridad-con-isabel-cayrasso": {
        "": [{"name": "Isabel Cayrasso", "affiliation": "", "position": "", "no_bio": True, "no_photo": True}],
    },
    "fotos-del-seminario-floss-25-10-2024": {
        "": [{"name": "David Benavides", "affiliation": "Universidad de Sevilla", "position": "Coordinador y profesor de teoría de EGC (Evolución y Gestión de la Configuración)", "no_bio": True}],
    },
    "imagenes-del-5-de-noviembre-de-2024": {
        "Charla Irene Morgado": [{"name": "Irene Morgado", "affiliation": "", "position": "", "no_bio": True}],
    },
    "images-of-november-6-2024": {
        "Talk by Raúl López": [{"name": "Raúl López", "affiliation": "", "position": "", "no_bio": True}],
        "Lecture Ignasi Labastida": [{"name": "Ignasi Labastida", "affiliation": "", "position": "", "no_bio": True}],
        "Rafael Guitart Talk": [{"name": "Rafael Guitart", "affiliation": "", "position": "", "no_bio": True}],
    },
}


def event_html_and_images(entry: dict, post: dict):
    ec = post["_"]["ec"]
    spec = entry.get("html", "post")
    if spec == "post":
        return post["content_html"], post["_"]["imgs"]
    if spec.startswith("section:"):
        nodes = section_by_heading(ec, spec[len("section:"):])
        if nodes is None:
            return "", []
        return nodes_html(nodes), image_urls(BeautifulSoup("".join(str(n) for n in nodes), "lxml"))
    return "", []


def build_events(posts_by_slug: dict) -> tuple[list[dict], list[str]]:
    events, problems = [], []
    for e in EVENTS:
        post = posts_by_slug.get(e["post"])
        if not post:
            problems.append(f"event '{e['title']}': post {e['post']} not in scope/manifest")
            continue
        html, imgs = event_html_and_images(e, post)
        if e.get("html", "post") == "post" and not e.get("no_poster") and not text_of(BeautifulSoup(html, "lxml")).strip():
            html = ""  # poster-only post: the image already goes to poster_url
        poster = ""
        if not e.get("no_poster"):
            src = posts_by_slug.get(e.get("poster_post") or e["post"])
            if src:
                poster = src["featured_image_url"] or (src["_"]["imgs"][0] if src["_"]["imgs"] else "")
        events.append({
            "edition_year": e["edition_year"],
            "title": e["title"],
            "kind": e["kind"],
            "starts_at": e.get("starts_at"),
            "ends_at": e.get("ends_at"),
            "room": e.get("room"),
            "modality": e.get("modality"),
            "speaker": e.get("speaker"),
            "company": e.get("company"),
            "summary": e.get("summary", ""),
            "description_html": html,
            "poster_url": poster or None,
            "link": e.get("link"),
            "lang": "es",
            "source_url": post["source_url"],
            "source_timestamp": post["source_timestamp"],
        })
    return events, problems


def build_speakers(posts_by_slug: dict) -> tuple[list[dict], list[str]]:
    speakers, problems = [], []
    seen: dict[str, dict] = {}
    for slug, headings in SPEAKER_SECTIONS.items():
        post = posts_by_slug.get(slug)
        if not post:
            problems.append(f"speakers: post {slug} not in scope/manifest")
            continue
        ec = post["_"]["ec"]
        year = post["edition_year"]
        for heading, people in headings.items():
            nodes = section_by_heading(ec, heading) if heading else sections(ec)[0][1]
            bio = nodes_html(nodes) if nodes else ""
            imgs = image_urls(BeautifulSoup("".join(str(n) for n in nodes), "lxml")) if nodes else []
            for p in people:
                key = p["name"].lower()
                entry = seen.get(key)
                if entry is None:
                    entry = {
                        "name": p["name"],
                        "affiliation": p.get("affiliation", ""),
                        "position": p.get("position", ""),
                        "bio_html": "" if p.get("no_bio") else bio,
                        "photo_url": "" if p.get("no_photo") else (imgs[0] if imgs else ""),
                        "links": [],
                        "edition_years": [year],
                        "source_url": post["source_url"],
                    }
                    seen[key] = entry
                    speakers.append(entry)
                elif year not in entry["edition_years"]:
                    entry["edition_years"].append(year)
    return speakers, problems


# --------------------------------------------------------------------------
# Editions and media
# --------------------------------------------------------------------------

def build_editions(posts: list[dict]) -> list[dict]:
    src23 = [p["source_url"] for p in posts if p["edition_year"] == 2023]
    src24 = [p["source_url"] for p in posts if p["edition_year"] == 2024]
    return [
        {
            "year": 2023, "number": edition_number_for_year(2023), "roman": roman(edition_number_for_year(2023)),
            "name": "InnoSoft Days 2023 (XI edición)",
            "starts_on": "2023-11-06", "ends_on": "2023-11-08",
            "venue": "ETSII, Universidad de Sevilla",
            "summary": "Undécima edición de las jornadas, celebrada en la ETSII del lunes 6 al miércoles 8 de noviembre de 2023 con la inteligencia artificial como tema central.",
            "description_html": (
                "<p>La XI edición de InnoSoft Days se celebró en la ETSII (Universidad de Sevilla) del lunes 6 al miércoles 8 de noviembre de 2023. "
                "El tema principal fue la inteligencia artificial: los posts previos introdujeron la IA, Copilot X, las IAs para programar, la IA en el arte y sus controversias.</p>"
                "<p>Actividades documentadas en el blog: la Game Jam de InnoSoft (20 de octubre al 3 de noviembre, itch.io), el concurso de imágenes generadas con IA sobre conciencia ambiental (23 al 29 de octubre), "
                "el torneo de Smash Bros (7 de noviembre, 17:30), la gymkana de sostenibilidad sobre la fauna de Doñana (7 de noviembre, 10:30 a 12:30), la charla de apertura, "
                "las dos partes de <em>Explorando el futuro profesional de los nuevos Ingenieros de Software</em> (6 de noviembre), la sesión <em>Tecnología y Arte</em> (8 de noviembre) "
                "y varias charlas anunciadas mediante cartel (produccion musical con IA, taller de ciberseguridad con Isabel Cayrasso, la IA como motor de la transformación laboral, retos sociales y éticos de la IA, "
                "escalado de los LLM, transformando la salud con IA). El comite de Igualdad publicó además cuatro lecturas en PDF.</p>"
            ),
            "registration_url": None,
            "sources": sorted(set(src23)),
            "confidence": "medium",
            "notes": "Dates inferred from the posts (talks on 6 Nov, Smash and gymkana on 7 Nov, Tecnología y Arte 'último día' and English photo posts for Monday 6, Tuesday 7 and Wednesday 8 November 2023). The home page meta description of the time said '6, 8 y 9 de noviembre de 2023' instead; the posts and photos support 6, 7 and 8.",
        },
        {
            "year": 2024, "number": edition_number_for_year(2024), "roman": roman(edition_number_for_year(2024)),
            "name": "InnoSoft Days 2024 (XII edición)",
            "starts_on": "2024-11-05", "ends_on": "2024-11-08",
            "venue": "ETSII, Universidad de Sevilla",
            "summary": "Duodécima edición de las jornadas, celebrada en la ETSII del 5 al 8 de noviembre de 2024, precedida por el seminario FLOSS del 25 de octubre.",
            "description_html": (
                "<p>La XII edición de InnoSoft Days se celebró en la ETSII (Universidad de Sevilla) en noviembre de 2024. El blog documenta el primer día (5 de noviembre: stands de Igualdad y Cruz Roja, punto de información, yincana, SofIA e IsaIA, charlas de Irene Morgado, Rewoox y 4i.ai, con Canal Sur grabando) "
                "y el segundo día (6 de noviembre: taller de cibervirus, ceremonia de apertura, charlas de Raúl López, Ignasi Labastida y Rafael Guitart y finales de dos torneos).</p>"
                "<p>Antes de las jornadas, el 25 de octubre de 2024, David Benavides impartió un seminario sobre software libre (FLOSS) que marcó el comienzo de la programación. "
                "Los comités de Sostenibilidad e Igualdad publicaron artículos sobre reciclaje de pilas, hardware y aceite, la huella de ChatGPT, el impacto ambiental de la blockchain, el transporte del alumnado a la ETSII y la brecha salarial en la informática, además de lecturas en PDF en inglés.</p>"
            ),
            "registration_url": None,
            "sources": sorted(set(src24)),
            "confidence": "medium",
            "notes": "Posts evidence days 5 and 6 November 2024 (first and second day). The full range 5 to 8 November comes from the home page meta description ('del 5 al 8 de noviembre de 2024') captured in November 2024; no post in this family covers 7 or 8 November.",
        },
    ]


POSTER_SLUGS = {
    "explorando-el-futuro-laboral-de-los-nuevos-ingenierso-de-software-parte-1",
    "informacion-sobre-la-ponencia-de-produccion-y-composicion-musical-con-inteligencia-artificial",
    "informacion-sobre-la-ponencia-del-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2",
    "taller-ciberseguridad-con-isabel-cayrasso",
    "informacion-de-la-charla-la-ia-motor-de-la-transformacion-laboral",
    "informacion-de-la-charla-retos-sociales-y-eticos-de-la-ia",
    "informacion-de-la-charla-superando-barreras-de-escalado-en-las-large-lenguage-models-llm",
    "informacion-de-la-charla-tecnologia-y-arte",
    "informacion-de-la-charla-transformando-la-salud-con-inteligencia-artificial",
    "innosoft-days-game-jam", "concurso-imagenes-ia", "gymkana-de-sostenibilidad", "torneo-smash-bros",
}
PHOTO_SLUGS = {
    "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-1",
    "explorando-el-futuro-profesional-de-los-nuevos-ingenieros-de-software-parte-2",
    "tecnologia-y-arte", "charla-de-apertura-de-las-jornadas",
    "fotos-del-seminario-floss-25-10-2024", "imagenes-del-5-de-noviembre-de-2024",
    "images-of-november-6-2024", "images-of-november-6-2024-2",
    "images-of-monday-november-6", "images-from-tuesday-november-7", "images-of-wednesday-november-8",
}


def build_media(posts: list[dict]) -> list[dict]:
    media: dict[str, dict] = {}

    def add(url, kind, year, caption, used_by):
        if not url or "/wp-content/uploads/" not in url:
            return
        m = media.get(url)
        if m is None:
            media[url] = {"url": url, "kind": kind, "edition_year": year, "caption": caption, "used_by": [used_by]}
        elif used_by not in m["used_by"]:
            m["used_by"].append(used_by)

    poster_titles = {}
    for e in EVENTS:
        if not e.get("no_poster"):
            poster_titles[e.get("poster_post") or e["post"]] = e["title"]
    for p in posts:
        slug, year, url = p["slug"], p["edition_year"], p["source_url"]
        if slug in POSTER_SLUGS:
            u = p["featured_image_url"] or (p["_"]["imgs"][0] if p["_"]["imgs"] else "")
            add(u, "poster", year, poster_titles.get(slug, p["title"]), url)
        if slug in PHOTO_SLUGS:
            ec = p["_"]["ec"]
            if ec is None:
                continue
            for heading, nodes in sections(ec):
                imgs = image_urls(BeautifulSoup("".join(str(n) for n in nodes), "lxml"))
                cap = f"{p['title']} - {heading}" if heading else p["title"]
                for u in imgs:
                    add(u, "photo", year, cap, url)
    return list(media.values())


# --------------------------------------------------------------------------
# Notes
# --------------------------------------------------------------------------

def write_notes(rows, chosen, posts, skipped, events, speakers, editions, media, problems):
    by_year = {}
    for p in posts:
        by_year.setdefault(p["edition_year"], []).append(p)
    lines = [
        f"# {FAMILY}",
        "",
        "Blog posts (kind=post) whose URL date year is 2023 or 2024, Spanish (/YYYY/MM/DD/slug/) and English (/en/YYYY/MM/DD/slug/) permalinks. "
        "All captures are the Astra single-post template of the WordPress site (Yoast schema graph for date/categories/tags, lazy images with data-src, wp-carousel-free galleries in the 2024 photo posts).",
        "",
        "## Coverage",
        "",
        f"- Captures in scope: {len(rows)} ({len(chosen)} distinct URLs).",
        f"- Posts extracted: {len(posts)}; skipped: {len(skipped)} URLs ({sum(len(v) for _, v, _ in skipped)} captures).",
        f"- Events: {len(events)}; speakers: {len(speakers)}; editions: {len(editions)}; media: {len(media)}.",
        "- The latest capture per URL was used; the parser hashes the entry-content text of every other capture of the same URL and lists any difference under Problems (none so far, so older captures are covered by the one used).",
        "",
        "## Per year (edition_year of the extracted posts)",
        "",
    ]
    for y in sorted(by_year):
        lines.append(f"- {y}: {len(by_year[y])} posts, {sum(1 for e in events if e['edition_year'] == y)} events, {sum(1 for s in speakers if y in s['edition_years'])} speakers, {sum(1 for m in media if m['edition_year'] == y)} media")
    lines += ["", "## Posts extracted (url, capture used, other captures)", ""]
    for p in sorted(posts, key=lambda p: p["date"]):
        others = [r["timestamp"] for r in rows if r["url"] == p["source_url"] and r["timestamp"] != p["source_timestamp"]]
        lines.append(f"- {p['date'][:10]} [{p['lang']}] {p['title']} <{p['source_url']}> capture {p['source_timestamp']}" + (f" (also {', '.join(others)})" if others else ""))
    lines += ["", "## Skipped (url, captures, reason)", ""]
    for url, tss, why in skipped:
        lines.append(f"- {url} ({', '.join(tss)}): {why}")
    lines += [
        "",
        "## How events, speakers and editions were derived",
        "",
        "- Events are a hand-curated table keyed by post slug (deterministic); description_html is the cleaned post content (or the gallery section under the matching heading in the photo posts). "
        "Announcement + report pairs were merged into ONE event: 'Explorando el futuro profesional... Parte 1' (poster post 2023-10-30 + report 2023-11-20), 'Parte 2' (poster 2023-10-30 + report 2023-11-20), 'Tecnología y Arte' (poster 2023-10-31 + report 2023-11-21). source_url points at the report post, poster_url at the announcement image.",
        "- Poster-only 2023 posts ('Información de la charla: ...') have no text at all, only the poster image; their events have title, kind and poster_url only (no date, no speaker). The event-plugin pages of 2023 (other family) should carry the schedule; merge by title.",
        "- 2024 events come from the headings of the photo posts of 5 November (Spanish) and 6 November (English only; the Spanish original was not captured). Titles under English headings were rendered in Spanish (Cyber Virus Workshop -> Taller de cibervirus, Opening Ceremony -> Ceremonia de apertura, Talk by X -> Charla de X). 'Detrás de las cámaras' (Canal Sur filming) was not made an event.",
        "- Speakers: names, affiliations and positions as written in the report posts; bio_html is the section about the person in 'Explorando... Parte 1/2'. For 'Tecnología y Arte' the post is organised by talk, so bio_html is the summary of that speaker's talk (noted here, not a biography). Juan Antonio Álvarez (US) only introduced Parte 2 and is included without bio or photo. Speakers of the 2024 photo posts (Irene Morgado, Raúl López, Ignasi Labastida, Rafael Guitart, David Benavides) have no bio; photo_url is the first photo of their talk.",
        "- Editions: 2023 dates from the posts (6, 7, 8 November 2023). 2024: posts evidence 5 and 6 November; the range 5-8 November comes from the home page meta description captured in November 2024 (cross-check only, listed in notes of the edition).",
        "- English posts /en/2024/11/09/images-of-{monday-november-6,tuesday-november-7,wednesday-november-8} were published in November 2024 but their photos are of the 2023 edition (weekday + date only match 2023, images under uploads/2023/11); edition_year forced to 2023.",
        "- Post 'date' is the Yoast datePublished converted from UTC to Europe/Madrid (naive); the URL keeps the WordPress permalink date, which always matched the local date.",
        "- categories = Yoast articleSection (WordPress categories) followed by keywords (WordPress tags such as Igualdad, Game Jam, Copilot). 'Sin categoría' is kept as the site had it.",
        "- Media: posters of the announcement posts (kind poster) and gallery/report photos (kind photo, caption = post title plus section heading). Featured images of plain articles are only in posts.featured_image_url.",
        "",
        "## Oddities",
        "",
        "- Four spam/placeholder posts by user innosoft_manager (two Turkish casino texts of January and July 2024, two empty 'New Post' of May 2024) show the site was compromised at some point; skipped.",
        "- 'Las controversias que agitan el mundo de la IA' uses a hot-linked featured image (i.blogs.es); kept as is.",
        "- 'Reciclaje de pilas, hardware y aceite' has an http:// og:image (normalised to https) and four Google Maps iframes (kept as <iframe>).",
        "- The four 2023-11-04 Igualdad posts and the ten /en/2024/11/03-04 ones are just a link to a PDF in wp-content/uploads (the PDFs are not in the raw captures).",
        "- English photo posts of 2023 link to a SharePoint folder with all the photos.",
        "- 'Explorando el futuro laboral de los nuevos ingenierso de software. Parte 1' (sic) is the announcement poster of the 2023-11-20 report; both kept as posts.",
    ]
    if problems:
        lines += ["", "## Problems", ""] + [f"- {p}" for p in problems]
    (PARTS / f"{FAMILY}.notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def strip_private(items: list[dict]) -> list[dict]:
    return [{k: v for k, v in it.items() if k != "_"} for it in items]


def main() -> None:
    PARTS.mkdir(parents=True, exist_ok=True)
    rows = scope_rows()
    chosen = latest_per_url(rows)
    posts, skipped, problems = [], [], []
    for url in sorted(chosen):
        row = chosen[url]
        slug = URL_DATE_RE.match(url).group(4)
        tss = sorted(r["timestamp"] for r in rows if r["url"] == url)
        if slug in SKIP_SLUGS:
            skipped.append((url, tss, SKIP_SLUGS[slug]))
            continue
        try:
            p = parse_post(row)
        except Exception as exc:  # keep going, report
            skipped.append((url, tss, f"parse error: {exc!r}"))
            continue
        if not p["content_html"] and not p["featured_image_url"]:
            skipped.append((url, tss, "no content and no image in the capture"))
            continue
        posts.append(p)

    # Versions of the same URL: report any whose entry-content text differs
    # from the capture used (so far all versions were identical).
    import hashlib
    for p in posts:
        ref = hashlib.md5(text_of(p["_"]["ec"]).encode("utf-8")).hexdigest() if p["_"]["ec"] is not None else ""
        for r in rows:
            if r["url"] != p["source_url"] or r["timestamp"] == p["source_timestamp"]:
                continue
            try:
                ec2 = (soup_of(r).find("article") or soup_of(r)).find(class_="entry-content")
            except Exception:
                continue
            h2 = hashlib.md5(text_of(ec2).encode("utf-8")).hexdigest() if ec2 is not None else ""
            if h2 != ref:
                problems.append(f"{p['source_url']}: capture {r['timestamp']} has different content text than the one used ({p['source_timestamp']}); review manually")

    posts_by_slug = {p["slug"]: p for p in posts}
    events, ep = build_events(posts_by_slug)
    speakers, sp = build_speakers(posts_by_slug)
    problems += ep + sp
    editions = build_editions(posts)
    media = build_media(posts)

    posts.sort(key=lambda p: (p["date"], p["slug"]))
    events.sort(key=lambda e: (e["edition_year"], e["starts_at"] or "9999", e["title"]))
    speakers.sort(key=lambda s: (min(s["edition_years"]), s["name"]))

    def dump_part(kind: str, data):
        (PARTS / f"{FAMILY}.{kind}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    dump_part("posts", strip_private(posts))
    dump_part("events", events)
    dump_part("speakers", speakers)
    dump_part("editions", editions)
    dump_part("media", media)
    write_notes(rows, chosen, posts, skipped, events, speakers, editions, media, problems)

    print(json.dumps({
        "captures_in_scope": len(rows), "urls": len(chosen), "posts": len(posts),
        "skipped_urls": len(skipped), "skipped_captures": sum(len(t) for _, t, _ in skipped),
        "events": len(events), "speakers": len(speakers), "editions": len(editions), "media": len(media),
        "problems": problems,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
