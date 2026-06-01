# Collins Family Tree — Audit & Sourcing Plan

*Generated from `Collins Family Tree.ged` (Ancestry export, 685 individuals). Scope of the active plan: Branden Collins's direct ancestral line, generations 0–4.*

---

## 1. Headline

The tree is **strong close in and speculative far out** — a normal shape, but worth naming precisely so effort goes where it pays. Your first four generations are essentially complete and well-documented; everything past roughly 1750 is thin, unsourced, and should be treated as hypothesis rather than fact.

Whole-tree confidence (all 685 people, scored 4→1):

| Rank | Label | People | Share |
|---|---|---|---|
| 4 | **Confirmed** | 478 | 70% |
| 3 | **Probable** | 83 | 12% |
| 2 | **Possible** | 83 | 12% |
| 1 | **Speculative** | 41 | 6% |

The 41 Speculative are almost entirely the deep English **Burrage / Burgh** line running back to the 1400s — unsourced and a classic signature of a tree copied onto a medieval "gateway" lineage.

---

## 2. The confidence ladder

Every person now carries a `confidence` rank in their vault frontmatter, so Obsidian can filter and colour by it.

- **4 — Confirmed.** Backed by real records (census, certificate, draft card, naturalization, passenger list, marriage record, military), whether an original image or an official index.
- **3 — Probable.** Some evidence, but thin: derivative-only sources (SSDI, public-records index, Find A Grave text) or a single citation.
- **2 — Possible.** In the tree but essentially unsourced; plausible by name, place and date, not yet proven.
- **1 — Speculative.** Unverified, likely inherited from other trees. Here: unsourced *and* born before 1750.

The point of the ladder is motion: **the gap between a person's current rank and "Confirmed" is their to-do list.**

---

## 3. Coverage by generation (direct line)

| Gen | Relationship | Known / Possible | Notes |
|---|---|---|---|
| 0 | self | 1 / 1 | Branden — currently unsourced (easy fix) |
| 1 | parents | 2 / 2 | thinly sourced; need vitals |
| 2 | grandparents | 4 / 4 | well documented, census-backed |
| 3 | great-grandparents | 8 / 8 | strong; mostly census + some certs |
| 4 | 2× great | 14 / 16 | strong, but **4 zero-source** close kin |
| 5 | 3× great | 15 / 32 | half missing; a third unsourced |
| 6–7 | 3×–5× great | 12 / 64, 5 / 128 | falling off |
| 11+ | deep line | single threads | **speculative — do not source** |

The standouts needing work are the close-in zero-source people — **Delores (—), Fredrick Lasalle, Fanny Hubbard, William Thomas** — because they're near you yet completely undocumented.

---

## 4. The real problem: index ≠ primary source

The tree's 178 "sources" look healthy by count (median 5 per person), but most are **Ancestry index entries, not original documents**. Breakdown:

- **~24 census** — genuinely primary (original page images exist). Highest-value, already attached.
- **~9 military/draft, ~8 immigration/naturalization** — usually real document images. Gold, especially for the immigrant Lasalle/Warner branches.
- **~35 marriage, ~31 death/burial, ~7 birth** — but mostly *indexes* ("North Carolina Death **Indexes**"), which point to a record rather than being it.
- **~2 SSDI, ~1 directory, ~58 public-records/misc** — derivative.
- **4 "Family Data Collection" / member trees** — not evidence at all.

So the work isn't *quantity* of sources — it's **upgrading index hits to the underlying original image**, and filling the zero-source gaps.

A reliability ladder for each fact: **Primary image** (census page, certificate, headstone photo) > **Official index** > **Derivative** (SSDI, public-records) > **Other trees** (discard).

---

## 5. The plan

Work **outward from yourself, by generation, stopping where the line goes speculative.**

**Tier 1 — do first (you + parents + any confidence ≤ 2).** Closest kin and the weakest records. Birth/marriage/death certificates exist for this era; pull them from state vital-records offices and FamilySearch (free). Branden himself has zero sources — start there.

**Tier 2 — grandparents & derivative-only records.** Upgrade index entries to original census and certificate images, decade by decade (1850–1950).

**Tier 3 — already-confirmed ancestors.** Verify and close remaining gaps (often a missing death date).

**Do NOT source:** anyone past ~1750 (the Burrage/Burgh line). Mark speculative, revisit only if a documented bridge appears.

**Per-person workflow:** find the original image → save it into `people/<slug>/documents/` → add a `sources/` node with `reliability: high` → cite it in the person's Timeline → re-run `stamp_confidence.py` + `regenerate.py` to watch the rank climb.

---

## 6. Data-quality fixes noted along the way

- **Lorraine Breedlove** — recorded born 1903 but died 1901 (impossible). Real error in the source tree.
- **"Miro Collins Collins"** and similar doubled surnames — the source record put a full name in the given-name field.
- **Place duplicates** — e.g. "denver" vs "Denver, CO" became separate place nodes; worth merging.

These were carried through faithfully rather than silently "corrected," so you decide each one.

---

*Companion file: `Collins-sourcing-tracker.xlsx` — the per-person working checklist, sorted by tier, with target records and where to find them.*
