"""
Print the tables of the E2 census (docs/plan_e2.md) from scripts/provenance_census.py's outputs.

Tables:
    1. per subset (in isolation) and label: coverage, effective support, overlap, element coverage, push-pull diagonal
    2. the full feature set per label, and the correlation of its statistics with file size
    3. the subset confusion matrix (the blocks of M under the full provenance), mean over files
    4. the round-trip bound of each explainer: error, bound, and their ratio, relative to the attribution mass
    5. the spectrum of M on the attributable features: eigenvalues near 1 and near 0, participation ratio

Usage:
    python scripts/e2_tables.py --seed 0
"""

from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
from numpy import typing as npt
import polars as pl
from scipy.stats import spearmanr


ROOT = Path(__file__).parent.parent


def markdown(df: pl.DataFrame, digits: int = 3) -> str:
    def fmt(v: object) -> str:
        return f"{v:.{digits}g}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.iter_rows()]
    return "\n".join(lines)


def quantiles(x: npt.ArrayLike, q: tuple[float, ...] = (0.1, 0.5, 0.9)) -> str:
    v = np.asarray(x, dtype=np.float64)
    v = v[np.isfinite(v)]
    return " / ".join(f"{t:.3g}" for t in np.quantile(v, q)) if v.size else "—"


def main() -> None:
    parser = ArgumentParser(description="Print the tables of the E2 census.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--name", type=str, default="census")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    args = parser.parse_args()

    indir = args.explanations / f"seed-{args.seed}" / args.name
    report = json.loads((indir / "report.json").read_text())
    if "statistics" not in report:
        raise RuntimeError(f"{indir.as_posix()} predates the 2026-10-08 definitions; rerun scripts/provenance_census.py.")
    census = pl.read_parquet(indir / "census.parquet").filter(pl.col("status") == "ok")
    subsets: list[str] = report["subsets"]
    labels = census.filter(pl.col("subset") == "all").sort("index")["label"].to_numpy()
    print("## Run\n")
    print(json.dumps({k: report[k] for k in ("num_samples", "num_failed", "num_mismatched_features", "seconds_per_file", "minutes")}), "\n")

    print("## 1. Per subset, in isolation (median over files; 10th / 50th / 90th percentile for overlap)\n")
    rows = []
    for subset in ["all", *subsets]:
        t = census.filter(pl.col("subset") == subset)
        row: dict[str, object] = {"subset": subset, "features": int(t["num_features"][0])}
        for lab, name in ((0, "benign"), (1, "malware")):
            u = t.filter(pl.col("label") == lab)
            row[f"coverage ({name})"] = float(u["coverage"].median())  # type: ignore[arg-type]
        row["effective support"] = float(t["effective_support"].median())  # type: ignore[arg-type]
        has = t.filter(pl.col("num_attributable") > 0)
        row["overlap"] = quantiles(has["overlap"].to_numpy())
        row["element coverage"] = float(t["element_coverage"].median())  # type: ignore[arg-type]
        row["N_ii"] = float(t["push_pull_diagonal"].median())  # type: ignore[arg-type]
        rows.append(row)
    print(markdown(pl.DataFrame(rows)), "\n")

    print("## 2. Full feature set: benign vs. malware, and Spearman correlation with file size\n")
    full = census.filter(pl.col("subset") == "all")
    rows = []
    for column in ("coverage", "ambiguity", "effective_support", "overlap"):
        x = full[column].to_numpy()
        rho = spearmanr(x, full["num_elements"].to_numpy()).statistic
        rows.append({"statistic": column, "benign": quantiles(x[full["label"].to_numpy() == 0]), "malware": quantiles(x[full["label"].to_numpy() == 1]), "rho with size": float(rho)})
    print(markdown(pl.DataFrame(rows)), "\n")

    print("## 3. Subset confusion matrix (full provenance; mean over files; row: from, column: lands on)\n")
    confusion = np.load(indir / "confusion.npy")
    mean = np.nanmean(confusion, axis=0)
    present = ~np.all(np.isnan(confusion[:, :, 0]), axis=0)
    short = {s: s[:6] for s in subsets}
    table = pl.DataFrame({"from": [s for s, p in zip(subsets, present) if p]} | {
        short[s]: [float(mean[g, h]) for g, p in enumerate(present) if p] for h, s in enumerate(subsets) if present[h]
    })
    print(markdown(table, 2), "\n")
    for lab, name in ((0, "benign"), (1, "malware")):
        diag = np.nanmean(confusion[labels == lab], axis=0).diagonal()
        print(f"Diagonal ({name}): " + ", ".join(f"{s} {d:.2f}" for s, d, p in zip(subsets, diag, present) if p))
    print()

    print("## 4. Round-trip bound per explainer (attributable features; relative to ||a||_1; 10th / 50th / 90th)\n")
    rows = []
    for e in report["explainers"]:
        if f"pull_push_error:{e}" not in full.columns:
            continue
        t = full.drop_nulls(f"pull_push_error:{e}")
        l1 = t[f"pull_push_l1:{e}"].to_numpy()
        err = t[f"pull_push_error:{e}"].to_numpy()
        bound = t[f"pull_push_bound:{e}"].to_numpy()
        ok = l1 > 0
        rows.append({
            "explainer": e,
            "files": int(ok.sum()),
            "error / ||a||": quantiles(err[ok] / l1[ok]),
            "bound / ||a||": quantiles(bound[ok] / l1[ok]),
            "error / bound": quantiles(err[ok] / bound[ok]),
            "bound holds": f"{int((err <= bound + 1e-9).sum())}/{err.size}",
        })
    print(markdown(pl.DataFrame(rows)), "\n")

    print("## 5. Spectrum of M on the attributable features (per file; 10th / 50th / 90th)\n")
    spectrum = np.load(indir / "spectrum.npz")
    values, offsets = spectrum["values"], spectrum["offsets"]
    stats: dict[str, list[float]] = {"features": [], "> 0.99": [], "< 0.01": [], "participation ratio / n'": [], "1 - mean = O": []}
    for i in range(offsets.size - 1):
        v = values[offsets[i]:offsets[i + 1]].astype(np.float64)
        if v.size == 0:
            continue
        stats["features"].append(v.size)
        stats["> 0.99"].append(float((v > 0.99).mean()))
        stats["< 0.01"].append(float((v < 0.01).mean()))
        stats["participation ratio / n'"].append(float(v.sum() ** 2 / (v ** 2).sum() / v.size))
        stats["1 - mean = O"].append(float(1 - v.mean()))
    print(markdown(pl.DataFrame([{"quantity": k, "10th / 50th / 90th": quantiles(v)} for k, v in stats.items()])), "\n")
    print("Shares are of the attributable features; '> 0.99' are attribution patterns a round trip preserves, '< 0.01' "
          "patterns it (almost) erases; the mean eigenvalue is the trace / n' = 1 - O.\n")


if __name__ == "__main__":
    main()
