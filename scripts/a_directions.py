"""
Direction A, step 2 (docs/direction-A-threat-model.md): the provisional direction table. For every EMBER v3 feature and
every operation of the threat models M_add, M_shift, M_full, the signs the operation can give the feature's change on
some file; a threat model's direction is the union over its operations (fixed, up, down, both). The same for the
feature's re-encoding as a layer-2 sum, where one exists.

The per-group rules are written by hand from the extractor's code and the operations' declared side effects: a
stand-in for C4 computed from the item table, used only for screening (go/no-go checks 2 and 3).

Outputs, in `{outdir}/`:
    directions.csv      one row per feature: index, name, group, the signs per operation, the direction under each
                        threat model, the re-encoding (if any), and its directions (all re-encodings need
                        re-extraction: the feature store holds only the features)
    summary.json        counts per group and threat model, for the features and their re-encodings
    {tm}[-quirkfixed].neutralize.txt   the features a sound monotone GBDT must drop (both), for scripts/train_classic.py
    {tm}[-quirkfixed].monotone.tsv     name<TAB>sign for the up (+1) and down (-1) features; fixed ones stay free
                        (`-quirkfixed`: as if the duplicate-library import quirk were fixed; check 3's sensitivity)

Usage:
    python scripts/a_directions.py --outdir artifacts/experiments/a_directions
"""

from __future__ import annotations

from argparse import ArgumentParser
import csv
import json
from pathlib import Path
import re
from typing import NamedTuple
from typing import Optional

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import StringExtractor

__all__ = [
    "OPS",
    "THREAT_MODELS",
    "Rule",
    "direction",
    "feature_rule",
]

################################################################################
# Operations and threat models
################################################################################

OPS = ("app", "sec", "imp", "ext", "shf", "slk", "dos", "hdr", "chk", "ren", "rdb", "rsg")
ADD = ("app", "sec", "imp")
INSERT = ("ext", "shf")
OVERWRITE = ("slk", "dos", "hdr", "chk", "ren", "rdb", "rsg")
THREAT_MODELS: dict[str, tuple[str, ...]] = {
    "M_add": ADD,
    "M_shift": ADD + INSERT,
    "M_full": OPS,
}

# Operations that write bytes in place inside the header region (an added section's table entry and counts, an
# insertion's pointer updates, and the overwrites other than slack).
HEADER_WRITES = ("sec", "imp", "ext", "shf", "dos", "hdr", "chk", "ren", "rdb", "rsg")

Signs = dict[str, str]  # op -> "", "+", "-", or "+-"


class Rule(NamedTuple):
    """The signs per operation for a feature, and for its re-encoding (if any)."""
    signs: Signs
    note: str
    reencoding: str = ""
    resigns: Optional[Signs] = None


def signs(**kwargs: str) -> Signs:
    """Signs per operation; operations not named do not move the feature."""
    unknown = set(kwargs) - set(OPS)
    if unknown:
        raise ValueError(f"Unknown operations: {sorted(unknown)}")
    return {op: kwargs.get(op, "") for op in OPS}


def every(sign: str, ops: tuple[str, ...] = OPS) -> Signs:
    """The same sign for every operation in `ops`; the others do not move the feature."""
    return {op: sign if op in ops else "" for op in OPS}


def direction(s: Signs, ops: tuple[str, ...]) -> str:
    """The direction of a feature under the operations `ops`: fixed, up, down, or both."""
    union = set("".join(s[op] for op in ops))
    if not union:
        return "fixed"
    if union == {"+"}:
        return "up"
    if union == {"-"}:
        return "down"
    return "both"


################################################################################
# Per-group rules
################################################################################

# Region-restricted counts (section bodies without slack, plus the overlay): only the additions move them.
BODY = signs(app="+", sec="+", imp="+")
NOTE_BODY = "counts over section bodies and the overlay only (no header region, no slack)"


def _trailing_boundary(pattern: str) -> bool:
    """Whether a regex ends in a word boundary, so that extending a matching string to the right can unmatch it."""
    return pattern.endswith("\\b")


def feature_rule(group: str, name: str, regexes: dict[str, str]) -> Rule:
    """The provisional rule for one feature (see the module docstring and the threat-model doc, Section 2)."""
    if group == "general":
        if name == "size":
            return Rule(signs(app="+", sec="+", imp="+", ext="+", shf="+"), "file size grows with every addition")
        if name == "entropy":
            return Rule(every("+-"), "entropy readout over the byte histogram")
        if name in ("is_pe", "start_byte_0", "start_byte_1"):
            return Rule(signs(), "'MZ' and a valid PE are kept")
        return Rule(signs(dos="+-"), "bytes 2-3 are DOS header fields")

    if group == "histogram":
        return Rule(every("+-"), "normalized by the file size",
                    reencoding=NOTE_BODY, resigns=BODY)

    if group == "byteentropy":
        return Rule(every("+-"), "normalized; insertions re-tile windows, in-place writes change them",
                    reencoding="windows tiled per region over section bodies and the overlay", resigns=BODY)

    if group == "strings":
        # In-place writes can merge or break existing strings, insertions can merge two strings across the gap.
        counted = {**every("+-", HEADER_WRITES + ("slk",)), "app": "+"}
        if name in ("numstrings", "printables"):
            return Rule(counted, "appends only add or extend strings", reencoding=NOTE_BODY, resigns=BODY)
        if name.startswith("printable_"):
            return Rule(every("+-"), "normalized by the number of printable characters",
                        reencoding="raw printable counts; " + NOTE_BODY, resigns=BODY)
        if name in ("avlength", "entropy"):
            return Rule(every("+-"), "ratio or entropy readout")
        if name.startswith("regex_"):
            key = name[len("regex_"):]
            if _trailing_boundary(regexes.get(key, "")):
                both = {**counted, "app": "+-"}
                return Rule(both, "the regex ends in \\b: extending a match to the right can unmatch it",
                            reencoding=NOTE_BODY, resigns={**BODY, "app": "+-"})
            return Rule(counted, "strings matching the regex", reencoding=NOTE_BODY, resigns=BODY)
        raise ValueError(f"Unexpected strings feature {name}")

    if group == "header":
        if name in ("file_header_NumberOfSections", "optional_header_SizeOfImage", "optional_header_SizeOfCode",
                    "optional_header_SizeOfInitializedData", "optional_header_SizeOfUninitializedData"):
            return Rule(signs(sec="+", imp="+"), "declared delta of an added section")
        if name == "optional_header_SizeOfHeaders":
            return Rule(signs(ext="+"), "the DOS extension grows the headers")
        if name == "dos_e_lfanew":
            return Rule(signs(ext="+"), "the DOS extension moves the PE header forward")
        if name in ("file_header_TimeDateStamp", "file_header_NumberOfSymbols", "file_header_PointerToSymbolTable",
                    "optional_header_MajorImageVersion", "optional_header_MinorImageVersion",
                    "optional_header_MajorLinkerVersion", "optional_header_MinorLinkerVersion",
                    "optional_header_MajorOperatingSystemVersion", "optional_header_MinorOperatingSystemVersion"):
            return Rule(signs(hdr="+-"), "loader-ignored header field")
        if name == "optional_header_CheckSum":
            return Rule(signs(chk="+-"), "checksum")
        if name.startswith("dos_") and name != "dos_e_magic":
            return Rule(signs(dos="+-"), "DOS header field in bytes 2-59")
        return Rule(signs(), "not written by any operation")

    if group == "section":
        if name in ("num_sections", "num_zero_size", "num_rx", "num_w"):
            return Rule(signs(sec="+", imp="+"), "count over sections")
        if name == "num_empty_name":
            return Rule(signs(sec="+", imp="+", ren="+-"), "count over sections; renaming can empty or fill a name")
        if name in ("min_entropy", "min_size_ratio", "min_vsize_ratio"):
            return Rule(signs(), "constant 0: the extractor appends 0 to the list before taking the min")
        if name == "max_vsize_ratio":
            return Rule(signs(sec="+", imp="+"), "max over sections of SizeOfRawData / VirtualSize")
        if name == "max_entropy":
            return Rule(signs(app="+-", sec="+", imp="+", slk="+-"),
                        "max includes the overlay's entropy, which appending can lower")
        if name == "max_size_ratio":
            return Rule(every("+-", ADD + INSERT), "divided by the file size")
        if name == "overlay_size":
            return Rule(signs(app="+"), "the overlay grows only by appending")
        if name in ("overlay_size_ratio", "overlay_entropy"):
            return Rule(every("+-", ADD + INSERT), "ratio or entropy readout")
        if name.startswith("entry_name_hash_"):
            return Rule(signs(ren="+-"), "signed hash of the entry section's name")
        if re.match(r"(size|vsize|entropy|characteristics)_hash_\d+$", name):
            s = signs(sec="+-", imp="+-", ren="+-", slk="+-" if name.startswith("entropy") else "")
            r = signs(sec="+", imp="+", ren="+-", slk="+-" if name.startswith("entropy") else "")
            return Rule(s, "signed hash keyed by section name",
                        reencoding="positive and negative parts of the bucket", resigns=r)
        raise ValueError(f"Unexpected section feature {name}")

    if group == "imports":
        if name == "num_libraries" or name.startswith("library_hash_"):
            return Rule(signs(imp="+"), "set of library names: duplicates do not remove one")
        return Rule(signs(imp="+-"), "a repeated DLL name overwrites the earlier descriptor's functions",
                    reencoding="imports accumulated per library (quirk fixed)", resigns=signs(imp="+"))

    if group == "exports":
        return Rule(signs(), "no operation touches the exports")

    if group == "datadirectories":
        if name.startswith(("import_", "iat_")):
            return Rule(signs(imp="+-"), "the import directory moves to a new section")
        if name.startswith("security_"):
            return Rule(signs(ext="+", shf="+", rsg="-"), "a file offset: insertions move it, removal zeroes it")
        if name.startswith("debug_"):
            return Rule(signs(rdb="-"), "removal zeroes it")
        return Rule(signs(), "not written by any operation")

    if group == "richheader":
        return Rule(signs(dos="+-"), "the Rich header lies in the DOS stub")

    if group == "authenticode":
        if name == "signing_time_diff":
            return Rule(signs(rsg="+-"), "falls to 0 when the signature is removed; may be negative")
        return Rule(signs(rsg="-"), "falls to 0 when the signature is removed")

    if group == "pefilewarnings":
        return Rule(every("+-"), "outside the model (no items)")

    raise ValueError(f"Unknown feature group {group}")


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, default=Path("artifacts/experiments/a_directions"))
    args = parser.parse_args()

    extractor = PEFeatureExtractor()
    strings = next(f for f in extractor.features if isinstance(f, StringExtractor))
    regexes = {k: r.pattern for k, r in strings._regexes.items()}

    rows: list[dict[str, str | int]] = []
    summary: dict[str, dict[str, dict[str, int]]] = {}
    index = 0
    for fs in extractor.features:
        for name in fs.feature_names:
            rule = feature_rule(fs.name, name, regexes)
            row: dict[str, str | int] = {"index": index, "name": name, "group": fs.name, "note": rule.note}
            row.update({f"op_{op}": rule.signs[op] for op in OPS})
            for tm, ops in THREAT_MODELS.items():
                d = direction(rule.signs, ops)
                rd = direction(rule.resigns, ops) if rule.resigns is not None else d
                row[tm] = d
                row[f"{tm}_reencoded"] = rd
                for kind, value in (("features", d), ("reencoded", rd)):
                    counts = summary.setdefault(f"{tm}/{kind}", {}).setdefault(fs.name, {})
                    counts[value] = counts.get(value, 0) + 1
            row["reencoding"] = rule.reencoding
            rows.append(row)
            index += 1

    args.outdir.mkdir(parents=True, exist_ok=True)
    with open(args.outdir / "directions.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    for tm in THREAT_MODELS:
        for variant in ("", "-quirkfixed"):
            drop, mono = [], []
            for row in rows:
                d = str(row[f"{tm}_reencoded" if variant and row["group"] == "imports" else tm])
                if d == "both":
                    drop.append(f"{row['group']}:{row['name']}")
                elif d in ("up", "down"):
                    mono.append(f"{row['group']}:{row['name']}\t{1 if d == 'up' else -1}")
            (args.outdir / f"{tm}{variant}.neutralize.txt").write_text("".join(n + "\n" for n in drop))
            (args.outdir / f"{tm}{variant}.monotone.tsv").write_text("".join(m + "\n" for m in mono))
    totals = {key: {d: sum(g.get(d, 0) for g in groups.values()) for d in ("fixed", "up", "down", "both")}
              for key, groups in summary.items()}
    with open(args.outdir / "summary.json", "w") as f:
        json.dump({"num_features": index, "totals": totals, "per_group": summary}, f, indent=2)
    for key, t in totals.items():
        print(f"{key:20s} {t}")


if __name__ == "__main__":
    main()
