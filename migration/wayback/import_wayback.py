#!/usr/bin/env python3
"""Phase 4: load data/extracted/*.json into the product.

Runs INSIDE the product's web container, where the app and its database are:

    docker exec -w /workspace/innosoft_app innosoft_app_web \\
        python migration/wayback/import_wayback.py [--only editions,events,...]

Idempotent end to end. Every row it creates is found again by a stable key
(edition slug, event slug inside its edition, member slug, post slug, media
source_key "wayback://<original url>"), so rerunning after fixing the JSON
updates instead of duplicating. Rows that already exist and were NOT created
by this importer (the seeded XIII edition and its programme, the seeded
speakers) are completed, never overwritten: an empty field is filled, a
filled one is left alone.

Images are taken from data/raw/ (the archived bytes), never from the live
Wayback Machine, so the import works offline and always the same.
"""

from __future__ import annotations

import argparse
import html as htmlmod
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
EXTRACTED = DATA / "extracted"
RAW = DATA / "raw"
MANIFEST = RAW / "manifest.jsonl"

ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV"}
KIND_MAP = {"talk": "talk", "workshop": "workshop", "competition": "competition", "ceremony": "ceremony", "social": "social", "stand": "stand", "mentoring": "mentoring", "other": "activity"}
# The XIII edition (2025) is already curated in the product (seeded programme
# and imported photos); the archive only fills empty fields of that edition.
SKIP_YEARS = {2025}


def _norm_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    url = re.sub(r"^https?://web\.archive\.org/web/\d+(?:id_|im_|js_|cs_)?/", "", url)
    url = url.replace("http://", "https://").replace("://innosoftdays.com", "://www.innosoftdays.com")
    return url.split("#")[0]


def _load(name: str):
    p = EXTRACTED / name
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


class RawFiles:
    """Original URL -> local raw file (latest capture), from the manifest."""

    def __init__(self):
        self.by_url: dict[str, Path] = {}
        if MANIFEST.exists():
            for line in MANIFEST.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                m = json.loads(line)
                if m.get("error") or not m.get("path"):
                    continue
                self.by_url[_norm_url(m["url"])] = RAW / m["path"]  # later timestamps overwrite earlier

    def find(self, url: str) -> Path | None:
        url = _norm_url(url)
        if url in self.by_url:
            return self.by_url[url]
        # WordPress size variants (-300x200) point at the same original.
        base = re.sub(r"-\d{2,4}x\d{2,4}(\.[a-z0-9]+)$", r"\1", url, flags=re.I)
        return self.by_url.get(base)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    only = set(x.strip() for x in args.only.split(",") if x.strip())

    from splent_cli.utils.dynamic_imports import get_app
    from splent_framework.db import db
    from splent_framework.utils.text import slugify

    app = get_app()
    with app.app_context():
        from splent_io.splent_feature_editions.models import Edition
        from splent_io.splent_feature_editions.services import EditionsService
        from splent_io.splent_feature_events.models import Event
        from splent_io.splent_feature_media.services import MediaService
        from splent_io.splent_feature_post.models import Category, Post
        from splent_io.splent_feature_team.models import Role, TeamMember

        raw = RawFiles()
        media = MediaService()
        stats: dict[str, int] = {}

        def bump(k):
            stats[k] = stats.get(k, 0) + 1

        def import_image(url: str, title: str = "", gallery: bool = False) -> str:
            """Media URL for an archived image, importing it once (under its
            original file name, out of the public gallery unless ``gallery``).
            "" if we do not hold the bytes."""
            if not url:
                return ""
            from splent_io.splent_feature_media.models import MediaItem

            # Already in the library from the 2025 migration (imported by URL)?
            existing = MediaItem.query.filter(MediaItem.source_url.in_([_norm_url(url), url, url.replace("https://", "http://")])).first()
            if existing is not None:
                bump("image_reused")
                return existing.url
            path = raw.find(url)
            if path is None or not path.exists():
                bump("image_missing")
                return ""
            import shutil
            import tempfile

            original_name = _norm_url(url).rsplit("/", 1)[-1] or path.name
            with tempfile.TemporaryDirectory() as tmp:
                staged = Path(tmp) / original_name
                shutil.copyfile(path, staged)
                item = media.import_from_file(
                    str(staged),
                    title=title or re.sub(r"\.[a-z0-9]+$", "", original_name, flags=re.I).replace("-", " ").replace("_", " "),
                    source_key="wayback://" + _norm_url(url),
                    in_gallery=gallery,
                )
            bump("image_ok")
            return item.url

        def rewrite_images(html: str) -> str:
            """Point every archived <img> at the media library. An image the
            archive never captured is removed rather than left as a broken
            box (both old sites are offline, so its src can never resolve)."""
            def repl(m):
                tag = m.group(0)
                srcm = re.search(r"""\ssrc=["']([^"']+)["']""", tag, flags=re.I)
                if not srcm:
                    return ""
                new = import_image(srcm.group(1))
                if not new:
                    bump("image_dropped")
                    return ""
                tag = tag[: srcm.start(1)] + new + tag[srcm.end(1):]
                # drop srcset/sizes (variants we do not hold) so src is used
                return re.sub(r"""\s(?:srcset|sizes)=["'][^"']*["']""", "", tag, flags=re.I)
            html = re.sub(r"<img\b[^>]*>", repl, html or "", flags=re.I)
            # figures and links left without their image
            html = re.sub(r"<figure>\s*(?:<figcaption>.*?</figcaption>)?\s*</figure>", "", html, flags=re.I | re.S)
            html = re.sub(r"<a\b[^>]*>\s*</a>", "", html, flags=re.I)
            return html

        def fill(obj, **fields):
            """Set only the empty attributes; report whether anything changed."""
            changed = False
            for k, v in fields.items():
                if v in (None, "", []):
                    continue
                if getattr(obj, k, None) in (None, "", 0) or (isinstance(getattr(obj, k, None), str) and not getattr(obj, k).strip()):
                    setattr(obj, k, v)
                    changed = True
            return changed

        # ── Editions ────────────────────────────────────────────────────
        editions_by_year: dict[int, Edition] = {}
        for e in Edition.query.all():
            if e.starts_on:
                editions_by_year[e.starts_on.year] = e
        if not only or "editions" in only:
            for ed in sorted(_load("editions.json"), key=lambda x: x.get("year", 0)):
                year = int(ed["year"])
                number = ed.get("number")
                roman = ed.get("roman") or (ROMAN.get(int(number)) if number else "")
                name = ed.get("name") or (f"InnoSoft Days {roman}" if roman else f"InnoSoft Days {year}")
                slug = slugify(name)
                edition = editions_by_year.get(year) or Edition.query.filter_by(slug=slug).first()
                if edition is None:
                    edition = Edition(name=name, slug=slug, published=True, is_current=False)
                    db.session.add(edition)
                    bump("edition_created")
                else:
                    bump("edition_updated")
                fill(
                    edition,
                    number=int(number) if number else None,
                    starts_on=datetime.fromisoformat(ed["starts_on"]).date() if ed.get("starts_on") else None,
                    ends_on=datetime.fromisoformat(ed["ends_on"]).date() if ed.get("ends_on") else None,
                    venue=ed.get("venue", ""),
                    summary=ed.get("summary", ""),
                    description=rewrite_images(ed.get("description_html", "")),
                    # registration_url of past editions are dead links; skipped
                    order=int(number) if number else 0,
                )
                if not edition.image and ed.get("image_url"):
                    edition.image = import_image(ed["image_url"], title=name)
                db.session.flush()
                editions_by_year[year] = edition
            # Informative pages of a year (about, sustainability, organisation
            # copy) become sections of that edition's description, once.
            for pg in _load("pages.json"):
                year = pg.get("edition_year")
                if not year or int(year) not in editions_by_year or int(year) in SKIP_YEARS:
                    continue
                if (pg.get("kind") or "other") in ("how_to_get",):
                    continue
                edition = editions_by_year[int(year)]
                title = (pg.get("title") or "").strip()
                body = rewrite_images(pg.get("content_html", ""))
                if not body:
                    continue
                marker = f'<!-- wayback:{_norm_url(pg.get("url", ""))} -->'
                if marker in (edition.description or ""):
                    continue
                section = f"\n{marker}\n" + (f"<h2>{title}</h2>\n" if title else "") + body
                edition.description = (edition.description or "") + section
                bump("page_folded")
            db.session.commit()

        # ── Events ──────────────────────────────────────────────────────
        if not only or "events" in only:
            svc = EditionsService()
            for ev in _load("events.json"):
                year = int(ev["edition_year"])
                if year in SKIP_YEARS:
                    bump("event_skipped_curated_year")
                    continue
                edition = editions_by_year.get(year)
                if edition is None:
                    bump("event_without_edition")
                    continue
                title = (ev.get("title") or "").strip()
                if not title:
                    continue
                base_slug = slugify(title) or "event"
                slug = f"{base_slug}-{year}" if Event.query.filter(Event.slug == base_slug, Event.edition_id != edition.id).first() else base_slug
                event = Event.query.filter_by(slug=slug).first()
                if event is None:
                    # a seeded event of the same edition with the same title
                    event = Event.query.filter(Event.edition_id == edition.id, Event.title == title).first()
                if event is None:
                    event = Event(title=title, slug=slug, edition_id=edition.id, published=True)
                    db.session.add(event)
                    bump("event_created")
                else:
                    bump("event_updated")
                starts = datetime.fromisoformat(ev["starts_at"]) if ev.get("starts_at") else None
                ends = datetime.fromisoformat(ev["ends_at"]) if ev.get("ends_at") else None
                fill(
                    event,
                    kind=KIND_MAP.get((ev.get("kind") or "talk").lower(), "talk"),
                    summary=ev.get("summary", ""),
                    description=rewrite_images(ev.get("description_html", "")),
                    speaker=(ev.get("speaker") or "") + (f" ({ev['company']})" if ev.get("company") and ev.get("speaker") else ""),
                    room=ev.get("room", "") or ("Online" if ev.get("modality") == "online" else ""),
                    starts_at=starts,
                    ends_at=ends,
                    link=ev.get("link", ""),
                )
                if event.edition_id is None:
                    event.edition_id = edition.id
                if not event.image and ev.get("poster_url"):
                    event.image = import_image(ev["poster_url"], title=title)
            db.session.commit()

        # ── Team: speakers and organisers ───────────────────────────────
        def role(name: str, order: int) -> Role:
            r = Role.query.filter_by(slug=slugify(name)).first()
            if r is None:
                r = Role(name=name, slug=slugify(name), order=order)
                db.session.add(r)
                db.session.flush()
            return r

        def member(name: str, published: bool = True):
            """Return (member, created). New members are published only when
            asked: speakers are public figures, but the per-edition organising
            committees are hundreds of students, so they are imported
            unpublished (kept and editable in the admin, off the public /team)."""
            slug = slugify(name)
            m = TeamMember.query.filter_by(slug=slug).first()
            if m is None:
                m = TeamMember(name=name.strip(), slug=slug, published=published)
                db.session.add(m)
                db.session.flush()
                bump("member_created")
                return m, True
            bump("member_updated")
            return m, False

        if not only or "team" in only:
            for sp in _load("speakers.json"):
                name = (sp.get("name") or "").strip()
                if not name:
                    continue
                if sp.get("edition_years") and set(int(y) for y in sp["edition_years"]) <= SKIP_YEARS:
                    bump("speaker_skipped_curated_year")
                    continue
                m, _ = member(name, published=True)
                if not m.published:  # promote a former organiser who also spoke
                    m.published = True
                # Speakers are grouped by edition: one "Ponentes <roman>" role
                # per year they took part in, so /team is not one flat list.
                for y in sp.get("edition_years", []):
                    if int(y) in SKIP_YEARS:
                        continue
                    rn = ROMAN.get(int(y) - 2012, str(y))
                    r = role(f"Ponentes {rn}", 100 - (int(y) - 2012))
                    if r not in m.roles:
                        m.roles.append(r)
                fill(m, affiliation=sp.get("affiliation", ""), position=sp.get("position", ""), bio=sp.get("bio_html", ""), link=(sp.get("links") or [{}])[0].get("url", "") if sp.get("links") else "")
                if sp.get("links") and not m.links:
                    m.links = sp["links"]
                if not m.photo and sp.get("photo_url"):
                    m.photo = import_image(sp["photo_url"], title=name)
            for org in _load("organisers.json"):
                name = (org.get("name") or "").strip()
                if not name:
                    continue
                year = int(org["edition_year"])
                edition = editions_by_year.get(year)
                roman = ROMAN.get(edition.number) if edition and edition.number else str(year)
                r = role(f"Organización {roman}", 100 - (edition.number or 0) if edition else 100)
                m, _ = member(name, published=False)
                fill(m, position=org.get("role", ""))
                if not m.photo and org.get("photo_url"):
                    m.photo = import_image(org["photo_url"], title=name)
                if r not in m.roles:
                    m.roles.append(r)
            db.session.commit()

        # ── News ────────────────────────────────────────────────────────
        if not only or "posts" in only:
            for p in _load("posts.json"):
                title = (p.get("title") or "").strip()
                slug = (p.get("slug") or slugify(title))[:255]
                if not slug:
                    continue
                post = Post.query.filter_by(slug=slug).first()
                if post is None:
                    post = Post(title=title, slug=slug, status="published", comment_status="closed")
                    db.session.add(post)
                    bump("post_created")
                else:
                    bump("post_updated")
                fill(
                    post,
                    excerpt=htmlmod.unescape(re.sub(r"<[^>]+>", "", p.get("excerpt") or ""))[:1000],
                    content=rewrite_images(p.get("content_html", "")),
                )
                # The publication date is authoritative (it drives the
                # permalink), so set it directly rather than only-if-empty.
                if p.get("date"):
                    try:
                        post.published_at = datetime.fromisoformat(p["date"])
                    except ValueError:
                        pass
                if not post.featured_image and p.get("featured_image_url"):
                    post.featured_image = import_image(p["featured_image_url"], title=title)
                year = p.get("edition_year")
                if year and int(year) in editions_by_year:
                    edition = editions_by_year[int(year)]
                    cat = Category.query.filter_by(slug=edition.slug).first()
                    if cat is None:
                        cat = Category(name=edition.name, slug=edition.slug)
                        db.session.add(cat)
                        db.session.flush()
                    if cat not in post.categories:
                        post.categories.append(cat)
                for cname in p.get("categories") or []:
                    cslug = slugify(cname)
                    if not cslug or cslug == "uncategorized" or cslug == "sin-categoria":
                        continue
                    cat = Category.query.filter_by(slug=cslug).first()
                    if cat is None:
                        cat = Category(name=cname, slug=cslug)
                        db.session.add(cat)
                        db.session.flush()
                    if cat not in post.categories:
                        post.categories.append(cat)
            db.session.commit()

        # ── Standalone media (photos, posters not attached elsewhere) ────
        if not only or "media" in only:
            for m in _load("media.json"):
                year = m.get("edition_year")
                if year and int(year) in SKIP_YEARS:
                    continue
                edition = editions_by_year.get(int(year)) if year else None
                title = m.get("caption") or (edition.name if edition else "InnoSoft Days")
                name = _norm_url(m["url"]).rsplit("/", 1)[-1]
                is_photo = (m.get("kind") == "photo") and bool(re.search(r"(^|[^a-z])(img|dsc|_mg|photo|foto|jammers)", name, re.I))
                import_image(m["url"], title=title, gallery=is_photo)
            db.session.commit()

        print(json.dumps(stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
