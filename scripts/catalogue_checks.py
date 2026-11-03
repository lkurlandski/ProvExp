"""
Derivation step 6, the catalogue check G7 (docs/item-layer-design.md, "Validation and go/no-go checks"): do the
operations of the threat models change features only in the directions the C4 engine derived for them?

The derived directions (scripts/a_directions.py --derive --extractor sums) rest on the edit catalogue
(`featuresets/ember2024/catalogue.py`): the structural operations are declared there as item changes, the in-place ones
derived from the bytes they write. This script applies every operation to real files with our own byte-level edit
functions, including adversarial parameter choices (a repeated DLL name, an empty or colliding section name, printable
bytes next to existing strings, a forged Rich header in an inserted gap), re-extracts the edited file with the sums
extractor (thrember's features with merged imports, plus the four re-encoded groups), and checks every feature that
moved against the derived signs of that operation: a move the derived table rules out is a violation. The strict
variant must hold on every file; the precondition variant on the files that pass the precondition check.

The edits do exactly the declared operation and nothing else, unlike LIEF's writer, which relays out the file
(assumption A4, scripts/a1_adaptive.py): an added section's header goes into zero bytes after the section table, its
data at the end of the file or before the overlay (the attacker's choice; both layouts are tried on files with an
overlay); an import section holds a copy of the import descriptors plus the new ones, and the IMPORT entry points to
it; an insertion (`ext` at e_lfanew, `shf` before the first section's data) adds a multiple of FileAlignment and raises
the pointers past it (e_lfanew, SizeOfHeaders for `ext`, PointerToRawData, the certificate table's offset). Fields the
loader ignores (debug data pointers, PointerToSymbolTable) are left as they are, as the toolkits leave them. An
operation that does not apply to a file (no room for a section header, no debug entry, headers that cannot grow) is
recorded as such.

For the in-place operations and appends, the C1 engine (provexp.reach.predict, thrember's features with merged
imports) also predicts the edited file, which extends G6's random writes with the adversarial contents.

Outputs, in `{outdir}/`:
    edits.parquet   one row per (file, operation, instance): applies, parses, precondition, the precondition on the
                    edited file (P1, closure; for files that pass), features changed, violations under each
                    variant, the C1 result
    report.json     per operation: edits, violations by feature, observed (feature, sign) cells, edits that take a
                    passing file to a failing one; the verdicts (`pass`: G7; `closed`: P1)

Usage (smoke on three files):
    PYTHONHASHSEED=0 python scripts/catalogue_checks.py --outdir artifacts/experiments/catalogue_checks/smoke --num_files 3
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
from multiprocessing import get_context
from pathlib import Path
import struct
import sys
import time
from typing import Any
from typing import Callable
from typing import Optional
import warnings

import numpy as np
import pefile
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.catalogue import DEBUG_ENTRY
from provexp.featuresets.ember2024.catalogue import HDR_FIELDS
from provexp.featuresets.ember2024.catalogue import SECURITY_ENTRY
from provexp.featuresets.ember2024.catalogue import PAGE
from provexp.featuresets.ember2024.catalogue import passes_precondition
from provexp.featuresets.ember2024.catalogue import predict_add_imports
from provexp.featuresets.ember2024.catalogue import predict_add_section
from provexp.featuresets.ember2024.catalogue import predict_insert_gap
from provexp.featuresets.ember2024.catalogue import predict_rename
from provexp.featuresets.ember2024.catalogue import predict_zero_entry
from provexp.featuresets.ember2024.catalogue import regions
from provexp.featuresets.ember2024.catalogue import write_gap
from provexp.featuresets.ember2024.catalogue import write_imports
from provexp.featuresets.ember2024.catalogue import write_section
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.items import ItemTable
from provexp.reach import ByteEdit
from provexp.reach import Prediction
from provexp.reach import predict

__all__ = [
    "OPS",
    "add_imports",
    "add_section",
    "forged_rich",
    "insert_gap",
    "instances",
    "observed_signs",
]

OPS = ("app", "sec", "imp", "ext", "shf", "slk", "dos", "hdr", "chk", "ren", "rdb", "rsg")

SCN_CODE, SCN_DATA = 0x00000020, 0x00000040
SCN_EXECUTE, SCN_READ, SCN_WRITE = 0x20000000, 0x40000000, 0x80000000
DATA_CHARACTERISTICS = SCN_DATA | SCN_READ | SCN_WRITE
CODE_CHARACTERISTICS = SCN_CODE | SCN_READ | SCN_EXECUTE
IMPORT_ENTRY = 1

################################################################################
# Byte-level edits (exactly the declared operation)
################################################################################


def _parse(z: bytes, fast: bool = False) -> Optional[pefile.PE]:
    """Parse as the extractor does, or None."""
    try:
        return pefile.PE(data=z, fast_load=fast)
    except (pefile.PEFormatError, AttributeError):
        return None


def add_section(z: bytes, name: bytes, content: bytes, characteristics: int, before_overlay: bool,
                content_at_rva: Optional[Callable[[int], bytes]] = None) -> Optional[tuple[bytes, int]]:
    """
    Add a section (`sec`; `catalogue.write_section`): a header after the section table, the content padded to
    FileAlignment at the end of the file or (`before_overlay`) where pefile's overlay starts.

    Returns:
        The edited file and the new section's RVA, or None if the headers have no room for another section header.
    """
    written = write_section(z, name, content, characteristics, before_overlay, content_at_rva)
    return None if written is None else (written.new, written.layout["rva"])


def add_imports(z: bytes, library: bytes, functions: list[bytes], before_overlay: bool) -> Optional[bytes]:
    """Add imports (`imp`; `catalogue.write_imports`): a new section holding the import table, pointed to by IMPORT."""
    written = write_imports(z, library, functions, before_overlay)
    return None if written is None else written.new


def insert_gap(z: bytes, at_pe_header: bool, gap: bytes) -> Optional[bytes]:
    """Insert a gap (`ext` before the PE header, `shf` before the first section's data; `catalogue.write_gap`)."""
    written = write_gap(z, at_pe_header, gap)
    return None if written is None else written.new


def forged_rich(pairs: list[tuple[int, int]], key: int = 0x5EED5EED) -> bytes:
    """A Rich header block (DanS, padding, (comp.id, count) pairs, Rich, key), XOR-ed with `key`."""
    words = [0x536E6144 ^ key, key, key, key]
    for comp, count in pairs:
        words += [comp ^ key, count ^ key]
    return struct.pack(f"<{len(words)}I", *words) + b"Rich" + struct.pack("<I", key)


################################################################################
# Instances: each operation with ordinary and adversarial parameters
################################################################################

# An instance: (operation, label, the edited file or None if it does not apply, the in-place byte edits or None).
# The declared prediction of an item-stated instance (Table 5): writes the instance and predicts its features from the
# item table (`catalogue.predict_*`), given the extractor; None for the element-stated operations.
Declared = Optional[Callable[[PEFeatureExtractor], Optional[Prediction]]]
Instance = tuple[str, str, Optional[bytes], Optional[list[ByteEdit]], Declared]


def _printable(n: int, rng: np.random.Generator) -> bytes:
    return rng.integers(0x20, 0x7F, n, dtype=np.uint8).tobytes()


def _random(n: int, rng: np.random.Generator) -> bytes:
    return rng.integers(0, 256, n, dtype=np.uint8).tobytes()


def _in_place(op: str, label: str, z: bytes, edits: list[ByteEdit], declared: Declared = None) -> Instance:
    out = z
    for e in edits:
        out = e.apply(out)
    return op, label, out, edits, declared


def instances(z: bytes, pe: pefile.PE, table: ItemTable, rng: np.random.Generator) -> list[Instance]:
    """
    Every operation's instances on one file (parameters seeded by `rng`). The item-stated ones carry their declared
    prediction (`Declared`), which writes the same file.
    """
    out: list[Instance] = []
    has_overlay = pe.get_overlay_data_start_offset() is not None
    layouts = [False, True] if has_overlay else [False]
    sections = [s.Name.rstrip(b"\x00") for s in pe.sections]
    fa = pe.OPTIONAL_HEADER.FileAlignment or 0x200

    # app: random (crossing window boundaries), printable (extending a trailing string), a single zero byte.
    n = len(z)
    for label, content in (("random_3000", _random(3000, rng)), ("printable_64", _printable(64, rng)), ("zero_1", b"\x00")):
        out.append(("app", label, z + content, [ByteEdit(n, n, content)], None))

    # sec: ordinary, an empty name with printable code, a name colliding with an existing section, a case variant.
    specs = [("data_random", b".pv0", _random(4096, rng), DATA_CHARACTERISTICS),
             ("empty_name_printable_code", b"", _printable(700, rng), CODE_CHARACTERISTICS),
             ("colliding_name_zeros", sections[0] if sections else b".text", b"\x00" * 512, DATA_CHARACTERISTICS),
             ("case_variant_1_byte", (sections[-1] if sections else b".data").upper(), b"\x01", DATA_CHARACTERISTICS)]
    for label, name, content, ch in specs:
        for before in layouts:
            r = add_section(z, name, content, ch, before)

            def declared_sec(e: PEFeatureExtractor, name: bytes = name, content: bytes = content, ch: int = ch, before: bool = before) -> Optional[Prediction]:
                return predict_add_section(e, table, z, name, content, ch, before)

            out.append(("sec", label + ("_before_overlay" if before else ""), r[0] if r else None, None, declared_sec))

    # imp: a new library, a repeated library with a new function, a case variant with a function it already imports,
    # a library with no functions.
    imports = [(e.dll, [i.name for i in e.imports if i.name]) for e in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) if e.dll]
    specs_imp: list[tuple[str, bytes, list[bytes]]] = [("new_library", b"pvext.dll", [b"PvFunctionOne", b"PvFunctionTwo"])]
    if imports:
        dll, names = imports[0]
        specs_imp.append(("repeated_library", dll, [b"PvExtraFunction"]))
        specs_imp.append(("case_variant_duplicate_function", dll.swapcase(), names[:1] or [b"PvExtraFunction"]))
    specs_imp.append(("no_functions", b"pvempty.dll", []))
    for label, dll, funcs in specs_imp:
        for before in layouts:
            def declared_imp(e: PEFeatureExtractor, dll: bytes = dll, funcs: list[bytes] = funcs, before: bool = before) -> Optional[Prediction]:
                return predict_add_imports(e, table, z, dll, funcs, before)

            out.append(("imp", label + ("_before_overlay" if before else ""), add_imports(z, dll, funcs, before), None, declared_imp))

    # ext and shf: zeros, random, printable, and (ext) a forged Rich header in the gap.
    rich = forged_rich([(0x00FF0000 | 30319, 7), (0x00010000 | 40219, 3)])
    gaps = [("zeros", b"\x00" * fa), ("random", _random(fa, rng)), ("printable", _printable(fa, rng))]
    def declared_gap(at_pe_header: bool, gap: bytes) -> Declared:
        return lambda e: predict_insert_gap(e, table, z, at_pe_header, gap)

    def declared_rename(name: bytes) -> Declared:
        return lambda e: predict_rename(e, table, z, 0, name)

    def declared_entry(index: int) -> Declared:
        return lambda e: predict_zero_entry(e, table, z, index)

    for label, gap in gaps + [("forged_rich", rich + b"\x00" * (fa - len(rich)))]:
        out.append(("ext", label, insert_gap(z, True, gap), None, declared_gap(True, gap)))
    for label, gap in gaps:
        out.append(("shf", label, insert_gap(z, False, gap), None, declared_gap(False, gap)))

    # The in-place operations, over the regions the catalogue derives them from.
    reg = regions(pe, z, table)
    slack = sorted(reg["slk"], key=lambda r: r[0] - r[1])[:1]
    for lo, hi in slack:
        hi = min(hi, lo + 512)
        for label, content in (("printable", _printable(hi - lo, rng)), ("zeros", b"\x00" * (hi - lo)), ("random", _random(hi - lo, rng))):
            out.append(_in_place("slk", label, z, [ByteEdit(lo, hi, content)]))
    if not slack:
        out.append(("slk", "no_slack", None, None, None))
    dos = sorted(reg["dos"], key=lambda r: r[0] - r[1])
    if dos:
        lo, hi = dos[0]
        for label, content in (("printable", _printable(hi - lo, rng)), ("zeros", b"\x00" * (hi - lo)), ("random", _random(hi - lo, rng))):
            out.append(_in_place("dos", label, z, [ByteEdit(lo, hi, content)]))
        start = max(lo, 0x80)
        if hi - start >= len(rich):
            out.append(_in_place("dos", "forged_rich", z, [ByteEdit(start, start + len(rich), rich)]))
    fields = [field_range(getattr(pe, h), f) for h, f in HDR_FIELDS]
    for label, fill in (("zeros", lambda m: b"\x00" * m), ("max", lambda m: b"\xff" * m), ("random", lambda m: _random(m, rng))):
        out.append(_in_place("hdr", label, z, [ByteEdit(lo, hi, fill(hi - lo)) for lo, hi in fields]))
    lo, hi = field_range(pe.OPTIONAL_HEADER, "CheckSum")
    for label, content in (("zero", b"\x00" * 4), ("max", b"\xff" * 4), ("random", _random(4, rng))):
        out.append(_in_place("chk", label, z, [ByteEdit(lo, hi, content)]))
    if pe.sections:
        lo = pe.sections[0].get_file_offset()
        other = sections[1] if len(sections) > 1 else b".data"
        for label, name in (("empty", b""), ("colliding", other), ("printable_8", _printable(8, rng)),
                            ("case_variant", sections[0].swapcase()), ("random", _random(8, rng))):
            out.append(_in_place("ren", label, z, [ByteEdit(lo, lo + 8, name[:8].ljust(8, b"\x00"))],
                                 declared_rename(name)))
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    for op, index in (("rdb", DEBUG_ENTRY), ("rsg", SECURITY_ENTRY)):
        d = directories[index] if len(directories) > index else None
        if d is None or not (d.VirtualAddress or d.Size):
            out.append((op, "no_entry", None, None, None))
            continue
        lo = d.get_file_offset()
        out.append(_in_place(op, "zero_entry", z, [ByteEdit(lo, lo + 8, b"\x00" * 8)],
                             declared_entry(index)))
    return out


################################################################################
# The comparison
################################################################################


def observed_signs(before: np.ndarray, after: np.ndarray) -> dict[int, str]:
    """The features that moved and how: "+", "-", or "?" (a value appeared or disappeared as NaN)."""
    out: dict[int, str] = {}
    nb, na = np.isnan(before), np.isnan(after)
    for i in np.where((before != after) & ~(nb & na))[0]:
        out[int(i)] = "?" if nb[i] or na[i] else ("+" if after[i] > before[i] else "-")
    return out


def _violations(moves: dict[int, str], allowed: list[str]) -> list[tuple[int, str, str]]:
    return [(i, s, allowed[i]) for i, s in moves.items() if (s == "?" and allowed[i] != "+-") or (s != "?" and s not in allowed[i])]


_STATE: dict[str, Any] = {}


def _init_worker(db: Path, directions: Path) -> None:
    warnings.filterwarnings("ignore")
    sums = SumsFeatureExtractor()
    d = pl.read_csv(directions, infer_schema=False).sort(pl.col("index").cast(pl.Int64))
    if d["name"].to_list() != [n.split(":", 1)[1] for n in sums.feature_names]:
        raise RuntimeError(f"{directions} does not list the sums extractor's features in order.")
    _STATE.update(
        reader=SimpleDBReader(SimpleDB(db, check=False)), sums=sums, merged=merge_import_descriptors(PEFeatureExtractor()),
        strict={op: [s or "" for s in d[f"op_{op}"].to_list()] for op in OPS},
        pre={op: [s or "" for s in d[f"op_{op}_pre"].to_list()] for op in OPS},
    )


def _c1(merged: PEFeatureExtractor, table: ItemTable, z: bytes, edits: list[ByteEdit], edited: bytes) -> tuple[str, int]:
    """The C1 engine on a chain of in-place writes or an append: "exact", "mismatch" (with the count), or "flagged"."""
    old, t = z, table
    for e in edits:
        p = predict(t, old, e, merged.recognizers)
        if p.table is None:
            return "flagged", 0
        old, t = p.new, p.table
    modeled = ~np.array([n.startswith("pefilewarnings:") for n in merged.feature_names])
    x = np.asarray(merged.feature_vector(edited))  # type: ignore[no-untyped-call]
    y = np.asarray(p.features(merged.readouts))
    bad = modeled & ~((x == y) | (np.isnan(x) & np.isnan(y)))
    return ("exact", 0) if not bad.any() else ("mismatch", int(bad.sum()))


def _declared(merged: PEFeatureExtractor, declared: Callable[[PEFeatureExtractor], Optional[Prediction]], edited: bytes,
              modeled: np.ndarray, x: np.ndarray) -> tuple[str, list[str], float]:
    """
    The declared prediction of an item-stated instance against re-extraction (`x`, the merged extractor's features of
    the edited file): "exact", "mismatch" (with the features), "flagged", or "error"; and the prediction's seconds.
    """
    t0 = time.perf_counter()
    try:
        p = declared(merged)
    except Exception as e:  # noqa: BLE001
        return "error", [f"{type(e).__name__}: {e}"[:300]], time.perf_counter() - t0
    if p is None or p.new != edited:
        return "error", ["the declaration wrote another file"], time.perf_counter() - t0
    if p.table is None:
        return "flagged", [p.reason], time.perf_counter() - t0
    y = np.asarray(p.features(merged.readouts))
    seconds = time.perf_counter() - t0
    bad = modeled & ~((x == y) | (np.isnan(x) & np.isnan(y)))
    names = merged.feature_names
    return ("exact", [], seconds) if not bad.any() else ("mismatch", [f"{names[i]} {x[i]} != {y[i]}" for i in np.where(bad)[0]], seconds)


def _check_file(task: tuple[str, int]) -> list[dict[str, Any]]:
    """Every instance on one file."""
    name, seed = task
    sums: SumsFeatureExtractor = _STATE["sums"]
    merged: PEFeatureExtractor = _STATE["merged"]
    z = _STATE["reader"].get(name).data
    pe = _parse(z)
    if pe is None:
        return []
    names = sums.feature_names
    table = merged.item_table(z)
    pre = passes_precondition(merged, z)
    before = np.asarray(sums.feature_vector(z))  # type: ignore[no-untyped-call]
    rows: list[dict[str, Any]] = []
    modeled = ~np.array([n.startswith("pefilewarnings:") for n in merged.feature_names])
    for op, label, edited, edits, declared in instances(z, pe, table, np.random.default_rng([seed, int(name[:8], 16)])):
        row: dict[str, Any] = {"name": name, "op": op, "instance": label, "applies": edited is not None,
                               "precondition": pre, "parses": False, "changed": 0, "violations_strict": [],
                               "violations_pre": [], "c1": "", "c1_mismatches": 0, "precondition_after": None,
                               "declared": "", "declared_detail": [], "declared_seconds": 0.0, "extract_seconds": 0.0,
                               "seconds": 0.0}
        if edited is not None:
            t0 = time.perf_counter()
            row["parses"] = _parse(edited) is not None
            # P1, closure: the edited file passes the precondition whenever the original did.
            row["precondition_after"] = passes_precondition(merged, edited) if pre else None
            moves = observed_signs(before, np.asarray(sums.feature_vector(edited)))  # type: ignore[no-untyped-call]
            row["changed"] = len(moves)
            row["moves"] = [f"{names[i]} {s}" for i, s in sorted(moves.items())]
            row["violations_strict"] = [f"{names[i]} {s} (allowed '{a}')" for i, s, a in _violations(moves, _STATE["strict"][op])]
            if pre:
                row["violations_pre"] = [f"{names[i]} {s} (allowed '{a}')" for i, s, a in _violations(moves, _STATE["pre"][op])]
            if edits is not None:
                row["c1"], row["c1_mismatches"] = _c1(merged, table, z, edits, edited)
            if declared is not None:
                # Table 5: the item-stated operations, declared, against re-extraction of the file our own edit wrote.
                t1 = time.perf_counter()
                x = np.asarray(merged.feature_vector(edited))  # type: ignore[no-untyped-call]
                row["extract_seconds"] = time.perf_counter() - t1
                row["declared"], row["declared_detail"], row["declared_seconds"] = _declared(merged, declared, edited, modeled, x)
            row["seconds"] = time.perf_counter() - t0
        rows.append(row)
    return rows


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--files", type=Path, default=Path("artifacts/experiments/e1/seed-0/zeros/files.parquet"))
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--directions", type=Path,
                        default=Path("artifacts/experiments/a_directions_derived_sums_pilot/directions_sums.csv"))
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--num_files", type=int, default=0, help="Only the first N files (0: all).")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")
    files = sorted(df["name"].to_list())
    if args.num_files:
        files = files[: args.num_files]
    print(f"{len(files)} files, {args.workers} workers, directions {args.directions}", flush=True)

    rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    with get_context("forkserver").Pool(args.workers, initializer=_init_worker, initargs=(args.db, args.directions)) as pool:
        tasks = [(f, args.seed) for f in files]
        for r in tqdm(pool.imap_unordered(_check_file, tasks), total=len(files), mininterval=30, file=sys.stdout):
            rows += r
            for row in r:
                for v in row["violations_strict"][:3] + row["violations_pre"][:3]:
                    print(f"{row['op']}/{row['instance']} {row['name'][:12]}: {v}", flush=True)
    rows.sort(key=lambda r: (OPS.index(r["op"]), r["name"], r["instance"]))

    report: dict[str, Any] = {"files": len(files), "seconds": time.perf_counter() - t0}
    for op in OPS:
        mine = [r for r in rows if r["op"] == op]
        done = [r for r in mine if r["applies"]]
        cells = Counter(m for r in done for m in r.get("moves", []))
        report[op] = {
            "edits": len(mine),
            "applied": len(done),
            "not_parsing": sum(not r["parses"] for r in done),
            "edits_violating_strict": sum(bool(r["violations_strict"]) for r in done),
            "edits_violating_pre": sum(bool(r["violations_pre"]) for r in done),
            "violations_strict": Counter(v.split(" (")[0] for r in done for v in r["violations_strict"]).most_common(),
            "violations_pre": Counter(v.split(" (")[0] for r in done for v in r["violations_pre"]).most_common(),
            "instances": Counter(r["instance"] for r in done).most_common(),
            "c1": Counter(r["c1"] for r in done if r["c1"]).most_common(),
            "declared": Counter(r["declared"] for r in done if r["declared"]).most_common(),
            "declared_mismatches": Counter(d.split(" ")[0] for r in done if r["declared"] == "mismatch" for d in r["declared_detail"]).most_common(),
            "declared_flags": Counter(r["declared_detail"][0] for r in done if r["declared"] in ("flagged", "error")).most_common(),
            "declared_median_ms": float(np.median([1e3 * r["declared_seconds"] for r in done if r["declared"] == "exact"] or [0.0])),
            "extract_median_ms": float(np.median([1e3 * r["extract_seconds"] for r in done if r["declared"]] or [0.0])),
            "applied_on_passing": sum(bool(r["precondition"]) for r in done),
            "leaving_population": sum(r["precondition_after"] is False for r in done),
            "leaving_population_instances": Counter(r["instance"] for r in done if r["precondition_after"] is False).most_common(),
            "observed_cells": len(cells),
        }
    report["pass"] = all(report[op]["edits_violating_strict"] == 0 and report[op]["edits_violating_pre"] == 0 for op in OPS)
    report["closed"] = all(report[op]["leaving_population"] == 0 for op in OPS)
    # Table 5: no declared prediction of an item-stated operation is wrong (flagged allowed, reported).
    report["exact"] = all(dict(report[op]["declared"]).get("mismatch", 0) == 0 and dict(report[op]["declared"]).get("error", 0) == 0 for op in OPS)

    args.outdir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows, infer_schema_length=None).write_parquet(args.outdir / "edits.parquet")
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({op: {k: report[op][k] for k in ("applied", "not_parsing", "edits_violating_strict", "edits_violating_pre", "c1",
                                               "applied_on_passing", "leaving_population", "declared", "declared_mismatches",
                                               "declared_flags")} for op in OPS}, indent=1))
    print(f"pass: {report['pass']}, closed: {report['closed']}, exact: {report['exact']}")


if __name__ == "__main__":
    main()
