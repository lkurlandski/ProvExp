"""
Discover which PE header fields ablation must not touch (see provexp.featuresets.ember2024.ablation), and check a
choice of protected fields.

Modes:
    sweep   On a sample of files, zero each header field alone and record whether pefile (called as the feature
            extractor calls it) still parses the file and whether the layout changes.
    check   With a set of protected fields, zero (a) every unprotected header byte, (b) every unprotected byte with
            zeros, and (c) every unprotected byte with random bytes, all at once, and record whether the file still
            parses with the same layout and whether feature extraction succeeds with is_pe = 1. (b) is the starting
            point of the insertion curves.

Outputs, in `{outdir}/`:
    sweep.parquet / check.parquet       one row per (file, field) or (file, ablation)
    sweep.json / check.json             a summary per field key or ablation

Usage:
    python scripts/discover_protected_fields.py sweep --split tr --num_samples 2000 --num_workers 16
    python scripts/discover_protected_fields.py check --split ts --fields fields.json --num_workers 16
"""

from argparse import ArgumentParser
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import sys
import time
from types import FrameType
from typing import Any
from typing import Optional
import warnings

import numpy as np
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.ablation import PROTECTED_FIELDS
from provexp.featuresets.ember2024.ablation import HeaderFill
from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.

_EXTRACTOR: Optional[PEFeatureExtractor] = None


class Timeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise Timeout()


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


################################################################################
# Per File
################################################################################


def sweep_file(data: bytes) -> list[dict[str, Any]]:
    """Zero each header field alone and parse the result."""
    original = parse(data)
    if original.status != "ok":
        return [{"key": "", "lo": -1, "hi": -1, "noop": True, "status": f"original_{original.status}", "layout_changed": False}]
    assert original.pe is not None
    records = []
    for field in header_fields(original.pe):
        lo, hi = max(field.lo, 0), min(field.hi, len(data))
        noop = hi <= lo or not any(data[lo:hi])
        if noop:
            records.append({"key": field.key, "lo": lo, "hi": hi, "noop": True, "status": "ok", "layout_changed": False})
            continue
        ablated = data[:lo] + bytes(hi - lo) + data[hi:]
        result = parse(ablated)
        records.append({
            "key": field.key, "lo": lo, "hi": hi, "noop": False, "status": result.status,
            "layout_changed": result.status == "ok" and result.layout != original.layout,
        })
    return records


def check_file(data: bytes, fields: frozenset[str], per_file: bool, header_fill: HeaderFill, seed: int) -> list[dict[str, Any]]:
    """
    Protect a file as an experiment does (`protect`), then ablate every unprotected header byte, and every unprotected
    byte (zeros, random), all at once, and check each result as an experiment does (`verify`).
    """
    assert _EXTRACTOR is not None
    original = parse(data)
    if original.status != "ok" or original.pe is None:
        return [{"ablation": "", "status": f"original_{original.status}"}]
    try:
        protection = protect(data, fields, per_file=per_file, header=header_fill)
    except ValueError as err:
        return [{"ablation": "", "status": "unprotectable", "problem": str(err)[:300]}]
    m = len(data)
    header, protected, values = protection.header, protection.mask, protection.header_values
    buffer = np.frombuffer(data, dtype=np.uint8)
    noise = np.random.default_rng(seed).integers(0, 256, size=m, dtype=np.uint8)
    ablations = {
        "header_only": np.where(header & ~protected, values, buffer),
        "all_zeros": np.where(protected, buffer, np.where(header, values, 0)),
        # Header bytes always take their header values, never random ones (see Protection).
        "all_random": np.where(protected, buffer, np.where(header, values, noise)),
    }
    base = {
        "protected_bytes": int(protection.mask.sum()),
        "file_fields": ",".join(sorted(protection.file_fields)),
    }
    records = []
    for name, ablated in ablations.items():
        z = ablated.astype(np.uint8).tobytes()
        is_pe: Optional[float] = None
        try:
            is_pe = float(_EXTRACTOR.feature_vector(z)[IS_PE])  # type: ignore[no-untyped-call]
            problem = verify(protection, data, z, is_pe)
        except Exception as err:
            problem = f"extraction failed: {type(err).__name__}: {err}"[:300]
        records.append(base | {"ablation": name, "status": "ok" if problem is None else "broken", "problem": problem or ""})
    return records


def process_shard(mode: str, shard: int, samples: list[dict[str, Any]], dbdir: Path, fields: frozenset[str], per_file: bool, header_fill: HeaderFill, timeout: int) -> list[dict[str, Any]]:
    wanted = {s["position"]: s for s in samples}
    records: list[dict[str, Any]] = []
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        meta = wanted[position]
        base = {"name": sample.name, "label": meta["label"], "size": len(sample.data)}
        signal.alarm(timeout)
        try:
            rows = sweep_file(sample.data) if mode == "sweep" else check_file(sample.data, fields, per_file, header_fill, meta["row"])
            records.extend(base | {"error": ""} | r for r in rows)
        except Timeout:
            records.append(base | {"error": f"timeout after {timeout} seconds"})
        except Exception as err:
            records.append(base | {"error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    return records


def _star(task: tuple[Any, ...]) -> list[dict[str, Any]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def summarize(mode: str, table: pl.DataFrame) -> dict[str, Any]:
    ok = table.filter(pl.col("error") == "")
    if mode == "sweep":
        fields = ok.filter(pl.col("key") != "")
        per_key = (
            fields.group_by("key")
            .agg(
                pl.col("name").n_unique().alias("files"),
                (~pl.col("noop")).sum().alias("ablated"),
                (pl.col("status") == "not_pe").sum().alias("not_pe"),
                (pl.col("status") == "crash").sum().alias("crash"),
                pl.col("layout_changed").sum().alias("layout_changed"),
            )
            .with_columns(((pl.col("not_pe") + pl.col("crash") + pl.col("layout_changed")) / pl.col("ablated").clip(1)).alias("break_rate"))
            .sort("break_rate", "key", descending=[True, False])
        )
        return {
            "files": ok["name"].n_unique(),
            "not_pe_originally": int(ok.filter(pl.col("status").str.starts_with("original_"))["name"].n_unique()),
            "errors": int((table["error"] != "").sum()),
            "fields": per_key.to_dicts(),
        }
    checks = ok.filter(pl.col("ablation") != "")
    files = ok.unique("name")
    per_ablation = (
        checks.group_by("ablation")
        .agg(pl.len().alias("files"), (pl.col("status") != "ok").sum().alias("broken"), pl.col("protected_bytes").median().alias("median_protected_bytes"))
        .sort("ablation")
    )
    problems = checks.filter(pl.col("status") != "ok").group_by("ablation", "problem").len().sort("len", descending=True)
    file_fields = checks.filter(pl.col("file_fields") != "").unique("name")["file_fields"].str.split(",").explode().value_counts(sort=True)
    return {
        "files": files.height,
        "not_pe_originally": int(ok.filter(pl.col("status").str.starts_with("original_"))["name"].n_unique()),
        "unprotectable": ok.filter(pl.col("status") == "unprotectable").select("name", "problem").to_dicts(),
        "errors": int((table["error"] != "").sum()),
        "files_with_file_specific_fields": int(checks.filter(pl.col("file_fields") != "")["name"].n_unique()),
        "file_specific_fields": file_fields.to_dicts(),
        "ablations": per_ablation.to_dicts(),
        "problems": problems.head(20).to_dicts(),
    }


def main() -> None:
    parser = ArgumentParser(description="Discover or check the protected PE header fields for ablation.")
    parser.add_argument("mode", choices=["sweep", "check"])
    parser.add_argument("--split", type=str, default="tr")
    parser.add_argument("--num_samples", type=int, default=2000, help="Files per split, balanced by label (ignored with --explanation_set).")
    parser.add_argument("--explanation_set", action="store_true", help="Use the explanation set (test split) instead of a sample.")
    parser.add_argument("--fields", type=Path, default=None, help="A JSON list of protected field keys (check mode); default PROTECTED_FIELDS.")
    parser.add_argument("--no_per_file", action="store_true", help="Check mode: protect only the given fields, not the fields that break each file.")
    parser.add_argument("--header", type=str, choices=["zeros", "typical"], default="zeros", help="Check mode: how ablation fills header fields.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA)
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "reports" / "protected_fields")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    if args.explanation_set:
        split = "ts"
        samples = pl.read_parquet(ROOT / "artifacts" / "explanation_set" / "ts.parquet").select("row", "name", "label", "shard", "position")
    else:
        split = args.split
        meta = pl.read_parquet(args.features / split / "meta.parquet").filter(pl.col("status") == "ok")
        per_label = args.num_samples // 2
        samples = pl.concat([meta.filter(pl.col("label") == lab).sample(per_label, seed=args.seed) for lab in (0, 1)])
        samples = samples.select("row", "name", "label", "shard", "position")
    fields = frozenset(json.loads(args.fields.read_text())) if args.fields is not None else PROTECTED_FIELDS

    tasks = [
        (args.mode, int(shard), group.to_dicts(), args.db / split, fields, not args.no_per_file, args.header, args.timeout)
        for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True)
    ]
    print(f"{args.mode}: {samples.height} files from {split} in {len(tasks)} shards.", flush=True)
    t_0 = time.time()
    records: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for recs in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks)):
            records.extend(recs)

    args.outdir.mkdir(parents=True, exist_ok=True)
    tag = f"{args.mode}-{'explanation_set' if args.explanation_set else split}" + ("-typical-header" if args.mode == "check" and args.header == "typical" else "")
    table = pl.DataFrame(records, infer_schema_length=None)
    table.write_parquet(args.outdir / f"{tag}.parquet")
    summary = summarize(args.mode, table) | {"split": split, "protected_fields": sorted(fields), "minutes": (time.time() - t_0) / 60}
    (args.outdir / f"{tag}.json").write_text(json.dumps(summary, indent=2))
    shown = summary | ({"fields": summary["fields"][:25]} if args.mode == "sweep" else {})
    print(json.dumps(shown, indent=2), flush=True)
    print(f"Wrote {(args.outdir / tag).as_posix()}.*", flush=True)


if __name__ == "__main__":
    main()
