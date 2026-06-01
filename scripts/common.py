"""Shared helpers for the Family Tree Archive scripts.

Plain-text in, plain-text out. Only dependency is PyYAML (see requirements.txt).
The whole archive remains readable with zero tooling — these scripts only
compute the convenience blocks and check integrity.
"""
from __future__ import annotations
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required. Install it with:\n"
        "    pip install pyyaml   (or: pip install -r scripts/requirements.txt)"
    )

ROOT = Path(__file__).resolve().parent.parent
FM_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def split_frontmatter(text: str):
    """Return (frontmatter_dict, body_str). Empty dict if no frontmatter."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    data = yaml.safe_load(m.group(1)) or {}
    return data, m.group(2)


def person_files():
    """Yield (slug, Path) for every people/<slug>/<slug>.md note."""
    pdir = ROOT / "people"
    if not pdir.exists():
        return
    for folder in sorted(pdir.iterdir()):
        if not folder.is_dir():
            continue
        note = folder / f"{folder.name}.md"
        if note.exists():
            yield folder.name, note


def family_files():
    fdir = ROOT / "families"
    if not fdir.exists():
        return
    for folder in sorted(fdir.iterdir()):
        if not folder.is_dir():
            continue
        note = folder / f"{folder.name}.md"
        if note.exists():
            yield folder.name, note


def load_people():
    """slug -> {'fm': dict, 'body': str, 'path': Path}"""
    out = {}
    for slug, path in person_files():
        fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
        out[slug] = {"fm": fm, "body": body, "path": path}
    return out


def partner_slugs(fm: dict):
    """Normalise the partners field to a list of slugs."""
    slugs = []
    for p in fm.get("partners") or []:
        if isinstance(p, dict):
            if p.get("person"):
                slugs.append(p["person"])
        elif isinstance(p, str):
            slugs.append(p)
    return slugs


def link(slug: str, people: dict) -> str:
    """An Obsidian wikilink, with display name when we know it."""
    name = people.get(slug, {}).get("fm", {}).get("full_name")
    return f"[[{slug}|{name}]]" if name else f"[[{slug}]]"
