# The Collins Family Tree

A shared, plain-text archive of our family history — every person, the records that
prove who they were, and the web of relationships connecting us all.

This is built to last. Every page is a plain text file you can open in 30 years with
any program. Nothing is locked inside paid software. You can read it three ways:

- **On the web** — the published site shows every person and an interactive map of
  how everyone connects. *(Link goes here once published — see `docs/PUBLISHING.md`.)*
- **In Obsidian** — open this folder as a vault for the same graph on your own
  computer, free. ([obsidian.md](https://obsidian.md))
- **As files** — just open any `.md` file in `people/`. It's readable as-is.

---

## How it's organized

Everything is a node you can link to:

- **`people/`** — one folder per person (`surname-given-birthyear`), holding their
  page plus their own `photos/`, `documents/`, and `notes/`. *Grab one folder and
  you have everything about that person.*
- **`sources/`** — the records that back up our facts (census pages, certificates,
  obituaries). A single source can document many people.
- **`places/`** — locations, so "everyone born in Caswell County" is one click.
- **`families/`** — marriage facts.

The golden rule: **facts live inside the files, not in the folder structure.** Each
person lists their own parents; children, siblings, and cousins are computed
automatically. That keeps the tree from ever contradicting itself.

## How sure are we? — the confidence ranking

Every person carries a confidence level, because not everything in a family tree is
equally proven. When you browse, you'll see one of:

- **Confirmed** — backed by real records (a census, a certificate)
- **Probable** — some evidence, but thin
- **Possible** — in the tree and plausible, but not yet documented
- **Speculative** — unverified, likely carried over from other people's trees; treat
  as a lead, not a fact

The goal of this whole project is to move people *up* that ladder by finding real
documents. Which brings us to —

## How you can help (yes, you!)

If you have an old photo, a certificate, a family Bible page, an obituary, or just a
story or correction — **we want it.** You do not need to be technical. See
**[CONTRIBUTING.md](CONTRIBUTING.md)** for three easy ways to add what you have,
from "just tell us about it" to "upload the scan yourself."

## For the maintainer

- **`scripts/`** — the tooling. After any change to the data, run:
  `python3 scripts/regenerate.py` (rebuilds the relationship blocks) then
  `python3 scripts/validate.py` (checks integrity). When new records arrive, the
  document-ingest workflow reads them and proposes updates.
- **`docs/PUBLISHING.md`** — one-time setup to put the site online with Quartz.
- **`_inbox/`** — drop new documents here for processing.

*Started from an Ancestry export of 685 people. Maintained as a living archive.*
