"""Family pages_editions: the site pages that describe the event itself.

Scope (kind=page in the manifest, plus /es/eventos and /en/events which the
survey classed as event-index): every capture version of the home page "/"
(2022 X edition, 2023 XI, 2024 XII, 2025 placeholder), the roman-numeral
edition archive pages (/v-edicion/ .. /xi-edicion/ with their embedded MEC
calendars, /programa-x-edicion/), the 2025 Blocksy site (/es/inicio,
/about-us, /es/sobre-nosotros, /es/cronograma, /schedule, /es/eventos,
/es/fotos, /fotos-2, /photos, /es/cuestionario), the Astra site pages
(/como-llegar, /en/find-us, /acceso-online-innosoft-days,
/encuestas-de-satisfaccion, sustainability and equality pages, TDAH pages,
games: crosswords / wordle / hangman / guess-the-logo / CTF, the 2022
"Información sobre la ponencia" poster pages), the WordPress attachment pages
of the 2025 Twenty Twenty-Five interim site, The Events Calendar category
listings (/events/categoria/*) and the `?method=ical&id=N` MEC iCal exports.

Cross-family rule: an event (or speaker) that another family already
extracted is NOT emitted again here. The other families' parts
(data/extracted/parts/<family>.events.json / .speakers.json) are read at run
time; a match is the same title (loose key, "Conferencia –" / "Taller –"
prefixes ignored, or the same word set) on the same date, or the same event
URL / slug. When those files are missing everything is emitted and the notes
say so.

Deliberately NOT handled here (listed as skipped with the family that covers
them): institucional.us.es captures (institucional family), organisation
pages (people family), Eventin / MEC taxonomy archives (events_eventos_etn),
forms / accounts / forum / legal pages.

Outputs data/extracted/parts/pages_editions.{editions,events,speakers,pages,
media}.json and pages_editions.notes.md. Deterministic, no network.
"""

from __future__ import annotations

import hashlib
import html as html_mod
import json
import re
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from bs4 import BeautifulSoup  # noqa: E402

from parse.common import (  # noqa: E402
    EXTRACTED, best_srcset_url, clean_html, dump_part, elementor_normalise, fix_lazy_images,
    manifest_rows, name_key, name_phrase_in_text, norm_key, norm_url,
    parse_time, read_html_any, roman, same_person, soup_any, text_of,
    tidy_html,
)

FAMILY = "pages_editions"
SITE = "https://www.innosoftdays.com"

# ----------------------------------------------------------------------------
# capture selection
# ----------------------------------------------------------------------------

EXTRA_URLS = {SITE + "/es/eventos/", SITE + "/en/events/"}  # event-index kind, listed in scope

SKIP_RULES = [
    # (regex on url path+query, reason)
    (r"^/(acceder|registrar|registrar-2|carrito|mi-cuenta|password-reset)/", "login / registration / cart / account page (no event content)"),
    (r"^/usuario/", "user profile page (excluded by scope)"),
    (r"^/forums/", "forum (excluded by scope)"),
    (r"^/topics/", "bbPress topics archive full of spam threads (no event content)"),
    (r"^/(contactar|en/contact-us|envia-tu-duda-a-nuestro-equipo|newsletter|miembros)/", "contact / newsletter / members form page (no event content)"),
    (r"^/politica-de-cookies/", "legal page"),
    (r"^/(events-tab-pro|related-event-widget-pro-2)/", "empty plugin demo page"),
    (r"^/etn_category/[a-z]", "Eventin category listing (Yincana, Pensamiento Computacional, tournaments...): covered by the events_eventos_etn family, which uses it for its listing-only stubs"),
    (r"^/etn_category-\d+/", "empty Eventin category archive ('Etn Category', no events): listed by the events_eventos_etn family"),
    (r"^/mec-category/", "MEC year archive rendered empty by the theme ('¡No hay eventos!'): listed by the events_eventos_etn family; the events themselves are single event captures (events_mec)"),
    (r"^/en/tickets-store/", "Eventin ticket store shell (\"Discover 55 Upcoming and Expire Events\", no rows rendered); used only as the 2024 registration_url"),
    (r"^/organizacion-.*-edicion/|^/en/xii-edition-organization/", "organisation (committee members) page: covered by the people family (organisers.json)"),
    (r"^/informacion-sobre-la-ponencia-.*/embed/$", "WordPress oEmbed rendering of a talk page (only a title card)"),
    (r"^/programa-2/$", "empty page: the entry-content of both captures is empty (title 'Programa', no blocks)"),
    (r"^/planes-xi-edicion/$", "placeholder page: its only content is 'Aquí se mostrará los diferentes planes de los comités de las jornadas 2023' (no plans published)"),
]

INSTITUCIONAL_SKIP = "institucional.us.es capture: covered by the institucional family (parse/institucional.py: 2018 programme, 2019 home, 2021 MEC calendar)"

ARCHIVE_PAGES = OrderedDict([
    ("/v-edicion/", 2017), ("/vi-edicion/", 2018), ("/vii-edicion/", 2019), ("/viii-edicion/", 2020),
    ("/ix-edicion/", 2021), ("/x-edicion/", 2022), ("/xi-edicion/", 2023),
])
ORDINALS = {2017: "Quinta edición (V)", 2018: "Sexta edición (VI)", 2019: "Séptima edición (VII)", 2020: "Octava edición (VIII)",
            2021: "Novena edición (IX)", 2022: "Décima edición (X)", 2023: "Undécima edición (XI)", 2024: "Duodécima edición (XII)", 2025: "Decimotercera edición (XIII)"}
ETSII = "Escuela Técnica Superior de Ingeniería Informática (ETSII), Universidad de Sevilla"
WEEKDAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS_ES_NAMES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def path_of(url: str) -> str:
    return url.replace(SITE, "", 1) if url.startswith(SITE) else url


def content_hash(soup: BeautifulSoup) -> str:
    node = soup.select_one(".entry-content") or soup.select_one("#content") or soup.find("main") or soup.body
    return hashlib.md5(text_of(node).encode("utf-8")).hexdigest()[:10] if node is not None else "-"


def esc(s: str) -> str:
    return html_mod.escape(s or "", quote=False)


# ----------------------------------------------------------------------------
# captured uploads and cross-family index
# ----------------------------------------------------------------------------

ALL_ROWS = manifest_rows()
CAPTURED = {r["url"] for r in ALL_ROWS if r["kind"] in ("upload", "file")}


def full_size(url: str) -> str:
    """Strip the WordPress -WxH size suffix (keeps -scaled)."""
    return re.sub(r"-\d{2,4}x\d{2,4}(?=\.\w{3,4}$)", "", url)


def pick_url(url: str) -> str:
    """The URL the importer can resolve: the full-size upload when the archive
    captured it, else the URL as the page referenced it (largest srcset
    candidate, already resolved by fix_lazy_images); never a synthesised URL
    that no capture references."""
    url = norm_url(url)
    if not url:
        return url
    full = full_size(url)
    if full in CAPTURED:
        return full
    return url


def image_base(url: str) -> str:
    """Same image regardless of -WxH / -scaled suffixes and host scheme."""
    return re.sub(r"-scaled(?=\.\w{3,4}$)", "", full_size(norm_url(url)))


def upgrade_srcset(node) -> None:
    """In place: a non-lazy <img> whose srcset lists a larger variant of the
    same image gets that (referenced) URL as src, like the lazy ones do."""
    for img in node.find_all("img"):
        src = img.get("src") or ""
        best = best_srcset_url(img.get("srcset") or img.get("data-srcset"))
        if src and not src.startswith("data:") and best and "innosoftdays" in best and image_base(best) == image_base(src):
            img["src"] = best


def sync_media_urls(html: str) -> str:
    if not html:
        return html
    return re.sub(r'(<img[^>]*?\ssrc=")([^"]+)(")', lambda m: m.group(1) + pick_url(m.group(2)) + m.group(3), html)


def ev_key(title: str) -> str:
    k = norm_key(title)
    k = re.sub(r"^(conferencia|taller|charla|proyeccion|mesa redonda|competicion)\s+", "", k)
    return k


def slug_of(url: str | None) -> str:
    if not url:
        return ""
    s = urlparse(url).path.rstrip("/").split("/")[-1]
    return re.sub(r"-\d+$", "", s)


class Others:
    """Events and speakers already extracted by the other families."""

    def __init__(self) -> None:
        self.loaded: list[str] = []
        self.by_key: dict[tuple, list] = defaultdict(list)
        self.by_tokens: dict[tuple, list] = defaultdict(list)
        self.urls: dict[str, str] = {}
        self.slugs: dict[str, str] = {}
        self.speakers: list[tuple[str, str]] = []
        parts = EXTRACTED / "parts"
        if not parts.exists():
            return
        for f in sorted(parts.glob("*.events.json")):
            fam = f.name.split(".")[0]
            if fam == FAMILY:
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            self.loaded.append(fam)
            for e in data:
                t = e.get("title") or ""
                d = (e.get("starts_at") or "")[:10]
                self.by_key[(ev_key(t), d)].append((fam, t))
                self.by_tokens[(tuple(sorted(set(ev_key(t).split()))), d)].append((fam, t))
                for u in (e.get("source_url"), e.get("link")):
                    u = norm_url(u)
                    if u and "innosoftdays" in u and re.search(r"/(events?|eventos)/[^/]+/$", u):
                        self.urls.setdefault(u, f"{fam}: {t}")
                        self.slugs.setdefault(slug_of(u), f"{fam}: {t}")
        for f in sorted(parts.glob("*.speakers.json")):
            fam = f.name.split(".")[0]
            if fam == FAMILY:
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            for s in data:
                if s.get("name"):
                    self.speakers.append((fam, s["name"]))

    def event_match(self, title: str, date: str | None, url: str | None = None) -> str | None:
        d = (date or "")[:10]
        hit = self.by_key.get((ev_key(title), d)) or self.by_tokens.get((tuple(sorted(set(ev_key(title).split()))), d))
        if hit:
            return ", ".join(sorted({f"{fam}: {t}" for fam, t in hit}))
        u = norm_url(url) if url else ""
        if u and u in self.urls:
            return self.urls[u]
        if u and slug_of(u) in self.slugs:
            return self.slugs[slug_of(u)]
        return None

    def speaker_match(self, name: str) -> str | None:
        for fam, n in self.speakers:
            if name_key(n) == name_key(name) or same_person(n, name):
                return f"{fam}: {n}"
        return None


OTHERS = Others()

# ----------------------------------------------------------------------------
# generic helpers
# ----------------------------------------------------------------------------

def page_meta(soup: BeautifulSoup) -> dict:
    """Yoast graph dates + og:image + <title> + canonical."""
    out = {"published": None, "modified": None, "og_image": None, "title": None, "canonical": None}
    if soup.title and soup.title.string:
        out["title"] = re.sub(r"\s*[-–]\s*InnoSoft Days\s*$", "", soup.title.string.strip())
    c = soup.find("link", rel="canonical")
    if c is not None and c.get("href"):
        out["canonical"] = norm_url(c["href"])
    for m in soup.find_all("meta"):
        if m.get("property") == "og:image" and not out["og_image"]:
            out["og_image"] = norm_url(m.get("content"))
        if m.get("property") == "article:modified_time":
            out["modified"] = out["modified"] or m.get("content")
        if m.get("property") == "article:published_time":
            out["published"] = out["published"] or m.get("content")
    for ld in soup.find_all("script", type="application/ld+json"):
        try:
            g = json.loads(ld.string or "")
        except (ValueError, TypeError):
            continue
        for n in g.get("@graph", []) if isinstance(g, dict) else []:
            t = n.get("@type")
            t = t if isinstance(t, list) else [t]
            if "WebPage" in t or "Article" in t or "CollectionPage" in t:
                out["published"] = out["published"] or n.get("datePublished")
                out["modified"] = out["modified"] or n.get("dateModified")
    return out


def year_of(iso: str | None) -> int | None:
    return int(iso[:4]) if iso and re.match(r"\d{4}", iso) else None


def content_node(soup: BeautifulSoup):
    return soup.select_one(".entry-content") or soup.select_one("#primary #content") or soup.select_one("#content") or soup.find("main")


DROP_SELECTORS = [
    ".container-countdown", ".countdown", "ul.wp-block-social-links", ".wp-block-social-links",
    ".wp-block-post-title", ".page-title-new", ".ast-breadcrumbs", ".sharedaddy",
    ".wp-block-buttons", ".modula-grid-sizer", ".elementor-widget-nav-menu",
    ".wp-block-cover__image-background", ".wp-block-cover__background",
]


def clean_node(node, drop_selectors=DROP_SELECTORS, elementor=False, lang="es") -> str:
    if node is None:
        return ""
    node = BeautifulSoup(str(node), "lxml")
    for sel in drop_selectors:
        for t in node.select(sel):
            t.decompose()
    for v in node.find_all("video"):
        src = v.get("src") or (v.find("source").get("src") if v.find("source") else None)
        p = node.new_tag("p")
        if src:
            a = node.new_tag("a", href=norm_url(src))
            a.string = "Presentation video" if lang == "en" else "Vídeo de presentación"
            p.append(a)
        fig = v.find_parent("figure")
        (fig if fig is not None else v).replace_with(p)
    for ifr in list(node.find_all("iframe")):
        src = ifr.get("src") or ""
        if "facebook.com/plugins/post.php" in src:
            href = parse_qs(urlparse(src).query).get("href", [""])[0]
            p = node.new_tag("p")
            a = node.new_tag("a", href=unquote(href) or src)
            a.string = "Facebook post" if lang == "en" else "Publicación en Facebook"
            p.append(a)
            ifr.replace_with(p)
            continue
        ifr.clear()  # the "Your browser does not support iframes" boilerplate (escaped several times by WordPress)
    if elementor:
        elementor_normalise(node)
    upgrade_srcset(node)
    fix_lazy_images(node)
    # modula galleries: the <a> around the image has no href (lazy), keep only the img
    for a in node.select("a.modula-item-link"):
        a.unwrap()
    # headings that only wrap an iframe / image become paragraphs; headings inside list items are unwrapped
    for h in list(node.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])):
        if h.find_parent("li") is not None:
            h.unwrap()
        elif h.find(["iframe", "img"]) is not None and not h.get_text(strip=True):
            h.name = "p"
    marker = ""
    if node.find("iframe") is not None and node.body is not None:
        # clean_html() returns "" for text-less fragments; an iframe-only page (crossword) must survive
        m = node.new_tag("p")
        m.string = "__IFRAME_MARK__"
        node.body.append(m)
        marker = "<p>__IFRAME_MARK__</p>"
    html = tidy_html(clean_html(node))
    if marker:
        html = html.replace(marker, "").strip()
    return sync_media_urls(html)


def img_urls(node) -> list[str]:
    """Real image URLs of a node in document order (lazy-load aware), largest
    variant, deduplicated, original-site URLs only."""
    node = BeautifulSoup(str(node), "lxml")
    upgrade_srcset(node)
    fix_lazy_images(node)
    seen, out = set(), []
    for img in node.find_all("img"):
        u = norm_url(img.get("src") or "")
        if not u or u.startswith("data:") or "innosoftdays" not in u and "institucional.us.es" not in u:
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def spanish_date_label(ymd: str) -> str:
    """'20171106' / '2017-11-06' -> 'lunes 6 de noviembre de 2017'."""
    d = ymd.replace("-", "")
    dt = datetime(int(d[:4]), int(d[4:6]), int(d[6:8]))
    return f"{WEEKDAYS_ES[dt.weekday()]} {dt.day} de {MONTHS_ES_NAMES[dt.month - 1]} de {dt.year}"


def days_in_text(text: str) -> tuple[str | None, str | None, str | None]:
    """'los días 6 y 9 de noviembre de 2017' / 'del 6 al 9 de noviembre de 2023'
    -> (starts_on, ends_on, matched phrase)."""
    dm = re.search(r"d[ií]as\s+([\d][\d,\sy]*?)\s+de\s+noviembre\s+de\s+(\d{4})", text)
    if dm:
        days = [int(x) for x in re.findall(r"\d{1,2}", dm.group(1))]
        y = int(dm.group(2))
        return f"{y}-11-{min(days):02d}", f"{y}-11-{max(days):02d}", dm.group(0)
    rm = re.search(r"del\s+(\d{1,2})\s+al\s+(\d{1,2})\s+de\s+noviembre\s+de\s+(\d{4})", text)
    if rm:
        y = int(rm.group(3))
        return f"{y}-11-{int(rm.group(1)):02d}", f"{y}-11-{int(rm.group(2)):02d}", rm.group(0)
    return None, None, None


# ----------------------------------------------------------------------------
# state
# ----------------------------------------------------------------------------

editions: dict[int, dict] = {}
events: list[dict] = []
speakers: list[dict] = []
pages: list[dict] = []
media: "OrderedDict[str, dict]" = OrderedDict()
notes_used: list[str] = []      # "url ts -> what"
notes_skipped: list[str] = []   # "url ts -> reason"
oddities: list[str] = []
covered_events: list[str] = []  # events seen here but already extracted elsewhere
dropped_speakers: list[str] = []


def add_media(url: str, kind: str, year: int | None, caption: str, used_by: str) -> None:
    url = pick_url(url)
    if not url:
        return
    m = media.get(url)
    if m is None:
        media[url] = {"url": url, "kind": kind, "edition_year": year, "caption": caption, "used_by": [used_by]}
    else:
        if used_by not in m["used_by"]:
            m["used_by"].append(used_by)
        if not m["caption"] and caption:
            m["caption"] = caption


def add_edition(year: int, **kw) -> dict:
    e = editions.setdefault(year, {
        "year": year, "number": year - 2012, "roman": roman(year - 2012),
        "name": f"InnoSoft Days {roman(year - 2012)}",
        "starts_on": None, "ends_on": None, "venue": None, "summary": None,
        "description_html": "", "registration_url": None, "sources": [],
        "confidence": "medium", "notes": "", "_conf_set": None,
    })
    for k, v in kw.items():
        if k == "sources":
            for s in v:
                if s not in e["sources"]:
                    e["sources"].append(s)
        elif k == "notes":
            e["notes"] = (e["notes"] + " " + v).strip() if e["notes"] else v
        elif k == "confidence":
            rank = {"low": 0, "medium": 1, "high": 2}
            if e.get("_conf_set") is None or rank[v] > rank[e["confidence"]]:
                e["confidence"] = v
                e["_conf_set"] = True
        elif v is not None and (e.get(k) in (None, "") or k in ("description_html", "summary")):
            if k == "description_html" and e["description_html"]:
                e["description_html"] = e["description_html"] + "\n" + v
            else:
                e[k] = v
    return e


def used(row: dict, what: str) -> None:
    notes_used.append(f"{row['url']} @{row['timestamp']}: {what}")


def skipped(row: dict, why: str) -> None:
    notes_skipped.append(f"{row['url']} @{row['timestamp']}: {why}")


def add_event(**kw) -> dict:
    e = {
        "edition_year": None, "title": None, "kind": "other", "starts_at": None, "ends_at": None,
        "room": None, "modality": "in_person", "speaker": None, "company": None, "summary": None,
        "description_html": "", "poster_url": None, "link": None, "lang": "es",
        "source_url": None, "source_timestamp": None,
    }
    e.update(kw)
    events.append(e)
    return e


def find_event(title: str, date: str | None) -> dict | None:
    d = (date or "")[:10]
    for e in events:
        if ev_key(e["title"] or "") == ev_key(title) and (e["starts_at"] or "")[:10] == d:
            return e
    return None


def add_speaker(name: str, year: int, source_url: str, affiliation=None, position=None, bio_html="", photo_url=None, links=None) -> None:
    name = SPEAKER_ALIASES.get(norm_key(name), name)
    key = norm_key(name)
    for s in speakers:
        if norm_key(s["name"]) == key:
            if year not in s["edition_years"]:
                s["edition_years"].append(year)
            if not s["affiliation"] and affiliation:
                s["affiliation"] = affiliation
            if not s["position"] and position:
                s["position"] = position
            if not s["bio_html"] and bio_html:
                s["bio_html"] = bio_html
            for l in links or []:
                if l not in s["links"]:
                    s["links"].append(l)
            return
    speakers.append({"name": name, "affiliation": affiliation, "position": position, "bio_html": bio_html or "",
                     "photo_url": photo_url, "links": links or [], "edition_years": [year], "source_url": source_url})


def event_kind(title: str) -> str:
    k = norm_key(title)
    if k.startswith("taller") or " taller " in f" {k} ":
        return "workshop"
    if re.search(r"\b(inauguracion|clausura|apertura|ceremonia|bienvenido|presentacion del dia)\b", k):
        return "ceremony"
    if re.search(r"\b(sorteo|barrilada|musica|grupo|quedada|networking)\b", k):
        return "social"
    if re.search(r"\b(torneo|ajedrez|brawlhalla|gymkhana|gymkana|yincana|ctf|hackaton|escape room|scape room|competicion)\b", k):
        return "competition"
    if k.startswith("stand"):
        return "stand"
    if k.startswith("proyeccion"):
        return "social"
    return "talk"


# ----------------------------------------------------------------------------
# home page versions
# ----------------------------------------------------------------------------

def handle_home(rows: list[dict]) -> None:
    """Every version of / describes the edition current at capture time."""
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        s = soup_any(r)
        node = content_node(s)
        h = content_hash(s)
        groups[h].append((r, s, node))
    for h, items in sorted(groups.items(), key=lambda kv: kv[1][0][0]["timestamp"]):
        items.sort(key=lambda t: t[0]["timestamp"])
        r, s, node = items[-1]  # latest of identical versions
        text = text_of(node)
        others = [x[0] for x in items[:-1]]
        if not text or "Widget de ejemplo" in text:
            for rr, _, _ in items:
                skipped(rr, "home page with only the ColorMag placeholder sidebar widget (empty content)")
            continue
        if "Disponible próximamente" in text:
            for rr, _, _ in items:
                skipped(rr, "2025 interim Twenty Twenty-Five home: only \"Disponible próximamente en el curso 2025/26\"")
            continue
        m = re.search(r"edición\s+([IVX]+)", text)
        num = None
        if m:
            num = {"X": 10, "XI": 11, "XII": 12, "XIII": 13}.get(m.group(1))
        year = 2012 + num if num else None
        if not year:
            for rr, _, _ in items:
                skipped(rr, "home version without an edition number in the copy")
            continue
        html = clean_node(node)
        starts, ends, when = days_in_text(text)
        tm = re.search(r"tem[aá]tica(?: de este año)?(?: es| el| la)?\s+(?:la |el )?([^.]+)\.", text, re.I)
        theme = tm.group(1).strip() if tm else None
        theme = theme[0].upper() + theme[1:] if theme else None
        venue = ETSII if "ETSII" in text or "Ingeniería Informática" in text else None
        ordinal = ORDINALS.get(year, f"Edición {roman(year-2012)}")
        summary = f"{ordinal} de las jornadas InnoSoft Days, {when or 'noviembre de ' + str(year)} en la Escuela Técnica Superior de Ingeniería Informática (ETSII) de la Universidad de Sevilla."
        add_edition(year, starts_on=starts, ends_on=ends, venue=venue, summary=summary or None,
                    description_html=html, sources=[r["url"]], confidence="high",
                    notes=f"Home page copy of {year} (capture {r['timestamp']}" + (", identical versions " + ", ".join(x["timestamp"] for x in others) if others else "") + ").")
        if theme:
            editions[year]["notes"] += f" Theme stated on the home page: {theme}."
            editions[year]["summary"] = (editions[year]["summary"] or "") + f" Temática: {theme.lower() if theme.split()[0].istitle() and theme.split()[0].lower() != 'ia' else theme}."
        for u in img_urls(node):
            fs = full_size(u)
            if year == 2022:
                cap = "Horario de las jornadas X edición" if "horario" in u else "Cartel de las jornadas X edición"
            elif year == 2023:
                cap = "Cartel de las jornadas XI edición"
            else:
                cap = POSTER_CAPTIONS.get(Path(fs).name, "Cartel " + Path(fs).stem.replace("-", " "))
            add_media(u, "poster", year, cap, r["url"])
        used(r, f"home copy of edition {roman(year-2012)} ({year}) -> editions + poster media")
        for rr in others:
            used(rr, f"same content as {r['timestamp']} (edition {year}); covered")
        # side widgets of the 2022 ColorMag home: mascot / poster image in the sidebar
        if year == 2022:
            side = s.select_one("#secondary")
            if side is not None:
                for u in img_urls(side):
                    add_media(u, "logo", 2022, "Logotipo InnoSoft Days (barra lateral de la portada 2022)", r["url"])


# ----------------------------------------------------------------------------
# edition archive pages (/v-edicion/ .. /xi-edicion/, /programa-x-edicion/)
# ----------------------------------------------------------------------------

def parse_mec_calendar(wrap) -> list[dict]:
    """Events rendered by an embedded MEC calendar (daily or monthly skin):
    date (from the day container id / data-mec-cell), time, title, room,
    event URL and organizer/location from the JSON-LD blocks (matched by URL
    or by name because the plugin misplaces the <script> tags)."""
    ld: dict[str, dict] = {}
    for sc in wrap.find_all("script", type="application/ld+json"):
        try:
            g = json.loads(sc.string or "")
        except (ValueError, TypeError):
            continue
        if not isinstance(g, dict):
            continue
        name = html_mod.unescape(g.get("name") or "")
        rec = {"organizer": (g.get("organizer") or {}).get("name") or None,
               "location": (g.get("location") or {}).get("name") or None,
               "url": norm_url(g.get("url") or ""), "start": g.get("startDate")}
        if rec["url"]:
            ld["url:" + rec["url"]] = rec
        ld.setdefault("name:" + norm_key(name), rec)
    out: list[dict] = []
    seen = set()
    for t in wrap.select(".mec-event-title"):
        art = t.find_parent("article")
        if art is None:
            continue
        date = None
        for p in art.parents:
            pid = p.get("id") or ""
            m = re.search(r"_(\d{8})$", pid)
            if m:
                date = m.group(1)
                break
            if p.get("data-mec-cell"):
                date = p.get("data-mec-cell")
                break
        tm = art.find("div", class_="mec-event-time", recursive=False)
        st, en = parse_time(text_of(tm)) if tm is not None else (None, None)
        title = re.sub(r"\s+", " ", "".join(x for x in t.find_all(string=True) if x.find_parent("script") is None)).strip()
        a = t.find("a")
        url = norm_url(a["href"]) if a is not None and a.get("href") else None
        room = None
        det = art.find("div", class_="mec-event-detail", recursive=False)
        if det is not None:
            lp = det.find("div", class_="mec-event-loc-place")
            if lp is not None:
                first = [x for x in lp.children if isinstance(x, str) and x.strip()]
                room = first[0].strip() if first else None
        rec = (ld.get("url:" + url) if url else None) or ld.get("name:" + norm_key(title)) or {}
        url = url or rec.get("url") or None
        room = room or rec.get("location") or None
        dkey = (norm_key(title), date, st)
        if dkey in seen:
            continue
        seen.add(dkey)
        out.append({"date": f"{date[:4]}-{date[4:6]}-{date[6:]}" if date else None, "start": st, "end": en,
                    "title": title, "url": url, "room": room, "organizer": rec.get("organizer")})
    return out


def programme_html(evs: list[dict]) -> str:
    if not evs:
        return ""
    days: "OrderedDict[str, list]" = OrderedDict()
    for e in sorted(evs, key=lambda e: (e["date"] or "", e["start"] or "", e["title"])):
        days.setdefault(e["date"] or "", []).append(e)
    parts = []
    for d, lst in days.items():
        if d:
            parts.append(f"<h4>{spanish_date_label(d)}</h4>")
        parts.append("<ul>")
        for e in lst:
            tm = f"{e['start']} - {e['end']}" if e["start"] and e["end"] else (e["start"] or "")
            title = f'<a href="{e["url"]}">{esc(e["title"])}</a>' if e["url"] else esc(e["title"])
            room = f" ({esc(e['room'])})" if e["room"] else ""
            parts.append(f"<li>{('<strong>' + tm + '</strong> ') if tm else ''}{title}{room}</li>")
        parts.append("</ul>")
    return "".join(parts)


ORG_COMPANIES = {"atsistemas": "atSistemas", "moon flower technologies": "Moon Flower Technologies", "abatic": "Abatic", "bitnami": "Bitnami"}
SLUG_SPEAKERS = {  # event URL slug -> speaker (accents restored by hand)
    "charla-del-sr-pablo-garcia-sanchez": "Pablo García Sánchez",
}


def calendar_events_to_records(evs: list[dict], year: int, r: dict, page_label: str) -> tuple[int, int]:
    """Add the calendar events that no other family extracted; return
    (added, covered)."""
    added = covered = 0
    for e in evs:
        if not e["date"]:
            continue
        hit = OTHERS.event_match(e["title"], e["date"], e["url"])
        if hit:
            covered += 1
            covered_events.append(f"{year} {e['date']} {e['start'] or ''} '{e['title']}' ({page_label}) -> {hit}")
            continue
        own = find_event(e["title"], e["date"])
        if own is not None:
            # already added here (MEC iCal export or another archive page): enrich
            if not own["room"] and e["room"] and own["modality"] != "online":
                own["room"] = e["room"]
            if not own["link"] and e["url"]:
                own["link"] = e["url"]
            covered += 1
            covered_events.append(f"{year} {e['date']} {e['start'] or ''} '{e['title']}' ({page_label}) -> already extracted here from {own['source_url']}")
            continue
        org = e["organizer"] or None
        speaker = company = None
        if org:
            if norm_key(org) in ORG_COMPANIES:
                company = ORG_COMPANIES[norm_key(org)]
            elif org not in ("Organizer Name", "InnoSoft"):
                speaker = re.sub(r"^(Dr|Dra|Sr|Sra)\.\s*", "", org).strip()
        if not speaker and slug_of(e["url"]) in SLUG_SPEAKERS:
            speaker = SLUG_SPEAKERS[slug_of(e["url"])]
        if e["title"].startswith("Charla de ") and not company and not speaker:
            rest = e["title"][len("Charla de "):].strip()
            if rest[:1].isupper() and norm_key(rest) not in ("clausura", "apertura", "mesa redonda", "clausura de las jornadas", "apertura de las jornadas"):
                company = rest
        if norm_key(e["title"]).startswith("charla de oficina de software libre"):
            company = "Oficina de Software Libre (Universidad de Sevilla)"
        online = bool(e["room"] and "twitch" in e["room"].lower())
        st = f"{e['date']}T{e['start']}:00" if e["start"] else e["date"] + "T00:00:00"
        en = f"{e['date']}T{e['end']}:00" if e["end"] else None
        if en and st and en < st:
            en = None
        add_event(edition_year=year, title=e["title"], kind=event_kind(e["title"]), starts_at=st, ends_at=en,
                  room=None if online else e["room"], modality="online" if online else "in_person",
                  speaker=speaker, company=company, summary=("Retransmitido en " + e["room"]) if online else None,
                  description_html="", link=e["url"], lang="es", source_url=r["url"], source_timestamp=r["timestamp"])
        if speaker:
            add_speaker(speaker, year, r["url"], affiliation=company)
        added += 1
    return added, covered


def archive_media(html: str, year: int, r: dict) -> None:
    """Images of an edition archive page -> media, captioned from context."""
    s = BeautifulSoup(html, "lxml")
    body = s.body if s.body else s
    section = ""
    prev_text = ""
    rn = roman(year - 2012)
    n_photo = 0
    for el in body.find_all(True):
        if el.name in ("h2", "h3", "h4"):
            section = text_of(el).lower()
            prev_text = text_of(el)
            continue
        if el.name == "p" and el.find("img") is None:
            prev_text = text_of(el)
        if el.name == "a" and (el.get("href") or "").endswith(".mp4"):
            add_media(el["href"], "other", year, f"Vídeo de presentación de la {rn} edición ({year})", r["url"])
            continue
        if el.name != "img":
            continue
        u = norm_url(el.get("src") or "")
        if not u:
            continue
        name = Path(u).name.lower()
        if "logo" in name:
            kind, cap = "logo", f"Logotipo de las jornadas, {rn} edición ({year})"
        elif "ping-u" in name:
            kind, cap = "other", "Mascota Ping-U de la X edición (2022)"
        elif "synthia" in name:
            kind, cap = "other", "Mascota Synthia de la XI edición (2023)"
        elif section.startswith("fotos"):
            n_photo += 1
            kind, cap = "photo", f"Fotos de la {rn} edición ({year}), {n_photo}"
        elif re.search(r"cartel|horario|triptico|programa|martes_|jueves_|viernes_|competitiva|rocket|musical", name) or section.startswith("programa"):
            kind = "poster"
            if prev_text and len(prev_text) <= 160 and prev_text.rstrip().endswith(":"):
                cap = re.sub(r"^(a continuaci[oó]n,?\s*(se puede ver|se detalla|se muestra|veamos)|en primer lugar,?\s*veamos|este es|veamos a continuaci[oó]n)\s+", "", prev_text.rstrip(": ").strip(), flags=re.I)
                cap = cap[:1].upper() + cap[1:] + f" ({rn} edición, {year})"
            else:
                cap = f"Cartel de la {rn} edición ({year})"
            if re.search(r"martes_|jueves_|viernes_", name):
                cap = f"Programa diario de la {rn} edición ({year}), " + re.sub(r"[-_].*", "", Path(u).stem)
            if "encuentro_musical" in name:
                cap = "Cartel del encuentro musical, IX edición (2021)"
            elif "competitiva" in name:
                cap = "Cartel del concurso de programación competitiva, IX edición (2021)"
            elif "rocket" in name:
                cap = "Cartel del torneo de Rocket League, IX edición (2021)"
        else:
            kind, cap = "other", f"Imagen de la página de la {rn} edición ({year}), " + Path(u).stem
        add_media(u, kind, year, cap, r["url"])


def handle_archive_page(rows: list[dict], year: int) -> None:
    r = sorted(rows, key=lambda x: x["timestamp"])[-1]
    s = soup_any(r)
    node = BeautifulSoup(str(content_node(s)), "lxml")
    text = text_of(node)
    rn = roman(year - 2012)
    # calendar
    wraps = node.select(".mec-wrap")
    cal = parse_mec_calendar(wraps[0]) if wraps else []
    holder = node.select_one(".schedule-container") or (wraps[0] if wraps else None)
    if holder is not None:
        ph = node.new_tag("p")
        ph.string = "__PROGRAMME__"
        holder.replace_with(ph)
    for w in node.select(".mec-wrap, .flex-container.tab, .page-header-new"):
        w.decompose()
    html = clean_node(node)
    prog = programme_html(cal)
    if "__PROGRAMME__" in html:
        html = html.replace("<p>__PROGRAMME__</p>", prog)
        html = html.replace("__PROGRAMME__", prog)
    elif prog:
        html = html + prog
    html = re.sub(r"<h[23]>Programa</h[23]>$", "", html).strip()
    # dates, theme, venue
    starts, ends, when = days_in_text(text)
    when = re.sub(r"\s+", " ", when.replace("dias", "días")) if when else when
    tm = re.search(r"tem[aá]tica(?: que guio el transcurso de las jornadas| de esta edici[oó]n| principal)?\s+fue\s+(?:la |el )?([^.]+)\.", text, re.I)
    theme = tm.group(1).strip() if tm else None
    venue = ETSII if ("Ingeniería Informática" in text or "ETSII" in text) else None
    venue_note = ""
    if venue is None and year in (2017, 2018, 2019):
        venue = ETSII
        venue_note = " Venue inferred from the programme rooms (Aula A1.16, Lab B1.36, Salón de Grados...) of the ETSII."
    if venue is None and year == 2020:
        venue = "Online (retransmisión por Twitch, twitch.tv/innosoftdays)"
        venue_note = " Every programme slot of the page is located at 'Twitch Innosoft'."
    if venue is None and year == 2021:
        venue = "Escuela Técnica Superior de Ingeniería Informática, Sevilla"
        venue_note = " Venue from the MEC events of 2021 (institucional family / iCal exports)."
    where = "en la ETSII de la Universidad de Sevilla" if venue == ETSII else ("íntegramente online por Twitch" if year == 2020 else "en la ETSII (Sevilla)")
    summary = f"{ORDINALS.get(year, rn)} de las jornadas InnoSoft Days, {when or 'noviembre de ' + str(year)}, {where}."
    if theme:
        summary += f" Temática: {theme}."
    if year == 2022:
        summary += " Mascota Ping-U."
    if year == 2023:
        summary += " Mascota Synthia."
    add_edition(year, starts_on=starts, ends_on=ends, venue=venue, summary=summary, description_html=html,
                sources=[r["url"]], confidence="high",
                notes=f"Retrospective edition page {path_of(r['url'])} (capture {r['timestamp']}): '{when}'" + (f", theme '{theme}'" if theme else "") + (f"; embedded MEC calendar with {len(cal)} programme slots rendered as the 'Programa' list of the description." if cal else "; no calendar, the programme is the triptych image.") + venue_note)
    archive_media(html, year, r)
    added, covered = calendar_events_to_records(cal, year, r, path_of(r["url"]))
    for rr in sorted(rows, key=lambda x: x["timestamp"]):
        if rr is r:
            used(rr, f"edition archive page {rn} ({year}) -> edition (dates, copy, programme list), media ({len(img_urls(node))} images), calendar: {len(cal)} slots, {added} events added here, {covered} already extracted by other families")
        else:
            same = content_hash(soup_any(rr)) == content_hash(s)
            used(rr, f"edition archive page {rn} ({year}), " + ("same content as" if same else "older version superseded by") + f" {r['timestamp']}; covered")


def handle_programa_x(rows: list[dict]) -> None:
    r = sorted(rows, key=lambda x: x["timestamp"])[-1]
    s = soup_any(r)
    node = content_node(s)
    wraps = node.select(".mec-wrap")
    cal = parse_mec_calendar(wraps[0]) if wraps else []
    added, covered = calendar_events_to_records(cal, 2022, r, "/programa-x-edicion/")
    add_edition(2022, sources=[r["url"]], notes=f"/programa-x-edicion/ (MEC monthly calendar of November 2022, {len(cal)} slots) cross-checked against the X programme.")
    for rr in sorted(rows, key=lambda x: x["timestamp"]):
        used(rr, f"X edition programme calendar (MEC, gzip capture): {len(cal)} slots, {added} events added here, {covered} already extracted (events_mec / this family's /x-edicion/)")


# ----------------------------------------------------------------------------
# 2025 site (Blocksy + Elementor)
# ----------------------------------------------------------------------------

def latest(rows: list[dict]) -> dict:
    return sorted(rows, key=lambda r: r["timestamp"])[-1]


def cover_versions(rows: list[dict], chosen: dict, what: str) -> None:
    hashes = {}
    for r in rows:
        hashes[r["timestamp"]] = content_hash(soup_any(r))
    for r in sorted(rows, key=lambda r: r["timestamp"]):
        if r is chosen:
            used(r, what)
        elif hashes[r["timestamp"]] == hashes[chosen["timestamp"]]:
            used(r, f"same content as {chosen['timestamp']}; covered")
        else:
            used(r, f"older/different version, superseded by {chosen['timestamp']} (differences noted)")


def handle_inicio_2025(rows: list[dict]) -> None:
    r = latest(rows)
    s = soup_any(r)
    node = content_node(s)
    html = clean_node(node, elementor=True)
    add_edition(2025, starts_on="2025-11-04", ends_on="2025-11-06",
                venue="Escuela Técnica Superior de Ingeniería Informática (ETSII), Universidad de Sevilla, Av. Reina Mercedes s/n, 41012 Sevilla",
                summary="Jornadas InnoSoft Days edición XIII, días 4 a 6 de noviembre de 2025 en la ETSII (torneos online desde el 3 de noviembre). Charlas, talleres, eSports, escape room, game jam y gincanas en torno a la tecnología, la programación y la inteligencia artificial.",
                description_html=html, sources=[r["url"]], confidence="high",
                notes="Dates and venue from /es/inicio (\"Días 4-6 de noviembre, ETSII Universidad de Sevilla\"); the schedule adds online eSports on Monday 3 November.")
    for u in img_urls(node):
        add_media(u, "other", 2025, "Imagen de la portada 2025 (" + Path(full_size(u)).stem + ")", r["url"])
    cover_versions(rows, r, "2025 home copy (ES) -> edition 2025 description")


def handle_home_en_2025(rows: list[dict]) -> None:
    """The English 2025 home only survives under ?method=ical&id=N URLs (MEC
    was uninstalled, WordPress served the front page, canonical
    https://www.innosoftdays.com/)."""
    if not rows:
        return
    r = latest(rows)
    s = soup_any(r)
    node = content_node(s)
    html = clean_node(node, elementor=True, lang="en")
    meta = page_meta(s)
    page_url = meta["canonical"] or SITE + "/"
    pages.append({"edition_year": 2025, "title": "InnoSoft Days XIII (English home)", "url": page_url, "content_html": html, "kind": "about",
                  "source_url": r["url"], "source_timestamp": r["timestamp"]})
    editions[2025]["sources"].append(r["url"]) if r["url"] not in editions[2025]["sources"] else None
    for rr in sorted(rows, key=lambda x: x["timestamp"]):
        if rr is r:
            used(rr, f"English 2025 home rendered under an iCal URL (canonical {page_url}) -> pages (about, en)")
        else:
            used(rr, f"English 2025 home rendered under an iCal URL, same content as {r['timestamp']}; covered")


def handle_about(rows: list[dict], lang: str) -> None:
    r = latest(rows)
    s = soup_any(r)
    node = content_node(s)
    html = clean_node(node, elementor=True, lang=lang)
    title = "About us" if lang == "en" else "Sobre nosotros"
    pages.append({"edition_year": 2025, "title": title, "url": r["url"], "content_html": html, "kind": "about",
                  "source_url": r["url"], "source_timestamp": r["timestamp"]})
    add_edition(2025, sources=[r["url"]])
    cover_versions(rows, r, f"2025 about page ({lang}) -> pages")


DAY_RE = re.compile(r"^(LUNES|MARTES|MI[ÉE]RCOLES|JUEVES|VIERNES|S[ÁA]BADO|DOMINGO)\s+(\d{1,2})\s+(NOVIEMBRE|OCTUBRE)$", re.I)
COMPANY_PREFIXES = {"ntt data": "NTT Data", "indra": "Indra", "caixabank tech": "CaixaBank Tech"}
NON_PERSON_PREFIXES = {"esports", "torneo", "escape room", "game jam", "gincana", "comite de igualdad", "ceremonia de apertura", "ceremonia de cierre", "el desafio sostenible", "una charla con rebeca"}


def classify_2025(title: str, desc: str) -> str:
    k = norm_key(title)
    d = norm_key(desc)
    if k.startswith("ceremonia"):
        return "ceremony"
    if any(k.startswith(p) for p in ("torneo", "esports", "game jam", "escape room", "gincana", "el desafio sostenible")):
        return "competition"
    if "taller" in d or "talleres" in d:
        return "workshop"
    return "talk"


def split_title(title: str) -> tuple[str | None, str | None]:
    """'Pablo Reina - Predicción...' -> (speaker, company)."""
    if " - " not in title:
        return None, None
    prefix = title.split(" - ", 1)[0].strip()
    k = norm_key(prefix)
    if k in COMPANY_PREFIXES:
        return None, COMPANY_PREFIXES[k]
    if any(k.startswith(p) for p in NON_PERSON_PREFIXES):
        return None, None
    return prefix, None


def parse_eventos_2025(rows: list[dict]) -> dict[str, dict]:
    """/es/eventos: per event block title, description, date/time/room, poster,
    links. Returns key -> info."""
    r = latest(rows)
    s = soup_any(r)
    node = content_node(s)
    out: dict[str, dict] = {}
    for block in node.select(".e-con-full.e-transform"):
        heads = [h for h in block.select(".elementor-widget-heading .elementor-heading-title")]
        if not heads:
            continue
        title = text_of(heads[0]).replace("\n", " ")
        title = re.sub(r"\s+", " ", title)
        info = {"title": title, "desc_html": "", "date": None, "time": None, "room": None, "poster": None, "links": [], "bio_html": ""}
        for h in heads[1:]:
            t = text_of(h)
            m = re.match(r"(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2}:\d{2})\s*(.*)$", t)
            if m:
                info["date"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                info["time"] = f"{int(m.group(4).split(':')[0]):02d}:{m.group(4).split(':')[1]}"
                info["room"] = m.group(5).strip() or None
            elif t.lower().startswith("sobre "):
                continue
            else:
                h2 = BeautifulSoup(str(h), "lxml")
                for tag in h2.find_all(["h1", "h2", "h3", "h4"]):
                    tag.name = "p"
                frag = tidy_html(clean_html(h2))
                if norm_key(t).startswith(norm_key(title.split(" - ")[0])) and len(t) > 300:
                    info["bio_html"] += frag
                else:
                    info["desc_html"] += frag
        img = block.find("img")
        if img is not None:
            fix_lazy_images(block)
            img = block.find("img")
            info["poster"] = norm_url(img.get("src") or "")
        for a in block.find_all("a", href=True):
            info["links"].append({"label": text_of(a), "url": a["href"]})
        out[norm_key(title)] = info
    for rr in sorted(rows, key=lambda x: x["timestamp"]):
        used(rr, "2025 events listing (descriptions, posters, links, speaker names) merged into the cronograma events" + ("" if rr is r else f"; same content as {r['timestamp']}"))
    return out


SPEAKER_FULL_2025 = {  # short name in the schedule -> (full name, affiliation, position) as written in /es/eventos
    "pablo reina": ("Pablo Reina Jiménez", "Universidad de Sevilla", "Docente e investigador"),
    "pedro almagro": ("Pedro Almagro Blanco", "Universidad de Sevilla", "Profesor"),
    "pablo davila": ("Pablo Dávila Herrero", None, None),
    "manuel carranza": ("Manuel Carranza", None, None),
    "andreas zeller": ("Andreas Zeller", "CISPA Helmholtz Center for Information Security / Universidad de Saarland", "Profesor e investigador"),
}

# speakers named only inside the /es/eventos description of a company talk
DESC_SPEAKERS_2025 = [
    ("José Carlos Moral Cuevas", "NTT Data", "Experto en seguridad"),
    ("Jorge Martos", "Indra", None),
    ("Mario Jiménez Calderón", "CaixaBank Tech", None),
    ("Rebeca Sarai González Guerra", None, None),
]

TITLE_ALIASES = {  # cronograma title -> eventos title
    "ceremonia de cierre": "ceremonia de clausura",
    "ceremonia de apertura": "ceremonia de apertura",
}


def handle_cronograma_2025(rows: list[dict], eventos_rows: list[dict], schedule_rows: list[dict]) -> None:
    r = latest(rows)
    s = soup_any(r)
    node = content_node(s)
    fix_lazy_images(node)
    infos = parse_eventos_2025(eventos_rows) if eventos_rows else {}
    online = False
    day = None
    cur = None
    parsed: list[dict] = []
    for el in node.select(".elementor-widget-heading .elementor-heading-title, .elementor-widget-image img"):
        if el.name == "img":
            if cur is not None and not cur.get("poster"):
                cur["poster"] = norm_url(el.get("src") or "")
            continue
        t = re.sub(r"[​]", "", text_of(el)).strip()
        t = re.sub(r"\s+", " ", t)
        if not t:
            continue
        if t.upper() == "ONLINE":
            online = True
            cur = None
            continue
        if t.upper().startswith("QR "):
            cur = None
            continue
        dm = DAY_RE.match(t)
        if dm:
            month = 11 if dm.group(3).upper().startswith("NOV") else 10
            day = f"2025-{month:02d}-{int(dm.group(2)):02d}"
            cur = None
            continue
        if t.lower().startswith("hora"):
            if cur is not None:
                a, b = parse_time(t)
                cur["start"], cur["end"] = a, b
            continue
        if t.lower().startswith("lugar"):
            if cur is not None:
                cur["room"] = re.sub(r"^lugar:\s*", "", t, flags=re.I).strip() or None
            continue
        cur = {"title": t, "day": day, "online": online, "start": None, "end": None, "room": None, "poster": None}
        parsed.append(cur)
    seen_keys = set()
    for p in parsed:
        title = p["title"]
        title = re.sub(r"\s*\((cuartos Bo1|semi y Final)\)\s*", lambda m: " (" + m.group(1) + ")", title)
        title = title.replace("Intentando Bo3", "").strip()
        key = norm_key(title)
        dk = (key, p["day"], p["start"])
        if dk in seen_keys:
            continue
        seen_keys.add(dk)
        info = infos.get(TITLE_ALIASES.get(key, key)) or infos.get(key)
        if info is None:
            for k2, v in infos.items():
                if k2.split()[:3] == key.split()[:3]:
                    info = v
                    break
        speaker, company = split_title(title)
        if speaker:
            speaker = SPEAKER_FULL_2025.get(norm_key(speaker), (speaker,))[0]
        desc = info["desc_html"] if info else ""
        desc_text = re.sub(r"\s+", " ", text_of(BeautifulSoup(desc, "lxml"))) if desc else ""
        if not speaker and desc_text:
            for name, _aff, _pos in DESC_SPEAKERS_2025:
                if name_phrase_in_text(name, desc_text):
                    speaker = name
                    break
        kind = classify_2025(title, desc_text)
        if p["online"] or key.startswith("esports tft") or key.startswith("esports lol"):
            kind = "competition"
        starts_at = f"{p['day']}T{p['start']}:00" if p["day"] and p["start"] else (p["day"] + "T00:00:00" if p["day"] else None)
        ends_at = f"{p['day']}T{p['end']}:00" if p["day"] and p["end"] else None
        link = None
        if info and info["links"]:
            ext = [l for l in info["links"] if "innosoftdays" not in l["url"]]
            pref = [l for l in ext if l["label"].lower().startswith("charla")]
            if pref or ext:
                link = (pref or ext)[0]["url"]
        poster = p["poster"] or (info["poster"] if info else None)
        poster = pick_url(poster) if poster else None
        add_event(edition_year=2025, title=title, kind=kind, starts_at=starts_at, ends_at=ends_at,
                  room=p["room"] if not p["online"] else None,
                  modality="online" if p["online"] else "in_person",
                  speaker=speaker, company=company,
                  summary=desc_text[:300] if desc_text else None,
                  description_html=desc, poster_url=poster, link=link, lang="es",
                  source_url=r["url"], source_timestamp=r["timestamp"])
        if info and info.get("date") and p["day"] and info["date"] != p["day"]:
            oddities.append(f"2025 event '{title}': cronograma day {p['day']} vs eventos date {info['date']} (cronograma kept)")
        if info and info.get("time") and p["start"] and info["time"] != p["start"]:
            oddities.append(f"2025 event '{title}': cronograma start {p['start']} vs eventos {info['time']} (cronograma kept)")
        if info and info.get("room") and p["room"] and norm_key(info["room"].replace("Aula", "")) != norm_key(p["room"]):
            oddities.append(f"2025 event '{title}': cronograma room {p['room']} vs eventos {info['room']} (cronograma kept)")
        if poster:
            add_media(poster, "poster", 2025, f"Cartel: {title}", r["url"])
    have = {norm_key(e["title"]) for e in events if e["edition_year"] == 2025}
    for k, info in infos.items():
        alias_hit = any(TITLE_ALIASES.get(h, h) == k for h in have)
        if k in have or alias_hit:
            continue
        loose = any(h.split()[:3] == k.split()[:3] for h in have)
        if loose:
            continue
        oddities.append(f"/es/eventos block without a slot in /es/cronograma: {info['title']}")
    # speakers 2025 (from the eventos descriptions)
    er = latest(eventos_rows) if eventos_rows else r
    for k, info in infos.items():
        speaker, company = split_title(info["title"])
        if k.startswith("andreas zeller"):
            add_speaker("Andreas Zeller", 2025, er["url"], affiliation="CISPA Helmholtz Center for Information Security / Universidad de Saarland",
                        position="Profesor e investigador", bio_html=info["bio_html"], links=[l for l in info["links"]])
        elif speaker:
            full = SPEAKER_FULL_2025.get(norm_key(speaker), (speaker, None, None))
            add_speaker(full[0], 2025, er["url"], affiliation=full[1], position=full[2])
    for name, aff, pos in DESC_SPEAKERS_2025:
        if any(e["edition_year"] == 2025 and e["speaker"] == name for e in events):
            add_speaker(name, 2025, er["url"], affiliation=aff, position=pos)
        else:
            oddities.append(f"2025 speaker {name} not found in any /es/eventos description (not added)")
    add_edition(2025, sources=[r["url"]] + ([latest(eventos_rows)["url"]] if eventos_rows else []))
    cover_versions(rows, r, "2025 schedule (ES) -> events 2025 (titles, day, time, room, poster)")
    for rr in sorted(schedule_rows, key=lambda x: x["timestamp"]):
        used(rr, "English 2025 schedule: same programme as /es/cronograma (English titles not extracted separately; times/rooms cross-checked)")
    if schedule_rows:
        sr = latest(schedule_rows)
        ss = soup_any(sr)
        heads = [re.sub(r"\s+", " ", text_of(h)) for h in content_node(ss).select(".elementor-widget-heading .elementor-heading-title")]
        en_rooms = [h for h in heads if h.lower().startswith("room")]
        es_rooms = [e["room"] for e in events if e["edition_year"] == 2025 and e["room"]]
        if len(en_rooms) != len(es_rooms):
            oddities.append(f"/schedule (EN) lists {len(en_rooms)} rooms vs {len(es_rooms)} in /es/cronograma; the EN page shows the Escape Room in A2.12/A2.15 (ES: AS45) and CaixaBank Tech at 9:30 AM (ES: 11:30). ES kept.")


def handle_fotos_2025(rows_es: list[dict], rows_en: list[list[dict]]) -> None:
    r = latest(rows_es)
    s = soup_any(r)
    node = content_node(s)
    top_imgs = []
    for img in node.select(".metaslider img"):
        if img.find_parent(class_="e-n-tabs") is None:
            top_imgs.append(norm_url(img.get("src") or ""))
    for u in top_imgs:
        add_media(u, "photo", 2025, "InnoSoft Days 2025 (galería general)", r["url"])
    tabs = node.select_one(".e-n-tabs")
    n = len(top_imgs)
    if tabs is not None:
        titles = [text_of(b) for b in tabs.select(".e-n-tabs-heading .e-n-tab-title")]
        contents = tabs.select_one(".e-n-tabs-content").find_all(recursive=False)
        for day, c in zip(titles, contents):
            for panel in c.select(".gutena-accordion-block__panel"):
                h = text_of(panel.select_one(".gutena-accordion-block__panel-title"))
                for img in panel.select("ul.slides img"):
                    u = norm_url(img.get("src") or "")
                    if u:
                        add_media(u, "photo", 2025, f"{h} ({day.strip()} de noviembre de 2025)", r["url"])
                        n += 1
    cover_versions(rows_es, r, f"2025 photo galleries -> media ({n} photo slots, grouped by activity)")
    for grp in rows_en:
        for rr in sorted(grp, key=lambda x: x["timestamp"]):
            ss = soup_any(rr)
            imgs = {pick_url(i.get("src") or "") for i in content_node(ss).select("ul.slides img")}
            extra = [u for u in imgs if u not in media]
            for u in extra:
                add_media(u, "photo", 2025, "InnoSoft Days 2025", rr["url"])
            used(rr, f"English/older photo gallery: {len(imgs)} photos, {len(extra)} not already in /es/fotos" + (" (added)" if extra else ""))
            for u in imgs:
                if u in media and rr["url"] not in media[u]["used_by"]:
                    media[u]["used_by"].append(rr["url"])


def handle_cuestionario_2025(rows: list[dict]) -> None:
    r = latest(rows)
    s = soup_any(r)
    node = content_node(s)
    node = BeautifulSoup(str(node), "lxml")
    for f in node.find_all("form"):
        f.decompose()
    html = clean_node(node, elementor=True)
    pages.append({"edition_year": 2025, "title": "Cuestionario de calidad", "url": r["url"], "content_html": html, "kind": "other",
                  "source_url": r["url"], "source_timestamp": r["timestamp"]})
    cover_versions(rows, r, "2025 satisfaction questionnaire intro -> pages (other); the form fields themselves are dropped")


# ----------------------------------------------------------------------------
# Astra site pages (2022 to early 2025)
# ----------------------------------------------------------------------------

def astra_page(rows: list[dict], kind: str, year: int, title: str | None = None, extra_drop=(), what: str = "", lang: str = "es") -> tuple[dict, BeautifulSoup, str]:
    r = latest(rows)
    s = soup_any(r)
    node = content_node(s)
    html = clean_node(node, drop_selectors=DROP_SELECTORS + list(extra_drop), lang=lang)
    meta = page_meta(s)
    t = title or meta["title"] or text_of(s.find("h1"))
    if t and html.startswith(t):
        html = html[len(t):].lstrip()
    pages.append({"edition_year": year, "title": t, "url": r["url"], "content_html": html, "kind": kind,
                  "source_url": r["url"], "source_timestamp": r["timestamp"]})
    cover_versions(rows, r, what or f"{kind} page -> pages (edition {year})")
    return r, s, html


def handle_como_llegar(rows: list[dict], lang: str) -> None:
    """Two versions: 2024-09 says 'Las XI jornadas' (2023 text), 2024-12 says
    'Las XII jornadas'. Extract each distinct version with its own year."""
    by_hash: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_hash[content_hash(soup_any(r))].append(r)
    for h, grp in sorted(by_hash.items(), key=lambda kv: kv[1][0]["timestamp"]):
        r = latest(grp)
        s = soup_any(r)
        node = content_node(s)
        text = text_of(node)
        m = re.search(r"\b(XI{0,3}|IX|X)\b\s+(jornadas|edition)|The (\d+)(?:th|st|nd|rd) edition", text)
        year = None
        if m:
            if m.group(3):
                year = 2012 + int(m.group(3))
            else:
                year = 2012 + {"IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13}[m.group(1)]
        year = year or 2024
        html = clean_node(node, lang=lang)
        pages.append({"edition_year": year, "title": "Cómo llegar" if lang == "es" else "Find us", "url": r["url"], "content_html": html, "kind": "how_to_get",
                      "source_url": r["url"], "source_timestamp": r["timestamp"]})
        add_edition(year, venue="Escuela Técnica Superior de Ingeniería Informática (ETSII), Campus de Reina Mercedes (Av. Reina Mercedes s/n), Sevilla", sources=[r["url"]])
        for rr in sorted(grp, key=lambda x: x["timestamp"]):
            used(rr, f"how_to_get page version describing edition {year} -> pages" + ("" if rr is r else f" (same content as {r['timestamp']})"))


def handle_talk_pages(groups: dict[str, list[dict]]) -> None:
    """2022 'Información sobre la ponencia ...' pages: image-only posters."""
    for url, rows in sorted(groups.items()):
        r = latest(rows)
        s = soup_any(r)
        node = content_node(s)
        meta = page_meta(s)
        title = meta["title"] or text_of(s.find("h1"))
        year = year_of(meta["modified"]) or year_of(meta["published"]) or 2022
        imgs = img_urls(node)
        seen, uniq = set(), []
        for u in imgs:
            fs = full_size(u)
            if fs not in seen:
                seen.add(fs)
                uniq.append(pick_url(u))
        html = "".join(f'<figure><img src="{u}" alt="{esc(title)}"/></figure>' for u in uniq)
        extra = TALK_TRANSCRIPTIONS.get(slug := path_of(url).strip("/"))
        if extra:
            html = extra["html"] + html
        pages.append({"edition_year": year, "title": title, "url": r["url"], "content_html": html, "kind": "other",
                      "source_url": r["url"], "source_timestamp": r["timestamp"]})
        for u in uniq:
            add_media(u, "poster", year, title, r["url"])
        m = re.search(r"ponencia (?:del|de la|de los|de las|de)\s+(?:Sr\.|Sra\.|Srs\.|Sras\.)?\s*(.+)$", title)
        names = []
        if m:
            raw = m.group(1).strip()
            names = [n.strip() for n in re.split(r"\s+y\s+|,", raw) if n.strip()]
        affil = TALK_AFFILIATION.get(slug)
        for n in names:
            n = re.sub(r"^(Sr|Sra|Srs|Sras)\.\s*", "", n)
            add_speaker(n, year, r["url"], affiliation=affil or (extra or {}).get("affiliation"), position=(extra or {}).get("position"))
        for rr in sorted(rows, key=lambda x: x["timestamp"]):
            used(rr, f"talk poster page ({', '.join(names) or title}) -> pages (other, {year}) + poster media" + ("" if rr is r else f"; same images as {r['timestamp']}"))


POSTER_CAPTIONS = {
    "Flyerpara-impresion-en-pequeno-1.webp": "Flyer de las jornadas XII edición (2024)",
    "cartelMentoria2.webp": "Cartel de las mentorías, XII edición (2024)",
    "Torneos-Videojuegos-InnoSoft.webp": "Cartel de los torneos de videojuegos, XII edición (2024)",
    "Charla-sostenibilidad-Anabel-Carmona.webp": "Cartel de la charla de sostenibilidad de Anabel Carmona (2024)",
    "cartel7.webp": "Cartel de actividades XII edición (2024), 7",
    "cartel6.webp": "Cartel de actividades XII edición (2024), 6",
    "cartel-minecraft.jpg": "Cartel del torneo de Minecraft, XII edición (2024)",
}

SPEAKER_ALIASES = {
    "israel blancas alvares": "Israel Blancas Álvarez",  # slug typo on one of the two pages
}

# The only 2022 talk posters the archive captured as files (uploads 1-22.png,
# 2-22.png) were read by hand; the text lives only inside the images.
TALK_TRANSCRIPTIONS = {
    "informacion-sobre-la-ponencia-del-sr": {
        "affiliation": "Ártica / Pandora FMS",
        "position": "CEO y fundador de Ártica",
        "html": "<p><strong>Sancho Lerena</strong>, CEO y fundador de Ártica (Pandora FMS). Ponencia online el 8 de noviembre de 2022, 09:30 a 10:30.</p>"
                "<p>Ponencia: El OpenSource es uno de los caminos a seguir por cualquier ingeniero, desarrollador y soñador que quiera aprender por su cuenta. Es el perfecto lugar de encuentro entre creadores, autodidactas, soñadores e ingenieros. Un camino profesional e incluso empresarial. Pandora FMS comenzó en 2003 como un proyecto puramente libre, y con el paso de los años fue tomando forma como proyecto empresarial viable. Casi 20 años después, nuestros clientes nos han consolidado en un lugar de privilegio en el panorama del software especializado hecho en España. En esta charla abierta, donde se busca el diálogo, Sancho Lerena hablará sobre ese proceso.</p>",
    },
}

TALK_AFFILIATION = {
    "prise": "PRiSE",
    "red-hat": "Red Hat",
    "tragsatec": "Tragsatec",
    "informacion-sobre-la-ponencia-de-los-srs-rafael-poveda-santos-y-jose-carlos-gomez": "Accenture",
    "informacion-sobre-la-ponencia-del-sr-antonio-castillo": "Deloitte",
    "informacion-sobre-la-ponencia-del-sr-israel-blancas-alvares": "Red Hat",
}


def quiz_html(node) -> tuple[str, list[str]] | None:
    """Quiz and Survey Master form (Adivina el logo): questions, images and
    options as an ordered list (the form itself is dropped by clean_html)."""
    qs = node.select(".qsm-question-wrapper")
    if not qs:
        return None
    parts = []
    intro = node.select_one(".qsm-before-message")
    if intro is not None:
        parts.append(tidy_html(clean_html(intro)))
    parts.append("<ol>")
    imgs_all = []
    for q in qs:
        qt = text_of(q.select_one(".mlw_qmn_new_question"))
        qt = re.sub(r"\s*\[\d+/\d+\]\s*$", "", qt)
        qimg = q.select_one(".mlw_qmn_question")
        imgs = [pick_url(u) for u in img_urls(qimg)] if qimg is not None else []
        imgs_all.extend(imgs)
        opts = [text_of(l) for l in q.select("label.qsm-input-label") if text_of(l)]
        parts.append(f"<li><p>{esc(qt)}</p>" + "".join(f'<figure><img src="{u}" alt="{esc(qt)}"/></figure>' for u in imgs)
                     + ("<ul>" + "".join(f"<li>{esc(o)}</li>" for o in opts) + "</ul>" if opts else "") + "</li>")
    parts.append("</ol>")
    return "".join(parts), imgs_all


def handle_games(groups: dict[str, list[dict]]) -> None:
    """Online games of the site: one event (kind other, online) per game,
    year = first publication (the edition that created it)."""
    for url, rows in sorted(groups.items()):
        r = latest(rows)
        s = soup_any(r)
        node = content_node(s)
        meta = page_meta(s)
        title = meta["title"] or text_of(s.find("h1"))
        year = year_of(meta["published"]) or year_of(meta["modified"])
        quiz = quiz_html(node) if "adivina" in url else None
        if quiz:
            html = quiz[0]
            for i, u in enumerate(quiz[1], 1):
                add_media(u, "other", year, f"Adivina el logo, imagen de la pregunta {i}", r["url"])
        else:
            html = clean_node(node)
            html = re.sub(r"<p>\s*Your browser does not support iframes\.\.\.\s*</p>", "", html)
        text = text_of(node)
        lang = "en" if path_of(url).startswith("/en/") else "es"
        summary = None
        if "crucigrama" in url or "crossword" in url:
            summary = "Crucigrama online publicado en la web de las jornadas (morepuzzles.com)."
        elif "wordle" in url:
            days = re.findall(r"(\d{2}/\d{2}/\d{4})", text)
            summary = f"Wordle diario de las jornadas: {len(days)} palabras publicadas entre el {days[-1]} y el {days[0]}." if days else "Wordle diario de las jornadas."
        elif "ahorcado" in url:
            summary = "Juego del ahorcado online (plugin Hangman) en la web de las jornadas."
        elif "adivina" in url:
            n = len(quiz[1]) if quiz else 5
            summary = f"Quiz online: adivina el logo ({n} logos de software)."
        elif "ctf" in url:
            summary = "Captura la bandera (CTF) de InnoSoft 2021; la página capturada no conserva el contenido."
        starts = ends = None
        if "wordle" in url:
            days = re.findall(r"(\d{2})/(\d{2})/(\d{4})", text)
            if days:
                ds = sorted(f"{y}-{m}-{d}" for d, m, y in days)
                starts, ends = ds[0] + "T00:00:00", ds[-1] + "T23:59:59"
        add_event(edition_year=year, title=title, kind="other", starts_at=starts, ends_at=ends, room=None,
                  modality="online", summary=summary, description_html=html, link=r["url"], lang=lang,
                  source_url=r["url"], source_timestamp=r["timestamp"])
        if not text.strip() and not html:
            oddities.append(f"{url}: entry-content empty in the capture ({r['timestamp']}); event kept with title only")
        cover_versions(rows, r, f"online game page -> events (other, online, {year})")


def handle_attachment_pages(groups: dict[str, list[dict]]) -> None:
    """Twenty Twenty-Five attachment pages: just one image each."""
    for url, rows in sorted(groups.items()):
        r = latest(rows)
        s = soup_any(r)
        node = content_node(s)
        links = [norm_url(a.get("href")) for a in node.find_all("a", href=True) if "/wp-content/uploads/" in (a.get("href") or "")]
        imgs = img_urls(node)
        target = links[0] if links else (imgs[0] if imgs else None)
        title = text_of(s.find("h1")) or Path(path_of(url).strip("/")).name
        if not target:
            for rr in rows:
                skipped(rr, "attachment page without any image in the capture")
            continue
        m = re.search(r"/uploads/(\d{4})/", target)
        year = int(m.group(1)) if m else None
        kind = "other"
        low = title.lower()
        if any(w in low for w in ("ajedrez", "brawlhalla", "torneo", "gymkana", "gymkhana")):
            kind = "poster"
        elif "libnamic" in low:
            kind = "logo"
        add_media(target, kind, year, f"Adjunto '{title}' (página de adjunto de WordPress)", r["url"])
        for rr in sorted(rows, key=lambda x: x["timestamp"]):
            used(rr, f"WordPress attachment page: image {pick_url(target)} -> media ({kind}, {year})" + ("" if rr is r else "; same"))


def handle_tec_listings(groups: dict[str, list[dict]]) -> None:
    """The Events Calendar category / tag archives (2024): the JSON-LD block
    lists the events of the view; all of them are single event captures of
    the events_eventos_etn family, so nothing new is emitted unless missing."""
    for url, rows in sorted(groups.items()):
        for r in sorted(rows, key=lambda x: x["timestamp"]):
            s = soup_any(r)
            items = []
            for ld in s.find_all("script", type="application/ld+json"):
                try:
                    g = json.loads(ld.string or "")
                except (ValueError, TypeError):
                    continue
                for it in (g if isinstance(g, list) else [g]):
                    if isinstance(it, dict) and it.get("@type") == "Event":
                        items.append(it)
            # the JSON-LD block only lists part of the view; the rendered articles (month grid, list, mobile) hold the rest
            by_href: dict[str, dict] = OrderedDict()
            for it in items:
                u = norm_url(it.get("url") or "")
                if u:
                    by_href[u] = it
            for art in s.select("article.tribe_events"):
                a = art.find("a", href=re.compile(r"/event/[^/]+/$"))
                if a is None:
                    continue
                u = norm_url(a["href"])
                if u in by_href:
                    continue
                name = (a.get("title") or text_of(a)).strip()
                day = None
                for tm in art.find_all("time"):
                    if re.match(r"\d{4}-\d{2}-\d{2}$", tm.get("datetime") or ""):
                        day = tm["datetime"]
                        break
                st_txt = text_of(art.select_one(".tribe-event-date-start")) or ""
                en_txt = text_of(art.select_one(".tribe-event-time")) or ""
                st, _ = parse_time(st_txt)
                en, _ = parse_time(en_txt)
                if not st:
                    hh = [tm.get("datetime") for tm in art.find_all("time") if re.match(r"\d{2}:\d{2}$", tm.get("datetime") or "")]
                    st = hh[0] if hh else None
                    en = hh[1] if len(hh) > 1 else en
                desc_node = art.select_one(".tribe-events-calendar-month__calendar-event-tooltip-description, .tribe-events-calendar-list__event-description, .tribe-events-calendar-day__event-description")
                by_href[u] = {"@type": "Event", "name": name, "url": u,
                              "startDate": f"{day}T{st}:00" if day and st else (day or ""),
                              "endDate": f"{day}T{en}:00" if day and en else "", "description": text_of(desc_node), "_html": True}
            items = list(by_href.values())
            if not items:
                used(r, "TEC listing view without events in the capture (empty month/day view or JavaScript-rendered list); nothing to extract")
                continue
            covered, added = [], []
            for it in items:
                name = html_mod.unescape(it.get("name") or "")
                start = (it.get("startDate") or "")[:19]
                hit = OTHERS.event_match(name, start[:10], it.get("url"))
                if hit:
                    covered.append(f"{name} -> {hit}")
                    continue
                own = find_event(name, start[:10])
                if own is not None:
                    covered.append(f"{name} -> already extracted here")
                    continue
                end = (it.get("endDate") or "")[:19]
                loc = (it.get("location") or {}).get("name")
                desc = html_mod.unescape(it.get("description") or "")
                add_event(edition_year=int(start[:4]) if start else 2024, title=name, kind=event_kind(name),
                          starts_at=start or None, ends_at=end or None, room=None,
                          modality="online" if "online" in desc.lower() else "in_person",
                          summary=desc or None, description_html=f"<p>{esc(desc)}</p>" if desc else "",
                          poster_url=pick_url(it["image"]) if it.get("image") else None,
                          link=norm_url(it.get("url") or "") or None, lang="es", source_url=r["url"], source_timestamp=r["timestamp"])
                added.append(name)
            used(r, f"TEC category listing: {len(items)} events (JSON-LD + rendered articles), {len(covered)} already extracted ({'; '.join(covered)})" + (f", added here: {', '.join(added)}" if added else ""))


def handle_ical(rows: list[dict], event_urls: set[str]) -> None:
    """MEC iCal exports under ?method=ical&id=N. MEC writes the site's LOCAL
    time with a fake 'Z' suffix (WordPress timezone UTC): iCal 2510 says
    165000Z and the MEC page shows 16:50; so DTSTART/DTEND are read as naive
    Europe/Madrid, no conversion."""
    by_url: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_url[r["url"]].append(r)
    en_home_rows: list[dict] = []
    for url, grp in sorted(by_url.items()):
        for r in sorted(grp, key=lambda x: x["timestamp"]):
            t = read_html_any(r)
            if "BEGIN:VCALENDAR" not in t:
                if "Why should you attend" in t:
                    en_home_rows.append(r)
                elif "Disponible próximamente" in t:
                    skipped(r, "iCal URL served the 2025 interim placeholder home (\"Disponible próximamente en el curso 2025/26\")")
                elif "no se ha encontrado nada" in t:
                    skipped(r, "iCal URL served an empty blog listing of the interim 2025 site")
                else:
                    skipped(r, "iCal URL served an unrecognised page")
                continue

            def field(name):
                m = re.search(r"^" + name + r"(?:;[^:]*)?:(.*)$", t, re.M)
                return m.group(1).strip() if m else None
            summ = (field("SUMMARY") or "").replace("\\,", ",")
            dtstart, dtend = field("DTSTART"), field("DTEND")
            loc = field("LOCATION")
            org = re.search(r"^ORGANIZER;CN=([^:]*):", t, re.M)
            org = org.group(1).strip() if org else None
            cat = field("CATEGORIES")
            m = re.search(r"^URL:(.*)$", t, re.M)
            ev_url = norm_url(m.group(1).strip()) if m else None

            def local(v):
                if not v:
                    return None
                for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S"):
                    try:
                        return datetime.strptime(v, fmt).isoformat(timespec="seconds")
                    except ValueError:
                        continue
                return None
            st, en = local(dtstart), local(dtend)
            year = int(st[:4]) if st else (int(cat) if cat and cat.isdigit() else None)
            desc = f"{summ} | {st} | {loc or ''} | {org or ''} | {ev_url}"
            if ev_url in event_urls:
                skipped(r, f"MEC iCal export of an event whose page was captured (events family): {desc}")
                continue
            hit = OTHERS.event_match(summ, st, ev_url)
            if hit:
                skipped(r, f"MEC iCal export duplicating an event already extracted by another family from its own page ({hit}): {desc}")
                continue
            own = find_event(summ, st)
            if own is not None:
                used(r, f"MEC iCal export, same event as {own['source_url']} (already extracted here): {desc}")
                continue
            speaker = org if org and org not in ("Organizer Name", "InnoSoft") else None
            company = position = None
            if speaker and speaker.lower() in ("atsistemas", "digitálica salud"):
                company, speaker = speaker, None
            if speaker and " - " in speaker:
                speaker, position = [x.strip() for x in speaker.split(" - ", 1)]
            if not speaker:
                mm = re.search(r"[–-]\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+){1,3})$", summ)
                if mm:
                    speaker = mm.group(1)
            online = bool(loc and "twitch" in loc.lower())
            add_event(edition_year=year, title=summ, kind=event_kind(summ), starts_at=st, ends_at=en, room=None if online else (loc or None),
                      modality="online" if online else "in_person",
                      speaker=speaker, company=company, summary=("Retransmitido en " + loc) if online else None, description_html="",
                      link=ev_url, lang="es", source_url=r["url"], source_timestamp=r["timestamp"])
            if speaker:
                add_speaker(speaker, year, r["url"], position=position)
            used(r, f"MEC iCal export of an event with no captured event page -> events (local time, no UTC shift): {desc}")
    handle_home_en_2025(en_home_rows)


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main() -> None:
    all_rows = ALL_ROWS
    rows = [r for r in all_rows if r["kind"] == "page" or r["url"] in EXTRA_URLS]
    event_urls = {r["url"] for r in all_rows if r["kind"] == "event"}
    by_url: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_url[r["url"]].append(r)
    in_scope = len(rows)

    handled: set[str] = set()

    def take(pred) -> dict[str, list[dict]]:
        out = {}
        for u, grp in by_url.items():
            if u in handled:
                continue
            if pred(u):
                out[u] = grp
                handled.add(u)
        return out

    # 1. skip rules
    for u, grp in list(by_url.items()):
        p = path_of(u)
        if u.startswith("https://institucional.us.es/"):
            for r in grp:
                skipped(r, INSTITUCIONAL_SKIP)
            handled.add(u)
            continue
        for rx, why in SKIP_RULES:
            if re.search(rx, p):
                for r in grp:
                    skipped(r, why)
                handled.add(u)
                break

    # 2. home versions
    home = take(lambda u: u == SITE + "/")
    handle_home(home[SITE + "/"])

    # 3. 2025 home first (edition 2025 must exist), then iCal exports (also yields the English 2025 home)
    inicio = take(lambda u: u == SITE + "/es/inicio/")
    handle_inicio_2025(inicio[SITE + "/es/inicio/"])
    ical = take(lambda u: "method=ical" in u)
    handle_ical([r for grp in ical.values() for r in grp], event_urls)

    # 4. edition archive pages (after the iCal exports so the calendars enrich them instead of duplicating)
    for p, year in ARCHIVE_PAGES.items():
        grp = take(lambda u, p=p: u == SITE + p)
        if SITE + p in grp:
            handle_archive_page(grp[SITE + p], year)
    px = take(lambda u: u == SITE + "/programa-x-edicion/")
    if SITE + "/programa-x-edicion/" in px:
        handle_programa_x(px[SITE + "/programa-x-edicion/"])

    # 5. 2025 site
    about_en = take(lambda u: u == SITE + "/about-us/")
    about_es = take(lambda u: u == SITE + "/es/sobre-nosotros/")
    handle_about(about_en[SITE + "/about-us/"], "en")
    handle_about(about_es[SITE + "/es/sobre-nosotros/"], "es")
    cron = take(lambda u: u == SITE + "/es/cronograma/")
    sched = take(lambda u: u == SITE + "/schedule/")
    eventos = take(lambda u: u == SITE + "/es/eventos/")
    handle_cronograma_2025(cron[SITE + "/es/cronograma/"], eventos.get(SITE + "/es/eventos/", []), sched.get(SITE + "/schedule/", []))
    fotos = take(lambda u: u == SITE + "/es/fotos/")
    fotos_en = take(lambda u: u in (SITE + "/fotos-2/", SITE + "/photos/"))
    handle_fotos_2025(fotos[SITE + "/es/fotos/"], [fotos_en[k] for k in sorted(fotos_en)])
    cuest = take(lambda u: u == SITE + "/es/cuestionario/")
    handle_cuestionario_2025(cuest[SITE + "/es/cuestionario/"])
    en_events = take(lambda u: u == SITE + "/en/events/")
    for r in en_events.get(SITE + "/en/events/", []):
        skipped(r, "/en/events/ (The Events Calendar, 2024): the listing is rendered by JavaScript, the capture only holds the navigation")

    # 6. Astra pages
    grp = take(lambda u: u == SITE + "/en/innosoft-days-english/")
    for u, rs in grp.items():
        r = latest(rs)
        s = soup_any(r)
        node = content_node(s)
        html = clean_node(node, lang="en")
        pages.append({"edition_year": 2024, "title": "InnoSoft Days XII (English home)", "url": r["url"], "content_html": html, "kind": "about",
                      "source_url": r["url"], "source_timestamp": r["timestamp"]})
        add_edition(2024, sources=[r["url"]], notes="English home /en/innosoft-days-english/ confirms 5 to 8 November 2024, theme sustainability.")
        for uu in img_urls(node):
            fs = full_size(uu)
            add_media(uu, "poster", 2024, POSTER_CAPTIONS.get(Path(fs).name, "Cartel " + Path(fs).stem.replace("-", " ")), r["url"])
        cover_versions(rs, r, "English 2024 home copy -> pages (about, en)")

    handle_como_llegar(take(lambda u: u == SITE + "/como-llegar/")[SITE + "/como-llegar/"], "es")
    handle_como_llegar(take(lambda u: u == SITE + "/en/find-us/")[SITE + "/en/find-us/"], "en")

    # 2020 online access
    grp = take(lambda u: u == SITE + "/acceso-online-innosoft-days/")
    for u, rs in grp.items():
        r, s, html = astra_page(rs, "other", 2020, title="Acceso Online", what="2020 online-edition access page -> pages (other) + edition 2020 (online venue)")
        add_edition(2020, venue="Online (retransmisión por Twitch, twitch.tv/innosoftdays)",
                    description_html=html, sources=[r["url"]],
                    notes="/acceso-online-innosoft-days/ describes the Twitch access of the fully online 2020 edition.")

    # 2021 satisfaction surveys
    grp = take(lambda u: u == SITE + "/encuestas-de-satisfaccion/")
    for u, rs in grp.items():
        r, s, html = astra_page(rs, "other", 2021, title="Encuestas de satisfacción", what="2021 satisfaction survey links (one per talk, per day) -> pages (other) + edition 2021 dates")
        cn = content_node(s)
        text = text_of(cn)
        days = re.findall(r"(Lunes|Martes|Miércoles|Jueves|Viernes)\s+(\d{1,2})\s+de\s+noviembre", text)
        nums = sorted(int(d) for _, d in days)
        n_items = len([li for li in cn.select("li") if li.find("a") is not None])
        add_edition(2021, starts_on=f"2021-11-{nums[0]:02d}" if nums else None, ends_on=f"2021-11-{nums[-1]:02d}" if nums else None,
                    venue="Escuela Técnica Superior de Ingeniería Informática, Sevilla",
                    summary="Edición IX (2021), lunes 8, miércoles 10, lunes 15 y miércoles 17 de noviembre de 2021, dedicada a la ciberseguridad: " + f"{n_items} charlas, talleres y torneos con encuesta de satisfacción por actividad.",
                    sources=[r["url"]], confidence="medium",
                    notes=f"Dates are the four days listed on /encuestas-de-satisfaccion/ (8, 10, 15, 17 November 2021; {n_items} activities with a survey link); venue from the MEC iCal exports of the 2021 events (LOCATION: Escuela Técnica Superior de Ingeniería Informática, Sevilla).")

    # sustainability / equality
    sust = {
        SITE + "/que-hacemos-xi/": ("sustainability", 2023, "¿Qué hacemos? (Comité de Sostenibilidad)", "es"),
        SITE + "/en/what-do-we-do-sustainability-xii/": ("sustainability", 2023, "What do we do (sustainability)", "en"),
        SITE + "/noticias-de-sostenibilidad/": ("sustainability", 2024, "Noticias de sostenibilidad", "es"),
        SITE + "/en/sustainability-news/": ("sustainability", 2024, "Sustainability news", "en"),
        SITE + "/buscadores-sostenibles/": ("sustainability", 2023, "Buscadores sostenibles", "es"),
        SITE + "/en/sustainable-search-engines/": ("sustainability", 2024, "Sustainable search engines", "en"),
        SITE + "/igualdad-xi/": ("other", 2023, "¿Qué hacemos? (Comité de Igualdad)", "es"),
        SITE + "/noticias-de-igualdad/": ("other", 2023, "Noticias de Igualdad", "es"),
    }
    for u, (kind, year, title, lang) in sust.items():
        grp = take(lambda x, u=u: x == u)
        if u in grp:
            astra_page(grp[u], kind, year, title=title, what=f"{kind} page -> pages ({year})", lang=lang)
    oddities.append("/en/what-do-we-do-sustainability-xii/ is titled XII but its body is the XI (2023) text: '6 to 10 November', 'Sustainable Gymkana (7/11/2023)'; assigned edition_year 2023 like /que-hacemos-xi/.")
    oddities.append("/buscadores-sostenibles/ was published 2023-10-20 and edited 2024-10-29; assigned 2023 (first edition it served), its English twin /en/sustainable-search-engines/ (created 2024) to 2024.")

    # TDAH
    tdah = take(lambda u: path_of(u).startswith("/tdah/"))
    for u in sorted(tdah):
        astra_page(tdah[u], "other", 2024, what="TDAH information page (Comité de Igualdad XII) -> pages (other, 2024)")

    # games
    games = take(lambda u: re.search(r"/(crucigrama[^/]*|en/hardware-crossword|haz-tu-wordle-diario|juego-ahorcado|adivina-el-logo|innosoft-ctf)/$", u))
    handle_games(games)

    # talk poster pages (2022)
    talks = take(lambda u: re.search(r"/(informacion-sobre-la-ponencia-[^/?]*|carlos-perez|maria-jose-escalona|prise|red-hat|tragsatec)/$", u))
    handle_talk_pages(talks)
    variants = take(lambda u: re.search(r"/informacion-sobre-la-ponencia-del-sr/\?", u))
    for u, rs in variants.items():
        for r in rs:
            skipped(r, "query-string variant (utm / hss_channel) of /informacion-sobre-la-ponencia-del-sr/ with the same poster images")

    # attachment pages of the interim 2025 site
    att = take(lambda u: re.search(r"/(ajedrez|brawlhalla|torneo|gymkana|gymkhana|libnamic|manuel-jesus-flores-montano)/$", u))
    handle_attachment_pages(att)

    # TEC category / tag listings (2024)
    tec = take(lambda u: re.search(r"/events/(categoria|etiqueta)/", u))
    handle_tec_listings(tec)

    # anything left over
    for u, grp in sorted(by_url.items()):
        if u in handled:
            continue
        for r in grp:
            skipped(r, "not classified by pages_editions (left over; check scope)")
        oddities.append(f"LEFTOVER url not handled: {u}")

    # 2024 registration url + finishing touches
    add_edition(2024, registration_url=SITE + "/en/tickets-store/", sources=[SITE + "/en/tickets-store/"],
                notes="Registration: the XII site had an Eventin ticket store (/en/tickets-store/, 'Event Attendance ... download the ticket at the end of the purchase') per activity.")
    for y, e in editions.items():
        e["description_html"] = sync_media_urls(e["description_html"] or "")
        e["sources"] = list(dict.fromkeys(e["sources"]))
        e.pop("_conf_set", None)
    for e in events:
        e["description_html"] = sync_media_urls(e["description_html"] or "")
    for p in pages:
        p["content_html"] = sync_media_urls(p["content_html"] or "")

    # speakers already carried by another family are not repeated here
    kept_speakers = []
    for s in speakers:
        hit = OTHERS.speaker_match(s["name"])
        if hit:
            dropped_speakers.append(f"{s['name']} ({', '.join(str(y) for y in s['edition_years'])}) -> {hit}")
        else:
            kept_speakers.append(s)

    # write outputs
    eds = [editions[y] for y in sorted(editions)]
    evs = sorted(events, key=lambda e: (e["edition_year"] or 0, e["starts_at"] or "", e["title"]))
    sps = sorted(kept_speakers, key=lambda s: (min(s["edition_years"]), norm_key(s["name"])))
    pgs = sorted(pages, key=lambda p: (p["edition_year"] or 0, p["url"]))
    med = list(media.values())
    dump_part(f"{FAMILY}.editions.json", eds)
    dump_part(f"{FAMILY}.events.json", evs)
    dump_part(f"{FAMILY}.speakers.json", sps)
    dump_part(f"{FAMILY}.pages.json", pgs)
    dump_part(f"{FAMILY}.media.json", med)
    write_notes(in_scope, eds, evs, sps, pgs, med)
    print(json.dumps({"in_scope": in_scope, "used": len(notes_used), "skipped": len(notes_skipped),
                      "editions": len(eds), "events": len(evs), "speakers": len(sps), "pages": len(pgs), "media": len(med)}, ensure_ascii=False))


def write_notes(in_scope, eds, evs, sps, pgs, med) -> None:
    per_year = defaultdict(lambda: defaultdict(int))
    for e in eds:
        per_year[e["year"]]["editions"] += 1
    for e in evs:
        per_year[e["edition_year"]]["events"] += 1
    for s in sps:
        for y in s["edition_years"]:
            per_year[y]["speakers"] += 1
    for p in pgs:
        per_year[p["edition_year"]]["pages"] += 1
    for m in med:
        per_year[m["edition_year"]]["media"] += 1
    L = []
    L.append(f"# {FAMILY}\n")
    L.append("Site pages (kind=page in the manifest, plus /es/eventos and /en/events from the event-index kind) that describe the event itself: every version of the home page, the roman-numeral edition archive pages (/v-edicion/ .. /xi-edicion/ and /programa-x-edicion/), the 2025 Blocksy/Elementor site (home, about, schedule, events listing, photo galleries, questionnaire), the Astra site's informative pages (how to get there, online access 2020, satisfaction surveys 2021, sustainability and equality pages, TDAH, online games, 2022 talk poster pages), the Twenty Twenty-Five attachment pages, The Events Calendar category listings and the MEC iCal exports served under `?method=ical&id=N`.\n")
    L.append("## Coverage\n")
    L.append(f"- Captures in scope: {in_scope} ({len(notes_used)} used or covered by an identical/later version, {len(notes_skipped)} skipped with a reason below).")
    L.append(f"- Editions: {len(eds)}; events: {len(evs)}; speakers: {len(sps)}; pages: {len(pgs)}; media: {len(med)}.")
    L.append("- The latest capture of each URL is used; every other capture of the same URL is hashed on its entry-content text and reported as 'same content' or 'older/different version'. Where different versions describe different editions (home page, /como-llegar) each version is extracted with its own year.")
    L.append(f"- Cross-family rule: events and speakers already extracted by another family are not repeated here. Other families read at run time: {', '.join(OTHERS.loaded) or 'none (parts missing: everything emitted)'}. An event matches when it has the same title (loose key ignoring 'Conferencia –' / 'Taller –' prefixes, or the same word set) on the same date, or the same event URL / slug; a speaker matches by name (same_person). {len(covered_events)} calendar slots and {len(dropped_speakers)} speakers were left to the other families (lists below).\n")
    L.append("## Per year\n")
    for y in sorted(per_year, key=lambda v: (v is None, v or 0)):
        c = per_year[y]
        L.append(f"- {y}: " + ", ".join(f"{k} {c[k]}" for k in ("editions", "events", "speakers", "pages", "media") if c[k]))
    L.append("")
    L.append("## Editions\n")
    for e in eds:
        L.append(f"- {e['year']} ({e['roman']}): {e['starts_on']} to {e['ends_on']}, venue: {e['venue']}, confidence {e['confidence']}. {e['notes']}")
    L.append("")
    L.append("## What was extracted from where\n")
    L.append("- `/` versions: 2022-10-23 x2 placeholder (skipped), 2022-11-07 = X edition copy (8, 10 and 11 November 2022, ETSII, software libre, timetable and poster images), 2024-03-21 (gzip) / 2024-06-16 / 2024-07-25 / 2024-08-09 = XI copy (6, 8 and 9 November 2023, IA, poster Cartel-XI, presentation video), 2024-11-13 / 2025-02-07 / 2025-02-14 / 2025-02-27 (gzip) = XII copy (5 to 8 November 2024, sostenibilidad, seven activity posters), 2025-04-21 .. 2025-11-01 = interim placeholder (skipped).")
    L.append("- Edition archive pages: `/v-edicion/` (2017: '6 y 9 de noviembre de 2017', old logo, V poster, MEC daily calendar with 19 slots), `/vi-edicion/` (2018: '12, 13 y 16 de noviembre', 23 slots), `/vii-edicion/` (2019: '4, 5 y 6 de noviembre', 18 slots), `/viii-edicion/` (2020: '24, 26 y 27 de noviembre de 2020', posters of the three days, MEC monthly calendar with 22 slots on Twitch, four photos), `/ix-edicion/` (2021: '8, 10, 15 y 17 de noviembre de 2021', poster cartelfinal, logo, triptych programme, three activity posters), `/x-edicion/` (2022: '8, 9, 10 y 11 de noviembre de 2022', software libre, mascot Ping-U, video, Facebook post, timetable poster innosoft10_horario, 31 slots), `/xi-edicion/` (2023: 'del 6 al 9 de noviembre de 2023', IA, mascot Synthia, Cartel-XI, video, 25 slots). Each page -> edition (dates, summary, description_html = page copy + the calendar rendered as a 'Programa' list with day/time/room/link) + media (logos, posters, mascots, photos, videos). The calendar slots that no other family extracted become events (see 'Events added from the calendars'); the rest are listed as covered. `/programa-x-edicion/` (gzip capture, MEC monthly calendar of the X programme, 30 slots) is cross-checked the same way.")
    L.append("- `/es/inicio` (4 identical versions) = XIII home (4-6 November 2025, ETSII) -> edition 2025 description; the English XIII home only survives under `?method=ical&id=...` URLs (MEC gone, WordPress served the front page, canonical https://www.innosoftdays.com/) -> pages (about, url = canonical, source_url = the iCal URL).")
    L.append("- `/about-us`, `/es/sobre-nosotros` -> pages (about, 2025). `/es/cronograma` (+ `/schedule` EN cross-check) -> 2025 events with day, time, room and poster; `/es/eventos` adds descriptions, links, Andreas Zeller's bio and the speakers named inside the company talks (José Carlos Moral Cuevas / NTT Data, Jorge Martos / Indra, Mario Jiménez Calderón / CaixaBank Tech, Rebeca Sarai González Guerra); `/es/fotos` (latest of 3 versions, superset of `/fotos-2` and `/photos`) -> media photos grouped by activity; `/es/cuestionario` -> pages (other).")
    L.append("- `/como-llegar` 2024-09 version says 'Las XI jornadas' (2023) and 2024-12 'Las XII jornadas' (2024): both extracted; `/en/find-us` (12th edition) -> 2024.")
    L.append("- `/acceso-online-innosoft-days` -> 2020 page + online venue of the 2020 edition (dates come from `/viii-edicion/`). `/encuestas-de-satisfaccion` -> 2021 page (26 activities with a survey link) + edition dates (8, 10, 15, 17 November 2021).")
    L.append("- Sustainability / equality: `/que-hacemos-xi`, `/en/what-do-we-do-sustainability-xii` (2023 text), `/noticias-de-sostenibilidad`, `/en/sustainability-news`, `/buscadores-sostenibles`, `/en/sustainable-search-engines`, `/igualdad-xi`, `/noticias-de-igualdad` -> pages. Post embeds inside them are turned into plain links.")
    L.append("- `/tdah`, `/tdah/tdah-servicios`, `/tdah/tdah-recursos-tecnologicos`, `/tdah/tdah-becas-y-ayudas` -> pages (other, 2024).")
    L.append("- Games (crosswords incl. `/en/hardware-crossword`, `/haz-tu-wordle-diario`, `/juego-ahorcado`, `/adivina-el-logo`, `/innosoft-ctf`) -> events (kind other, modality online, year = first publication from the Yoast graph, link = page URL). Crossword pages hold only a morepuzzles.com iframe (kept, emptied of its escaped fallback text). `/adivina-el-logo` is a Quiz and Survey Master form: the five questions (image + options) are rendered as an ordered list; the Wordle event spans its first and last published word as full datetimes.")
    L.append("- 2022 'Información sobre la ponencia ...' pages (15 URLs incl. `/carlos-perez`, `/maria-jose-escalona`, `/prise`, `/red-hat`, `/tragsatec`): image-only posters -> pages (other, 2022) + poster media. The speaker names of the titles are all carried by the people family (with affiliations), so they are not repeated in speakers.json here (list below). The Sancho Lerena posters are the only ones the archive holds as files (uploads/2022/11/1-22.png, 2-22.png); their text (CEO y fundador de Ártica / Pandora FMS, 8 November 2022 09:30-10:30 online, talk abstract) was transcribed by hand into that page.")
    L.append("- Twenty Twenty-Five attachment pages (`/ajedrez`, `/brawlhalla`, `/torneo`, `/gymkana`, `/gymkhana`, `/libnamic`, `/manuel-jesus-flores-montano`) -> media only (one image each, year from the upload path).")
    L.append("- The Events Calendar category / tag listings (`/events/categoria/*`, `/events/etiqueta/*`, 2024): the JSON-LD block plus the rendered articles (month grid tooltips, list and mobile views: title, date, times, description) of each view are read and matched against the other families. Every event is a single event capture already extracted by events_eventos_etn (the TEC umbrella `mentoria-2` = /event/mentoria/ and the Eventin mentoring shifts, `yincana-coles` = /eventos/yincana-coles/) except 'Final Torneo CS2' (6 Nov 2024 13:30-14:30, played online and streamed), which events_eventos_etn only has as the undated listing stub 'Torneo CS2 (Final)': it is emitted here with its date (only event from these listings).")
    L.append("- `?method=ical&id=N`: 45 MEC iCal exports (2017 to 2024). MEC writes the local time with a fake 'Z' (iCal 2510 165000Z = 16:50 on the MEC page, 2734 083000Z = 08:30 in the 2021 calendar), so DTSTART/DTEND are read as naive Europe/Madrid without conversion. Exports whose event page was captured, or whose event another family already extracted (Prometheus/Grafana talk and drone raffle 2018 = institucional, Pablo Pino 2024 = events_eventos_etn), are listed as skipped; the remaining ones (2017 Scratch and Docker workshops, 2020 opening) become events here and are enriched with the room of the archive calendar. The remaining iCal URL captures are the interim placeholder or the 2025 English home.")
    L.append("- Media URLs: the full-size upload when the archive captured it, else the sized variant the page used when that one was captured (2022/11/horario-1024x1024.jpg, 2024/10/cartel6-816x1024.webp), else the full-size URL; the <img> sources inside description_html/content_html point at the same URL.")
    L.append("")
    L.append("## Events added from the calendars (no other family has them)\n")
    for e in evs:
        if e["source_url"] and re.search(r"-edicion/$|programa-x-edicion/$", e["source_url"]):
            L.append(f"- {e['edition_year']} {e['starts_at']} to {e['ends_at']}: '{e['title']}' ({e['kind']}, room {e['room']}, speaker {e['speaker']}, company {e['company']}, link {e['link']}) from {e['source_url']}")
    L.append("")
    L.append("## Calendar / iCal slots left to other families\n")
    for l in covered_events:
        L.append(f"- {l}")
    L.append("")
    L.append("## Speakers left to other families\n")
    for l in dropped_speakers:
        L.append(f"- {l}")
    L.append("")
    L.append("## Not extracted here (covered by other families)\n")
    L.append("- institucional.us.es captures (home 2019, /programa/ 2018, /programa-ix-edicion/ 2021): institucional family.")
    L.append("- Organisation pages `/organizacion-ix-edicion/`, `/organizacion-xi-edicion/`, `/organizacion-xii-edicion/`, `/en/xii-edition-organization/`: people family (organisers.json).")
    L.append("- Eventin category listings `/etn_category/*`, empty `/etn_category-N/` and `/mec-category/*` archives: events_eventos_etn family. `/en/tickets-store/` only used as the 2024 registration_url.")
    L.append("")
    L.append("## Oddities\n")
    for o in oddities:
        L.append(f"- {o}")
    L.append("- The 2022 home copy (7 Nov 2022) says '8, 10 y 11 de noviembre' (the days with talks) while `/x-edicion/` says '8, 9, 10 y 11' (9 November had the Brawlhalla tournament and gymkhana); starts_on/ends_on are 8 to 11 either way. Both copies are concatenated in the 2022 description_html (home first, archive after).")
    L.append("- `/x-edicion/` calendar 'Charla de Oficina de Software Libre' (8 Nov 2022 16:30-17:30) links /events/charla-del-sr-pablo-garcia-sanchez/ (never captured): speaker taken from that slug. 'Ajedrez' (10 Nov 2022 11:30-12:30) is the chess tournament the posts_2022 family lists undated as 'Torneo de ajedrez'.")
    L.append("- `/viii-edicion/` calendar 'Behaviour Driven Development and Chaos Engineering' (24 Nov 2020 19:00-20:00, Twitch) is the talk the posts_2018_2020 family lists date-only under its Spanish title 'Desarrollo Impulsado por la Ingeniería del Caos'; kept here because the titles differ (it adds the time).")
    L.append("- The `/v-edicion/` calendar markup is malformed (unclosed divs nest the articles and misplace the JSON-LD scripts); titles, times and rooms are read per article and organizers matched by event name.")
    L.append("- Three raw captures are gzip-compressed on disk (`/` 2024-03-21 and 2025-02-27, `/programa-x-edicion/` 2022-11-07); `read_html_any()` in common.py transparently gunzips them.")
    L.append("- The 2025 photo URLs are the metaslider 2000x1000 crops (`...-scaled-2000x1000.jpg`); no 2025/11 upload was captured by the archive, so the importer will not find them locally.")
    L.append("- 2025 timetable: `/es/cronograma` lists 'Escape Room - El Enigma de Grace' twice on Tuesday (9:30-12:30 and 15:30-17:30) and 'Game Jam' / 'Torneo - RogueLikes' on both days; kept as separate events. Andreas Zeller's second talk (Friday 7, doctorate programme) is only a link, not an InnoSoft slot.")
    L.append("- The `/en/what-do-we-do-sustainability-xii/` and `/que-hacemos-xi/` texts describe the 2023 sustainability stand activities (gymkana 7/11/2023, punto limpio, huerto urbano, cuestionario, aviones de papel); the stand itself is a MEC event (iCal 5134, 2023-11-06) so no events were created from them.")
    L.append("- The decorative cover background of `/x-edicion/` (uploads/2023/10/BannerEventBrite.png) is dropped from the description and not listed as media.")
    L.append("")
    L.append("## Captures used or covered\n")
    for l in sorted(notes_used):
        L.append(f"- {l}")
    L.append("")
    L.append("## Captures skipped (with reason)\n")
    for l in sorted(notes_skipped):
        L.append(f"- {l}")
    L.append("")
    (HERE / "data" / "extracted" / "parts").mkdir(parents=True, exist_ok=True)
    (HERE / "data" / "extracted" / "parts" / f"{FAMILY}.notes.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
