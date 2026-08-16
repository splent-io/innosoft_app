#!/usr/bin/env python3
"""Trim edition descriptions down to their own intro. One-off, idempotent.

The importer folded every informative page of a year (sustainability, TDAH,
grants, the English home copy...) into that year's edition description as
`<!-- wayback:URL -->` sections, and the edition's own home HTML already
carried the poster art as <figure><img> blocks. The result was an unreadable
wall with giant inline posters. This keeps only the leading intro (everything
before the first folded section) and drops the poster figures, which already
live in the edition's Posters section. The folded page content stays archived
in data/extracted/pages.json, so nothing is lost from the migration.

    docker exec -w /workspace/innosoft_app innosoft_app_web \
        python migration/wayback/clean_descriptions.py [--dry-run]
"""
from __future__ import annotations
import argparse, re


def clean(html: str) -> str:
    if not html:
        return html or ""
    # Drop every folded page: keep only what precedes the first marker.
    html = html.split("<!-- wayback:", 1)[0]
    # Drop an inline programme that duplicates the structured Programme
    # section: everything from the first heading whose text is exactly
    # "Programa" onward. Retrospective prose that sits before it is kept.
    html = re.sub(r"<(h[1-6])\b[^>]*>(?:\s|<[^>]+>)*programa(?:\s|<[^>]+>)*</\1>.*$", "", html, flags=re.I | re.S)
    # Drop every image (poster art, logos, mascots): images belong in the
    # edition's own sections (Posters, Gallery), never inline in the copy.
    html = re.sub(r"<figure\b.*?</figure>", "", html, flags=re.I | re.S)
    html = re.sub(r"<img\b[^>]*>", "", html, flags=re.I)
    # Drop plain sentences that only introduced a now-removed image and end
    # on a colon ("El logo de las jornadas fue el siguiente:").
    html = re.sub(
        r"<p>(?![^<]*<a\b)[^<]*(?:logo|cartel|mascota|imagen|foto)[^<]*:\s*</p>",
        "", html, flags=re.I,
    )
    # Drop paragraphs/headings left empty where an image used to sit.
    html = re.sub(r"<(p|h[1-6])>\s*(?:&nbsp;|<br\s*/?>)?\s*</\1>", "", html, flags=re.I)
    # Drop headings that only labelled a now-removed image (Logo, Mascota...).
    html = re.sub(
        r"<(h[1-6])>\s*(?:Logo(?:tipo)?|Mascota|Cartel(?:es)?)\s*</\1>\s*(?=<h[1-6]>|$)",
        "", html, flags=re.I,
    )
    # Tidy the leftover whitespace between block tags.
    html = re.sub(r">\s+<", "><", html).strip()
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from splent_cli.utils.dynamic_imports import get_app
    app = get_app()
    with app.app_context():
        from splent_framework.db import db
        from splent_io.splent_feature_editions.models import Edition

        changed = 0
        for ed in Edition.query.order_by(Edition.order).all():
            before = ed.description or ""
            after = clean(before)
            if after != before:
                changed += 1
                print(f"  {ed.name}: {len(before)} -> {len(after)} chars")
                if not args.dry_run:
                    ed.description = after
            else:
                print(f"  {ed.name}: already clean ({len(before)} chars)")
        if not args.dry_run:
            db.session.commit()
        print(f"\n{'DRY RUN ' if args.dry_run else ''}editions trimmed: {changed}")


if __name__ == "__main__":
    main()
