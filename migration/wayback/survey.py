#!/usr/bin/env python3
"""Phase 3a: survey the raw captures. Classify every HTML capture by
"template family" (which WordPress plugin/theme produced it) and year
signals, so the extraction can be organised family by family and nothing
is silently left out.

Writes data/survey.jsonl (one row per capture) and data/survey_summary.md.
Run it any time; it only reads data/raw/.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RAW = DATA / "raw"
MANIFEST = RAW / "manifest.jsonl"
OUT = DATA / "survey.jsonl"
SUMMARY = DATA / "survey_summary.md"

SIGNATURES = [
    ("mec", re.compile(r'class="[^"]*\bmec-', re.I)),           # Modern Events Calendar
    ("eventon", re.compile(r'\betn[-_]|eventon', re.I)),         # EventON
    ("tribe", re.compile(r'tribe-events', re.I)),                # The Events Calendar
    ("elementor", re.compile(r'elementor', re.I)),
    ("bbpress", re.compile(r'bbpress|bbp-', re.I)),
    ("polylang", re.compile(r'polylang|pll_', re.I)),
    ("forminator", re.compile(r'forminator', re.I)),
    ("metaslider", re.compile(r'metaslider', re.I)),
    ("wpforms", re.compile(r'wpforms', re.I)),
    ("woocommerce", re.compile(r'woocommerce', re.I)),
]


def analyse(path: Path, meta: dict) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    gen = ""
    m = soup.find("meta", attrs={"name": "generator"})
    if m and m.get("content"):
        gen = m["content"]
    theme = ""
    tm = re.search(r"/wp-content/themes/([^/]+)/", html)
    if tm:
        theme = tm.group(1)
    body_class = ""
    if soup.body and soup.body.get("class"):
        body_class = " ".join(soup.body.get("class"))
    sigs = [name for name, rx in SIGNATURES if rx.search(html)]
    og_type = ""
    og = soup.find("meta", property="og:type")
    if og:
        og_type = og.get("content", "")
    pub = ""
    pt = soup.find("meta", property="article:published_time")
    if pt:
        pub = pt.get("content", "")
    lang = soup.html.get("lang", "") if soup.html else ""
    text = soup.get_text(" ", strip=True)
    years = sorted(set(re.findall(r"\b(20[12]\d)\b", text)))
    edition_words = sorted(set(re.findall(r"\b([IVX]{1,5})\s+edici[oó]n|edici[oó]n\s+([IVX]{1,5})\b", text, re.I)))
    ed = sorted({a or b for a, b in edition_words if (a or b)})
    h1 = soup.find("h1")
    return {
        **{k: meta.get(k) for k in ("url", "timestamp", "digest", "kind", "path")},
        "title": title[:200],
        "h1": h1.get_text(" ", strip=True)[:200] if h1 else "",
        "generator": gen,
        "theme": theme,
        "signatures": sigs,
        "og_type": og_type,
        "published": pub,
        "lang": lang,
        "years_in_text": years,
        "edition_numerals": ed,
        "text_len": len(text),
        "body_class": body_class[:300],
    }


def main() -> int:
    rows = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        if m.get("error") or not m.get("path", "").endswith(".html"):
            continue
        p = RAW / m["path"]
        if not p.exists():
            continue
        try:
            rows.append(analyse(p, m))
        except Exception as e:  # keep surveying
            rows.append({**m, "error": f"survey: {e}"})
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    fam = collections.Counter()
    for r in rows:
        key = (r.get("kind"), r.get("theme"), ",".join(s for s in r.get("signatures", []) if s in ("mec", "eventon", "tribe", "elementor", "bbpress")))
        fam[key] += 1
    lines = ["# Survey summary", "", f"html captures analysed: {len(rows)}", "", "## Families (kind, theme, plugin signatures)"]
    for (kind, theme, sig), n in fam.most_common():
        lines.append(f"- {n:4d}  kind={kind}  theme={theme}  sig={sig or '-'}")
    lines += ["", "## Themes"] + [f"- {t or '-'}: {n}" for t, n in collections.Counter(r.get('theme') for r in rows).most_common()]
    lines += ["", "## Capture years"] + [f"- {y}: {n}" for y, n in sorted(collections.Counter(r['timestamp'][:4] for r in rows if r.get('timestamp')).items())]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
