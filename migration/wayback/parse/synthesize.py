#!/usr/bin/env python3
"""Phase 3c: merge every per-family part (data/extracted/parts/*.json) into
the final data/extracted/{editions,events,speakers,organisers,posts,pages,
media}.json following the README schema, plus data/extracted/REPORT.md.

Deterministic and rerunnable: no network, no randomness, stable ordering.

Merge rules (see REPORT.md for the outcome):

* editions  one entry per year documented by any part; fields taken from the
            source with the highest confidence, ties broken by a per-field
            family priority (dates: edition/timetable pages > event pages >
            posts); name is always "InnoSoft Days <roman>", number = year-2012.
* events    clustered per year with a greedy best-match on normalised title
            (generic prefixes such as "Conferencia –", "Charla de", "Taller"
            removed), date compatibility and speaker identity; a family never
            merges with itself (a family does not duplicate its own events).
            Longest description wins, times by majority of the dated sources
            then family priority, source_url of the richest source.
* speakers  clustered on accent/case-insensitive names with subset matching
            ("Clara Grima" ~ "Clara Isabel Grima Ruiz") and one-typo tolerance
            on surnames, blocked when the affiliations are incompatible
            (two "Daniel García" in 2022: PRiSE vs SUSE); fields merged, years
            unioned; event speaker strings are canonicalised to the merged name.
* organisers deduped per (year, name); posts by slug; pages by url; media by
            image (WordPress size variants and the institucional host collapse
            into the media family's canonical url).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from parse.common import (  # noqa: E402
    EXTRACTED,
    edition_number_for_year,
    name_key,
    name_tokens,
    norm_key,
    norm_media_url,
    roman,
    same_person,
    strip_accents,
)

PARTS = EXTRACTED / "parts"

# ---------------------------------------------------------------------------
# Family priorities (index 0 = most trusted). Used only to break ties.

FAMILY_ORDER = [
    "events_eventos_etn",  # 2024 plugins, edited until the event
    "events_mec",          # MEC event pages 2017-2024, explicit times
    "institucional",       # institucional.us.es snapshots 2018-2021
    "people",              # speaker/organisation pages
    "pages_editions",      # edition archive pages, calendars, 2025 site
    "posts_2023_2024",
    "posts_2022",
    "posts_2021",
    "posts_2018_2020",
    "posts_2025",
    "media",
]
FAMILY_RANK = {f: i for i, f in enumerate(FAMILY_ORDER)}

# Times: the institucional calendar captured on 2021-11-14 (corrected
# programme, one day before the second week) beats the 2024 MEC copy of the
# same 2021 events (stale for "Introducción al hacking 3").
TIME_ORDER_BY_YEAR = {2021: ["institucional", "events_eventos_etn", "events_mec", "people", "pages_editions"]}

# Editions: edition/timetable pages > institucional site > event pages > posts.
EDITION_ORDER = ["pages_editions", "institucional", "events_eventos_etn", "events_mec", "posts_2023_2024", "posts_2022", "posts_2021", "posts_2018_2020"]
EDITION_TEXT_ORDER = ["pages_editions", "institucional", "posts_2023_2024", "posts_2022", "posts_2021", "posts_2018_2020", "events_eventos_etn", "events_mec"]
CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2, None: 3}

# Speakers: portrait/bio sources first.
SPEAKER_ORDER = ["people", "events_eventos_etn", "posts_2023_2024", "posts_2022", "posts_2021", "posts_2018_2020", "pages_editions", "institucional", "events_mec"]

# Media: the media family already collapsed variants and adopted hand-picked
# kinds/captions from the others.
MEDIA_ORDER = ["media", "pages_editions", "posts_2023_2024", "posts_2022", "posts_2018_2020", "events_eventos_etn", "events_mec", "institucional"]

KINDS = {"talk", "workshop", "competition", "ceremony", "social", "stand", "mentoring", "other"}
MODALITIES = {"in_person", "online"}

# Names written differently by the sources for the same person (nickname,
# typo, first names only). Applied before clustering; documented in REPORT.
SPEAKER_ALIASES = {
    "paco profe": "Francisco Pérez Fernández",          # 2021 'Becario en Ciberseguridad' (posts_2021 names him)
    "javier antonio perez": "José Antonio Pérez",       # 2024 MEC typo of the TEC/ETN speaker
    "pablo y alberto": "Pablo Pérez y Alberto Olmo",    # 2024 MEC 'Charla Proyecto de investigación – Pablo y Alberto' (VOLUM)
    "anabel carmona guitierrez": "Anabel Carmona Gutiérrez",
    "israel blancas alvares": "Israel Blancas Álvarez",
    "paula garrido lerman": "Paula Garrido Lerma",
    "carlos perez": "Carlos Pérez",
}
SPEAKER_ALIASES = {name_key(k): v for k, v in SPEAKER_ALIASES.items()}
# Speaker records that are not one person (kept as free text on the event).
SPEAKER_DROP = {"andres adolfo"}

# Container entries of the MEC calendar (whole-day/whole-edition blocks).
UMBRELLA_TITLE = re.compile(r"^innosoft days( 20\d\d| dia \d)$")

STOPWORDS = {"de", "la", "el", "los", "las", "y", "e", "a", "en", "del", "al", "con", "para", "por", "sobre", "un", "una", "unos", "unas", "que", "se", "su", "sus", "lo", "o", "u", "es", "the", "of", "and", "in", "to", "on", "sr", "sra", "d", "don"}
TITLE_PREFIX = re.compile(r"^(?:(?:conferencia|taller|proyeccion|charla|ponencia|seminario|keynote|informacion sobre la ponencia|informacion de la charla|informacion sobre la charla|resumen)\s+(?:de\s+la\s+|de\s+los\s+|del\s+|de\s+|sobre\s+)?(?:sr\s+|sra\s+|la\s+sra\s+|el\s+sr\s+)?)+")

# ---------------------------------------------------------------------------
# helpers


def load_parts(kind: str) -> list[tuple[str, dict]]:
    out = []
    for p in sorted(PARTS.glob(f"*.{kind}.json")):
        family = p.name[: -len(f".{kind}.json")]
        for item in json.loads(p.read_text(encoding="utf-8")):
            out.append((family, item))
    return out


def rank(family: str, order: list[str] | None = None) -> int:
    if order and family in order:
        return order.index(family)
    base = len(order) if order else 0
    return base + FAMILY_RANK.get(family, 99)


def html_text(html: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def norm_dt(v: str | None) -> str | None:
    """'2024-11-05T08:25' -> '2024-11-05T08:25:00'; date-only stays."""
    if not v:
        return None
    v = v.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", v):
        return v + ":00"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", v):
        return v
    m = re.match(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", v)
    if m:
        return f"{m.group(1)}T{m.group(2)}:00"
    return v


def is_full_dt(v: str | None) -> bool:
    return bool(v) and "T" in v


def date_of(v: str | None) -> str | None:
    return v[:10] if v else None


def minutes_of(v: str) -> int:
    return int(v[11:13]) * 60 + int(v[14:16])


TITLE_SYNONYMS = [
    (re.compile(r"\binteligencia artificial\b"), "ia"),
    (re.compile(r"\b(?:gymkhana|gymkana|gincana|gimcana|yincana|yinkana)\b"), "yincana"),
    (re.compile(r"\b(?:concurso|competicion|campeonato|torneo)\b"), "torneo"),
    (re.compile(r"\b(?:scape|escape) room\b"), "escaperoom"),
    (re.compile(r"\bhackat[oh]n\b"), "hackathon"),
    (re.compile(r"\bcl[aá]usura\b"), "clausura"),
]


def title_key(title: str) -> str:
    k = norm_key(title)
    k = re.sub(r"\bmª\b", "maria", k)
    k = TITLE_PREFIX.sub("", k).strip()
    k = re.sub(r"\s*(keynote)$", "", k).strip()
    for rx, rep in TITLE_SYNONYMS:
        k = rx.sub(rep, k)
    return k or norm_key(title)


def sig_tokens(key: str) -> frozenset:
    return frozenset(t for t in key.split() if t not in STOPWORDS)


def title_similarity(a: str, b: str) -> float:
    ka, kb = title_key(a), title_key(b)
    if ka == kb:
        return 1.0
    ja, jb = ka.replace(" ", ""), kb.replace(" ", "")
    if len(ja) >= 10 and levenshtein1(ja, jb) and re.findall(r"\d+", ka) == re.findall(r"\d+", kb):
        return 0.9
    sa, sb = sig_tokens(ka), sig_tokens(kb)
    if not sa or not sb:
        return 0.0
    small, big = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    if small <= big:
        if len(small) >= 2:
            return 0.8
        tok = next(iter(small))
        return 0.6 if len(tok) >= 6 else 0.0
    return len(sa & sb) / len(sa | sb)


SPLIT_SPEAKERS = re.compile(r"\s*(?:,|;|/| y | e | and |&)\s*", flags=re.I)


def split_persons(s: str | None) -> list[str]:
    if not s:
        return []
    s = SPEAKER_ALIASES.get(name_key(s), s)
    s = re.sub(r"^(jurado|ponentes?|moderador[a]?)\s*:\s*", "", s.strip(), flags=re.I)
    s = re.sub(r"\(.*?\)", " ", s)
    parts = [p.strip(" .") for p in SPLIT_SPEAKERS.split(s) if p and p.strip(" .")]
    return [p for p in parts if len(name_tokens(p)) >= 1]


def levenshtein1(a: str, b: str) -> bool:
    """True when a and b differ by one edit (both at least 5 chars)."""
    if a == b:
        return True
    if min(len(a), len(b)) < 5 or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    i = 0
    while i < len(s) and s[i] == l[i]:
        i += 1
    return s[i:] == l[i + 1:]


COMMON_SURNAMES = {"garcia", "fernandez", "gonzalez", "rodriguez", "lopez", "martinez", "sanchez", "perez", "gomez", "martin", "jimenez", "ruiz", "hernandez", "diaz", "moreno", "munoz", "alvarez", "romero", "alonso", "gutierrez", "navarro", "torres", "dominguez", "vazquez", "ramos", "gil", "ramirez", "serrano", "blanco", "molina", "morales", "suarez", "ortega", "delgado", "castro", "ortiz", "rubio", "marin", "sanz", "nunez", "iglesias", "medina", "garrido", "cortes", "castillo", "santos", "lozano", "guerrero", "cano", "prieto", "mendez", "calvo", "cruz", "gallego", "vidal", "leon", "marquez", "herrera", "pena", "flores", "cabrera", "campos", "vega", "fuentes", "carrasco", "diez", "caballero", "reyes", "nieto", "aguilar", "pascual", "herrero", "santana", "lorenzo", "montero", "hidalgo", "gimenez", "ibanez", "ferrer", "duran", "santiago", "benitez", "vargas", "mora", "vicente", "arias", "carmona", "crespo", "roman", "pastor", "soto", "saez", "velasco", "moya", "soler", "parra", "esteban", "bravo", "gallardo", "rojas", "salado"}


def common_short_name(name: str) -> bool:
    """'Antonio García', 'Daniel García': a first name plus one very common
    surname; a subset match on such a name is not evidence by itself."""
    t = person_tokens(name)
    return len(t) == 2 and t[1] in COMMON_SURNAMES


def person_tokens(name: str) -> tuple:
    t = strip_accents(name or "").lower()
    t = t.replace("mª", "maria").replace("m.ª", "maria")
    return name_tokens(t)


def fuzzy_same_person(a: str, b: str) -> bool:
    """same_person() plus one-typo tolerance on tokens of 5+ chars:
    'Olga Albillo' ~ 'Olga Albillos Castillo', 'Guitiérrez' ~ 'Gutiérrez'."""
    ta, tb = person_tokens(a), person_tokens(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    if same_person(" ".join(ta), " ".join(tb)):
        return True
    s, l = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(s) < 2 or s[0] != l[0]:
        return False
    return all(any(levenshtein1(x, y) for y in l) for x in s)


def speaker_score(a: str | None, b: str | None) -> float:
    """1 same person(s), 0.5 partial overlap or unknown, 0 conflicting."""
    pa, pb = split_persons(a), split_persons(b)
    if not pa or not pb:
        return 0.5
    for x in pa:
        for y in pb:
            if fuzzy_same_person(x, y):
                return 1.0
    wa = set(t for p in pa for t in person_tokens(p))
    wb = set(t for p in pb for t in person_tokens(p))
    return 0.5 if wa & wb else 0.0


# ---------------------------------------------------------------------------
# events


def event_richness(e: dict) -> int:
    return len(e.get("description_html") or "") + (500 if is_full_dt(e.get("starts_at")) else 0) + (200 if e.get("speaker") else 0) + (100 if e.get("room") else 0) + (100 if e.get("summary") else 0)


def load_events():
    recs = []
    for fam, e in load_parts("events"):
        e = dict(e)
        e["_family"] = fam
        e["starts_at"] = norm_dt(e.get("starts_at"))
        e["ends_at"] = norm_dt(e.get("ends_at"))
        e["kind"] = e.get("kind") if e.get("kind") in KINDS else "other"
        e["modality"] = e.get("modality") if e.get("modality") in MODALITIES else "in_person"
        e["_tkey"] = title_key(e.get("title") or "")
        recs.append(e)
    return recs


def alt_keys(e: dict) -> list[str]:
    """Title-like keys of a record: its title, its company and its speaker
    ('Charla de Rewoox' ~ company Rewoox; 'Irene M Morgado' ~ speaker)."""
    keys = []
    if e.get("company"):
        keys.append(norm_key(e["company"]))
    for p in split_persons(e.get("speaker")):
        keys.append(name_key(p))
    return [k for k in keys if k]


def record_similarity(a: dict, b: dict) -> float:
    t = title_similarity(a["title"], b["title"])
    if t >= 0.6:
        return t
    ta, tb = title_key(a["title"]), title_key(b["title"])
    for k in alt_keys(b):
        if k == ta or (len(sig_tokens(k)) >= 2 and sig_tokens(k) <= sig_tokens(ta)):
            return max(t, 0.9 if k == ta else 0.8)
    for k in alt_keys(a):
        if k == tb or (len(sig_tokens(k)) >= 2 and sig_tokens(k) <= sig_tokens(tb)):
            return max(t, 0.9 if k == tb else 0.8)
    return t


def pair_score(a: dict, b: dict, unique_titles: dict) -> tuple[float, str] | None:
    """Score of merging a and b (same year, different families) or None."""
    if a.get("company") and b.get("company") and not affiliations_compatible(a["company"], b["company"]):
        return None
    t = record_similarity(a, b)
    sa, sb = a["starts_at"], b["starts_at"]
    reason = ""
    if sa and sb:
        if date_of(sa) != date_of(sb):
            # same title, unique in both families for the year, dates differ:
            # a data-entry error in one source (kept, conflict recorded)
            if a["_tkey"] == b["_tkey"] and unique_titles[(a["_family"], a["edition_year"])].get(a["_tkey"], 0) == 1 and unique_titles[(b["_family"], b["edition_year"])].get(b["_tkey"], 0) == 1:
                dcomp, reason = 0.3, "date-conflict"
            else:
                return None
        elif is_full_dt(sa) and is_full_dt(sb):
            d = abs(minutes_of(sa) - minutes_of(sb))
            dcomp = 1.0 if d == 0 else (0.7 if d <= 90 else 0.4)
        else:
            dcomp = 0.9
    else:
        dcomp = 0.5
    sp = speaker_score(a.get("speaker"), b.get("speaker"))
    if sp == 0.0:
        return None
    ok = False
    if t >= 0.6 and dcomp > 0:
        ok = True
        if not reason:
            reason = "title"
    elif t >= 0.4 and dcomp == 1.0 and is_full_dt(sa):
        ok, reason = True, "title+time"
    elif sp == 1.0 and dcomp >= 0.9:
        ok, reason = True, "speaker+date"
    elif sp == 1.0 and t >= 0.25 and dcomp >= 0.7:
        ok, reason = True, "speaker+title"
    elif sp == 1.0 and (not sa or not sb):
        # same person, one source undated: weak, needs a unique candidate
        # (checked by the caller) and, for a first name plus a common
        # surname, a compatible company
        pa = [p for p in split_persons(a.get("speaker")) if any(fuzzy_same_person(p, q) for q in split_persons(b.get("speaker")))]
        if pa and (not common_short_name(pa[0]) or (a.get("company") and b.get("company"))):
            ok, reason = True, "speaker-only"
    if not ok:
        return None
    return (t * 2 + dcomp + sp, reason)


def cluster_events(recs: list[dict]):
    by_year = defaultdict(list)
    for r in recs:
        by_year[r["edition_year"]].append(r)
    unique_titles = defaultdict(Counter)
    for r in recs:
        unique_titles[(r["_family"], r["edition_year"])][r["_tkey"]] += 1
    clusters = []
    links = []
    for year in sorted(by_year):
        items = sorted(by_year[year], key=lambda r: (-event_richness(r), FAMILY_RANK.get(r["_family"], 99), r["source_url"], r["title"]))
        year_clusters: list[list[dict]] = []
        for r in items:
            cands = []
            for c in year_clusters:
                if any(m["_family"] == r["_family"] for m in c):
                    continue
                total, reasons, blocked = 0.0, [], False
                for m in c:
                    ps = pair_score(r, m, unique_titles)
                    if ps is None:
                        # a hard conflict with any member blocks the cluster
                        if m["starts_at"] and r["starts_at"] and date_of(m["starts_at"]) != date_of(r["starts_at"]):
                            blocked = True
                        if speaker_score(r.get("speaker"), m.get("speaker")) == 0.0:
                            blocked = True
                        continue
                    total += ps[0]
                    reasons.append(ps[1])
                if blocked or not reasons:
                    continue
                cands.append((total, c, "+".join(sorted(set(reasons)))))
            strong = [x for x in cands if x[2] != "speaker-only"]
            if strong:
                cands = strong
            elif len(cands) > 1:
                cands = []  # ambiguous weak match: keep the record apart
            best, best_score, best_reason = None, 0.0, ""
            for total, c, reason in cands:
                if total > best_score:
                    best, best_score, best_reason = c, total, reason
            if best is None:
                year_clusters.append([r])
            else:
                best.append(r)
                links.append((year, r, best[0], best_reason))
        clusters.extend(year_clusters)
    return clusters, links


def kind_hint(title: str) -> str | None:
    k = norm_key(title)
    if re.match(r"^(taller|workshop|seminario)\b", k):
        return "workshop"
    if re.match(r"^(torneo|concurso|competicion|campeonato|final torneo|yincana|gymkhana|gymkana|gincana|escape room|scape room|game jam|esports|ctf|hackathon|hackaton)\b", k):
        return "competition"
    if re.match(r"^(ceremonia|acto de (apertura|clausura|inauguracion|cierre)|inauguracion|clausura)\b", k):
        return "ceremony"
    if re.match(r"^(stand|stands)\b", k):
        return "stand"
    if re.match(r"^mentoria\b", k):
        return "mentoring"
    return None


def choose_title(members: list[dict]) -> str:
    def score(m):
        t = m["title"] or ""
        letters = [c for c in t if c.isalpha()]
        caps = bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.9
        stripped = title_key(t)
        s = min(len(stripped), 120)
        if caps:
            s -= 60
        if TITLE_PREFIX.match(norm_key(t)):
            s -= 5
        # generic 'Charla de <speaker/company>' titles score low
        if m.get("speaker") and stripped == name_key(m["speaker"]):
            s -= 30
        # titles of similar descriptiveness: prefix-less first, then family priority
        return (s // 20, 0 if TITLE_PREFIX.match(norm_key(t)) else 1, -FAMILY_RANK.get(m["_family"], 99))
    return max(members, key=score)["title"]


def fix_title_names(title: str, members: list[dict], speaker: str | None, company: str | None) -> str:
    """Replace, inside the chosen title, a speaker spelling used by another
    source with the canonical one ('Anabel Carmona Guitiérrez' ->
    'Anabel Carmona Gutiérrez'), and a company typo with the merged company."""
    canon = split_persons(speaker)
    variants = set()
    for m in members:
        for v in split_persons(m.get("speaker")):
            variants.add(v)
        if m.get("speaker"):
            variants.add(re.sub(r"^(jurado|ponentes?)\s*:\s*", "", m["speaker"].strip(), flags=re.I))
    for v in sorted(variants, key=len, reverse=True):
        for c in canon:
            if v == c or v not in title or c in title:
                continue
            typo = len(person_tokens(v)) == len(person_tokens(c)) and name_key(v) != name_key(c) and fuzzy_same_person(v, c)
            if typo or name_key(v) in SPEAKER_ALIASES:
                title = title.replace(v, c)
    if company:
        for m in members:
            c = m.get("company")
            if c and c != company and c in title and company not in title and levenshtein1(norm_key(c).replace(" ", ""), norm_key(company).replace(" ", "")):
                title = title.replace(c, company)
    return title


def pick_first(members, field, order=None):
    for m in sorted(members, key=lambda m: rank(m["_family"], order)):
        v = m.get(field)
        if v not in (None, "", []):
            return v
    return None


def merge_event_cluster(members: list[dict], conflicts: list[str]) -> dict:
    year = members[0]["edition_year"]
    time_order = TIME_ORDER_BY_YEAR.get(year)
    families = sorted({m["_family"] for m in members}, key=lambda f: FAMILY_RANK.get(f, 99))
    title = choose_title(members)
    # description: longest wins (text length first, so a photo gallery does
    # not beat a real description; then markup length); source_url of that
    # (richest) source
    richest = max(members, key=lambda m: (len(html_text(m.get("description_html"))), len(m.get("description_html") or ""), -rank(m["_family"])))
    # times: majority of the (start, end) pairs among fully dated sources, then priority
    dated = [m for m in members if is_full_dt(m["starts_at"])]
    if dated:
        votes = Counter((m["starts_at"], m["ends_at"]) for m in dated)
        winner = min(dated, key=lambda m: (-votes[(m["starts_at"], m["ends_at"])], rank(m["_family"], time_order)))
        starts_at, ends_at = winner["starts_at"], winner["ends_at"]
        others = sorted({(m["_family"], m["starts_at"], m["ends_at"]) for m in dated if m["starts_at"] != starts_at or (m["ends_at"] and ends_at and m["ends_at"] != ends_at)})
        if others:
            conflicts.append(f"{year} '{title}': kept {starts_at}..{ends_at or '?'} ({winner['_family']}); other sources said " + "; ".join(f"{f}: {s}..{e or '?'}" for f, s, e in others))
        if ends_at is None:
            ends_at = pick_first(dated, "ends_at", time_order)
    else:
        starts_at = pick_first(members, "starts_at", time_order)
        ends_at = pick_first(members, "ends_at", time_order)
    # kind: majority among specific kinds (the title wording of the merged
    # event votes too: 'Taller ...' -> workshop, 'Torneo ...' -> competition),
    # then priority
    kinds = [m["kind"] for m in members if m["kind"] != "other"]
    hints = Counter(h for h in (kind_hint(m["title"]) for m in members) if h)
    hint = hints.most_common(1)[0][0] if hints else None
    if kinds:
        kc = Counter(kinds)
        if hint:
            kc[hint] += 1
        kind = min(members, key=lambda m: (m["kind"] == "other", -kc.get(m["kind"], 0), rank(m["_family"])))["kind"]
        if len(set(kinds)) > 1:
            conflicts.append(f"{year} '{title}': kind {kind} chosen among " + ", ".join(f"{m['_family']}={m['kind']}" for m in members) + (f" (title suggests {hint})" if hint else ""))
    else:
        kind = hint or "other"
    # speaker: most complete string (most name tokens), then priority
    speakers = [m for m in members if m.get("speaker")]
    speaker = max(speakers, key=lambda m: (len(name_tokens(m["speaker"])), -rank(m["_family"])))["speaker"] if speakers else None
    summaries = [m["summary"] for m in members if m.get("summary")]
    summary = max(summaries, key=len) if summaries else None
    links = [m["link"] for m in sorted(members, key=lambda m: rank(m["_family"])) if m.get("link")]
    links = sorted(links, key=lambda u: ("institucional.us.es" in u, links.index(u)))
    modalities = [m["modality"] for m in members]
    modality = "online" if year == 2020 or Counter(modalities).most_common(1)[0][0] == "online" else "in_person"
    return {
        "edition_year": year,
        "title": title,
        "kind": kind,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "room": pick_first(members, "room", time_order),
        "modality": modality,
        "speaker": speaker,
        "company": pick_first(members, "company"),
        "summary": summary,
        "description_html": richest.get("description_html") or "",
        "poster_url": pick_first(members, "poster_url"),
        "link": links[0] if links else None,
        "lang": Counter([m.get("lang") or "es" for m in members]).most_common(1)[0][0] if len(members) > 1 else (richest.get("lang") or "es"),
        "source_url": richest["source_url"],
        "source_timestamp": richest.get("source_timestamp"),
        "_families": families,
        "_sources": sorted({m["source_url"] for m in members}),
        "_members": members,
    }


# ---------------------------------------------------------------------------
# speakers


def speaker_richness(s: dict) -> int:
    return len(s.get("bio_html") or "") + (300 if s.get("photo_url") else 0) + (100 if s.get("affiliation") else 0) + (100 if s.get("position") else 0) + 20 * len(s.get("links") or [])


def aff_key(a: str | None) -> frozenset:
    return frozenset(t for t in norm_key(a or "").split() if t not in STOPWORDS and len(t) > 1)


def affiliations_compatible(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return True
    ka, kb = aff_key(a), aff_key(b)
    if not ka or not kb:
        return True
    if ka & kb:
        return True
    ja, jb = "".join(sorted(ka)), "".join(sorted(kb))
    return any(x in y or y in x or levenshtein1(x, y) for x in ka for y in kb) or ja in jb or jb in ja


def canonical_speaker_name(name: str) -> str:
    return SPEAKER_ALIASES.get(name_key(name), name).strip()


def load_speakers():
    recs = []
    for fam, s in load_parts("speakers"):
        s = dict(s)
        s["_family"] = fam
        s["name"] = canonical_speaker_name(s.get("name") or "")
        if not s["name"] or name_key(s["name"]) in SPEAKER_DROP:
            s["_dropped"] = True
        recs.append(s)
    return recs


def cluster_speakers(recs: list[dict]):
    items = sorted([r for r in recs if not r.get("_dropped")], key=lambda r: (-speaker_richness(r), rank(r["_family"], SPEAKER_ORDER), r["name"]))
    clusters: list[list[dict]] = []
    for r in items:
        cands = []
        for c in clusters:
            exact = any(name_key(m["name"]) == name_key(r["name"]) for m in c)
            fuzzy = exact or any(fuzzy_same_person(m["name"], r["name"]) for m in c)
            if not fuzzy:
                continue
            if not all(affiliations_compatible(m.get("affiliation"), r.get("affiliation")) for m in c):
                continue
            years = set(y for m in c for y in (m.get("edition_years") or []))
            overlap = len(years & set(r.get("edition_years") or []))
            if not exact and (common_short_name(r["name"]) or any(common_short_name(m["name"]) for m in c)):
                # 'Daniel García' ~ 'Daniel García Moreno' only with a shared
                # edition year or a matching affiliation
                shared_aff = r.get("affiliation") and any(m.get("affiliation") for m in c)
                if not overlap and not shared_aff:
                    continue
            cands.append(((0 if exact else 1, -overlap), c))
        if cands:
            cands.sort(key=lambda x: x[0])
            cands[0][1].append(r)
        else:
            clusters.append([r])
    return clusters


def merge_speaker_cluster(members: list[dict]) -> dict:
    def name_score(m):
        n = m["name"]
        return (len(person_tokens(n)), sum(1 for c in n if ord(c) > 127), -rank(m["_family"], SPEAKER_ORDER))
    name = max(members, key=name_score)["name"]
    # affiliation: group compatible spellings, most sources wins, then the
    # highest-priority family's spelling (people > Eventin > posts > ... > MEC)
    aff_groups: list[list[dict]] = []
    for m in sorted(members, key=lambda m: rank(m["_family"], SPEAKER_ORDER)):
        if not m.get("affiliation"):
            continue
        for g in aff_groups:
            if affiliations_compatible(g[0]["affiliation"], m["affiliation"]):
                g.append(m)
                break
        else:
            aff_groups.append([m])
    aff_groups.sort(key=lambda g: (-len(g), rank(g[0]["_family"], SPEAKER_ORDER)))
    affs = [aff_groups[0][0]["affiliation"]] if aff_groups else []
    positions = [m["position"] for m in members if m.get("position")]
    bios = sorted([m for m in members if m.get("bio_html")], key=lambda m: (-len(m["bio_html"]), rank(m["_family"], SPEAKER_ORDER)))
    links, seen = [], set()
    for m in sorted(members, key=lambda m: rank(m["_family"], SPEAKER_ORDER)):
        for l in m.get("links") or []:
            u = (l.get("url") or "").strip()
            if u and u not in seen:
                seen.add(u)
                links.append({"label": l.get("label") or "", "url": u})
    years = sorted({int(y) for m in members for y in (m.get("edition_years") or [])})
    src = bios[0] if bios else sorted(members, key=lambda m: rank(m["_family"], SPEAKER_ORDER))[0]
    return {
        "name": name,
        "affiliation": max(affs, key=len) if affs else None,
        "position": max(positions, key=len) if positions else None,
        "bio_html": bios[0]["bio_html"] if bios else "",
        "photo_url": pick_first(members, "photo_url", SPEAKER_ORDER),
        "links": links,
        "edition_years": years,
        "source_url": src["source_url"],
        "_names": sorted({m["name"] for m in members}),
        "_families": sorted({m["_family"] for m in members}),
    }


class SpeakerRegistry:
    def __init__(self, speakers: list[dict]):
        self.speakers = speakers
        self.by_key: dict[str, list[dict]] = defaultdict(list)
        for s in speakers:
            for n in s["_names"] + [s["name"]]:
                self.by_key[name_key(n)].append(s)

    def candidates(self, person: str) -> list[dict]:
        person = canonical_speaker_name(person)
        k = name_key(person)
        cands = list({id(s): s for s in self.by_key.get(k, [])}.values())
        if not cands and not common_short_name(person):
            cands = [s for s in self.speakers if fuzzy_same_person(s["name"], person) or any(fuzzy_same_person(n, person) for n in s["_names"])]
        return cands

    def canonical(self, person: str, year: int | None, company: str | None = None) -> str | None:
        cands = self.candidates(person)
        if not cands:
            return None
        if len(cands) > 1 and year:
            yc = [s for s in cands if year in s["edition_years"]]
            if yc:
                cands = yc
        if len(cands) > 1 and company:
            cc = [s for s in cands if s.get("affiliation") and affiliations_compatible(s["affiliation"], company)]
            if cc:
                cands = cc
        if len(cands) > 1:
            return None
        return cands[0]["name"]


def canonicalise_speaker_string(s: str | None, year: int, reg: SpeakerRegistry, company: str | None = None) -> str | None:
    if not s:
        return s
    s = SPEAKER_ALIASES.get(name_key(s), s)
    m = re.match(r"^((?:jurado|ponentes?|moderador[a]?)\s*:\s*)(.*)$", s.strip(), flags=re.I)
    prefix, body = (m.group(1), m.group(2)) if m else ("", s.strip())
    parts = re.split(r"(\s*(?:,|;|/| y | e | and |&)\s*)", body, flags=re.I)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1 or not p.strip():
            out.append(p)
            continue
        core = re.sub(r"\s*\(.*?\)\s*$", "", p).strip()
        c = reg.canonical(core, year, company) if len(name_tokens(core)) >= 2 else None
        if c and c != core:
            out.append(p.replace(core, c, 1))
        else:
            out.append(p)
    return prefix + "".join(out)


# ---------------------------------------------------------------------------
# editions


def merge_editions(parts, events, conflicts):
    by_year = defaultdict(list)
    for fam, e in parts:
        e = dict(e)
        e["_family"] = fam
        by_year[int(e["year"])].append(e)
    years = sorted(set(by_year) | set(range(2018, 2026)))
    out = []
    for year in years:
        members = by_year.get(year, [])
        n = edition_number_for_year(year)
        item = {"year": year, "number": n, "roman": roman(n), "name": f"InnoSoft Days {roman(n)}"}

        def pick(field, order):
            cands = [m for m in members if m.get(field) not in (None, "", [])]
            cands.sort(key=lambda m: (CONFIDENCE_RANK.get(m.get("confidence"), 3), rank(m["_family"], order)))
            return (cands[0][field], cands[0]["_family"]) if cands else (None, None)

        notes = []
        for field, order in (("starts_on", EDITION_ORDER), ("ends_on", EDITION_ORDER), ("venue", EDITION_ORDER), ("summary", EDITION_TEXT_ORDER), ("description_html", EDITION_TEXT_ORDER), ("registration_url", EDITION_ORDER)):
            val, fam = pick(field, order)
            item[field] = val
            if field in ("starts_on", "ends_on") and val:
                others = sorted({(m["_family"], m[field]) for m in members if m.get(field) and m[field] != val})
                if others:
                    msg = f"{year} {field}: kept {val} ({fam}); " + ", ".join(f"{f} said {v}" for f, v in others)
                    notes.append(msg)
                    conflicts.append("edition " + msg)
        # cross-check with the dated events of the main programme (Oct 15 - Nov 30)
        ev_dates = sorted({date_of(e["starts_at"]) for e in events if e["edition_year"] == year and e["starts_at"]})
        core = [d for d in ev_dates if d[5:7] == "11" or (d[5:7] == "10" and int(d[8:10]) >= 15)]
        if item.get("starts_on") and core:
            inside = [d for d in core if item["starts_on"] <= d <= item["ends_on"]]
            outside = [d for d in core if d not in inside]
            if outside:
                notes.append(f"dated activities outside {item['starts_on']}..{item['ends_on']}: {', '.join(outside)} (pre-events, follow-up seminars or online tournaments)")
        elif not item.get("starts_on") and core:
            item["starts_on"], item["ends_on"] = core[0], core[-1]
            notes.append(f"dates taken from the dated events ({core[0]}..{core[-1]})")
        sources = sorted({s for m in members for s in (m.get("sources") or [])})
        item["sources"] = sources
        confs = [m.get("confidence") for m in members if m.get("confidence")]
        item["confidence"] = min(confs, key=lambda c: CONFIDENCE_RANK.get(c, 3)) if confs else "low"
        fam_notes = [f"[{m['_family']}] {m['notes'].strip()}" for m in sorted(members, key=lambda m: rank(m['_family'], EDITION_ORDER)) if m.get("notes")]
        names = sorted({m.get("name") for m in members if m.get("name") and m.get("name") != item["name"]})
        if names:
            fam_notes.append("Also called: " + "; ".join(names))
        item["notes"] = " ".join(notes + fam_notes) or None
        item["_families"] = sorted({m["_family"] for m in members})
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# media


def media_base(url: str) -> str:
    u = norm_media_url(url)
    u = re.sub(r"-\d{2,4}x\d{2,4}(?=\.[a-z0-9]+$)", "", u, flags=re.I)
    u = re.sub(r"-scaled(?=\.[a-z0-9]+$)", "", u, flags=re.I)
    return u.lower()


def merge_media(parts):
    groups: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for fam, m in parts:
        if not m.get("url"):
            continue
        groups[media_base(m["url"])].append((fam, m))
    out = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda fm: rank(fm[0], MEDIA_ORDER))
        fam0, m0 = members[0]
        used = sorted({u for _, m in members for u in (m.get("used_by") or [])})
        caption = m0.get("caption") or next((m.get("caption") for _, m in members if m.get("caption")), None)
        kind = m0.get("kind") if m0.get("kind") in {"poster", "photo", "logo", "other"} else "other"
        year = m0.get("edition_year") or next((m.get("edition_year") for _, m in members if m.get("edition_year")), None)
        out.append({"url": m0["url"], "kind": kind, "edition_year": year, "caption": caption, "used_by": used, "_families": sorted({f for f, _ in members}), "_variants": len(members)})
    return out


# ---------------------------------------------------------------------------
# main


def strip_private(items, keep):
    return [{k: it.get(k) for k in keep} for it in items]


EVENT_FIELDS = ["edition_year", "title", "kind", "starts_at", "ends_at", "room", "modality", "speaker", "company", "summary", "description_html", "poster_url", "link", "lang", "source_url", "source_timestamp"]
EDITION_FIELDS = ["year", "number", "roman", "name", "starts_on", "ends_on", "venue", "summary", "description_html", "registration_url", "sources", "confidence", "notes"]
SPEAKER_FIELDS = ["name", "affiliation", "position", "bio_html", "photo_url", "links", "edition_years", "source_url"]
ORGANISER_FIELDS = ["edition_year", "name", "role", "photo_url", "source_url"]
POST_FIELDS = ["date", "title", "slug", "excerpt", "content_html", "featured_image_url", "lang", "edition_year", "categories", "source_url", "source_timestamp"]
PAGE_FIELDS = ["edition_year", "title", "url", "content_html", "kind"]
MEDIA_FIELDS = ["url", "kind", "edition_year", "caption", "used_by"]


def main() -> int:
    conflicts: list[str] = []
    report: dict = {}

    # ---- events
    recs = load_events()
    dropped_events = []
    kept = []
    for r in recs:
        t = (r.get("title") or "").strip()
        if not t or norm_key(t) in ("leer mas", "read more") or UMBRELLA_TITLE.match(norm_key(t)):
            dropped_events.append(r)
        else:
            kept.append(r)
    clusters, links = cluster_events(kept)
    events = [merge_event_cluster(c, conflicts) for c in clusters]

    # ---- speakers
    srecs = load_speakers()
    sclusters = cluster_speakers(srecs)
    speakers = [merge_speaker_cluster(c) for c in sclusters]
    speakers.sort(key=lambda s: (name_key(s["name"]), s["name"]))
    reg = SpeakerRegistry(speakers)
    canon_changes = []
    title_fixes = []
    for e in events:
        new = canonicalise_speaker_string(e.get("speaker"), e["edition_year"], reg, e.get("company"))
        if new != e.get("speaker"):
            canon_changes.append((e["edition_year"], e["speaker"], new))
            e["speaker"] = new
        # company: a typo of the merged speaker's affiliation ('CoverMananger')
        persons = split_persons(e.get("speaker"))
        if e.get("company") and len(persons) == 1:
            sp = reg.candidates(persons[0])
            if len(sp) == 1 and sp[0].get("affiliation"):
                a, c = sp[0]["affiliation"], e["company"]
                if a != c and levenshtein1(norm_key(c).replace(" ", ""), norm_key(a).replace(" ", "")):
                    e["company"] = a
        old_title = e["title"]
        e["title"] = fix_title_names(e["title"], e["_members"], e.get("speaker"), e.get("company"))
        if e["title"] != old_title:
            title_fixes.append((e["edition_year"], old_title, e["title"]))
    events.sort(key=lambda e: (e["edition_year"], e["starts_at"] or "9999", title_key(e["title"]), e["title"]))

    # event speakers without a speaker record
    ev_persons = set()
    for e in events:
        for p in split_persons(e.get("speaker")):
            if len(name_tokens(p)) >= 2:
                ev_persons.add((e["edition_year"], p))
    missing_speakers = sorted({(y, p) for y, p in ev_persons if not reg.candidates(p)})

    # ---- editions
    editions = merge_editions(load_parts("editions"), events, conflicts)

    # ---- organisers
    org_groups: dict[tuple, list] = defaultdict(list)
    for fam, o in load_parts("organisers"):
        if not (o.get("name") or "").strip():
            continue
        org_groups[(int(o["edition_year"]), name_key(o["name"]))].append((fam, o))
    organisers = []
    for key in sorted(org_groups):
        members = org_groups[key]
        roles = []
        for _, o in members:
            for r in re.split(r"\s*/\s*", o.get("role") or ""):
                if r and r not in roles:
                    roles.append(r)
        organisers.append({
            "edition_year": key[0],
            "name": max((o["name"] for _, o in members), key=len),
            "role": " / ".join(roles) or None,
            "photo_url": next((o["photo_url"] for _, o in members if o.get("photo_url")), None),
            "source_url": members[0][1]["source_url"],
        })
    organisers.sort(key=lambda o: (o["edition_year"], name_key(o["name"])))

    # ---- posts
    post_groups: dict[str, list] = defaultdict(list)
    for fam, p in load_parts("posts"):
        if not p.get("slug"):
            continue
        post_groups[p["slug"]].append((fam, p))
    posts = []
    dup_posts = []
    for slug in sorted(post_groups):
        members = sorted(post_groups[slug], key=lambda fp: (-len(fp[1].get("content_html") or ""), fp[1].get("source_timestamp") or ""))
        if len(members) > 1:
            dup_posts.append((slug, [f for f, _ in members]))
        p = dict(members[0][1])
        cats = []
        for _, m in members:
            for c in m.get("categories") or []:
                if c not in cats:
                    cats.append(c)
        p["categories"] = cats
        posts.append(p)
    posts.sort(key=lambda p: (p.get("date") or "", p["slug"]))

    # ---- pages
    # pages: one per url and edition year (the same page captured in two
    # years, e.g. /como-llegar/ 2023 and 2024, describes two editions)
    page_groups: dict[tuple, list] = defaultdict(list)
    for fam, pg in load_parts("pages"):
        page_groups[(pg["url"], pg.get("edition_year") or 0)].append((fam, pg))
    pages = []
    for key in sorted(page_groups):
        members = sorted(page_groups[key], key=lambda fp: (-len(fp[1].get("content_html") or ""), fp[1].get("source_timestamp") or ""))
        pages.append(members[0][1])
    pages.sort(key=lambda p: (p.get("edition_year") or 0, p["url"]))

    # ---- media
    media = merge_media(load_parts("media"))
    media.sort(key=lambda m: (m["edition_year"] or 0, m["url"]))

    # ---- write
    def dump_final(name, items, fields):
        p = EXTRACTED / name
        p.write_text(json.dumps(strip_private(items, fields), ensure_ascii=False, indent=1), encoding="utf-8")
        return p

    outputs = {
        "editions.json": (editions, EDITION_FIELDS),
        "events.json": (events, EVENT_FIELDS),
        "speakers.json": (speakers, SPEAKER_FIELDS),
        "organisers.json": (organisers, ORGANISER_FIELDS),
        "posts.json": (posts, POST_FIELDS),
        "pages.json": (pages, PAGE_FIELDS),
        "media.json": (media, MEDIA_FIELDS),
    }
    for name, (items, fields) in outputs.items():
        dump_final(name, items, fields)

    # ---- report
    write_report(editions, events, speakers, organisers, posts, pages, media, recs, dropped_events, links, srecs, canon_changes, title_fixes, missing_speakers, dup_posts, conflicts)
    print(json.dumps({k: len(v[0]) for k, v in outputs.items()}, indent=1))
    print("conflicts:", len(conflicts))
    return 0


def write_report(editions, events, speakers, organisers, posts, pages, media, event_recs, dropped_events, links, speaker_recs, canon_changes, title_fixes, missing_speakers, dup_posts, conflicts):
    L = []
    L.append("# Synthesis report (data/extracted/*.json)")
    L.append("")
    L.append("Produced by `parse/synthesize.py` from `data/extracted/parts/*.json` (all families, both runs). Deterministic; rerun after fixing a part.")
    L.append("")
    fams = sorted({f for f, _ in load_parts("events")} | {f for f, _ in load_parts("posts")} | {f for f, _ in load_parts("media")} | {f for f, _ in load_parts("speakers")} | {f for f, _ in load_parts("editions")} | {f for f, _ in load_parts("pages")} | {f for f, _ in load_parts("organisers")})
    L.append(f"Families merged: {', '.join(fams)}.")
    L.append("")
    # coverage table
    L.append("## Coverage per year")
    L.append("")
    L.append("| year | edition | events (merged / raw) | speakers | organisers | posts | pages | media |")
    L.append("|---|---|---|---|---|---|---|---|")
    years = sorted({e["year"] for e in editions})
    raw_by_year = Counter(r["edition_year"] for r in event_recs)
    for y in years:
        ed = next(e for e in editions if e["year"] == y)
        n_ev = sum(1 for e in events if e["edition_year"] == y)
        n_sp = sum(1 for s in speakers if y in s["edition_years"])
        n_org = sum(1 for o in organisers if o["edition_year"] == y)
        n_po = sum(1 for p in posts if p.get("edition_year") == y)
        n_pg = sum(1 for p in pages if p.get("edition_year") == y)
        n_me = sum(1 for m in media if m.get("edition_year") == y)
        edd = f"{ed['roman']} {ed['starts_on'] or '?'}..{ed['ends_on'] or '?'} ({ed['confidence']})"
        L.append(f"| {y} | {edd} | {n_ev} / {raw_by_year.get(y, 0)} | {n_sp} | {n_org} | {n_po} | {n_pg} | {n_me} |")
    L.append(f"| total | {len(editions)} | {len(events)} / {len(event_recs)} | {len(speakers)} (records: {len(speaker_recs)}) | {len(organisers)} | {len(posts)} | {len(pages)} | {len(media)} |")
    L.append("")
    # families per year of events
    L.append("Event sources per year (family: raw records):")
    L.append("")
    fy = defaultdict(Counter)
    for r in event_recs:
        fy[r["edition_year"]][r["_family"]] += 1
    for y in sorted(fy):
        L.append(f"- {y}: " + ", ".join(f"{f} {n}" for f, n in sorted(fy[y].items())))
    L.append("")
    # editions
    L.append("## Editions")
    L.append("")
    L.append("One entry per year 2017 to 2025 (2017 = V is documented by the MEC event pages and /v-edicion/). Name is always `InnoSoft Days <roman>` with number = year - 2012. Dates and venue come from the highest-confidence source (edition/timetable pages, then the institucional site, then event pages, then posts); summary and description from the same order with posts before event pages. The importer only fills empty fields, so the seeded XIII (2025) edition keeps its own copy.")
    L.append("")
    L.append("| year | name | dates | venue | families | confidence |")
    L.append("|---|---|---|---|---|---|")
    for e in editions:
        L.append(f"| {e['year']} | {e['name']} | {e['starts_on']}..{e['ends_on']} | {(e['venue'] or '')[:70]} | {', '.join(e['_families'])} | {e['confidence']} |")
    L.append("")
    # events merge
    L.append("## Events")
    L.append("")
    L.append(f"{len(event_recs)} raw records from {len(fy)} years became {len(events)} events; {len(dropped_events)} container/boilerplate records dropped, {len(links)} records merged into another record.")
    L.append("")
    L.append("Clustering (per year, greedy, richest record first, a family never merges with itself): two records merge when the normalised titles match (generic prefixes such as `Conferencia –`, `Taller`, `Charla de la Sra.` removed; exact key, token subset or Jaccard >= 0.6) and the dates are compatible (same day, or one source has no date), or when the speaker is the same person on the same day (multi-speaker strings are split; a conflicting speaker blocks the merge). Same-title records with different dates only merge when the title is unique in both families for that year (a data-entry error in one source, recorded below).")
    L.append("")
    L.append("Field rules: longest `description_html` wins and gives `source_url`; `starts_at`/`ends_at` by majority of the fully dated sources then family priority (Eventin/TEC 2024 > MEC > institucional > people > pages > posts; for 2021 the institucional calendar captured on 2021-11-14 beats the MEC copy); `kind` by majority of the specific kinds; `speaker` is the most complete name string, then canonicalised to the merged speaker name; `title` prefers a descriptive, non-ALL-CAPS, prefix-less title; `link` prefers live-site URLs over the dead institucional.us.es ones; `modality` online for 2020.")
    L.append("")
    L.append("### Dropped records")
    L.append("")
    for r in dropped_events:
        L.append(f"- {r['edition_year']} [{r['_family']}] '{r['title']}' ({r['starts_at']}) {r['source_url']}: container entry of the calendar, not an activity")
    L.append("")
    L.append("### Merges (record -> cluster seed, reason)")
    L.append("")
    for year, r, seed, reason in sorted(links, key=lambda x: (x[0], x[2]["title"], x[1]["_family"])):
        L.append(f"- {year} [{r['_family']}] '{r['title']}' ({r['starts_at'] or 'no date'}; {r.get('speaker') or '-'}) -> [{seed['_family']}] '{seed['title']}' ({seed['starts_at'] or 'no date'}; {seed.get('speaker') or '-'}) [{reason}]")
    L.append("")
    multi = [e for e in events if len(e["_families"]) > 1]
    L.append(f"{len(multi)} events combine 2+ families; {len(events) - len(multi)} come from a single family.")
    L.append("")
    L.append("### Speaker strings canonicalised on events")
    L.append("")
    for y, old, new in sorted(canon_changes, key=lambda x: (x[0], x[1] or "")):
        L.append(f"- {y}: '{old}' -> '{new}'")
    L.append("")
    L.append("### Titles corrected with the canonical speaker/company spelling")
    L.append("")
    for y, old, new in sorted(title_fixes):
        L.append(f"- {y}: '{old}' -> '{new}'")
    L.append("")
    # speakers
    L.append("## Speakers")
    L.append("")
    L.append(f"{len(speaker_recs)} records -> {len(speakers)} speakers. Names are matched accent/case-insensitively with subset matching (`Clara Grima` = `Clara Isabel Grima Ruiz`) and one-typo tolerance on 5+ letter tokens; the merge is blocked when the affiliations are incompatible. Aliases applied: " + "; ".join(f"`{k}` -> `{v}`" for k, v in sorted(SPEAKER_ALIASES.items())) + f". Dropped records (not a person): {', '.join(sorted(SPEAKER_DROP))}. Merged name = the most complete spelling; affiliation/position = the longest; bio = the longest; photo by family priority (people, Eventin, posts...); links unioned; edition_years unioned.")
    L.append("")
    L.append("### Merged speakers (2+ spellings or families)")
    L.append("")
    for s in speakers:
        if len(s["_names"]) > 1 or len(s["_families"]) > 1:
            L.append(f"- {s['name']} ({', '.join(str(y) for y in s['edition_years'])}): {', '.join(s['_names'])} [{', '.join(s['_families'])}]" + (f" | {s['affiliation']}" if s.get("affiliation") else ""))
    L.append("")
    same_key = defaultdict(list)
    for s in speakers:
        same_key[person_tokens(s["name"])[0] if person_tokens(s["name"]) else ""].append(s)
    L.append("### Speakers kept apart although the names overlap")
    L.append("")
    for s in speakers:
        for t in speakers:
            if s is t or s["name"] >= t["name"]:
                continue
            if fuzzy_same_person(s["name"], t["name"]):
                L.append(f"- '{s['name']}' ({s.get('affiliation') or '-'}; {s['edition_years']}) vs '{t['name']}' ({t.get('affiliation') or '-'}; {t['edition_years']}): affiliations incompatible")
    L.append("")
    L.append(f"### Event speakers without a speaker record ({len(missing_speakers)})")
    L.append("")
    L.append("Names that only appear in an event's `speaker` field with no speaker record under that exact name (for a first name plus a very common surname a longer-name record is not assumed to be the same person: 'Antonio García' of the 2020 trading talk is not 'Antonio Jesús García Nieto'); the importer keeps them as free text on the event.")
    L.append("")
    for y, p in missing_speakers:
        L.append(f"- {y}: {p}")
    L.append("")
    # organisers, posts, pages, media
    L.append("## Organisers, posts, pages, media")
    L.append("")
    oy = Counter(o["edition_year"] for o in organisers)
    L.append(f"- organisers: {len(organisers)} people ({', '.join(f'{y}: {n}' for y, n in sorted(oy.items()))}), from the people family only (XI and XII organisation pages); deduped per (year, name), roles joined with ' / '.")
    L.append(f"- posts: {len(posts)} ({', '.join(f'{y}: {n}' for y, n in sorted(Counter(p.get('edition_year') for p in posts).items()))}); deduped by slug" + (f", duplicates merged: {dup_posts}" if dup_posts else ", no slug appeared twice") + ". posts_2025 contributed nothing (151 spam captures and the default 'Hola, mundo' post of the rebuilt 2025 site).")
    L.append(f"- pages: {len(pages)}, all from pages_editions, deduped by (url, edition_year) so a page captured in two years (/como-llegar/ 2023 and 2024) keeps both versions; README fields only (source timestamps stay in the part).")
    fams_media = Counter()
    for m in media:
        for f in m["_families"]:
            fams_media[f] += 1
    variants = sum(1 for m in media if m["_variants"] > 1)
    L.append(f"- media: {len(media)} images from {sum(1 for _ in load_parts('media'))} part records; grouped by image (size variants `-WxH`, `-scaled` and the institucional.us.es/innosoft host collapse into one entry whose url is the media family's canonical one: fetched original > largest fetched variant > largest referenced); {variants} entries had 2+ records; kinds: {dict(Counter(m['kind'] for m in media))}. External images (imgur, bitnami.com, ...) from the institucional family are kept as their own entries.")
    L.append("")
    # conflicts
    L.append(f"## Conflicts resolved ({len(conflicts)})")
    L.append("")
    for c in conflicts:
        L.append(f"- {c}")
    L.append("")
    # gaps
    L.append("## Gaps and open questions")
    L.append("")
    gaps = [
        "2013-2016 (editions I to IV) have no capture at all: the archive holds nothing before the 2017 MEC event pages; only the editions 2017-2025 are produced.",
        "2017 (V): only calendar slots (title, time, room, some speakers) from the MEC pages and /v-edicion/; no descriptions, posters or posts.",
        "2019 (VII): programme from the MEC pages (ALL CAPS titles kept verbatim) and five blog articles; no speaker bios or posters (2019 poster is an imgur URL).",
        "2021 (IX): institucional links point at the dead institucional.us.es site; the MEC copy on innosoftdays.com is preferred where both exist. The /ponentes-ix-edicion/ page and the 2021 organisation were never captured.",
        "2022 (X): speaker pages hold only infographic card images (positions/bios missing for 15 speakers); the poster text of Sancho Lerena is hand-transcribed in the parser.",
        "2023 (XI): the XI table gives times and rooms; several speakers only have the talk poster as bio.",
        "2024 (XII): three plugins published the same programme; TEC/ETN times were preferred over the stale MEC copies (Ignasi Labastida 11:00 vs 16:00, VOLUM 09:30 vs 11:00). Four listing stubs (4i.ai, Irene M Morgado, Mentoría Turno Mañana, Torneo CS2 Final) keep a source_url that was never captured. Umbrella stands/mentoring blocks coexist with per-day slots by design.",
        "2025 (XIII): only the Elementor site (schedule, speakers, photo galleries); the product already seeds this edition, the importer only fills empty fields. 508 of the 2025 media URLs (metaslider crops) are not in the raw uploads.",
        "posts: 2025 has no genuine post; /category/noticias/ (institucional, 2021) was never fetched.",
        "media: 986 of the 1039 images have no captured variant in the CDX index (see parts/media.notes.md appendix for a second fetch pass); the importer drops images it cannot resolve.",
        "speakers: names only present on events (list above) have no bio/affiliation; the 'Daniel García' of 2021/2022 (PRiSE) and 'Daniel García Moreno' (SUSE/openSUSE) are kept as two people; 'Carlos Pérez' (CoverManager 2022 and entrepreneur 2023) is one person as the people family decided.",
        "date-only `starts_at` values (posts that give the day but not the hour) are kept as `YYYY-MM-DD`; the importer parses them as midnight.",
        "kind `other` covers web games (crosswords, wordle, hangman), screenings and receptions; the importer maps it to talk.",
        "registration_url values are historical and dead (institucional.us.es/innosoft/inscripciones/ for 2020, /en/tickets-store/ for 2024); kept as extracted, the importer may prefer to skip them.",
        "speaker 'Mª Carmen Romero' (2017 talk on the security policy of the Universidad de Sevilla) was merged into 'María del Carmen Romero Ternero' (ETSII director, 2022) through the Mª = María normalisation: plausible (same ETSII professor) but not confirmed by any capture.",
        "'Yoana Dimitrova' (Presidenta InnoSoft 2020) is the MEC organiser of the 2020 opening/closing ceremonies and comes through as a speaker record; the product may want her under organisation instead.",
        "2022: the posts say the gymkhana ran on 10 Nov 15:30 while the MEC calendar has 'Gymkhana 1' (8 Nov) and 'Gymkhana 2' (9 Nov); the three records are kept apart. 2020: 'Presentación del día' of 27 Nov is date-only (posts) while the 26 Nov one has MEC times.",
        "2018: end times of the institucional timetable are geometric (row spans) and differ from the MEC per-event times for Blockchain, Sngular/Sass, YOLO and the Bitnami competition; MEC won on priority except where a third source agreed with institucional (Bitnami 19:30).",
        "Duplicated activities by design (different granularity, all kept): 2024 TEC umbrellas 'Stand Sostenibilidad' / 'Stand Igualdad' / 'Photocall' vs the per-day ETN stands, TEC 'Mentoría' vs the per-turn slots, morning/afternoon 'Yincana Inauguración' turns; 2023 two 'CTF prueba presencial' sessions; 2025 two Escape Room / Game Jam / RogueLikes slots.",
    ]
    for g in gaps:
        L.append(f"- {g}")
    L.append("")
    (EXTRACTED / "REPORT.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
