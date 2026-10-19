"""
PB1 pilot: problem-space faithfulness and cost of pulled-back explanations vs. direct occlusion and random
(docs/experiments/pb1.md).

For each file, every method ranks the file's bytes, and deletion curves ablate the top-ranked bytes up to log-spaced
budgets, re-extract the features, and re-score the models. (Insertion was dropped after the pilot; see
docs/experiments/pb1.md.) Ablation is PE-aware (protected header fields,
header bytes zero-filled), and every ablated file is verified; perturbations that fail verification are recorded and
excluded from the curves.

Methods (each ranks bytes by evidence for the model's predicted class, sign(f(x)) times the score):
    pullback:{explainer}        the instrumented pullback of a feature explanation, per byte
    pullback_abs:{explainer}    the same, ranked by magnitude regardless of sign (tests whether the overshoot beyond
                                full ablation comes from keeping the opposing evidence; docs/experiments/pb1.md)
    pullback_k:{explainer}      the same, coarsened to the K windows (separates granularity from information)
    pullback_k{J}:{explainer}   the same, coarsened to J windows, for each J in --sweep_windows
    blackbox:{explainer}        the pullback through the provenance estimated from the occlusion run (K windows)
    occlusion                   the drop in the model's log-odds when each of K windows is occluded
    occlusion_k{J}              the same with J windows, for each J in --sweep_windows (the cost-faithfulness curve)
    kernelshap_windows          KernelSHAP over the K windows (players: windows; absent: ablated), a second direct
                                problem-space explainer, with --kernelshap_samples coalitions
    field_occlusion             with --field_oracle: occlude each parsed PE field and section (one extraction each),
                                rank bytes by their region's drop; the structure-aware upper bound (a defender with a
                                PE parser), which tests whether the byte-level pullback's win is just the read set
    kernelshap_k{J}             KernelSHAP over J windows, with --kernelshap_per_window * J coalitions, for each J in
                                --kernelshap_windows (the same explainer at every budget; added 2026-10-19)
    partition_b{B}              adaptive KernelSHAP: Owen values over a binary hierarchy of --partition_leaves contiguous
                                windows (provexp.explain.feature.owen_partition), at B + 2 queries, for each B in
                                --partition_budgets (matched to occlusion's cost at B windows)
    random:{seed}               a random order of the K windows (shared by the models)

With --pushforward (Section 5.2 of the manuscript, under the shared byte-deletion protocol), feature rankings scored by
deleting the bytes they point to, i.e., ranking bytes by the pullback of the feature explanation:
    pushforward:{source}        a window explanation (occlusion, occlusion_k{J}, kernelshap_windows, kernelshap_k{J},
                                partition_b{B}) pushed forward through P coarsened to its windows, then pulled back
    trend_k{J}:{explainer}      a feature explanation (--trend_explainers) pulled back, summed over J windows, pushed
                                forward, and pulled back: what a J-window source can reach (the reference curve)
    trend_bytes:{explainer}     the same from the bytes
    random_features:{r}         random feature explanations, pulled back (the floor)

Outputs, in `{outdir}/seed-{seed}/{fill}[-{header}-header][-{tag}]/`:
    curves.parquet      one row per (file, model, method, curve, budget): the log-odds and whether it is valid
    files.parquet       one row per file: size, protection, log-odds, cost (extractions, seconds), problems
    provenance.npz      per file and feature: total variation distance between the instrumented and black-box
                        provenance coarsened to windows, which features each finds attributable, and the overlap and
                        ambiguity of each feature under each of them at the window level (`overlap_instrumented`,
                        `overlap_blackbox`, `ambiguity_instrumented`, `ambiguity_blackbox`)
    window_scores.npz   per file, every direct problem-space explanation's per-window scores and the features of
                        the original and fully ablated file, which PF1 pushes forward (docs/experiments/pf1.md); keys
                        `{index}/{key}`, read with `load_window_scores` (see `window_arrays` for the keys)
    report.json         the configuration, exclusions, verification failures, and timing

Parallelism (restructured 2026-10-08): a single file can cost hours (4.1 h of a 6.1 h run), so parallelizing across
files alone caps the wall-clock at the slowest file no matter how many workers there are. The work of one file is
instead split over two passes, both parallel:

    pass 1  the occlusion sweep (one task per file, window count, and chunk of windows) and KernelSHAP over the
            windows (one task per file): about 93% of the work, in tasks of a few minutes each
    pass 2  one task per file: the K-window occlusion, the black-box provenance, the rankings, and the deletion
            curves, which need pass 1's per-window scores

Tasks are self-contained (each loads and protects its file), so nothing is shared between processes; chunk sizes come
from the cost model below, and the results are identical to the single-task version because every mask's random fill
is seeded by the mask itself.

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
from provexp.ablation import window_order
from provexp.ablation import window_pushforward
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import kernelshap
from provexp.explain.feature import mlp_function
from provexp.explain.feature import owen_partition
from provexp.featuresets.ember2024.ablation import HeaderFill
from provexp.featuresets.ember2024.ablation import Protection
from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
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
BAR_FORMAT = "{desc}: {percentage:3.0f}%|{bar}| {n:.0f}/{total:.0f} predicted worker-minutes [{elapsed}<{remaining}]"

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


def field_regions(data: bytes) -> list[tuple[str, int, int]]:
    """
    The byte range [lo, hi) of every parsed PE field and section, for the field-occlusion oracle.

    This is the structure-aware upper bound a defender could build with a PE parser: it names, per file, where each
    header field and each section lives. Sections come first, so that a header field falling inside a section's raw
    data overwrites the section's (coarser) attribution when the oracle assigns scores (process_file). Returns an
    empty list if the file does not parse.
    """
    p = parse(data)
    if p.pe is None or p.layout is None:
        return []
    regions: list[tuple[str, int, int]] = []
    for i, (ptr, size) in enumerate(p.layout.sections):
        lo, hi = max(ptr, 0), min(ptr + size, len(data))
        if hi > lo:
            regions.append((f"section[{i}]", lo, hi))
    for field in header_fields(p.pe):
        lo, hi = max(field.lo, 0), min(field.hi, len(data))
        if hi > lo:
            regions.append((field.key, lo, hi))
    return regions


def field_occlusion(scorer: Scorer, data: bytes, m: int, f0: dict[str, float], unprotected: BoolArray) -> tuple[dict[str, FloatArray], int, int]:
    """
    The field-occlusion oracle: occlude each parsed field and section once (under the same PE-aware operator as the
    deletion curves), and score every byte by the drop its region causes. One extraction per region.

    Args:
        scorer: The file's scorer.
        data: The file's bytes.
        m: The file size.
        f0: The model's log-odds on the unablated file.
        unprotected: The bytes the deletion operator is allowed to change.

    Returns:
        A per-model byte score (the drop of each byte's region, 0 for bytes in no region), the number of regions
        scored, and the extractions this cost.
    """
    scores = {name: np.zeros(m) for name in scorer.models}
    extractions_0 = scorer.extractions
    scored = 0
    for _key, lo, hi in field_regions(data):
        region = np.zeros(m, dtype=np.bool_)
        region[lo:hi] = True
        region &= unprotected
        if not region.any():
            continue
        s, ok = scorer.scores(region)
        if not ok:
            continue
        scored += 1
        for name in scorer.models:
            scores[name][lo:hi] = f0[name] - s[name]
    return scores, scored, scorer.extractions - extractions_0


def occlude_range(scorer: Scorer, window: npt.NDArray[np.int64], f0: dict[str, float], k_lo: int, k_hi: int, features: Optional[FloatArray] = None) -> tuple[dict[str, FloatArray], int]:
    """
    Occlude windows [k_lo, k_hi) of one file: one extraction each.

    Args:
        scorer: The file's scorer.
        window: The window of each element.
        f0: The model's log-odds on the unablated file.
        k_lo: The first window (inclusive).
        k_hi: The last window (exclusive).
        features: Optionally, an array of shape (k_hi - k_lo, d) to fill with the features of each occluded file,
            which the black-box provenance needs. A window that fails verification is left as it is, so the caller
            should prefill the original's features (treating the window as no change).

    Returns:
        The occlusion score of each window per model (the drop in the log-odds), and how many failed verification.
    """
    scores = {name: np.zeros(k_hi - k_lo) for name in scorer.models}
    invalid = 0
    for k in range(k_lo, k_hi):
        x, problem = scorer.features(window == k)
        if problem is not None:
            invalid += 1
            continue
        if features is not None:
            features[k - k_lo] = x
        for name, f in scorer.models.items():
            scores[name][k - k_lo] = f0[name] - float(f(x[None, :])[0])
    return scores, invalid


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
    X_occluded = np.repeat(x0[None, :], K, axis=0)  # A window that fails verification counts as no change.
    occlusion, invalid = occlude_range(scorer, window, f0, 0, K, X_occluded)
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


def load_sample(shard: int, position: int, name: str, dbdir: Path) -> bytes:
    """The bytes of one file of a SimpleDB shard, checked against its name."""
    for at, sample in enumerate(SimpleDBIterator(SimpleDB(dbdir, check=False)).iter(shard)):
        if at == position:
            if sample.name != name:
                raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {name}.")
            return bytes(sample.data)
    raise RuntimeError(f"Shard {shard} has no sample at position {position}.")


def process_occlusion_chunk(task: dict[str, Any]) -> dict[str, Any]:
    """
    Occlude windows [k_lo, k_hi) of `num_windows` for one file (pass 1).

    Returns the per-model score of each window in the chunk, how many failed verification, and the timing. Only the
    scores are returned, never the features, so the payload stays small.
    """
    data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
    m = len(data)
    protection = protect(data, header=task["header"])
    scorer = Scorer(data, protection, task["fill"], task["seed"])
    f0, _ = scorer.scores(np.zeros(m, dtype=np.bool_))
    edges = window_edges(m, task["num_windows"])
    window = np.repeat(np.arange(edges.shape[0] - 1), np.diff(edges))
    k_lo, k_hi = task["k_lo"], min(task["k_hi"], edges.shape[0] - 1)
    t_0 = time.perf_counter()
    scores, invalid = occlude_range(scorer, window, f0, k_lo, k_hi)
    return {
        "kind": "occlude", "index": task["index"], "num_windows": task["num_windows"], "k_lo": k_lo, "k_hi": k_hi,
        "scores": scores, "invalid": invalid, "seconds": time.perf_counter() - t_0,
        "extractions": scorer.extractions, "problems": scorer.problems,
    }


def process_kernelshap(task: dict[str, Any]) -> dict[str, Any]:
    """KernelSHAP over the K windows of one file (pass 1)."""
    data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
    m = len(data)
    protection = protect(data, header=task["header"])
    scorer = Scorer(data, protection, task["fill"], task["seed"])
    edges = window_edges(m, task["num_windows"])
    K = edges.shape[0] - 1
    window = np.repeat(np.arange(K), np.diff(edges))
    t_0 = time.perf_counter()
    values, failed = kernelshap_windows(scorer, window, K, task["kernelshap_samples"], task["seed"])
    return {
        "kind": task["kind"], "index": task["index"], "num_windows": task["num_windows"], "values": values,
        "failed": failed, "seconds": time.perf_counter() - t_0, "extractions": scorer.extractions,
        "problems": scorer.problems,
    }


def partition_windows(scorer: Scorer, window: npt.NDArray[np.int64], K: int, max_evals: int, seed: int) -> tuple[dict[str, FloatArray], int]:
    """
    Adaptive KernelSHAP over K contiguous windows: Owen values over a binary hierarchy of the windows
    (`owen_partition`), with the same game as `kernelshap_windows`: a coalition keeps its windows and ablates the rest,
    and coalitions that fail verification score as the original file.

    Returns:
        The value of each window per model (evidence for malware), and the number of coalitions that failed
        verification.
    """
    f0, _ = scorer.scores(np.zeros(window.shape[0], dtype=np.bool_))
    failed = 0
    values: dict[str, FloatArray] = {}
    for name in scorer.models:
        if K < 2:
            values[name] = np.zeros(K)
            continue

        def f(Z: npt.NDArray[np.floating], name: str = name) -> FloatArray:
            nonlocal failed
            out = np.zeros(Z.shape[0])
            for i, z in enumerate(Z):
                s, ok = scorer.scores(~(z > 0.5)[window])
                if not ok:
                    failed += 1
                out[i] = s[name] if ok else f0[name]
            return out
        # The same seed expands the same groups for every model only if their outputs agree; the scorer's cache still
        # saves the coalitions they share.
        values[name] = owen_partition(f, K, max_evals, seed)
    return values, failed // max(len(scorer.models), 1)


def process_partition(task: dict[str, Any]) -> dict[str, Any]:
    """Adaptive KernelSHAP over --partition_leaves windows of one file at one budget (pass 1)."""
    data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
    m = len(data)
    protection = protect(data, header=task["header"])
    scorer = Scorer(data, protection, task["fill"], task["seed"])
    edges = window_edges(m, task["partition_leaves"])
    K = edges.shape[0] - 1
    window = np.repeat(np.arange(K), np.diff(edges))
    t_0 = time.perf_counter()
    values, failed = partition_windows(scorer, window, K, task["budget"] + 2, task["seed"])
    return {
        "kind": "partition", "index": task["index"], "budget": task["budget"], "values": values, "failed": failed,
        "seconds": time.perf_counter() - t_0, "extractions": scorer.extractions, "problems": scorer.problems,
    }


def process_file(data: bytes, explanations: dict[str, FloatArray], num_windows: int, fill: Fill, header: HeaderFill, seed: int, budgets: tuple[float, ...], sweep: Optional[dict[int, dict[str, FloatArray]]] = None, shapley: Optional[dict[str, FloatArray]] = None, pass1: Optional[dict[str, Any]] = None, tiebreak: bool = True, field_oracle: bool = False, ks_sweep: Optional[dict[int, dict[str, FloatArray]]] = None, partition: Optional[dict[int, dict[str, FloatArray]]] = None, partition_leaves: int = 16384, pushforward: bool = False, trend_explainers: tuple[str, ...] = ()) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """
    Everything for one file that pass 1 did not do: the K-window occlusion, the black-box provenance, the rankings,
    and the deletion curves.

    Args:
        sweep: Per further window count, the per-model occlusion score of each window (from pass 1).
        shapley: Per model, the Shapley value of each of the K windows (from pass 1).
        pass1: Pass 1's timing, extraction counts, and verification failures, to record alongside this pass's.
        tiebreak: Break ties in every ranking by a seeded random permutation (of the bytes for byte-level rankings, of
            the windows for window-level ones), instead of by position in the file. Ties are common: at 4,096 windows,
            occluding most windows changes nothing, so their scores are exactly 0.
        ks_sweep: Per window count J, per model, KernelSHAP's value of each of J windows (from pass 1).
        partition: Per budget B, per model, adaptive KernelSHAP's value of each of `partition_leaves` windows.
        partition_leaves: The number of leaf windows of adaptive KernelSHAP.
        pushforward: Add the feature rankings of Section 5.2 (`pushforward:*`, `trend_*`, `random_features:*`).
        trend_explainers: The feature explanations whose resolution trend to add with `pushforward`.
    """
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

    # The cost-faithfulness sweep and KernelSHAP over the windows came from pass 1; their window maps are recomputed
    # here, deterministically, instead of being shipped.
    windowed: dict[int, tuple[int, npt.NDArray[np.int64], dict[str, FloatArray]]] = {}
    for J, scores in (sweep or {}).items():
        edges_j = window_edges(m, J)
        window_j = np.repeat(np.arange(edges_j.shape[0] - 1), np.diff(edges_j))
        windowed[J] = (edges_j.shape[0] - 1, window_j, scores)
    shapley = shapley or {}
    sweep_info: dict[str, Any] = dict(pass1 or {})

    # Rankings: element orders per model and method. Window-level methods rank whole windows (window_order), so a tie
    # is broken between windows, never by scattering their bytes. The permutations come from their own seeded stream,
    # the same for every model and method at a resolution, so that the random orders below are unchanged.
    t_0 = time.perf_counter()
    ties = np.random.default_rng([seed, 1]) if tiebreak else None

    def permutation(n: int) -> Optional[npt.NDArray[np.int64]]:
        return ties.permutation(n).astype(np.int64) if ties is not None else None

    byte_perm = permutation(m)
    perm_K = permutation(K)
    window_sets: dict[int, tuple[int, npt.NDArray[np.int64], npt.NDArray[np.int64], dict[str, FloatArray], Optional[npt.NDArray[np.int64]]]] = {}
    for J, (K_j, window_j, scores_j) in sorted(windowed.items()):
        window_sets[J] = (K_j, window_j, window_edges(m, J), scores_j, permutation(K_j))
    orders: dict[str, dict[str, npt.NDArray[np.int64]]] = {name: {} for name in scorer.models}
    for name in scorer.models:
        d = direction[name]
        for e in MODELS.get(name, []):
            if e not in explanations:
                continue
            b = prov.pullback(explanations[e])[:m]
            orders[name][f"pullback:{e}"] = element_order(b, d, byte_perm)
            orders[name][f"pullback_abs:{e}"] = element_order(np.abs(b), 1.0, byte_perm)
            orders[name][f"pullback_k:{e}"] = window_order(np.bincount(window, weights=b, minlength=K), edges, d, perm_K)
            for J, (K_j, window_j, edges_j, _, perm_j) in window_sets.items():
                orders[name][f"pullback_k{J}:{e}"] = window_order(np.bincount(window_j, weights=b, minlength=K_j), edges_j, d, perm_j)
            # The black-box provenance is spread evenly over each window, so each window's first element carries its score.
            orders[name][f"blackbox:{e}"] = window_order(blackbox.pullback(explanations[e])[:m][edges[:-1]], edges, d, perm_K)
        # Occlusion scores are already the evidence for malware (f0 - f(occluded)), and so are the Shapley values.
        orders[name]["occlusion"] = window_order(occlusion[name], edges, d, perm_K)
        for J, (K_j, _, edges_j, scores_j, perm_j) in window_sets.items():
            # NOTE: pass 1 allocates J scores, but a file with fewer than J bytes has only K_j windows.
            orders[name][f"occlusion_k{J}"] = window_order(scores_j[name][:K_j], edges_j, d, perm_j)
        if name in shapley:
            orders[name]["kernelshap_windows"] = window_order(shapley[name], edges, d, perm_K)

    # KernelSHAP at every budget and adaptive KernelSHAP (pass 1). A resolution keeps one tie-break permutation for all
    # methods; new resolutions draw theirs after the earlier ones, which therefore stay unchanged.
    perms: dict[int, Optional[npt.NDArray[np.int64]]] = {K: perm_K}
    for K_j, _, _, _, perm_j in window_sets.values():
        perms.setdefault(K_j, perm_j)

    def perm_for(n: int) -> Optional[npt.NDArray[np.int64]]:
        if n not in perms:
            perms[n] = permutation(n)
        return perms[n]

    sources: dict[str, tuple[npt.NDArray[np.int64], dict[str, FloatArray]]] = {"occlusion": (edges, occlusion)}
    for J, (K_j, _, edges_j, scores_j, _) in window_sets.items():
        sources[f"occlusion_k{J}"] = (edges_j, {name: v[:K_j] for name, v in scores_j.items()})
    if shapley:
        sources["kernelshap_windows"] = (edges, shapley)
    for J, values in sorted((ks_sweep or {}).items()):
        edges_j = window_edges(m, J)
        K_j = edges_j.shape[0] - 1
        sources[f"kernelshap_k{J}"] = (edges_j, {name: v[:K_j] for name, v in values.items()})
    if partition:
        edges_l = window_edges(m, partition_leaves)
        K_l = edges_l.shape[0] - 1
        for B, values in sorted(partition.items()):
            sources[f"partition_b{B}"] = (edges_l, {name: v[:K_l] for name, v in values.items()})
    for method, (edges_s, values) in sources.items():
        if method.startswith(("kernelshap_k", "partition_b")):
            for name in scorer.models:
                if name in values:
                    orders[name][method] = window_order(values[name], edges_s, direction[name], perm_for(edges_s.shape[0] - 1))

    # Section 5.2: feature explanations scored by the bytes they point to (their pullback). The pushforward of every
    # window explanation; the resolution trend of the chosen feature explanations; random feature explanations.
    if pushforward:
        features_rng = np.random.default_rng([seed, 2])
        random_features = [features_rng.normal(size=prov.num_features) for _ in range(3)]
        for name in scorer.models:
            d = direction[name]
            for method, (edges_s, values) in sources.items():
                if name in values:
                    a = window_pushforward(prov, edges_s, values[name])
                    orders[name][f"pushforward:{method}"] = element_order(prov.pullback(a)[:m], d, byte_perm)
            for e in trend_explainers:
                if e not in explanations or e not in MODELS.get(name, []):
                    continue
                b = prov.pullback(explanations[e])[:m]
                for J in sorted({num_windows, *windowed}):
                    edges_j = window_edges(m, J)
                    K_j = edges_j.shape[0] - 1
                    a = window_pushforward(prov, edges_j, np.add.reduceat(b, edges_j[:-1]) if m > 0 else np.zeros(K_j))
                    orders[name][f"trend_k{J}:{e}"] = element_order(prov.pullback(a)[:m], d, byte_perm)
                orders[name][f"trend_bytes:{e}"] = element_order(prov.pullback(prov.pushforward(b))[:m], d, byte_perm)
            for r, a in enumerate(random_features):
                orders[name][f"random_features:{r}"] = element_order(prov.pullback(a)[:m], d, byte_perm)
    t_rank = time.perf_counter() - t_0

    # The field-occlusion oracle: a structure-aware direct baseline that occludes each parsed field/section (one
    # extraction each) and ranks bytes by their region's drop. It is the natural upper bound for a direct explainer
    # that knows the parser's read set, so it answers whether the byte-level pullback's win is just that knowledge.
    t_oracle, field_extractions, field_regions_scored = 0.0, 0, 0
    if field_oracle:
        t_0 = time.perf_counter()
        oracle_scores, field_regions_scored, field_extractions = field_occlusion(scorer, data, m, f0, unprotected)
        t_oracle = time.perf_counter() - t_0
        for name in scorer.models:
            orders[name]["field_occlusion"] = element_order(oracle_scores[name], direction[name], byte_perm)
    rng = np.random.default_rng(seed)
    random_orders = {f"random:{r}": window_order(rng.permutation(K).astype(np.float64), edges) for r in range(3)}

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
        "seconds_field_oracle": t_oracle,
        "field_oracle_extractions": field_extractions,
        "field_oracle_regions": field_regions_scored,
        "occlusion_extractions": occlusion_extractions,
        "extractions": scorer.extractions,
        "invalid_windows": invalid_windows,
        "fully_ablated_valid": ok_ablated,
        "problems": json.dumps(scorer.problems),
    } | sweep_info | {f"log_odds:{name}": v for name, v in f0.items()} | {f"log_odds_ablated:{name}": v for name, v in f_ablated.items()}
    arrays_windows = window_arrays(edges, occlusion, windowed, shapley, x0, scorer.features(unprotected)[0], ok_ablated,
                                   ks_sweep or {}, partition or {}, partition_leaves)
    # The statistics of both at the window level (docs/experiments/cp.md, CP.3): do they differ where T1 says?
    coarse = {"instrumented": coarsen_provenance(prov, edges), "blackbox": coarsen_provenance(blackbox, edges)}
    arrays = {"tv": tv.astype(np.float32), "attributable": attributable, "estimated": estimated, "windows": arrays_windows}
    for name, Pk in coarse.items():
        arrays[f"overlap_{name}"] = Pk.overlap().per_feature.astype(np.float32)
        arrays[f"ambiguity_{name}"] = Pk.ambiguity().per_feature.astype(np.float32)
    return records, info, arrays


def window_arrays(edges: npt.NDArray[np.int64], occlusion: dict[str, FloatArray], windowed: dict[int, tuple[int, npt.NDArray[np.int64], dict[str, FloatArray]]], shapley: dict[str, FloatArray], x: FloatArray, x_ablated: FloatArray, ablated_valid: bool, ks_sweep: Optional[dict[int, dict[str, FloatArray]]] = None, partition: Optional[dict[int, dict[str, FloatArray]]] = None, partition_leaves: int = 16384) -> dict[str, npt.NDArray[Any]]:
    """
    The per-window scores of every direct problem-space explanation of one file, for PF1 (docs/experiments/pf1.md).

    Keys: `edges` and `occlusion:{model}` (the K windows), `edges_k{J}` and `occlusion_k{J}:{model}` (each further
    window count), `kernelshap_windows:{model}` (over the K windows), `x` (the file's features), and `x_ablated` (the
    features of the fully ablated file, PF1's reference matched to the problem-space; NaN if it failed verification),
    `kernelshap_k{J}:{model}` (KernelSHAP over J windows), and `edges_leaves` with `partition_b{B}:{model}` (adaptive
    KernelSHAP over the leaf windows at budget B).

    Args:
        edges: The K windows' edges.
        occlusion: Per model, the occlusion score of each of the K windows.
        windowed: Per further window count J, the number of windows, the window of each element, and per model the
            occlusion score of each window.
        shapley: Per model, KernelSHAP's value of each of the K windows (empty if it was not run).
        x: The features of the file.
        x_ablated: The features of the fully ablated file.
        ablated_valid: Whether the fully ablated file passed verification.

    Returns:
        The arrays, by key.
    """
    out: dict[str, npt.NDArray[Any]] = {"edges": np.asarray(edges, dtype=np.int64), "x": np.asarray(x, dtype=np.float64)}
    out["x_ablated"] = np.asarray(x_ablated, dtype=np.float64) if ablated_valid else np.full(x.shape[0], np.nan)
    for name, values in occlusion.items():
        out[f"occlusion:{name}"] = np.asarray(values, dtype=np.float64)
    for J, (K_j, _, scores) in windowed.items():
        out[f"edges_k{J}"] = window_edges(int(edges[-1]), J)
        for name, values in scores.items():
            # NOTE: pass 1 allocates J scores, but a file with fewer than J bytes has only K_j windows.
            out[f"occlusion_k{J}:{name}"] = np.asarray(values[:K_j], dtype=np.float64)
    for name, values in shapley.items():
        out[f"kernelshap_windows:{name}"] = np.asarray(values, dtype=np.float64)
    m = int(edges[-1])
    for J, per_model in (ks_sweep or {}).items():
        for name, values in per_model.items():
            out[f"kernelshap_k{J}:{name}"] = np.asarray(values, dtype=np.float64)
    if partition:
        out["edges_leaves"] = window_edges(m, partition_leaves)
        for B, per_model in partition.items():
            for name, values in per_model.items():
                out[f"partition_b{B}:{name}"] = np.asarray(values, dtype=np.float64)
    return out


def save_window_scores(path: Path, arrays: dict[int, dict[str, npt.NDArray[Any]]]) -> None:
    """Save every file's `window_arrays` in one archive, under the keys `{index}/{key}`."""
    flat = {f"{index}/{key}": value for index, per_file in arrays.items() for key, value in per_file.items()}
    np.savez_compressed(path, **flat)  # type: ignore[arg-type]


def load_window_scores(path: Path) -> dict[int, dict[str, npt.NDArray[Any]]]:
    """Load an archive written by `save_window_scores`: per file index, its arrays by key."""
    out: dict[int, dict[str, npt.NDArray[Any]]] = {}
    with np.load(path) as archive:
        for flat in archive.files:
            index, key = flat.split("/", 1)
            out.setdefault(int(index), {})[key] = archive[flat]
    return out


def process_one(task: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[int, dict[str, Any]]]:
    """
    Pass 2: everything left for one file, given pass 1's per-window scores.

    Returns the curve records, the file's record, and its provenance arrays (empty on failure).
    """
    base = {"index": task["index"], "name": task["name"], "label": task["label"]}
    t_0 = time.perf_counter()
    signal.alarm(task["timeout"])
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        recs, info, arr = process_file(
            data, task["explanations"], task["num_windows"], task["fill"], task["header"],
            task["seed"], task["budgets"], task["sweep"], task["shapley"], task["pass1"], task["tiebreak"],
            task["field_oracle"], task.get("ks_sweep"), task.get("partition"), task.get("partition_leaves", 16384),
            task.get("pushforward", False), tuple(task.get("trend_explainers", ())),
        )
        return (
            [base | r for r in recs],
            base | {"status": "ok", "error": "", "seconds": task["pass1_seconds"] + time.perf_counter() - t_0} | info,
            {task["index"]: arr},
        )
    except Timeout:
        return [], base | {"status": "timeout", "error": f"Exceeded {task['timeout']} seconds."}, {}
    except ValueError as err:
        return [], base | {"status": "unprotectable", "error": str(err)[:300]}, {}
    except Exception as err:
        return [], base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]}, {}
    finally:
        signal.alarm(0)


def _pass1(task: dict[str, Any]) -> dict[str, Any]:
    """Run one pass-1 task, reporting a failure instead of raising so that one bad file cannot stop the run."""
    signal.alarm(task["timeout"])
    try:
        if task["kind"] == "occlude":
            return process_occlusion_chunk(task)
        if task["kind"] == "partition":
            return process_partition(task)
        return process_kernelshap(task)
    except Exception as err:
        return {"kind": task["kind"], "index": task["index"], "error": f"{type(err).__name__}: {err}"[:300],
                "num_windows": task.get("num_windows", 0), "k_lo": task.get("k_lo", 0), "k_hi": task.get("k_hi", 0)}
    finally:
        signal.alarm(0)


def reuse_pass1(rundir: Path, indices: list[int], config: dict[str, Any]) -> tuple[dict[int, dict[int, dict[str, FloatArray]]], dict[int, dict[str, FloatArray]], dict[int, dict[str, Any]], dict[int, float], dict[int, dict[int, dict[str, FloatArray]]], dict[int, dict[int, dict[str, FloatArray]]]]:
    """
    Pass 1's outputs from an earlier run's window_scores.npz and files.parquet, so that a run that changes only pass 2
    (e.g., the rankings) need not repeat it. The earlier run's configuration must match.

    Returns:
        Per file index: the sweep's per-window scores (per window count and model), KernelSHAP's per-window values (per
        model), pass 1's record (timing, extractions, failures), pass 1's seconds, and whatever the earlier run has of
        KernelSHAP at further window counts and adaptive KernelSHAP (per window count or budget, and model); the caller
        computes the rest.
    """
    report = json.loads((rundir / "report.json").read_text())
    for key, value in config.items():
        if report.get(key) != value:
            raise ValueError(f"{rundir.as_posix()} was run with {key} = {report.get(key)}, not {value}.")
    scores = load_window_scores(rundir / "window_scores.npz")
    files = pl.read_parquet(rundir / "files.parquet")
    missing = sorted(set(indices) - set(scores))
    if missing:
        raise RuntimeError(f"{rundir.as_posix()} has no window scores for files {missing[:5]}.")
    prefixes = ("seconds_occlusion_k", "occlusion_extractions_k", "invalid_windows_k", "num_windows_k", "seconds_kernelshap_windows",
                "kernelshap_windows_extractions", "kernelshap_windows_failed", "seconds_kernelshap_k", "kernelshap_k",
                "seconds_partition_b", "partition_b")
    columns = [c for c in files.columns if c.startswith(prefixes)]
    records = {int(r["index"]): r for r in files.select("index", *columns).to_dicts()}
    sweeps: dict[int, dict[int, dict[str, FloatArray]]] = {}
    shapleys: dict[int, dict[str, FloatArray]] = {}
    info: dict[int, dict[str, Any]] = {}
    seconds: dict[int, float] = {}
    ks_sweeps: dict[int, dict[int, dict[str, FloatArray]]] = {}
    partitions: dict[int, dict[int, dict[str, FloatArray]]] = {}
    for i in indices:
        for key, value in scores[i].items():
            method, _, name = key.partition(":")
            if method.startswith("kernelshap_k") and name in config["classifiers"]:
                ks_sweeps.setdefault(i, {}).setdefault(int(method.removeprefix("kernelshap_k")), {})[name] = value
            elif method.startswith("partition_b") and name in config["classifiers"]:
                partitions.setdefault(i, {}).setdefault(int(method.removeprefix("partition_b")), {})[name] = value
        sweeps[i] = {J: {name: scores[i][f"occlusion_k{J}:{name}"] for name in config["classifiers"]}
                     for J in dict.fromkeys(config["sweep_windows"]) if J != config["num_windows"]}
        if config["kernelshap_samples"] > 0:
            shapleys[i] = {name: scores[i][f"kernelshap_windows:{name}"] for name in config["classifiers"]}
        info[i] = {c: v for c, v in records[i].items() if c != "index" and v is not None}
        seconds[i] = float(sum(v for c, v in info[i].items() if c.startswith(("seconds_occlusion_k", "seconds_kernelshap", "seconds_partition_b"))))
    return sweeps, shapleys, info, seconds, ks_sweeps, partitions


def extractions_per_file(num_windows: int, sweep_windows: tuple[int, ...], kernelshap_samples: int, budgets: tuple[float, ...], num_methods: int = 26) -> int:
    """
    How many feature extractions one file costs, which is known exactly before a run: the original and the fully
    ablated file, one per window of every occlusion run, the KernelSHAP coalitions, and one per budget and method.
    """
    windows = (num_windows, *(J for J in sweep_windows if J != num_windows))
    return 2 + sum(windows) + kernelshap_samples + len(budgets) * num_methods


def predict_seconds(sizes: npt.NDArray[np.int64], extractions: int) -> FloatArray:
    """The predicted seconds per file, from its size and the number of extractions (see SECONDS_PER_EXTRACTION)."""
    megabytes = np.asarray(sizes, dtype=np.float64) / 1e6
    return np.asarray(extractions * (SECONDS_PER_EXTRACTION + SECONDS_PER_EXTRACTION_PER_MB * megabytes), dtype=np.float64)


def chunk_windows(num_windows: int, size_bytes: int, target_seconds: float = 180.0) -> list[tuple[int, int]]:
    """
    Split `num_windows` windows into chunks of about `target_seconds` of predicted work, so that no single task
    dominates the run and the per-task overhead (loading and protecting the file) stays small.
    """
    seconds_each = max(SECONDS_PER_EXTRACTION + SECONDS_PER_EXTRACTION_PER_MB * size_bytes / 1e6, 1e-6)
    per_chunk = int(np.clip(round(target_seconds / seconds_each), 1, num_windows))
    return [(lo, min(lo + per_chunk, num_windows)) for lo in range(0, num_windows, per_chunk)]


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
    parser.add_argument("--kernelshap_windows", type=int, nargs="*", default=[], help="Window counts for KernelSHAP over windows at every budget (methods kernelshap_k{J}), e.g., 64 256 1024.")
    parser.add_argument("--kernelshap_per_window", type=int, default=8, help="Coalitions per window for --kernelshap_windows (8: 2,048 at 256 windows, as --kernelshap_samples 2048).")
    parser.add_argument("--partition_budgets", type=int, nargs="*", default=[], help="Budgets B for adaptive KernelSHAP (B + 2 queries, matched to occlusion over B windows), e.g., 64 256 1024 4096.")
    parser.add_argument("--partition_leaves", type=int, default=16384, help="The leaf windows of adaptive KernelSHAP's hierarchy.")
    parser.add_argument("--pushforward", action="store_true", help="Add Section 5.2's feature rankings: every window explanation pushed forward, the resolution trend, and random feature explanations, all scored by the bytes they point to.")
    parser.add_argument("--trend_explainers", type=str, nargs="*", default=["treeshap_interventional"], help="Feature explanations whose resolution trend --pushforward adds.")
    parser.add_argument("--field_oracle", action="store_true", help="Add the field-occlusion oracle: occlude each parsed PE field/section and rank bytes by the drop (a structure-aware upper bound; one extraction per region).")
    parser.add_argument("--tag", type=str, default="", help="A suffix for the output directory.")
    parser.add_argument("--files", type=Path, default=None, help="Reuse the files of an earlier run (its files.parquet); --num_files then takes the first files per label.")
    parser.add_argument("--sample_seed", type=int, default=0)
    parser.add_argument("--include", type=Path, default=None, help="A files.parquet whose files the sample must contain (e.g., the pilot's); the rest of each label is sampled with --sample_seed.")
    parser.add_argument("--select_only", type=Path, default=None, help="Write the selected files (name, label) to this parquet and exit, before any explanation is required.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "e1")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=3600, help="The maximum number of seconds per file.")
    parser.add_argument("--tiebreak", type=str, choices=["random", "position"], default="random", help="Break ties in the rankings by a seeded random permutation (the default since 2026-10-09) or by position in the file (the earlier behavior).")
    parser.add_argument("--reuse_scores", type=Path, default=None, help="An earlier run's directory whose window_scores.npz provides pass 1 (the sweep and KernelSHAP over windows), which is then skipped; its configuration must match.")
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
    elif args.include is not None:
        # A superset of earlier files (the pilot's 100), filled up per label by a seeded sample of the rest.
        names = pl.read_parquet(args.include)["name"]
        parts = []
        for lab in (0, 1):
            pool = samples.filter(pl.col("label") == lab)
            kept = pool.filter(pl.col("name").is_in(names.implode()))
            if kept.height > per_label:
                raise RuntimeError(f"--include has {kept.height} files of label {lab}, more than {per_label}.")
            rest = pool.filter(~pl.col("name").is_in(names.implode()))
            parts += [kept, rest.sample(per_label - kept.height, seed=args.sample_seed)]
        samples = pl.concat(parts)
        if samples.filter(pl.col("name").is_in(names.implode())).height != names.len():
            raise RuntimeError(f"Some files of {args.include.as_posix()} are not in the explanation set or are excluded.")
    else:
        samples = pl.concat([samples.filter(pl.col("label") == lab).sample(per_label, seed=args.sample_seed) for lab in (0, 1)])
    if args.select_only is not None:
        args.select_only.parent.mkdir(parents=True, exist_ok=True)
        samples.select("name", "label").sort("label", "name").write_parquet(args.select_only)
        print(f"Wrote {samples.height} files to {args.select_only.as_posix()}.", flush=True)
        return
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left").sort("index")
    for e, A in explanations.items():
        if not np.all(np.isfinite(A[samples["index"].to_numpy()])):
            raise RuntimeError(f"{e} has no explanations for some selected files; compute it for them (explain.py --subset).")

    # The cost of a file is its size times its number of extractions, both known up front (see predict_seconds).
    # The field oracle adds one budgeted method and roughly 250 region extractions per file (the number varies with
    # the file's field and section count, so this is only for the up-front estimate).
    per_file = extractions_per_file(args.num_windows, tuple(args.sweep_windows), args.kernelshap_samples, BUDGETS,
                                    num_methods=27 if args.field_oracle else 26)
    per_file += 250 if args.field_oracle else 0
    per_file += sum(args.kernelshap_per_window * J + 2 for J in args.kernelshap_windows) + sum(B + 2 for B in args.partition_budgets)
    per_file += len(BUDGETS) * (len(args.kernelshap_windows) + len(args.partition_budgets))
    if args.pushforward:
        num_sources = 1 + len(args.sweep_windows) + (args.kernelshap_samples > 0) + len(args.kernelshap_windows) + len(args.partition_budgets)
        per_file += len(BUDGETS) * (num_sources + len(args.trend_explainers) * (2 + len(args.sweep_windows)) + 3)
    # The legacy KernelSHAP at --num_windows counts as kernelshap_k{num_windows} when its coalitions match.
    legacy_k = args.num_windows if args.kernelshap_samples > 0 and args.kernelshap_samples == args.kernelshap_per_window * args.num_windows else None
    sizes = pl.read_parquet(args.explanation_set).select("name", "size")
    samples = samples.join(sizes, on="name", how="left").with_columns(pl.col("size").fill_null(0))
    files_of = {"gbdt": args.models / "gbdt" / f"seed-{args.seed}" / "model.txt", "mlp": args.models / "mlp" / f"seed-{args.seed}" / "model.pt"}
    d = next(iter(explanations.values())).shape[1]
    initargs = ({name: files_of[name] for name in models}, d)
    common = {"dbdir": args.db, "num_windows": args.num_windows, "fill": args.fill, "header": args.header,
              "timeout": args.timeout, "field_oracle": args.field_oracle}
    rows = samples.select("index", "name", "label", "shard", "position", "size").to_dicts()
    predicted = {int(r["index"]): float(predict_seconds(np.asarray([r["size"]]), per_file)[0]) for r in rows}
    total = sum(predicted.values())
    # The progress bars count predicted worker-minutes, not tasks: tasks run longest-first, so a count of tasks makes
    # the run look far slower than it is until the end.
    each = {int(r["index"]): float(predict_seconds(np.asarray([r["size"]]), 1)[0]) / 60 for r in rows}

    def pass1_minutes(out: dict[str, Any]) -> float:
        if out["kind"] == "occlude":
            n = out.get("k_hi", 0) - out.get("k_lo", 0)
        elif out["kind"] == "kernelshap_k":
            n = args.kernelshap_per_window * out.get("num_windows", 0) + 2
        elif out["kind"] == "partition":
            n = out.get("budget", 0) + 2
        else:
            n = args.kernelshap_samples
        return float(n) * each[int(out["index"])]

    pass2_extractions = 2 + args.num_windows + len(BUDGETS) * 26
    print(f"Explainers: {explainers}.", flush=True)
    print(f"PB1: {samples.height} files ({int(bad.sum())} excluded for local accuracy), models {list(models)}, {args.num_windows} windows (sweep {args.sweep_windows}), KernelSHAP over windows {args.kernelshap_samples}, fill {args.fill}, header {args.header}.", flush=True)
    print(f"Cost: {per_file} extractions per file; predicted {total / 3600:.1f} worker-hours, so about "
          f"{total / args.num_workers / 3600:.1f} h wall-clock on {args.num_workers} workers (a file can take twice "
          f"its prediction, so treat this as a floor).", flush=True)

    # Pass 1: the occlusion sweep in chunks of windows, and KernelSHAP, both of which only need per-window scores.
    pass1_tasks: list[dict[str, Any]] = []
    for r in rows:
        for J in dict.fromkeys(args.sweep_windows):
            if J == args.num_windows:
                continue
            for k_lo, k_hi in chunk_windows(J, int(r["size"])):
                pass1_tasks.append(common | {"kind": "occlude", "index": int(r["index"]), "name": r["name"],
                                             "shard": int(r["shard"]), "position": int(r["position"]),
                                             "seed": args.sample_seed + int(r["index"]),
                                             "num_windows": J, "k_lo": k_lo, "k_hi": k_hi})
        if args.kernelshap_samples > 0:
            pass1_tasks.append(common | {"kind": "kernelshap", "index": int(r["index"]), "name": r["name"],
                                         "shard": int(r["shard"]), "position": int(r["position"]),
                                         "seed": args.sample_seed + int(r["index"]),
                                         "kernelshap_samples": args.kernelshap_samples})
        for J in dict.fromkeys(args.kernelshap_windows):
            if J == legacy_k:
                continue
            pass1_tasks.append(common | {"kind": "kernelshap_k", "index": int(r["index"]), "name": r["name"],
                                         "shard": int(r["shard"]), "position": int(r["position"]),
                                         "seed": args.sample_seed + int(r["index"]), "num_windows": J,
                                         "kernelshap_samples": args.kernelshap_per_window * J})
        for B in dict.fromkeys(args.partition_budgets):
            pass1_tasks.append(common | {"kind": "partition", "index": int(r["index"]), "name": r["name"],
                                         "shard": int(r["shard"]), "position": int(r["position"]),
                                         "seed": args.sample_seed + int(r["index"]), "budget": B,
                                         "partition_leaves": args.partition_leaves})
    t_0 = time.time()
    sweeps: dict[int, dict[int, dict[str, FloatArray]]] = {int(r["index"]): {} for r in rows}
    shapleys: dict[int, dict[str, FloatArray]] = {}
    pass1_info: dict[int, dict[str, Any]] = {int(r["index"]): {} for r in rows}
    pass1_seconds: dict[int, float] = {int(r["index"]): 0.0 for r in rows}
    pass1_failures: list[str] = []
    ks_sweeps: dict[int, dict[int, dict[str, FloatArray]]] = {int(r["index"]): {} for r in rows}
    partitions: dict[int, dict[int, dict[str, FloatArray]]] = {int(r["index"]): {} for r in rows}
    if args.reuse_scores is not None:
        indices = [int(r["index"]) for r in rows]
        config = {"seed": args.seed, "sweep_windows": args.sweep_windows, "kernelshap_samples": args.kernelshap_samples,
                  "fill": args.fill, "header": args.header, "num_windows": args.num_windows, "classifiers": list(models)}
        sweeps, shapleys, pass1_info, pass1_seconds, reused_ks, reused_partition = reuse_pass1(args.reuse_scores, indices, config)
        for i in indices:
            ks_sweeps[i] |= {J: v for J, v in reused_ks.get(i, {}).items() if J in args.kernelshap_windows}
            partitions[i] |= {B: v for B, v in reused_partition.get(i, {}).items() if B in args.partition_budgets}
        # The occlusion sweep and the legacy KernelSHAP come from the earlier run; so do the new explainers it has.
        todo = [t for t in pass1_tasks if (t["kind"] == "kernelshap_k" and t["num_windows"] not in ks_sweeps[t["index"]])
                or (t["kind"] == "partition" and t["budget"] not in partitions[t["index"]])]
        print(f"Pass 1: reused from {args.reuse_scores.as_posix()} ({len(pass1_tasks) - len(todo)} tasks skipped).", flush=True)
        pass1_tasks = todo
    if pass1_tasks:
        # Longest-first, so that the biggest chunks start immediately.
        pass1_tasks.sort(key=lambda t: -(predicted[t["index"]] * (t.get("k_hi", 0) - t.get("k_lo", 0) + t.get("kernelshap_samples", 0) + t.get("budget", 0))))
        print(f"Pass 1: {len(pass1_tasks)} tasks (the sweep in chunks of windows, and KernelSHAP).", flush=True)
        with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=initargs) as pool:
            bar = tqdm(total=sum(pass1_minutes(t) for t in pass1_tasks), desc="pass 1", smoothing=0.0, mininterval=30,
                       bar_format=BAR_FORMAT)
            with bar:
                for out in pool.imap_unordered(_pass1, pass1_tasks):
                    bar.update(pass1_minutes(out))
                    i_file = out["index"]
                    if "error" in out:
                        pass1_failures.append(f"{i_file}: {out['error']}")
                        continue
                    pass1_seconds[i_file] += out["seconds"]
                    info = pass1_info[i_file]
                    if out["kind"] == "occlude":
                        J = out["num_windows"]
                        into = sweeps[i_file].setdefault(J, {})
                        for name, values in out["scores"].items():
                            if name not in into:
                                into[name] = np.zeros(J)
                            into[name][out["k_lo"]:out["k_hi"]] = values
                        info[f"seconds_occlusion_k{J}"] = info.get(f"seconds_occlusion_k{J}", 0.0) + out["seconds"]
                        info[f"occlusion_extractions_k{J}"] = info.get(f"occlusion_extractions_k{J}", 0) + out["extractions"]
                        info[f"invalid_windows_k{J}"] = info.get(f"invalid_windows_k{J}", 0) + out["invalid"]
                        info[f"num_windows_k{J}"] = J
                    elif out["kind"] == "kernelshap_k":
                        J = out["num_windows"]
                        ks_sweeps[i_file][J] = out["values"]
                        info |= {f"seconds_kernelshap_k{J}": out["seconds"], f"kernelshap_k{J}_extractions": out["extractions"],
                                 f"kernelshap_k{J}_failed": out["failed"]}
                    elif out["kind"] == "partition":
                        B = out["budget"]
                        partitions[i_file][B] = out["values"]
                        info |= {f"seconds_partition_b{B}": out["seconds"], f"partition_b{B}_extractions": out["extractions"],
                                 f"partition_b{B}_failed": out["failed"]}
                    else:
                        shapleys[i_file] = out["values"]
                        info |= {"seconds_kernelshap_windows": out["seconds"],
                                 "kernelshap_windows_extractions": out["extractions"],
                                 "kernelshap_windows_failed": out["failed"]}
        if pass1_failures:
            print(f"Pass 1 failures ({len(pass1_failures)}): {pass1_failures[:5]}", flush=True)

    if legacy_k is not None and legacy_k in args.kernelshap_windows:
        for i, values in shapleys.items():
            ks_sweeps[i][legacy_k] = values

    # Pass 2: one task per file, the rest of the work.
    pass2_tasks = [
        common | {
            "index": int(r["index"]), "name": r["name"], "label": r["label"],
            "shard": int(r["shard"]), "position": int(r["position"]), "budgets": BUDGETS, "tiebreak": args.tiebreak == "random",
            "seed": args.sample_seed + int(r["index"]),
            "explanations": {e: A[int(r["index"])] for e, A in explanations.items()},
            "sweep": sweeps[int(r["index"])], "shapley": shapleys.get(int(r["index"])),
            "pass1": pass1_info[int(r["index"])], "pass1_seconds": pass1_seconds[int(r["index"])],
            "ks_sweep": ks_sweeps[int(r["index"])], "partition": partitions[int(r["index"])],
            "partition_leaves": args.partition_leaves, "pushforward": args.pushforward,
            "trend_explainers": args.trend_explainers,
        }
        for r in rows
    ]
    pass2_tasks.sort(key=lambda t: -predicted[t["index"]])
    print(f"Pass 2: {len(pass2_tasks)} tasks (one per file).", flush=True)
    records: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    arrays: dict[int, dict[str, Any]] = {}
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=initargs) as pool:
        bar = tqdm(total=sum(pass2_extractions * each[t["index"]] for t in pass2_tasks), desc="pass 2", smoothing=0.0,
                   mininterval=30, bar_format=BAR_FORMAT)
        with bar:
            for recs, inf, arr in pool.imap_unordered(process_one, pass2_tasks):
                bar.update(pass2_extractions * each[int(inf["index"])])
                records.extend(recs)
                infos.append(inf)
                arrays.update(arr)
                elapsed = (time.time() - t_0) / 60
                bar.write(f"  [{len(infos):3d}/{len(pass2_tasks)} {elapsed:6.1f} min] {inf['name'][:16]} "
                          f"{inf.get('num_elements', 0) / 1e6:5.2f} MB  {inf.get('seconds', float('nan')) / 60:6.1f} min  "
                          f"{inf.get('extractions', 0):6d} extractions (pass 2)  {inf['status']}")

    pl.DataFrame(records, infer_schema_length=None).write_parquet(outdir / "curves.parquet")
    files = pl.DataFrame(infos, infer_schema_length=None).sort("index")
    files.write_parquet(outdir / "files.parquet")
    order = sorted(arrays)
    stacked: dict[str, Any] = {"index": np.array(order, dtype=np.int64)}
    for key in ("tv", "attributable", "estimated", *(f"{s}_{p}" for s in ("overlap", "ambiguity") for p in ("instrumented", "blackbox"))):
        stacked[key] = np.stack([arrays[i][key] for i in order]) if order else np.zeros((0, d))
    np.savez_compressed(outdir / "provenance.npz", **stacked)
    save_window_scores(outdir / "window_scores.npz", {i: arrays[i]["windows"] for i in order})

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
        "tiebreak": args.tiebreak,
        "field_oracle": args.field_oracle,
        "kernelshap_windows": args.kernelshap_windows,
        "kernelshap_per_window": args.kernelshap_per_window,
        "partition_budgets": args.partition_budgets,
        "partition_leaves": args.partition_leaves,
        "pushforward": args.pushforward,
        "trend_explainers": args.trend_explainers,
        "reuse_scores": args.reuse_scores.as_posix() if args.reuse_scores is not None else None,
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
