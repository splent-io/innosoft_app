#!/usr/bin/env python3
"""Attach the posters (carteles) to their editions, by year. One-off,
idempotent. Posters are the images the gallery curation left out that are
promotional art: the archive's poster-classified images plus the seeded
event posters, matched to an edition by year and linked as kind="poster".

    docker exec -w /workspace/innosoft_app innosoft_app_web \\
        python migration/wayback/link_posters.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEDIA_JSON = HERE / "data" / "extracted" / "media.json"
POSTER_RX = re.compile(r"(cartel|poster|flyer|afiche)", re.I)


def _norm(url):
    url = re.sub(r"^wayback://", "", url or "")
    return url.replace("http://", "https://").replace("://innosoftdays.com", "://www.innosoftdays.com").split("#")[0]


def year_of(item, meta):
    src = item.source_url or ""
    m = re.search(r"/uploads/(20\d\d)/", src)
    if m:
        return int(m.group(1))
    md = meta.get(_norm(src))
    if md and md.get("edition_year"):
        return int(md["edition_year"])
    # seeded XIII event posters
    if src.startswith("seed://events/"):
        return 2025
    return None


def is_poster(item, meta):
    src = item.source_url or ""
    name = item.filename or ""
    if src.startswith("seed://events/"):
        return True  # the XIII programme posters
    md = meta.get(_norm(src))
    if md and (md.get("kind") == "poster"):
        return True
    return bool(POSTER_RX.search(name) or POSTER_RX.search(src))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    meta = {}
    if MEDIA_JSON.exists():
        for m in json.loads(MEDIA_JSON.read_text()):
            meta[_norm(m.get("url", ""))] = m

    from splent_cli.utils.dynamic_imports import get_app
    app = get_app()
    with app.app_context():
        from splent_io.splent_feature_media.models import MediaItem
        from splent_io.splent_feature_editions.models import Edition
        from splent_io.splent_feature_editions.services import EditionsService
        svc = EditionsService()
        editions_by_year = {e.starts_on.year: e for e in Edition.query.all() if e.starts_on}

        buckets = {}
        for item in MediaItem.query.filter_by(access="public").filter(MediaItem.mime_type.like("image/%")).all():
            if not is_poster(item, meta):
                continue
            y = year_of(item, meta)
            ed = editions_by_year.get(y) if y else None
            if ed is None:
                continue
            buckets.setdefault(ed.id, []).append(item.id)

        total = 0
        for ed_id, ids in sorted(buckets.items()):
            ed = Edition.query.get(ed_id)
            if args.dry_run:
                n = len(set(ids) - svc.photo_media_ids(ed, "poster"))
            else:
                n = svc.attach_photos(ed, ids, kind="poster")
            total += n
            print(f"  {ed.name}: {'would add' if args.dry_run else 'added'} {n} poster(s)")
        print(f"\n{'DRY RUN ' if args.dry_run else ''}total posters attached: {total}")


if __name__ == "__main__":
    sys.exit(main())
