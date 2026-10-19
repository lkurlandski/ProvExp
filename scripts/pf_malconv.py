"""
M1 (docs/experiments/mocks.md; revision plan item 10): is the pushforward faithful on MalConv, the model the audit
(Section 5.3) pushes forward?

MalConv never computes the features, so a feature-space explanation of it cannot be tested by deleting features.
Instead, each feature-space explanation is pulled back through the file's P and its top bytes are deleted with PB1's
operator (run 21: level 3, zeros fill; `--fill random` for the robustness check); MalConv scores every deleted file.
For each of PB1's 100 pilot files:

    pushforward   the pushforward of MalConv's Integrated Gradients, a = P^T D^+ b (the method; what the audit uses);
    pushforward_exact   with `--exact` (run 63): the exact pushforward of the same IG, M^+ P^T D^+ b with
                  M = P^T D^+ P (Definition Exact Pushforward; the conjugate-gradient limit of scripts/pf_inverse.py);
    surrogate     interventional TreeSHAP of the surrogate of MalConv (scripts/audit_surrogate.py; the realistic
                  alternative, which never saw these files);
    random_feat   random feature explanations (standard normal), the floor;

With --occlusion_windows, --kernelshap_windows, and --partition_budgets (Section 5.2's shared protocol, 2026-10-19),
also the pushforward of MalConv's window explanations, which use no gradients, each scored the same way:

    pushforward:occlusion_k{J}      occlusion of J windows (each deleted with the operator), pushed forward
    pushforward:kernelshap_k{J}     KernelSHAP over J windows (8 coalitions per window by default), pushed forward
    pushforward:partition_b{B}      adaptive KernelSHAP over 16,384 leaf windows at B + 2 queries, pushed forward

The window explanations run on the GPU in phase 1 (batched MalConv passes over ablated files); their queries per file
are recorded in files.parquet.

and, as problem-space references that name no features:

    ig            Integrated Gradients itself, per byte (the pushforward's source);
    ig_k256       Integrated Gradients summed over PB1's 256 windows;
    random        random window orders.

Each ranking deletes evidence for MalConv's predicted class (PB1's convention).

Outputs, in `{outdir}/seed-{seed}/` (suffixed `-random` with `--fill random`, `-exact` with `--exact`):
    curves.parquet      one row per (file, ranking, budget): MalConv's log-odds, and whether the file verified
    files.parquet       one row per file: size, MalConv's log-odds, status, timing
    report.json         the configuration and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/pf_malconv.py --seed 0 --device cuda:1 --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
from typing import Any
import warnings

import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats
import torch
from tqdm import tqdm

from provexp.ablation import BUDGETS
from provexp.ablation import ablate
from provexp.ablation import budget_masks
from provexp.ablation import element_order
from provexp.ablation import window_edges
from provexp.ablation import window_order
from provexp.ablation import window_pushforward
from provexp.explain.feature import kernelshap
from provexp.explain.feature import owen_partition
from provexp.featuresets.ember2024.ablation import Protection
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.malconv import MalConv
from provexp.models.malconv import load_pretrained_malconv
from provexp.provenance import Provenance

sys.path.insert(0, str(Path(__file__).parent))

from cm_check import malconv_explanations  # noqa: E402
from cm_check import malconv_log_odds  # noqa: E402
from faithfulness import load_sample  # noqa: E402
from faithfulness import load_window_scores  # noqa: E402
from pf_inverse import inverse_pushforwards  # noqa: E402
from pf_inverse import provenance_matrix  # noqa: E402


__all__ = [
    "feature_explanations",
]


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
NUM_RANDOM = 3
FEATURE_RANKINGS = ("pushforward", "surrogate", "random_feat")

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]
BoolArray = npt.NDArray[np.bool_]

_STATE: dict[str, Any] = {}


################################################################################
# Rankings
################################################################################


def feature_explanations(
    prov: Provenance,
    ig: FloatArray,
    surrogate: FloatArray,
    rng: np.random.Generator,
    exact: bool = False,
) -> dict[str, FloatArray]:
    """
    The feature-space explanations of MalConv compared on one file.

    Args:
        prov: The file's provenance.
        ig: MalConv's Integrated Gradients, per byte, shape (num_elements,).
        surrogate: The surrogate's TreeSHAP for the file, shape (num_features,).
        rng: The source of the random feature explanations.
        exact: Also the exact pushforward of `ig` ("pushforward_exact").

    Returns:
        The pushforward of `ig`, the surrogate's explanation, and NUM_RANDOM random ones, each of shape (num_features,).
    """
    if ig.shape != (prov.num_elements,):
        raise ValueError(f"Expected Integrated Gradients of shape ({prov.num_elements},). Got {ig.shape}.")
    if surrogate.shape != (prov.num_features,):
        raise ValueError(f"Expected a surrogate explanation of shape ({prov.num_features},). Got {surrogate.shape}.")
    out = {"pushforward": prov.pushforward(ig), "surrogate": surrogate}
    if exact:
        # The null element carries none of IG, so P without its row suffices (the null features get zero either way).
        out["pushforward_exact"] = inverse_pushforwards(provenance_matrix(prov), ig, ())["cg"]
    for r in range(NUM_RANDOM):
        out[f"random_feat:{r}"] = rng.standard_normal(prov.num_features)
    return out


################################################################################
# MalConv's Window Explanations
################################################################################


class WindowScorer:
    """
    Scores versions of one file with some of its windows deleted (PB1's operator) by MalConv on a device, in batches,
    and counts the queries. Deletion is the same as in the deletion curves, so the explanations and their evaluation
    share one notion of removing content.
    """

    def __init__(self, model: MalConv, data: bytes, protection: Protection, fill: str, seed: int, device: str,
                 batch_tokens: int = 2 ** 25) -> None:
        self.model = model
        self.data = data
        self.protection = protection
        self.fill = fill
        self.seed = seed
        self.device = device
        self.batch = max(1, batch_tokens // max(len(data), 1))
        self.queries = 0

    def __call__(self, deleted: BoolArray, window: IntArray) -> FloatArray:
        """
        MalConv's log-odds with the windows marked in each row of `deleted` (N, K) deleted, shape (N,).

        Args:
            deleted: Which windows to delete, per query.
            window: The window of each byte, shape (m,).
        """
        out = np.zeros(deleted.shape[0])
        for lo in range(0, deleted.shape[0], self.batch):
            rows = []
            for d in deleted[lo:lo + self.batch]:
                which = d[window]
                key = hashlib.blake2b(np.packbits(which).tobytes(), digest_size=16).digest()
                rng = np.random.default_rng([self.seed, int.from_bytes(key[:8], "little")])
                z = ablate(self.data, which, self.protection.mask, self.fill, rng, self.protection.header,  # type: ignore[arg-type]
                           self.protection.header_values)
                rows.append(torch.frombuffer(bytearray(z), dtype=torch.uint8))
            x = torch.stack(rows).to(self.device).to(torch.int64) + 1
            with torch.no_grad():
                logits = self.model(x)
            out[lo:lo + len(rows)] = (logits[:, 1] - logits[:, 0]).double().cpu().numpy()
            self.queries += len(rows)
        return out


def window_explanations(
    scorer: WindowScorer,
    m: int,
    occlusion_windows: tuple[int, ...],
    kernelshap_windows: tuple[int, ...],
    partition_budgets: tuple[int, ...],
    per_window: int,
    leaves: int,
    seed: int,
) -> tuple[dict[str, tuple[IntArray, FloatArray]], dict[str, int]]:
    """
    MalConv's window explanations of one file: occlusion, KernelSHAP over windows, and adaptive KernelSHAP, the same
    three explainers as for the GBDT (scripts/faithfulness.py). Each attributes the evidence for malware.

    Returns:
        Per method, the window edges and the value of each window; and the queries each method took.
    """
    out: dict[str, tuple[IntArray, FloatArray]] = {}
    queries: dict[str, int] = {}

    def layout(K: int) -> tuple[IntArray, IntArray, int]:
        edges = window_edges(m, K)
        n = edges.shape[0] - 1
        return edges, np.repeat(np.arange(n), np.diff(edges)).astype(np.int64), n

    for J in occlusion_windows:
        edges, window, n = layout(J)
        q_0 = scorer.queries
        f0 = scorer(np.zeros((1, n), dtype=np.bool_), window)[0]
        out[f"occlusion_k{J}"] = (edges, f0 - scorer(np.eye(n, dtype=np.bool_), window))
        queries[f"occlusion_k{J}"] = scorer.queries - q_0
    for J in kernelshap_windows:
        edges, window, n = layout(J)
        q_0 = scorer.queries

        def f(Z: npt.NDArray[np.floating], window: IntArray = window) -> FloatArray:
            return scorer(~(Z > 0.5), window)

        out[f"kernelshap_k{J}"] = (edges, kernelshap(f, np.ones((1, n)), np.zeros((1, n)), nsamples=per_window * n, seed=seed)[0])
        queries[f"kernelshap_k{J}"] = scorer.queries - q_0
    if partition_budgets:
        edges, window, n = layout(leaves)
        for B in partition_budgets:
            q_0 = scorer.queries

            def g(Z: npt.NDArray[np.floating], window: IntArray = window) -> FloatArray:
                return scorer(~(Z > 0.5), window)

            values = owen_partition(g, n, B + 2, seed) if n >= 2 else np.zeros(n)
            out[f"partition_b{B}"] = (edges, values)
            queries[f"partition_b{B}"] = scorer.queries - q_0
    return out, queries


################################################################################
# Per File
################################################################################


def _init_worker(malconv_file: Path) -> None:
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    torch.set_num_threads(1)
    _STATE["extractor"] = PEFeatureExtractor()
    _STATE["malconv"] = load_pretrained_malconv(malconv_file)


def process_file(task: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The deletion curves of every ranking for one file, scored by MalConv."""
    t_0 = time.perf_counter()
    base = {"index": task["index"], "name": task["name"], "label": task["label"]}
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        extractor: PEFeatureExtractor = _STATE["extractor"]
        _, prov = extractor.feature_vector_with_provenance(data)
        ig = task["ig"].astype(np.float64)
        m0 = task["malconv_log_odds"]
        d = float(np.sign(m0)) or 1.0
        ties = np.random.default_rng([task["seed"], 1])
        byte_perm = ties.permutation(m).astype(np.int64)
        edges = task["windows"]["edges"]
        K = edges.shape[0] - 1
        w = np.repeat(np.arange(K), np.diff(edges))

        # Each feature-space explanation is pulled back onto the bytes, where MalConv lives.
        feats = feature_explanations(prov, ig, task["surrogate"], np.random.default_rng([task["seed"], 2]), task["exact"])
        orders = {name: element_order(prov.pullback(a)[:m], d, byte_perm) for name, a in feats.items()}
        for method, (edges_s, values) in task.get("sources", {}).items():
            a = window_pushforward(prov, edges_s, values)
            orders[f"pushforward:{method}"] = element_order(prov.pullback(a)[:m], d, byte_perm)
        orders["ig"] = element_order(ig, d, byte_perm)
        orders["ig_k256"] = window_order(np.bincount(w, weights=ig, minlength=K), edges, d, ties.permutation(K).astype(np.int64))
        rng = np.random.default_rng(task["seed"])
        for r in range(NUM_RANDOM):
            orders[f"random:{r}"] = window_order(rng.permutation(K).astype(np.float64), edges)

        protection = protect(data, header="typical")
        malconv = _STATE["malconv"]
        cache: dict[bytes, dict[str, Any]] = {}
        curves: list[dict[str, Any]] = []
        for method, order in orders.items():
            for budget, mask in zip(BUDGETS, budget_masks(order, protection.mask, BUDGETS)):
                key = hashlib.blake2b(np.packbits(mask).tobytes(), digest_size=16).digest()
                if key not in cache:
                    # The same mask always gets the same random fill (as in faithfulness.py).
                    fill_rng = np.random.default_rng([task["seed"], int.from_bytes(key[:8], "little")])
                    z = ablate(data, mask, protection.mask, task["fill"], fill_rng, protection.header, protection.header_values)
                    try:
                        x = np.asarray(extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
                        problem = verify(protection, data, z, float(x[IS_PE]))
                    except Exception as err:
                        problem = f"extraction failed: {type(err).__name__}"
                    cache[key] = {"malconv": malconv_log_odds(malconv, z), "valid": problem is None}
                curves.append({"method": method, "budget": budget} | cache[key])
        info = {"status": "ok", "error": "", "size": m, "malconv_log_odds": m0, "extractions": len(cache),
                "seconds": time.perf_counter() - t_0} | {f"queries:{k}": v for k, v in task.get("queries", {}).items()} \
            | {f"seconds_window:{k}": v for k, v in task.get("window_seconds", {}).items()}
        return [base | c for c in curves], base | info
    except Exception as err:
        return [], base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300], "seconds": time.perf_counter() - t_0}


################################################################################
# Summary
################################################################################


def summarize(curves: pl.DataFrame, files: pl.DataFrame) -> None:
    """Print the deletion areas (mean evidence removed, budgets 0.1%-50%), a few budgets, and paired tests."""
    f0 = files.select("index", pl.col("malconv_log_odds").alias("m0"))
    c = curves.join(f0, on="index").filter(pl.col("budget") <= 0.5)
    c = c.with_columns((pl.col("m0").sign() * (pl.col("m0") - pl.col("malconv"))).alias("removed"),
                       pl.col("method").str.replace(r":\d+$", "").alias("method"))
    valid = c.group_by("index").agg(pl.col("valid").all()).filter(pl.col("valid"))["index"]
    c = c.filter(pl.col("index").is_in(valid.implode()))
    per_budget = c.group_by("index", "method", "budget").agg(pl.col("removed").mean())
    area = per_budget.group_by("index", "method").agg(pl.col("removed").mean().alias("area"))
    with pl.Config(tbl_rows=100, tbl_cols=20, tbl_width_chars=200, float_precision=2):
        print(f"\nMalConv evidence removed (median over {valid.len()} files with every deletion verified):")
        wide = per_budget.group_by("method", "budget").agg(pl.col("removed").median()).sort("budget") \
            .pivot(on="budget", index="method", values="removed")
        wide = wide.join(area.group_by("method").agg(pl.col("area").median()), on="method").sort("area", descending=True)
        print(wide)
    a = area.pivot(on="method", index="index", values="area")
    print("\nPaired comparisons of the per-file area (wins of the first, Wilcoxon p):")
    for x, y in [("pushforward_exact", "pushforward"), ("pushforward_exact", "surrogate"),
                 ("pushforward", "surrogate"), ("pushforward", "random_feat"), ("pushforward", "ig_k256"),
                 ("pushforward", "ig"), ("surrogate", "random_feat"),
                 *((m, "surrogate") for m in sorted(c["method"].unique().to_list()) if m.startswith("pushforward:"))]:
        if x in a.columns and y in a.columns:
            u, v = a[x].to_numpy(), a[y].to_numpy()
            p = stats.wilcoxon(u, v).pvalue if np.any(u != v) else float("nan")
            print(f"  {x} vs. {y}: {int((u > v).sum())}/{len(u)}, p = {p:.1e}, median ratio of areas "
                  f"{np.median(u) / np.median(v):.2f}")


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of MalConv and of the surrogate.")
    parser.add_argument("--pb1_run", type=Path, default=ROOT / "artifacts" / "experiments" / "e1" / "seed-0" / "zeros-typical-header-baselines-ties", help="The PB1 run whose files and windows to reuse.")
    parser.add_argument("--num_files", type=int, default=0, help="Only the first files per label (0: all), for smoke tests.")
    parser.add_argument("--ig_steps", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--surrogate", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_surrogate")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "pf_malconv")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--fill", type=str, choices=["zeros", "random"], default="zeros", help="How deleted content bytes are filled.")
    parser.add_argument("--exact", action="store_true", help="Also rank by the exact pushforward of IG.")
    parser.add_argument("--occlusion_windows", type=int, nargs="*", default=[], help="Window counts for MalConv's occlusion (pushed forward), e.g., 64 256 1024 4096.")
    parser.add_argument("--kernelshap_windows", type=int, nargs="*", default=[], help="Window counts for KernelSHAP over windows of MalConv, e.g., 64 256 1024.")
    parser.add_argument("--kernelshap_per_window", type=int, default=8)
    parser.add_argument("--partition_budgets", type=int, nargs="*", default=[], help="Budgets B for adaptive KernelSHAP of MalConv (B + 2 queries).")
    parser.add_argument("--partition_leaves", type=int, default=16384)
    parser.add_argument("--tag", type=str, default="", help="A suffix for the output directory.")
    parser.add_argument("--tables_only", action="store_true", help="Print the tables of an earlier run.")
    args = parser.parse_args()

    outdir = args.outdir / (f"seed-{args.seed}" + ("" if args.fill == "zeros" else f"-{args.fill}") + ("-exact" if args.exact else "")
                            + (f"-{args.tag}" if args.tag else ""))
    if args.tables_only:
        summarize(pl.read_parquet(outdir / "curves.parquet"), pl.read_parquet(outdir / "files.parquet").filter(pl.col("status") == "ok"))
        return
    outdir.mkdir(parents=True, exist_ok=True)
    files = pl.read_parquet(args.pb1_run / "files.parquet").filter(pl.col("status") == "ok")
    if args.num_files > 0:
        files = pl.concat([files.filter(pl.col("label") == lab).sort("index").head(args.num_files) for lab in (0, 1)])
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    files = files.select("index", "name", "label").join(location, on="name", how="left").sort("index")
    # The surrogate's TreeSHAP is saved in the explanation set's order, as are PB1's file indices.
    surrogate = np.load(args.surrogate / f"seed-{args.seed}" / "shap.npy", mmap_mode="r")
    names = pl.read_parquet(args.surrogate / f"seed-{args.seed}" / "predictions.parquet")["name"]
    if any(names[int(i)] != n for i, n in files.select("index", "name").iter_rows()):
        raise RuntimeError("The surrogate's explanations are not in the order of PB1's file indices.")
    windows = load_window_scores(args.pb1_run / "window_scores.npz")
    malconv_file = args.checkpoints / f"malconv-seed{args.seed}.pt"
    print(f"M1: {files.height} files from {args.pb1_run.as_posix()}, MalConv seed {args.seed}, {args.fill} fill.", flush=True)

    # Phase 1, on the GPU: MalConv's log-odds and Integrated Gradients, file by file.
    t_0 = time.time()
    model = load_pretrained_malconv(malconv_file).to(args.device)
    tasks: list[dict[str, Any]] = []
    for r in tqdm(files.iter_rows(named=True), total=files.height, desc="MalConv", mininterval=10):
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], args.db)
        log_odds, ig, _ = malconv_explanations(model, data, args.ig_steps, args.device)
        sources: dict[str, tuple[IntArray, FloatArray]] = {}
        queries: dict[str, int] = {"ig": 2 * args.ig_steps}
        window_seconds: dict[str, float] = {}
        if args.occlusion_windows or args.kernelshap_windows or args.partition_budgets:
            t_w = time.perf_counter()
            scorer = WindowScorer(model, data, protect(data, header="typical"), args.fill, int(r["index"]), args.device)
            sources, q = window_explanations(scorer, len(data), tuple(args.occlusion_windows), tuple(args.kernelshap_windows),
                                             tuple(args.partition_budgets), args.kernelshap_per_window,
                                             args.partition_leaves, int(r["index"]))
            queries |= q
            window_seconds["all"] = time.perf_counter() - t_w
        tasks.append({"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
                      "position": int(r["position"]), "dbdir": args.db, "seed": int(r["index"]),
                      "surrogate": np.asarray(surrogate[int(r["index"])], dtype=np.float64),
                      "windows": windows[int(r["index"])], "malconv_log_odds": log_odds, "ig": ig, "fill": args.fill,
                      "exact": args.exact, "sources": sources, "queries": queries, "window_seconds": window_seconds})
    seconds_malconv = time.time() - t_0
    del model
    print(f"Phase 1 (MalConv on {args.device}): {seconds_malconv:.0f} s.", flush=True)

    # Phase 2, on the CPU: provenance and the deletions, which need feature extraction to verify each file.
    t_0 = time.time()
    curves: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    tasks.sort(key=lambda t: -t["ig"].shape[0])
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(malconv_file,)) as pool:
        for c, info in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
            curves += c
            infos.append(info)
            if info["status"] != "ok":
                print(f"File {info['index']}: {info['error']}", flush=True)
    seconds_files = time.time() - t_0
    print(f"Phase 2 (files on {args.num_workers} workers): {seconds_files:.0f} s.", flush=True)

    curves_df, files_df = pl.DataFrame(curves), pl.DataFrame(infos).sort("index")
    curves_df.write_parquet(outdir / "curves.parquet")
    files_df.write_parquet(outdir / "files.parquet")
    report = {"config": {k: v.as_posix() if isinstance(v, Path) else v for k, v in vars(args).items()},
              "budgets": list(BUDGETS), "seconds_malconv": seconds_malconv, "seconds_files": seconds_files,
              "failed": int((files_df["status"] != "ok").sum())}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    summarize(curves_df, files_df.filter(pl.col("status") == "ok"))


if __name__ == "__main__":
    main()
