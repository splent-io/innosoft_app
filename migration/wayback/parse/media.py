#!/usr/bin/env python3
"""Family media: the media library of every past edition.

Scope
- every fetched capture with kind=upload or kind=file (WordPress uploads:
  posters, photos, logos, PDFs, one video), and
- every image / PDF / video referenced from the HTML captures (page, post,
  event, event-index, speaker) of both hosts.

Output (data/extracted/parts/media.media.json, README schema):
  [{"url", "kind" (poster|photo|logo|other), "edition_year", "caption",
    "used_by": [source urls]}]

One entry per IMAGE, not per URL: WordPress emits a size variant per
breakpoint (name-300x200.jpg, name-1024x683.jpg, name-scaled.jpg ...) and
listing them all would put the same poster seven times in the media library
(the importer is idempotent by URL). Variants are grouped under their base
name and the entry's url is the best URL the importer can actually resolve:
the fetched original, else the largest fetched variant, else (nothing
fetched) the largest URL the site referenced, so a second fetch pass knows
what to get.

Deterministic, offline, rerunnable: python3 parse/media.py
"""

from __future__ import annotations

import collections
import glob
import html as htmlmod
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import (  # noqa: E402
    EXTRACTED, MANIFEST, RAW, dump_part, manifest_rows, norm_media_url, norm_url, read_html, soup_of, text_of,
)

FAMILY = "media"
HTML_KINDS = {"page", "post", "event", "event-index", "speaker"}
MEDIA_KINDS = {"upload", "file"}

IMG_EXTS = ("png", "jpg", "jpeg", "gif", "webp", "svg", "avif", "bmp")
DOC_EXTS = ("pdf",)
VID_EXTS = ("mp4", "webm", "mov", "m4v", "ogv", "mp3", "ogg", "wav")
MEDIA_EXTS = IMG_EXTS + DOC_EXTS + VID_EXTS
EXT_RE = re.compile(r"\.(" + "|".join(MEDIA_EXTS) + r")$", re.I)

HOME_URLS = {"https://www.innosoftdays.com/", "https://institucional.us.es/innosoft/"}

# Site chrome (header, footer, menus, sidebars): images found only there are
# theme logos / favicons, not content of a page.
CHROME_SELECTORS = [
    "header#masthead", "header.site-header", "header.ct-header", "header[data-elementor-type]",
    "header[role=banner]", ".elementor-location-header", "[data-elementor-type=header]",
    "footer#colophon", "footer.site-footer", "footer.ct-footer", "footer[data-elementor-type]",
    "footer[role=contentinfo]", ".elementor-location-footer", "[data-elementor-type=footer]",
    "#masthead", "#colophon", ".site-header", ".site-footer", ".ast-mobile-header-wrap",
    ".ast-above-header-wrap", ".ast-below-header-wrap", ".ast-primary-header-bar", "#header", "#footer",
    ".ct-header", ".ct-footer", "nav", "aside", ".widget-area", "#secondary", ".sidebar", ".site-branding",
    ".ast-mobile-popup-drawer", "#ast-mobile-header", ".ast-header-break-point .main-header-bar-wrap",
    ".widget", ".widget_media_image", ".mec-single-event .col-md-4",
]

# WordPress / plugin photo galleries (a class token of an ancestor, body excluded)
GALLERY_CLASS_RE = re.compile(
    r"^(wp-block-gallery|blocks-gallery-\w+|gallery|gallery-\d+|modula-gallery|modula-items|modula-item|"
    r"tiled-gallery|envira-gallery\w*|foogallery\w*|ngg-\w+|metaslider|ms-image|elementor-image-carousel|"
    r"elementor-image-gallery|elementor-gallery\w*|wp-block-jetpack-slideshow\w*|slides|slide-\d+)$",
    re.I,
)
HEADINGS = ["h1", "h2", "h3", "h4", "h5"]

# Any upload URL of the two hosts (absolute; the sites never used relative
# ones for media). Query strings and fragments are stripped later.
UPLOAD_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:innosoftdays\.com|institucional\.us\.es/innosoft)/wp-content/uploads/[^\s\"'<>()\\,]+",
    re.I,
)
SIZE_RE = re.compile(r"-(\d{2,4})x(\d{2,4})(?=\.[a-z0-9]+$)", re.I)
SCALED_RE = re.compile(r"-scaled(?=\.[a-z0-9]+$)", re.I)

POSTER_WORDS = ("cartel", "poster", "flyer", "banner", "programa", "horario", "portada", "insta", "torneo",
                "concurso", "yincana", "gymkana", "gymkhana", "sabias", "my-project", "diseno-sin-titulo",
                "publicacion", "story", "stories", "evento", "charla", "taller", "jornadas", "mentoria")
PHOTO_WORDS = ("img_", "img-", "dsc", "pxl_", "whatsapp", "foto", "photo", "_mg_", "picture", "jammers",
               "retrato", "headshot", "avatar", "perfil")
LOGO_WORDS = ("logo", "isotipo", "favicon", "cropped-", "icono", "icon-", "escudo", "marca")
PHOTO_PAGE_RE = re.compile(r"\b(fotos|fotograf|im[aá]genes|images|photos|galer[ií]a|gallery)\b", re.I)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def squash(t: str | None) -> str:
    return re.sub(r"\s+", " ", t or "").strip()


def strip_query(url: str) -> str:
    return url.split("?")[0].split("#")[0]


def canonical_variant(url: str) -> str:
    """norm_url form of a variant URL (https, www, host kept)."""
    return strip_query(norm_url(htmlmod.unescape(url).replace("\\/", "/")))


def group_key(url: str) -> str:
    """Base image of a WordPress size variant, on the current host so both
    hosts' copies of the pre-2021 uploads group together."""
    u = norm_media_url(canonical_variant(url))
    u = SIZE_RE.sub("", u)
    u = SCALED_RE.sub("", u)
    return u


def variant_area(url: str) -> int:
    """Ranking key: original > -scaled > -WxH (by pixel count)."""
    m = SIZE_RE.search(url)
    if m:
        return int(m.group(1)) * int(m.group(2))
    if SCALED_RE.search(url):
        return 2560 * 2560
    return 10 ** 9


def variant_dims(url: str):
    m = SIZE_RE.search(url)
    return (int(m.group(1)), int(m.group(2))) if m else None


def ext_of(url: str) -> str:
    m = EXT_RE.search(strip_query(url))
    return m.group(1).lower() if m else ""


def is_media_url(url: str) -> bool:
    return bool(EXT_RE.search(strip_query(url)))


def upload_year_month(url: str):
    m = re.search(r"/wp-content/uploads/(\d{4})/(\d{2})/", url)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def humanise(url: str) -> str:
    name = strip_query(url).rsplit("/", 1)[-1]
    name = re.sub(r"\.[a-z0-9]+$", "", name, flags=re.I)
    name = SIZE_RE.sub("", name + ".x")[:-2] if SIZE_RE.search(name + ".x") else name
    name = re.sub(r"-scaled$", "", name)
    name = re.sub(r"-e\d{13}$", "", name)
    name = re.sub(r"[-_]+", " ", name).strip()
    return name


ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10,
         "xi": 11, "xii": 12, "xiii": 13, "xiv": 14}


def load_parts_years() -> dict[str, int]:
    """source_url -> edition_year from the other families' parts (optional
    enrichment; the parser works without them)."""
    votes: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(str(EXTRACTED / "parts" / "*.json"))):
        if Path(f).name.startswith(FAMILY + "."):
            continue
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            y = item.get("edition_year")
            src = item.get("source_url") or item.get("url")
            if not y or not src or "wp-content" in str(src):
                continue
            for s in ([src] if isinstance(src, str) else src):
                votes[norm_url(s)][int(y)] += 1
            for s in item.get("sources") or []:
                votes[norm_url(s)][int(y)] += 1
    return {u: c.most_common(1)[0][0] for u, c in votes.items()}


def load_parts_media() -> dict[str, dict]:
    """group_key -> {"kind": Counter, "caption": Counter} from the other
    families' media parts (hand-picked kinds/captions win on conflict)."""
    out: dict[str, dict] = {}
    for f in sorted(glob.glob(str(EXTRACTED / "parts" / "*.media.json"))):
        if Path(f).name.startswith(FAMILY + "."):
            continue
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict) or not item.get("url"):
                continue
            k = group_key(item["url"])
            slot = out.setdefault(k, {"kind": collections.Counter(), "caption": collections.Counter()})
            if item.get("kind") in ("poster", "photo", "logo", "other"):
                slot["kind"][item["kind"]] += 1
            if item.get("caption"):
                slot["caption"][squash(item["caption"])] += 1
    return out


def page_year(url: str, parts_years: dict[str, int]):
    """Edition year a page talks about, from the other parts, then its URL."""
    if url in parts_years:
        return parts_years[url]
    m = re.search(r"/(20\d\d)/(\d\d)/\d\d/", url)
    if m:
        return int(m.group(1))
    slug = url.lower()
    m = re.search(r"(?:^|[/-])(i{1,3}|iv|vi{0,3}|ix|xi{0,3}|xiv)-edicion", slug)
    if m and m.group(1) in ROMAN:
        return 2012 + ROMAN[m.group(1)]
    m = re.search(r"/(?:mec-category|categoria|category)/(?:[^/]+/)?(20\d\d)(?:-\d\d)?/?$", slug)
    if m:
        return int(m.group(1))
    m = re.search(r"/(20\d\d)-(\d\d)/?$", slug)
    if m:
        return int(m.group(1))
    return None


# --------------------------------------------------------------------------
# reference extraction from one HTML capture
# --------------------------------------------------------------------------

class Ref:
    __slots__ = ("url", "ctx", "alt", "title", "caption", "gallery", "heading", "page_url", "page_kind", "page_title", "ts")

    def __init__(self, url, ctx, page, alt="", title="", caption="", gallery=False, heading=""):
        self.url = url
        self.ctx = ctx  # content | featured | gallery | chrome | favicon
        self.alt = squash(alt)
        self.title = squash(title)
        self.caption = squash(caption)
        self.gallery = gallery
        self.heading = squash(heading)
        self.page_url, self.page_kind, self.page_title, self.ts = page


def urls_in(text: str) -> list[str]:
    text = htmlmod.unescape(text).replace("\\/", "/")
    out = []
    for m in UPLOAD_URL_RE.finditer(text):
        u = strip_query(m.group(0)).rstrip(".;:")
        if is_media_url(u):
            out.append(u)
    return out


def img_urls(img) -> list[str]:
    urls = []
    for attr in ("src", "data-src", "data-lazy-src", "data-original", "data-full", "data-large_image", "data-orig-file", "data-large-file", "data-medium-file", "data-bg"):
        v = img.get(attr)
        if v and not v.startswith("data:"):
            urls.append(v)
    for attr in ("srcset", "data-srcset", "data-lazy-srcset"):
        v = img.get(attr)
        if v:
            for cand in v.split(","):
                parts = cand.strip().split()
                if parts:
                    urls.append(parts[0])
    return urls


def caption_near(img) -> str:
    fig = img.find_parent("figure")
    if fig is not None:
        fc = fig.find("figcaption")
        if fc is not None:
            return text_of(fc)
    wc = img.find_parent(class_=re.compile(r"wp-caption"))
    if wc is not None:
        t = wc.find(class_=re.compile(r"wp-caption-text"))
        if t is not None:
            return text_of(t)
    return img.get("data-caption") or ""


def in_gallery(img) -> bool:
    for p in img.parents:
        if p is None or p.name in ("body", "html", "[document]"):
            return False
        for c in p.get("class") or []:
            if GALLERY_CLASS_RE.match(c):
                return True
    return False


META_HEADING_RE = re.compile(r"^(hora|lugar|fecha|d[ií]a|sala|aula|time|place|date|room|cu[aá]ndo|d[oó]nde|when|where)\b", re.I)


def context_heading(img) -> str:
    """Heading that names the image on the page: the nearest previous
    heading inside the smallest block that holds both (skipping Hora/Lugar/
    Time/Room lines), else the first heading of that block (Elementor cards
    may put the image before the title)."""
    anc = None
    depth = 0
    for p in img.parents:
        if p is None or p.name in ("body", "html", "[document]"):
            break
        depth += 1
        if depth > 12:
            break
        if p.find(HEADINGS) is not None:
            anc = p
            break
    if anc is None:
        return ""
    for prev in img.find_all_previous(HEADINGS, limit=6):
        if not any(a is anc for a in prev.parents):
            break
        t = text_of(prev)
        if t and not META_HEADING_RE.match(t):
            return t
    for h in anc.find_all(HEADINGS):
        t = text_of(h)
        if t and not META_HEADING_RE.match(t):
            return t
    return ""


def refs_from_capture(row: dict) -> tuple[list[Ref], collections.Counter]:
    soup = soup_of(row)
    page_url = row["url"]
    ext_hosts: collections.Counter = collections.Counter()

    og_title = soup.find("meta", property="og:title")
    h1 = soup.find("h1")
    page_title = (og_title.get("content") if og_title else "") or text_of(h1) or (soup.title.string.strip() if soup.title and soup.title.string else "")
    page_title = squash(re.sub(r"\s*[-|–]\s*InnoSoft Days.*$", "", page_title or ""))
    page = (page_url, row["kind"], page_title, row["timestamp"])
    refs: list[Ref] = []

    # head: featured image + favicons
    if soup.head is not None:
        for meta in soup.head.find_all("meta"):
            prop = (meta.get("property") or meta.get("name") or "").lower()
            content = meta.get("content") or ""
            if prop in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
                for u in urls_in(content):
                    refs.append(Ref(u, "featured", page))
            elif prop == "msapplication-tileimage":
                for u in urls_in(content):
                    refs.append(Ref(u, "favicon", page))
        for link in soup.head.find_all("link"):
            rel = " ".join(link.get("rel") or []).lower()
            if "icon" in rel:
                for u in urls_in(link.get("href") or ""):
                    refs.append(Ref(u, "favicon", page))
        soup.head.decompose()

    body = soup.body or soup
    for s in body.find_all(["script", "style", "noscript", "template"]):
        s.decompose()

    # chrome: pull out header/footer/nav/aside first, sweep them for URLs
    chrome_html = []
    for sel in CHROME_SELECTORS:
        try:
            found = body.select(sel)
        except Exception:
            found = []
        for el in found:
            if el.parent is None:
                continue
            chrome_html.append(str(el))
            el.extract()
    for el in list(body.find_all(["header", "footer"], recursive=False)):
        chrome_html.append(str(el))
        el.extract()
    for u in urls_in("\n".join(chrome_html)):
        refs.append(Ref(u, "chrome", page))

    # content: DOM pass for <img>, <a>, <video>, then a sweep for the rest
    seen = set()
    for img in body.find_all("img"):
        gallery = in_gallery(img)
        alt, title, cap = img.get("alt") or "", img.get("title") or "", caption_near(img)
        heading = None
        for raw in img_urls(img):
            if UPLOAD_URL_RE.match(htmlmod.unescape(raw)):
                if heading is None:
                    heading = context_heading(img)
                for u in urls_in(raw):
                    refs.append(Ref(u, "gallery" if gallery else "content", page, alt, title, cap, gallery, heading))
                    seen.add(u)
            elif re.match(r"https?://", raw) and "innosoftdays" not in raw and "institucional.us.es" not in raw:
                if is_media_url(raw):
                    ext_hosts[re.match(r"https?://([^/]+)", raw).group(1).lower()] += 1
    for a in body.find_all("a", href=True):
        for u in urls_in(a["href"]):
            refs.append(Ref(u, "content", page, caption=text_of(a)))
            seen.add(u)
    for v in body.find_all(["video", "source", "audio", "embed", "object"]):
        for attr in ("src", "poster", "data"):
            for u in urls_in(v.get(attr) or ""):
                refs.append(Ref(u, "content", page))
                seen.add(u)
    for u in urls_in(str(body)):
        if u not in seen:
            refs.append(Ref(u, "content", page))
            seen.add(u)
    return refs, ext_hosts


# --------------------------------------------------------------------------
# aggregation
# --------------------------------------------------------------------------

class Group:
    def __init__(self, key: str):
        self.key = key
        self.variants: dict[str, dict] = {}  # canonical variant url -> {"fetched": bool, "indexed": bool}
        self.content_pages: set[str] = set()
        self.chrome_pages: set[str] = set()
        self.featured_pages: set[str] = set()
        self.gallery_pages: set[str] = set()
        self.favicon = False
        self.page_kinds: collections.Counter = collections.Counter()
        self.page_titles_featured: collections.Counter = collections.Counter()
        self.page_titles_content: collections.Counter = collections.Counter()
        self.captions: collections.Counter = collections.Counter()   # figcaption / link text
        self.alts: collections.Counter = collections.Counter()
        self.titles: collections.Counter = collections.Counter()
        self.headings: collections.Counter = collections.Counter()
        self.page_years: collections.Counter = collections.Counter()
        self.first_ts = "99999999999999"

    def add_variant(self, url: str, fetched=False, indexed=False):
        v = self.variants.setdefault(url, {"fetched": False, "indexed": False})
        v["fetched"] |= fetched
        v["indexed"] |= indexed

    @property
    def fetched_variants(self):
        return [u for u, v in self.variants.items() if v["fetched"]]

    @property
    def any_indexed(self):
        return any(v["indexed"] for v in self.variants.values())

    def best_url(self, manifest_urls: set[str]) -> str:
        fetched = self.fetched_variants
        if fetched:
            return sorted(fetched, key=lambda u: (-variant_area(u), u.startswith("https://institucional"), len(u), u))[0]
        return sorted(self.variants, key=lambda u: (-variant_area(u), u.startswith("https://institucional"), len(u), u))[0]

    def dims(self):
        best = None
        for u in self.variants:
            d = variant_dims(u)
            if d and (best is None or d[0] * d[1] > best[0] * best[1]):
                best = d
        return best


def is_trivial_text(t: str, key: str) -> bool:
    if not t:
        return True
    tl = t.strip().lower()
    if tl in ("image", "imagen", "img", "photo", "foto", "picture", "logo", "post", "screenshot", "captura",
              "descarga", "descargar", "download", "aqui", "aquí", "here", "click here", "pincha aqui", "pincha aquí",
              "ver", "ver mas", "ver más", "leer mas", "leer más", "read more", "enlace", "link", "pdf"):
        return True
    stem = humanise(key).lower()
    if tl.replace("-", " ").replace("_", " ") == stem:
        return True  # WordPress copies the file name into title/alt
    if re.fullmatch(r"[\w\-. ]+\.(png|jpe?g|webp|gif|pdf)", tl):
        return True
    if tl.startswith(("http://", "https://", "www.")) or re.fullmatch(r"\S+/\S+", tl):
        return True  # a link whose text is its own URL
    return False


def meaningless_stem(stem: str) -> bool:
    """File names that say nothing: camera counters (DSC04297, IMG_0386),
    messaging exports, timestamps, Twitter media ids, bare numbers."""
    h = stem.strip()
    if not h:
        return True
    hl = h.lower()
    if re.fullmatch(r"[\d\s\-.]*", h):
        return True
    if re.match(r"(dsc|dscn|dcim|img|imb|pxl|mvimg|p|pic|photo|image|imagen|foto|screenshot|captura|screen shot|whatsapp image|photo)\W*\d", hl):
        return True
    if "whatsapp" in hl or hl in ("captura", "captura de pantalla", "sin titulo", "untitled", "diseno sin titulo", "imagen", "image"):
        return True
    tokens = h.split()
    joined = "".join(tokens)
    if len(tokens) <= 3 and len(joined) >= 10:
        # every token is irregular (digits or inner case switches): a media id
        def irregular(t):
            if len(t) <= 2 or re.search(r"\d", t):
                return True
            return not re.fullmatch(r"[A-Z]?[a-z]+|[A-Z]+", t)  # not a plain word shape
        if all(irregular(t) for t in tokens):
            return True
    return False


def pick_caption(g: Group) -> str | None:
    key = g.key
    for counter in (g.captions, g.alts, g.titles):
        for text, _ in counter.most_common():
            if not is_trivial_text(text, key) and len(text) <= 200:
                return text
    if g.featured_pages and g.page_titles_featured:
        t = g.page_titles_featured.most_common(1)[0][0]
        if t:
            return t
    stem = humanise(key)
    if not g.content_pages and (g.favicon or meaningless_stem(stem)):
        return "InnoSoft Days"  # site chrome without a usable name (favicon, the 2022 logo IMG_0386)
    if g.content_pages and (meaningless_stem(stem) or ext_of(key) not in IMG_EXTS):
        for counter in (g.headings, g.page_titles_content):
            for text, _ in counter.most_common():
                if text and not is_trivial_text(text, key) and len(text) <= 200:
                    return text
    return stem or None


def classify_kind(g: Group) -> str:
    key = g.key
    name = key.rsplit("/", 1)[-1].lower()
    ext = ext_of(key)
    if ext in DOC_EXTS or ext in VID_EXTS:
        return "other"
    if g.favicon or any(w in name for w in LOGO_WORDS):
        return "logo"
    if g.chrome_pages and not g.content_pages:
        return "logo"
    if any(w in name for w in PHOTO_WORDS):
        return "photo"
    photo_page = any(PHOTO_PAGE_RE.search(t) for t in list(g.page_titles_content) + list(g.page_titles_featured))
    if photo_page and not any(w in name for w in ("cartel", "poster", "flyer")):
        return "photo"
    if any(w in name for w in POSTER_WORDS):
        return "poster"
    if any("/eventos/" in p for p in g.content_pages):
        return "photo"  # EventON (2024) events carry the speaker's photo as featured image
    d = g.dims()
    portrait = d is not None and d[1] >= d[0] * 1.15
    square = d is not None and abs(d[0] - d[1]) <= max(d) * 0.05
    if g.featured_pages and g.page_kinds.get("event", 0) and not photo_page:
        return "poster"
    if photo_page:
        return "photo"
    if g.gallery_pages and not portrait:
        return "photo"
    if portrait or square:
        return "poster"
    if ext in ("jpeg", "jpg"):
        return "photo"
    return "other"


def edition_year_of(g: Group) -> int | None:
    """Majority year of the pages that use the image; the upload path
    (/uploads/YYYY/MM/) breaks ties and covers unreferenced uploads."""
    y, m = upload_year_month(g.key)
    if g.page_years:
        ranked = g.page_years.most_common()
        top = ranked[0][1]
        tied = [yy for yy, n in ranked if n == top]
        if len(tied) == 1:
            return tied[0]
        if y in tied:
            return y
        return sorted(tied)[0]
    return y


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    parts_years = load_parts_years()
    parts_media = load_parts_media()
    manifest = manifest_rows()
    media_rows = [r for r in manifest if r["kind"] in MEDIA_KINDS]
    html_rows = [r for r in manifest if r["kind"] in HTML_KINDS]
    manifest_urls = {r["url"] for r in manifest}

    # errored media captures (fetch failed) for the notes
    errored: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        if m.get("kind") in MEDIA_KINDS and m.get("error"):
            errored[norm_url(m["url"])] = m["error"]

    # CDX index: every upload the archive knows (status 200)
    indexed: dict[str, list[dict]] = collections.defaultdict(list)
    for line in (RAW.parent / "index.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("kind") in MEDIA_KINDS and r.get("statuscode") == "200":
            indexed[strip_query(norm_url(r["original"]))].append(r)

    groups: dict[str, Group] = {}

    def group_for(url: str) -> Group:
        k = group_key(url)
        g = groups.get(k)
        if g is None:
            g = groups[k] = Group(k)
        return g

    # 1) fetched uploads / files
    skipped: list[tuple[str, str]] = []
    fetched_in_scope = 0
    for r in media_rows:
        u = strip_query(r["url"])
        fetched_in_scope += 1
        if "/wp-content/uploads/" not in u:
            skipped.append((u, "plugin UI asset (kind=file), not event media"))
            continue
        if not is_media_url(u):
            skipped.append((u, "not a media file (Elementor stylesheet)"))
            continue
        g = group_for(u)
        g.add_variant(u, fetched=True, indexed=u in indexed)
        g.first_ts = min(g.first_ts, r["timestamp"])
    for u in indexed:
        if "/wp-content/uploads/" in u and is_media_url(u):
            group_for(u).add_variant(u, indexed=True)

    # 2) references from every HTML capture
    ext_hosts: collections.Counter = collections.Counter()
    refs_total = 0
    for r in html_rows:
        refs, hosts = refs_from_capture(r)
        ext_hosts.update(hosts)
        py = page_year(r["url"], parts_years)
        for ref in refs:
            refs_total += 1
            u = canonical_variant(ref.url)
            g = group_for(u)
            g.add_variant(u, fetched=u in manifest_urls, indexed=u in indexed)
            g.first_ts = min(g.first_ts, ref.ts)
            if ref.ctx in ("chrome", "favicon"):
                g.chrome_pages.add(ref.page_url)
                g.favicon |= ref.ctx == "favicon"
                continue
            g.content_pages.add(ref.page_url)
            g.page_kinds[ref.page_kind] += 1
            if py:
                g.page_years[py] += 1
            if ref.ctx == "featured":
                g.featured_pages.add(ref.page_url)
                if ref.page_title:
                    g.page_titles_featured[ref.page_title] += 1
            else:
                if ref.page_title:
                    g.page_titles_content[ref.page_title] += 1
            if ref.ctx == "gallery":
                g.gallery_pages.add(ref.page_url)
            if ref.caption:
                g.captions[ref.caption] += 1
            if ref.alt:
                g.alts[ref.alt] += 1
            if ref.title:
                g.titles[ref.title] += 1
            if ref.heading:
                g.headings[ref.heading] += 1

    # 2b) originals whose own name ends in -WxH (X-800x445.jpg) look like a
    # variant of X.jpg; the double-sized X-800x445-768x427.jpg proves the
    # sized name is the original: move that URL into the right group.
    for key in sorted(groups):
        if not SIZE_RE.search(key):
            continue
        parent_key = SIZE_RE.sub("", key)
        parent = groups.get(parent_key)
        if parent is None:
            continue
        g = groups[key]
        for u in list(parent.variants):
            if group_key(u) == parent_key and norm_media_url(u) == key:
                info = parent.variants.pop(u)
                g.add_variant(u, fetched=info["fetched"], indexed=info["indexed"])
        if not parent.variants:  # everything moved: the parent was a phantom
            for attr in ("content_pages", "chrome_pages", "featured_pages", "gallery_pages"):
                getattr(g, attr).update(getattr(parent, attr))
            for attr in ("page_kinds", "page_titles_featured", "page_titles_content", "captions", "alts", "titles", "headings", "page_years"):
                getattr(g, attr).update(getattr(parent, attr))
            g.favicon |= parent.favicon
            g.first_ts = min(g.first_ts, parent.first_ts)
            del groups[parent_key]

    # 3) entries
    items = []
    overridden = 0
    for key, g in groups.items():
        url = g.best_url(manifest_urls)
        if g.content_pages:
            used_by = sorted(g.content_pages)
        else:
            homes = sorted(p for p in g.chrome_pages if p in HOME_URLS)
            used_by = homes or sorted(g.chrome_pages)[:3]
        kind, caption = classify_kind(g), pick_caption(g)
        other = parts_media.get(key)
        if other:
            if other["kind"]:
                k2 = other["kind"].most_common(1)[0][0]
                overridden += k2 != kind
                kind = k2
            if other["caption"] and (not caption or caption == humanise(key)):
                caption = other["caption"].most_common(1)[0][0]
        items.append({
            "url": url,
            "kind": kind,
            "edition_year": edition_year_of(g),
            "caption": caption,
            "used_by": used_by,
        })
    print(f"kinds overridden by other families' media parts: {overridden} of {sum(1 for k in groups if k in parts_media)} shared images")
    items.sort(key=lambda i: (i["edition_year"] or 0, i["url"]))
    out = dump_part(f"{FAMILY}.media.json", items)

    # 4) notes
    write_notes(groups, items, media_rows, skipped, errored, indexed, manifest_urls, ext_hosts, refs_total, len(html_rows), fetched_in_scope, parts_years)
    print(f"{out}: {len(items)} media items from {len(media_rows)} fetched uploads and {len(html_rows)} html captures")
    return 0


def write_notes(groups, items, media_rows, skipped, errored, indexed, manifest_urls, ext_hosts, refs_total, n_html, fetched_in_scope, parts_years):
    by_year = collections.defaultdict(lambda: collections.Counter())
    for key, g in groups.items():
        y = edition_year_of(g) or 0
        c = by_year[y]
        c["images"] += 1
        fetched = g.fetched_variants
        if fetched:
            c["fetched"] += 1
            if not any(variant_area(u) >= 10 ** 9 for u in fetched):
                c["fetched_only_sized_variant"] += 1
        elif g.any_indexed:
            c["in_index_not_fetched"] += 1
        else:
            c["not_in_archive"] += 1
        if not g.content_pages and not g.chrome_pages:
            c["unreferenced"] += 1
        if g.chrome_pages and not g.content_pages:
            c["chrome_only"] += 1
    kinds = collections.Counter(i["kind"] for i in items)
    kinds_by_year = collections.defaultdict(collections.Counter)
    for i in items:
        kinds_by_year[i["edition_year"] or 0][i["kind"]] += 1

    # inventory: index uploads never fetched
    unfetched_index = collections.defaultdict(list)
    for u, rows in indexed.items():
        if u not in manifest_urls:
            y, _ = upload_year_month(u)
            unfetched_index[y or 0].append(u)
    # referenced but not in the archive at all
    missing = collections.defaultdict(list)
    for key, g in groups.items():
        if not g.fetched_variants and not g.any_indexed:
            y = edition_year_of(g) or 0
            missing[y].append(g)
    # referenced, only sized variants held
    sized_only = []
    for key, g in groups.items():
        f = g.fetched_variants
        if f and not any(variant_area(u) >= 10 ** 9 for u in f):
            sized_only.append((key, sorted(f, key=lambda u: -variant_area(u))[0]))
    chrome_only = [(g.key, len(g.chrome_pages)) for g in groups.values() if g.chrome_pages and not g.content_pages]

    L = []
    L.append("# Family media: notes\n")
    L.append("Parser: parse/media.py. Output: data/extracted/parts/media.media.json.\n")
    L.append("## Scope and coverage\n")
    L.append(f"- Fetched captures in scope (manifest kind upload|file, with a file): {fetched_in_scope}; "
             f"{fetched_in_scope - len(skipped)} extracted (each is a variant of one of the entries), {len(skipped)} skipped (listed below).")
    L.append(f"- Fetch errors in the manifest for media URLs (kind upload, no file): {len(errored)} unique URLs, listed below.")
    L.append(f"- HTML captures swept for references: {n_html} (kinds page, post, event, event-index, speaker); {refs_total} media references found (all size variants, all contexts).")
    L.append(f"- Media items written: {len(items)} (one per image, size variants grouped: {sum(len(g.variants) for g in groups.values())} distinct URLs).")
    L.append(f"- Kinds: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + ".")
    L.append(f"- Other families' parts used to date pages (source_url to edition_year): {len(parts_years)} page URLs.\n")

    L.append("## Per-year counts (edition_year)\n")
    L.append("| year | images | poster | photo | logo | other | fetched | only sized variant fetched | in index, not fetched | never archived | unreferenced | chrome only |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for y in sorted(by_year):
        c = by_year[y]
        k = kinds_by_year[y]
        L.append(f"| {y or 'none'} | {c['images']} | {k['poster']} | {k['photo']} | {k['logo']} | {k['other']} | {c['fetched']} | {c['fetched_only_sized_variant']} | {c['in_index_not_fetched']} | {c['not_in_archive']} | {c['unreferenced']} | {c['chrome_only']} |")
    L.append("")
    L.append("Columns: fetched = at least one variant of the image is in data/raw; "
             "only sized variant = the unsized original was never captured, the entry's url is the largest fetched variant; "
             "in index, not fetched = the CDX index has the URL with status 200 but fetch.py did not get it; "
             "never archived = referenced by a page but no variant is in the CDX index at all; "
             "unreferenced = a fetched upload no HTML capture points at (kept, dated by its upload path); "
             "chrome only = header logo / favicon, referenced by every page of its era.\n")

    L.append("## How the fields are built\n")
    L.append("- url: fetched original > largest fetched size variant > (nothing fetched) largest referenced URL. Always a URL that was really referenced or fetched, never synthesised. The two hosts' copies of the 2018 uploads (institucional.us.es/innosoft/wp-content/... and www.innosoftdays.com/wp-content/...) are one image; the url keeps the host that was actually fetched.")
    L.append("- kind: logo when it is a favicon / header logo / sidebar widget image (sponsor logos, the 2022 logo IMG_0386.png) / the file name says logo, cropped-, isotipo; other for PDF, video; photo when the file name looks like a camera or messaging export (IMG_, DSC, PXL_, WhatsApp, foto, photo), or the page is a photo post (Fotos, Imagenes, Images, Photos, Galeria), or it is used by an EventON event page (/eventos/, whose featured image is the speaker's photo), or it comes from a gallery block in landscape; poster when the name says cartel, poster, flyer, banner, programa, horario, torneo, concurso, ..., or it is the featured image of a MEC / Tribe event page, or its size variants say it is portrait or square (Instagram-style posts); jpg photos by default; otherwise other.")
    L.append("- edition_year: the majority year of the pages that reference the image (a page's year comes from the other parts' edition_year for that source_url, else the /YYYY/MM/DD/ post date, else a roman numeral or year in the slug); the upload path (/uploads/YYYY/MM/) breaks ties and dates the uploads no page references. Page years win over the upload path because the retrospective edition pages (vii-edicion, viii-edicion) show photos uploaded a year later.")
    L.append("- caption: figcaption / wp-caption / link text > alt > title attribute (skipping values WordPress copies from the file name) > title of the page it is the featured image of > for camera-style or numeric file names (DSC04297, IMG_0386, 1.jpg, Twitter ids) the heading of the block that holds the image, else the page title > file name humanised.")
    L.append("- used_by: every page URL that references the image in its content (any size variant, including as featured image / og:image). Site chrome images (header logo, favicon) list only the home page of their era; the number of pages that carry them is below.\n")

    L.append("## Skipped fetched captures\n")
    for u, why in sorted(skipped):
        L.append(f"- {u}: {why}")
    L.append("")
    L.append("## Media URLs whose fetch failed (in the manifest with an error, no file)\n")
    for u, err in sorted(errored.items()):
        L.append(f"- {u}: {err}")
    L.append("")

    L.append("## Inventory for a second fetch pass\n")
    L.append("### Uploads in the CDX index (kind upload, status 200) that are NOT in the manifest\n")
    tot = sum(len(v) for v in unfetched_index.values())
    L.append(f"{tot} unique URLs.")
    for y in sorted(unfetched_index):
        L.append(f"- {y or 'no year in path'}: {len(unfetched_index[y])}")
        for u in sorted(unfetched_index[y]):
            L.append(f"  - {u}")
    L.append("")
    L.append("### Images referenced by the pages that the CDX index does not have at all (no variant, any status)\n")
    L.append("These are the real gaps: the archive never captured them (or the CDX query missed them). Counts by edition_year; the full list of base URLs is the appendix at the end of this file.")
    for y in sorted(missing):
        L.append(f"- {y or 'no year'}: {len(missing[y])} images")
    L.append("")
    L.append("### Images held only as a sized variant (the unsized original was never captured)\n")
    L.append(f"{len(sized_only)} images; the entry's url is the largest fetched variant. NOTE for the importer: RawFiles.find() falls back from a sized URL to the unsized original only, so content_html of other families that references these images by another variant will not resolve unless the importer also tries the sibling variants held in the manifest.")
    for key, best in sorted(sized_only):
        L.append(f"- {key} -> {best}")
    L.append("")

    L.append("## Site chrome images (header logos, favicons)\n")
    for key, n in sorted(chrome_only, key=lambda x: -x[1]):
        L.append(f"- {key}: on {n} pages")
    L.append("")
    L.append("## External images (not on the two hosts, not extracted)\n")
    L.append("Hotlinked from post content; the importer cannot resolve them, so they are only counted here (img references, all captures):")
    for h, n in ext_hosts.most_common():
        L.append(f"- {h}: {n}")
    L.append("")
    L.append("## Oddities\n")
    L.append("- 2024/10/Video-web.webm is exactly 26214400 bytes in data/raw, the fetch.py MAX_BYTES cap (25 MiB): the capture is truncated. The kind is other; the importer should not treat it as a complete file.")
    L.append("- The two Elementor stylesheets fetched as uploads (elementor/css/post-214.css, post-48.css) are skipped: they are not media, and post-52.css / post-271.css failed with 404 in the archive.")
    L.append("- The three kind=file captures are plugin UI assets (Ultimate Member default avatar, Instagram Feed placeholder, tgchannel background) and are skipped.")
    L.append("- 2018/10/logo_2_negro-e1540204473260.png is a WordPress edited-image original (the -e<timestamp> suffix); it is kept as its own image, separate from logo_2_negro(-150x150,-300x300), because the edited file is a different crop.")
    L.append("- The 2025/01-02 posts are casino spam (the site was compromised before the 2025 rebuild); they reference no uploads besides the theme logo, so nothing from them enters the media list.")
    L.append("- The home page has versions in 2022 (colormag), 2024 (astra) and 2025 (blocksy / twentytwentyfive); the images each version references are dated by their upload path, so the same used_by URL legitimately appears in several years.")
    L.append("- WordPress edited-image originals (-e<timestamp> suffix, e.g. 2024/10/cartel6-e1730682914307.webp next to cartel6-816x1024.webp) are kept as their own image because the edited file is a different crop; the importer sees two entries for such posters.")
    L.append("- Kind is heuristic (file name, page kind, aspect ratio from the size variants). Where another family's media part covers the same image (matched by base name, any size variant) its hand-picked kind is adopted, and its caption too when this parser only had the file name; the count is printed when the parser runs.")
    L.append("")
    L.append("## Appendix: images never archived, base URL (content pages, chrome pages, size variants referenced)\n")
    for y in sorted(missing):
        L.append(f"### {y or 'no year'}: {len(missing[y])}\n")
        for g in sorted(missing[y], key=lambda g: g.key):
            L.append(f"- {g.key} ({len(g.content_pages)}, {len(g.chrome_pages)}, {len(g.variants)})")
        L.append("")
    (EXTRACTED / "parts" / f"{FAMILY}.notes.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
