"""
Whether an attack's output counts: one rule for the whole evaluation (user, session 85).

An output counts (as an evasion, as a defense's training example, as evidence that a feature can be lowered) only if it
is still a working file as far as two independent parsers can tell: LIEF (a stand-in for the loader) and pefile (the
parser of our feature extractor) both read it, and neither has lost a structure the original had (its sections, its
imported DLLs and functions). The attacks only add, rename or shift; none removes a section or an import, so a loss is
breakage (session 85: secml-malware's shift writing in front of the MZ header, edits that overwrite the import data).

Losses are found by sets, not counts (user, session 101), so that an added DLL cannot hide a lost one: DLLs by
lowercase name, functions by (lowercase DLL, name or "#ordinal"), sections by virtual address as a multiset (user,
session 104). A section is identified by its address because that is the one property no attack changes: renames
(the adaptive search's `ren`, MAB-Malware's SR) change its name, shifts and header growth its file offset, `ext` its
sizes, slack writes its content; added sections sit at new addresses. A section moved in memory counts as lost, which
it is unless every reference into it were rewritten, and no attack does that (checked on 1,217 kept outputs, session
104). The rule does not check section content: whether an attack changed only what it declares is the catalogue
check's and `toolkit.structure_kept`'s question, not this one.

An output that only pefile fails on may be a working file our extractor misreads (e.g. pefile's 8,192-import cap,
`docs/upstream-issues.md` §10). It does not count either, since its feature vector is wrong and would propagate (a
false evasion, a feature marked lowerable that no working file lowers); the reason names the parser, so these cases
are logged as extractor quirks to fix at the source, after which the same rule counts them.

PE-specific by design: this guards the experiment's integrity and is not part of the framework (CLAUDE.md).
"""

from __future__ import annotations

from collections import Counter
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
    """What each parser reads of a file: section addresses (sorted, a multiset), imported DLLs (lowercase) and
    imported functions ((lowercase DLL, name or "#ordinal")). Small and picklable: computed in the main process and
    sent to workers."""

    pefile_sections: tuple[int, ...]
    pefile_dlls: frozenset[str]
    pefile_functions: frozenset[tuple[str, str]]
    lief_sections: tuple[int, ...]
    lief_dlls: frozenset[str]
    lief_functions: frozenset[tuple[str, str]]


_Parsed = tuple[tuple[int, ...], frozenset[str], frozenset[tuple[str, str]]]


def _text(b: Optional[str | bytes]) -> str:
    """A parser's name as text (bytes as latin-1: every byte maps, so distinct names stay distinct)."""
    return "" if b is None else (b if isinstance(b, str) else b.decode("latin-1"))


def _read_pefile(data: bytes) -> tuple[Optional[_Parsed], str]:
    try:
        pe = pefile.PE(data=data)  # a full parse, as the extractor does
    except (pefile.PEFormatError, AttributeError) as e:
        return None, f"pefile does not parse ({str(e)[:80]})"
    entries = getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
    dlls = frozenset(_text(e.dll).lower() for e in entries)
    functions = frozenset((_text(e.dll).lower(), _text(i.name) if i.name else f"#{i.ordinal}")
                          for e in entries for i in e.imports)
    return (tuple(sorted(s.VirtualAddress for s in pe.sections)), dlls, functions), ""


def _read_lief(data: bytes) -> tuple[Optional[_Parsed], str]:
    binary = lief.PE.parse(list(data))
    if binary is None:
        return None, "lief does not parse"
    imports = list(binary.imports)
    dlls = frozenset(_text(i.name).lower() for i in imports)
    functions = frozenset((_text(i.name).lower(), f"#{f.ordinal}" if f.is_ordinal else _text(f.name))
                          for i in imports for f in i.entries)
    return (tuple(sorted(s.virtual_address for s in binary.sections)), dlls, functions), ""


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


_EXAMPLES = 3


def _lost(original: Structure, output: Structure, parser: str) -> list[str]:
    """What `parser` read in the original and not in the output, one entry per kind with a few examples."""
    sections = Counter(getattr(original, f"{parser}_sections")) - Counter(getattr(output, f"{parser}_sections"))
    lost: dict[str, list[str]] = {
        "sections": sorted(f"0x{va:x}" for va in sections.elements()),
        "dlls": sorted(getattr(original, f"{parser}_dlls") - getattr(output, f"{parser}_dlls")),
        "functions": sorted(f"{d}!{f}" for d, f in getattr(original, f"{parser}_functions")
                            - getattr(output, f"{parser}_functions")),
    }
    return [f"{len(v)} {k} ({', '.join(v[:_EXAMPLES])}{', ...' if len(v) > _EXAMPLES else ''})"
            for k, v in lost.items() if v]


def output_invalid(original: Structure, output: bytes) -> Optional[str]:
    """
    Why an attack's output does not count, or None if it does.

    Args:
        original: `structure` of the file the attack started from.
        output: The attack's output.

    Returns:
        None if both parsers read the output and neither lost a section (by address), an imported DLL or an imported
        function the original had; else the reason, starting with which parser failed ("both", "pefile only", "lief
        only"): the "pefile only" cases are the extractor's to fix.
    """
    s, why = structure(output)
    if s is None:
        return why
    lost = {parser: _lost(original, s, parser) for parser in ("pefile", "lief")}
    if not lost["pefile"] and not lost["lief"]:
        return None
    return f"{_who(bool(lost['pefile']), bool(lost['lief']))}: lost " + "; ".join(lost["pefile"] or lost["lief"])
