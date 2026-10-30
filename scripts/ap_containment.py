"""
Direction A', step 4's test (docs/direction-A-prime-encoding.md, "The test"): the edit-choice encoding must contain the
real file.

For each pilot file the encoding covers, draw random edits from the catalogue (up to K sections with random names,
flags, and contents, then an append), write each with our own byte-level edits (`scripts/catalogue_checks.py`), and
re-extract. Three checks per edit:
    exact      every feature whose value is fixed by the choice (sizes, counts, buckets, header fields, the ratios of
               those) equals the re-extracted value;
    held       every feature the encoding holds fixed (pefile's warnings, the untouched groups) is unchanged;
    contained  with the choice variables fixed to the edit and every split binary fixed to the re-extracted vector's
               side, the program is feasible: the real file's path through every tree of every detector is one the
               encoding allows (the statement a certificate needs). Splits are the union over the detectors.
A failure is a bug or an assumption to list; failing features are named (bisection over feature groups).

Outputs, in `{outdir}/`:
    edits.parquet    one row per (file, edit): the edit, written or not, the three checks, the failing features
    report.json      totals per check, and per failing feature the number of edits

Usage (smoke on two files, three edits each):
    PYTHONHASHSEED=0 python scripts/ap_containment.py --outdir /tmp/apc --num_files 2 --edits 3 --workers 2
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional

import lightgbm
import numpy as np
from tqdm import tqdm

from provexp.featuresets.ember2024.sums import SUMS_GROUPS
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))
from a1_adaptive import _parse_defenses  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from ap_check0_solver import Ensemble  # noqa: E402
from ap_encoding import FLAGS  # noqa: E402
from ap_encoding import Choice  # noqa: E402
from ap_encoding import Encoding  # noqa: E402
from ap_encoding import NotCovered  # noqa: E402
from ap_encoding import budget  # noqa: E402
from ap_encoding import link_ensemble  # noqa: E402
from ap_encoding import write  # noqa: E402

__all__ = [
    "random_choice",
    "check_edit",
    "main",
]

ROOT = Path(__file__).resolve().parents[1]
# NOTE: the extracted vector is float32; the exact features are compared at that precision.
EXACT_RTOL = 1e-5
WORDS = (b"http://example.com/a", b"C:/Windows/system32", b"window", b"HKCU\\Software", b"kernel32.dll", b"/proc/self",
         b"192.168.0.1", b"GetProcAddress", b"!This program cannot be run in DOS mode")


################################################################################
# Random edits
################################################################################


def _content(rng: np.random.Generator, size: int, donors: list[bytes]) -> bytes:
    """Bytes of one of five kinds: zeros, random, printable text, a slice of a goodware file, or a mix."""
    kind = rng.integers(5)
    if size == 0:
        return b""
    if kind == 0:
        return b"\x00" * size
    if kind == 1:
        return rng.integers(0, 256, size, dtype=np.uint8).tobytes()
    if kind == 2:
        parts: list[bytes] = []
        while sum(map(len, parts)) < size:
            parts.append(WORDS[rng.integers(len(WORDS))] if rng.random() < 0.3 else
                         rng.integers(0x20, 0x7f, int(rng.integers(1, 40)), dtype=np.uint8).tobytes())
            parts.append(bytes([int(rng.choice([0, 0x0a, 0x20]))]))
        return b"".join(parts)[:size]
    if kind == 3:
        d = donors[int(rng.integers(len(donors)))]
        lo = int(rng.integers(0, max(1, len(d) - size)))
        return (d[lo:lo + size] * (size // max(1, len(d[lo:lo + size])) + 1))[:size]
    half = size // 2
    return _content(rng, half, donors) + _content(rng, size - half, donors)


def random_choice(rng: np.random.Generator, k: int, donors: list[bytes]) -> Choice:
    """A random edit: 0..k sections (random names, flags, contents up to 64 KB), then an append up to 128 KB (or none)."""
    sections = []
    for _ in range(int(rng.integers(0, k + 1))):
        size = 0 if rng.random() < 0.1 else int(2 ** rng.uniform(0, 16))
        r = rng.random()
        if r < 0.2:
            name = b""
        elif r < 0.5:
            name = [b".text", b".data", b".rsrc", b".reloc", b"UPX0", b".idata"][int(rng.integers(6))]
        else:
            name = rng.integers(0x21, 0x7f, int(rng.integers(1, 9)), dtype=np.uint8).tobytes()
        characteristics = sum(bit for bit in FLAGS.values() if rng.random() < 0.5)
        sections.append((name, _content(rng, size, donors), characteristics))
    append = _content(rng, int(2 ** rng.uniform(0, 17)), donors) if rng.random() < 0.7 else b""
    return Choice(tuple(sections), append)


################################################################################
# The checks
################################################################################


class _Splits:
    """The union of the detectors' split thresholds (an Ensemble's `thresholds` only)."""

    def __init__(self, ensembles: list[Ensemble]) -> None:
        merged: dict[int, set[float]] = {}
        for ens in ensembles:
            for f, ts in ens.thresholds.items():
                merged.setdefault(f, set()).update(ts.tolist())
        self.thresholds = {f: np.array(sorted(ts)) for f, ts in sorted(merged.items())}


def _contained(make: Any, choice: Choice, edited: bytes, x1: np.ndarray, splits: _Splits, features: Optional[set[int]]) -> bool:
    """Whether the program is feasible with the choice fixed and the splits (of `features`, or all) on x1's sides."""
    enc = make()
    enc.fix(choice, edited)
    sub = _Splits([])
    sub.thresholds = {f: ts for f, ts in splits.thresholds.items() if features is None or f in features}
    link_ensemble(enc, sub, sides=x1)  # type: ignore[arg-type]
    res = enc.program.solve(time_limit=120.0)
    return bool(res.status == 0)


def check_edit(make: Any, extractor: SumsFeatureExtractor, z: bytes, choice: Choice, splits: _Splits,
               names: list[str]) -> dict[str, Any]:
    """The three checks on one edit (see the module docstring)."""
    edited = write(z, choice)
    row: dict[str, Any] = {"sections": len(choice.sections), "append": len(choice.append),
                           "content": sum(len(c) for _, c, _ in choice.sections), "written": edited is not None,
                           "held": [], "held_split": [], "exact": [], "failing": [], "contained": None}
    if edited is None:
        return row
    x1 = np.asarray(extractor.feature_vector(edited), dtype=np.float64)  # type: ignore[no-untyped-call]
    enc = make()
    enc.fix(choice, edited)
    split = set(splits.thresholds)
    # NOTE: the re-encoded sums columns are not encoded (the A' detectors neutralize them; no split reads them).
    held = [f for f in range(x1.size) if f not in enc.values and names[f].split(":")[0] not in SUMS_GROUPS
            and not (x1[f] == enc.x0[f] or np.isnan(x1[f]) and np.isnan(enc.x0[f]))]
    exact = []
    for f in enc.values:
        v = enc.fixed_value(f)
        if v is not None and not np.isclose(v, x1[f], rtol=EXACT_RTOL, atol=1e-6):
            exact.append(f)
    row.update(held=[names[f] for f in held], held_split=[names[f] for f in held if f in split],
               exact=[names[f] for f in exact])
    row["contained"] = _contained(make, choice, edited, x1, splits, None)

    def find(fs: list[int]) -> list[str]:
        """The features whose splits alone exclude the real file (halving; a joint failure is named by its range)."""
        if _contained(make, choice, edited, x1, splits, set(fs)):
            return []
        if len(fs) == 1:
            return [names[fs[0]]]
        half = len(fs) // 2
        out = find(fs[:half]) + find(fs[half:])
        return out or [f"jointly: {names[fs[0]]} .. {names[fs[-1]]}"]

    row["failing"] = [] if row["contained"] else find(sorted(splits.thresholds))
    return row


################################################################################
# Main
################################################################################


_STATE: dict[str, Any] = {}


def _job(task: tuple[str, bytes, int]) -> list[dict[str, Any]]:
    name, z, seed = task
    extractor: SumsFeatureExtractor = _STATE["extractor"]
    args = _STATE["args"]
    b = budget(len(z), args.budget_frac, args.budget_min)

    def make() -> Encoding:
        return Encoding(extractor, z, b, args.max_sections)

    try:
        t0 = time.time()
        enc = make()
        build = time.time() - t0
    except NotCovered as e:
        return [{"name": name, "covered": False, "reason": str(e), "written": False, "held": [], "held_split": [],
                 "exact": [], "failing": [], "contained": None}]
    rng = np.random.default_rng(seed)
    choices = [Choice((), b"")] + [random_choice(rng, enc.k, _STATE["donors"]) for _ in range(args.edits)]
    rows = []
    for i, choice in enumerate(choices):
        t0 = time.time()
        row = check_edit(make, extractor, z, choice, _STATE["splits"], extractor.feature_names)
        row.update(name=name, covered=True, reason=None, edit=i, k=enc.k, budget=b, build_seconds=build, seconds=time.time() - t0)
        rows.append(row)
    return rows


def main() -> None:
    import polars as pl

    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", default=None, help="name=model_dir (repeatable); default: the "
                        "three 10%% detectors.")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_files", type=int, default=None, help="At most this many files (malware first).")
    parser.add_argument("--goodware", action="store_true", help="Also test the pilot goodware.")
    parser.add_argument("--edits", type=int, default=12, help="Random edits per file (plus the empty edit).")
    parser.add_argument("--max_sections", type=int, default=3, help="K: at most this many added sections.")
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    specs = args.defense or [f"{d}=artifacts/models/gbdt/seed-0-s10-{d}" for d in ("ref", "pv-seen", "pv-all")]
    ensembles = [Ensemble(lightgbm.Booster(model_file=str(m / "model.txt"))) for m in _parse_defenses(specs).values()]
    malware, goodware = load_pilot(args.pilot_files, args.db)
    files = malware + (goodware if args.goodware else [])
    if args.num_files is not None:
        files = files[:args.num_files]
    _STATE.update(extractor=SumsFeatureExtractor(), args=args, splits=_Splits(ensembles), donors=[d for _, d in goodware])
    tasks = [(name, z, args.seed * 100003 + i) for i, (name, z) in enumerate(files)]
    print(f"{len(tasks)} files, {args.edits} edits each, K={args.max_sections}; "
          f"{len(_STATE['splits'].thresholds)} split features", flush=True)

    # NOTE: fork, so the workers inherit the extractor, the splits, and the donors.
    rows: list[dict[str, Any]] = []
    with multiprocessing.get_context("fork").Pool(args.workers) as pool:
        for out in tqdm(pool.imap_unordered(_job, tasks), total=len(tasks), mininterval=30):
            rows += out

    args.outdir.mkdir(parents=True, exist_ok=True)
    df = pl.DataFrame(rows, infer_schema_length=None)
    df.write_parquet(args.outdir / "edits.parquet")
    edits = df.filter(pl.col("covered") & pl.col("written"))
    failing: Counter[str] = Counter()
    for col in ("held", "exact", "failing"):
        for xs in edits[col].to_list():
            failing.update(f"{col}: {x}" for x in xs)
    report = {
        "files": len(tasks),
        "covered": int(df.filter(pl.col("covered"))["name"].n_unique()),
        "not_covered": dict(Counter(df.filter(~pl.col("covered"))["reason"].to_list())),
        "edits_written": edits.height,
        "edits_not_written": int(df.filter(pl.col("covered") & ~pl.col("written")).height),
        "contained": int(edits["contained"].sum()),
        "exact_ok": int((edits["exact"].list.len() == 0).sum()),
        "held_ok": int((edits["held"].list.len() == 0).sum()),
        "held_ok_on_splits": int((edits["held_split"].list.len() == 0).sum()),
        "median_seconds_per_edit": float(edits["seconds"].median()),  # type: ignore[arg-type]
        "failing_features": dict(failing.most_common(50)),
        "args": {k: str(v) for k, v in vars(args).items()},
    }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
