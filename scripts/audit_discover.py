"""
3-C revised (docs/experiments/audit.md): find what a raw-byte detector (MalConv) keys on across a corpus by pushing each
file's byte explanation forward into the EMBER features, where every file shares the same coordinates.

Phase `ig` (GPU): MalConv's log-odds and Integrated Gradients per byte for every explanation-set file, saved one file
at a time (`ig/{index}.npy`), since together they hold about 4 bytes per input byte.

Phase `discover` (CPU workers): per file and per source of a feature-space explanation a,
    - `malconv`: the pushforward of MalConv's IG, a = psi(b) = P^T D^+ b (the method);
    - `surrogate`: interventional TreeSHAP of a surrogate of MalConv on the same features (the realistic alternative,
      scripts/audit_surrogate.py);
the `top_k` features with the most credit in the chosen direction (seeded tie-break), and for each feature j the
content it was credited for: among the maximal runs of contiguous bytes in the support of P's column j, the run that
passes the most of the IG to j (for `malconv`: sum over the run of b_i P_ij / D_ii) or, for the surrogate, which has
no byte explanation, the run holding the most of j's provenance. A feature whose support is too spread (more than
`max_runs` runs) or whose chosen run is longer than `max_content` bytes is recorded with empty content: an aggregate,
which cannot be written into another file. Across files, the (feature, content) keys form patterns, scored as in 3-B
(scripts/shortcuts.py) by the number of files times the mean credit; the patterns are the transplant's candidates
(scripts/shortcuts_transplant.py --scorer malconv).

Outputs, in `{outdir}/seed-{seed}/`:
    ig/{index}.npy              MalConv's IG per byte (float32), phase `ig`
    malconv-{part}.parquet      one row per file of a part: MalConv's log-odds, the IG's sum, its completeness gap
    {source}-{direction}/
        files.parquet           one row per file: status, total credit in the direction, the aggregates' share of it
        features.parquet        one row per (file, top feature): rank, credit, share, run start and length, content
        patterns.parquet        one row per (feature, content) with content (3-B's columns: top_feature, content,
                                files, benign_files, malware_files, mean_credit, total_credit, length, score)
        aggregates.parquet      the same for the features recorded without content
        report.json             the configuration and the summary

Usage:
    CUDA_VISIBLE_DEVICES=0 PYTHONHASHSEED=0 python scripts/audit_discover.py --seed 0 --phase ig --part 0 --num_parts 4
    PYTHONHASHSEED=0 python scripts/audit_discover.py --seed 0 --phase discover --num_workers 32
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
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
from numpy import typing as npt
import polars as pl
import torch
from tqdm import tqdm

from provexp.ablation import element_order
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.data.tabular import load_features
from provexp.explain.problem import malconv_integrated_gradients
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.malconv import encode
from provexp.models.malconv import load_pretrained_malconv
from provexp.provenance import Provenance

sys.path.insert(0, str(Path(__file__).parent))
from faithfulness import load_sample  # noqa: E402
from shortcuts import patterns  # noqa: E402
from shortcuts import preview  # noqa: E402


__all__ = [
    "feature_credit_runs",
    "choose_content",
]


ROOT = Path(__file__).parent.parent
DIRECTIONS = {"benign": -1.0, "malware": 1.0}
SOURCES = ("malconv", "surrogate")

_EXTRACTOR: Optional[PEFeatureExtractor] = None


################################################################################
# Content
################################################################################


def feature_credit_runs(
    prov: Provenance,
    feature: int,
    weights: Optional[npt.NDArray[np.float64]],
    max_runs: int,
) -> Optional[list[tuple[int, int, float]]]:
    """
    The maximal runs of contiguous elements in the support of P's column `feature`, each with its credit.

    Args:
        prov: The provenance of one file.
        feature: The feature j.
        weights: Per element, the weight w_i of its provenance: the run's credit is the sum over the run of
            w_i P_ij (for the pushforward of b, w = D^+ b). None weighs every element by 1 (the provenance mass).
        max_runs: Give up (return None) if the support has more runs than this (an aggregate).

    Returns:
        [(start, length, credit), ...] sorted by start, or None for a too spread support. The null element is never
        part of a run.
    """
    m = prov.num_elements
    pieces = prov.select(np.array([feature], dtype=np.int64)).pieces()
    runs: list[list[float]] = []
    for lo, hi, val in zip(pieces.lo.tolist(), pieces.hi.tolist(), pieces.val.tolist()):
        hi = min(hi, m)
        if lo >= hi:
            continue
        credit = float(val * (weights[lo:hi].sum() if weights is not None else hi - lo))
        if runs and runs[-1][0] + runs[-1][1] == lo:
            runs[-1][1] += hi - lo
            runs[-1][2] += credit
        else:
            if len(runs) >= max_runs:
                return None
            runs.append([lo, hi - lo, credit])
    return [(int(s), int(n), float(c)) for s, n, c in runs]


def choose_content(runs: Optional[list[tuple[int, int, float]]], direction: float, max_content: int) -> tuple[int, int]:
    """
    The run with the most credit in `direction` (ties: the first), as (start, length), or (-1, 0) if there is none,
    the support was too spread, or the run is longer than `max_content`.
    """
    if not runs:
        return -1, 0
    best = max(range(len(runs)), key=lambda r: (direction * runs[r][2], -r))
    start, length, _ = runs[best]
    if length > max_content:
        return -1, 0
    return start, length


################################################################################
# Phase 1: MalConv's IG
################################################################################


def run_ig(samples: pl.DataFrame, checkpoint: Path, db: Path, steps: int, device: str, outdir: Path) -> pl.DataFrame:
    """MalConv's log-odds and IG for each sample, saved to `outdir/ig/`; files already done are skipped."""
    igdir = outdir / "ig"
    igdir.mkdir(parents=True, exist_ok=True)
    model = load_pretrained_malconv(checkpoint).to(device)
    rows = []
    for r in tqdm(samples.iter_rows(named=True), total=samples.height, desc="MalConv IG", mininterval=30):
        path = igdir / f"{r['index']}.npy"
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], db)
        x = encode(data).to(device)
        with torch.no_grad():
            z = model(x[None])
            empty = model(torch.zeros_like(x)[None])
        log_odds, baseline = float(z[0, 1] - z[0, 0]), float(empty[0, 1] - empty[0, 0])
        if path.exists():
            ig = np.load(path)
        else:
            ig = malconv_integrated_gradients(model, x, steps=steps, batch_size=16).float().cpu().numpy()
            np.save(path, ig)
        total = float(ig.astype(np.float64).sum())
        rows.append({"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "size": len(data),
                     "log_odds": log_odds, "ig_sum": total, "completeness_gap": total - (log_odds - baseline)})
    return pl.DataFrame(rows)


################################################################################
# Phase 2: workers
################################################################################


class DiscoverTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise DiscoverTimeout()


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    igdir: Path,
    surrogate: Optional[npt.NDArray[np.float64]],
    features: npt.NDArray[np.float32],
    direction: float,
    top_k: int,
    max_runs: int,
    max_content: int,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    The top features of each source for the explanation-set samples in one SimpleDB shard.

    Args:
        shard: The shard.
        samples: The samples in the shard, each with its `index`, `position`, `name`, and `label`.
        dbdir: The SimpleDB.
        igdir: The directory of MalConv's IG, one `{index}.npy` per sample.
        surrogate: The surrogate's explanations of these samples, shape (len(samples), d), or None to skip it.
        features: The stored feature vectors of these samples, shape (len(samples), d).
        direction: The sign of the credit to look for (-1 for benign, 1 for malware).
        top_k: The number of features per file and source.
        max_runs: Features whose support has more runs than this are aggregates (no content).
        max_content: Chosen runs longer than this are aggregates (no content).
        seed: The seed of the tie-break permutations (one per file, from the seed and the file's index).
        timeout: The maximum number of seconds per file.

    Returns:
        The file records and the feature records, each with its `source`.
    """
    assert _EXTRACTOR is not None
    names = _EXTRACTOR.feature_names
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        i = wanted[position]
        meta = samples[i]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"], "label": meta["label"]}
        t_0 = time.time()
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            x, prov = _EXTRACTOR.feature_vector_with_provenance(data)
            matches = bool(np.allclose(x, features[i], rtol=1e-5, atol=1e-6, equal_nan=True))
            m = prov.num_elements
            b = np.load(igdir / f"{meta['index']}.npy").astype(np.float64)
            if b.shape != (m,):
                raise RuntimeError(f"MalConv's IG has shape {b.shape} for a file of {m} bytes.")
            D = prov.rowsum()[:m]
            pushed = np.where(D > 0, b / np.where(D > 0, D, 1.0), 0.0)
            sources: dict[str, tuple[npt.NDArray[np.float64], Optional[npt.NDArray[np.float64]]]] = {
                "malconv": (prov.pushforward(b), pushed)}
            if surrogate is not None:
                sources["surrogate"] = (np.asarray(surrogate[i], dtype=np.float64), None)
            tiebreak = np.random.default_rng([seed, int(meta["index"])]).permutation(prov.num_features).astype(np.int64)
            for source, (a, weights) in sources.items():
                credit = direction * a
                total = float(credit[credit > 0].sum())
                order = element_order(a, direction, tiebreak)[:top_k]
                order = order[credit[order] > 0]
                aggregate = 0.0
                for rank, j in enumerate(order.tolist()):
                    runs = feature_credit_runs(prov, j, weights, max_runs)
                    start, length = choose_content(runs, direction if weights is not None else 1.0, max_content)
                    if length == 0:
                        aggregate += float(credit[j])
                    records.append({
                        "source": source, "index": meta["index"], "label": meta["label"], "rank": rank,
                        "top_feature": names[j], "credit": float(credit[j]),
                        "share": float(credit[j]) / total if total > 0 else float("nan"),
                        "num_runs": len(runs) if runs is not None else -1, "start": start, "length": length,
                        "content": data[start:start + length] if length else b"",
                    })
                files.append(base | {
                    "source": source, "status": "ok", "error": "", "matches": matches, "size": m, "credit": total,
                    "top_k_share": float(credit[order].sum()) / total if total > 0 else float("nan"),
                    "aggregate_share": aggregate / total if total > 0 else float("nan"), "seconds": time.time() - t_0,
                })
        except DiscoverTimeout:
            files.append(base | {"source": "", "status": "timeout", "error": f"Exceeded {timeout} seconds."})
        except Exception as err:
            files.append(base | {"source": "", "status": "error", "error": f"{type(err).__name__}: {err}"[:500]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files, records


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Find what MalConv keys on through the pushforward (3-C revised).")
    parser.add_argument("--seed", type=int, default=0, help="The seed of MalConv, the surrogate, and the tie-breaks.")
    parser.add_argument("--phase", type=str, choices=["ig", "discover"], required=True)
    parser.add_argument("--direction", type=str, choices=list(DIRECTIONS), default="benign")
    parser.add_argument("--top_k", type=int, default=20, help="The number of most credited features per file.")
    parser.add_argument("--max_runs", type=int, default=256, help="Features with more runs than this are aggregates.")
    parser.add_argument("--max_content", type=int, default=256, help="Chosen runs longer than this are aggregates.")
    parser.add_argument("--min_length", type=int, default=4, help="The shortest content that forms a pattern.")
    parser.add_argument("--steps", type=int, default=256, help="IG steps (as in 3-A).")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--surrogate", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_surrogate")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_discover")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples (for testing).")
    parser.add_argument("--part", type=int, default=0, help="Phase ig: which part of the files to do (one per GPU).")
    parser.add_argument("--num_parts", type=int, default=1, help="Phase ig: the number of parts.")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=900, help="The maximum number of seconds per file.")
    parser.add_argument("--show", type=int, default=30, help="The number of top patterns to print per source.")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")
    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)

    # The explanation set, in the order of the saved explanations, with its location in the SimpleDB.
    samples = pl.read_parquet(args.explanations / f"seed-{args.seed}" / "samples.parquet").select("row", "name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left", maintain_order="left").with_row_index("index")
    samples = samples.with_columns(pl.col("index").cast(pl.Int64))
    if samples["shard"].null_count() > 0:
        raise RuntimeError(f"Some explained samples are not in {args.explanation_set.as_posix()}.")
    if args.limit is not None:
        samples = samples.head(args.limit)

    if args.phase == "ig":
        if not 0 <= args.part < args.num_parts:
            raise ValueError(f"Expected 0 <= part < num_parts. Got {args.part} and {args.num_parts}.")
        t_0 = time.time()
        part = samples.filter(pl.col("index") % args.num_parts == args.part)
        print(f"MalConv IG ({args.steps} steps) on {part.height} files (part {args.part} of {args.num_parts}), "
              f"{args.device}.", flush=True)
        table = run_ig(part, args.checkpoints / f"malconv-seed{args.seed}.pt", args.db, args.steps, args.device, outdir)
        table.write_parquet(outdir / f"malconv-{args.part}.parquet")
        gap = table["completeness_gap"].abs().to_numpy()
        print(f"Done in {(time.time() - t_0) / 60:.1f} min. Completeness gap (|sum IG - (f(x) - f(empty))|): "
              f"median {np.median(gap):.2e}, max {gap.max():.2e}. Wrote {outdir.as_posix()}.")
        return

    direction = DIRECTIONS[args.direction]
    surrogate_file = args.surrogate / f"seed-{args.seed}" / "shap.npy"
    A_s = np.load(surrogate_file) if surrogate_file.exists() else None
    if A_s is None:
        print(f"No surrogate at {surrogate_file.as_posix()}: MalConv only.", flush=True)
    elif A_s.shape[0] < samples.height:
        raise RuntimeError(f"The surrogate explains {A_s.shape[0]} files, fewer than {samples.height}.")
    missing = [i for i in samples["index"].to_list() if not (outdir / "ig" / f"{i}.npy").exists()]
    if missing:
        raise RuntimeError(f"No IG for {len(missing)} files (e.g., {missing[:5]}); run --phase ig first.")
    X, _ = load_features(args.features, "ts")
    print(f"Discovery on {samples.height} files: sources {'malconv, surrogate' if A_s is not None else 'malconv'}, "
          f"{args.direction}, top {args.top_k} features per file.", flush=True)

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        idx = group["index"].to_numpy()
        tasks.append((int(shard), group.select("index", "name", "label", "position").to_dicts(), args.db,
                      outdir / "ig", A_s[idx] if A_s is not None else None, np.asarray(X[group["row"].to_numpy()]),
                      direction, args.top_k, args.max_runs, args.max_content, args.seed, args.timeout))

    t_0 = time.time()
    files: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for f, r in tqdm(pool.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks),
                         desc="shards", mininterval=10):
            files.extend(f)
            records.extend(r)
    file_table = pl.DataFrame(files, infer_schema_length=None)
    feature_table = pl.DataFrame(records, schema_overrides={"content": pl.Binary}, infer_schema_length=None)
    failed = file_table.filter(pl.col("status") != "ok")
    if failed.height:
        print(f"{failed.height} files failed: {failed.select('index', 'status', 'error').head(5).to_dicts()}", flush=True)

    for source in feature_table["source"].unique().sort().to_list():
        sub = outdir / f"{source}-{args.direction}"
        sub.mkdir(parents=True, exist_ok=True)
        fs = file_table.filter(pl.col("source") == source).sort("index")
        rec = feature_table.filter(pl.col("source") == source).sort("index", "rank")
        with_content = patterns(rec.filter(pl.col("length") > 0), args.min_length)
        aggregates = (rec.filter(pl.col("length") == 0).group_by("top_feature")
                      .agg(pl.len().alias("files"), (pl.col("label") == 0).sum().alias("benign_files"),
                           (pl.col("label") == 1).sum().alias("malware_files"), pl.col("credit").mean().alias("mean_credit"))
                      .with_columns((pl.col("files") * pl.col("mean_credit")).alias("score")).sort("score", descending=True))
        fs.write_parquet(sub / "files.parquet")
        rec.write_parquet(sub / "features.parquet")
        with_content.write_parquet(sub / "patterns.parquet")
        aggregates.write_parquet(sub / "aggregates.parquet")
        report = {
            "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
            "source": source, "num_files": fs.height,
            "status": dict(Counter(file_table.filter(pl.col("status") != "ok")["status"].to_list())),
            "features_match": int(fs["matches"].sum()),
            "median_top_k_share": float(fs["top_k_share"].median() or 0.0),  # type: ignore[arg-type]
            "median_aggregate_share": float(fs["aggregate_share"].median() or 0.0),  # type: ignore[arg-type]
            "num_patterns": with_content.height,
            "patterns_in_10_or_more_files": int((with_content["files"] >= 10).sum()),
            "minutes": (time.time() - t_0) / 60,
        }
        (sub / "report.json").write_text(json.dumps(report, indent=2))
        print(f"\n=== {source} ===")
        print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))
        print(f"Top {args.show} patterns in >= 10 files (score = files x mean credit):")
        for r in with_content.filter(pl.col("files") >= 10).head(args.show).iter_rows(named=True):
            print(f"{r['score']:8.3f}  files {r['files']:4d} (benign {r['benign_files']:4d})  credit {r['mean_credit']:.3f}  "
                  f"len {r['length']:4d}  {r['top_feature'][:40]:40s}  {preview(r['content'])}")
        print("Top aggregates (no content):")
        for r in aggregates.head(10).iter_rows(named=True):
            print(f"{r['score']:8.3f}  files {r['files']:4d}  credit {r['mean_credit']:.3f}  {r['top_feature']}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
