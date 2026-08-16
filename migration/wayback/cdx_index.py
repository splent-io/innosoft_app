#!/usr/bin/env python3
"""Phase 1 of the InnoSoft Days archive recovery: build a complete local index
of what the Wayback Machine holds for every past web of the event.

Ad hoc, one-off tooling for this migration (not a SPLENT feature). It only
talks to the CDX API and writes data/index.jsonl (one capture per line) plus
data/index_summary.md, so the expensive discovery is done once and every
later phase works offline.

Polite by construction: one request every PAUSE seconds, exponential backoff
on 429/503, resumable (targets already indexed are skipped unless --force).

Usage: python3 cdx_index.py [--force] [--only innosoftdays.com]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
INDEX = DATA / "index.jsonl"
STATE = DATA / "index_state.json"
SUMMARY = DATA / "index_summary.md"

CDX = "https://web.archive.org/cdx/search/cdx"
PAUSE = 4.0
FIELDS = "timestamp,original,statuscode,mimetype,digest,length"

# Every place the event has lived on the web, as far as we know. The
# institutional site's exact path is unknown, so several shapes are tried,
# including a domain scan filtered by "innosoft" (heavier, done last).
TARGETS = [
    {"name": "innosoftdays.com", "url": "innosoftdays.com/*", "match": None},
    {"name": "innosoftdays.com-www", "url": "www.innosoftdays.com/*", "match": None},
    {"name": "innosoftdays.es", "url": "innosoftdays.es/*", "match": None},
    {"name": "innosoftdays.org", "url": "innosoftdays.org/*", "match": None},
    {"name": "us.es-innosoftdays", "url": "us.es/innosoftdays*", "match": "prefix"},
    {"name": "www.us.es-innosoftdays", "url": "www.us.es/innosoftdays*", "match": "prefix"},
    {"name": "institucional-innosoftdays", "url": "institucional.us.es/innosoftdays*", "match": "prefix"},
    {"name": "institucional-innosoft", "url": "institucional.us.es/innosoft*", "match": "prefix"},
    # The one that exists: the pre-2021 WordPress lived at /innosoft/ (the
    # 2018-2020 posts on innosoftdays.com still embed images from there).
    {"name": "institucional-innosoft-dir", "url": "institucional.us.es/innosoft/*", "match": None},
    {"name": "institucional-innosoft-dir-http", "url": "http://institucional.us.es/innosoft/*", "match": None},
    {"name": "innosoftdays.us.es", "url": "innosoftdays.us.es/*", "match": None},
    {"name": "innosoft.us.es", "url": "innosoft.us.es/*", "match": None},
    {"name": "institucional-domain-filter", "url": "institucional.us.es/*", "match": "prefix",
     "extra": {"filter": "original:.*[Ii]nno[Ss]oft.*"}},
    {"name": "us.es-domain-filter", "url": "us.es", "match": "domain",
     "extra": {"filter": "original:.*[Ii]nno[Ss]oft[Dd]ays.*"}},
]


def _get(url: str, attempt: int = 0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "innosoft-days-archive-recovery/1.0 (contact: innosoftdays@gmail.com)"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (429, 503, 502, 504) and attempt < 8:
            wait = min(600, PAUSE * (2 ** (attempt + 1)))
            print(f"    {e.code}, waiting {wait:.0f}s", flush=True)
            time.sleep(wait)
            return _get(url, attempt + 1)
        raise
    except (urllib.error.URLError, TimeoutError) as e:
        if attempt < 6:
            wait = min(600, PAUSE * (2 ** (attempt + 1)))
            print(f"    {e}, waiting {wait:.0f}s", flush=True)
            time.sleep(wait)
            return _get(url, attempt + 1)
        raise


def query(target: dict) -> list[dict]:
    """All captures for a target, paginated with resume keys."""
    rows: list[dict] = []
    resume = None
    page = 0
    while True:
        params = {
            "url": target["url"],
            "output": "json",
            "fl": FIELDS,
            "collapse": "digest",
            "limit": "5000",
            "showResumeKey": "true",
        }
        if target.get("match"):
            params["matchType"] = target["match"]
        params.update(target.get("extra", {}))
        if resume:
            params["resumeKey"] = resume
        url = CDX + "?" + urllib.parse.urlencode(params)
        page += 1
        print(f"  {target['name']}: page {page}", flush=True)
        body = _get(url)
        time.sleep(PAUSE)
        body = body.strip()
        if not body:
            break
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            print(f"    non-JSON answer ({body[:80]!r}), treating as empty", flush=True)
            break
        if not data:
            break
        header, *items = data
        resume = None
        # With showResumeKey the resume key travels as a trailing 1-item row
        # preceded by an empty row.
        if items and items[-1] and len(items[-1]) == 1:
            resume = items[-1][0]
            items = items[:-1]
            if items and not items[-1]:
                items = items[:-1]
        for it in items:
            if not it:
                continue
            row = dict(zip(header, it))
            row["target"] = target["name"]
            rows.append(row)
        if not resume:
            break
    return rows


def classify(url: str) -> str:
    u = url.lower()
    if "/wp-content/uploads/" in u:
        return "upload"
    if re.search(r"/20\d\d/\d\d/\d\d/[^/?]+/?$", u):
        return "post"
    if re.search(r"/(events?|eventos)/[^/?]+/?$", u):
        return "event"
    if re.search(r"/(events?|eventos)/?$", u):
        return "event-index"
    if "ponente" in u or "speaker" in u:
        return "speaker"
    if any(x in u for x in ("/wp-json", "/wp-admin", "/wp-includes", "/feed", "xmlrpc", "?p=", "/tag/", "/category/", "/author/", "/page/", "/comments/", "/forums/", "/topic/", "?share=", "?replytocom", "/wp-login", "/oembed")):
        return "noise"
    if re.search(r"\.(css|js|woff2?|ttf|svg|ico|json|xml|txt|map)(\?|$)", u):
        return "asset"
    if re.search(r"\.(jpe?g|png|gif|webp|pdf|mp4|heic)(\?|$)", u):
        return "file"
    return "page"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    for target in TARGETS:
        if args.only and target["name"] != args.only:
            continue
        if not args.force and target["name"] in state:
            print(f"  {target['name']}: indexed ({state[target['name']]['captures']} captures), skip")
            continue
        try:
            rows = query(target)
        except Exception as e:  # keep going with the other targets
            print(f"  {target['name']}: FAILED {e}", flush=True)
            state[target["name"]] = {"captures": 0, "error": str(e)}
            STATE.write_text(json.dumps(state, indent=2))
            continue
        with INDEX.open("a", encoding="utf-8") as fh:
            for r in rows:
                r["kind"] = classify(r.get("original", ""))
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        state[target["name"]] = {"captures": len(rows)}
        STATE.write_text(json.dumps(state, indent=2))
        print(f"  {target['name']}: {len(rows)} captures", flush=True)
    summarize()
    return 0


def summarize() -> None:
    if not INDEX.exists():
        return
    rows = [json.loads(l) for l in INDEX.read_text(encoding="utf-8").splitlines() if l.strip()]
    ok = [r for r in rows if r.get("statuscode") == "200"]
    by_target = collections.Counter(r["target"] for r in rows)
    kinds = collections.Counter(r["kind"] for r in ok)
    urls = {r["original"] for r in ok}
    years = collections.Counter(r["timestamp"][:4] for r in ok)
    posts = collections.Counter()
    for r in ok:
        if r["kind"] == "post":
            m = re.search(r"/(20\d\d)/\d\d/\d\d/", r["original"])
            if m:
                posts[m.group(1)] += 1
    lines = ["# Wayback index summary", "", f"captures: {len(rows)}, with 200: {len(ok)}, unique 200 URLs: {len(urls)}", ""]
    lines.append("## Captures per target")
    lines += [f"- {k}: {v}" for k, v in by_target.most_common()]
    lines += ["", "## Kinds (status 200)"] + [f"- {k}: {v}" for k, v in kinds.most_common()]
    lines += ["", "## Capture years (status 200)"] + [f"- {k}: {v}" for k, v in sorted(years.items())]
    lines += ["", "## Dated posts per year"] + [f"- {k}: {v}" for k, v in sorted(posts.items())]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
