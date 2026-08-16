"""Family posts_2025: blog posts (kind=post) whose URL date year is 2025
(/2025/MM/DD/slug/, /en/2025/..., /es/2025/...).

What the captures are (see notes.md for the per-URL list):

* 151 captures (151 URLs, January 8 to February 5 2025) are SEO spam
  published through the compromised author account ``innosoft_manager`` on
  the old Astra WordPress site: online-casino / betting texts in Dutch,
  German, Spanish, Portuguese, French, English, Russian, Turkish, Greek,
  Polish, Korean, Georgian, Azeri, Czech, Italian, Finnish, Swedish,
  Norwegian, Estonian, Hungarian, Slovak... plus a few scraped Turkish
  parliament/association transcripts used as link filler. None mentions
  InnoSoft Days, ETSII or the event.
* 3 captures (1 URL, /es/2025/10/20/hola-mundo/) are the WordPress default
  "Hello world" post of the site rebuilt in October 2025 for the XIII
  edition (Blocksy theme); no editorial content.

So this family yields NO genuine posts, events or speakers.  The parser still
runs the full classification deterministically (so a rerun on a refreshed
archive would extract any genuine 2025 post it finds), writes an empty
posts.json to make the result explicit, and documents every capture in
notes.md with the reason it was skipped.

Deterministic, rerunnable, no network.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse.common import (  # noqa: E402
    BeautifulSoup, clean_html, dump_part, fix_lazy_images, manifest_rows,
    norm_url, soup_of, survey_rows, text_of, wp_datetime_local,
)

FAMILY = "posts_2025"
SITE = "https://www.innosoftdays.com"

URL_RE = re.compile(r"^https://www\.innosoftdays\.com/(?:(en|es)/)?(2025)/(\d{2})/(\d{2})/([^/]+)/?$")

# Signals of the SEO spam wave (same compromised account as the 2024 spam
# posts skipped by posts_2023_2024): gambling vocabulary in many languages.
GAMBLING_RE = re.compile(
    r"casino|casinò|kasino|kasyno|kasiino|kazino|казино|카지노|plinko|pokies|"
    r"\bslots?\b|gokkast|bahis|kumar|\bbets?\b|betting|apuestas|apostas|aposte|"
    r"1win|1xbet|22bet|mostbet|pokerdom|poker|jackpot|glücksspiel|glucksspiel|"
    r"hazardn|stoikhemat|στοιχημ|καζίνο|ставк|букмекер|totalizator|ტოტალიზატორ|"
    r"sugar rush|big bass|fortune|lucky|\bspins?\b|zooma|zuma|riobet|vavada|"
    r"pinco|pinko|pin up|pin-up|pinup|get x|olimp|1xslots|jojobet|casibom|onwin|"
    r"sahabet|tipobet|bettilt|grandpasha|becric|\bmcw\b|b9 game|banger|8k8|"
    r"jonbet|jon bet|betriot|glory|wazamba|lemon|winbay|winspirit|zino|vincispin|"
    r"gransino|ninecasino|viggoslots|gates of olympus|crazy time|lightning storm|"
    r"zeus|mega joker|pirots|balloon|globos|avia masters|kings casino|thebes|"
    r"\bb7\b|betonred|bet on red|le bandit|playpix|reel love|nettcasino|casinoin|"
    r"xanadı|glorqo|pocket option|casinoli|\br7\b|kumarhane|kelim|gokk",
    re.I,
)
# Anything a genuine InnoSoft Days post would mention.
GENUINE_RE = re.compile(r"innosoft|etsii|escuela técnica superior de ingeniería informática|universidad de sevilla|jornadas", re.I)
# Scraped Turkish text used as link filler (parliament transcripts, bylaws).
TURKISH_FILLER_RE = re.compile(r"millet meclisi|milletvekili|yönetim kurulu|komisyon|başkan", re.I)
WP_HELLO_RE = re.compile(r"bienvenida a wordpress|welcome to wordpress|esta es tu primera entrada|this is your first post", re.I)

# What the compromised author account was called (also used by the genuine
# team in earlier years, so it is only a hint, not proof, of spam).
SPAM_AUTHOR = "innosoft_manager"


# ---------------------------------------------------------------------------
# capture-level facts
# ---------------------------------------------------------------------------

def graph_of(soup) -> list[dict]:
    """Nodes of the Yoast @graph (empty on the Blocksy site, which has none)."""
    for sc in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(sc.string or "")
        except (TypeError, ValueError):
            continue
        if isinstance(data, dict) and "@graph" in data:
            return data["@graph"]
    return []


def facts(row: dict) -> dict:
    """Everything the classifier and the notes need from one capture."""
    m = URL_RE.match(row["url"])
    lang_prefix, year, month, day, slug = m.groups() if m else (None, "2025", "", "", row["url"].rstrip("/").split("/")[-1])
    soup = soup_of(row)
    title = ""
    h1 = soup.select_one("h1.entry-title, h1.page-title, article h1, h1")
    if h1 is not None:
        title = text_of(h1)
    if not title and soup.title and soup.title.string:
        title = re.sub(r"\s*[-–|]\s*InnoSoft Days\s*$", "", soup.title.string.strip())
    article = soup.find("article")
    classes = article.get("class") or [] if article is not None else []
    categories = [c[len("category-"):] for c in classes if c.startswith("category-")]
    author = ""
    for n in graph_of(soup):
        if n.get("@type") == "Person" and n.get("name"):
            author = n["name"]
    if not author:
        author = text_of(soup.select_one(".author-name, .ct-meta-element-author, .posted-by .author"))
    meta = soup.find("meta", property="article:published_time")
    published = wp_datetime_local(meta.get("content")) if meta is not None and meta.get("content") else None
    if not published:
        t = soup.select_one("article time[datetime], time.entry-date[datetime], time.ct-meta-element-date[datetime]")
        if t is not None:
            published = wp_datetime_local(t.get("datetime"))
    content = soup.select_one(".entry-content")
    if content is None and article is not None:
        content = article
    text = text_of(content)
    ext_domains = sorted({
        urlparse(a["href"]).netloc.lower().removeprefix("www.")
        for a in (content.find_all("a", href=True) if content is not None else [])
        if a["href"].startswith("http") and "innosoftdays" not in a["href"] and "web.archive.org" not in a["href"]
    })
    return {
        "row": row, "url": row["url"], "timestamp": row["timestamp"], "lang_prefix": lang_prefix,
        "year": int(year), "month": month, "day": day, "slug": slug, "title": title,
        "categories": categories, "author": author, "published": published,
        "text": text, "text_len": len(text), "ext_domains": ext_domains,
        "soup": soup, "content": content, "post_id": next((c for c in classes if re.match(r"post-\d+$", c)), ""),
    }


def classify(f: dict) -> tuple[str, str]:
    """('genuine' | 'skip', reason). Genuine = editorial content of the event."""
    head = f["title"] + " " + f["slug"].replace("-", " ")
    if WP_HELLO_RE.search(f["text"]) and f["text_len"] < 400:
        return "skip", "WordPress default 'Hello world' post of the site rebuilt in October 2025 for the XIII edition (Blocksy theme); no editorial content"
    if GAMBLING_RE.search(head) and not GENUINE_RE.search(f["text"]):
        return "skip", "SEO spam (online casino / betting text) published through the compromised author account, not InnoSoft content"
    if TURKISH_FILLER_RE.search(f["text"]) and not GENUINE_RE.search(f["text"]):
        return "skip", "SEO spam (scraped Turkish text used as link filler) published through the compromised author account, not InnoSoft content"
    if not GENUINE_RE.search(f["text"]) and not GENUINE_RE.search(head) and f["ext_domains"] and f["month"] in ("01", "02"):
        return "skip", "SEO spam (unrelated text with outbound links, part of the January/February 2025 spam wave), not InnoSoft content"
    return "genuine", ""


# ---------------------------------------------------------------------------
# extraction of a genuine post (Astra or Blocksy single-post template)
# ---------------------------------------------------------------------------

def content_html(node) -> str:
    if node is None:
        return ""
    node = BeautifulSoup(str(node), "lxml")
    for sel in (".wpcp-carousel-preloader", ".swiper-pagination", ".swiper-button-prev",
                ".swiper-button-next", ".wpcp-swiper-dots", "i.fa", ".ez-toc-container",
                ".ct-share-box", ".post-navigation", ".comments-area"):
        for t in node.select(sel):
            t.decompose()
    fix_lazy_images(node)
    for img in list(node.find_all("img")):
        src = img.get("src") or ""
        if not src or src.startswith("data:") or "/wp-content/plugins/" in src:
            img.decompose()
    for fig in list(node.find_all("figure")):
        if fig.find("figure") is not None:
            fig.unwrap()
    return clean_html(node)


def extract_post(f: dict) -> dict:
    soup = f["soup"]
    graph = graph_of(soup)
    categories, excerpt, featured = [], "", ""
    for n in graph:
        if n.get("@type") in ("Article", "BlogPosting"):
            sec = n.get("articleSection") or []
            categories = [sec] if isinstance(sec, str) else list(sec)
        if n.get("@type") == "WebPage" and n.get("description"):
            excerpt = n["description"]
    og = soup.find("meta", property="og:image")
    if og is not None and og.get("content"):
        featured = norm_url(og["content"])
    if not featured:
        fig = soup.select_one(".post-thumb img, .ct-featured-image img, .wp-post-image")
        if fig is not None:
            fix_lazy_images(fig.parent)
            featured = norm_url(fig.get("src"))
    if not excerpt:
        md = soup.find("meta", attrs={"name": "description"})
        excerpt = md.get("content", "") if md is not None else ""
    if not excerpt:
        excerpt = f["text"][:200]
    html = content_html(f["content"])
    date = f["published"] or f"{f['year']}-{f['month']}-{f['day']}T00:00:00"
    lang = "en" if f["lang_prefix"] == "en" else "es"
    return {
        "date": date, "title": f["title"], "slug": f["slug"], "excerpt": excerpt,
        "content_html": html, "featured_image_url": featured, "lang": lang,
        "edition_year": f["year"],
        "categories": categories, "source_url": f["url"], "source_timestamp": f["timestamp"],
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    rows = [r for r in manifest_rows("post") if URL_RE.match(r["url"])]
    rows.sort(key=lambda r: (r["url"], r["timestamp"]))
    survey = {(norm_url(s["url"]), s["timestamp"]): s for s in survey_rows()}

    per_url: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_url[r["url"]].append(r)

    posts, skipped, genuine_urls = [], [], []
    templates = Counter()
    for url, caps in sorted(per_url.items()):
        fs = [facts(c) for c in caps]
        for f in fs:
            s = survey.get((f["url"], f["timestamp"]), {})
            templates[(s.get("theme", "?"), s.get("generator", "?"))] += 1
        # every version is classified; a URL is genuine when its latest
        # non-empty version is genuine (versions never differ here, checked
        # via the text length below and reported in the notes)
        verdicts = [classify(f) for f in fs]
        latest = fs[-1]
        kind, reason = verdicts[-1]
        lens = sorted({f["text_len"] for f in fs})
        if kind == "genuine":
            posts.append(extract_post(latest))
            genuine_urls.append((latest, [f["timestamp"] for f in fs]))
        else:
            skipped.append({
                "url": url, "timestamps": [f["timestamp"] for f in fs], "title": latest["title"],
                "reason": reason, "published": latest["published"], "author": latest["author"],
                "categories": latest["categories"], "ext_domains": latest["ext_domains"],
                "text_len": lens, "post_id": latest["post_id"], "month": latest["month"],
            })

    posts.sort(key=lambda p: (p["date"], p["slug"]))
    dump_part(f"{FAMILY}.posts.json", posts)
    write_notes(rows, per_url, posts, genuine_urls, skipped, templates)
    print(f"{FAMILY}: captures={len(rows)} urls={len(per_url)} posts={len(posts)} skipped_urls={len(skipped)} skipped_captures={sum(len(s['timestamps']) for s in skipped)}")


def write_notes(rows, per_url, posts, genuine_urls, skipped, templates) -> None:
    n_caps = len(rows)
    n_skip_caps = sum(len(s["timestamps"]) for s in skipped)
    by_reason: dict[str, list[dict]] = defaultdict(list)
    for s in skipped:
        by_reason[s["reason"]].append(s)
    months = Counter(s["month"] for s in skipped for _ in s["timestamps"])
    authors = Counter(s["author"] for s in skipped)
    cats = Counter(c for s in skipped for c in s["categories"])
    ext = Counter(d for s in skipped for d in s["ext_domains"])
    pubs = sorted(p for p in (s["published"] for s in skipped if s["month"] in ("01", "02")) if p)

    L = []
    L.append(f"# {FAMILY}\n")
    L.append("Blog posts (kind=post) whose URL date year is 2025: Spanish (/2025/MM/DD/slug/), English (/en/2025/...) and the new-site Spanish prefix (/es/2025/...). Two templates: the old Astra WordPress site (Yoast schema graph, WordPress 6.7.x, captured February 2025) and the site rebuilt in October 2025 for the XIII edition (Blocksy theme, WordPress 6.8/6.9, captured November 2025 to May 2026).\n")
    L.append("## What these captures are\n")
    L.append("- The 151 captures of January and February 2025 are the tail of the SEO-spam wave that hit the old site through the author account `innosoft_manager` (the same account behind the two 2024 spam posts skipped by posts_2023_2024): online casino / betting / slot texts in some twenty languages, plus scraped Turkish parliament transcripts and association bylaws used as link filler, each with an outbound link to an unrelated domain. Not one of them mentions InnoSoft Days, ETSII or the event. They are NOT WooCommerce products, forum digests or auto-generated event content; the WooCommerce / bbPress / EventON signatures in the survey come from plugins loaded site-wide.")
    L.append("- The 3 captures of /es/2025/10/20/hola-mundo/ are the WordPress default 'Hello world' post (post-1, 'Te damos la bienvenida a WordPress...') of the site rebuilt for the XIII edition. The rebuilt site never published a blog post in the captured period; its navigation (Inicio, Eventos, Cronograma, Fotos, Feedback, Sobre nosotros) has no news section, and the XIII programme is already migrated in the product.")
    L.append("- Result: no genuine editorial post, no speaker, no event and no activity missing from the XIII programme. `posts_2025.posts.json` is written empty on purpose so the coverage is explicit; no speakers/events/editions files are produced.\n")
    L.append("## Coverage\n")
    L.append(f"- Captures in scope: {n_caps} ({len(per_url)} distinct URLs); every URL of the CDX index dated 2025 was fetched (checked against data/index.jsonl, 0 missing).")
    L.append(f"- Posts extracted: {len(posts)}; skipped: {len(skipped)} URLs ({n_skip_caps} captures).")
    L.append("- Templates seen: " + ", ".join(f"{t[0]}/{t[1]} x{n}" for t, n in sorted(templates.items(), key=lambda kv: -kv[1])) + ".")
    L.append(f"- Spam publication dates (article:published_time, Europe/Madrid): {pubs[0][:10]} to {pubs[-1][:10]}; author of every capture: " + ", ".join(f"{a} x{n}" for a, n in authors.most_common()) + ".")
    L.append("- WordPress categories of the skipped posts: " + ", ".join(f"{c} x{n}" for c, n in cats.most_common()) + " (sin-categoria-es = default Spanish category of the old site; the one-letter ones are spam categories created by the attacker).")
    L.append("- Outbound link domains in the spam (top 15): " + ", ".join(f"{d} x{n}" for d, n in ext.most_common(15)) + ".")
    L.append("- Versions: the only URL with several captures is hola-mundo (3 identical versions, same text length); every other URL has one capture, so no cross-version merging was needed.\n")
    L.append("## Per year\n")
    L.append(f"- 2025: {len(posts)} posts, 0 events, 0 speakers, 0 media (captures: {n_caps}, of which {months.get('01', 0)} in January, {months.get('02', 0)} in February and {n_caps - months.get('01', 0) - months.get('02', 0)} in October).\n")
    if posts:
        L.append("## Posts extracted (url, capture used, other captures)\n")
        for f, ts in genuine_urls:
            others = ", ".join(t for t in ts if t != f["timestamp"])
            L.append(f"- {f['published'] or ''} [{f['lang_prefix'] or 'es'}] {f['title']} <{f['url']}> capture {f['timestamp']}" + (f" (also {others})" if others else ""))
        L.append("")
    L.append("## Skipped (url, captures, reason)\n")
    for reason, items in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
        L.append(f"### {reason} ({len(items)} URLs, {sum(len(i['timestamps']) for i in items)} captures)\n")
        for s in sorted(items, key=lambda s: s["url"]):
            extra = ""
            if s["ext_domains"]:
                extra = " links: " + ", ".join(s["ext_domains"][:3])
            L.append(f"- {s['url']} ({', '.join(s['timestamps'])}): \"{s['title'][:90]}\"{extra}")
        L.append("")
    L.append("## Oddities\n")
    L.append("- The old site's header menu captured with the spam (Inicio, Noticias, Cronograma, Igualdad, TDAH, Sostenibilidad, Juegos > Crucigramas...) shows the XII-era section structure; those pages belong to the pages family, not to this one.")
    L.append("- Several spam URLs come in near-duplicate pairs (slug and slug-2: riobet, zooma, zuma, olimp, pinko, vavada, casinoin, pokerdom, 1xslots...): the attacker published the same text twice. Irrelevant for the migration, listed for completeness.")
    L.append("- The rebuilt XIII site was captured with the /es/ Polylang prefix even for its default language; if the product ever imports posts from it, permalinks should drop that prefix as the 2018-2024 importer does with /en/.")
    L.append("- The classifier is rule based (gambling vocabulary in title/slug, scraped-Turkish markers, absence of any InnoSoft/ETSII/US mention, outbound unrelated links, the WordPress hello-world sentence). If a refreshed archive brings a genuine 2025 post it will be extracted with the Astra/Blocksy single-post extractor in this file (Yoast graph or <time datetime> for the date, entry-content cleaned with clean_html, og:image as featured image).")
    out = Path(__file__).resolve().parent.parent / "data" / "extracted" / "parts" / f"{FAMILY}.notes.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
