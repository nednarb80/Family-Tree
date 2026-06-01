#!/usr/bin/env python3
"""GEDCOM -> Family Tree Archive importer (fresh-path copy to dodge mount cache).

Reads an Ancestry.com GEDCOM 5.5.1 export and stamps out the vault:
  people/<slug>/<slug>.md   (+ photos/ documents/ notes/ subfolders)
  families/<slug>/<slug>.md
  sources/<slug>.md
  places/<slug>.md
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"])}
MONTH_NAME = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DROP_PLACE_TOKENS = {
    "usa", "u.s.a.", "us", "united states", "united states of america",
}


class Node:
    __slots__ = ("level", "tag", "xref", "value", "children")

    def __init__(self, level, tag, xref, value):
        self.level = level
        self.tag = tag
        self.xref = xref
        self.value = value
        self.children = []

    def kids(self, tag):
        return [c for c in self.children if c.tag == tag]

    def first(self, tag):
        for c in self.children:
            if c.tag == tag:
                return c
        return None

    def val(self, tag, default=None):
        c = self.first(tag)
        return c.value if c else default

    def full_value(self):
        out = self.value or ""
        for c in self.children:
            if c.tag == "CONC":
                out += c.value or ""
            elif c.tag == "CONT":
                out += "\n" + (c.value or "")
        return out


def parse_gedcom(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    roots = []
    stack = []
    for raw in text.split("\n"):
        if not raw.strip():
            continue
        m = re.match(r"^(\d+)\s+(@[^@]+@)?\s*(\S+)?\s?(.*)$", raw)
        if not m:
            continue
        level = int(m.group(1))
        xref = m.group(2)
        tag = m.group(3)
        value = m.group(4)
        node = Node(level, tag, xref, value)
        if level == 0:
            roots.append(node)
            stack = [(0, node)]
        else:
            while stack and stack[-1][0] >= level:
                stack.pop()
            if stack:
                stack[-1][1].children.append(node)
            stack.append((level, node))
    return roots


def slugify(s):
    s = (s or "").lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def norm_date(raw):
    if not raw:
        return None
    s = raw.strip()
    approx = False
    mm = re.match(r"^(ABT|EST|CAL|BEF|AFT|ABOUT|CIRCA|C)\b\.?\s*(.*)$", s, re.I)
    if mm:
        approx = True
        s = mm.group(2).strip()
    bm = re.match(r"^BET\b\.?\s+(.*?)\s+AND\s+(.*)$", s, re.I)
    if bm:
        s = bm.group(1).strip()
        approx = True
    fm = re.match(r"^(FROM|TO)\b\.?\s+(.*)$", s, re.I)
    if fm:
        s = fm.group(2).strip()
    parts = s.split()
    iso = year = None
    try:
        if len(parts) == 3:
            d = int(parts[0]); mon = MONTHS[parts[1].lower()[:3]]; y = int(parts[2])
            iso = f"{y:04d}-{mon:02d}-{d:02d}"; year = y
        elif len(parts) == 2:
            mon = MONTHS[parts[0].lower()[:3]]; y = int(parts[1])
            iso = f"{y:04d}-{mon:02d}"; year = y
        elif len(parts) == 1 and re.match(r"^\d{3,4}$", parts[0]):
            y = int(parts[0]); iso = f"{y:04d}"; year = y
    except (KeyError, ValueError):
        pass
    return {"iso": iso, "year": year, "approx": approx, "raw": raw.strip()}


def pretty_date(nd):
    if not nd:
        return ""
    if nd["iso"] and len(nd["iso"]) == 10:
        y, m, d = nd["iso"].split("-")
        disp = f"{int(d)} {MONTH_NAME[int(m)]} {y}"
    elif nd["iso"] and len(nd["iso"]) == 7:
        y, m = nd["iso"].split("-")
        disp = f"{MONTH_NAME[int(m)]} {y}"
    elif nd["iso"]:
        disp = nd["iso"]
    else:
        disp = nd["raw"]
    return ("abt " + disp) if nd["approx"] else disp


def parse_name(node):
    """Pick the most canonical NAME as primary; score slash-surnames highest."""
    names = node.kids("NAME")

    def parse_one(n):
        v = n.value or ""
        sm = re.search(r"/([^/]*)/", v)
        slash_sn = sm.group(1).strip() if sm else ""
        gv = re.sub(r"/[^/]*/", "", v).strip()
        gv = (n.val("GIVN") or gv or "").strip()
        sn = (slash_sn or n.val("SURN") or "").strip()
        disp = (gv + " " + sn).strip() or v.replace("/", "").strip()
        score = (2 if slash_sn else 0) + (1 if gv else 0)
        return gv, sn, disp, score

    parsed = [parse_one(n) for n in names]
    if not parsed:
        return "", "", "", []
    best = max(range(len(parsed)), key=lambda i: (parsed[i][3], -i))
    gv, sn, full, _ = parsed[best]
    alts = [p[2] for j, p in enumerate(parsed)
            if j != best and p[2] and p[2] != full]
    return full, gv, sn, alts


def place_country(raw):
    low = raw.lower()
    if any(t in low for t in ("united states", "usa", "u.s.a")):
        return "USA"
    return ""


def yfix(v):
    if v is None or v == "":
        return ""
    s = str(v)
    needs_quote = (
        s != s.strip()
        or s[0] in "?-:,[]{}#&*!|>'\"%@`"
        or ": " in s or " #" in s
        or s.lower() in ("null", "true", "false", "yes", "no", "~", "none")
        or re.fullmatch(r"-?\d+(\.\d+)?", s) is not None
    )
    if needs_quote:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def fm_list(key, items):
    if not items:
        return f"{key}: []"
    out = [f"{key}:"]
    for it in items:
        out.append(f"  - {yfix(it)}")
    return "\n".join(out)


def build(ged_path, dry_run=False):
    text = Path(ged_path).read_bytes().decode("utf-8-sig")
    roots = parse_gedcom(text)

    indis = {r.xref: r for r in roots if r.tag == "INDI"}
    fams = {r.xref: r for r in roots if r.tag == "FAM"}
    sours = {r.xref: r for r in roots if r.tag == "SOUR"}

    person = {}
    used_slugs = {}

    def claim(base):
        base = base or "unknown"
        if base not in used_slugs:
            used_slugs[base] = 1
            return base
        used_slugs[base] += 1
        return f"{base}-{used_slugs[base]}"

    for xref, rec in indis.items():
        full, given, surname, alts = parse_name(rec)
        bd = norm_date(rec.first("BIRT").val("DATE")) if rec.first("BIRT") else None
        dd = norm_date(rec.first("DEAT").val("DATE")) if rec.first("DEAT") else None
        if bd and bd["year"]:
            yr = ("c" + str(bd["year"])) if bd["approx"] else str(bd["year"])
        else:
            yr = "unknown"
        sg = slugify(surname) or "unknown"
        gg = slugify(given.split()[0]) if given.strip() else "unknown"
        slug = claim(f"{sg}-{gg}-{yr}")
        person[xref] = {
            "slug": slug, "full": full, "given": given, "surname": surname,
            "alts": alts, "birth": bd, "death": dd, "rec": rec,
            "sex": rec.val("SEX", ""),
            "famc": rec.first("FAMC").value if rec.first("FAMC") else None,
            "fams": [c.value for c in rec.kids("FAMS")],
            "src": [], "tags": [],
        }

    source = {}
    s_used = {}

    def s_claim(base):
        base = base or "source"
        if base not in s_used:
            s_used[base] = 1
            return base
        s_used[base] += 1
        return f"{base}-{s_used[base]}"

    SRC_TYPES = [
        ("census", "census"), ("draft", "draft-registration"),
        ("naturaliz", "naturalization"), ("marriage", "certificate"),
        ("death", "certificate"), ("birth", "certificate"),
        ("obituary", "obituary"), ("cemetery", "cemetery"),
        ("find a grave", "cemetery"), ("social security", "ssdi"),
        ("passenger", "immigration"), ("immigration", "immigration"),
        ("military", "military"), ("directory", "directory"),
    ]

    for xref, rec in sours.items():
        title = (rec.first("TITL").full_value() if rec.first("TITL") else "") or ""
        title = title.strip()
        auth = (rec.first("AUTH").full_value() if rec.first("AUTH") else "") or ""
        publ = (rec.first("PUBL").full_value() if rec.first("PUBL") else "") or ""
        repo = rec.val("REPO", "") or ""
        low = title.lower()
        stype = "record"
        for kw, t in SRC_TYPES:
            if kw in low:
                stype = t
                break
        base = slugify(title)[:60] if title else slugify(xref.strip("@"))
        slug = s_claim(base or "source")
        source[xref] = {
            "slug": slug, "title": title or f"Source {xref.strip('@')}",
            "auth": auth.strip(), "publ": publ.strip(), "repo": repo.strip(),
            "stype": stype, "people": [],
        }

    def src_refs(node):
        out = []
        for c in node.kids("SOUR"):
            if c.value and c.value.startswith("@"):
                out.append(c.value)
        return out

    places = {}

    def reg_place(raw):
        if not raw or not raw.strip():
            return None
        raw = raw.strip()
        toks = [t.strip() for t in raw.split(",") if t.strip()]
        keep = [t for t in toks if t.lower() not in DROP_PLACE_TOKENS]
        slug = slugify(" ".join(keep)) or slugify(raw)
        if not slug:
            return None
        p = places.setdefault(slug, {"name": raw, "country": place_country(raw), "count": 0})
        p["count"] += 1
        return slug

    family = {}
    f_used = {}

    def f_claim(base):
        if base not in f_used:
            f_used[base] = 1
            return base
        f_used[base] += 1
        return f"{base}-{f_used[base]}"

    for xref, rec in fams.items():
        husb = rec.val("HUSB")
        wife = rec.val("WIFE")
        chil = [c.value for c in rec.kids("CHIL")]
        marr = rec.first("MARR")
        mdate = norm_date(marr.val("DATE")) if marr else None
        mplace = reg_place(marr.val("PLAC")) if marr else None
        div = rec.first("DIV")
        ddate = norm_date(div.val("DATE")) if div else None
        partners = [p for p in (husb, wife) if p and p in person]
        s_parts = [slugify(person[p]["surname"]) or "x" for p in partners] or ["union"]
        myr = str(mdate["year"]) if (mdate and mdate["year"]) else "unknown"
        slug = f_claim("-".join(s_parts + [myr]))
        family[xref] = {
            "slug": slug, "husb": husb, "wife": wife, "chil": chil,
            "mdate": mdate, "mplace": mplace, "ddate": ddate,
            "partners": partners, "src": src_refs(rec),
        }

    # partners: symmetric pair written to BOTH spouses
    for p in person.values():
        p["partners"] = []
    seen_pair = {}
    for fx, f in family.items():
        h, w = f["husb"], f["wife"]
        if not (h in person and w in person):
            continue
        entry = {
            "married": (f["mdate"]["iso"] if f["mdate"] else None),
            "place": f["mplace"],
            "divorced": (f["ddate"]["iso"] if f["ddate"] else None),
        }
        for a, b in ((h, w), (w, h)):
            if a == b or person[a]["slug"] == person[b]["slug"]:
                continue
            if b in seen_pair.get(a, set()):
                continue
            seen_pair.setdefault(a, set()).add(b)
            person[a]["partners"].append({"person": person[b]["slug"], **entry})

    for xref, p in person.items():
        rec = p["rec"]
        parents = []
        if p["famc"] and p["famc"] in family:
            f = family[p["famc"]]
            for pp in (f["husb"], f["wife"]):
                if pp and pp in person and person[pp]["slug"] != p["slug"]:
                    parents.append(person[pp]["slug"])
        p["parents"] = parents

        bplace = reg_place(rec.first("BIRT").val("PLAC")) if rec.first("BIRT") else None
        dplace = reg_place(rec.first("DEAT").val("PLAC")) if rec.first("DEAT") else None
        p["bplace"] = bplace
        p["dplace"] = dplace

        seen = set()
        srcs = []
        for sref in src_refs(rec):
            if sref in source and sref not in seen:
                seen.add(sref)
                srcs.append(source[sref]["slug"])
                source[sref]["people"].append(p["slug"])
        p["sources"] = srcs

        events = []

        def add_ev(nd, label, plac_raw, srefs):
            plac_slug = reg_place(plac_raw) if plac_raw else None
            slink = ""
            for sr in srefs:
                if sr in source:
                    slink = f"[[{source[sr]['slug']}]]"
                    break
            events.append({
                "sort": (nd["iso"] or ("%04d" % nd["year"]) if nd and (nd["iso"] or nd["year"]) else "9999"),
                "date": pretty_date(nd) if nd else "",
                "label": label,
                "place": f"[[{plac_slug}]]" if plac_slug else (plac_raw or ""),
                "src": slink,
            })

        if rec.first("BIRT"):
            b = rec.first("BIRT")
            add_ev(norm_date(b.val("DATE")), "Born", b.val("PLAC"), src_refs(b))
        for ev in rec.kids("RESI"):
            note = ev.val("NOTE", "")
            lbl = "Residence" + (f" — {note}" if note else "")
            add_ev(norm_date(ev.val("DATE")), lbl, ev.val("PLAC"), src_refs(ev))
        for ev in rec.kids("EVEN"):
            t = ev.val("TYPE", "Event")
            add_ev(norm_date(ev.val("DATE")), t, ev.val("PLAC"), src_refs(ev))
        for ev in rec.kids("OCCU"):
            events.append({"sort": "9998", "date": "", "label": f"Occupation: {ev.value}",
                           "place": "", "src": ""})
        for fx in p["fams"]:
            f = family.get(fx)
            if f and f["mdate"]:
                other = f["wife"] if f["husb"] == xref else f["husb"]
                oname = person[other]["full"] if other in person else "?"
                add_ev(f["mdate"], f"Married {oname}", None, [])
                if f["mplace"]:
                    events[-1]["place"] = f"[[{f['mplace']}]]"
        if rec.first("DEAT"):
            d = rec.first("DEAT")
            add_ev(norm_date(d.val("DATE")), "Died", d.val("PLAC"), src_refs(d))
        if rec.first("BURI"):
            bu = rec.first("BURI")
            add_ev(norm_date(bu.val("DATE")), "Buried", bu.val("PLAC"), src_refs(bu))
        events.sort(key=lambda e: e["sort"])
        p["events"] = events

        if not p["death"]:
            by = p["birth"]["year"] if p["birth"] else None
            if by is None or by >= 1935:
                p["tags"].append("living?")
        if p["surname"]:
            p["tags"].append(slugify(p["surname"]) + "-family")

    if dry_run:
        print(f"DRY RUN: {len(person)} people, {len(family)} families, "
              f"{len(source)} sources, {len(places)} places.")
        return

    npeople = nfam = nsrc = nplace = 0

    for xref, p in person.items():
        d = ROOT / "people" / p["slug"]
        (d / "photos").mkdir(parents=True, exist_ok=True)
        (d / "documents").mkdir(parents=True, exist_ok=True)
        (d / "notes").mkdir(parents=True, exist_ok=True)
        fm = ["---"]
        fm.append(f"id: {p['slug']}")
        fm.append("type: person")
        fm.append(f"full_name: {yfix(p['full'])}")
        fm.append(f"given_name: {yfix(p['given'])}")
        fm.append(f"surname: {yfix(p['surname'])}")
        fm.append(fm_list("alternate_names", p["alts"]))
        fm.append(f"birth_date: {yfix(p['birth']['iso']) if p['birth'] and p['birth']['iso'] else ''}")
        fm.append(f"death_date: {yfix(p['death']['iso']) if p['death'] and p['death']['iso'] else ''}")
        fm.append(f"birth_place: {yfix(p['bplace']) if p['bplace'] else ''}")
        fm.append(f"death_place: {yfix(p['dplace']) if p['dplace'] else ''}")
        fm.append(fm_list("parents", p["parents"]))
        if p["partners"]:
            fm.append("partners:")
            for pt in p["partners"]:
                fm.append(f"  - person: {yfix(pt['person'])}")
                fm.append(f"    married: {yfix(pt['married']) if pt['married'] else 'null'}")
                fm.append(f"    place: {yfix(pt['place']) if pt['place'] else 'null'}")
                fm.append(f"    divorced: {yfix(pt['divorced']) if pt['divorced'] else 'null'}")
        else:
            fm.append("partners: []")
        fm.append(fm_list("sources", p["sources"]))
        fm.append(fm_list("tags", p["tags"]))
        fm.append("---")

        born = pretty_date(p["birth"])
        died = pretty_date(p["death"])
        bp = f", [[{p['bplace']}]]" if p["bplace"] else ""
        dp = f", [[{p['dplace']}]]" if p["dplace"] else ""
        body = [f"\n# {p['full'] or p['slug']}\n", "## Snapshot"]
        body.append(f"- **Born:** {born}{bp}" if born or bp else "- **Born:** —")
        body.append(f"- **Died:** {died}{dp}" if died or dp else "- **Died:** —")
        if p["alts"]:
            body.append(f"- **Also known as:** {', '.join(p['alts'])}")
        body.append("\n## Biography\n_Imported from Ancestry. Add narrative here._\n")
        body.append("## Timeline")
        body.append("| Date | Event | Place | Source |")
        body.append("|------|-------|-------|--------|")
        if p["events"]:
            for e in p["events"]:
                body.append(f"| {e['date']} | {e['label']} | {e['place']} | {e['src']} |")
        else:
            body.append("|  |  |  |  |")
        body.append("\n<!-- AUTO:relations — regenerated by scripts/regenerate.py, do not edit by hand -->")
        body.append("<!-- /AUTO -->\n")

        (d / f"{p['slug']}.md").write_text("\n".join(fm) + "\n" + "\n".join(body), encoding="utf-8")
        npeople += 1

    for fx, f in family.items():
        if len(f["partners"]) < 1:
            continue
        d = ROOT / "families" / f["slug"]
        d.mkdir(parents=True, exist_ok=True)
        pslugs = [person[p]["slug"] for p in f["partners"]]
        pnames = [person[p]["full"] or person[p]["slug"] for p in f["partners"]]
        fsrc = [source[s]["slug"] for s in f["src"] if s in source]
        fm = ["---", f"id: {f['slug']}", "type: family"]
        fm.append(fm_list("partners", pslugs))
        fm.append(f"marriage_date: {yfix(f['mdate']['iso']) if f['mdate'] and f['mdate']['iso'] else ''}")
        fm.append(f"marriage_place: {yfix(f['mplace']) if f['mplace'] else ''}")
        fm.append(f"divorce_date: {yfix(f['ddate']['iso']) if f['ddate'] and f['ddate']['iso'] else ''}")
        fm.append(fm_list("sources", fsrc))
        fm.append("---")
        title = " & ".join(f"[[{s}|{n}]]" for s, n in zip(pslugs, pnames))
        body = [f"\n# Marriage of {title}\n"]
        if f["mdate"]:
            where = f" in [[{f['mplace']}]]" if f["mplace"] else ""
            body.append(f"Married {pretty_date(f['mdate'])}{where}.\n")
        body.append("Marriage-level facts only. Children are derived from each child's "
                    "`parents` field and rendered below by the regenerator.\n")
        body.append("<!-- AUTO:family — regenerated by scripts/regenerate.py, do not edit by hand -->")
        body.append("<!-- /AUTO -->\n")
        d.joinpath(f"{f['slug']}.md").write_text("\n".join(fm) + "\n" + "\n".join(body), encoding="utf-8")
        nfam += 1

    for sx, s in source.items():
        ppl = sorted(set(s["people"]))
        fm = ["---", f"id: {s['slug']}", "type: source",
              f"title: {yfix(s['title'])}", "date: ",
              f"source_type: {yfix(s['stype'])}",
              "reliability: medium"]
        fm.append(fm_list("people", ppl))
        fm.append(f"repository: {yfix(s['repo'])}")
        fm.append("---")
        body = [f"\n# {s['title']}\n", "## Summary",
                "_Imported from Ancestry._\n", "## Citation"]
        cite = ", ".join(x for x in (s["auth"], s["publ"], s["repo"]) if x)
        body.append(cite or "_Citation detail not provided in the export._")
        (ROOT / "sources" / f"{s['slug']}.md").write_text(
            "\n".join(fm) + "\n" + "\n".join(body), encoding="utf-8")
        nsrc += 1

    for slug, pl in places.items():
        fm = ["---", f"id: {slug}", "type: place",
              f"name: {yfix(pl['name'])}", "county: ", "state: ",
              f"country: {yfix(pl['country'])}", "coordinates: ", "---"]
        body = [f"\n# {pl['name']}\n",
                f"Referenced by {pl['count']} record(s). "
                "Backlinks show everyone connected to this place.\n"]
        (ROOT / "places" / f"{slug}.md").write_text(
            "\n".join(fm) + "\n" + "\n".join(body), encoding="utf-8")
        nplace += 1

    print(f"import complete: {npeople} people, {nfam} families, "
          f"{nsrc} sources, {nplace} places written.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ged")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    build(args.ged, dry_run=args.dry_run)
