"""
Pull the stage-1 explanations of the explanation set back into the problem-space and measure how well the explainers
agree before and after the pullback (hypothesis (c)). Also saves the raw per-feature ambiguity and support of each
file's provenance and the pulled-back explanations binned along the file, for the pilot report.

Agreement between two explanations u and v of the same file, in either space:
    spearman    Spearman's rank correlation (ties get their average rank)
    cosine      cosine similarity
    wjaccard    weighted Jaccard similarity of the attribution magnitudes, sum min(|u|, |v|) / sum max(|u|, |v|),
                after normalizing each to unit L1 norm

In the problem-space, the vectors have one entry per element plus the null element. As a control for agreement
created by the pullback itself, each pair is also compared after randomly permuting the features of the second
explanation (the same permutation in both spaces).

Outputs, in `{explanations}/seed-{seed}/pullback/`:
    agreement.parquet   one row per (file, pair of explainers, space, control)
    entropy.npy         float32 (N, d), H_j of each feature (0 for unattributable features)
    support.npy         int32 (N, d), |A_j|, the number of elements with nonzero provenance of each feature
    bins.npy            float32 (N, E, 2, B + 1), per explainer the signed and absolute pulled-back attribution in B
                        equal-width bins of the elements, then the null element
    report.json         the configuration, failures, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/pullback_agreement.py --seed 0 --num_workers 16
"""

from argparse import ArgumentParser
from itertools import combinations
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
from scipy.stats import rankdata
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor


ROOT = Path(__file__).parent.parent

_EXTRACTOR: Optional[PEFeatureExtractor] = None

FloatArray = npt.NDArray[np.float64]


################################################################################
# Agreement
################################################################################


def agreement(u: FloatArray, v: FloatArray, ru: FloatArray, rv: FloatArray) -> dict[str, float]:
    """The agreement of two explanations, given their ranks (see the module docstring)."""
    def corr(x: FloatArray, y: FloatArray) -> float:
        x, y = x - x.mean(), y - y.mean()
        d = float(np.sqrt((x @ x) * (y @ y)))
        return float(x @ y) / d if d > 0 else float("nan")
    nu, nv = float(np.linalg.norm(u)), float(np.linalg.norm(v))
    pu, pv = np.abs(u), np.abs(v)
    su, sv = float(pu.sum()), float(pv.sum())
    wjaccard = float(np.minimum(pu / su, pv / sv).sum() / np.maximum(pu / su, pv / sv).sum()) if su > 0 and sv > 0 else float("nan")
    return {
        "spearman": corr(ru, rv),
        "cosine": float(u @ v) / (nu * nv) if nu > 0 and nv > 0 else float("nan"),
        "wjaccard": wjaccard,
    }


def binned(b: FloatArray, num_bins: int) -> npt.NDArray[np.float32]:
    """The signed and absolute sums of a pulled-back explanation in equal-width bins of the elements, then the null."""
    m = b.shape[0] - 1
    which = np.minimum(np.arange(m) * num_bins // max(m, 1), num_bins - 1)
    out = np.zeros((2, num_bins + 1), dtype=np.float64)
    out[0, :num_bins] = np.bincount(which, weights=b[:m], minlength=num_bins)
    out[1, :num_bins] = np.bincount(which, weights=np.abs(b[:m]), minlength=num_bins)
    out[:, num_bins] = b[m], abs(b[m])
    return out.astype(np.float32)


################################################################################
# Workers
################################################################################


class Timeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise Timeout()


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def process_file(data: bytes, explanations: dict[str, FloatArray], num_bins: int, seed: int) -> tuple[list[dict[str, Any]], npt.NDArray[np.float32], npt.NDArray[np.int32], npt.NDArray[np.float32]]:
    """
    Returns:
        The agreement records, the raw ambiguity and support of each feature, and the binned pullbacks (E, 2, B + 1).
    """
    assert _EXTRACTOR is not None
    _, prov = _EXTRACTOR.feature_vector_with_provenance(data)
    ambiguity = prov.ambiguity()
    names = list(explanations)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(prov.num_features)

    feature = {e: explanations[e] for e in names}
    problem = {e: prov.pullback(a) for e, a in feature.items()}
    feature_perm = {e: a[perm] for e, a in feature.items()}
    problem_perm = {e: prov.pullback(a) for e, a in feature_perm.items()}
    ranks = {
        (space, control, e): rankdata(vectors[e])
        for space, control, vectors in [
            ("feature", False, feature), ("problem", False, problem),
            ("feature", True, feature_perm), ("problem", True, problem_perm),
        ]
        for e in names
    }

    records = []
    for e1, e2 in combinations(names, 2):
        for space, vectors, permuted in [("feature", feature, feature_perm), ("problem", problem, problem_perm)]:
            for control, v in [(False, vectors[e2]), (True, permuted[e2])]:
                r = agreement(vectors[e1], v, ranks[(space, False, e1)], ranks[(space, control, e2)])
                records.append({"explainer_1": e1, "explainer_2": e2, "space": space, "control": control} | r)
    bins = np.stack([binned(problem[e], num_bins) for e in names])
    return records, ambiguity.per_feature.astype(np.float32), ambiguity.support.astype(np.int32), bins


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    explanations: dict[str, FloatArray],
    num_bins: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], dict[int, tuple[npt.NDArray[np.float32], npt.NDArray[np.int32], npt.NDArray[np.float32]]]]:
    """Process the explanation-set samples in one SimpleDB shard (see scripts/provenance_census.py)."""
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    records: list[dict[str, Any]] = []
    arrays = {}
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
        base = {"index": meta["index"], "name": meta["name"], "label": meta["label"], "num_elements": len(sample.data)}
        signal.alarm(timeout)
        try:
            recs, entropy, support, bins = process_file(sample.data, {e: A[i] for e, A in explanations.items()}, num_bins, meta["index"])
            records.extend(base | {"status": "ok", "error": ""} | r for r in recs)
            arrays[meta["index"]] = (entropy, support, bins)
        except Timeout:
            records.append(base | {"status": "timeout", "error": f"Exceeded {timeout} seconds."})
        except Exception as err:
            records.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:500]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return records, arrays


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Pull back the stage-1 explanations and measure the agreement of explainers.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained models.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_bins", type=int, default=256)
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600, help="The maximum number of seconds per file.")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples (for testing).")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    indir = args.explanations / f"seed-{args.seed}"
    outdir = indir / "pullback"
    outdir.mkdir(parents=True, exist_ok=True)

    samples = pl.read_parquet(indir / "samples.parquet").select("name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left", maintain_order="left").with_row_index("index")
    if samples["shard"].null_count() > 0:
        raise RuntimeError(f"Some explained samples are not in {args.explanation_set.as_posix()}.")
    explainers = sorted(p.stem for p in indir.glob("*.npy"))
    if not explainers:
        raise RuntimeError(f"No explanations found in {indir.as_posix()}.")
    explanations = {name: np.load(indir / f"{name}.npy") for name in explainers}
    if args.limit is not None:
        samples = samples.head(args.limit)
    N, d = samples.height, next(iter(explanations.values())).shape[1]
    print(f"Pulling back {N} samples with explainers {explainers}.", flush=True)

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        idx = group["index"].to_numpy()
        tasks.append((
            int(shard),
            group.select("index", "name", "label", "position").to_dicts(),
            args.db,
            {name: A[idx] for name, A in explanations.items()},
            args.num_bins,
            args.timeout,
        ))

    t_0 = time.time()
    records: list[dict[str, Any]] = []
    entropy = np.full((N, d), np.nan, dtype=np.float32)
    support = np.zeros((N, d), dtype=np.int32)
    bins = np.full((N, len(explainers), 2, args.num_bins + 1), np.nan, dtype=np.float32)
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for recs, arrays in tqdm(pool.imap_unordered(_star_process_shard, tasks), total=len(tasks)):
            records.extend(recs)
            for i, (h, s, b) in arrays.items():
                entropy[i], support[i], bins[i] = h, s, b

    table = pl.DataFrame(records, infer_schema_length=None).sort("index", maintain_order=True)
    table.write_parquet(outdir / "agreement.parquet")
    np.save(outdir / "entropy.npy", entropy)
    np.save(outdir / "support.npy", support)
    np.save(outdir / "bins.npy", bins)

    failed = table.unique("index").filter(pl.col("status") != "ok")
    report = {
        "seed": args.seed,
        "explainers": explainers,
        "num_bins": args.num_bins,
        "num_samples": N,
        "num_failed": failed.height,
        "failed": failed.select("name", "status", "error").to_dicts(),
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report | {"failed": report["failed"][:5]}, indent=2), flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


def _star_process_shard(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], dict[int, tuple[npt.NDArray[np.float32], npt.NDArray[np.int32], npt.NDArray[np.float32]]]]:
    return process_shard(*task)


if __name__ == "__main__":
    main()
