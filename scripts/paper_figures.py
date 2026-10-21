"""
Data files for the manuscript's pgfplots figures and result tables, written to `manuscript/assets/data/`.

    pb_gbdt.dat      pullback faithfulness on the GBDT (Section 5.1; runs 66 and 74): per deletion budget, the median GBDT
                     evidence removed by each ranking in PB_CURVES
    pb_gbdt_area.dat the same experiment's deletion areas (mean evidence removed over the budgets below 100%), mean over
                     the files, with the median feature extractions per file (Figure 3, right; the areas in the text)
    pf_gbdt.dat      the pushforward on the GBDT (Section 5.2; runs 66 and 74): per resolution of the source, the median over
                     files of each pushed-forward ranking's deletion area relative to the pullback of TreeSHAP
    pf_malconv.dat   the pushforward on MalConv (Section 5.2; run 67): per deletion budget, the median MalConv
                     evidence removed by each ranking, over the files with every deletion verified

Usage:
    python scripts/paper_figures.py
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import polars as pl


__all__ = [
    "pb_gbdt_areas",
    "pb_gbdt_curves",
    "pf_gbdt_resolution",
    "pf_malconv_curves",
]


ROOT = Path(__file__).parent.parent
METHODS = ("pushforward", "pushforward:occlusion_k1024", "pushforward:kernelshap_k1024", "surrogate", "ig_k256", "random_feat",
           "random")
EXPLAINER = "treeshap_interventional"
PB_CURVES = {
    f"pullback:{EXPLAINER}": "pullback",
    "occlusion": "occlusion_k256",
    "occlusion_k4096": "occlusion_k4096",
    "kernelshap_k1024": "kernelshap_k1024",
    "kernelshap_k4096": "kernelshap_k4096",
    "partition_b4096": "adaptive_b4096",
    "random": "random",
}
PB_AREAS = {
    f"pullback_k64:{EXPLAINER}": ("pullback_k64", None),
    f"pullback_k:{EXPLAINER}": ("pullback_k256", None),
    f"pullback_k1024:{EXPLAINER}": ("pullback_k1024", None),
    f"pullback_k4096:{EXPLAINER}": ("pullback_k4096", None),
    f"pullback:{EXPLAINER}": ("pullback", None),
    "occlusion_k64": ("occlusion_k64", "occlusion_extractions_k64"),
    "occlusion": ("occlusion_k256", "occlusion_extractions"),
    "occlusion_k1024": ("occlusion_k1024", "occlusion_extractions_k1024"),
    "occlusion_k4096": ("occlusion_k4096", "occlusion_extractions_k4096"),
    "kernelshap_k64": ("kernelshap_k64", "kernelshap_k64_extractions"),
    "kernelshap_windows": ("kernelshap_k256", "kernelshap_windows_extractions"),
    "kernelshap_k1024": ("kernelshap_k1024", "kernelshap_k1024_extractions"),
    "kernelshap_k4096": ("kernelshap_k4096", "kernelshap_k4096_extractions"),
    "partition_b64": ("adaptive_b64", "partition_b64_extractions"),
    "partition_b256": ("adaptive_b256", "partition_b256_extractions"),
    "partition_b1024": ("adaptive_b1024", "partition_b1024_extractions"),
    "partition_b4096": ("adaptive_b4096", "partition_b4096_extractions"),
    "random": ("random", None),
}
# Section 5.2 on the GBDT: per source resolution (windows; the bytes drawn at 2^20), the pushed-forward rankings.
PF_WINDOWS = {64: "_k64", 256: "_k256", 1024: "_k1024", 4096: "_k4096", 2**20: "_bytes"}
PF_SOURCES = {
    "trend": "trend{k}:" + EXPLAINER,
    "occlusion": "pushforward:occlusion{k}",
    "kernelshap": "pushforward:kernelshap{k}",
    "adaptive": "pushforward:partition{b}",
}


################################################################################
# Pullback on the GBDT
################################################################################


def _pb_gbdt_evidence(run: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """The GBDT evidence removed per (file, ranking, budget), as scripts/pb1_tables.py computes it, and the files."""
    curves = pl.read_parquet(run / "curves.parquet")
    files = pl.read_parquet(run / "files.parquet").filter(pl.col("status") == "ok")
    c = (
        curves.filter(pl.col("valid") & (pl.col("model") == "gbdt") & (pl.col("curve") == "deletion"))
        .with_columns(pl.col("method").str.replace(r"^(random|random_features):\d+$", "${1}"))
        .group_by("index", "method", "budget").agg(pl.col("log_odds").mean())
        .join(files.select("index", pl.col("log_odds:gbdt").alias("f0")), on="index")
        .with_columns((pl.col("f0").sign().replace(0, 1) * (pl.col("f0") - pl.col("log_odds"))).alias("removed"))
    )
    return c, files


def pb_gbdt_curves(run: Path) -> pl.DataFrame:
    """
    The median GBDT evidence removed per (budget, ranking) for the rankings in PB_CURVES.

    Args:
        run: A scripts/faithfulness.py output directory (run 74, which extends run 66).

    Returns:
        One row per budget (budgets up to 50%, in percent), one column per ranking.
    """
    c, _ = _pb_gbdt_evidence(run)
    c = c.filter(pl.col("method").is_in(list(PB_CURVES)) & (pl.col("budget") <= 0.5))
    wide = c.group_by("method", "budget").agg(pl.col("removed").median()).pivot(on="method", index="budget", values="removed")
    missing = [m for m in PB_CURVES if m not in wide.columns]
    if missing:
        raise RuntimeError(f"The run has no rankings {missing}.")
    return wide.sort("budget").select(pl.col("budget") * 100, *[pl.col(m).alias(n) for m, n in PB_CURVES.items()])


def pb_gbdt_areas(run: Path) -> pl.DataFrame:
    """
    The deletion area of each ranking in PB_AREAS, mean over the files with every ranking, and its cost.

    Args:
        run: A scripts/faithfulness.py output directory (run 74, which extends run 66).

    Returns:
        One row per ranking: its area (mean evidence removed over the budgets below 100%), its gain (area over random,
        relative to occlusion at 256 windows), and the median feature extractions per file (1 for the pullbacks, whose
        P comes with the single extraction; 0 for random).
    """
    c, files = _pb_gbdt_evidence(run)
    areas = (
        c.filter(pl.col("budget") < 1.0).group_by("index", "method").agg(pl.col("removed").mean().alias("area"))
        .pivot(on="method", index="index", values="area").drop_nulls()
    )
    missing = [m for m in PB_AREAS if m not in areas.columns]
    if missing:
        raise RuntimeError(f"The run has no rankings {missing}.")
    random = float(areas["random"].to_numpy().mean())
    occlusion = float(areas["occlusion"].to_numpy().mean())
    rows = []
    for method, (name, cost) in PB_AREAS.items():
        area = float(areas[method].to_numpy().mean())
        extractions = float(np.median(files[cost].to_numpy())) if cost is not None else (0.0 if method == "random" else 1.0)
        rows.append({"method": name, "area": area, "gain": (area - random) / (occlusion - random), "extractions": extractions})
    return pl.DataFrame(rows)


################################################################################
# Pushforward on the GBDT
################################################################################


def pf_gbdt_resolution(run: Path) -> pl.DataFrame:
    """
    The deletion area of each pushed-forward ranking relative to the pullback of TreeSHAP, per source resolution.

    Args:
        run: A scripts/faithfulness.py output directory with the pushforward and the trend (run 74).

    Returns:
        One row per resolution (windows; the bytes at 2^20), one column per source in PF_SOURCES: the median over files
        of the ranking's area over the reference's area, as scripts/pb1_tables.py reports it; NaN where not run.
    """
    c, _ = _pb_gbdt_evidence(run)
    areas = (
        c.filter(pl.col("budget") < 1.0).group_by("index", "method").agg(pl.col("removed").mean().alias("area"))
        .pivot(on="method", index="index", values="area")
    )
    reference = f"pullback:{EXPLAINER}"
    if reference not in areas.columns:
        raise RuntimeError(f"The run has no reference ranking {reference}.")
    rows = []
    for windows, k in PF_WINDOWS.items():
        row: dict[str, float] = {"windows": float(windows)}
        for name, pattern in PF_SOURCES.items():
            method = pattern.format(k=k, b=k.replace("_k", "_b"))
            # NOTE: the primary window count (256) is stored without a suffix for some methods (e.g., occlusion).
            if method not in areas.columns and method.endswith("_k256"):
                method = method.removesuffix("_k256")
            if method in areas.columns:
                ratio = areas.select(pl.col(method) / pl.col(reference)).drop_nulls().to_series().to_numpy()
                row[name] = float(np.median(ratio))
            else:
                row[name] = float("nan")
        rows.append(row)
    return pl.DataFrame(rows)


################################################################################
# Pushforward on MalConv
################################################################################


def pf_malconv_curves(run: Path) -> pl.DataFrame:
    """
    The median MalConv evidence removed per (budget, ranking), as `summarize` in scripts/pf_malconv.py prints it.

    Args:
        run: A scripts/pf_malconv.py output directory.

    Returns:
        One row per budget (budgets up to 50%), one column per ranking in METHODS.
    """
    curves = pl.read_parquet(run / "curves.parquet")
    files = pl.read_parquet(run / "files.parquet").filter(pl.col("status") == "ok")
    c = curves.join(files.select("index", pl.col("malconv_log_odds").alias("m0")), on="index").filter(pl.col("budget") <= 0.5)
    c = c.with_columns((pl.col("m0").sign() * (pl.col("m0") - pl.col("malconv"))).alias("removed"),
                       pl.col("method").str.replace(r":\d+$", "").alias("method"))
    valid = c.group_by("index").agg(pl.col("valid").all()).filter(pl.col("valid"))["index"]
    c = c.filter(pl.col("index").is_in(valid.implode()))
    per_file = c.group_by("index", "method", "budget").agg(pl.col("removed").mean())
    table = per_file.group_by("method", "budget").agg(pl.col("removed").median())
    wide = table.pivot(on="method", index="budget", values="removed").sort("budget")
    missing = [m for m in METHODS if m not in wide.columns]
    if missing:
        raise RuntimeError(f"The run has no rankings {missing}.")
    names = {m: m.replace("pushforward:", "pf_") for m in METHODS}
    return wide.select("budget", *[pl.col(m).alias(n) for m, n in names.items()]).with_columns(pl.col("budget") * 100)


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Write the data files of the manuscript's figures.")
    parser.add_argument("--pb_gbdt", type=Path, default=ROOT / "artifacts" / "experiments" / "e1" / "seed-0" / "zeros-typical-header-shared-ks4096")
    parser.add_argument("--pf_malconv", type=Path, default=ROOT / "artifacts" / "experiments" / "pf_malconv" / "seed-0-shared")
    parser.add_argument("--outdir", type=Path, default=ROOT / "manuscript" / "assets" / "data")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    pb = pb_gbdt_curves(args.pb_gbdt)
    pb.write_csv(args.outdir / "pb_gbdt.dat", separator=" ", float_precision=4)
    print(pb)
    pb_areas = pb_gbdt_areas(args.pb_gbdt)
    pb_areas.write_csv(args.outdir / "pb_gbdt_area.dat", separator=" ", float_precision=4)
    print(pb_areas)
    pf_gbdt = pf_gbdt_resolution(args.pb_gbdt)
    pf_gbdt.write_csv(args.outdir / "pf_gbdt.dat", separator=" ", float_precision=4)
    print(pf_gbdt)
    pf = pf_malconv_curves(args.pf_malconv)
    pf.write_csv(args.outdir / "pf_malconv.dat", separator=" ", float_precision=4)
    print(pf)


if __name__ == "__main__":
    main()
