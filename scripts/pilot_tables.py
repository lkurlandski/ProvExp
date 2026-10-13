"""
Print the tables of the pilot census report (the old Phase 2 pilot report, in git history) from the census and, if present, the pullback agreement.

Usage:
    python scripts/pilot_tables.py --seed 0
"""

from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
from numpy import typing as npt
import polars as pl
from scipy.stats import spearmanr

from provexp.featuresets.ember2024.features import PEFeatureExtractor


ROOT = Path(__file__).parent.parent
EXPLAINERS = ["treeshap_path", "treeshap_interventional", "integrated_gradients", "gradient_x_input"]


def quantiles(x: npt.ArrayLike, q: tuple[float, ...] = (0.1, 0.5, 0.9)) -> str:
    return " / ".join(f"{v:.2f}" for v in np.nanquantile(np.asarray(x, dtype=np.float64), q))


def markdown(df: pl.DataFrame) -> str:
    def fmt(v: object) -> str:
        return f"{v:.3f}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    parser = ArgumentParser(description="Print the tables of the pilot report.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    args = parser.parse_args()

    indir = args.explanations / f"seed-{args.seed}"
    census = pl.read_parquet(indir / "census" / "census.parquet").filter(pl.col("status") == "ok")
    attributable = np.load(indir / "census" / "attributable.npy")
    samples = pl.read_parquet(indir / "samples.parquet")
    report = json.loads((indir / "report.json").read_text())
    if "statistics" not in json.loads((indir / "census" / "report.json").read_text()):
        print("NOTE: this census predates the 2026-10-08 definitions of ambiguity and overlap (normalized entropy and "
              "pairwise overlap); the old pilot report (git history) has those. Rerun scripts/provenance_census.py for the current ones.\n")
    names = PEFeatureExtractor().feature_names
    prefix = np.array([n.split(":", 1)[0] for n in names])
    groups = list(dict.fromkeys(prefix.tolist()))
    A = {e: np.load(indir / f"{e}.npy") for e in EXPLAINERS}
    labels = samples["label"].to_numpy()

    print("## Completeness of the explanations (max |sum(a) - (f(x) - baseline)| per sample)\n")
    rows: list[dict[str, object]] = []
    for e in EXPLAINERS:
        if "baseline_output" not in report[e]:
            continue
        out = samples["gbdt_log_odds" if e.startswith("treeshap") else "mlp_log_odds"].to_numpy()
        err = np.abs(A[e].sum(axis=1) - (out - report[e]["baseline_output"]))
        rows.append({"explainer": e, "median": float(np.median(err)), "p99": float(np.quantile(err, 0.99)), "max": float(err.max()), "n > 1e-3": int((err > 1e-3).sum())})
    print(markdown(pl.DataFrame(rows)), "\n")

    print("## Provenance statistics per subset (median over files; benign / malware)\n")
    table = (
        census.group_by("subset", "label", maintain_order=True)
        .agg(pl.col("num_features").first().alias("features"), pl.col("coverage", "ambiguity", "overlap").median())
        .pivot(on="label", index=["subset", "features"], values=["coverage", "ambiguity", "overlap"])
    )
    print(markdown(table), "\n")

    # Features that are never attributable in any file cannot be localized by construction; the others are
    # unattributable only in the files where they are (e.g., an empty hash bucket).
    never = ~attributable.any(axis=0)
    print(f"Never attributable in any file: {int(never.sum())} features; by subset: "
          + ", ".join(f"{g} {int(never[prefix == g].sum())}/{int((prefix == g).sum())}" for g in groups if never[prefix == g].any()), "\n")

    print("## Localizability of the explanations (10th / 50th / 90th percentile; benign | malware)\n")
    overall = census.filter(pl.col("subset") == "all")
    size = overall["num_elements"].to_numpy()
    rows = []
    for e in EXPLAINERS:
        a = np.abs(A[e])
        total = a.sum(axis=1)
        unattributable = np.where(attributable, 0.0, a)
        ell = overall[f"localizability:{e}"].to_numpy()
        rows.append({
            "explainer": e,
            "benign": quantiles(ell[overall["label"].to_numpy() == 0]),
            "malware": quantiles(ell[overall["label"].to_numpy() == 1]),
            "never-attributable share": float((unattributable[:, never].sum(axis=1) / total).mean()),
            "sometimes-attributable share": float((unattributable[:, ~never].sum(axis=1) / total).mean()),
            "spearman(l, size)": float(spearmanr(ell, size).statistic),
        })
    print(markdown(pl.DataFrame(rows)), "\n")

    L = np.array([overall[f"localizability:{e}"].to_numpy() for e in EXPLAINERS])
    print("Spearman correlation of localizability across explainers:\n")
    print(markdown(pl.DataFrame(np.round(spearmanr(L.T).statistic, 2), schema=EXPLAINERS).insert_column(0, pl.Series("", EXPLAINERS))), "\n")

    print("## Share of attribution magnitude per subset (mean over files)\n")
    rows = []
    for e in EXPLAINERS:
        a = np.abs(A[e])
        total = a.sum(axis=1)
        rows.append({"explainer": e} | {g: float((a[:, prefix == g].sum(axis=1) / total).mean()) for g in groups})
    print(markdown(pl.DataFrame(rows)), "\n")

    print("## Largest sources of non-localizable attribution (mean |a| over files on unattributable features)\n")
    for e in EXPLAINERS:
        m = np.where(attributable, 0.0, np.abs(A[e])).mean(axis=0)
        top = np.argsort(m)[::-1][:5]
        print(f"- {e}: " + "; ".join(f"`{names[j][:60]}` {m[j]:.3f}" for j in top))
    print()

    pullback = indir / "pullback"
    if not (pullback / "agreement.parquet").exists():
        print("(No pullback agreement yet; run scripts/pullback_agreement.py.)")
        return

    entropy = np.load(pullback / "entropy.npy")
    support = np.load(pullback / "support.npy")
    print("## Effective support of attributable features, exp(H_j), in elements and as a fraction of the file (median over attributable features and files)\n")
    effective = np.where(attributable, np.exp(entropy), np.nan)
    rows = [
        {
            "subset": g,
            "elements": float(np.nanmedian(effective[:, prefix == g])),
            "support |A_j|": float(np.nanmedian(np.where(attributable, support, np.nan)[:, prefix == g])),
            "fraction of file": f"{np.nanmedian(effective[:, prefix == g] / size[:, None]):.1e}",
        }
        for g in groups if attributable[:, prefix == g].any()
    ]
    print(markdown(pl.DataFrame(rows)), "\n")

    print("## Explanation-weighted effective support, sum |a_j| exp(H_j) / sum |a_j| over attributable j, as a fraction of the file\n")
    rows = []
    for e in EXPLAINERS:
        a = np.where(attributable, np.abs(A[e]), 0.0)
        w = (a * np.exp(np.nan_to_num(entropy))).sum(axis=1) / a.sum(axis=1) / size
        rows.append({"explainer": e, "benign": quantiles(w[labels == 0]), "malware": quantiles(w[labels == 1])})
    print(markdown(pl.DataFrame(rows)), "\n")

    print("## Agreement between explainers (median over files and pairs)\n")
    agreement = pl.read_parquet(pullback / "agreement.parquet").filter(pl.col("status") == "ok")
    table = agreement.group_by("space", "control").agg(pl.col("spearman", "cosine", "wjaccard").median()).sort("space", "control")
    print(markdown(table), "\n")
    table = (
        agreement.filter(~pl.col("control"))
        .group_by("explainer_1", "explainer_2", "space").agg(pl.col("spearman", "cosine", "wjaccard").median())
        .sort("explainer_1", "explainer_2", "space")
    )
    print(markdown(table), "\n")


if __name__ == "__main__":
    main()
