"""
Cut out of a review folder everything one group of register items rests on, so a drafting agent reads a few pages
instead of the meta-review and all four reviews.

For each item: its register row (meta-review §6), the meta-review's §3 verdicts on the findings it cites, the §5
entries it names, and the cited reviewer passages (weaknesses, questions, numbered sections) in full. The register's
notes are appended once. Written to stdout.

Usage: python3 dossier.py docs/reviews/<TAG> R2 R17 R13 > docs/reviews/<TAG>/rebuttal/<group>.dossier.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

__all__ = ["build"]

################################################################################
# Parsing
################################################################################

FINDING = re.compile(r"\b([A-D])-([WQS])(\d+)\b")
SECTION_REF = re.compile(r"\b([A-D]) \(?§(\d)\)?")
META5_REF = re.compile(r"§5, items? ([\d, and]+)")


def section(lines: list[str], number: str) -> list[str]:
    """The lines of `## <number>.` up to the next `## ` heading."""
    out: list[str] = []
    on = False
    for line in lines:
        if line.startswith("## "):
            if on:
                break
            on = line.startswith(f"## {number}.")
        if on:
            out.append(line)
    return out


def passage(lines: list[str], fid: str) -> Optional[str]:
    """A reviewer's weakness, strength or question `fid` (e.g. B-W3), up to the next finding or heading."""
    start = re.compile(rf"^(#+ |\*\*|- \*\*){re.escape(fid)}\.")
    stop = re.compile(r"^(#+ |\*\*[A-D]-[WSQ]\d+\.|- \*\*[A-D]-[WSQ]\d+\.)")
    for i, line in enumerate(lines):
        if start.match(line):
            j = i + 1
            while j < len(lines) and not stop.match(lines[j]):
                j += 1
            return "\n".join(lines[i:j]).rstrip()
    return None


def numbered_item(lines: list[str], n: int) -> Optional[str]:
    """Item `n.` of a numbered list, up to the next item."""
    for i, line in enumerate(lines):
        if line.startswith(f"{n}. "):
            j = i + 1
            while j < len(lines) and not re.match(r"^(\d+\. |## )", lines[j]):
                j += 1
            return "\n".join(lines[i:j]).rstrip()
    return None


################################################################################
# The dossier
################################################################################


def build(out: Path, items: list[str]) -> str:
    """The dossier of `items` from the review folder `out`.

    Args:
        out: the review folder (holds meta-review.md and reviewer-*.md).
        items: register items, e.g. ["R2", "R17"].

    Returns:
        The dossier as Markdown.
    """
    meta = (out / "meta-review.md").read_text().splitlines()
    reviews = {r: (out / f"reviewer-{r}.md").read_text().splitlines()
               for r in "ABCD" if (out / f"reviewer-{r}.md").exists()}
    register = section(meta, "6")
    verdicts = section(meta, "3")
    missed = section(meta, "5")

    rows = {}
    for line in register:
        m = re.match(r"^\| (R\d+) \|", line)
        if m:
            rows[m.group(1)] = line
    unknown = [i for i in items if i not in rows]
    if unknown:
        raise ValueError(f"not in the register (§6): {unknown}")

    parts = [f"# Dossier: {' '.join(items)}", "",
             f"Cut from `{out}/` by `docs/reviews/process/dossier.py`. Facts tagged [verified] in the meta-review "
             "are taken as established.", ""]
    for item in items:
        row = rows[item]
        ids = sorted({f"{r}-{k}{n}" for r, k, n in FINDING.findall(row)},
                     key=lambda s: (s[0], s[2], int(s[3:])))
        parts += [f"## {item}", "", "### Register row (meta-review §6)", "",
                  "| R# | Risk | Raised by | L | Severity | Mitigation | Type | Effort |",
                  "|---|---|---|---|---|---|---|---|", row, ""]

        vrows = [ln for ln in verdicts if any(ln.startswith(f"| {i} |") for i in ids)]
        if vrows:
            parts += ["### Meta-review verdicts (§3)", "", "| ID | Verdict | Evidence |", "|---|---|---|", *vrows, ""]

        nums = sorted({int(n) for m in META5_REF.findall(row) for n in re.findall(r"\d+", m)})
        for n in nums:
            text = numbered_item(missed, n)
            if text:
                parts += [f"### Meta-review §5, item {n} (what the reviewers missed)", "", text, ""]

        parts += ["### Reviewer passages cited", ""]
        for fid in ids:
            text = passage(reviews.get(fid[0], []), fid)
            parts += [text if text else f"*{fid}: not found in reviewer-{fid[0]}.md*", ""]
        for r, n in sorted(set(SECTION_REF.findall(row))):
            parts += [f"*Reviewer {r}, §{n}:*", "", "\n".join(section(reviews.get(r, []), n)).rstrip(), ""]

    notes = []
    on = False
    for line in register:
        if line.startswith("Notes:"):
            on = True
        if on:
            notes.append(line)
    if notes:
        parts += ["## Register notes (meta-review §6)", "", *notes, ""]
    return "\n".join(parts)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: dossier.py <review folder> R# [R# ...]")
    sys.stdout.write(build(Path(sys.argv[1]), sys.argv[2:]))
