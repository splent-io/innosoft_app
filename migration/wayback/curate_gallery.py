#!/usr/bin/env python3
"""Curate the public gallery after the archive import: decide, for every
image in the media library, whether visitors should browse it.

Photos of the activities belong in the gallery. Posters, logos, flyers,
portraits, infographics, screenshots and site furniture do not: they still
live in the library (events, partners and posts reference them) but stay
out of /media and the homepage strip. Runs inside the web container:

    docker exec -w /workspace/innosoft_app innosoft_app_web \\
        python migration/wayback/curate_gallery.py [--apply]

Without --apply it only prints the decisions. Also gives the archived items
a human title (their original file name or the caption the archive gave
them) instead of the capture timestamp they were imported with.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEDIA_JSON = HERE / "data" / "extracted" / "media.json"

PHOTO_RX = re.compile(r"(^|[^a-z])(img|dsc|dscf|dscn|_mg|p\d{7}|photo|foto|jammers|selfie|grupo|equipo|team|clausura|apertura|ceremon)", re.I)
NOT_PHOTO_RX = re.compile(r"(cartel|poster|flyer|logo|banner|icon|captura|screenshot|infograf|horario|cronograma|programa|slide|thumb|cuadro|copilot|discord|unity|godot|gamekit|placeholder|favicon|qr|mapa|map|portada|cover|firma|plantilla|template|etsii|innosoft\.jpg|interior)", re.I)


def _norm(url: str) -> str:
    url = (url or "").strip()
    url = re.sub(r"^wayback://", "", url)
    url = url.replace("http://", "https://").replace("://innosoftdays.com", "://www.innosoftdays.com")
    return url.split("#")[0]


def _base(url: str) -> str:
    return re.sub(r"-\d{2,4}x\d{2,4}(\.[a-z0-9]+)$", r"\1", url, flags=re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    kinds: dict[str, dict] = {}
    if MEDIA_JSON.exists():
        for m in json.loads(MEDIA_JSON.read_text(encoding="utf-8")):
            u = _norm(m.get("url", ""))
            kinds[u] = m
            kinds[_base(u)] = m

    from splent_cli.utils.dynamic_imports import get_app
    from splent_framework.db import db

    app = get_app()
    with app.app_context():
        from splent_io.splent_feature_media.models import MediaItem

        decisions = {"in": [], "out": [], "keep": []}
        retitled = 0
        for item in MediaItem.query.order_by(MediaItem.id).all():
            if not item.is_image or not item.is_public:
                continue
            src = item.source_url or ""
            name = item.filename or ""
            reason = ""
            verdict = None
            if src.startswith("seed://"):
                verdict, reason = False, "bundled by a feature seeder (poster, logo, portrait)"
            elif src.startswith("wayback://"):
                url = _norm(src)
                meta = kinds.get(url) or kinds.get(_base(url)) or {}
                orig = url.rsplit("/", 1)[-1]
                stem = re.sub(r"\.[a-z0-9]+$", "", orig, flags=re.I)
                kind = (meta.get("kind") or "").lower()
                # Only camera-style names count as photos here: the archived
                # images embedded in posts are illustrations, AI renders and
                # screenshots even when the extraction called them "photo".
                if PHOTO_RX.search(stem) and not NOT_PHOTO_RX.search(stem):
                    verdict, reason = True, f"photo by file name ({orig})"
                else:
                    verdict, reason = False, f"archived illustration, archive kind '{kind or 'unknown'}', file {orig}"
                # human title instead of the capture timestamp
                caption = (meta.get("caption") or "").strip()
                if re.fullmatch(r"\d{14}", item.title or "") or not item.title:
                    new_title = caption if caption and not re.fullmatch(r"\d{14}", caption) else stem.replace("-", " ").replace("_", " ").strip()
                    if new_title and new_title != item.title:
                        item.title = new_title[:255]
                        retitled += 1
            elif src.startswith("http"):
                # The 2025 photo import (photos.json, full-size gallery photos).
                if NOT_PHOTO_RX.search(name) and not PHOTO_RX.search(name):
                    verdict, reason = False, f"imported by URL but named like an asset ({name})"
                else:
                    verdict, reason = True, "imported photo of the XIII edition"
            else:
                verdict, reason = None, "uploaded in the admin, editor decides"

            if verdict is None:
                decisions["keep"].append((item, reason))
                continue
            bucket = "in" if verdict else "out"
            decisions[bucket].append((item, reason))
            if args.apply and item.in_gallery != verdict:
                item.in_gallery = verdict

        for bucket, label in (("in", "IN the gallery"), ("out", "OUT of the gallery"), ("keep", "left as the editor set")):
            rows = decisions[bucket]
            print(f"\n== {label}: {len(rows)}")
            groups: dict[str, int] = {}
            for _, reason in rows:
                key = re.sub(r"\(.*\)$", "", reason).strip()
                groups[key] = groups.get(key, 0) + 1
            for k, n in sorted(groups.items(), key=lambda kv: -kv[1]):
                print(f"   {n:4d}  {k}")
            if bucket == "out":
                for item, reason in rows[:80]:
                    print(f"      - #{item.id} {item.filename}: {reason}")
        print(f"\nretitled archived items: {retitled}")
        if args.apply:
            db.session.commit()
            print("applied.")
        else:
            db.session.rollback()
            print("dry run (nothing written); rerun with --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
