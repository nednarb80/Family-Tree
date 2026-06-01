#!/usr/bin/env python3
"""Integrity check for the Family Tree Archive.

Verifies every link resolves, no one is their own ancestor, partners are
symmetric, and dates are sane. Exits non-zero if any ERROR is found
(warnings don't fail the run). Run:

    python scripts/validate.py
"""
from __future__ import annotations
import re
import sys
from common import ROOT, load_people, partner_slugs, split_frontmatter

errors, warnings = [], []


def err(m): errors.append(m)
def warn(m): warnings.append(m)


def year(v):
    if v is None:
        return None
    m = re.match(r"(\d{4})", str(v))
    return int(m.group(1)) if m else None


def existing(kind):
    d = ROOT / kind
    if not d.exists():
        return set()
    out = set()
    for f in d.iterdir():
        if f.is_dir() and (f / f"{f.name}.md").exists():
            out.add(f.name)
        elif f.suffix == ".md":
            out.add(f.stem)
    return out


def is_ancestor(person, target, people, seen=None):
    """True if `target` appears in `person`'s ancestry."""
    seen = seen or set()
    for p in people.get(person, {}).get("fm", {}).get("parents") or []:
        if p == target or (p not in seen and is_ancestor(p, target, people, seen | {p})):
            return True
    return False


def main():
    people = load_people()
    place_ids = existing("places")
    source_ids = existing("sources")

    for slug, rec in people.items():
        fm = rec["fm"]
        if fm.get("id") != slug:
            err(f"{slug}: frontmatter id '{fm.get('id')}' != folder/file slug")

        # referential integrity
        for p in fm.get("parents") or []:
            if p not in people:
                err(f"{slug}: parent '{p}' is not a person node")
        for sp in partner_slugs(fm):
            if sp not in people:
                err(f"{slug}: partner '{sp}' is not a person node")
            elif slug not in partner_slugs(people[sp]["fm"]):
                warn(f"{slug}: partner '{sp}' does not list {slug} back (partners should be symmetric)")
        for src in fm.get("sources") or []:
            if src not in source_ids:
                err(f"{slug}: source '{src}' not found in sources/")
        for pl in (fm.get("birth_place"), fm.get("death_place")):
            if pl and pl not in place_ids:
                warn(f"{slug}: place '{pl}' not found in places/")

        # self / cycle
        if slug in (fm.get("parents") or []):
            err(f"{slug}: lists itself as a parent")
        elif is_ancestor(slug, slug, people):
            err(f"{slug}: is its own ancestor (parentage cycle)")

        # date sanity
        b, d = year(fm.get("birth_date")), year(fm.get("death_date"))
        if b and d and b > d:
            err(f"{slug}: birth {b} after death {d}")
        for p in fm.get("partners") or []:
            if isinstance(p, dict):
                m = year(p.get("married"))
                if b and m and m < b:
                    err(f"{slug}: married {m} before born {b}")
                if d and m and m > d:
                    warn(f"{slug}: married {m} after death {d}")

    # sources point back at real people
    sdir = ROOT / "sources"
    if sdir.exists():
        for f in sdir.glob("*.md"):
            fm, _ = split_frontmatter(f.read_text(encoding="utf-8"))
            for pid in fm.get("people") or []:
                if pid not in people:
                    err(f"source {f.stem}: references unknown person '{pid}'")

    print(f"validate: {len(people)} people checked.")
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    if errors:
        print(f"\nFAILED with {len(errors)} error(s), {len(warnings)} warning(s).")
        sys.exit(1)
    print(f"\nOK — 0 errors, {len(warnings)} warning(s).")


if __name__ == "__main__":
    main()
