"""
E1 pilot: problem-space faithfulness and cost of pulled-back explanations vs. direct occlusion and random
(docs/plan_e1.md).

For each file, every method ranks the file's bytes, and deletion and insertion curves ablate the top-ranked bytes up to
log-spaced budgets, re-extract the features, and re-score the models. Ablation is PE-aware (protected header fields,
header bytes zero-filled), and every ablated file is verified; perturbations that fail verification are recorded and
excluded from the curves.

Methods (each ranks bytes by evidence for the model's predicted class, sign(f(x)) times the score):
    pullback:{explainer}        the instrumented pullback of a feature explanation, per byte
    pullback_k:{explainer}      the same, coarsened to the K windows (separates granularity from information)
    blackbox:{explainer}        the pullback through the provenance estimated from the occlusion run (K windows)
    occlusion                   the drop in the model's log-odds when each of K windows is occluded
    random:{seed}               a random order of the K windows (shared by both models)

Outputs, in `{outdir}/seed-{seed}/{fill}/`:
    curves.parquet      one row per (file, model, method, curve, budget): the log-odds and whether it is valid
    files.parquet       one row per file: size, protection, log-odds, cost (extractions, seconds), problems
    provenance.npz      per file and feature: total variation distance between the instrumented and black-box
                        provenance coarsened to windows, and which features each finds attributable
    report.json         the configuration, exclusions, verification failures, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16
"""

from argparse import ArgumentParser
from collections.abc import Callable
import hashlib
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

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
import torch
from tqdm import tqdm

from provexp.ablation import BUDGETS
from provexp.ablation import Fill
from provexp.ablation import ablate
from provexp.ablation import budget_masks
from provexp.ablation import coarsen
from provexp.ablation import element_order
from provexp.ablation import estimate_provenance
from provexp.ablation import window_edges
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import mlp_function
from provexp.featuresets.ember2024.ablation import Protection
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.mlp import Standardize
from provexp.models.mlp import build_mlp


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
MODELS = {"gbdt": ["treeshap_path", "treeshap_interventional"], "mlp": ["integrated_gradients"]}

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]

_STATE: dict[str, Any] = {}


class Timeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise Timeout()


def _init_worker(gbdt_file: Path, mlp_file: Path, d: int) -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)
    torch.set_num_threads(1)
    mlp = build_mlp(Standardize(torch.zeros(d), torch.ones(d)))
    mlp.load_state_dict(torch.load(mlp_file, map_location="cpu", weights_only=True))
    _STATE["extractor"] = PEFeatureExtractor()
    _STATE["models"] = {
        "gbdt": gbdt_function(lgb.Booster(model_file=str(gbdt_file))),
        "mlp": mlp_function(mlp.double().eval()),
    }


################################################################################
# Per File
################################################################################


class Scorer:
    """
    Extracts, verifies, and scores ablated versions of one file, caching by content and counting extractions.
    """

    def __init__(self, data: bytes, protection: Protection, fill: Fill, seed: int) -> None:
        self.data = data
        self.protection = protection
        self.fill: Fill = fill
        self.seed = seed
        self.extractor: PEFeatureExtractor = _STATE["extractor"]
        self.models: dict[str, Callable[[FloatArray], FloatArray]] = _STATE["models"]
        self.cache: dict[bytes, tuple[FloatArray, Optional[str]]] = {}
        self.extractions = 0
        self.problems: dict[str, int] = {}

    def features(self, which: BoolArray) -> tuple[FloatArray, Optional[str]]:
        """The features of the file with `which` ablated, and the verification problem, if any."""
        key = hashlib.blake2b(np.packbits(which).tobytes(), digest_size=16).digest()
        if key in self.cache:
            return self.cache[key]
        # The same mask always gets the same random fill.
        rng = np.random.default_rng([self.seed, int.from_bytes(key[:8], "little")])
        z = ablate(self.data, which, self.protection.mask, self.fill, rng, zero_only=self.protection.header)
        self.extractions += 1
        try:
            x = np.asarray(self.extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
            problem = verify(self.protection, self.data, z, float(x[IS_PE]))
        except Exception as err:
            x, problem = np.full(0, np.nan), f"extraction failed: {type(err).__name__}"
        if problem is not None:
            self.problems[problem] = self.problems.get(problem, 0) + 1
        self.cache[key] = (x, problem)
        return x, problem

    def scores(self, which: BoolArray) -> tuple[dict[str, float], bool]:
        x, problem = self.features(which)
        if problem is not None:
            return {name: float("nan") for name in self.models}, False
        return {name: float(f(x[None, :])[0]) for name, f in self.models.items()}, True


def process_file(data: bytes, explanations: dict[str, FloatArray], num_windows: int, fill: Fill, seed: int, budgets: tuple[float, ...]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    m = len(data)
    t_0 = time.perf_counter()
    protection = protect(data)
    t_protect = time.perf_counter() - t_0
    scorer = Scorer(data, protection, fill, seed)
    none = np.zeros(m, dtype=np.bool_)
    unprotected = ~protection.mask

    # The instrumented provenance: the cost of a pullback is this one extraction plus the pullback itself.
    t_0 = time.perf_counter()
    x0, prov = scorer.extractor.feature_vector_with_provenance(data)
    t_instrumented = time.perf_counter() - t_0
    f0, _ = scorer.scores(none)
    direction = {name: float(np.sign(v)) or 1.0 for name, v in f0.items()}
    f_ablated, ok_ablated = scorer.scores(unprotected)

    # Occlusion of K windows: one extraction each, shared by both models and the black-box provenance.
    edges = window_edges(m, num_windows)
    K = edges.shape[0] - 1
    window = np.repeat(np.arange(K), np.diff(edges))
    X_occluded = np.zeros((K, x0.shape[0]))
    occlusion = {name: np.zeros(K) for name in scorer.models}
    t_0 = time.perf_counter()
    invalid_windows = 0
    for k in range(K):
        which = window == k
        x, problem = scorer.features(which)
        if problem is not None:
            invalid_windows += 1
            X_occluded[k] = x0  # Treated as no change.
            continue
        X_occluded[k] = x
        for name, f in scorer.models.items():
            occlusion[name][k] = f0[name] - float(f(x[None, :])[0])
    t_occlusion = time.perf_counter() - t_0
    occlusion_extractions = scorer.extractions
    blackbox = estimate_provenance(x0, X_occluded, edges)

    # Rankings: element orders per model and method.
    t_0 = time.perf_counter()
    orders: dict[str, dict[str, npt.NDArray[np.int64]]] = {name: {} for name in scorer.models}
    for name, explainers in MODELS.items():
        for e in explainers:
            b = prov.pullback(explanations[e])[:m]
            orders[name][f"pullback:{e}"] = element_order(b, direction[name])
            per_window = np.bincount(window, weights=b, minlength=K)
            orders[name][f"pullback_k:{e}"] = element_order(per_window[window], direction[name])
            orders[name][f"blackbox:{e}"] = element_order(blackbox.pullback(explanations[e])[:m], direction[name])
        # Occlusion scores are already the evidence for malware (f0 - f(occluded)).
        orders[name]["occlusion"] = element_order(occlusion[name][window], direction[name])
    t_rank = time.perf_counter() - t_0
    rng = np.random.default_rng(seed)
    random_orders = {f"random:{r}": element_order(rng.permutation(K).astype(np.float64)[window]) for r in range(3)}

    records: list[dict[str, Any]] = []

    def curves(order: npt.NDArray[np.int64], models: list[str], method: str) -> None:
        for budget, mask in zip(budgets, budget_masks(order, protection.mask, budgets)):
            for curve, which in (("deletion", mask), ("insertion", unprotected & ~mask)):
                s, ok = scorer.scores(which)
                for name in models:
                    records.append({"model": name, "method": method, "curve": curve, "budget": budget, "log_odds": s[name], "valid": ok})

    for name in scorer.models:
        for method, order in orders[name].items():
            curves(order, [name], method)
    for method, order in random_orders.items():
        curves(order, list(scorer.models), method)

    # The black-box provenance against the instrumented one, coarsened to the same windows.
    P = coarsen(prov, edges)[:K]
    Q = coarsen(blackbox, edges)[:K]
    attributable = P.sum(axis=0) > 0
    estimated = Q.sum(axis=0) > 0
    both = attributable & estimated
    tv = np.full(x0.shape[0], np.nan)
    tv[both] = 0.5 * np.abs(P[:, both] / P[:, both].sum(axis=0) - Q[:, both] / Q[:, both].sum(axis=0)).sum(axis=0)

    info = {
        "num_elements": m,
        "num_windows": K,
        "protected_bytes": int(protection.mask.sum()),
        "file_fields": ",".join(sorted(protection.file_fields)),
        "seconds_protect": t_protect,
        "seconds_instrumented": t_instrumented,
        "seconds_occlusion": t_occlusion,
        "seconds_rank": t_rank,
        "occlusion_extractions": occlusion_extractions,
        "extractions": scorer.extractions,
        "invalid_windows": invalid_windows,
        "fully_ablated_valid": ok_ablated,
        "problems": json.dumps(scorer.problems),
    } | {f"log_odds:{name}": v for name, v in f0.items()} | {f"log_odds_ablated:{name}": v for name, v in f_ablated.items()}
    arrays = {"tv": tv.astype(np.float32), "attributable": attributable, "estimated": estimated}
    return records, info, arrays


def process_shard(shard: int, samples: list[dict[str, Any]], dbdir: Path, explanations: dict[str, FloatArray], num_windows: int, fill: Fill, seed: int, budgets: tuple[float, ...], timeout: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    records: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    arrays: dict[int, dict[str, Any]] = {}
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        i = wanted[position]
        meta = samples[i]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"], "label": meta["label"]}
        t_0 = time.perf_counter()
        signal.alarm(timeout)
        try:
            recs, info, arr = process_file(sample.data, {e: A[i] for e, A in explanations.items()}, num_windows, fill, seed + meta["index"], budgets)
            records.extend(base | r for r in recs)
            infos.append(base | {"status": "ok", "error": "", "seconds": time.perf_counter() - t_0} | info)
            arrays[meta["index"]] = arr
        except Timeout:
            infos.append(base | {"status": "timeout", "error": f"Exceeded {timeout} seconds."})
        except ValueError as err:
            infos.append(base | {"status": "unprotectable", "error": str(err)[:300]})
        except Exception as err:
            infos.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    return records, infos, arrays


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="E1 pilot: problem-space faithfulness and cost.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained models.")
    parser.add_argument("--num_files", type=int, default=100, help="Files per run, balanced by label.")
    parser.add_argument("--num_windows", type=int, default=256)
    parser.add_argument("--fill", type=str, choices=["zeros", "random"], default="zeros")
    parser.add_argument("--sample_seed", type=int, default=0)
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "e1")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=3600, help="The maximum number of seconds per file.")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    indir = args.explanations / f"seed-{args.seed}"
    outdir = args.outdir / f"seed-{args.seed}" / args.fill
    outdir.mkdir(parents=True, exist_ok=True)
    explainers = sorted({e for es in MODELS.values() for e in es})
    explanations = {e: np.load(indir / f"{e}.npy") for e in explainers}
    report = json.loads((indir / "report.json").read_text())

    # The files: balanced by label, excluding files on which an explainer violates local accuracy (see
    # treeshap_interventional), whose explanations are not trustworthy.
    samples = pl.read_parquet(indir / "samples.parquet").with_row_index("index")
    bad = np.zeros(samples.height, dtype=np.bool_)
    for e in explainers:
        if "baseline_output" in report[e]:
            out = samples["gbdt_log_odds" if e.startswith("treeshap") else "mlp_log_odds"].to_numpy()
            bad |= np.abs(explanations[e].sum(axis=1) - (out - report[e]["baseline_output"])) > 1e-2
    samples = samples.filter(~pl.Series(bad))
    per_label = args.num_files // 2
    samples = pl.concat([samples.filter(pl.col("label") == lab).sample(per_label, seed=args.sample_seed) for lab in (0, 1)])
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left").sort("index")

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        idx = group["index"].to_numpy()
        tasks.append((
            int(shard),
            group.select("index", "name", "label", "position").to_dicts(),
            args.db,
            {e: A[idx] for e, A in explanations.items()},
            args.num_windows,
            args.fill,
            args.sample_seed,
            BUDGETS,
            args.timeout,
        ))
    print(f"E1: {samples.height} files ({int(bad.sum())} excluded for local accuracy), {args.num_windows} windows, fill {args.fill}.", flush=True)

    t_0 = time.time()
    records: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    arrays: dict[int, dict[str, Any]] = {}
    d = next(iter(explanations.values())).shape[1]
    initargs = (args.models / "gbdt" / f"seed-{args.seed}" / "model.txt", args.models / "mlp" / f"seed-{args.seed}" / "model.pt", d)
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=initargs) as pool:
        for recs, inf, arr in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks)):
            records.extend(recs)
            infos.extend(inf)
            arrays.update(arr)

    pl.DataFrame(records, infer_schema_length=None).write_parquet(outdir / "curves.parquet")
    files = pl.DataFrame(infos, infer_schema_length=None).sort("index")
    files.write_parquet(outdir / "files.parquet")
    order = sorted(arrays)
    stacked: dict[str, Any] = {"index": np.array(order, dtype=np.int64)}
    for key in ("tv", "attributable", "estimated"):
        stacked[key] = np.stack([arrays[i][key] for i in order]) if order else np.zeros((0, d))
    np.savez_compressed(outdir / "provenance.npz", **stacked)

    ok = files.filter(pl.col("status") == "ok")
    curves_table = pl.DataFrame(records, infer_schema_length=None) if records else pl.DataFrame({"valid": []})
    summary = {
        "seed": args.seed,
        "fill": args.fill,
        "num_windows": args.num_windows,
        "budgets": list(BUDGETS),
        "num_files": samples.height,
        "excluded_for_local_accuracy": int(bad.sum()),
        "status": files.group_by("status").len().to_dicts(),
        "failed": files.filter(pl.col("status") != "ok").select("name", "status", "error").to_dicts(),
        "invalid_curve_points": int((~curves_table["valid"]).sum()) if curves_table.height else 0,
        "curve_points": curves_table.height,
        "files_with_invalid_windows": int((ok["invalid_windows"] > 0).sum()) if ok.height else 0,
        "files_with_file_specific_fields": int((ok["file_fields"] != "").sum()) if ok.height else 0,
        "median_seconds_per_file": float(ok["seconds"].median() or 0.0) if ok.height else 0.0,  # type: ignore[arg-type]
        "minutes": (time.time() - t_0) / 60,
    }
    invalid_rate = summary["invalid_curve_points"] / max(summary["curve_points"], 1)
    if invalid_rate > 0.01:
        summary["warning"] = f"{invalid_rate:.1%} of the curve points failed verification; inspect before analyzing."
    (outdir / "report.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary | {"failed": summary["failed"][:5]}, indent=2), flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
