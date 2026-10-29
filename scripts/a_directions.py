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

With `--extractor sums`, the same for the features of `SumsFeatureExtractor` (merged imports plus the four re-encoded
groups, which `feature_rule` covers with the re-encodings' signs). Its variants are `{tm}` (every feature: the "C4 on
sums" detector) and `{tm}-control` (the four re-encoded groups dropped: "C4 on features" on the same store);
`reencoded.neutralize.txt` lists the four groups, for the unconstrained reference on the same store.

With `--derive --extractor sums`, the variant files are written in the sums extractor's layout (`write_sums_layout`):
`{tm}-pre` and `{tm}-pre-control`, as run 80's `{tm}` and `{tm}-control`.

With `--derive`, the directions are computed instead of read off the hand rules (derivation step 7, C4;
docs/item-layer-design.md, component 5): the kinds' term vocabulary and the in-place operations' changes come from the
item tables of the files in --files, the structural operations' changes from the catalogue
(provexp.featuresets.ember2024.catalogue), and provexp.reach.directions turns them into signs. Two variants: strict
(appending may complete structures past the end of the file, on any file) and the precondition row's (`-pre`: only
files where no locating range lies past the end of the file). The re-encodings are derived too (step 8), from the item
tables of `SumsFeatureExtractor` (imports merged, and the four re-encoded groups as identity readouts over their sums):
    directions_sums.csv one row per feature of the sums extractor: the derived signs per operation, the derived and
                        hand directions per threat model, in both variants
Also writes the comparison with the hand rules (G3):
    g3_cells.csv        one row per (feature, operation) where the derived and hand signs differ
    g3_sums_cells.csv   the same for the four re-encoded groups (G3 for sums), per variant
    g3.json             counts per group and threat model, the features whose direction changes, and the corpus
                        (files, those with a locating range past the end, and the kinds located there)

Usage:
    python scripts/a_directions.py --outdir artifacts/experiments/a_directions
    python scripts/a_directions.py --extractor sums --outdir artifacts/experiments/a_directions_sums
    python scripts/a_directions.py --derive --outdir artifacts/experiments/a_directions_derived
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import csv
import json
from multiprocessing import Pool
from pathlib import Path
import re
from typing import Any
from typing import NamedTuple
from typing import Optional
import warnings

import pefile
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.catalogue import PAST_END_KINDS
from provexp.featuresets.ember2024.catalogue import declared_changes
from provexp.featuresets.ember2024.catalogue import file_region_changes
from provexp.featuresets.ember2024.catalogue import precondition
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import StringExtractor
from provexp.featuresets.ember2024.sums import SUMS_GROUPS
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.reach import Change
from provexp.reach import Signs as SignSet
from provexp.reach import Vocabulary
from provexp.reach import directions as derive_directions
from provexp.reach import extension_monotone

warnings.filterwarnings("ignore", category=SyntaxWarning)

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

    # The re-encoded groups (provexp.featuresets.ember2024.sums), with the signs of their re-encodings above.
    if group in ("body_histogram", "body_byteentropy"):
        return Rule(BODY, NOTE_BODY)
    if group == "body_strings":
        if name.startswith("regex_") and _trailing_boundary(regexes.get(name[len("regex_"):], "")):
            return Rule({**BODY, "app": "+-"}, "the regex ends in \\b: extending a match to the right can unmatch it")
        return Rule(BODY, NOTE_BODY)
    if group == "section_split":
        return Rule(signs(sec="+", imp="+", ren="+-", slk="+-" if name.startswith("entropy") else ""),
                    "one sign's part of a bucket keyed by section name")

    raise ValueError(f"Unknown feature group {group}")


################################################################################
# Derived directions (--derive)
################################################################################

_READER: Optional[SimpleDBReader] = None
# The merged variant is the sums extractor: its features start with the merged extractor's, in the same layout.
_EXTRACTORS: dict[str, PEFeatureExtractor] = {"original": PEFeatureExtractor(), "merged": SumsFeatureExtractor()}


def _init(db: str) -> None:
    global _READER
    _READER = SimpleDBReader(SimpleDB(Path(db), check=False))


def _past_end(table: Any) -> list[tuple[str, str]]:
    """The (group, kind) of the items with a locating range past the end of the file."""
    n = table.num_elements
    return sorted({(item.group, item.kind) for item in table.items if any(hi > n for _, hi in item.locating)})


def collect(name: str) -> dict[str, Any]:
    """One file: the vocabulary and the in-place operations' changes, per import variant, and the kinds past the end."""
    assert _READER is not None
    bytez = _READER.get(name).data
    try:
        pe = pefile.PE(data=bytez)
    except (pefile.PEFormatError, AttributeError):
        pe = None
    out: dict[str, Any] = {"name": name, "is_pe": pe is not None, "size": len(bytez)}
    for variant, extractor in _EXTRACTORS.items():
        table = extractor.item_table(bytez)
        v = Vocabulary()
        v.add(table)
        out[variant] = {"vocabulary": v, "changes": file_region_changes(pe, bytez, table) if pe is not None else {}}
        out["past_end"] = _past_end(table)
        out["precondition"] = pe is not None and precondition(pe, table)
    return out


def _signs_str(s: SignSet) -> str:
    return "".join(c for c in "+-" if c in s)


def _write_monotone(outdir: Path, stem: str, rows: list[dict[str, Any]], column: str) -> None:
    """The neutralize (both) and monotone (up/down) files for one variant, from a direction column."""
    drop, mono = [], []
    for row in rows:
        d = str(row[column])
        if d == "both":
            drop.append(f"{row['group']}:{row['name']}")
        elif d in ("up", "down"):
            mono.append(f"{row['group']}:{row['name']}\t{1 if d == 'up' else -1}")
    (outdir / f"{stem}.neutralize.txt").write_text("".join(n + "\n" for n in drop))
    (outdir / f"{stem}.monotone.tsv").write_text("".join(m + "\n" for m in mono))


def reencoding_features(group: str, name: str) -> list[tuple[str, str]]:
    """The features of `SumsFeatureExtractor` that re-encode a feature of thrember's (none if it has no re-encoding)."""
    if group in ("histogram", "byteentropy"):
        return [(f"body_{group}", name)]
    if group == "strings" and (name in ("numstrings", "printables") or name.startswith(("printable_", "regex_"))):
        return [("body_strings", name)]
    if group == "section" and re.match(r"(size|vsize|entropy|characteristics)_hash_\d+$", name):
        return [("section_split", f"{name}_{part}") for part in ("pos", "neg")]
    if group == "imports":
        return [("imports", name)]
    return []


def write_sums_layout(outdir: Path, sums_rows: list[dict[str, Any]]) -> None:
    """
    The precondition row's derived directions for the features of `SumsFeatureExtractor` (the 10% store of Table A1).
    Variants `{tm}-pre` (every feature: C4 on sums) and `{tm}-pre-control` (the re-encoded groups dropped: C4 on
    features), and `reencoded.neutralize.txt`.
    """
    rows = []
    for row in sums_rows:
        out = {"group": row["group"], "name": row["name"]}
        for tm in THREAT_MODELS:
            out[tm] = row[f"{tm}_pre"]
            out[f"{tm}-control"] = "both" if row["group"] in SUMS_GROUPS else row[f"{tm}_pre"]
        rows.append(out)
    for tm in THREAT_MODELS:
        _write_monotone(outdir, f"{tm}-pre", rows, tm)
        _write_monotone(outdir, f"{tm}-pre-control", rows, f"{tm}-control")
    reencoded = [f"{row['group']}:{row['name']}" for row in rows if row["group"] in SUMS_GROUPS]
    (outdir / "reencoded.neutralize.txt").write_text("".join(n + "\n" for n in reencoded))


def main_derive(args: Any) -> None:
    """Derive the directions (C4) and compare them with the hand rules (G3)."""
    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")
    names = sorted(df["name"].to_list())
    if args.limit > 0:
        names = names[: args.limit]

    vocab = {v: Vocabulary() for v in _EXTRACTORS}
    changes: dict[tuple[str, bool], dict[str, set[Change]]] = {}
    past_end_files: Counter[tuple[str, str]] = Counter()
    num_pe = num_pre = 0
    failing: list[dict[str, Any]] = []
    with Pool(args.workers, initializer=_init, initargs=(str(args.db),)) as pool:
        for i, rec in enumerate(pool.imap_unordered(collect, names, chunksize=1)):
            num_pe += rec["is_pe"]
            pre = rec["precondition"]
            num_pre += pre
            if rec["is_pe"] and not pre:
                failing.append({"name": rec["name"], "size": rec["size"], "past_end_items": rec["past_end"]})
            past_end_files.update(rec["past_end"])
            for variant in _EXTRACTORS:
                vocab[variant].merge(rec[variant]["vocabulary"])
                for op, cs in rec[variant]["changes"].items():
                    changes.setdefault((variant, False), {}).setdefault(op, set()).update(cs)
                    if pre:
                        changes.setdefault((variant, True), {}).setdefault(op, set()).update(cs)
            if (i + 1) % 20 == 0:
                print(f"{i + 1}/{len(names)} files", flush=True)

    strings = next(f for f in _EXTRACTORS["original"].features if isinstance(f, StringExtractor))
    regexes = {k: r.pattern for k, r in strings._regexes.items()}
    monotone = [extension_monotone(regexes[k]) for k in sorted(regexes)]
    derived: dict[tuple[str, bool], dict[str, list[SignSet]]] = {}
    for variant, extractor in _EXTRACTORS.items():
        profiles, sizes = vocab[variant].finish()
        for pre in (False, True):
            ops = {op: sorted(cs, key=repr) for op, cs in changes[(variant, pre)].items()}
            ops.update(declared_changes(profiles, monotone, strict=not pre))
            derived[(variant, pre)] = derive_directions(extractor.readouts, ops, profiles, sizes)

    # The features of the sums extractor (the merged variant), by (group, name).
    sums_extractor = _EXTRACTORS["merged"]
    sums_index = {(fs.name, n): i for i, (fs, n) in enumerate((fs, n) for fs in sums_extractor.features for n in fs.feature_names)}

    # One row per feature, in run 76's shape, plus the precondition row's directions.
    extractor = _EXTRACTORS["original"]
    rows: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    changed: dict[str, list[str]] = {}
    index = 0
    for fs in extractor.features:
        for name in fs.feature_names:
            hand = feature_rule(fs.name, name, regexes)
            row: dict[str, Any] = {"index": index, "name": name, "group": fs.name, "note": ""}
            for pre in (False, True):
                suffix = "_pre" if pre else ""
                s = {op: derived[("original", pre)][op][index] for op in OPS}
                m = {op: derived[("merged", pre)][op] for op in OPS}
                if not pre:
                    row.update({f"op_{op}": _signs_str(s[op]) for op in OPS})
                else:
                    row["op_app_pre"] = _signs_str(s["app"])
                for tm, tm_ops in THREAT_MODELS.items():
                    d = direction({op: _signs_str(s[op]) for op in OPS}, tm_ops)
                    re_ = [sums_index[f] for f in reencoding_features(fs.name, name)]
                    rd = direction({op: _signs_str(frozenset().union(*(m[op][j] for j in re_))) for op in OPS}, tm_ops) if re_ else d
                    row[f"{tm}{suffix}"] = d
                    row[f"{tm}{suffix}_reencoded"] = rd
                    if not pre:
                        hd = direction(hand.signs, tm_ops)
                        if d != hd:
                            changed.setdefault(tm, []).append(f"{fs.name}:{name} {hd} -> {d}")
            row["reencoding"] = hand.reencoding
            for op in OPS:
                h, d_ = hand.signs[op], str(row[f"op_{op}"])
                if set(h) != set(d_):
                    kind = "stricter" if set(h) < set(d_) else "looser" if set(d_) < set(h) else "different"
                    cells.append({"index": index, "group": fs.name, "name": name, "op": op, "hand": h, "derived": d_, "relation": kind})
            rows.append(row)
            index += 1

    args.outdir.mkdir(parents=True, exist_ok=True)
    with open(args.outdir / "directions.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    # With the sums extractor, the variant files are in its layout (below) instead.
    for tm in THREAT_MODELS if args.extractor == "ember2024" else ():
        for pre in ("", "_pre"):
            stem = tm + pre.replace("_", "-")
            _write_monotone(args.outdir, stem, rows, f"{tm}{pre}")
            quirk = [{**row, "d": row[f"{tm}{pre}_reencoded"] if row["group"] == "imports" else row[f"{tm}{pre}"]} for row in rows]
            _write_monotone(args.outdir, f"{stem}-quirkfixed", quirk, "d")
    # The sums extractor's features (G3 for sums: its re-encoded groups against the hand rules' re-encoded signs).
    sums_rows: list[dict[str, Any]] = []
    sums_cells: list[dict[str, Any]] = []
    for fs in sums_extractor.features:
        for name in fs.feature_names:
            j = sums_index[(fs.name, name)]
            hand = feature_rule(fs.name, name, regexes)
            row = {"index": j, "name": name, "group": fs.name}
            for pre in (False, True):
                suffix = "_pre" if pre else ""
                d_ = {op: _signs_str(derived[("merged", pre)][op][j]) for op in OPS}
                row.update({f"op_{op}{suffix}": d_[op] for op in OPS})
                for tm, tm_ops in THREAT_MODELS.items():
                    row[f"{tm}{suffix}"] = direction(d_, tm_ops)
                if fs.name in SUMS_GROUPS:
                    for op in OPS:
                        h = hand.signs[op]
                        if set(h) != set(d_[op]):
                            kind = "stricter" if set(h) < set(d_[op]) else "looser" if set(d_[op]) < set(h) else "different"
                            sums_cells.append({"index": j, "group": fs.name, "name": name, "variant": "pre" if pre else "strict", "op": op, "hand": h, "derived": d_[op], "relation": kind})
            for tm, tm_ops in THREAT_MODELS.items():
                row[f"{tm}_hand"] = direction(hand.signs, tm_ops) if fs.name in SUMS_GROUPS else ""
            sums_rows.append(row)
    with open(args.outdir / "directions_sums.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(sums_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sums_rows)
    cell_schema = {"index": pl.Int64, "group": pl.String, "name": pl.String, "variant": pl.String, "op": pl.String, "hand": pl.String, "derived": pl.String, "relation": pl.String}
    pl.DataFrame(sums_cells, schema=cell_schema).write_csv(args.outdir / "g3_sums_cells.csv")
    if args.extractor == "sums":
        write_sums_layout(args.outdir, sums_rows)
    pl.DataFrame(cells, schema={"index": pl.Int64, "group": pl.String, "name": pl.String, "op": pl.String, "hand": pl.String, "derived": pl.String, "relation": pl.String}).write_csv(args.outdir / "g3_cells.csv")

    summary: dict[str, Any] = {"files": len(names), "pe_files": num_pe, "precondition_files": num_pre,
                               "past_end_kinds": {f"{g}/{k}": c for (g, k), c in past_end_files.most_common()},
                               "past_end_kinds_undeclared": sorted(f"{g}/{k}" for g, k in past_end_files if (g, k) not in PAST_END_KINDS),
                               "precondition_failing": sorted(failing, key=lambda r: r["name"]),
                               "precondition_failing_at_size_cap": sum(r["size"] == 4_000_000 for r in failing)}
    for key in ["", "_pre"]:
        for tm in THREAT_MODELS:
            per_group: dict[str, dict[str, int]] = {}
            for row in rows:
                c = per_group.setdefault(row["group"], {})
                c[row[f"{tm}{key}"]] = c.get(row[f"{tm}{key}"], 0) + 1
            summary[f"{tm}{key}"] = {"totals": dict(Counter(row[f"{tm}{key}"] for row in rows)), "per_group": per_group}
    summary["hand"] = {tm: dict(Counter(direction(feature_rule(row["group"], row["name"], regexes).signs, ops) for row in rows)) for tm, ops in THREAT_MODELS.items()}
    summary["cells_by_relation"] = dict(Counter(c["relation"] for c in cells))
    summary["cells_by_group_op"] = dict(Counter(f"{c['group']}/{c['op']}/{c['relation']}" for c in cells).most_common())
    summary["threat_model_changes"] = changed
    # G3 for sums: the re-encoded groups' derived directions per threat model against the hand rules'.
    reencoded_rows = [row for row in sums_rows if row["group"] in SUMS_GROUPS]
    summary["sums"] = {
        f"{tm}{key}": {"totals": dict(Counter(row[f"{tm}{key}"] for row in reencoded_rows)),
                       "changes": [f"{row['group']}:{row['name']} {row[f'{tm}_hand']} -> {row[f'{tm}{key}']}" for row in reencoded_rows if row[f"{tm}{key}"] != row[f"{tm}_hand"]]}
        for key in ("", "_pre") for tm in THREAT_MODELS
    }
    summary["sums"]["hand"] = {tm: dict(Counter(row[f"{tm}_hand"] for row in reencoded_rows)) for tm in THREAT_MODELS}
    summary["sums"]["cells_by_group_op"] = dict(Counter(f"{c['variant']}/{c['group']}/{c['op']}/{c['relation']}" for c in sums_cells).most_common())
    (args.outdir / "g3.json").write_text(json.dumps(summary, indent=2))
    for key in ["hand"] + [f"{tm}{s}" for s in ("", "_pre") for tm in THREAT_MODELS]:
        print(f"{key:14s} {summary[key] if key == 'hand' else summary[key]['totals']}")
    for key in ["hand"] + [f"{tm}{s}" for s in ("", "_pre") for tm in THREAT_MODELS]:
        sums_summary = summary["sums"][key]
        print(f"sums {key:9s} {sums_summary if key == 'hand' else sums_summary['totals']}")
    print(json.dumps({k: summary[k] for k in ("files", "pe_files", "precondition_files", "precondition_failing_at_size_cap", "past_end_kinds", "past_end_kinds_undeclared", "cells_by_relation")}, indent=2))


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, default=Path("artifacts/experiments/a_directions"))
    parser.add_argument("--extractor", type=str, choices=["ember2024", "sums"], default="ember2024")
    parser.add_argument("--derive", action="store_true", help="Derive the directions from the item tables (C4).")
    parser.add_argument("--files", type=Path, default=Path("artifacts/experiments/e1/seed-0/zeros/files.parquet"), help="derive: the corpus (a `name` column).")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0, help="derive: only the first N files (0: all).")
    args = parser.parse_args()
    if args.derive:
        main_derive(args)
        return
    sums = args.extractor == "sums"

    extractor = SumsFeatureExtractor() if sums else PEFeatureExtractor()
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
        for variant in ("", "-control") if sums else ("", "-quirkfixed"):
            drop, mono = [], []
            for row in rows:
                # The sums extractor's imports are merged, so they take the quirk-fixed directions.
                merged = (sums or variant == "-quirkfixed") and row["group"] == "imports"
                d = str(row[f"{tm}_reencoded" if merged else tm])
                if variant == "-control" and row["group"] in SUMS_GROUPS:
                    d = "both"
                if d == "both":
                    drop.append(f"{row['group']}:{row['name']}")
                elif d in ("up", "down"):
                    mono.append(f"{row['group']}:{row['name']}\t{1 if d == 'up' else -1}")
            (args.outdir / f"{tm}{variant}.neutralize.txt").write_text("".join(n + "\n" for n in drop))
            (args.outdir / f"{tm}{variant}.monotone.tsv").write_text("".join(m + "\n" for m in mono))
    if sums:
        # The re-encoded groups alone, for the unconstrained reference on the same store.
        reencoded = [f"{row['group']}:{row['name']}" for row in rows if row["group"] in SUMS_GROUPS]
        (args.outdir / "reencoded.neutralize.txt").write_text("".join(n + "\n" for n in reencoded))
    totals = {key: {d: sum(g.get(d, 0) for g in groups.values()) for d in ("fixed", "up", "down", "both")}
              for key, groups in summary.items()}
    with open(args.outdir / "summary.json", "w") as f:
        json.dump({"num_features": index, "totals": totals, "per_group": summary}, f, indent=2)
    for key, t in totals.items():
        print(f"{key:20s} {t}")


if __name__ == "__main__":
    main()
