#!/usr/bin/env python3
"""Post-import cleanup pass for the family-tree vault.

Fixes systematic artifacts inherited from the Ancestry export without needing a
re-import:

  1. Doubled surnames — "Eda Warner Warner" (a merged duplicate NAME record stuffed
     the surname into the given-name field). If given_name ends with the surname,
     strip it; rebuild full_name and the H1 heading.
  2. Collapsed whitespace — "Muriel  Marshall" -> "Muriel Marshall".
  3. Impossible vital dates — death before birth. We don't guess which date is
     right; we move the suspect death_date into a `death_date_disputed` field,
     null the live field so the graph is consistent, and leave a NOTE so a human
     can verify against a real record later.

Operates on people/<slug>/<slug>.md in place. Idempotent. Run:
    python scripts/cleanup.py
Then re-run regenerate.py (to refresh display names in AUTO blocks) and validate.py.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def get(field, text):
    m = re.search(rf"^{field}:\s*(.*)$", text, re.M)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def set_line(field, value, text):
    return re.sub(rf"^{field}:.*$", f"{field}: {value}", text, count=1, flags=re.M)


def year(v):
    m = re.match(r"(\d{4})", str(v or ""))
    return int(m.group(1)) if m else None


def main():
    fixed_names = fixed_ws = fixed_dates = 0
    for folder in sorted((ROOT / "people").iterdir()):
        note = folder / f"{folder.name}.md"
        if not note.exists():
            continue
        text = note.read_text(encoding="utf-8")
        orig = text

        given = get("given_name", text)
        surname = get("surname", text)
        full = get("full_name", text)

        # 1 + 2: de-duplicate surname and collapse whitespace
        g_tokens = given.split()
        new_given = given
        if surname and len(g_tokens) > 1 and g_tokens[-1] == surname:
            new_given = " ".join(g_tokens[:-1])
        new_given = re.sub(r"\s+", " ", new_given).strip()
        new_full = re.sub(r"\s+", " ", f"{new_given} {surname}".strip()).strip()
        # also catch a doubled full_name even if given was already clean
        ft = new_full.split()
        if len(ft) >= 2 and ft[-1] == ft[-2]:
            new_full = " ".join(ft[:-1])

        if new_given != given:
            text = set_line("given_name", new_given, text)
        if new_full != full:
            text = set_line("full_name", new_full, text)
            # fix the H1 heading line that mirrors full_name
            text = re.sub(rf"^# {re.escape(full)}\s*$", f"# {new_full}", text, count=1, flags=re.M)
        if new_full != full or new_given != given:
            if re.sub(r"\s+", " ", full) != new_full:
                fixed_names += 1
            else:
                fixed_ws += 1

        # 3: impossible dates (death before birth)
        b, d = year(get("birth_date", text)), year(get("death_date", text))
        if b and d and d < b and "death_date_disputed" not in text:
            bad = get("death_date", text)
            text = set_line("death_date", "", text)
            # insert a disputed field right after death_date
            text = re.sub(r"^(death_date:.*)$",
                          rf"\1\ndeath_date_disputed: {bad}  # death before birth — verify",
                          text, count=1, flags=re.M)
            note_line = (f"\n> **Data note:** the source listed death {bad}, which is before the "
                         f"birth year {b} — impossible. Death date removed pending verification "
                         f"against a primary record.\n")
            # drop the note just after the frontmatter close
            parts = text.split("---", 2)
            if len(parts) == 3:
                text = parts[0] + "---" + parts[1] + "---" + note_line + parts[2]
            fixed_dates += 1

        if text != orig:
            note.write_text(text, encoding="utf-8")

    print(f"cleanup: {fixed_names} doubled names fixed, {fixed_ws} whitespace, "
          f"{fixed_dates} impossible-date records flagged.")


if __name__ == "__main__":
    main()
