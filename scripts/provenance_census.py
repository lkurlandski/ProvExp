"""
Compute the provenance census of the explanation set: the statistics of each file's provenance, overall and for each
subset of features, and the localizability of each stage-1 explanation (see scripts/explain.py).

The subsets are the groups of the feature set, i.e., the prefixes of the feature names before the first ":". The
statistics of a subset describe it in isolation (see `Provenance.select`).

Outputs, in `{explanations}/seed-{seed}/census/`:
    census.parquet      one row per (file, subset): coverage, ambiguity, overlap, and the localizability of each
                        explanation restricted to the subset, plus the file's metadata
    ambiguity.npy       float32 (N, d), the normalized ambiguity of each feature under the full provenance
    overlap.npy         float32 (N, d), the normalized overlap of each feature under the full provenance
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
        record: dict[str, Any] = {
            "subset": subset,
            "num_features": sub.num_features,
            "num_attributable": int(sub.included.sum()),
            "coverage": sub.coverage,
            "ambiguity": sub.ambiguity().overall,
            "overlap": sub.overlap().overall,
        }
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
) -> tuple[list[dict[str, Any]], dict[int, tuple[npt.NDArray[np.float32], npt.NDArray[np.float32], npt.NDArray[np.bool_]]]]:
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
        attributability under the full provenance.
    """
    assert _EXTRACTOR is not None
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
            arrays[meta["index"]] = (
                prov.ambiguity().normalized.astype(np.float32),
                prov.overlap().normalized.astype(np.float32),
                prov.included.copy(),
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


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Compute the provenance census of the explanation set.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained models.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600, help="The maximum number of seconds per file.")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples (for testing).")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    indir = args.explanations / f"seed-{args.seed}"
    outdir = indir / "census"
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
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for recs, arrays in tqdm(pool.starmap(process_shard, tasks, chunksize=1), total=len(tasks)):
            records.extend(recs)
            for i, (h, o, a) in arrays.items():
                ambiguity[i], overlap[i], attributable[i] = h, o, a

    table = pl.DataFrame(records, infer_schema_length=None).sort("index", maintain_order=True)
    table.write_parquet(outdir / "census.parquet")
    np.save(outdir / "ambiguity.npy", ambiguity)
    np.save(outdir / "overlap.npy", overlap)
    np.save(outdir / "attributable.npy", attributable)

    files = table.unique("index")
    failed = files.filter(pl.col("status") != "ok")
    ok = table.filter((pl.col("status") == "ok") & (pl.col("subset") == ALL))
    report = {
        "seed": args.seed,
        "explainers": explainers,
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
