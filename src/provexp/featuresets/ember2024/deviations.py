"""
Where our extractor departs from EMBER v3 as released, and where the parser's heuristics decide a feature: for one file,
whether each deviation or candidate applies (the extractor audit, Appendix D's deviations table).

Each check reads the file with pefile (with our patches installed by `features`) and states whether the case occurs:

    overlay_rules_differ    pefile's overlay start (data-directory extents included) differs from LIEF's (sections only)
    guard_fired             a directory parser crashed and only that directory was lost (our guard)
    repeated_descriptor     a DLL has more than one import descriptor (thrember's overwrite; we merge)
    dirs_below_16           fewer than 16 data directories, so thrember's loop drops the last real one, not RESERVED
    dropped_dir_nonzero     ... and that directory is not empty
    entry_rule_differs      thrember's entry section (pefile's `contains_rva`, then the first executable section) differs
                            from the section whose virtual extent [VA, VA + VirtualSize aligned up) holds the entry point
    entry_length_sensitive  pefile's `contains_rva` would answer otherwise if the file held every section's raw data
    align_bits              a section's alignment field is nonzero (pefile decodes it as several flags)
    sections_cut            pefile stopped reading the section table early (a null header, or its cap)
    export_names_lost       named exports pefile stopped before (an invalid name, a repeated entry, its caps)
    import_cap              pefile's 8,192-import cap was reached
    import_dll_invalid      a DLL name outside pefile's character set (read as "*invalid*")
    import_stopped          pefile stopped reading the import or delay-import descriptors after repeated errors
    string_patterns_differ  a string feature whose pattern we fixed (registry_key, email_addr, .click() counts otherwise
                            than thrember's; the names that differ in `string_patterns`)
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pefile

from provexp.featuresets.ember2024 import features

__all__ = ["CHECKS", "deviations"]

CHECKS = ("overlay_rules_differ", "guard_fired", "repeated_descriptor", "dirs_below_16", "dropped_dir_nonzero",
          "entry_rule_differs", "entry_length_sensitive", "align_bits", "sections_cut", "export_names_lost",
          "import_cap", "import_dll_invalid", "import_stopped", "string_patterns_differ")

SCN_EXECUTE = 0x20000000
_STRINGS_V3 = features.StringExtractor()  # type: ignore[no-untyped-call]
_STRINGS_FIXED = features.StringExtractorFixed()
SCN_ALIGN_MASK = 0x00F00000


################################################################################
# The checks
################################################################################


def _align_up(x: int, a: int) -> int:
    return x if a <= 0 else (x + a - 1) // a * a


def _name(s: pefile.SectionStructure) -> str:
    return str(s.Name.strip(b"\x00").decode(errors="ignore").lower())


def _fallback(pe: pefile.PE, found: str) -> str:
    """thrember's fallback: the first executable section when no section holds the entry point."""
    for s in pe.sections:
        if found:
            break
        if s.Characteristics & SCN_EXECUTE:
            found = _name(s)
    return found


def entry_sections(pe: pefile.PE) -> tuple[str, str]:
    """The entry section by thrember's rule and by the virtual extent of each section (both with thrember's fallback)."""
    ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    alignment = pe.OPTIONAL_HEADER.SectionAlignment
    thrember = virtual = ""
    for s in pe.sections:
        if s.contains_rva(ep):
            thrember = _name(s)
        if s.VirtualAddress <= ep < s.VirtualAddress + _align_up(s.Misc_VirtualSize or s.SizeOfRawData, alignment):
            virtual = _name(s)
    return _fallback(pe, thrember), _fallback(pe, virtual)


def _entry_length_sensitive(pe: pefile.PE, n: int) -> bool:
    """Whether `contains_rva`'s answer for the entry point hangs on the file's length (its truncated-section branch)."""
    ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    for s in pe.sections:
        if n - s.get_PointerToRawData_adj() < s.SizeOfRawData:
            lo = s.get_VirtualAddress_adj()
            if lo + s.Misc_VirtualSize <= ep < lo + max(s.SizeOfRawData, s.Misc_VirtualSize):
                return True
    return False


def deviations(z: bytes) -> dict[str, Any]:
    """
    Which deviations and candidates apply to one file (see the module docstring).

    Args:
        z: The file's bytes.

    Returns:
        `parses` and, if it parses, one entry per name in CHECKS (bool, or a count for `export_names_lost`), plus the
        two entry sections and the dropped directory's name where they apply.
    """
    # The string features do not depend on the parse.
    v3 = _STRINGS_V3.raw_features(z, None)["string_counts"]  # type: ignore[no-untyped-call]
    fixed = _STRINGS_FIXED.raw_features(z, None)["string_counts"]  # type: ignore[no-untyped-call]
    differ = sorted(k for k in features.FIXED_STRING_PATTERNS if v3.get(k, 0) != fixed.get(k, 0))
    row: dict[str, Any] = {"parses": False, "string_patterns_differ": bool(differ), "string_patterns": ",".join(differ)}
    try:
        pe = pefile.PE(data=z)
    except (pefile.PEFormatError, AttributeError):
        return row
    row["parses"] = True
    warnings = pe.get_warnings()
    row["overlay_rules_differ"] = features.PEFILE_OVERLAY_START(pe) != features.overlay_data_start_offset(pe)
    row["guard_fired"] = any("the directory is skipped" in w for w in warnings)
    imports = getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
    row["repeated_descriptor"] = any(k > 1 for k in Counter(e.dll for e in imports).values())
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    row["dirs_below_16"] = 0 < len(directories) < 16
    row["dropped_dir_nonzero"] = row["dirs_below_16"] and bool(directories[-1].Size or directories[-1].VirtualAddress)
    row["dropped_dir"] = directories[-1].name if row["dirs_below_16"] else ""
    row["entry_thrember"], row["entry_virtual"] = entry_sections(pe)
    row["entry_rule_differs"] = row["entry_thrember"] != row["entry_virtual"]
    row["entry_length_sensitive"] = _entry_length_sensitive(pe, len(z))
    row["align_bits"] = any(s.Characteristics & SCN_ALIGN_MASK for s in pe.sections)
    row["sections_cut"] = len(pe.sections) < pe.FILE_HEADER.NumberOfSections
    exports = getattr(pe, "DIRECTORY_ENTRY_EXPORT", None)
    named = sum(1 for e in exports.symbols if e.name) if exports is not None else 0
    row["export_names_lost"] = max(0, min(exports.struct.NumberOfNames, pefile.MAX_SYMBOL_EXPORT_COUNT) - named) if exports is not None else 0
    row["import_cap"] = any("too many imported symbols" in w.lower() or "excessive number of imports" in w.lower() for w in warnings)
    row["import_dll_invalid"] = any(e.dll == b"*invalid*" for e in imports)
    row["import_stopped"] = any(w.startswith(("Too many errors parsing the import directory",
                                              "Too many errors parsing the Delay import directory")) for w in warnings)
    return row
