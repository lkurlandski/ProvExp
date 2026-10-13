"""
3-C revised, the global comparison (docs/experiments/audit.md, "Comparing the two detectors globally"): what the GBDT and
MalConv rely on across the whole corpus, in the same feature-space vocabulary. The GBDT has a feature-space
explanation already (interventional TreeSHAP); MalConv does not, until its per-byte IG is pushed forward into the same
features. Then the two global reliances can be compared feature by feature, which is the pullback/pushforward symmetry
applied to an audit. This replaces the per-file feature-space comparison that was Appendix F (removed).

Phase `push` (CPU workers): per explanation-set file, MalConv's IG (saved by scripts/audit_discover.py --phase ig) is
pushed forward through the file's provenance, a = psi(b) = P^T D^+ b, and the full feature vector is saved to
`pushforward.npy` (one row per file, aligned to the explanations' samples order). Per-feature provenance support is
accumulated so aggregate (non-localizable) features can be flagged.

Phase `compare` (driver): both models' per-file attributions are reduced to per-feature global reliance:
    - `mean_abs`: the mean over files of |a_j|, the raw importance (ranked by this);
    - `mean_signed`: the mean over files of a_j, the net direction (both explainers attribute the malware log-odds, so
      positive pushes malware).
A feature is an *aggregate* (reported separately) if its provenance holds no locatable content in most files (median
support 0 or above `max_content`): the histogram, byte-entropy, and other whole-file statistics, where "MalConv relies
on the byte histogram" is not an actionable finding (PF1's resolution limit).

Outputs, in `{outdir}/seed-{seed}/`:
    pushforward.npy     MalConv's pushed-forward attributions, shape (num_files, num_features), phase `push`
    features.parquet    one row per feature: name, aggregate flag, median support, and each model's mean_abs and
                        mean_signed; a `scramble_confirmed` flag for the features confirmed in run 44
    report.json         the configuration, the rank correlations, the top features, and the shared reliance

Usage:
    PYTHONHASHSEED=0 python scripts/cm_global.py --seed 0 --phase push --num_workers 16
    PYTHONHASHSEED=0 python scripts/cm_global.py --seed 0 --phase compare
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional

import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))
from faithfulness import load_sample  # noqa: E402


__all__ = [
    "feature_support",
    "global_reliance",
]


ROOT = Path(__file__).parent.parent

_EXTRACTOR: Optional[PEFeatureExtractor] = None


################################################################################
# Pushforward
################################################################################


def feature_support(prov: Any) -> npt.NDArray[np.int64]:
    """The number of locatable (non-null) bytes in each feature's provenance, shape (num_features,)."""
    pieces = prov.pieces()
    lengths = (pieces.hi - pieces.lo).astype(np.int64)
    locatable = pieces.lo < prov.num_elements  # the null element sits at index num_elements.
    return np.bincount(pieces.col[locatable], weights=lengths[locatable], minlength=prov.num_features).astype(np.int64)


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    sys.stdout = open(os.devnull, "w")


def process_shard(
    shard: int, samples: list[dict[str, Any]], dbdir: Path, igdir: Path, num_features: int,
) -> tuple[list[int], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    """
    MalConv's pushed-forward attributions and per-feature support for the explanation-set files in one shard.

    Returns:
        The files' indices, their pushforward rows (len(indices), num_features), and the support rows (same shape).
    """
    assert _EXTRACTOR is not None
    wanted = {s["position"]: s for s in samples}
    indices: list[int] = []
    rows: list[npt.NDArray[np.float64]] = []
    supports: list[npt.NDArray[np.int64]] = []
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        meta = wanted[position]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        data = bytes(sample.data)
        _, prov = _EXTRACTOR.feature_vector_with_provenance(data)
        b = np.load(igdir / f"{meta['index']}.npy").astype(np.float64)
        if b.shape[0] != prov.num_elements:
            raise RuntimeError(f"File {meta['index']}: IG has {b.shape[0]} bytes, provenance {prov.num_elements}.")
        indices.append(int(meta["index"]))
        rows.append(prov.pushforward(b))
        supports.append(feature_support(prov))
    if not indices:
        return [], np.zeros((0, num_features)), np.zeros((0, num_features), dtype=np.int64)
    return indices, np.stack(rows), np.stack(supports)


def _star(task: tuple[Any, ...]) -> tuple[list[int], npt.NDArray[np.float64], npt.NDArray[np.int64]]:
    return process_shard(*task)


################################################################################
# Global reliance
################################################################################


def global_reliance(A: npt.NDArray[np.float64]) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """The per-feature mean |attribution| and mean signed attribution over files, each shape (num_features,)."""
    return np.abs(A).mean(axis=0), A.mean(axis=0)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-C revised: compare the GBDT's and MalConv's global reliance in feature space.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--phase", type=str, choices=["push", "compare"], required=True)
    parser.add_argument("--max_content", type=int, default=256, help="Features with more support than this are aggregates.")
    parser.add_argument("--top_k", type=int, default=25, help="The number of top features reported per model.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--discover", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_discover")
    parser.add_argument("--scramble", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_scramble")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_global")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many files (for testing; push and compare must match).")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")
    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    names = PEFeatureExtractor().feature_names
    num_features = len(names)

    samples = pl.read_parquet(args.explanations / f"seed-{args.seed}" / "samples.parquet").select("row", "name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left", maintain_order="left").with_row_index("index")
    samples = samples.with_columns(pl.col("index").cast(pl.Int64))
    if samples["shard"].null_count() > 0:
        raise RuntimeError(f"Some explained samples are not in {args.explanation_set.as_posix()}.")
    if args.limit is not None:
        samples = samples.head(args.limit)

    if args.phase == "push":
        igdir = args.discover / f"seed-{args.seed}" / "ig"
        missing = [i for i in samples["index"].to_list() if not (igdir / f"{i}.npy").exists()]
        if missing:
            raise RuntimeError(f"No IG for {len(missing)} files (e.g., {missing[:5]}); run audit_discover --phase ig first.")
        tasks = []
        for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
            tasks.append((int(shard), group.select("index", "name", "position").to_dicts(), args.db, igdir, num_features))
        t_0 = time.time()
        A = np.zeros((samples.height, num_features), dtype=np.float64)
        support = np.zeros((samples.height, num_features), dtype=np.int64)
        seen = 0
        with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
            for idx, rows, sup in tqdm(pool.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))),
                                       total=len(tasks), desc="shards", mininterval=10):
                for k, i in enumerate(idx):
                    A[i] = rows[k]
                    support[i] = sup[k]
                seen += len(idx)
        if seen != samples.height:
            raise RuntimeError(f"Pushed forward {seen} files, expected {samples.height}.")
        np.save(outdir / "pushforward.npy", A)
        np.save(outdir / "support.npy", support)
        print(f"Pushed forward {seen} files in {(time.time() - t_0) / 60:.1f} min. Wrote {outdir.as_posix()}.")
        return

    # compare
    A_m = np.load(outdir / "pushforward.npy")
    support = np.load(outdir / "support.npy")
    A_g = np.load(args.explanations / f"seed-{args.seed}" / "treeshap_interventional.npy")
    if A_g.shape[0] > A_m.shape[0] and args.limit is not None:
        A_g = A_g[:A_m.shape[0]]  # The pushforward was limited; TreeSHAP is aligned to the same leading samples.
    if A_m.shape != A_g.shape:
        raise RuntimeError(f"MalConv's pushforward is {A_m.shape}, the GBDT's TreeSHAP {A_g.shape}.")
    median_support = np.median(support, axis=0)
    aggregate = (median_support == 0) | (median_support > args.max_content)

    m_abs, m_signed = global_reliance(A_m)
    g_abs, g_signed = global_reliance(A_g)
    confirmed = set()
    scramble_summary = args.scramble / f"seed-{args.seed}" / "summary.parquet"
    if scramble_summary.exists():
        s = pl.read_parquet(scramble_summary)
        confirmed = set(s.filter((pl.col("kind") == "malconv") & pl.col("confirmed").fill_null(False))["top_feature"].to_list())

    table = pl.DataFrame({
        "feature": names, "aggregate": aggregate, "median_support": median_support,
        "malconv_abs": m_abs, "malconv_signed": m_signed, "gbdt_abs": g_abs, "gbdt_signed": g_signed,
        "scramble_confirmed": [n in confirmed for n in names],
    })
    table.write_parquet(outdir / "features.parquet")

    def correlations(mask: npt.NDArray[np.bool_]) -> dict[str, float]:
        return {
            "spearman_abs": float(stats.spearmanr(m_abs[mask], g_abs[mask]).statistic),
            "spearman_signed": float(stats.spearmanr(m_signed[mask], g_signed[mask]).statistic),
        }

    localizable = ~aggregate
    top_m = set(np.argsort(-m_abs)[:args.top_k].tolist())
    top_g = set(np.argsort(-g_abs)[:args.top_k].tolist())
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "num_files": int(A_m.shape[0]), "num_features": num_features,
        "num_aggregate": int(aggregate.sum()),
        "all_features": correlations(np.ones(num_features, dtype=bool)),
        "localizable_features": correlations(localizable),
        f"top_{args.top_k}_shared": sorted(names[i] for i in top_m & top_g),
        f"top_{args.top_k}_malconv_only": sorted(names[i] for i in top_m - top_g),
        f"top_{args.top_k}_gbdt_only": sorted(names[i] for i in top_g - top_m),
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))

    print(f"\nTop {args.top_k} features by mean |attribution|, each model (A = aggregate, C = scramble-confirmed):")
    for model, abs_, signed in (("MalConv", m_abs, m_signed), ("GBDT", g_abs, g_signed)):
        print(f"\n--- {model} ---")
        for i in np.argsort(-abs_)[:args.top_k]:
            flags = ("A" if aggregate[i] else " ") + ("C" if names[i] in confirmed else " ")
            print(f"  {abs_[i]:7.4f}  signed {signed[i]:+7.4f}  supp {int(median_support[i]):5d}  {flags}  {names[i]}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
