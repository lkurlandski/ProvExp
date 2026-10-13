"""
Explain the explanation set (see scripts/select_explanation_set.py) with the cheap feature-space explainers (stage 1).

Explainers:
    treeshap_path               GBDT, path-dependent TreeSHAP (LightGBM, no background)
    treeshap_interventional     GBDT, interventional TreeSHAP w.r.t. the background
    integrated_gradients        MLP, Integrated Gradients from the background mean
    gradient_x_input            MLP, gradient times input
    kernelshap_gbdt             GBDT, KernelSHAP (stage 2; expensive, usually with --subset)
    kernelshap_mlp              MLP, KernelSHAP (stage 2; expensive, usually with --subset)

KernelSHAP uses a small label-balanced subset of the background (saved as kernelshap_background.parquet) and no
feature selection (shap's default keeps only about 10 features).

The background is a fixed, label-balanced random sample of the training split, shared by every seed and explainer.
Every explainer attributes the malware log-odds and is computed in float64.

Outputs, in `{outdir}/`:
    background.parquet                     the background (rows of the training split's feature store)
    seed-{seed}/samples.parquet            the explained samples, in order, with each model's log-odds
    seed-{seed}/{explainer}.npy            float64 (N, d) attributions (NaN for samples outside --subset)
    seed-{seed}/report.json                per explainer: baseline output, completeness error, and timing

Usage:
    python scripts/explain.py --seed 0 --device cuda:0 --workers 16
"""

from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path
import time
from typing import Any
from typing import Optional

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
import torch
from torch import nn

from provexp.data.tabular import load_features
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import gradient_x_input
from provexp.explain.feature import integrated_gradients
from provexp.explain.feature import kernelshap
from provexp.explain.feature import log_odds
from provexp.explain.feature import mlp_function
from provexp.explain.feature import treeshap_interventional
from provexp.explain.feature import treeshap_path
from provexp.models.mlp import Standardize
from provexp.models.mlp import build_mlp


ROOT = Path(__file__).parent.parent
EXPLAINERS = ["treeshap_path", "treeshap_interventional", "integrated_gradients", "gradient_x_input"]
KERNELSHAP = ["kernelshap_gbdt", "kernelshap_mlp"]


def select_background(features: Path, size: int, seed: int) -> pl.DataFrame:
    """A label-balanced random sample of the training split's successfully extracted samples."""
    _, meta = load_features(features, "tr")
    meta = meta.filter(pl.col("status") == "ok")
    labels = sorted(meta["label"].unique().to_list())
    if size % len(labels) != 0:
        raise ValueError(f"The background size must be divisible by the number of labels ({len(labels)}). Got {size}.")
    parts = [meta.filter(pl.col("label") == label).sample(size // len(labels), seed=seed) for label in labels]
    return pl.concat(parts).select("row", "name", "label").sort("row")


def load_rows(features: Path, split: str, rows: npt.NDArray[np.int64]) -> npt.NDArray[np.float64]:
    X, _ = load_features(features, split)
    out = np.asarray(X[rows], dtype=np.float64)
    if not np.all(np.isfinite(out)):
        raise RuntimeError(f"Some selected rows of {split} are not finite.")
    return out


def load_mlp(path: Path, d: int, device: torch.device) -> nn.Module:
    model = build_mlp(Standardize(torch.zeros(d), torch.ones(d)))
    model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    return model.double().to(device).eval()


def _kernelshap_chunk(name: str, model_file: str, X: npt.NDArray[np.float64], background: npt.NDArray[np.float64], nsamples: int, seed: int) -> npt.NDArray[np.float64]:
    torch.set_num_threads(1)
    if name == "kernelshap_gbdt":
        f = gbdt_function(lgb.Booster(model_file=model_file))
    else:
        f = mlp_function(load_mlp(Path(model_file), X.shape[1], torch.device("cpu")))
    return np.concatenate([kernelshap(f, X[i:i + 1], background, nsamples=nsamples, seed=seed) for i in range(X.shape[0])])


def _interventional_chunk(model_file: str, X: npt.NDArray[np.float64], background: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return treeshap_interventional(lgb.Booster(model_file=model_file), X, background)


def explain(
    name: str,
    X: npt.NDArray[np.float64],
    background: npt.NDArray[np.float64],
    gbdt_file: Path,
    mlp_file: Path,
    device: torch.device,
    workers: int,
    ig_steps: int,
    kernel_background: Optional[npt.NDArray[np.float64]] = None,
    kernel_nsamples: int = 32768,
    seed: int = 0,
) -> tuple[npt.NDArray[np.float64], dict[str, Any]]:
    """
    Run one explainer. Returns the attributions (N, d) and a report, in which `completeness` is the largest absolute
    difference between the sum of a sample's attributions and its log-odds minus the baseline output.
    """
    if name in KERNELSHAP:
        if kernel_background is None:
            raise ValueError("KernelSHAP needs a background.")
        model_file = gbdt_file if name == "kernelshap_gbdt" else mlp_file
        if name == "kernelshap_gbdt":
            f_np = gbdt_function(lgb.Booster(model_file=str(gbdt_file)))
        else:
            f_np = mlp_function(load_mlp(mlp_file, X.shape[1], torch.device("cpu")))
        chunks = [c for c in np.array_split(np.arange(X.shape[0]), max(1, min(workers, X.shape[0]))) if c.size > 0]
        with ProcessPoolExecutor(len(chunks)) as pool:
            parts = pool.map(_kernelshap_chunk, [name] * len(chunks), [str(model_file)] * len(chunks), [X[c] for c in chunks], [kernel_background] * len(chunks), [kernel_nsamples] * len(chunks), [seed] * len(chunks))
            A = np.concatenate(list(parts))
        baseline = float(f_np(kernel_background).mean())
        completeness = float(np.abs(A.sum(axis=1) - (f_np(X) - baseline)).max())
        return A, {"model": model_file.as_posix(), "baseline_output": baseline, "nsamples": kernel_nsamples, "background": int(kernel_background.shape[0]), "completeness": completeness}

    if name in ("treeshap_path", "treeshap_interventional"):
        booster = lgb.Booster(model_file=str(gbdt_file))
        out = gbdt_function(booster)(X)
        if name == "treeshap_path":
            A, expected = treeshap_path(booster, X)
            baseline = float(expected[0])
        else:
            chunks = np.array_split(np.arange(X.shape[0]), max(1, min(workers, X.shape[0])))
            with ProcessPoolExecutor(len(chunks)) as pool:
                parts = pool.map(_interventional_chunk, [str(gbdt_file)] * len(chunks), [X[c] for c in chunks], [background] * len(chunks))
                A = np.concatenate(list(parts))
            baseline = float(gbdt_function(booster)(background).mean())
        return A, {"model": gbdt_file.as_posix(), "baseline_output": baseline, "completeness": float(np.abs(A.sum(axis=1) - (out - baseline)).max())}

    model = load_mlp(mlp_file, X.shape[1], device)
    f = log_odds(model)
    out = mlp_function(model, device)(X)
    x = torch.from_numpy(X).to(device)
    if name == "integrated_gradients":
        mean = torch.from_numpy(background.mean(axis=0)).to(device).unsqueeze(0)
        chunk = 32  # samples per batch, i.e., 32 * ig_steps points
        A = torch.cat([integrated_gradients(f, x[i:i + chunk], mean, steps=ig_steps, batch_size=256) for i in range(0, x.shape[0], chunk)]).cpu().numpy()
        baseline = float(mlp_function(model, device)(mean.cpu().numpy())[0])
        report = {"baseline_output": baseline, "steps": ig_steps, "completeness": float(np.abs(A.sum(axis=1) - (out - baseline)).max())}
    elif name == "gradient_x_input":
        A = torch.cat([gradient_x_input(f, x[i:i + 1024]) for i in range(0, x.shape[0], 1024)]).cpu().numpy()
        report = {}  # Gradient times input satisfies no completeness property.
    else:
        raise ValueError(f"Unknown explainer: {name}")
    return A, {"model": mlp_file.as_posix()} | report


def main() -> None:
    parser = ArgumentParser(description="Explain the explanation set with the stage-1 feature-space explainers.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained models.")
    parser.add_argument("--explainers", type=str, nargs="+", choices=EXPLAINERS + KERNELSHAP, default=EXPLAINERS)
    parser.add_argument("--subset", type=Path, default=None, help="A parquet file with a `name` column: explain only these samples (others are NaN).")
    parser.add_argument("--kernelshap_background", type=int, default=16, help="KernelSHAP background size (label-balanced).")
    parser.add_argument("--kernelshap_nsamples", type=int, default=32768)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--background_size", type=int, default=1000)
    parser.add_argument("--background_seed", type=int, default=0)
    parser.add_argument("--ig_steps", type=int, default=4096)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Processes for interventional TreeSHAP.")
    parser.add_argument("--limit", type=int, default=None, help="Explain at most this many samples (for testing).")
    parser.add_argument("--overwrite", action="store_true", help="Recompute explainers whose outputs exist.")
    parser.add_argument("--fill_missing", action="store_true", help="For explainers whose outputs exist, compute only the selected rows that are still NaN and keep the rest.")
    args = parser.parse_args()

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    device = torch.device(args.device)
    gbdt_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    mlp_file = args.models / "mlp" / f"seed-{args.seed}" / "model.pt"

    # The background is selected once and reused, so that every seed and explainer shares it.
    background_file = args.outdir / "background.parquet"
    if not background_file.exists():
        select_background(args.features, args.background_size, args.background_seed).write_parquet(background_file)
    background_meta = pl.read_parquet(background_file)
    if background_meta.height != args.background_size:
        raise RuntimeError(f"{background_file.as_posix()} has {background_meta.height} samples, not {args.background_size}.")
    background = load_rows(args.features, "tr", background_meta["row"].to_numpy())

    samples = pl.read_parquet(args.explanation_set).select("row", "name", "label")
    if args.limit is not None:
        samples = samples.head(args.limit)
    X = load_rows(args.features, "ts", samples["row"].to_numpy())
    print(f"Explaining {X.shape[0]} samples with a background of {background.shape[0]}.", flush=True)

    samples = samples.with_columns(
        pl.Series("gbdt_log_odds", gbdt_function(lgb.Booster(model_file=str(gbdt_file)))(X)),
        pl.Series("mlp_log_odds", mlp_function(load_mlp(mlp_file, X.shape[1], device), device)(X)),
    )
    samples_file = outdir / "samples.parquet"
    if samples_file.exists() and not args.overwrite:
        previous = pl.read_parquet(samples_file)
        if not previous.equals(samples):
            raise RuntimeError(f"{samples_file.as_posix()} describes different samples or models. Use --overwrite.")
    samples.write_parquet(samples_file)

    # KernelSHAP's background: a small label-balanced subset of the background, selected once and reused.
    kernel_file = args.outdir / "kernelshap_background.parquet"
    if not kernel_file.exists():
        per_label = args.kernelshap_background // 2
        parts = [background_meta.filter(pl.col("label") == lab).sample(per_label, seed=args.background_seed) for lab in (0, 1)]
        pl.concat(parts).sort("row").write_parquet(kernel_file)
    kernel_meta = pl.read_parquet(kernel_file)
    kernel_background = load_rows(args.features, "tr", kernel_meta["row"].to_numpy())

    # Optionally, explain only a subset of the samples; the other rows are NaN.
    rows = np.arange(X.shape[0])
    if args.subset is not None:
        names = set(pl.read_parquet(args.subset)["name"].to_list())
        rows = np.flatnonzero(samples["name"].is_in(list(names)).to_numpy())
        print(f"Explaining a subset of {rows.size} samples.", flush=True)

    report_file = outdir / "report.json"
    report: dict[str, Any] = json.loads(report_file.read_text()) if report_file.exists() else {}
    for name in args.explainers:
        todo = rows
        A = np.full(X.shape, np.nan)
        if (outdir / f"{name}.npy").exists() and not args.overwrite:
            if not args.fill_missing:
                print(f"{name}: exists, skipping.", flush=True)
                continue
            # Keep the rows already explained (e.g., the pilot's) and explain only the missing ones.
            A = np.load(outdir / f"{name}.npy")
            if A.shape != X.shape:
                raise RuntimeError(f"{name}.npy has shape {A.shape}, not {X.shape}.")
            todo = rows[~np.isfinite(A[rows]).all(axis=1)]
            print(f"{name}: {rows.size - todo.size} of {rows.size} rows exist, explaining {todo.size}.", flush=True)
            if todo.size == 0:
                continue
        t_0 = time.time()
        A_rows, info = explain(name, X[todo], background, gbdt_file, mlp_file, device, args.workers, args.ig_steps, kernel_background, args.kernelshap_nsamples, args.background_seed)
        A[todo] = A_rows
        info["seconds"] = time.time() - t_0
        info["samples"] = int(np.isfinite(A).all(axis=1).sum())
        np.save(outdir / f"{name}.npy", A)
        report[name] = info
        report_file.write_text(json.dumps(report, indent=2))
        print(f"{name}: {json.dumps(info)}", flush=True)
    print(f"Wrote {outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
