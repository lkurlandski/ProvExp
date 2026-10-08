"""
PB1 pilot: problem-space faithfulness and cost of pulled-back explanations vs. direct occlusion and random
(docs/pb1_plan.md).

For each file, every method ranks the file's bytes, and deletion curves ablate the top-ranked bytes up to log-spaced
budgets, re-extract the features, and re-score the models. (Insertion was dropped after the pilot; see
docs/pb1_pilot.md.) Ablation is PE-aware (protected header fields,
header bytes zero-filled), and every ablated file is verified; perturbations that fail verification are recorded and
excluded from the curves.

Methods (each ranks bytes by evidence for the model's predicted class, sign(f(x)) times the score):
    pullback:{explainer}        the instrumented pullback of a feature explanation, per byte
    pullback_abs:{explainer}    the same, ranked by magnitude regardless of sign (tests whether the overshoot beyond
                                full ablation comes from keeping the opposing evidence; docs/pb1_pilot.md)
    pullback_k:{explainer}      the same, coarsened to the K windows (separates granularity from information)
    pullback_k{J}:{explainer}   the same, coarsened to J windows, for each J in --sweep_windows
    blackbox:{explainer}        the pullback through the provenance estimated from the occlusion run (K windows)
    occlusion                   the drop in the model's log-odds when each of K windows is occluded
    occlusion_k{J}              the same with J windows, for each J in --sweep_windows (the cost-faithfulness curve)
    kernelshap_windows          KernelSHAP over the K windows (players: windows; absent: ablated), a second direct
                                problem-space explainer, with --kernelshap_samples coalitions
    random:{seed}               a random order of the K windows (shared by the models)

Outputs, in `{outdir}/seed-{seed}/{fill}[-{header}-header][-{tag}]/`:
    curves.parquet      one row per (file, model, method, curve, budget): the log-odds and whether it is valid
    files.parquet       one row per file: size, protection, log-odds, cost (extractions, seconds), problems
    provenance.npz      per file and feature: total variation distance between the instrumented and black-box
                        provenance coarsened to windows, which features each finds attributable, and the overlap and
                        ambiguity of each feature under each of them at the window level (`overlap_instrumented`,
                        `overlap_blackbox`, `ambiguity_instrumented`, `ambiguity_blackbox`)
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
from provexp.ablation import coarsen_provenance
from provexp.ablation import element_order
from provexp.ablation import estimate_provenance
from provexp.ablation import window_edges
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import kernelshap
from provexp.explain.feature import mlp_function
from provexp.featuresets.ember2024.ablation import HeaderFill
from provexp.featuresets.ember2024.ablation import Protection
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.mlp import Standardize
from provexp.models.mlp import build_mlp


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
# The explainers of each model; those without saved explanations are skipped.
MODELS = {
    "gbdt": ["treeshap_path", "treeshap_interventional", "kernelshap_gbdt"],
    "mlp": ["integrated_gradients", "kernelshap_mlp"],
}

FloatArray = npt.NDArray[np.float64]

# The cost of one feature extraction, seconds = SECONDS_PER_EXTRACTION + SECONDS_PER_EXTRACTION_PER_MB * megabytes,
# fitted on the 2026-10-08 baselines run (100 files, 0.005-4 MB). It predicts the total work well (63.0 vs. 63.1
# worker-hours) but a single file can take twice its prediction, so the wall-clock estimate is a lower bound. Used
# only to order the tasks, to predict the runtime, and to weight the progress bar.
SECONDS_PER_EXTRACTION = 0.040
SECONDS_PER_EXTRACTION_PER_MB = 0.251
BoolArray = npt.NDArray[np.bool_]

_STATE: dict[str, Any] = {}


class Timeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise Timeout()


def _init_worker(model_files: dict[str, Path], d: int) -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)
    torch.set_num_threads(1)
    models: dict[str, Callable[[FloatArray], FloatArray]] = {}
    if "gbdt" in model_files:
        models["gbdt"] = gbdt_function(lgb.Booster(model_file=str(model_files["gbdt"])))
    if "mlp" in model_files:
        mlp = build_mlp(Standardize(torch.zeros(d), torch.ones(d)))
        mlp.load_state_dict(torch.load(model_files["mlp"], map_location="cpu", weights_only=True))
        models["mlp"] = mlp_function(mlp.double().eval())
    _STATE["extractor"] = PEFeatureExtractor()
    _STATE["models"] = models


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
        z = ablate(self.data, which, self.protection.mask, self.fill, rng, self.protection.header, self.protection.header_values)
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


def occlude(scorer: Scorer, m: int, num_windows: int) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64], FloatArray, dict[str, FloatArray], int]:
    """
    Occlude each of `num_windows` windows: one extraction each.

    Returns:
        The window edges, the window of each element, the features of each occluded file (the original's where
        verification fails, i.e., treated as no change), the occlusion score of each window per model (the drop in
        the log-odds), and the number of windows that failed verification.
    """
    f0, _ = scorer.scores(np.zeros(m, dtype=np.bool_))
    x0, _ = scorer.features(np.zeros(m, dtype=np.bool_))
    edges = window_edges(m, num_windows)
    K = edges.shape[0] - 1
    window = np.repeat(np.arange(K), np.diff(edges))
    X_occluded = np.zeros((K, x0.shape[0]))
    occlusion = {name: np.zeros(K) for name in scorer.models}
    invalid = 0
    for k in range(K):
        x, problem = scorer.features(window == k)
        if problem is not None:
            invalid += 1
            X_occluded[k] = x0
            continue
        X_occluded[k] = x
        for name, f in scorer.models.items():
            occlusion[name][k] = f0[name] - float(f(x[None, :])[0])
    return edges, window, X_occluded, occlusion, invalid


def kernelshap_windows(scorer: Scorer, window: npt.NDArray[np.int64], K: int, nsamples: int, seed: int) -> tuple[dict[str, FloatArray], int]:
    """
    KernelSHAP over windows: the players are the K windows, a coalition keeps its windows and ablates the rest, and the
    reference is the fully ablated file. Coalitions that fail verification score as the original file (no change).

    Returns:
        The Shapley value of each window per model (evidence for malware), and the number of coalitions that failed
        verification.
    """
    f0, _ = scorer.scores(np.zeros(window.shape[0], dtype=np.bool_))
    failed = 0
    values: dict[str, FloatArray] = {}
    for name in scorer.models:
        def f(Z: npt.NDArray[np.floating], name: str = name) -> FloatArray:
            nonlocal failed
            out = np.zeros(Z.shape[0])
            for i, z in enumerate(Z):
                s, ok = scorer.scores(~(z > 0.5)[window])
                if not ok:
                    failed += 1
                out[i] = s[name] if ok else f0[name]
            return out
        # The same seed draws the same coalitions for every model, so later models hit the scorer's cache.
        values[name] = kernelshap(f, np.ones((1, K)), np.zeros((1, K)), nsamples=nsamples, seed=seed)[0]
    return values, failed // len(scorer.models)


def process_file(data: bytes, explanations: dict[str, FloatArray], num_windows: int, fill: Fill, header: HeaderFill, seed: int, budgets: tuple[float, ...], sweep_windows: tuple[int, ...] = (), kernelshap_samples: int = 0) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    m = len(data)
    t_0 = time.perf_counter()
    protection = protect(data, header=header)
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

    # Occlusion of K windows: one extraction each, shared by the models and the black-box provenance.
    t_0 = time.perf_counter()
    edges, window, X_occluded, occlusion, invalid_windows = occlude(scorer, m, num_windows)
    K = edges.shape[0] - 1
    t_occlusion = time.perf_counter() - t_0
    occlusion_extractions = scorer.extractions
    blackbox = estimate_provenance(x0, X_occluded, edges)
    del X_occluded

    # The cost-faithfulness sweep: occlusion at other window counts (the extractions are counted separately).
    sweep: dict[int, tuple[int, npt.NDArray[np.int64], dict[str, FloatArray]]] = {}
    sweep_info: dict[str, Any] = {}
    for J in sweep_windows:
        if J == num_windows:
            continue
        before = scorer.extractions
        t_0 = time.perf_counter()
        edges_j, window_j, _, occlusion_j, invalid_j = occlude(scorer, m, J)
        sweep[J] = (edges_j.shape[0] - 1, window_j, occlusion_j)
        sweep_info |= {
            f"seconds_occlusion_k{J}": time.perf_counter() - t_0,
            # Counted like occlusion_extractions: the windows, the original, and the fully ablated file (cached here).
            f"occlusion_extractions_k{J}": scorer.extractions - before + 2,
            f"invalid_windows_k{J}": invalid_j,
            f"num_windows_k{J}": edges_j.shape[0] - 1,
        }

    # KernelSHAP over the K windows.
    shapley: dict[str, FloatArray] = {}
    if kernelshap_samples > 0:
        before = scorer.extractions
        t_0 = time.perf_counter()
        shapley, failed_coalitions = kernelshap_windows(scorer, window, K, kernelshap_samples, seed)
        sweep_info |= {
            "seconds_kernelshap_windows": time.perf_counter() - t_0,
            "kernelshap_windows_extractions": scorer.extractions - before + 2,
            "kernelshap_windows_failed": failed_coalitions,
        }

    # Rankings: element orders per model and method.
    t_0 = time.perf_counter()
    orders: dict[str, dict[str, npt.NDArray[np.int64]]] = {name: {} for name in scorer.models}
    for name in scorer.models:
        explainers = MODELS[name]
        for e in explainers:
            if e not in explanations:
                continue
            b = prov.pullback(explanations[e])[:m]
            orders[name][f"pullback:{e}"] = element_order(b, direction[name])
            orders[name][f"pullback_abs:{e}"] = element_order(np.abs(b))
            per_window = np.bincount(window, weights=b, minlength=K)
            orders[name][f"pullback_k:{e}"] = element_order(per_window[window], direction[name])
            for J, (K_j, window_j, _) in sweep.items():
                per_window_j = np.bincount(window_j, weights=b, minlength=K_j)
                orders[name][f"pullback_k{J}:{e}"] = element_order(per_window_j[window_j], direction[name])
            orders[name][f"blackbox:{e}"] = element_order(blackbox.pullback(explanations[e])[:m], direction[name])
        # Occlusion scores are already the evidence for malware (f0 - f(occluded)), and so are the Shapley values.
        orders[name]["occlusion"] = element_order(occlusion[name][window], direction[name])
        for J, (_, window_j, occlusion_j) in sweep.items():
            orders[name][f"occlusion_k{J}"] = element_order(occlusion_j[name][window_j], direction[name])
        if name in shapley:
            orders[name]["kernelshap_windows"] = element_order(shapley[name][window], direction[name])
    t_rank = time.perf_counter() - t_0
    rng = np.random.default_rng(seed)
    random_orders = {f"random:{r}": element_order(rng.permutation(K).astype(np.float64)[window]) for r in range(3)}

    records: list[dict[str, Any]] = []

    def curves(order: npt.NDArray[np.int64], models: list[str], method: str) -> None:
        for budget, mask in zip(budgets, budget_masks(order, protection.mask, budgets)):
            s, ok = scorer.scores(mask)
            for name in models:
                records.append({"model": name, "method": method, "curve": "deletion", "budget": budget, "log_odds": s[name], "valid": ok})

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
    } | sweep_info | {f"log_odds:{name}": v for name, v in f0.items()} | {f"log_odds_ablated:{name}": v for name, v in f_ablated.items()}
    # The statistics of both at the window level (docs/cp_plan.md, CP.3): do they differ where T1 says?
    coarse = {"instrumented": coarsen_provenance(prov, edges), "blackbox": coarsen_provenance(blackbox, edges)}
    arrays = {"tv": tv.astype(np.float32), "attributable": attributable, "estimated": estimated}
    for name, Pk in coarse.items():
        arrays[f"overlap_{name}"] = Pk.overlap().per_feature.astype(np.float32)
        arrays[f"ambiguity_{name}"] = Pk.ambiguity().per_feature.astype(np.float32)
    return records, info, arrays


def process_shard(shard: int, samples: list[dict[str, Any]], dbdir: Path, explanations: dict[str, FloatArray], num_windows: int, fill: Fill, header: HeaderFill, seed: int, budgets: tuple[float, ...], timeout: int, sweep_windows: tuple[int, ...], kernelshap_samples: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, Any]]]:
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
            recs, info, arr = process_file(sample.data, {e: A[i] for e, A in explanations.items()}, num_windows, fill, header, seed + meta["index"], budgets, sweep_windows, kernelshap_samples)
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


def extractions_per_file(num_windows: int, sweep_windows: tuple[int, ...], kernelshap_samples: int, budgets: tuple[float, ...]) -> int:
    """
    How many feature extractions one file costs, which is known exactly before a run: the original and the fully
    ablated file, one per window of every occlusion run, the KernelSHAP coalitions, and one per budget and method.
    """
    windows = (num_windows, *(J for J in sweep_windows if J != num_windows))
    per_curve = len(budgets) * (3 + 3 * (1 + len(sweep_windows)))  # Rough: the methods that produce curves.
    return 2 + sum(J for J in windows) + kernelshap_samples + per_curve


def predict_seconds(sizes: npt.NDArray[np.int64], extractions: int) -> FloatArray:
    """The predicted seconds per file, from its size and the number of extractions (see SECONDS_PER_EXTRACTION)."""
    megabytes = np.asarray(sizes, dtype=np.float64) / 1e6
    return np.asarray(extractions * (SECONDS_PER_EXTRACTION + SECONDS_PER_EXTRACTION_PER_MB * megabytes), dtype=np.float64)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="PB1 pilot: problem-space faithfulness and cost.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained models.")
    parser.add_argument("--num_files", type=int, default=100, help="Files per run, balanced by label.")
    parser.add_argument("--num_windows", type=int, default=256)
    parser.add_argument("--fill", type=str, choices=["zeros", "random"], default="zeros")
    parser.add_argument("--header", type=str, choices=["zeros", "typical"], default="zeros", help="How ablation fills header fields (level 2: zeros; level 3: typical values).")
    parser.add_argument("--classifiers", type=str, nargs="+", choices=list(MODELS), default=["gbdt"], help="The models to evaluate (the GBDT first; PLAN.md, model scope).")
    parser.add_argument("--sweep_windows", type=int, nargs="*", default=[], help="Further window counts for occlusion and the coarsened pullback (the cost-faithfulness curve), e.g., 64 1024 4096.")
    parser.add_argument("--kernelshap_samples", type=int, default=0, help="Coalitions for KernelSHAP over the windows (0: skip).")
    parser.add_argument("--tag", type=str, default="", help="A suffix for the output directory.")
    parser.add_argument("--files", type=Path, default=None, help="Reuse the files of an earlier run (its files.parquet); --num_files then takes the first files per label.")
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
    variant = args.fill if args.header == "zeros" else f"{args.fill}-{args.header}-header"
    variant += f"-{args.tag}" if args.tag else ""
    if any(J < 1 for J in args.sweep_windows) or args.kernelshap_samples < 0:
        raise ValueError(f"Invalid --sweep_windows {args.sweep_windows} or --kernelshap_samples {args.kernelshap_samples}.")
    models = {name: es for name, es in MODELS.items() if name in args.classifiers}
    outdir = args.outdir / f"seed-{args.seed}" / variant
    outdir.mkdir(parents=True, exist_ok=True)
    explainers = sorted(e for es in models.values() for e in es if (indir / f"{e}.npy").exists())
    explanations = {e: np.load(indir / f"{e}.npy") for e in explainers}
    report = json.loads((indir / "report.json").read_text())

    # The files: balanced by label, excluding files on which an explainer violates local accuracy (see
    # treeshap_interventional), whose explanations are not trustworthy.
    samples = pl.read_parquet(indir / "samples.parquet").with_row_index("index")
    bad = np.zeros(samples.height, dtype=np.bool_)
    for e in explainers:
        if "baseline_output" in report[e]:
            model = next(name for name, es in models.items() if e in es)
            out = samples[f"{model}_log_odds"].to_numpy()
            bad |= np.abs(explanations[e].sum(axis=1) - (out - report[e]["baseline_output"])) > 1e-2
    samples = samples.filter(~pl.Series(bad))
    per_label = args.num_files // 2
    if args.files is not None:
        names = pl.read_parquet(args.files)["name"]
        samples = samples.filter(pl.col("name").is_in(names.implode()))
        if samples.height != names.len():
            raise RuntimeError(f"{names.len() - samples.height} files of {args.files.as_posix()} are not in the explanation set or are excluded.")
        samples = pl.concat([samples.filter(pl.col("label") == lab).sort("index").head(per_label) for lab in (0, 1)])
    else:
        samples = pl.concat([samples.filter(pl.col("label") == lab).sample(per_label, seed=args.sample_seed) for lab in (0, 1)])
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left").sort("index")
    for e, A in explanations.items():
        if not np.all(np.isfinite(A[samples["index"].to_numpy()])):
            raise RuntimeError(f"{e} has no explanations for some selected files; compute it for them (explain.py --subset).")

    # The cost of a file is dominated by its size times the number of extractions, both known up front. Tasks run
    # longest-first, so that the long poles start immediately (shorter wall-clock, and an honest ETA).
    per_file = extractions_per_file(args.num_windows, tuple(args.sweep_windows), args.kernelshap_samples, BUDGETS)
    sizes = pl.read_parquet(args.explanation_set).select("name", "size")
    samples = samples.join(sizes, on="name", how="left").with_columns(pl.col("size").fill_null(0))
    tasks = []
    weights = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        idx = group["index"].to_numpy()
        weights.append(float(predict_seconds(group["size"].to_numpy(), per_file).sum()))
        tasks.append((
            int(shard),
            group.select("index", "name", "label", "position").to_dicts(),
            args.db,
            {e: A[idx] for e, A in explanations.items()},
            args.num_windows,
            args.fill,
            args.header,
            args.sample_seed,
            BUDGETS,
            args.timeout,
            tuple(args.sweep_windows),
            args.kernelshap_samples,
        ))
    order = np.argsort(-np.asarray(weights))
    tasks = [tasks[i] for i in order]
    weights = [weights[i] for i in order]
    total = sum(weights)
    print(f"Explainers: {explainers}.", flush=True)
    print(f"Cost: {per_file} extractions per file; predicted {total / 3600:.1f} worker-hours and at least "
          f"{max(total / args.num_workers, max(weights)) / 3600:.1f} h wall-clock on {args.num_workers} workers "
          f"(the longest single task, {max(weights) / 3600:.1f} h, bounds the run; a single file can take twice its "
          f"prediction, so treat this as a floor).", flush=True)
    print(f"PB1: {samples.height} files ({int(bad.sum())} excluded for local accuracy), models {list(models)}, {args.num_windows} windows (sweep {args.sweep_windows}), KernelSHAP over windows {args.kernelshap_samples}, fill {args.fill}, header {args.header}.", flush=True)

    t_0 = time.time()
    records: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    arrays: dict[int, dict[str, Any]] = {}
    d = next(iter(explanations.values())).shape[1]
    files_of = {"gbdt": args.models / "gbdt" / f"seed-{args.seed}" / "model.txt", "mlp": args.models / "mlp" / f"seed-{args.seed}" / "model.pt"}
    initargs = ({name: files_of[name] for name in models}, d)
    done = 0.0
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=initargs) as pool:
        # The progress bar counts predicted seconds of work, not files, because files differ by three orders of
        # magnitude; its percentage and ETA are then meaningful. Every file is also logged as it finishes.
        bar = tqdm(total=round(total), unit="s", unit_scale=True, desc="work", smoothing=0.0, mininterval=30)
        with bar:
            for recs, inf, arr in pool.imap_unordered(_star, tasks):
                records.extend(recs)
                infos.extend(inf)
                arrays.update(arr)
                for one in inf:
                    predicted = float(predict_seconds(np.asarray([one.get("num_elements", 0)]), per_file)[0])
                    done += predicted
                    bar.update(round(predicted))
                    elapsed = (time.time() - t_0) / 60
                    # bar.write, not print: a bare print lands on the bar's line and is lost.
                    bar.write(f"  [{done / total:5.1%} {elapsed:6.1f} min] {one['name'][:16]} "
                              f"{one.get('num_elements', 0) / 1e6:5.2f} MB  {one.get('seconds', float('nan')) / 60:6.1f} min  "
                              f"{one.get('extractions', 0):6d} extractions  {one['status']}")

    pl.DataFrame(records, infer_schema_length=None).write_parquet(outdir / "curves.parquet")
    files = pl.DataFrame(infos, infer_schema_length=None).sort("index")
    files.write_parquet(outdir / "files.parquet")
    order = sorted(arrays)
    stacked: dict[str, Any] = {"index": np.array(order, dtype=np.int64)}
    for key in ("tv", "attributable", "estimated", *(f"{s}_{p}" for s in ("overlap", "ambiguity") for p in ("instrumented", "blackbox"))):
        stacked[key] = np.stack([arrays[i][key] for i in order]) if order else np.zeros((0, d))
    np.savez_compressed(outdir / "provenance.npz", **stacked)

    ok = files.filter(pl.col("status") == "ok")
    curves_table = pl.DataFrame(records, infer_schema_length=None) if records else pl.DataFrame({"valid": []})
    summary = {
        "seed": args.seed,
        "explainers": explainers,
        "classifiers": list(models),
        "sweep_windows": args.sweep_windows,
        "kernelshap_samples": args.kernelshap_samples,
        "fill": args.fill,
        "header": args.header,
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
