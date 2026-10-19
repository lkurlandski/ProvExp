"""
Print the tables of the PB1 pilot report (docs/experiments/pb1.md) from scripts/faithfulness.py's outputs.

Per file and model, with s the sign of the model's log-odds f(x) on the original file:
    removed(budget)     s · (f(x) - f(deleted)): the evidence for the predicted class removed by deleting the top
                        `budget` of the bytes (positive is good)
    recovered(budget)   s · (f(inserted) - f(fully ablated)): the evidence recovered by restoring them
    deletion area       the mean of removed() over the budgets below 100% (equal weight per log-spaced budget)
    insertion area      the mean of recovered() over the same budgets
    overshoot           the largest removed() below 100% minus removed(100%)
Random is the mean of its seeds. Runs without insertion (the default since the pilot) print deletion only.

Usage:
    python scripts/pb1_tables.py --seed 0 --fill zeros
"""

from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import wilcoxon

from provexp.featuresets.ember2024.features import PEFeatureExtractor


ROOT = Path(__file__).parent.parent


def markdown(df: pl.DataFrame, digits: int = 3) -> str:
    def fmt(v: object) -> str:
        return f"{v:.{digits}f}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    parser = ArgumentParser(description="Print the tables of the PB1 pilot report.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--fill", type=str, default="zeros")
    parser.add_argument("--indir", type=Path, default=ROOT / "artifacts" / "experiments" / "e1")
    args = parser.parse_args()

    indir = args.indir / f"seed-{args.seed}" / args.fill
    report = json.loads((indir / "report.json").read_text())
    files = pl.read_parquet(indir / "files.parquet").filter(pl.col("status") == "ok")
    curves = pl.read_parquet(indir / "curves.parquet")
    models = report.get("classifiers", ["gbdt", "mlp"])

    print("## Run\n")
    print(json.dumps({k: report[k] for k in ("num_files", "status", "invalid_curve_points", "curve_points", "files_with_invalid_windows", "files_with_file_specific_fields", "minutes")}), "\n")

    # Original and fully ablated log-odds per file and model.
    base = pl.concat([
        files.select("index", "label", pl.lit(model).alias("model"), pl.col(f"log_odds:{model}").alias("f0"), pl.col(f"log_odds_ablated:{model}").alias("fa"))
        for model in models
    ])
    c = (
        curves.filter(pl.col("valid"))
        .with_columns(pl.when(pl.col("method").str.starts_with("random:")).then(pl.lit("random"))
                      .when(pl.col("method").str.starts_with("random_features:")).then(pl.lit("random_features"))
                      .otherwise(pl.col("method")).alias("method"))
        .group_by("index", "model", "method", "curve", "budget").agg(pl.col("log_odds").mean())
        .join(base, on=["index", "model"])
        .with_columns(pl.col("f0").sign().replace(0, 1).alias("s"))
        .with_columns(
            pl.when(pl.col("curve") == "deletion")
            .then(pl.col("s") * (pl.col("f0") - pl.col("log_odds")))
            .otherwise(pl.col("s") * (pl.col("log_odds") - pl.col("fa")))
            .alias("evidence")
        )
    )

    print("## Evidence removed (deletion) and recovered (insertion) per budget, median over files\n")
    present = sorted(c["curve"].unique().to_list())
    for model in models:
        for curve in present:
            t = c.filter((pl.col("model") == model) & (pl.col("curve") == curve)).group_by("method", "budget").agg(pl.col("evidence").median()).sort("budget")
            t = t.with_columns(pl.col("budget").map_elements(lambda b: f"{b:.1%}", return_dtype=pl.String)).pivot(on="budget", index="method", values="evidence").sort("method")
            print(f"### {model}, {curve}\n")
            print(markdown(t, 2), "\n")

    areas = (
        c.filter(pl.col("budget") < 1.0).group_by("index", "label", "model", "method", "curve").agg(pl.col("evidence").mean().alias("area"))
    )
    print("## Areas (mean over budgets below 100%): mean over files, and the paired comparison per file\n")
    rows = []
    for model in models:
        for curve in present:
            a = areas.filter((pl.col("model") == model) & (pl.col("curve") == curve)).pivot(on="method", index="index", values="area").drop_nulls()
            methods = sorted(m for m in a.columns if m not in ("index", "random", "occlusion"))
            for method in methods + ["occlusion", "random"]:
                x = a[method].to_numpy()
                row: dict[str, object] = {"model": model, "curve": curve, "method": method, "files": len(x), "mean area": float(x.mean())}
                for ref in ("random", "occlusion"):
                    if method == ref:
                        row[f"wins vs {ref}"], row[f"p vs {ref}"] = "", ""
                        continue
                    y = a[ref].to_numpy()
                    row[f"wins vs {ref}"] = f"{int((x > y).sum())}/{len(x)}"
                    row[f"p vs {ref}"] = f"{wilcoxon(x, y).pvalue:.1e}" if np.any(x != y) else "n/a"
                gain_random = a["random"].to_numpy().mean()
                gain_occlusion = a["occlusion"].to_numpy().mean() - gain_random
                row["gain / occlusion gain"] = float((x.mean() - gain_random) / gain_occlusion) if gain_occlusion != 0 else float("nan")
                rows.append(row)
    print(markdown(pl.DataFrame(rows), 2), "\n")

    # Paired comparisons beyond "vs. occlusion at K": the byte-level pullbacks against every direct baseline, the
    # pullback against occlusion at the same window count, and occlusion at its two finest window counts.
    rows = []
    for model in models:
        a = areas.filter((pl.col("model") == model) & (pl.col("curve") == "deletion")).pivot(on="method", index="index", values="area").drop_nulls()
        if a.is_empty():
            continue
        windows = {report["num_windows"]: "occlusion"} | {J: f"occlusion_k{J}" for J in report.get("sweep_windows", []) if f"occlusion_k{J}" in a.columns}
        direct = [m for m in list(windows.values()) + ["kernelshap_windows", "field_occlusion"] if m in a.columns]
        pullbacks = sorted(m for m in a.columns if m.startswith("pullback:"))
        pairs = [(m, d, "byte-level pullback vs. direct baseline") for m in pullbacks for d in direct if d != "occlusion"]
        for J, d in sorted(windows.items()):
            prefix = "pullback_k:" if d == "occlusion" else f"pullback_k{J}:"
            pairs += [(m, d, f"same window count ({J})") for m in sorted(c for c in a.columns if c.startswith(prefix))]
        if len(windows) > 1:
            coarse, fine = sorted(windows)[-2:]
            pairs.append((windows[fine], windows[coarse], "occlusion: finest vs. next finest"))
        if len(pairs) == 0:
            continue
        gain_random = a["random"].to_numpy().mean()
        gain_occlusion = a["occlusion"].to_numpy().mean() - gain_random
        for x_name, y_name, kind in pairs:
            x, y = a[x_name].to_numpy(), a[y_name].to_numpy()
            rows.append({
                "model": model, "comparison": kind, "method": x_name, "against": y_name,
                "gain": float((x.mean() - gain_random) / gain_occlusion), "gain against": float((y.mean() - gain_random) / gain_occlusion),
                "wins": f"{int((x > y).sum())}/{len(x)}", "p": f"{wilcoxon(x, y).pvalue:.1e}" if np.any(x != y) else "n/a",
            })
    if rows:
        print("## Paired comparisons (deletion): gains relative to occlusion at the primary window count\n")
        print(markdown(pl.DataFrame(rows), 3), "\n")

    print("## Overshoot beyond full ablation (deletion): median over files, and the share of files above 0.5\n")
    d = c.filter(pl.col("curve") == "deletion")
    peak = d.filter(pl.col("budget") < 1.0).group_by("index", "model", "method").agg(pl.col("evidence").max().alias("peak"))
    full = d.filter(pl.col("budget") == 1.0).select("index", "model", "method", pl.col("evidence").alias("full"))
    overshoot = peak.join(full, on=["index", "model", "method"]).with_columns((pl.col("peak") - pl.col("full")).alias("overshoot"))
    t = (
        overshoot.group_by("model", "method").agg(pl.col("overshoot").median().alias("median overshoot"), (pl.col("overshoot") > 0.5).mean().alias("share > 0.5"))
        .sort("model", "method")
    )
    print(markdown(t, 2), "\n")

    # The unsigned ranking against the signed one, per explainer: on how many files it reduces the overshoot.
    rows = []
    for model in models:
        o = overshoot.filter(pl.col("model") == model).pivot(on="method", index="index", values="overshoot").drop_nulls()
        for unsigned in sorted(m for m in o.columns if m.startswith("pullback_abs:")):
            signed = unsigned.replace("pullback_abs:", "pullback:")
            if signed not in o.columns:
                continue
            x, y = o[unsigned].to_numpy(), o[signed].to_numpy()
            rows.append({
                "model": model, "explainer": unsigned.split(":", 1)[1], "signed": float(np.median(y)), "unsigned": float(np.median(x)),
                "reduced": f"{int((x < y).sum())}/{len(x)}", "p": f"{wilcoxon(x, y).pvalue:.1e}" if np.any(x != y) else "n/a",
            })
    if rows:
        print("### Signed vs. unsigned ranking of the byte-level pullback: median overshoot, files where unsigned reduces it\n")
        print(markdown(pl.DataFrame(rows), 2), "\n")

    # Cost vs. faithfulness: the extractions each direct method needs (the pullbacks need one).
    cost_columns = {"occlusion": "occlusion_extractions", "kernelshap_windows": "kernelshap_windows_extractions", "field_occlusion": "field_oracle_extractions"}
    cost_columns |= {f"occlusion_k{J}": f"occlusion_extractions_k{J}" for J in report.get("sweep_windows", []) if J != report["num_windows"]}
    cost_columns |= {f"kernelshap_k{J}": f"kernelshap_k{J}_extractions" for J in report.get("kernelshap_windows", [])}
    cost_columns |= {f"partition_b{B}": f"partition_b{B}_extractions" for B in report.get("partition_budgets", [])}
    # The legacy KernelSHAP at --num_windows stands in for kernelshap_k{num_windows} when it was reused.
    if f"kernelshap_k{report['num_windows']}_extractions" not in files.columns:
        cost_columns[f"kernelshap_k{report['num_windows']}"] = "kernelshap_windows_extractions"
    cost_columns = {k: v for k, v in cost_columns.items() if v in files.columns}
    if len(cost_columns) > 1:
        print("## Cost vs. faithfulness (deletion): median extractions and seconds per file, mean area\n")
        a = areas.filter(pl.col("curve") == "deletion").group_by("model", "method").agg(pl.col("area").mean())
        rows = []
        for method, column in cost_columns.items():
            seconds = column.replace("occlusion_extractions", "seconds_occlusion").replace("kernelshap_windows_extractions", "seconds_kernelshap_windows").replace("field_oracle_extractions", "seconds_field_oracle")
            if column.startswith(("kernelshap_k", "partition_b")):
                seconds = "seconds_" + column.removesuffix("_extractions")
            for model in models:
                area = a.filter((pl.col("model") == model) & (pl.col("method") == method))["area"]
                rows.append({"model": model, "method": method, "extractions": float(files[column].median() or 0), "seconds": float(files[seconds].median() or 0), "mean area": float(area[0]) if area.len() else float("nan")})  # type: ignore[arg-type]
        for model in models:
            for method in sorted(m for m in a.filter(pl.col("model") == model)["method"].to_list() if m.startswith("pullback")):
                area = a.filter((pl.col("model") == model) & (pl.col("method") == method))["area"]
                rows.append({"model": model, "method": method, "extractions": 1.0, "seconds": float(files["seconds_instrumented"].median() or 0), "mean area": float(area[0])})  # type: ignore[arg-type]
        print(markdown(pl.DataFrame(rows).sort("model", "extractions", "method"), 2), "\n")

    print("## Deletion area by label (mean over files)\n")
    t = areas.filter(pl.col("curve") == "deletion").group_by("model", "method", "label").agg(pl.col("area").mean()).sort("label").pivot(on="label", index=["model", "method"], values="area").sort("model", "method")
    print(markdown(t, 2), "\n")

    print("## Cost per file (median; seconds)\n")
    cost = files.select(
        pl.col("num_elements").median().alias("bytes"),
        pl.col("seconds_instrumented").median().alias("instrumented extraction"),
        pl.col("seconds_occlusion").median().alias(f"occlusion ({report['num_windows']} windows)"),
        (pl.col("seconds_occlusion") / pl.col("seconds_instrumented")).median().alias("occlusion / instrumented"),
        pl.col("occlusion_extractions").median().alias("occlusion extractions"),
        pl.col("seconds_protect").median().alias("protection (setup)"),
    )
    print(markdown(cost, 3), "\n")

    print("## Black-box vs. instrumented provenance, coarsened to the windows\n")
    npz = np.load(indir / "provenance.npz")
    tv, attributable, estimated = npz["tv"], npz["attributable"], npz["estimated"]
    names = PEFeatureExtractor().feature_names
    prefix = np.array([n.split(":", 1)[0] for n in names])
    rows = []
    for g in dict.fromkeys(prefix.tolist()):
        cols = prefix == g
        both = attributable[:, cols] & estimated[:, cols]
        rows.append({
            "subset": g,
            "attributable (instrumented)": float(attributable[:, cols].mean()),
            "attributable (black-box)": float(estimated[:, cols].mean()),
            "instrumented only": float((attributable[:, cols] & ~estimated[:, cols]).mean()),
            "black-box only": float((~attributable[:, cols] & estimated[:, cols]).mean()),
            "median TV where both": float(np.nanmedian(tv[:, cols][both])) if both.any() else float("nan"),
        })
    print(markdown(pl.DataFrame(rows), 3), "\n")

    # Section 5.2: feature rankings scored by byte deletion, relative to the reference (the pullback of TreeSHAP itself).
    reference = "pullback:treeshap_interventional"
    is_feature = pl.any_horizontal(pl.col("method").str.starts_with(p) for p in ("pushforward:", "trend_", "random_features"))
    a = areas.filter(pl.col("curve") == "deletion")
    if a.filter(is_feature).height and a.filter(pl.col("method") == reference).height:
        print(f"## Pushforward (Section 5.2): deletion area relative to {reference}, median over files\n")
        ref = a.filter(pl.col("method") == reference).select("index", "model", pl.col("area").alias("ref"))
        t = (a.filter(is_feature).join(ref, on=["index", "model"])
             .with_columns((pl.col("area") / pl.col("ref")).alias("relative"))
             .group_by("model", "method").agg(pl.col("relative").median().alias("median relative"), pl.col("area").mean().alias("mean area"), pl.len().alias("files"))
             .sort("model", "method"))
        print(markdown(t, 3), "\n")


if __name__ == "__main__":
    main()
