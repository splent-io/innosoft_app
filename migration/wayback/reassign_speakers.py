#!/usr/bin/env python3
"""Reorganise the speaker roles by edition. One-off, idempotent.

Every speaker was seeded under a single flat "Ponentes" role, which made
/team a flat list of 155. This assigns each speaker to a per-edition role
"Ponentes <roman>" from the extracted edition_years, so the team page groups
speakers by edition. The old flat role is removed at the end.

    docker exec -w /workspace/innosoft_app innosoft_app_web \\
        python migration/wayback/reassign_speakers.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEAKERS = HERE / "data" / "extracted" / "speakers.json"

ROMAN = {2013+i-2012: r for i, r in enumerate(
    ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV"], start=1)}
# year -> roman: year-2012 gives the ordinal
def roman_for_year(y): 
    n = y - 2012
    vals=[(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")]; out=""
    for v,s in vals:
        while n>=v: out+=s; n-=v
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data = json.loads(SPEAKERS.read_text()) if SPEAKERS.exists() else []

    from splent_cli.utils.dynamic_imports import get_app
    from splent_framework.db import db
    from splent_framework.utils.text import slugify
    app = get_app()
    with app.app_context():
        from splent_io.splent_feature_team.models import Role, TeamMember

        def get_role(name, order):
            slug = slugify(name)
            r = Role.query.filter_by(slug=slug).first()
            if r is None and not args.dry_run:
                r = Role(name=name, slug=slug, order=order); db.session.add(r); db.session.flush()
            return r

        assigned = 0; missing = 0; years = set()
        for sp in data:
            member = TeamMember.query.filter_by(slug=slugify(sp.get("name",""))).first()
            if member is None:
                missing += 1; continue
            for y in sp.get("edition_years", []):
                rn = roman_for_year(int(y)); years.add(int(y))
                # recent editions first: higher year -> lower order
                role = get_role(f"Ponentes {rn}", 100 - (int(y) - 2012))
                if role is not None and not args.dry_run and role not in member.roles:
                    member.roles.append(role); assigned += 1
                elif args.dry_run:
                    assigned += 1
        # drop the flat "Ponentes" role (members keep their per-edition roles)
        flat = Role.query.filter_by(slug="ponentes").first()
        if flat is not None and not args.dry_run:
            db.session.delete(flat)
        if not args.dry_run:
            db.session.commit()
        print(f"{'DRY RUN ' if args.dry_run else ''}assigned {assigned} speaker-edition roles across years {sorted(years)}; {missing} speakers not found")
        if not args.dry_run:
            for r in Role.query.filter(Role.slug.like("ponentes-%")).order_by(Role.order).all():
                print(f"  {r.name}: {sum(1 for m in r.members if m.published)} published")


if __name__ == "__main__":
    sys.exit(main())
