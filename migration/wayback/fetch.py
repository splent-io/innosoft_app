#!/usr/bin/env python3
"""Phase 2: download every relevant capture listed in data/index.jsonl into
data/raw/, so parsing works offline and stays reproducible.

One file per (URL, digest): the same page captured with different content
(the home page or /es/cronograma/ of a different year) is kept once per
version. Raw bytes are saved exactly as archived (`id_` flag, no Wayback
toolbar rewriting) next to a manifest line in data/raw/manifest.jsonl.

Polite and resumable: PAUSE seconds between requests, exponential backoff on
429/503, and anything already in the manifest is skipped.

Usage: python3 fetch.py [--kinds page,event,...] [--limit N] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
INDEX = DATA / "index.jsonl"
RAW = DATA / "raw"
MANIFEST = RAW / "manifest.jsonl"

PAUSE = 1.6
UA = "innosoft-days-archive-recovery/1.0 (contact: innosoftdays@gmail.com)"
DEFAULT_KINDS = ["page", "event", "event-index", "post", "speaker", "upload", "file"]
# Bigger than this and it is a video or a zip we do not need for the site.
MAX_BYTES = 25 * 1024 * 1024


def _norm(url: str) -> str:
    """innosoftdays.com and www.innosoftdays.com are one site."""
    return url.replace("://innosoftdays.com", "://www.innosoftdays.com").replace("http://", "https://")


def load_targets(kinds: set[str]) -> list[dict]:
    seen = set()
    out = []
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("statuscode") != "200" or r.get("kind") not in kinds:
            continue
        key = (_norm(r["original"]), r.get("digest"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    # Oldest capture first inside a URL, so the version history reads in order.
    out.sort(key=lambda r: (_norm(r["original"]), r["timestamp"]))
    return out


def already(manifest: Path) -> set:
    done = set()
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                m = json.loads(line)
                if m.get("path"):  # errors are retried on the next run
                    done.add((m["url"], m["digest"]))
    return done


def fetch(url: str, attempt: int = 0) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            ctype = resp.headers.get("Content-Type", "")
            data = resp.read(MAX_BYTES + 1)
            return data[:MAX_BYTES], ctype
    except urllib.error.HTTPError as e:
        if e.code in (429, 503, 502, 504) and attempt < 8:
            wait = min(900, 5 * (2 ** (attempt + 1)))
            print(f"    {e.code}, waiting {wait}s", flush=True)
            time.sleep(wait)
            return fetch(url, attempt + 1)
        raise
    except (urllib.error.URLError, TimeoutError, ConnectionResetError) as e:
        # Transport hiccups (a refused connection on one of the archive's
        # front ends) clear in seconds; only repeated ones back off.
        if attempt < 8:
            wait = 3 if attempt < 3 else min(300, 5 * (2 ** (attempt - 2)))
            print(f"    {e}, waiting {wait}s", flush=True)
            time.sleep(wait)
            return fetch(url, attempt + 1)
        raise


def ext_for(url: str, ctype: str, mime_hint: str) -> str:
    base = url.split("?")[0]
    if "." in base.rsplit("/", 1)[-1]:
        return "." + base.rsplit(".", 1)[-1].lower()[:5]
    guess = mimetypes.guess_extension((ctype or mime_hint or "").split(";")[0].strip()) or ".html"
    return ".html" if guess in (".htm", ".html", ".xhtml") else guess


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinds", default=",".join(DEFAULT_KINDS))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--shard", default="", help="i/n: process every n-th target starting at i (run n workers side by side)")
    args = ap.parse_args()
    kinds = set(k.strip() for k in args.kinds.split(",") if k.strip())
    RAW.mkdir(parents=True, exist_ok=True)
    targets = load_targets(kinds)
    done = already(MANIFEST)
    todo = [t for t in targets if (_norm(t["original"]), t.get("digest")) not in done]
    print(f"  targets: {len(targets)}, already fetched: {len(targets) - len(todo)}, to fetch: {len(todo)}", flush=True)
    if args.dry_run:
        return 0
    if args.shard:
        i, n = (int(x) for x in args.shard.split("/"))
        todo = todo[i::n]
    if args.limit:
        todo = todo[: args.limit]
    ok = err = 0
    with MANIFEST.open("a", encoding="utf-8") as mf:
        for i, r in enumerate(todo, 1):
            url = _norm(r["original"])
            ts = r["timestamp"]
            wb = f"https://web.archive.org/web/{ts}id_/{r['original']}"
            try:
                data, ctype = fetch(wb)
            except Exception as e:
                err += 1
                print(f"  [{i}/{len(todo)}] FAIL {ts} {url}: {e}", flush=True)
                mf.write(json.dumps({"url": url, "timestamp": ts, "digest": r.get("digest"), "kind": r["kind"], "error": str(e)}, ensure_ascii=False) + "\n")
                mf.flush()
                time.sleep(PAUSE)
                continue
            key = hashlib.sha1(url.encode()).hexdigest()[:16]
            folder = RAW / r["kind"] / key
            folder.mkdir(parents=True, exist_ok=True)
            fname = ts + ext_for(url, ctype, r.get("mimetype", ""))
            (folder / fname).write_bytes(data)
            (folder / "url.txt").write_text(url + "\n")
            mf.write(json.dumps({"url": url, "timestamp": ts, "digest": r.get("digest"), "kind": r["kind"], "path": str((folder / fname).relative_to(RAW)), "bytes": len(data), "content_type": ctype}, ensure_ascii=False) + "\n")
            mf.flush()
            ok += 1
            if i % 25 == 0 or i == len(todo):
                print(f"  [{i}/{len(todo)}] ok={ok} err={err}", flush=True)
            time.sleep(PAUSE)
    print(f"  done: ok={ok} err={err}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
