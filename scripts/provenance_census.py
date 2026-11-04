"""
Compute the provenance census of the explanation set: the statistics of each file's provenance, overall and for each
subset of features, and the localizability of each stage-1 explanation (see scripts/explain.py).

The subsets are the groups of the feature set, i.e., the prefixes of the feature names before the first ":". The
statistics of a subset describe it in isolation (see `Provenance.select`).

Outputs, in `{explanations}/seed-{seed}/{name}/` (default `census/`):
    census.parquet      one row per (file, subset): coverage, ambiguity H (the mean entropy of the attributable
                        features, in nats), the median effective support exp(H_j), overlap O (the mean of
                        O_j = 1 - M_jj), and the localizability of each explanation restricted to the subset, plus the
                        file's metadata
                        and, per subset in isolation, the element-side statistics: element coverage (the share of
                        elements that influence some feature of the subset) and the median push-pull diagonal N_ii over
                        those elements; for the full set, the pull-push error of each explanation restricted to the
                        attributable features and its bound 2 sum_j |a_j| O_j (manuscript, Theorem Round-Trip Bounds)
    ambiguity.npy       float32 (N, d), the ambiguity H_j of each feature under the full provenance
    overlap.npy         float32 (N, d), the overlap O_j of each feature under the full provenance
    confusion.npy       float32 (N, G, G), the subset confusion matrix of each file: entry (g, h) is the mean, over the
                        attributable features j of subset g, of the share of j's attribution that a pull-push round
                        trip lands on subset h (the blocks of M); NaN where g has no attributable feature
    spectrum.npz        the eigenvalues of M restricted to the attributable features of each file, concatenated
                        (`values`, float32) with `offsets` (N + 1); M is block-diagonal between attributable and
                        unattributable features, and the latter's block only has the eigenvalues 1 and 0
    attributable.npy    bool (N, d), whether each feature is attributable to some element
    report.json         the configuration, failures, and timing

Rows of the arrays follow the explanation set's samples.parquet. Rows of files that failed are NaN (or False).

Usage:
    PYTHONHASHSEED=0 python scripts/provenance_census.py --seed 0 --num_workers 16
"""

from argparse import ArgumentParser
from collections.abc import Sequence
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
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.data.tabular import load_features
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.provenance import Provenance
from provexp.data.paths import EMBER2024_DATA


ROOT = Path(__file__).parent.parent
ALL = "all"

_EXTRACTOR: Optional[PEFeatureExtractor] = None


################################################################################
# Workers
################################################################################


class CensusTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise CensusTimeout()


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def subsets_by_prefix(names: Sequence[str]) -> dict[str, npt.NDArray[np.bool_]]:
    """All features, then one subset per name prefix (the part before the first ":"), in order of appearance."""
    prefixes = np.array([name.split(":", 1)[0] for name in names])
    subsets = {ALL: np.ones(len(names), dtype=np.bool_)}
    for prefix in dict.fromkeys(prefixes.tolist()):
        subsets[prefix] = prefixes == prefix
    return subsets


def census(prov: Provenance, explanations: dict[str, npt.NDArray[np.float64]]) -> list[dict[str, Any]]:
    """
    The statistics of the provenance of every subset, and the localizability of each explanation restricted to it.
    """
    assert prov.feature_names is not None
    records = []
    for subset, mask in subsets_by_prefix(prov.feature_names).items():
        sub = prov if subset == ALL else prov.select(mask)
        ambiguity = sub.ambiguity()
        record: dict[str, Any] = {
            "subset": subset,
            "num_features": sub.num_features,
            "num_attributable": int(sub.included.sum()),
            "coverage": sub.coverage,
            "ambiguity": ambiguity.overall,
            "effective_support": float(np.median(ambiguity.effective_support[sub.included])) if sub.included.any() else float("nan"),
            "overlap": sub.overlap().overall,
        }
        # Element-side statistics, which are only informative per subset (for the full set, every element feeds the
        # byte histogram).
        live = sub.rowsum()[:sub.num_elements] > 0
        record["element_coverage"] = float(live.mean()) if live.size else 0.0
        record["push_pull_diagonal"] = float(np.median(sub.push_pull_diagonal()[:sub.num_elements][live])) if live.any() else float("nan")
        for name, a in explanations.items():
            record[f"localizability:{name}"] = sub.localizability(a[mask])
        records.append(record)
    return records


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    explanations: dict[str, npt.NDArray[np.float64]],
    features: npt.NDArray[np.float32],
    timeout: int,
) -> tuple[list[dict[str, Any]], dict[int, tuple[npt.NDArray[np.float32], npt.NDArray[np.float32], npt.NDArray[np.bool_], npt.NDArray[np.float32], npt.NDArray[np.float32]]]]:
    """
    Compute the census of the explanation-set samples in one SimpleDB shard.

    Args:
        shard: The shard.
        samples: The samples in the shard, each with its `index` in the explanation set, `position` in the shard,
            `name`, `label`, and `size`.
        dbdir: The SimpleDB.
        explanations: For each explainer, the explanations of these samples, shape (len(samples), d).
        features: The stored feature vectors of these samples, shape (len(samples), d).
        timeout: The maximum number of seconds per file.

    Returns:
        The census records and, for each successful sample's index, its per-feature ambiguity, overlap, and
        attributability under the full provenance, its subset confusion matrix, and its spectrum.
    """
    assert _EXTRACTOR is not None
    groups = {g: mask for g, mask in subsets_by_prefix(_EXTRACTOR.feature_names).items() if g != ALL}
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
        t_0 = time.time()
        signal.alarm(timeout)
        try:
            x, prov = _EXTRACTOR.feature_vector_with_provenance(sample.data)
            matches = bool(np.allclose(x, features[i], rtol=1e-5, atol=1e-6, equal_nan=True))
            rows = census(prov, {name: A[i] for name, A in explanations.items()})
            M = prov.pull_push_matrix()
            included = prov.included
            O = prov.overlap().per_feature
            for name, A in explanations.items():
                a = np.where(included, A[i], 0.0)
                if np.all(np.isfinite(a)):
                    rows[0][f"pull_push_l1:{name}"] = float(np.abs(a).sum())
                    rows[0][f"pull_push_error:{name}"] = float(np.abs(a - M @ a).sum())
                    rows[0][f"pull_push_bound:{name}"] = float(2 * (np.abs(a) * O).sum())
            confusion = np.full((len(groups), len(groups)), np.nan)
            for g, from_mask in enumerate(groups.values()):
                cols = from_mask & included
                if cols.any():
                    confusion[g] = [M[np.ix_(to_mask, cols)].sum(axis=0).mean() for to_mask in groups.values()]
            spectrum = np.linalg.eigvalsh(M[np.ix_(included, included)]) if included.any() else np.zeros(0)
            arrays[meta["index"]] = (
                prov.ambiguity().per_feature.astype(np.float32),
                prov.overlap().per_feature.astype(np.float32),
                prov.included.copy(),
                confusion.astype(np.float32),
                np.clip(spectrum, 0.0, 1.0).astype(np.float32),
            )
            seconds = time.time() - t_0
            records.extend(base | {"status": "ok", "error": "", "matches": matches, "seconds": seconds} | r for r in rows)
        except CensusTimeout:
            records.append(base | {"status": "timeout", "error": f"Exceeded {timeout} seconds."})
        except Exception as err:
            records.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:500]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return records, arrays


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], dict[int, Any]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Compute the provenance census of the explanation set.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained models.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600, help="The maximum number of seconds per file.")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples (for testing).")
    parser.add_argument("--name", type=str, default="census", help="The output directory's name, inside the seed's explanations.")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    indir = args.explanations / f"seed-{args.seed}"
    outdir = indir / args.name
    outdir.mkdir(parents=True, exist_ok=True)

    # The explained samples, in order, with their location in the SimpleDB.
    samples = pl.read_parquet(indir / "samples.parquet").select("row", "name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position", "size")
    samples = samples.join(location, on="name", how="left", maintain_order="left").with_row_index("index")
    if samples["shard"].null_count() > 0:
        raise RuntimeError(f"Some explained samples are not in {args.explanation_set.as_posix()}.")
    explainers = sorted(p.stem for p in indir.glob("*.npy"))
    if not explainers:
        raise RuntimeError(f"No explanations found in {indir.as_posix()}.")
    explanations = {name: np.load(indir / f"{name}.npy") for name in explainers}
    if args.limit is not None:
        samples = samples.head(args.limit)
    N = samples.height
    if any(A.shape[0] < N for A in explanations.values()):
        raise RuntimeError(f"Some explainers have fewer than {N} explanations.")
    X, _ = load_features(args.features, "ts")
    print(f"Census of {N} samples with explainers {explainers}.", flush=True)

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        idx = group["index"].to_numpy()
        tasks.append((
            int(shard),
            group.select("index", "name", "label", "position").to_dicts(),
            args.db,
            {name: A[idx] for name, A in explanations.items()},
            np.asarray(X[group["row"].to_numpy()]),
            args.timeout,
        ))

    t_0 = time.time()
    records: list[dict[str, Any]] = []
    d = X.shape[1]
    ambiguity = np.full((N, d), np.nan, dtype=np.float32)
    overlap = np.full((N, d), np.nan, dtype=np.float32)
    attributable = np.zeros((N, d), dtype=np.bool_)
    groups = [g for g in subsets_by_prefix(PEFeatureExtractor().feature_names) if g != ALL]
    confusion = np.full((N, len(groups), len(groups)), np.nan, dtype=np.float32)
    spectra: dict[int, npt.NDArray[np.float32]] = {}
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        # imap_unordered (not starmap), so that the progress bar advances as shards finish; shards with more samples first.
        ordered = sorted(tasks, key=lambda task: -len(task[1]))
        for recs, arrays in tqdm(pool.imap_unordered(_star, ordered), total=len(tasks), desc="shards", mininterval=10):
            records.extend(recs)
            for i, (h, o, a, c, e) in arrays.items():
                ambiguity[i], overlap[i], attributable[i], confusion[i], spectra[i] = h, o, a, c, e

    table = pl.DataFrame(records, infer_schema_length=None).sort("index", maintain_order=True)
    table.write_parquet(outdir / "census.parquet")
    np.save(outdir / "ambiguity.npy", ambiguity)
    np.save(outdir / "overlap.npy", overlap)
    np.save(outdir / "attributable.npy", attributable)
    np.save(outdir / "confusion.npy", confusion)
    values = [spectra.get(i, np.zeros(0, dtype=np.float32)) for i in range(N)]
    offsets = np.concatenate([[0], np.cumsum([v.size for v in values])]).astype(np.int64)
    np.savez_compressed(outdir / "spectrum.npz", values=np.concatenate(values) if values else np.zeros(0, dtype=np.float32), offsets=offsets)

    files = table.unique("index")
    failed = files.filter(pl.col("status") != "ok")
    ok = table.filter((pl.col("status") == "ok") & (pl.col("subset") == ALL))
    report = {
        # The definitions of the statistics (manuscript): pre-2026-10-08 censuses used normalized entropy and pairwise
        # overlap, which pilot_tables.py flags.
        "statistics": "2026-10-08: ambiguity = mean entropy H_j (nats), overlap = mean of 1 - M_jj",
        "seed": args.seed,
        "explainers": explainers,
        "subsets": groups,
        "num_samples": N,
        "num_failed": failed.height,
        "failed": failed.select("name", "status", "error").to_dicts(),
        "num_mismatched_features": int((~ok["matches"]).sum()),
        "seconds_per_file": {"median": float(ok["seconds"].median() or 0.0), "max": float(ok["seconds"].max() or 0.0)},  # type: ignore[arg-type]
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report | {"failed": report["failed"][:5]}, indent=2), flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
