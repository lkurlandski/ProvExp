"""
Compare two output trees: the old code's outputs of run/146_refactor_baseline.sh and the same computations run
through pipeline/ (pipeline/setup/identity_check.sh), or two runs of either.

Every file under the first tree must exist under the second and be byte-identical. Where the bytes differ, JSON and
parquet files are compared by content with timing fields set aside (keys or columns whose name contains one of
TIMING); the fields set aside are listed, so nothing is ignored silently. Logs and the MAB work directory are skipped. `--map old=new` maps a path prefix of the first tree to the second's (the stages' layout), `--rename
old=new` a detector name (whole string values, keys and path components only, so model paths containing the old
name stay as they are).

Usage:
    python pipeline/setup/compare_outputs.py artifacts/refactor-baseline/old artifacts/refactor-baseline/old-repeat
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


RENAME: dict[str, str] = {}


def strip(obj: Any, dropped: set[str], path: str = "") -> Any:
    """`obj` without timing keys (recorded in `dropped`), names renamed."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if timing(str(k)):
                dropped.add(f"{path}/{k}")
            else:
                out[RENAME.get(k, k)] = strip(v, dropped, f"{path}/{k}")
        return out
    if isinstance(obj, list):
        return [strip(v, dropped, path) for v in obj]
    if isinstance(obj, str):
        return RENAME.get(obj, obj)
    return obj


def renamed(df: pl.DataFrame) -> pl.DataFrame:
    """`df` with names renamed in its string columns."""
    if not RENAME:
        return df
    return df.with_columns(pl.col(c).replace(RENAME) for c, t in df.schema.items() if t == pl.String)


def compare(a: Path, b: Path) -> tuple[str, str]:
    """('same' | 'same-content' | 'DIFFERENT', detail)."""
    if a.read_bytes() == b.read_bytes():
        return "same", ""
    if a.suffix not in (".json", ".parquet", ".npy") and RENAME:
        text_a = a.read_bytes()
        for old, new in RENAME.items():
            text_a = text_a.replace(old.encode(), new.encode())
        if text_a == b.read_bytes():
            return "same-content", f"after renaming {RENAME}"
    if a.suffix == ".json":
        da: set[str] = set()
        db: set[str] = set()
        ja, jb = strip(json.loads(a.read_text()), da), strip(json.loads(b.read_text()), db)
        if ja == jb:
            return "same-content", f"set aside: {sorted(da | db)}"
        return "DIFFERENT", "JSON content differs"
    if a.suffix == ".parquet":
        fa, fb = renamed(pl.read_parquet(a)), pl.read_parquet(b)
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
    parser.add_argument("--map", nargs="*", default=[], help="old_prefix=new_prefix (relative paths)")
    parser.add_argument("--rename", nargs="*", default=[], help="old_name=new_name")
    args = parser.parse_args()
    RENAME.update(dict(r.split("=", 1) for r in args.rename))
    maps = [m.split("=", 1) for m in args.map]

    def mapped(rel: Path) -> Path:
        rel = Path(*[RENAME.get(part, part) for part in rel.parts])
        for old, new in maps:
            if rel.as_posix() == old or rel.as_posix().startswith(old + "/"):
                return Path(new + rel.as_posix()[len(old):])
        return rel

    files = sorted(p for p in args.first.rglob("*") if p.is_file()
                   and not any(part in SKIP_DIRS for part in p.relative_to(args.first).parts))
    others = {p.relative_to(args.second) for p in args.second.rglob("*") if p.is_file()
              and not any(part in SKIP_DIRS for part in p.relative_to(args.second).parts)}
    bad = 0
    for p in files:
        rel = p.relative_to(args.first)
        q = args.second / mapped(rel)
        if not q.exists():
            print(f"MISSING    {rel}")
            bad += 1
            continue
        verdict, detail = compare(p, q)
        bad += verdict == "DIFFERENT"
        if verdict != "same":
            print(f"{verdict:<12} {rel}  {detail}")
    extra = sorted(others - {mapped(p.relative_to(args.first)) for p in files})
    for rel in extra:
        print(f"EXTRA      {rel}")
    print(f"{len(files)} files compared; {bad} different or missing; {len(extra)} extra.")
    raise SystemExit(1 if bad or extra else 0)


if __name__ == "__main__":
    main()
