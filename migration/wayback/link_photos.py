#!/usr/bin/env python3
"""Distribute the gallery photos into their editions' albums, by year.

One-off, idempotent. For each public gallery image, work out its year (from
the archived upload path wayback://.../uploads/YYYY/, from the "InnoSoft Days
YYYY" import title, or from the media.json edition_year), then attach it to
the edition whose dates fall in that year. Runs inside the web container:

    docker exec -w /workspace/innosoft_app innosoft_app_web \\
        python migration/wayback/link_photos.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEDIA_JSON = HERE / "data" / "extracted" / "media.json"


def year_of(item, media_meta):
    src = item.source_url or ""
    m = re.search(r"/uploads/(20\d\d)/", src)
    if m:
        return int(m.group(1))
    m = re.search(r"InnoSoft Days\s+(20\d\d)", item.title or "")
    if m:
        return int(m.group(1))
    # the 2025 gallery import titled by day / "InnoSoft Days 2025"
    if src.startswith("http") and ("2025" in src or "innosoftdays.com" in src):
        return 2025
    meta = media_meta.get(_norm(src))
    if meta and meta.get("edition_year"):
        return int(meta["edition_year"])
    return None


def _norm(url):
    url = re.sub(r"^wayback://", "", url or "")
    return url.replace("http://", "https://").replace("://innosoftdays.com", "://www.innosoftdays.com").split("#")[0]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    media_meta = {}
    if MEDIA_JSON.exists():
        for m in json.loads(MEDIA_JSON.read_text()):
            media_meta[_norm(m.get("url", ""))] = m

    from splent_cli.utils.dynamic_imports import get_app
    app = get_app()
    with app.app_context():
        from splent_io.splent_feature_media.models import MediaItem
        from splent_io.splent_feature_editions.models import Edition
        from splent_io.splent_feature_editions.services import EditionsService
        svc = EditionsService()
        editions_by_year = {e.starts_on.year: e for e in Edition.query.all() if e.starts_on}

        buckets = {}
        skipped = 0
        for item in MediaItem.query.filter_by(in_gallery=True).all():
            if not item.is_image:
                continue
            y = year_of(item, media_meta)
            ed = editions_by_year.get(y) if y else None
            if ed is None:
                skipped += 1
                continue
            buckets.setdefault(ed.id, []).append(item.id)

        total = 0
        for ed_id, media_ids in sorted(buckets.items()):
            ed = Edition.query.get(ed_id)
            if args.dry_run:
                n = len(set(media_ids) - svc.photo_media_ids(ed))
            else:
                n = svc.attach_photos(ed, media_ids)
            total += n
            print(f"  {ed.name}: {'would add' if args.dry_run else 'added'} {n} (of {len(media_ids)} matched)")
        print(f"\n{'DRY RUN ' if args.dry_run else ''}total attached: {total}; unmatched gallery photos: {skipped}")


if __name__ == "__main__":
    sys.exit(main())
