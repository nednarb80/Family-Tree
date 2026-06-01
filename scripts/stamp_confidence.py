#!/usr/bin/env python3
"""Stamp a confidence rank onto every person's frontmatter.

Confidence ladder (4 -> 1):
  4 Confirmed   — backed by real records (census, certificate, draft, naturalization,
                  passenger, marriage record, military), image or official index.
  3 Probable    — some evidence but thin: derivative-only (SSDI, public-records index,
                  Find A Grave text) or a single source.
  2 Possible    — in the tree but essentially unsourced; plausible by name/place/date.
  1 Speculative — unverified, likely copied from other trees (here: unsourced AND born
                  before 1750, the deep Burrage/Burgh line).

Reads the GED to score by xref, maps xref->slug via the importer's own logic so the
ranks line up with the files on disk, then injects `confidence:` and
`confidence_label:` into each people/<slug>/<slug>.md frontmatter.

Run AFTER import_run.py, BEFORE regenerate.py:
    python scripts/stamp_confidence.py "Collins Family Tree.ged"
"""
from __future__ import annotations
import re, sys, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GED = sys.argv[1] if len(sys.argv) > 1 else "Collins Family Tree.ged"

# reuse the importer's parser + slug logic so slugs match exactly
spec = importlib.util.spec_from_file_location("imp", ROOT / "scripts" / "import_run.py")
imp = importlib.util.module_from_spec(spec); spec.loader.exec_module(imp)

LABELS = {4: "Confirmed", 3: "Probable", 2: "Possible", 1: "Speculative"}

REAL = ("census", "certificate", "draft", "naturaliz", "passenger",
        "marriage record", "military")
OFFICIAL = ("census", "cert", "draft", "naturaliz", "passenger", "marriage",
            "death", "birth", "military", "index")


def main():
    text = Path(ROOT / GED).read_bytes().decode("utf-8-sig")
    roots = imp.parse_gedcom(text)
    indis = {r.xref: r for r in roots if r.tag == "INDI"}
    sours = {r.xref: r for r in roots if r.tag == "SOUR"}

    def stitle(sx):
        if sx not in sours:
            return ""
        return (sours[sx].first("TITL").full_value() if sours[sx].first("TITL") else "").lower()

    def birthyear(rec):
        b = rec.first("BIRT")
        if not b:
            return None
        nd = imp.norm_date(b.val("DATE"))
        return nd["year"] if nd else None

    def score(rec):
        titles = []
        for c in rec.children:
            for sc in [c] + c.children:
                if sc.tag == "SOUR" and sc.value and sc.value.startswith("@"):
                    titles.append(stitle(sc.value))
        titles = [t for t in titles if t]
        n = len(titles)
        only_tree = n > 0 and all(("tree" in t or "family data" in t) for t in titles)
        has_real = any(any(k in t for k in REAL) for t in titles)
        has_official = any(any(k in t for k in OFFICIAL) for t in titles)
        y = birthyear(rec)
        if n == 0 or only_tree:
            return 1 if (y and y < 1750) else 2
        if has_real or (has_official and n >= 2):
            return 4
        return 3

    # rebuild xref -> slug exactly as the importer does
    used = {}
    def claim(base):
        base = base or "unknown"
        if base not in used:
            used[base] = 1; return base
        used[base] += 1; return f"{base}-{used[base]}"

    xref_conf = {}
    for xref, rec in indis.items():
        full, given, surname, alts = imp.parse_name(rec)
        bd = imp.norm_date(rec.first("BIRT").val("DATE")) if rec.first("BIRT") else None
        if bd and bd["year"]:
            yr = ("c" + str(bd["year"])) if bd["approx"] else str(bd["year"])
        else:
            yr = "unknown"
        sg = imp.slugify(surname) or "unknown"
        gg = imp.slugify(given.split()[0]) if given.strip() else "unknown"
        slug = claim(f"{sg}-{gg}-{yr}")
        xref_conf[slug] = score(rec)

    stamped = 0
    dist = {1: 0, 2: 0, 3: 0, 4: 0}
    for slug, c in xref_conf.items():
        f = ROOT / "people" / slug / f"{slug}.md"
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8")
        # insert/replace confidence lines just after the `type: person` line
        txt = re.sub(r"\n confidence:.*", "", txt)  # noop safety
        lines = txt.split("\n")
        out = []
        inserted = False
        for ln in lines:
            if ln.startswith("confidence:") or ln.startswith("confidence_label:"):
                continue  # drop old, we re-add
            out.append(ln)
            if ln.strip() == "type: person" and not inserted:
                out.append(f"confidence: {c}")
                out.append(f"confidence_label: {LABELS[c]}")
                inserted = True
        f.write_text("\n".join(out), encoding="utf-8")
        stamped += 1
        dist[c] += 1

    print(f"stamped confidence on {stamped} people")
    print(f"  4 Confirmed={dist[4]}  3 Probable={dist[3]}  2 Possible={dist[2]}  1 Speculative={dist[1]}")


if __name__ == "__main__":
    main()
