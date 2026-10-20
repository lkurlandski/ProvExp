"""
Attack transfer (manuscript, Section 6.1, Part A): does the GBDT's pullback on a file predict how much a
functionality-preserving perturbation of MalConv, confined to loader-ignored bytes, also lowers the GBDT's score?

For each of the selected malware that both detectors detect (scripts/cm_disagreement_select.py --both_detect):

    Phase 1 (GPU): perturb MalConv with scripts/.../attack.py (the DOS header, DOS stub, and section slack, by the
        embedding gradient, a fixed query budget, stopping at MalConv's threshold); record MalConv's log-odds before
        and after and the perturbed bytes C.
    Phase 2 (CPU): on the ORIGINAL file, compute the GBDT's interventional-TreeSHAP pullback and its occlusion over
        256 windows (the no-provenance window baseline, to be swapped for the best of Section 5.1); the GBDT then
        scores the perturbed file. Predictors of the GBDT's drop, all as evidence for the original predicted class:
            pullback_E      the pullback's evidence on the editable region E (the method; from the original file)
            occlusion_E     the window baseline's evidence on the windows overlapping E (no provenance)
            changed_C       the number of perturbed bytes |C| (the trivial predictor)
        and, for context, pullback_C (the pullback's evidence on the bytes actually changed).

    The outcome is the GBDT's drop, sign(f0) * (f0 - f_perturbed) in log-odds, and whether the GBDT's malware
    probability crossed its 1% false-positive threshold.

This doubles as the feasibility gate (implementation plan WP4): run with --num_files ~50 and read the share of files
whose GBDT drop exceeds one log-odds (the "go" criterion) and MalConv's evasion rate.

Outputs, in `{outdir}/seed-{seed}[-{tag}]/`:
    files.parquet   one row per file: sizes, MalConv/GBDT log-odds before and after, evasion, |E|, |C|, the predictors
    report.json     the configuration, the thresholds, the correlations and AUCs, and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/cm_transfer.py --seed 0 --device cuda:3 --num_workers 16
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

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats
import torch
from tqdm import tqdm

from provexp.data.tabular import load_features
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import treeshap_interventional
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.attack import attack_malconv
from provexp.featuresets.ember2024.attack import editable_region
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.malconv import load_pretrained_malconv

sys.path.insert(0, str(Path(__file__).parent))

import faithfulness  # noqa: E402
from cm_disagreement_select import load_malconv_predictions  # noqa: E402
from faithfulness import Scorer  # noqa: E402
from faithfulness import load_sample  # noqa: E402
from faithfulness import occlude  # noqa: E402


__all__ = [
    "predictors",
    "thresholds",
]


ROOT = Path(__file__).parent.parent
IS_PE = 2
FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]

_STATE: dict[str, Any] = {}


def predictors(pullback: FloatArray, occlusion_bytes: FloatArray, editable: BoolArray, changed: BoolArray, direction: float) -> dict[str, float]:
    """
    The evidence each explanation places on the editable region and on the changed bytes, as evidence for the original
    predicted class (so a larger value means the GBDT relies more on bytes the perturbation may touch).

    Args:
        pullback: The GBDT's pulled-back explanation per byte, shape (m,).
        occlusion_bytes: The GBDT's occlusion score spread over bytes, shape (m,).
        editable: The editable region E, shape (m,).
        changed: The perturbed bytes C, shape (m,).
        direction: The sign of the GBDT's original log-odds.
    """
    ev_pullback = direction * pullback
    ev_occlusion = direction * occlusion_bytes
    return {
        "pullback_E": float(ev_pullback[editable].sum()),
        "pullback_C": float(ev_pullback[changed].sum()),
        "occlusion_E": float(ev_occlusion[editable].sum()),
        "changed_C": float(changed.sum()),
    }


def thresholds(models: Path, features: Path, predictions: Path, seed: int, fpr: float) -> tuple[float, float]:
    """The GBDT's and MalConv's log-odds thresholds at `fpr` on the test split's benign files (as cm_disagreement_select)."""
    gbdt_pred = pl.read_parquet(models / "gbdt" / f"seed-{seed}" / "ts_predictions.parquet")
    p = gbdt_pred["prob"].to_numpy().clip(1e-15, 1 - 1e-15)
    gbdt_pred = gbdt_pred.with_columns(pl.Series("gbdt_log_odds", np.log(p / (1 - p)))).join(
        pl.read_parquet(features / "ts" / "meta.parquet").select("name", "label"), on="name")
    benign = gbdt_pred.filter(pl.col("label") == 0)["gbdt_log_odds"].to_numpy()
    malconv = load_malconv_predictions(predictions / f"malconv-seed{seed}")
    malconv_benign = malconv.join(gbdt_pred.select("name", "label"), on="name").filter(pl.col("label") == 0)
    return float(np.quantile(benign, 1 - fpr)), float(np.quantile(malconv_benign["malconv_log_odds"].to_numpy(), 1 - fpr))


def _init_worker(model_file: Path, background: FloatArray) -> None:
    sys.stdout = open(os.devnull, "w")
    torch.set_num_threads(1)
    _STATE["extractor"] = PEFeatureExtractor()
    _STATE["booster"] = lgb.Booster(model_file=str(model_file))
    _STATE["gbdt"] = gbdt_function(_STATE["booster"])
    _STATE["background"] = background
    # faithfulness.Scorer and occlude read faithfulness's own module state; the occlusion baseline needs the GBDT there.
    faithfulness._STATE["extractor"] = _STATE["extractor"]
    faithfulness._STATE["models"] = {"gbdt": _STATE["gbdt"]}


def process_file(task: dict[str, Any]) -> dict[str, Any]:
    """Phase 2 for one file: the GBDT's pullback and occlusion on the original, and its score on the perturbed file."""
    base = {"index": task["index"], "name": task["name"]}
    t_0 = time.perf_counter()
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        extractor: PEFeatureExtractor = _STATE["extractor"]
        gbdt = _STATE["gbdt"]
        x0, prov = extractor.feature_vector_with_provenance(data)
        f0 = float(gbdt(np.asarray(x0, dtype=np.float64)[None])[0])
        direction = float(np.sign(f0)) or 1.0

        a = treeshap_interventional(_STATE["booster"], np.asarray(x0, dtype=np.float64)[None], _STATE["background"])[0]
        pullback = prov.pullback(a)[:m]

        protection = protect(data, header="typical")
        scorer = Scorer(data, protection, "zeros", task["index"])
        edges, window, _, occlusion, _ = occlude(scorer, m, task["num_windows"])
        per_window = occlusion["gbdt"]
        occlusion_bytes = np.zeros(m)
        for k in range(edges.shape[0] - 1):
            occlusion_bytes[edges[k]:edges[k + 1]] = per_window[k]  # already f0 - f(occluded), spread over the window

        editable = editable_region(data)
        changed = np.asarray(task["changed"], dtype=np.bool_)
        preds = predictors(pullback, occlusion_bytes, editable, changed, direction)

        # The GBDT scores the perturbed file.
        x_pert = np.asarray(extractor.feature_vector(task["perturbed"]), dtype=np.float64)  # type: ignore[no-untyped-call]
        f_pert = float(gbdt(x_pert[None])[0])
        drop = direction * (f0 - f_pert)
        return base | {"status": "ok", "size": m, "gbdt_f0": f0, "gbdt_perturbed": f_pert, "gbdt_drop": drop,
                       "editable_bytes": int(editable.sum()), "seconds": time.perf_counter() - t_0} | preds
    except Exception as err:
        return base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]}


def summarize(files: pl.DataFrame, gbdt_threshold: float, drop_delta: float) -> dict[str, Any]:
    """Correlations and AUCs of each predictor against the GBDT's drop, and the headline rates."""
    ok = files.filter(pl.col("status") == "ok")
    drop = ok["gbdt_drop"].to_numpy()
    crossed = ok["gbdt_perturbed"].to_numpy() < gbdt_threshold  # the GBDT now scores it below its threshold
    big = drop > drop_delta
    out: dict[str, Any] = {
        "files": ok.height,
        "malconv_evaded": float(ok["malconv_evaded"].to_numpy().mean()),
        "gbdt_crossed_threshold": float(crossed.mean()),
        "gbdt_drop_median": float(np.median(drop)),
        f"gbdt_drop_over_{drop_delta}": float(big.mean()),
        "predictors": {},
    }
    for name in ("pullback_E", "occlusion_E", "changed_C", "pullback_C"):
        x = ok[name].to_numpy()
        rho = float(stats.spearmanr(x, drop).statistic) if ok.height > 2 else float("nan")
        # AUC for "drop exceeds drop_delta" = P(x higher on a big-drop file than on a small-drop one).
        auc = float("nan")
        if 0 < big.sum() < big.shape[0]:
            pos, neg = x[big], x[~big]
            auc = float((stats.rankdata(np.concatenate([pos, neg]))[:pos.size].sum() - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size))
        out["predictors"][name] = {"spearman": rho, "auc": auc}
    return out


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of MalConv and of the GBDT.")
    parser.add_argument("--selection", type=Path, default=None, help="Both-detect malware from cm_disagreement_select.py --both_detect (default: artifacts/explanation_set/ts-both-detect-seed{seed}.parquet).")
    parser.add_argument("--num_files", type=int, default=0, help="Only the first files (0: all); a small value is the WP4 gate.")
    parser.add_argument("--num_windows", type=int, default=256, help="Windows for the GBDT occlusion baseline (to be the best of Section 5.1).")
    parser.add_argument("--max_iterations", type=int, default=50, help="The attack's query budget in gradient steps.")
    parser.add_argument("--per_iteration", type=int, default=64, help="Editable positions updated per step.")
    parser.add_argument("--drop_delta", type=float, default=1.0, help="The GBDT log-odds drop that counts as transfer (the gate's go criterion is the share above it).")
    parser.add_argument("--background_size", type=int, default=1000)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--predictions", type=Path, default=ROOT / "artifacts" / "checkpoints-predictions")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_transfer")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--tag", type=str, default="")
    parser.add_argument("--tables_only", action="store_true")
    args = parser.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    selection = args.selection or ROOT / "artifacts" / "explanation_set" / f"ts-both-detect-seed{args.seed}.parquet"
    outdir = args.outdir / (f"seed-{args.seed}" + (f"-{args.tag}" if args.tag else ""))
    outdir.mkdir(parents=True, exist_ok=True)

    gbdt_threshold, malconv_threshold = thresholds(args.models, args.features, args.predictions, args.seed, args.fpr)

    if args.tables_only:
        files = pl.read_parquet(outdir / "files.parquet")
        print(json.dumps(summarize(files, gbdt_threshold, args.drop_delta), indent=2))
        return

    files = pl.read_parquet(selection)
    if args.num_files > 0:
        files = files.sort("row").head(args.num_files)
    files = files.select(pl.col("row").alias("index"), "name", "shard", "position").sort("index")
    print(f"Attack transfer: {files.height} both-detected malware, MalConv/GBDT seed {args.seed}, device {args.device}.", flush=True)
    print(f"Thresholds (1% FPR): GBDT {gbdt_threshold:.3f}, MalConv {malconv_threshold:.3f}.", flush=True)

    # Phase 1 (GPU): the attack, file by file.
    t_0 = time.time()
    model = load_pretrained_malconv(args.checkpoints / f"malconv-seed{args.seed}.pt").to(args.device).eval()
    perturbed: dict[int, dict[str, Any]] = {}
    for r in tqdm(files.iter_rows(named=True), total=files.height, desc="attack", mininterval=10):
        data = load_sample(int(r["shard"]), int(r["position"]), r["name"], args.db)
        result = attack_malconv(model, data, threshold=malconv_threshold, max_iterations=args.max_iterations,
                                per_iteration=args.per_iteration, device=args.device)
        perturbed[int(r["index"])] = {"perturbed": result.data, "changed": result.changed,
                                      "malconv_f0": result.log_odds_0, "malconv_perturbed": result.log_odds,
                                      "malconv_evaded": bool(result.evaded), "attack_queries": result.queries,
                                      "attack_iterations": result.iterations, "changed_bytes": int(result.changed.sum())}
    seconds_attack = time.time() - t_0
    del model
    print(f"Phase 1 (attack on {args.device}): {seconds_attack:.0f} s.", flush=True)

    # Phase 2 (CPU): the GBDT's explanations and its score on the perturbed files.
    background = np.asarray(load_features(args.features, "tr")[0][pl.read_parquet(ROOT / "artifacts" / "explanations" / "ember2024" / "background.parquet")["row"].to_numpy()[:args.background_size]], dtype=np.float64)
    tasks = [{"index": int(r["index"]), "name": r["name"], "shard": int(r["shard"]), "position": int(r["position"]),
              "dbdir": args.db, "num_windows": args.num_windows} | perturbed[int(r["index"])] for r in files.iter_rows(named=True)]
    t_0 = time.time()
    model_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    infos: list[dict[str, Any]] = []
    # Spawn, not fork: phase 1 initialized a CUDA context in this process, which a forked worker cannot use.
    with mp.get_context("spawn").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file, background)) as pool:
        for info in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="gbdt", mininterval=10):
            infos.append(info)
            if info["status"] != "ok":
                print(f"File {info['index']}: {info.get('error')}", flush=True)
    seconds_gbdt = time.time() - t_0

    meta = {int(r["index"]): perturbed[int(r["index"])] for r in files.iter_rows(named=True)}
    rows = [info | {k: meta[info["index"]][k] for k in ("malconv_f0", "malconv_perturbed", "malconv_evaded",
            "attack_queries", "attack_iterations", "changed_bytes")} for info in infos]
    files_df = pl.DataFrame(rows, infer_schema_length=None).sort("index")
    files_df.write_parquet(outdir / "files.parquet")
    summary = summarize(files_df, gbdt_threshold, args.drop_delta)
    report = {"seed": args.seed, "selection": selection.as_posix(), "num_windows": args.num_windows,
              "max_iterations": args.max_iterations, "per_iteration": args.per_iteration,
              "gbdt_threshold": gbdt_threshold, "malconv_threshold": malconv_threshold,
              "seconds_attack": seconds_attack, "seconds_gbdt": seconds_gbdt,
              "failed": int((files_df["status"] != "ok").sum())} | summary
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
