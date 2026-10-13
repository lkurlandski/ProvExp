"""
CP.3 (docs/experiments/cp.md): the statistics of P at coarser granularities. Coarsening P to windows of elements
never lowers a feature's overlap and never raises its ambiguity; this measures by how much, per subset, at the window
counts of PB1's sweep, and how the round-trip bound behaves at each granularity.

For each file and granularity (the elements themselves, then K windows), with the full provenance:
    overlap             the mean O_j over the attributable features (overall and per subset)
    effective support   the median exp(H_j), in units of the granularity (elements or windows)
    round trip          ||a - Ma||_1 / ||a||_1 and the bound 2 sum_j |a_j| O_j / ||a||_1 for an explainer's
                        explanation restricted to the attributable features

Outputs, in `{explanations}/seed-{seed}/coarsening/`:
    coarsening.parquet  one row per (file, granularity, subset)

Usage:
    PYTHONHASHSEED=0 python scripts/cp_coarsening.py --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet --num_workers 4
"""

from argparse import ArgumentParser
import multiprocessing as mp
import os
from pathlib import Path
import sys
from typing import Any
from typing import Optional
import warnings

import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.ablation import coarsen_provenance
from provexp.ablation import window_edges
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.provenance import Provenance


ROOT = Path(__file__).parent.parent
ELEMENTS = 0  # The granularity of the elements themselves.

_EXTRACTOR: Optional[PEFeatureExtractor] = None


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def statistics(prov: Provenance, a: npt.NDArray[np.float64], groups: dict[str, npt.NDArray[np.bool_]]) -> list[dict[str, Any]]:
    """The overlap and effective support overall and per subset, and the round trip of `a`, under `prov`."""
    att = prov.included
    O = prov.overlap().per_feature
    support = prov.ambiguity().effective_support
    b = np.where(att, a, 0.0)
    l1 = float(np.abs(b).sum())
    round_trip = float(np.abs(b - prov.pull_push(b)).sum()) / l1 if l1 > 0 else float("nan")
    bound = float(2 * (np.abs(b) * O).sum()) / l1 if l1 > 0 else float("nan")
    rows = []
    for name, mask in ({"all": np.ones_like(att)} | groups).items():
        cols = mask & att
        rows.append({
            "subset": name,
            "overlap": float(O[cols].mean()) if cols.any() else float("nan"),
            "effective_support": float(np.median(support[cols])) if cols.any() else float("nan"),
        } | ({"round_trip": round_trip, "bound": bound} if name == "all" else {}))
    return rows


def process_shard(shard: int, samples: list[dict[str, Any]], dbdir: Path, explanations: npt.NDArray[np.float64], windows: tuple[int, ...]) -> list[dict[str, Any]]:
    assert _EXTRACTOR is not None
    prefix = np.array([name.split(":", 1)[0] for name in _EXTRACTOR.feature_names])
    groups = {g: prefix == g for g in dict.fromkeys(prefix.tolist())}
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    records: list[dict[str, Any]] = []
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        i = wanted[position]
        meta = samples[i]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        _, prov = _EXTRACTOR.feature_vector_with_provenance(sample.data)
        base = {"index": meta["index"], "label": meta["label"], "num_elements": prov.num_elements}
        for K in (ELEMENTS, *windows):
            P = prov if K == ELEMENTS else coarsen_provenance(prov, window_edges(prov.num_elements, K))
            records.extend(base | {"granularity": K, "num_windows": P.num_elements} | r for r in statistics(P, explanations[i], groups))
    return records


def _star(task: tuple[Any, ...]) -> list[dict[str, Any]]:
    return process_shard(*task)


def main() -> None:
    parser = ArgumentParser(description="CP: the statistics of P at coarser granularities.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--files", type=Path, required=True, help="The files to use (a files.parquet with `name`), e.g., the PB1 files.")
    parser.add_argument("--windows", type=int, nargs="+", default=[4096, 1024, 256, 64])
    parser.add_argument("--explainer", type=str, default="treeshap_path")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_workers", type=int, default=4)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")
    if any(K < 1 for K in args.windows):
        raise ValueError(f"Window counts must be positive. Got {args.windows}.")

    indir = args.explanations / f"seed-{args.seed}"
    outdir = indir / "coarsening"
    outdir.mkdir(parents=True, exist_ok=True)
    A = np.load(indir / f"{args.explainer}.npy")
    names = pl.read_parquet(args.files)["name"]
    samples = pl.read_parquet(indir / "samples.parquet").with_row_index("index").filter(pl.col("name").is_in(names.implode()))
    samples = samples.join(pl.read_parquet(args.explanation_set).select("name", "shard", "position"), on="name")
    if samples.height != names.len():
        raise RuntimeError(f"{names.len() - samples.height} files of {args.files.as_posix()} are not in the explanation set.")

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "label", "position").to_dicts(), args.db, A[group["index"].to_numpy()], tuple(args.windows)))
    records: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for recs in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks), desc="shards"):
            records.extend(recs)
    table = pl.DataFrame(records, infer_schema_length=None).sort("index", "granularity")
    table.write_parquet(outdir / "coarsening.parquet")

    # Medians over files, by granularity (0 = the elements themselves).
    order = [ELEMENTS, *sorted(args.windows, reverse=True)]
    full = table.filter(pl.col("subset") == "all")
    print("## Full feature set (median over files)\n")
    print(full.group_by("granularity").agg(
        pl.col("overlap").median(), pl.col("effective_support").median(), pl.col("round_trip").median(), pl.col("bound").median(),
        (pl.col("round_trip") / pl.col("bound")).median().alias("round_trip / bound"),
    ).sort(pl.col("granularity").replace_strict(order, list(range(len(order))))), "\n")
    print("## Mean overlap per subset (median over files)\n")
    per = table.filter(pl.col("subset") != "all").group_by("subset", "granularity").agg(pl.col("overlap").median())
    print(per.pivot(on="granularity", index="subset", values="overlap").select("subset", *[str(K) for K in order]))
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
