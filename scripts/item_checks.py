"""
Mechanical checks of the item layer (docs/item-layer-design.md, "Validation and go/no-go checks").

    exact   G1 and G2 (G1 only with --no_g2). G1: the readouts over the recorded item table reproduce the extractor's feature vector exactly
            (float32, bit for bit) for every modeled feature (all but pefilewarnings), with the import descriptors
            merged (the variant the experiments use) and, for the imports group, also thrember's original. G2: the
            items spread over their elements reproduce today's provenance (the raw contributions, in canonical form).
            With --sums, also G1 for `SumsFeatureExtractor` (derivation step 8): every modeled feature, including the
            four re-encoded groups, read through its readouts over the sums extractor's item table.

    locating
            G5 (assumption A1). Flips bytes (XOR 0xFF) and re-parses. Every item that appears, disappears, or moves
            (its kind or member ranges change) must have the flipped byte among its locating ranges (in the table it
            belongs to), and every item whose contributions or attributes change must have it among its member or
            locating ranges. Only the items pefile parses are compared; items recognized from content (bytes,
            windows, strings) are re-recognized locally (G6). With --region header (the default), every byte of the
            header region, up to --max_bytes per file. With --region directories, the bytes past the header region
            that the parse reads per structure: up to --per_target bytes drawn from each data directory's data and
            from the member and locating ranges of each item kind. This checks that locating ranges can be recorded
            per structure (a flip in one directory's data changes no item located elsewhere).

    margins
            G6 (assumption A3). Random in-place writes (offset uniform over the file, 1-64 bytes, random or printable
            content), predicted by the C1 engine (provexp.reach) and compared with re-extraction: every prediction
            must be bit-exact; writes the engine flags (to locating ranges, or items without a local recognizer) are
            counted by reason.

Writes `files.parquet` (one row per file; `failures.parquet` for G5, `writes.parquet` for G6) and `report.json` (the totals and the verdict)
to --outdir.
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
from functools import partial
import json
from multiprocessing import Pool
from pathlib import Path
import time
from typing import Any
import warnings

import numpy as np
import pefile
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.features import ImportsInfo
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import rva_ranges
from provexp.featuresets.ember2024.sums import SUMS_GROUPS
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import evaluate
from provexp.items import project
from provexp.reach import ByteEdit
from provexp.reach import predict
from provexp.data.paths import EMBER2024_DATA

warnings.filterwarnings("ignore", category=SyntaxWarning)

ROOT = Path(__file__).resolve().parent.parent

################################################################################
# Checks
################################################################################

_READER: SimpleDBReader | None = None
_MERGED = merge_import_descriptors(PEFeatureExtractor())
_IMPORTS = ImportsInfo()  # type: ignore[no-untyped-call]
_SUMS = SumsFeatureExtractor()


def _init(db: str) -> None:
    global _READER
    _READER = SimpleDBReader(SimpleDB(Path(db), check=False))


def _parse(bytez: bytes) -> pefile.PE | None:
    """Parse as the extractor does."""
    try:
        return pefile.PE(data=bytez)
    except (pefile.PEFormatError, AttributeError):
        return None


def _equal(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Elementwise bit-exact equality of float32 vectors, with NaN equal to NaN."""
    out: np.ndarray = (x == y) | (np.isnan(x) & np.isnan(y))
    return out


def _g1(extractor: PEFeatureExtractor, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """G1: the modeled features (all but pefilewarnings) where the readouts' values `y` differ from the extractor's `x`."""
    modeled = np.array([not np.isnan(v) or not np.isnan(x[i]) for i, v in enumerate(y)])
    modeled &= ~np.array([n.startswith("pefilewarnings:") for n in extractor.feature_names])
    out: np.ndarray = np.where(modeled & ~_equal(x, y))[0]
    return out


def check_exact(name: str, g2: bool = True, sums: bool = False) -> dict[str, Any]:
    """G1 and (if `g2`) G2 on one file; with `sums`, also G1 for the sums extractor."""
    assert _READER is not None
    bytez = _READER.get(name).data
    t0 = time.perf_counter()
    if g2:
        x, prov = _MERGED.feature_vector_with_provenance(bytez)
    else:
        x = _MERGED.feature_vector(bytez)  # type: ignore[no-untyped-call]
    t1 = time.perf_counter()
    table = _MERGED.item_table(bytez)
    readouts = _MERGED.readouts
    y = evaluate(table, readouts)
    t2 = time.perf_counter()

    # G1: every modeled feature bit for bit.
    mismatch = _g1(_MERGED, x, y)

    # G1 for thrember's original imports (the descriptors of a DLL overwrite each other).
    pe = _parse(bytez)
    xi = _IMPORTS.feature_vector(bytez, pe).astype(np.float32)
    yi = evaluate(_IMPORTS.items(bytez, pe), _IMPORTS.readouts)
    mismatch_imports = int((~_equal(xi, yi)).sum())

    # G2: the projection equals the provenance's raw contributions, in canonical form.
    same_support, max_diff, num_pieces = True, 0.0, [0, 0]
    if g2:
        p, q = prov.contributions.pieces(), project(table, readouts).pieces()
        same_support = p.col.shape == q.col.shape and all(np.array_equal(a, b) for a, b in zip(p[:3], q[:3]))
        max_diff = float(np.max(np.abs(p.val - q.val) / np.maximum(np.abs(p.val), 1e-300))) if same_support and p.val.size else 0.0
        num_pieces = [int(p.col.size), int(q.col.size)]
    t3 = time.perf_counter()

    # G1 for the sums extractor (its thrember groups again, and the re-encoded ones).
    sums_mismatch: list[str] = []
    if sums:
        xs = _SUMS.feature_vector(bytez)  # type: ignore[no-untyped-call]
        bad = _g1(_SUMS, xs, evaluate(_SUMS.item_table(bytez), _SUMS.readouts))
        sums_mismatch = [_SUMS.feature_names[i] for i in bad]
    t4 = time.perf_counter()

    names = _MERGED.feature_names
    return {
        "name": name,
        "size": len(bytez),
        "num_items": len(table),
        "g1_mismatches": int(mismatch.size),
        "g1_features": [names[i] for i in mismatch[:20]],
        "g1_imports_original_mismatches": mismatch_imports,
        "g2_checked": g2,
        "g2_equal": bool(same_support and max_diff <= 1e-9),
        "g2_same_support": bool(same_support),
        "g2_max_rel_diff": max_diff,
        "g2_pieces": num_pieces,
        "seconds_extract": t1 - t0,
        "seconds_items": t2 - t1,
        "seconds_total": t3 - t0,
        "g1_sums_checked": sums,
        "g1_sums_mismatches": len(sums_mismatch),
        "g1_sums_reencoded_mismatches": sum(n.split(":")[0] in SUMS_GROUPS for n in sums_mismatch),
        "g1_sums_features": sums_mismatch[:20],
        "seconds_sums": t4 - t3,
    }


# The feature types whose items pefile parses, and the kinds recognized from content instead.
_PE_GROUPS = [fe for fe in _MERGED.features if fe.name not in ("histogram", "byteentropy", "strings", "pefilewarnings")]
_CONTENT_KINDS = ("bytes", "window", "string")


def _pe_items(bytez: bytes) -> dict[tuple[Any, ...], Item]:
    """The parsed items of a file, keyed by (kind, members, field, occurrence): equal keys mean the same location."""
    pe = _parse(bytez)
    table = ItemTable.concatenate([fe.items(bytez, pe) for fe in _PE_GROUPS])
    out: dict[tuple[Any, ...], Item] = {}
    for item in table.items:
        if item.kind in _CONTENT_KINDS:
            continue
        key: tuple[Any, ...] = (item.kind, item.members, item.attrs.get("field"))
        occurrence = 0
        while (*key, occurrence) in out:
            occurrence += 1
        out[(*key, occurrence)] = item
    return out


def _values(item: Item) -> tuple[Any, ...]:
    """What an item contributes and the attributes readouts read."""
    terms = tuple((t.op, t.family, t.index, t.amount, t.key) for t in item.terms)
    attrs = tuple(sorted((k, repr(v)) for k, v in item.attrs.items()))
    return terms, attrs


def _within(offset: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(lo <= offset < hi for lo, hi in ranges)


def check_locating(task: tuple[str, tuple[int, ...]]) -> dict[str, Any]:
    """G5 on the given byte offsets of one file."""
    assert _READER is not None
    name, offsets = task
    bytez = _READER.get(name).data
    before = _pe_items(bytez)
    failures: list[dict[str, Any]] = []
    structural = 0
    for offset in offsets:
        edited = bytearray(bytez)
        edited[offset] ^= 0xFF
        after = _pe_items(bytes(edited))
        changed = False
        for side, items, other in [("removed", before, after), ("added", after, before)]:
            for key, item in items.items():
                if key in other:
                    continue
                changed = True
                if not _within(offset, item.locating):
                    failures.append({"name": name, "offset": offset, "check": side, "kind": item.kind, "field": str(item.attrs.get("field")), "members": str(item.members[:3])})
        for key, item in before.items():
            if key in after and _values(item) != _values(after[key]):
                if not _within(offset, item.members + item.locating):
                    failures.append({"name": name, "offset": offset, "check": "value", "kind": item.kind, "field": str(item.attrs.get("field")), "members": str(item.members[:3])})
        structural += changed
    return {"name": name, "flips": len(offsets), "structural": structural, "failures": failures}


def _sample(ranges: list[tuple[int, int]], k: int, rng: np.random.Generator) -> list[int]:
    """Up to k distinct offsets drawn uniformly from the union of the ranges."""
    covered = sorted({o for lo, hi in ranges for o in range(lo, hi)}) if sum(hi - lo for lo, hi in ranges) <= 1 << 22 else []
    if not covered:
        return []
    return [covered[i] for i in rng.choice(len(covered), size=min(k, len(covered)), replace=False).tolist()]


def directory_offsets(bytez: bytes, pe: pefile.PE, per_target: int, rng: np.random.Generator) -> list[int]:
    """
    Offsets past the header region that the parse reads: up to `per_target` from each data directory's data (but
    security, which pefile does not parse) and from the member and locating ranges of each parsed item kind.
    """
    n = len(bytez)
    start = min(int(pe.OPTIONAL_HEADER.SizeOfHeaders), n)

    def inside(ranges: tuple[tuple[int, int], ...]) -> list[tuple[int, int]]:
        return [(max(lo, start), min(hi, n)) for lo, hi in ranges if min(hi, n) > max(lo, start)]

    targets: list[list[tuple[int, int]]] = []
    for i, d in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
        if i != 4 and d.VirtualAddress and d.Size:
            targets.append(inside(rva_ranges(pe, d.VirtualAddress, d.Size)))
    by_kind: dict[str, list[tuple[int, int]]] = {}
    for item in _pe_items(bytez).values():
        by_kind.setdefault(item.kind, []).extend(inside(item.members + item.locating))
    targets += [by_kind[k] for k in sorted(by_kind)]
    return sorted({o for t in targets for o in _sample(t, per_target, rng)})


def main_locating(args: Any) -> None:
    """G5 over the files, in chunks of header bytes."""
    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")
    rng = np.random.default_rng(args.seed)
    names = sorted(df["name"].to_list())
    _init(str(args.db))
    assert _READER is not None
    tasks: list[tuple[str, tuple[int, ...]]] = []
    chosen: list[str] = []
    for name in rng.permutation(names).tolist():
        if len(chosen) == args.num_files:
            break
        bytez = _READER.get(name).data
        pe = _parse(bytez)
        if pe is None:
            continue
        chosen.append(name)
        if args.region == "header":
            offsets = list(range(min(int(pe.OPTIONAL_HEADER.SizeOfHeaders), len(bytez), args.max_bytes)))
        else:
            offsets = directory_offsets(bytez, pe, args.per_target, np.random.default_rng([args.seed, int(name[:8], 16)]))
        tasks += [(name, tuple(offsets[i:i + 64])) for i in range(0, len(offsets), 64)]
    print(f"{len(chosen)} files, {len(tasks)} tasks, {sum(len(o) for _, o in tasks)} flips", flush=True)

    t0 = time.perf_counter()
    rows: list[dict[str, Any]] = []
    with Pool(args.workers, initializer=_init, initargs=(str(args.db),)) as pool:
        for i, row in enumerate(pool.imap_unordered(check_locating, tasks, chunksize=1)):
            rows.append(row)
            if (i + 1) % 50 == 0:
                print(f"{i + 1}/{len(tasks)} tasks, {time.perf_counter() - t0:.0f} s", flush=True)

    failures = pl.DataFrame([f for r in rows for f in r["failures"]], schema={"name": pl.String, "offset": pl.Int64, "check": pl.String, "kind": pl.String, "field": pl.String, "members": pl.String})
    files = pl.DataFrame([{k: r[k] for k in ("name", "flips", "structural")} for r in rows]).group_by("name").agg(
        pl.col("flips").sum(), pl.col("structural").sum()
    ).sort("name")
    args.outdir.mkdir(parents=True, exist_ok=True)
    files.write_parquet(args.outdir / "files.parquet")
    failures.write_parquet(args.outdir / "failures.parquet")
    summary = failures.group_by("check", "kind", "field").agg(pl.len().alias("count"), pl.col("offset").unique().sort().head(8).alias("offsets"), pl.col("name").n_unique().alias("files")).sort("count", descending=True)
    report = {
        "files": files.height,
        "flips": int(files["flips"].sum()),
        "flips_structural": int(files["structural"].sum()),
        "failures": failures.height,
        "failures_by_kind": [{k: (v if not isinstance(v, list) else v) for k, v in row.items()} for row in summary.head(40).to_dicts()],
        "wall_seconds": time.perf_counter() - t0,
    }
    report["pass"] = report["failures"] == 0
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


def check_margins(task: tuple[str, int, int]) -> list[dict[str, Any]]:
    """G6 on one file: `num_writes` random in-place writes, seeded by (seed, file)."""
    assert _READER is not None
    name, num_writes, seed = task
    bytez = _READER.get(name).data
    rng = np.random.default_rng([seed, int(name[:8], 16)])
    table = _MERGED.item_table(bytez)
    readouts = _MERGED.readouts
    modeled = ~np.array([n.startswith("pefilewarnings:") for n in _MERGED.feature_names])
    rows = []
    for _ in range(num_writes):
        size = int(rng.integers(1, 65))
        lo = int(rng.integers(0, max(1, len(bytez) - size)))
        hi = min(lo + size, len(bytez))
        printable = bool(rng.integers(0, 2))
        content = rng.integers(0x20, 0x7f, hi - lo, dtype=np.uint8) if printable else rng.integers(0, 256, hi - lo, dtype=np.uint8)
        t0 = time.perf_counter()
        p = predict(table, bytez, ByteEdit(lo, hi, content.tobytes()), _MERGED.recognizers)
        t1 = time.perf_counter()
        row: dict[str, Any] = {"name": name, "lo": lo, "hi": hi, "printable": printable, "flagged": p.table is None,
                               "reason": p.reason.split(":")[0] if p.table is None else "", "flagged_kinds": sorted({i.kind for i in p.flagged}),
                               "mismatches": 0, "features": [], "seconds_predict": t1 - t0, "seconds_extract": float("nan")}
        if p.table is not None:
            x = _MERGED.feature_vector(p.new)  # type: ignore[no-untyped-call]
            row["seconds_extract"] = time.perf_counter() - t1
            bad = np.where(modeled & ~_equal(x, p.features(readouts)))[0]
            row["mismatches"] = int(bad.size)
            row["features"] = [_MERGED.feature_names[i] for i in bad[:10]]
        rows.append(row)
    return rows


def main_margins(args: Any) -> None:
    """G6 over the files."""
    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")
    names = sorted(df["name"].to_list())
    if args.limit > 0:
        names = names[: args.limit]
    t0 = time.perf_counter()
    rows: list[dict[str, Any]] = []
    with Pool(args.workers, initializer=_init, initargs=(str(args.db),)) as pool:
        for out in pool.imap_unordered(check_margins, [(n, args.num_writes, args.seed) for n in names], chunksize=1):
            rows += out
            for r in out:
                if r["mismatches"]:
                    print(f"FAIL {r['name'][:12]} [{r['lo']}, {r['hi']}) printable={r['printable']}: {r['features']}", flush=True)
    writes = pl.DataFrame(rows)
    args.outdir.mkdir(parents=True, exist_ok=True)
    writes.write_parquet(args.outdir / "writes.parquet")
    predicted = writes.filter(~pl.col("flagged"))
    flagged = writes.filter(pl.col("flagged"))
    report = {
        "files": len(names),
        "writes": writes.height,
        "predicted": predicted.height,
        "predicted_exact": int((predicted["mismatches"] == 0).sum()),
        "flagged": flagged.height,
        "flagged_by_reason": dict(sorted(Counter(flagged["reason"].to_list()).items())),
        "flagged_by_kind": dict(Counter(k for ks in flagged["flagged_kinds"].to_list() for k in ks).most_common(12)),
        "mismatching_features": dict(Counter(f for fs in predicted["features"].to_list() for f in fs).most_common(20)),
        "seconds_predict_median": float(np.median(predicted["seconds_predict"].to_numpy())) if predicted.height else 0.0,
        "seconds_extract_median": float(np.median(predicted["seconds_extract"].to_numpy())) if predicted.height else 0.0,
        "wall_seconds": time.perf_counter() - t0,
    }
    report["pass"] = report["predicted_exact"] == report["predicted"]
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("check", choices=["exact", "locating", "margins"])
    parser.add_argument("--files", type=Path, required=True, help="Parquet with a `name` column (and optionally `status`).")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0, help="Only the first N files (0: all).")
    parser.add_argument("--no_g2", action="store_true", help="G1 only (G2 costs a provenance computation per file).")
    parser.add_argument("--sums", action="store_true", help="exact: also G1 for the sums extractor (step 8).")
    parser.add_argument("--num_files", type=int, default=20, help="locating: files drawn from --files (PE files only).")
    parser.add_argument("--max_bytes", type=int, default=1024, help="locating: header bytes flipped per file, at most.")
    parser.add_argument("--region", choices=["header", "directories"], default="header", help="locating: which bytes to flip.")
    parser.add_argument("--per_target", type=int, default=64, help="locating, directories: bytes drawn per directory and per item kind.")
    parser.add_argument("--num_writes", type=int, default=20, help="margins: random writes per file.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.check == "locating":
        main_locating(args)
        return
    if args.check == "margins":
        main_margins(args)
        return

    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")
    names = sorted(df["name"].to_list())
    if args.limit > 0:
        names = names[: args.limit]
    args.outdir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    rows: list[dict[str, Any]] = []
    with Pool(args.workers, initializer=_init, initargs=(str(args.db),)) as pool:
        for i, row in enumerate(pool.imap_unordered(partial(check_exact, g2=not args.no_g2, sums=args.sums), names, chunksize=1)):
            rows.append(row)
            if row["g1_mismatches"] or row["g1_imports_original_mismatches"] or not row["g2_equal"] or row["g1_sums_mismatches"]:
                print(f"FAIL {row['name']}: G1 {row['g1_mismatches']} {row['g1_features'][:5]} imports {row['g1_imports_original_mismatches']} G2 {row['g2_equal']} {row['g2_pieces']} {row['g2_max_rel_diff']:.3g} sums {row['g1_sums_mismatches']} {row['g1_sums_features'][:5]}", flush=True)
            if (i + 1) % 100 == 0:
                print(f"{i + 1}/{len(names)} files, {time.perf_counter() - t0:.0f} s", flush=True)

    out = pl.DataFrame(rows).sort("name")
    out.write_parquet(args.outdir / "files.parquet")
    report = {
        "files": len(rows),
        "g1_files_failed": int((out["g1_mismatches"] > 0).sum()),
        "g1_features_failed": sorted({f for fs in out["g1_features"].to_list() for f in fs}),
        "g1_imports_original_files_failed": int((out["g1_imports_original_mismatches"] > 0).sum()),
        "g1_sums_checked": args.sums,
        "g1_sums_files_failed": int((out["g1_sums_mismatches"] > 0).sum()),
        "g1_sums_reencoded_files_failed": int((out["g1_sums_reencoded_mismatches"] > 0).sum()),
        "g1_sums_features_failed": sorted({f for fs in out["g1_sums_features"].to_list() for f in fs}),
        "seconds_sums": float(out["seconds_sums"].to_numpy().sum()),
        "g2_checked": not args.no_g2,
        "g2_files_failed": int((~out["g2_equal"]).sum()),
        "g2_max_rel_diff": float(out["g2_max_rel_diff"].to_numpy().max()),
        "seconds_items_vs_extract": float(out["seconds_items"].to_numpy().sum() / out["seconds_extract"].to_numpy().sum()),
        "slowest_file_seconds": float(out["seconds_total"].to_numpy().max()),
        "wall_seconds": time.perf_counter() - t0,
    }
    report["pass"] = report["g1_files_failed"] == 0 and report["g1_imports_original_files_failed"] == 0 and report["g2_files_failed"] == 0 and report["g1_sums_files_failed"] == 0
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
