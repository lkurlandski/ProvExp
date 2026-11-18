"""
Whether an attack's output counts: one rule for the whole evaluation (user, session 85).

An output counts (as an evasion, as a defense's training example, as evidence that a feature can be lowered) only if it
is still a working file as far as two independent parsers can tell: LIEF (a stand-in for the loader) and pefile (the
parser of our feature extractor) both read it, and neither has lost a structure the original had (its sections, its
imported DLLs and functions). The attacks only add, rename or shift; none removes a section or an import, so a loss is
breakage (session 85: secml-malware's shift writing in front of the MZ header, edits that overwrite the import data).

An output that only pefile fails on may be a working file our extractor misreads (e.g. pefile's 8,192-import cap,
`docs/upstream-issues.md` §10). It does not count either, since its feature vector is wrong and would propagate (a
false evasion, a feature marked lowerable that no working file lowers); the reason names the parser, so these cases
are logged as extractor quirks to fix at the source, after which the same rule counts them.

PE-specific by design: this guards the experiment's integrity and is not part of the framework (CLAUDE.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import lief
import pefile

__all__ = ["Structure", "output_invalid", "structure", "unreadable"]

lief.logging.disable()  # its parse warnings would flood every log that judges outputs


################################################################################
# Structure
################################################################################


@dataclass(frozen=True)
class Structure:
    """What each parser reads of a file: sections, imported DLLs, imported functions."""

    pefile_sections: int
    pefile_dlls: int
    pefile_functions: int
    lief_sections: int
    lief_dlls: int
    lief_functions: int


def _read_pefile(data: bytes) -> tuple[Optional[tuple[int, int, int]], str]:
    try:
        pe = pefile.PE(data=data)  # a full parse, as the extractor does
    except (pefile.PEFormatError, AttributeError) as e:
        return None, f"pefile does not parse ({str(e)[:80]})"
    entries = getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
    return (len(pe.sections), len(entries), sum(len(e.imports) for e in entries)), ""


def _read_lief(data: bytes) -> tuple[Optional[tuple[int, int, int]], str]:
    binary = lief.PE.parse(list(data))
    if binary is None:
        return None, "lief does not parse"
    imports = list(binary.imports)
    return (len(list(binary.sections)), len(imports), sum(len(list(i.entries)) for i in imports)), ""


def _who(pefile_fails: bool, lief_fails: bool) -> str:
    return "both" if pefile_fails and lief_fails else ("pefile only" if pefile_fails else "lief only")


def structure(data: bytes) -> tuple[Optional[Structure], str]:
    """
    What both parsers read of a file.

    Args:
        data: The file.

    Returns:
        (structure, "") if both parsers read it, else (None, the reason: "both", "pefile only" or "lief only", then
        what failed).
    """
    p, why_p = _read_pefile(data)
    lf, why_l = _read_lief(data)
    if p is None or lf is None:
        return None, f"{_who(p is None, lf is None)}: {'; '.join(w for w in (why_p, why_l) if w)}"
    return Structure(*p, *lf), ""


def unreadable(data: bytes) -> Optional[str]:
    """Why an original cannot be attacked under the rule (a parser does not read it), or None. No output of such a
    file could count, so the attacks are not applicable to it."""
    s, why = structure(data)
    return why if s is None else None


################################################################################
# The rule
################################################################################


_WHAT = ("sections", "dlls", "functions")


def output_invalid(original: Structure, output: bytes) -> Optional[str]:
    """
    Why an attack's output does not count, or None if it does.

    Args:
        original: `structure` of the file the attack started from.
        output: The attack's output.

    Returns:
        None if both parsers read the output and neither lost a section, an imported DLL or an imported function the
        original had; else the reason, starting with which parser failed ("both", "pefile only", "lief only"): the
        "pefile only" cases are the extractor's to fix.
    """
    s, why = structure(output)
    if s is None:
        return why
    lost = {parser: [f"{w} {getattr(original, f'{parser}_{w}')} -> {getattr(s, f'{parser}_{w}')}" for w in _WHAT
                     if getattr(s, f"{parser}_{w}") < getattr(original, f"{parser}_{w}")]
            for parser in ("pefile", "lief")}
    if not lost["pefile"] and not lost["lief"]:
        return None
    return f"{_who(bool(lost['pefile']), bool(lost['lief']))}: lost " + "; ".join(lost["pefile"] or lost["lief"])
