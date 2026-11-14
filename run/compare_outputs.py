"""
Compare two output trees of run/146_refactor_baseline.sh (e.g., the old code's and the reorganized code's).

Every file under the first tree must exist under the second and be byte-identical. Where the bytes differ, JSON and
parquet files are compared by content with timing fields set aside (keys or columns whose name contains one of
TIMING); the fields set aside are listed, so nothing is ignored silently. Logs and the MAB work directory are skipped.

Usage:
    python run/compare_outputs.py artifacts/refactor-baseline/old artifacts/refactor-baseline/new
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

# Timing fields, and the commit a manifest records (expected to differ between code versions).
TIMING = ("time", "seconds", "_ms", "elapsed", "duration", "created", "date", "wall", "git_commit")
SKIP_DIRS = ("logs", "work")


def timing(key: str) -> bool:
    """Whether a key or column names a timing field."""
    return any(t in key.lower() for t in TIMING)


def strip(obj: Any, dropped: set[str], path: str = "") -> Any:
    """`obj` without timing keys (recorded in `dropped`)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if timing(str(k)):
                dropped.add(f"{path}/{k}")
            else:
                out[k] = strip(v, dropped, f"{path}/{k}")
        return out
    if isinstance(obj, list):
        return [strip(v, dropped, path) for v in obj]
    return obj


def compare(a: Path, b: Path) -> tuple[str, str]:
    """('same' | 'same-content' | 'DIFFERENT', detail)."""
    if a.read_bytes() == b.read_bytes():
        return "same", ""
    if a.suffix == ".json":
        da: set[str] = set()
        db: set[str] = set()
        ja, jb = strip(json.loads(a.read_text()), da), strip(json.loads(b.read_text()), db)
        if ja == jb:
            return "same-content", f"set aside: {sorted(da | db)}"
        return "DIFFERENT", "JSON content differs"
    if a.suffix == ".parquet":
        fa, fb = pl.read_parquet(a), pl.read_parquet(b)
        cols = [c for c in fa.columns if not timing(c)]
        aside = sorted(set(fa.columns) - set(cols))
        if fa.columns == fb.columns and fa.select(cols).equals(fb.select(cols), null_equal=True):
            return "same-content", f"set aside: {aside}"
        return "DIFFERENT", "parquet content differs"
    if a.suffix == ".npy":
        if np.array_equal(np.load(a), np.load(b), equal_nan=True):
            return "same-content", "arrays equal, bytes differ"
        return "DIFFERENT", "arrays differ"
    return "DIFFERENT", "bytes differ"


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()
    files = sorted(p for p in args.first.rglob("*") if p.is_file()
                   and not any(part in SKIP_DIRS for part in p.relative_to(args.first).parts))
    others = {p.relative_to(args.second) for p in args.second.rglob("*") if p.is_file()
              and not any(part in SKIP_DIRS for part in p.relative_to(args.second).parts)}
    bad = 0
    for p in files:
        rel = p.relative_to(args.first)
        q = args.second / rel
        if not q.exists():
            print(f"MISSING    {rel}")
            bad += 1
            continue
        verdict, detail = compare(p, q)
        bad += verdict == "DIFFERENT"
        if verdict != "same":
            print(f"{verdict:<12} {rel}  {detail}")
    extra = sorted(others - {p.relative_to(args.first) for p in files})
    for rel in extra:
        print(f"EXTRA      {rel}")
    print(f"{len(files)} files compared; {bad} different or missing; {len(extra)} extra.")
    raise SystemExit(1 if bad or extra else 0)


if __name__ == "__main__":
    main()
