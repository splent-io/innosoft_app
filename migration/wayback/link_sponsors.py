#!/usr/bin/env python3
"""Attach each edition's sponsors/collaborators, from the companies that took
part in it. One-off, idempotent. Companies come from the extracted events
(events.json `company`); a matching global partner is reused, otherwise a new
partner is created as a wordmark (no logo) kept OFF the homepage strip
(active=False) and linked to its edition. The current curated partners are
also attached to the current edition.

    docker exec -w /workspace/innosoft_app innosoft_app_web \\
        python migration/wayback/link_sponsors.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENTS = HERE / "data" / "extracted" / "events.json"


def norm(name):
    return re.sub(r"\s+", " ", (name or "").strip()).lower().replace("ntt data", "ntt data")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    events = json.loads(EVENTS.read_text()) if EVENTS.exists() else []
    by_year = defaultdict(set)
    for e in events:
        c = (e.get("company") or "").strip()
        if c and e.get("edition_year"):
            by_year[int(e["edition_year"])].add(c)

    from splent_cli.utils.dynamic_imports import get_app
    from splent_framework.db import db
    app = get_app()
    with app.app_context():
        from splent_io.splent_feature_editions.models import Edition
        from splent_io.splent_feature_editions.services import EditionsService
        from splent_io.splent_feature_partners.models import Partner
        svc = EditionsService()
        editions_by_year = {e.starts_on.year: e for e in Edition.query.all() if e.starts_on}
        partners_by_name = {norm(p.name): p for p in Partner.query.all()}

        created = 0; attached = 0
        for year, companies in sorted(by_year.items()):
            ed = editions_by_year.get(year)
            if ed is None:
                continue
            ids = []
            for company in sorted(companies):
                key = norm(company)
                p = partners_by_name.get(key)
                if p is None:
                    if args.dry_run:
                        created += 1; ids.append(-1); continue
                    p = Partner(name=company, link="", active=False, order=0)
                    db.session.add(p); db.session.flush()
                    partners_by_name[key] = p; created += 1
                ids.append(p.id)
            real_ids = [i for i in ids if i and i > 0]
            if args.dry_run:
                n = len(set(real_ids) - svc.sponsor_partner_ids(ed))
            else:
                n = svc.attach_sponsors(ed, real_ids)
            attached += n
            print(f"  {ed.name}: {len(companies)} companies -> {'would attach' if args.dry_run else 'attached'} {n}")

        # the current curated partners (active on the home) sponsor the current edition
        current = svc.current()
        if current is not None:
            cur = [p.id for p in Partner.query.filter_by(active=True).all()]
            if args.dry_run:
                n = len(set(cur) - svc.sponsor_partner_ids(current))
            else:
                n = svc.attach_sponsors(current, cur)
            attached += n
            print(f"  {current.name} (current): attached {n} curated partners")

        if not args.dry_run:
            db.session.commit()
        print(f"\n{'DRY RUN ' if args.dry_run else ''}partners created: {created}, sponsor links added: {attached}")


if __name__ == "__main__":
    sys.exit(main())
