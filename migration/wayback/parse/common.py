"""Shared helpers for the phase 3 parsers.

Every parser imports this so the extracted HTML is cleaned the same way and
every URL is normalised the same way. Keep it dependency-light: bs4 + lxml.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
RAW = DATA / "raw"
MANIFEST = RAW / "manifest.jsonl"
SURVEY = DATA / "survey.jsonl"
EXTRACTED = DATA / "extracted"

# Semantic tags kept in cleaned HTML; everything else is unwrapped.
KEEP_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "a", "img",
    "strong", "b", "em", "i", "u", "table", "thead", "tbody", "tr", "th", "td",
    "blockquote", "br", "figure", "figcaption", "pre", "code", "hr", "iframe",
}
KEEP_ATTRS = {"a": {"href", "title"}, "img": {"src", "alt", "title"}, "iframe": {"src", "title"}, "td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"}}
DROP_TAGS = {"script", "style", "noscript", "svg", "form", "input", "button", "select", "textarea", "nav", "footer", "header", "aside"}

MONTHS_ES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
MONTHS_EN = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}


def norm_url(url: str | None) -> str:
    """Absolute original-site URL, https, www host, no Wayback prefix."""
    if not url:
        return ""
    url = url.strip()
    url = re.sub(r"^https?://web\.archive\.org/web/\d+(?:id_|im_|js_|cs_)?/", "", url)
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/"):
        url = "https://www.innosoftdays.com" + url
    url = url.replace("http://", "https://").replace("://innosoftdays.com", "://www.innosoftdays.com")
    return url.split("#")[0]


def manifest_rows(kind: str | None = None) -> list[dict]:
    rows = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        if m.get("error") or not m.get("path"):
            continue
        if kind and m.get("kind") != kind:
            continue
        m["url"] = norm_url(m["url"])
        rows.append(m)
    return rows


def survey_rows() -> list[dict]:
    if not SURVEY.exists():
        return []
    return [json.loads(l) for l in SURVEY.read_text(encoding="utf-8").splitlines() if l.strip()]


def latest_per_url(rows: list[dict]) -> dict[str, dict]:
    """The most recent capture of each URL (rows sorted by timestamp)."""
    out: dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: r["timestamp"]):
        out[r["url"]] = r
    return out


def read_html(row: dict) -> str:
    return (RAW / row["path"]).read_text(encoding="utf-8", errors="replace")


def soup_of(row: dict) -> BeautifulSoup:
    return BeautifulSoup(read_html(row), "lxml")


def clean_html(node) -> str:
    """Semantic HTML from a plugin-heavy fragment: no wrappers, no classes,
    no inline styles, no scripts; images and links keep their targets
    (normalised to the original site URL). Returns "" for empty content."""
    if node is None:
        return ""
    if isinstance(node, str):
        node = BeautifulSoup(node, "lxml")
    node = BeautifulSoup(str(node), "lxml")  # work on a copy
    for c in node.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    for t in node.find_all(DROP_TAGS):
        t.decompose()
    for t in list(node.find_all(True)):
        if t.name in ("html", "body", "[document]"):
            continue
        if t.name not in KEEP_TAGS:
            t.unwrap()
            continue
        allowed = KEEP_ATTRS.get(t.name, set())
        for attr in list(t.attrs):
            if attr not in allowed:
                del t[attr]
        if t.name == "a" and t.get("href"):
            t["href"] = norm_url(t["href"]) if "innosoftdays" in t["href"] or t["href"].startswith("/") or "web.archive.org" in t["href"] else t["href"]
        if t.name == "img":
            src = t.get("src") or ""
            if not src or src.startswith("data:"):
                # lazy-loaded images keep the real URL in data-src, lost above; try text
                t.decompose()
                continue
            t["src"] = norm_url(src)
    body = node.body if node.body else node
    html = "".join(str(c) for c in body.children)
    # collapse empty paragraphs and whitespace
    html = re.sub(r"<p>\s*(?:<br\s*/?>|&nbsp;|\s)*</p>", "", html)
    html = re.sub(r"\n\s*\n+", "\n", html).strip()
    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    return html if text or "<img" in html else ""


def text_of(node) -> str:
    return node.get_text(" ", strip=True) if node is not None else ""


def parse_spanish_date(text: str, default_year: int | None = None):
    """'martes 24 de noviembre de 2020' / '24/11/2020' / '24 noviembre' -> date."""
    if not text:
        return None
    t = text.lower()
    m = re.search(r"(\d{1,2})\s*(?:de\s+)?(" + "|".join(MONTHS_ES) + r")(?:\s*(?:de\s+)?(\d{4}))?", t)
    if m:
        d, mon, y = int(m.group(1)), MONTHS_ES[m.group(2)], m.group(3)
        y = int(y) if y else default_year
        if y:
            try:
                return datetime(y, mon, d).date()
            except ValueError:
                return None
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
        except ValueError:
            return None
    m = re.search(r"(" + "|".join(MONTHS_EN) + r")\s+(\d{1,2})(?:,?\s*(\d{4}))?", t)
    if m:
        mon, d, y = MONTHS_EN[m.group(1)], int(m.group(2)), m.group(3)
        y = int(y) if y else default_year
        if y:
            try:
                return datetime(y, mon, d).date()
            except ValueError:
                return None
    return None


def parse_time(text: str):
    """'09:30', '9.30h', '15:30 - 16:30' -> ('09:30', '16:30' or None)."""
    if not text:
        return None, None
    times = re.findall(r"(\d{1,2})[:.h](\d{2})", text)
    if not times:
        m = re.findall(r"\b(\d{1,2})\s*h\b", text)
        times = [(h, "00") for h in m]
    norm = [f"{int(h):02d}:{mm}" for h, mm in times]
    if not norm:
        return None, None
    return norm[0], (norm[1] if len(norm) > 1 else None)


def edition_number_for_year(year: int) -> int:
    """InnoSoft Days I was 2013 (VI = 2018, XIII = 2025)."""
    return year - 2012


def roman(n: int) -> str:
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def dump(name: str, data) -> Path:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    p = EXTRACTED / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# --- additive helpers (posts_2022) -------------------------------------------

def unlazy_images(node) -> None:
    """In place: give lazy-loaded <img> their real URL (data-src /
    data-lazy-src / data-original) so clean_html keeps them, and drop the
    <noscript> duplicates WordPress lazy loaders emit next to them."""
    if node is None:
        return
    for ns in node.find_all("noscript"):
        ns.decompose()
    for img in node.find_all("img"):
        src = img.get("src") or ""
        real = img.get("data-src") or img.get("data-lazy-src") or img.get("data-original")
        if (not src or src.startswith("data:")) and real:
            img["src"] = real
        for attr in ("data-src", "data-srcset", "data-lazy-src", "data-sizes", "srcset", "sizes", "loading"):
            if attr in img.attrs:
                del img[attr]


def wp_datetime_local(iso: str | None) -> str | None:
    """'2022-10-23T19:55:01+00:00' (article:published_time, UTC) ->
    '2022-10-23T21:55:01' naive Europe/Madrid. None when unparsable."""
    if not iso:
        return None
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(ZoneInfo("Europe/Madrid")).replace(tzinfo=None)
        return dt.isoformat(timespec="seconds")
    except ValueError:
        return None


def dump_part(name: str, data) -> Path:
    """Write data/extracted/parts/<name> (per-family output)."""
    p = EXTRACTED / "parts" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# --- helpers added by parse/posts_2018_2020.py (additive only) ---------------

INSTITUCIONAL_PREFIX = "https://institucional.us.es/innosoft/"


def norm_media_url(url: str | None) -> str:
    """norm_url plus the pre-2021 host: the WordPress lived at
    institucional.us.es/innosoft/ and kept the same wp-content paths after the
    move to innosoftdays.com (the srcset of the same <img> proves it), so map
    that prefix to the current host to make the importer's lookup possible."""
    u = norm_url(url)
    if u.startswith(INSTITUCIONAL_PREFIX) and "/wp-content/" in u:
        u = "https://www.innosoftdays.com/" + u[len(INSTITUCIONAL_PREFIX):]
    return u


def best_srcset_url(srcset: str | None) -> str:
    """Largest candidate of a srcset attribute ('' when none)."""
    if not srcset:
        return ""
    best, best_w = "", -1
    for cand in srcset.split(","):
        parts = cand.strip().split()
        if not parts:
            continue
        w = 0
        if len(parts) > 1:
            m = re.match(r"(\d+)(w|x)", parts[1])
            if m:
                w = int(m.group(1))
        if w > best_w:
            best, best_w = parts[0], w
    return best


def fix_lazy_images(node) -> None:
    """In place: give lazy-loaded <img> (src="data:...", real URL in data-src /
    data-srcset / srcset) a real src so clean_html keeps them, choosing the
    largest srcset candidate. Also drops <noscript> fallbacks that duplicate
    the same image next to it."""
    if node is None:
        return
    for ns in node.find_all("noscript"):
        ns.decompose()
    for img in node.find_all("img"):
        src = img.get("src") or ""
        real = best_srcset_url(img.get("data-srcset") or img.get("srcset"))
        if not real:
            real = img.get("data-src") or img.get("data-lazy-src") or img.get("data-original") or ""
        if src.startswith("data:") or not src or ("web.archive.org" in src and real):
            if real:
                img["src"] = real
        if img.get("src"):
            img["src"] = norm_media_url(img["src"])
        for attr in ("data-src", "data-srcset", "srcset", "data-sizes", "sizes", "data-lazy-src", "loading", "decoding"):
            if attr in img.attrs:
                del img[attr]


# --- helpers added by parse/people.py (additive only) -------------------------

import unicodedata

NAME_PARTICLES = {"de", "del", "la", "las", "los", "y", "e", "i", "da", "do", "dos", "van", "von", "sr", "sra", "srs", "d"}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text or "") if unicodedata.category(c) != "Mn")


def name_tokens(name: str) -> tuple:
    """Accent-insensitive, lower-case tokens of a person name without
    particles or punctuation: 'María José Escalona' -> ('maria','jose','escalona')."""
    t = strip_accents(name or "").lower()
    t = re.sub(r"[“”\"'’`´().,;:/]", " ", t)
    return tuple(w for w in t.split() if w not in NAME_PARTICLES)


def name_key(name: str) -> str:
    return " ".join(name_tokens(name))


def name_in_text(name: str, text: str) -> bool:
    """True when every token of `name` (at least two tokens) appears as a
    whole word in `text` (accent-insensitive)."""
    toks = name_tokens(name)
    if len(toks) < 2:
        return False
    words = set(name_tokens(text))
    return all(t in words for t in toks)


def capture_year(row: dict, html: str | None = None):
    """Best-effort year an event/post capture describes: post URL /YYYY/,
    JSON-LD Event startDate, Eventin 'Date : dd/mm/yyyy', MEC start dates,
    then article:published_time. None when nothing matches."""
    m = re.search(r"innosoftdays\.com/(20\d\d)/\d\d/\d\d/", row.get("url", ""))
    if m:
        return int(m.group(1))
    if html is None:
        html = read_html(row)
    m = re.search(r'"startDate"\s*:\s*"(20\d\d)-', html)
    if m:
        return int(m.group(1))
    m = re.search(r"Date\s*:\s*<[^>]*>\s*\d{2}/\d{2}/(20\d\d)", html) or re.search(r"Date\s*:\s*\d{2}/\d{2}/(20\d\d)", html)
    if m:
        return int(m.group(1))
    m = re.search(r'article:published_time" content="(20\d\d)-', html)
    if m:
        return int(m.group(1))
    return None


def name_phrase_in_text(name: str, text: str) -> bool:
    """Stricter than name_in_text: the name tokens appear contiguously in
    the text (2+ tokens), or the name has 3+ tokens and all of them appear."""
    toks = name_tokens(name)
    if len(toks) < 2:
        return False
    words = name_tokens(text)
    n = len(toks)
    for i in range(len(words) - n + 1):
        if tuple(words[i:i + n]) == toks:
            return True
    return n >= 3 and all(t in set(words) for t in toks)


def same_person(a: str, b: str) -> bool:
    """Two name spellings refer to one person when the shorter one is a
    subset of the longer, both share the first token (first name) and the
    shorter has at least two tokens: 'Clara Grima' ~ 'Clara Isabel Grima Ruiz',
    but 'Pablo Pérez' !~ 'Luis Pablo del Árbol Pérez'."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return False
    s, l = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return len(s) >= 2 and s[0] == l[0] and set(s) <= set(l)


# --- helpers added by parse/pages_editions.py (additive only) ----------------

def read_html_any(row: dict) -> str:
    """read_html that also understands raw captures stored gzip-compressed
    (three page captures were saved with the transfer encoding intact)."""
    import gzip
    b = (RAW / row["path"]).read_bytes()
    if b[:2] == b"\x1f\x8b":
        try:
            b = gzip.decompress(b)
        except OSError:
            pass
    return b.decode("utf-8", errors="replace")


def soup_any(row: dict) -> BeautifulSoup:
    return BeautifulSoup(read_html_any(row), "lxml")


def tidy_html(html: str) -> str:
    """Second pass after clean_html(): drop empty inline/figure/list shells,
    turn WordPress embed cards (blockquote + iframe) into a plain link, wrap
    bare <img> in <figure> and collapse whitespace between block tags."""
    if not html:
        return ""
    s = BeautifulSoup(html, "lxml")
    body = s.body if s.body else s
    # wp embeds: <figure><blockquote><a href>title</a></blockquote><iframe .../embed/...></figure>
    for ifr in list(body.find_all("iframe")):
        src = ifr.get("src") or ""
        if "/embed/" in src and "innosoftdays" in src:
            fig = ifr.find_parent("figure")
            a = fig.find("a") if fig else None
            if fig is not None and a is not None and a.get("href"):
                p = s.new_tag("p")
                na = s.new_tag("a", href=a["href"])
                na.string = a.get_text(" ", strip=True)
                p.append(na)
                fig.replace_with(p)
            else:
                ifr.decompose()
    changed = True
    while changed:
        changed = False
        for t in list(body.find_all(["a", "i", "b", "em", "strong", "u", "figure", "ul", "ol", "li", "p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "td", "tr", "table", "figcaption"])):
            if t.find(["img", "iframe", "br"]) is not None and t.name != "p":
                continue
            if t.name == "p" and t.find(["img", "iframe"]) is not None:
                continue
            if not t.get_text(strip=True):
                t.decompose()
                changed = True
    for img in list(body.find_all("img")):
        if img.find_parent(["figure", "p", "li", "td", "a"]) is None:
            fig = s.new_tag("figure")
            img.replace_with(fig)
            fig.append(img)
    for h1 in body.find_all("h1"):
        h1.name = "h2"
    # bare text runs at the top level (unwrapped <div>/<span> copy) become paragraphs
    for c in list(body.children):
        if isinstance(c, NavigableString) and not isinstance(c, Comment) and c.strip():
            p = s.new_tag("p")
            c.replace_with(p)
            p.string = re.sub(r"\s+", " ", str(c)).strip()
    out = "".join(str(c) for c in body.children)
    # collapse whitespace between block-level tags only (inline runs keep their space)
    block = r"(?:p|h[1-6]|ul|ol|li|table|thead|tbody|tr|td|th|figure|figcaption|blockquote|hr|pre|iframe)"
    out = re.sub(r"(</" + block + r">)\s+", r"\1", out)
    out = re.sub(r"\s+(<" + block + r"[ >/])", r"\1", out)
    out = re.sub(r"(<" + block + r"[^>]*>)\s+", r"\1", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


ELEMENTOR_HEADING_MAX = 80


def elementor_normalise(node) -> None:
    """In place, before clean_html(): Elementor pages (2025 Blocksy site) put
    every line of copy in an <h2 class=elementor-heading-title>. Keep the
    first short heading of each section and question-like headings as <h2>,
    demote everything else to <p>. Also removes elementor navigation,
    buttons that are pure UI, and slider chrome."""
    if node is None:
        return
    for sel in (".elementor-widget-nav-menu", ".e-n-tabs-heading", ".elementor-widget-spacer", ".elementor-widget-divider", ".metaslider .flexslider .flex-direction-nav", ".e-n-accordion-item-title-icon"):
        for t in node.select(sel):
            t.decompose()
    for section in node.select(".e-parent, .elementor-section, .elementor-top-section"):
        first = True
        for h in section.select(".elementor-widget-heading .elementor-heading-title"):
            txt = h.get_text(" ", strip=True)
            keep = (first and len(txt) <= ELEMENTOR_HEADING_MAX) or (txt.endswith("?") and len(txt) <= ELEMENTOR_HEADING_MAX)
            first = False
            if not keep:
                h.name = "p"
            elif h.name not in ("h1", "h2", "h3", "h4"):
                h.name = "h2"
    # headings outside any recognised section: apply the length rule only
    for h in node.select(".elementor-widget-heading .elementor-heading-title"):
        if h.name.startswith("h") and len(h.get_text(" ", strip=True)) > ELEMENTOR_HEADING_MAX:
            h.name = "p"


def strip_accents(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")


def norm_key(s: str) -> str:
    """Loose matching key for titles: lowercase, no accents, no punctuation,
    single spaces."""
    s = strip_accents((s or "").lower())
    s = s.replace("​", "")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def unwrap_nested_figures(html: str) -> str:
    """'<figure><figure><img/></figure></figure>' -> '<figure><img/></figure>'
    (WordPress galleries wrap every image figure in a gallery figure)."""
    if not html or "<figure>" not in html:
        return html
    prev = None
    while prev != html:
        prev = html
        html = re.sub(r"<figure>\s*<figure>", "<figure>", html)
        html = re.sub(r"</figure>\s*</figure>", "</figure>", html)
    return html
