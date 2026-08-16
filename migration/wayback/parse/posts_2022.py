"""Phase 3 parser, family posts_2022.

Scope: every blog post (manifest kind=post) whose permalink date year is
2022, i.e. the news of InnoSoft Days X (8 to 11 November 2022 at the
ETSII, Universidad de Sevilla). Writes, under data/extracted/parts/:

    posts_2022.posts.json      one row per URL (latest capture, all versions
                               of a URL carry the same content)
    posts_2022.events.json     activities/talks described in those posts
    posts_2022.speakers.json   people named as speakers
    posts_2022.editions.json   the 2022 edition entry
    posts_2022.media.json      images/PDFs referenced from the posts
    posts_2022.notes.md        coverage report

Deterministic, no network: `.venv/bin/python parse/posts_2022.py`.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

from parse.common import (  # noqa: E402
    clean_html,
    dump_part,
    edition_number_for_year,
    latest_per_url,
    manifest_rows,
    norm_url,
    roman,
    soup_of,
    text_of,
    unlazy_images,
    wp_datetime_local,
)

FAMILY = "posts_2022"
YEAR = 2022
URL_RE = re.compile(r"^https://www\.innosoftdays\.com/2022/(\d\d)/(\d\d)/([^/]+)/?$")

# WordPress category/tag slugs seen on the 2022 posts (article class list).
CATEGORY_NAMES = {"noticias": "Noticias", "fotos": "Fotos"}
TAG_NAMES = {"igualdad": "Igualdad"}
DROP_CATEGORIES = {"sin-categoria"}  # WordPress default "Uncategorized"

VENUE = "Escuela Técnica Superior de Ingeniería Informática, Universidad de Sevilla"


# --------------------------------------------------------------------------
# posts
# --------------------------------------------------------------------------

def scope_rows() -> list[dict]:
    return [r for r in manifest_rows("post") if URL_RE.match(r["url"])]


def prepare_content(ec) -> None:
    """Normalise the Gutenberg blocks that clean_html cannot handle alone."""
    unlazy_images(ec)
    # wp-block-file: <object pdf> + <a>title</a> + <a download>Descarga</a>
    # -> a single paragraph linking the file by its title.
    for blk in ec.select(".wp-block-file"):
        links = [a for a in blk.find_all("a") if a.get("href")]
        if not links:
            blk.decompose()
            continue
        first = links[0]
        p = ec.new_tag("p") if hasattr(ec, "new_tag") else BeautifulSoup("", "lxml").new_tag("p")
        a = BeautifulSoup("", "lxml").new_tag("a", href=norm_url(first["href"]))
        a.string = text_of(first) or "Descarga"
        p.append(a)
        blk.replace_with(p)
    # sharing / related widgets injected inside entry-content by plugins
    for sel in (".sharedaddy", ".jp-relatedposts", ".post-navigation", ".ast-single-post-navigation"):
        for t in ec.select(sel):
            t.decompose()


SOFT_BREAK_RE = re.compile(r"(?<=[\wáéíóúñü,;:»)”])<br/>\s*(?=[a-záéíóúñü(«“])")


def unwrap_soft_breaks(html: str) -> str:
    """Text pasted from a PDF keeps a <br/> at every wrapped line; join a
    break back into a space when it splits a sentence (word before,
    lowercase after). Real breaks (after punctuation, before capitals) stay."""
    return SOFT_BREAK_RE.sub(" ", html)


def make_excerpt(content_html: str, words: int = 55) -> str:
    """WordPress-style automatic excerpt: first 55 words of the text."""
    txt = BeautifulSoup(content_html, "lxml").get_text(" ", strip=True)
    txt = re.sub(r"\s+", " ", txt)
    parts = txt.split(" ")
    if len(parts) <= words:
        return txt
    return " ".join(parts[:words]).rstrip(" ,;:") + "…"


def post_from_row(row: dict) -> dict:
    s = soup_of(row)
    m = URL_RE.match(row["url"])
    month, day, slug = m.group(1), m.group(2), m.group(3)
    title = text_of(s.select_one("h1.entry-title")) or text_of(s.find("h1"))
    title = title.replace("\xa0", " ").strip()

    published = None
    meta = s.find("meta", property="article:published_time")
    if meta and meta.get("content"):
        published = wp_datetime_local(meta["content"])
    if not published:
        published = f"{YEAR}-{month}-{day}T00:00:00"

    ec = s.select_one(".entry-content")
    prepare_content(ec)
    content_html = unwrap_soft_breaks(clean_html(ec))
    excerpt = make_excerpt(content_html)

    og = s.find("meta", property="og:image")
    featured = norm_url(og["content"]) if og and og.get("content") else ""

    cats: list[str] = []
    art = s.find("article")
    for c in art.get("class", []) if art else []:
        if c.startswith("category-"):
            slug_c = c[len("category-"):]
            if slug_c in DROP_CATEGORIES:
                continue
            cats.append(CATEGORY_NAMES.get(slug_c, slug_c.replace("-", " ").title()))
        elif c.startswith("tag-"):
            slug_t = c[len("tag-"):]
            cats.append(TAG_NAMES.get(slug_t, slug_t.replace("-", " ").title()))

    return {
        "date": published,
        "title": title,
        "slug": slug,
        "excerpt": excerpt,
        "content_html": content_html,
        "featured_image_url": featured,
        "lang": "es",
        "edition_year": YEAR,
        "categories": cats,
        "source_url": row["url"],
        "source_timestamp": row["timestamp"],
    }


# --------------------------------------------------------------------------
# events / speakers described in the posts (hand-mapped by slug, content and
# source pointers pulled from the parsed post so the output stays traceable)
# --------------------------------------------------------------------------

def _ev(post: dict, **kw) -> dict:
    base = {
        "edition_year": YEAR,
        "title": "",
        "kind": "other",
        "starts_at": None,
        "ends_at": None,
        "room": None,
        "modality": "in_person",
        "speaker": None,
        "company": None,
        "summary": None,
        "description_html": "",
        "poster_url": None,
        "link": None,
        "lang": "es",
        "source_url": post["source_url"],
        "source_timestamp": post["source_timestamp"],
    }
    base.update(kw)
    return base


def build_events(posts: dict[str, dict]) -> list[dict]:
    ev: list[dict] = []
    p = posts.get("informacion-sobre-la-gymkhana")
    if p:
        ev.append(_ev(p, title="Gymkhana", kind="competition",
                      starts_at="2022-11-10T15:30:00", room="Campus y ETSII",
                      summary="Pruebas repartidas por el campus y la facultad, sin inscripción previa; premios de La Estepeña para los seis primeros.",
                      description_html=p["content_html"], poster_url=p["featured_image_url"] or None))
    p = posts.get("its-a-me-innosoft-days-2022")
    if p:
        ev.append(_ev(p, title="Torneo de ajedrez", kind="competition",
                      summary="Torneo de ajedrez confirmado como evento social de la X edición; premios entregados en el acto de clausura.",
                      description_html=""))
    p = posts.get("importante-cambio-de-sala-del-evento-de-clausura")
    if p:
        ev.append(_ev(p, title="Torneo de Brawlhalla", kind="competition",
                      summary="Torneo de Brawlhalla; premios entregados en el acto de clausura.",
                      description_html=""))
        ev.append(_ev(p, title="Acto de clausura", kind="ceremony",
                      starts_at="2022-11-11", room="Salón de Actos (antes Salón de Grados)",
                      summary="Clausura de la X edición con entrega de premios de los torneos de Brawlhalla, ajedrez y la gymkhana. Entrada con QR escaneado en la puerta.",
                      description_html=p["content_html"]))
    p = posts.get("resumen-x-edicion-innosoft-days")
    if p:
        ev.append(_ev(p, title="Barrilada de clausura", kind="social",
                      starts_at="2022-11-11",
                      summary="Barrilada realizada tras el acto de clausura.",
                      description_html=""))
    p = posts.get("te-gustaria-estudiar-un-master-gratis")
    if p:
        ev.append(_ev(p, title="Sorteo de un máster", kind="stand",
                      summary="Sorteo de un máster entre alumnos de la Universidad de Sevilla que escaneen el QR del stand.",
                      description_html=p["content_html"], poster_url=p["featured_image_url"] or None))
    p = posts.get("software-libre-en-ntt-data")
    if p:
        ev.append(_ev(p, title="Software libre en NTT Data", kind="talk",
                      starts_at="2022-11-08", speaker="Jesús Alcaide Marín", company="NTT DATA",
                      summary="Herramientas de software libre (Trello, Keycloak, KIE, LibreOffice, Alfresco, WSO2 ESB, Docker) en los proyectos de NTT DATA, especialmente con la administración pública.",
                      description_html=p["content_html"]))
    p = posts.get("accenture-y-el-uso-de-software-libre-para-el-desarrollo-y-venta-de-servicios-asociados")
    if p:
        ev.append(_ev(p, title="Accenture y el uso de software libre para el desarrollo y venta de servicios asociados", kind="talk",
                      starts_at="2022-11-08", speaker="Rafael Poveda, Ángeles Sánchez, Rubén Ruíz", company="Accenture",
                      summary="Uso diario de software libre en Accenture (WordPress, Drupal, Moodle, Magento...), SAP y su escaparate Spartacus, y el programa de prácticas Dixcover.",
                      description_html=p["content_html"]))
    p = posts.get("resumen-opensuse")
    if p:
        ev.append(_ev(p, title="OpenSUSE", kind="talk",
                      speaker="Daniel García", company="OpenSUSE",
                      summary="Modelos de negocio basados en software libre, distribuciones GNU/Linux, gestión de dependencias y mantenimiento a largo plazo.",
                      description_html=p["content_html"]))
    p = posts.get("resumen-software-libre-en-la-sociedad-mas-libre")
    if p:
        ev.append(_ev(p, title="Software Libre en la sociedad más libre", kind="talk",
                      speaker="Fernando Fernández Mancera", company="Red Hat",
                      summary="Cómo afecta el software libre a la sociedad, las cuatro libertades y cómo contribuir para conseguir una sociedad más libre.",
                      description_html=p["content_html"]))
    return ev


def build_speakers(posts: dict[str, dict]) -> list[dict]:
    def sp(name, affiliation, position, bio, slug):
        p = posts.get(slug)
        return {
            "name": name,
            "affiliation": affiliation,
            "position": position,
            "bio_html": f"<p>{bio}</p>" if bio else "",
            "photo_url": None,
            "links": [],
            "edition_years": [YEAR],
            "source_url": p["source_url"] if p else None,
        }

    conf = "se-confirman-los-ponentes-principales-de-la-primera-charla-innosoft"
    out = [
        sp("María del Carmen Romero Ternero", "Universidad de Sevilla", "Directora de la ETSII",
           "Directora de la Escuela Técnica Superior de Ingeniería Informática, confirmada como ponente de la X edición.", conf),
        sp("María José Escalona Cuaresma", "Universidad de Sevilla", "Profesora",
           "Profesora de la Universidad de Sevilla, confirmada como ponente de la X edición.", conf),
        sp("Clara Isabel Grima Ruiz", "Universidad de Sevilla", "Profesora",
           "Profesora de la Universidad de Sevilla y una de las divulgadoras matemáticas más influyentes del panorama nacional, ponente de la X edición.", conf),
        sp("María Teresa Gómez López", "Universidad de Sevilla", "Profesora",
           "Profesora de la Universidad de Sevilla, confirmada como ponente de la X edición.", conf),
        sp("Jesús Lagares Galán", None, "Ingeniero informático",
           "Ingeniero informático, confirmado como ponente de la X edición.", conf),
        sp("Manuel Jesús Flores Montaño", None, "Ingeniero informático",
           "Ingeniero informático, confirmado como ponente de la X edición.", conf),
        sp("Jesús Alcaide Marín", "NTT DATA", None,
           "Graduado en ingeniería informática por la Universidad de Cádiz, con más de 20 años en NTT DATA. Ponencia «Software libre en NTT Data» (8 de noviembre de 2022).",
           "software-libre-en-ntt-data"),
        sp("Rafael Poveda", "Accenture", "Consultor senior",
           "Consultor senior de Accenture, anteriormente en WordPress Foundation y Drupal Association. Ponencia sobre el uso de software libre en Accenture (8 de noviembre de 2022).",
           "accenture-y-el-uso-de-software-libre-para-el-desarrollo-y-venta-de-servicios-asociados"),
        sp("Ángeles Sánchez", "Accenture", "Cazadora de talentos",
           "Cazadora de talentos en Accenture; presentó el programa de prácticas Dixcover (8 de noviembre de 2022).",
           "accenture-y-el-uso-de-software-libre-para-el-desarrollo-y-venta-de-servicios-asociados"),
        sp("Rubén Ruíz", "Accenture", "Mánager de desarrollo empresarial",
           "Mánager de desarrollo empresarial en Accenture; habló sobre SAP y su escaparate Spartacus (8 de noviembre de 2022).",
           "accenture-y-el-uso-de-software-libre-para-el-desarrollo-y-venta-de-servicios-asociados"),
        sp("Daniel García", "OpenSUSE", None,
           "Antiguo miembro de Wadobo, startup de soluciones con tecnologías de código abierto. Ponencia sobre OpenSUSE en la X edición.",
           "resumen-opensuse"),
        sp("Fernando Fernández Mancera", "Red Hat", "Senior Software Engineer",
           "Senior Software Engineer en Red Hat y miembro de SUGUS (asociación universitaria y grupo de usuarios de software libre de la Universidad de Sevilla). Ponencia «Software Libre en la sociedad más libre».",
           "resumen-software-libre-en-la-sociedad-mas-libre"),
    ]
    return [s for s in out if s["source_url"]]


def build_edition(posts: dict[str, dict]) -> dict:
    intro = posts.get("its-a-me-innosoft-days-2022")
    resumen = posts.get("resumen-x-edicion-innosoft-days")
    parts = []
    if intro:
        parts.append(intro["content_html"])
    if resumen:
        parts.append(resumen["content_html"])
    sources = [p["source_url"] for p in (intro, resumen) if p]
    for slug in ("informacion-sobre-la-gymkhana", "importante-cambio-de-sala-del-evento-de-clausura",
                 "se-confirman-los-ponentes-principales-de-la-primera-charla-innosoft"):
        if slug in posts:
            sources.append(posts[slug]["source_url"])
    n = edition_number_for_year(YEAR)
    return {
        "year": YEAR,
        "number": n,
        "roman": roman(n),
        "name": f"InnoSoft Days {roman(n)}",
        "starts_on": "2022-11-08",
        "ends_on": "2022-11-11",
        "venue": VENUE,
        "summary": ("Décima edición, del martes 8 al viernes 11 de noviembre de 2022, de vuelta a la presencialidad. "
                    "Ponencias sobre software libre (Red Hat, NTT DATA, Accenture, OpenSUSE, Guadaltel, PRiSE, Copyright Clearance Center, "
                    "Oficina de Software Libre, SUGUS, Metadev, Tenea, Pandora FMS...), foco en sostenibilidad e igualdad, mascota Ping-u, "
                    "juegos diarios en la web, gymkhana, torneos de ajedrez y Brawlhalla, sorteo de un máster y barrilada tras la clausura."),
        "description_html": "\n".join(parts),
        "registration_url": None,
        "sources": sources,
        "confidence": "medium",
        "notes": ("Dates from the intro post (8, 10 and 11 November announced) and the wrap-up post (Tuesday 8 to Friday 11, four days). "
                  "Venue inferred from Salón de Actos / Salón de Grados and campus references; not stated verbatim in the posts. "
                  "The talk timetable itself lived on /ponentes-x-edicion/, not in these posts."),
    }


# --------------------------------------------------------------------------
# media referenced from the posts
# --------------------------------------------------------------------------

def build_media(post_list: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for p in post_list:
        soup = BeautifulSoup(p["content_html"], "lxml")
        refs: list[tuple[str, str]] = []
        for img in soup.find_all("img"):
            refs.append((norm_url(img.get("src")), "img"))
        for a in soup.find_all("a"):
            href = norm_url(a.get("href"))
            if "/wp-content/uploads/" in href:
                refs.append((href, "file"))
        for url, how in refs:
            if not url:
                continue
            fname = url.rsplit("/", 1)[-1].lower()
            if how == "file" and fname.endswith(".pdf"):
                kind = "other"
            elif fname.startswith("dsc"):
                kind = "photo"
            else:
                kind = "poster"
            item = seen.setdefault(url, {
                "url": url, "kind": kind, "edition_year": YEAR,
                "caption": p["title"], "used_by": [],
            })
            if p["source_url"] not in item["used_by"]:
                item["used_by"].append(p["source_url"])
    return list(seen.values())


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> None:
    rows = scope_rows()
    latest = latest_per_url(rows)
    versions = defaultdict(list)
    for r in rows:
        versions[r["url"]].append(r["timestamp"])

    post_list = [post_from_row(latest[u]) for u in sorted(latest)]
    post_list.sort(key=lambda p: (p["date"], p["slug"]))
    posts = {p["slug"]: p for p in post_list}

    events = build_events(posts)
    speakers = build_speakers(posts)
    edition = build_edition(posts)
    media = build_media(post_list)

    dump_part(f"{FAMILY}.posts.json", post_list)
    dump_part(f"{FAMILY}.events.json", events)
    dump_part(f"{FAMILY}.speakers.json", speakers)
    dump_part(f"{FAMILY}.editions.json", [edition])
    dump_part(f"{FAMILY}.media.json", media)

    # ---- notes -------------------------------------------------------------
    skipped_versions = sum(len(v) - 1 for v in versions.values())
    n_clippings = sum(1 for p in post_list if p["categories"] == ["Igualdad"])
    lines = [
        f"# {FAMILY} notes",
        "",
        "Scope: manifest kind=post with permalink `/2022/MM/DD/slug/` (InnoSoft Days X, 8 to 11 November 2022).",
        f"Captures in scope: {len(rows)} ({len(latest)} distinct URLs). Every 2022 post URL present in data/index.jsonl was fetched.",
        f"Extracted: {len(latest)} posts (latest capture per URL). Older captures skipped: {skipped_versions} "
        "(same URL, entry-content text identical to the latest one; verified programmatically).",
        "",
        "## Outputs",
        f"- posts: {len(post_list)}",
        f"- events: {len(events)}",
        f"- speakers: {len(speakers)}",
        f"- editions: 1 (2022)",
        f"- media: {len(media)}",
        "",
        "## Per-month counts (posts)",
    ]
    by_month = Counter(p["date"][:7] for p in post_list)
    for k in sorted(by_month):
        lines.append(f"- {k}: {by_month[k]}")
    lines += [
        "",
        "## Skipped captures (older versions of a URL, content identical to the version used)",
    ]
    for u in sorted(versions):
        ts = sorted(versions[u])
        if len(ts) > 1:
            lines.append(f"- {u}: used {ts[-1]}, skipped {', '.join(ts[:-1])}")
    lines += [
        "",
        "## How fields were filled",
        "- date: `article:published_time` (UTC) converted to naive Europe/Madrid; matches the visible dd/mm/yyyy of every post.",
        "- content_html: `.entry-content` after un-lazying images (data-src -> src, `<noscript>` twins dropped) and collapsing "
        "`wp-block-file` (PDF embed + title link + Descarga button) into one paragraph linking the PDF by its title; then clean_html().",
        "- excerpt: WordPress-style automatic excerpt, first 55 words of the cleaned text (see below).",
        "- featured_image_url: `og:image` (WordPress falls back to the first content image; the posts have no real featured image). "
        f"Empty for the {sum(1 for p in post_list if not p['featured_image_url'])} posts without images.",
        "- categories: WordPress category classes on `<article>` (`Noticias`), plus the tag `Igualdad`; the default `Sin categoría` was dropped "
        f"(the {n_clippings} news-clipping posts are only tagged Igualdad, so that tag is what identifies them).",
        "- lang: es for every post (site language es-ES).",
        "",
        "## Events",
        "Only what the posts themselves state. `starts_at` is a full datetime when the post gives a time (gymkhana, 10/11 15:30), "
        "a date-only ISO string when only the day is known (NTT DATA and Accenture talks were 'this Tuesday' morning = 2022-11-08; "
        "closing ceremony and barrilada on 2022-11-11), and null otherwise (chess and Brawlhalla tournaments, OpenSUSE and Red Hat talks, master raffle stand). "
        "The talk timetable of the edition lived on /ponentes-x-edicion/ (family of the event pages), so times for talks should come from there. "
        "Talk description_html is the summary post written by the organisation after the talk.",
        "Not turned into events: the daily web games (Ahorcado, Wordle, crucigramas, post 'Sabías que'), the sustainability publication "
        f"'Linux Server vs Windows Server' (a student write-up with PDF, not an activity), and the {n_clippings} equality news clippings.",
        "",
        "## Speakers",
        "Six people confirmed in the 27/10 announcement (ETSII director, three professors, two engineers; no talk titles given) plus the "
        "six speakers named in the four talk summaries. Padmini Gopalakrishnan appears only as the subject of a news clipping, not a speaker.",
        "",
        "## Excerpt / soft breaks",
        "- excerpt: WordPress-style automatic excerpt (first 55 words of the cleaned text, ellipsis when cut); the SEO meta description "
        "was not used because on the PDF posts it glued the title to the 'Descarga' button label.",
        "- 'primera-publicacion-de-sostenibilidad' was pasted from a PDF with a `<br/>` at every wrapped line; breaks that split a "
        "sentence (word before, lowercase after) were joined into a space, the rest kept.",
        "",
        "## Oddities",
        f"- {n_clippings} posts dated 6 and 8 November are bare PDF embeds (`wp-block-file`, tag Igualdad, category Sin categoría): equality-themed press "
        "clippings; content_html is a single link to the PDF and excerpt equals the title.",
        "- 'primera-publicacion-de-sostenibilidad' has H1 '[RESUMEN] >>LINUX SERVER VS WINDOWS SERVER' (slug and title differ).",
        "- The 27/10 announcement lists Guadaltel twice; kept verbatim in the post, mentioned once in the edition summary.",
        "- The 2024 and 2025 captures of the same post differ only in the WordPress generator version and Wayback chrome.",
        "- Post images are the 1024px WordPress renditions referenced by the page (kept verbatim so the importer can resolve them).",
        "- No organisers or standalone pages in this family.",
    ]
    (Path(__file__).resolve().parent.parent / "data" / "extracted" / "parts" / f"{FAMILY}.notes.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"{FAMILY}: {len(post_list)} posts, {len(events)} events, {len(speakers)} speakers, {len(media)} media; "
          f"{len(rows)} captures in scope, {skipped_versions} older versions skipped")


if __name__ == "__main__":
    main()
