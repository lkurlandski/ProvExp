"""
The scale-up's reporting duties (PLAN.md step 3 (g) and session 63's list), read from the stored models and attack
outputs under one output root; runs no attack.

FOR ACADEMIC SECURITY RESEARCH ONLY. Reads stored outputs of attacks run against our own detectors.

Per detector of the registry's `scaleup` set whose model exists:

    detection         AUC, and the test split's TPR and FPR at the thresholds set at 1% and 0.1% FPR on the validation
                      split's goodware; the evaluation set's malware detected at each threshold
    margins (R3)      the detected evaluation malware whose logit lies within the hand table's maximum drop (1.57 logits)
                      above the threshold: the only ones the hand table's errors could carry below it
    still detected    after each attack (each toolkit attack, the adaptive search, MAB-Malware) and after any of them,
                      at 1% and 0.1% FPR: the evaluation malware detected on the original and not evaded, over ALL the
                      evaluation set's malware (files outside the population counted; undetected ones count as not
                      detected). An output counts only if it is valid and within the byte budget, as each attack's own
                      `evaded`; at 0.1% FPR evasion is re-read from the stored scores (each attack lowers the score, and
                      one that stopped at the 1% threshold is below the 0.1% one too). Escapes: the same, per escape,
                      for the adaptive search and the toolkit attacks after the escape write.
    fixed-feature gain (R15)   for the monotone detectors, the share of the model's split gain on features no edit of
                      the threat model moves (the derived table's free features)

Outputs, in `{outdir}/`: report.json, detection.csv, still_detected.csv (detector, escape, fpr, attack, malware,
detected, still_detected, share).

Usage:
    python pipeline/6-results/scaleup_tables.py --root artifacts/scaleup --outdir artifacts/scaleup/6-results/tables
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any

import lightgbm
import numpy as np
from numpy import typing as npt
import polars as pl
from sklearn.metrics import roc_auc_score

from provexp.data.tabular import load_features
from provexp.data.tabular import load_manifest
from provexp.detectors import detection_at
from provexp.detectors import model_threshold
from provexp.models.erdalt import load_detector
from provexp.registry import ESCAPES
from provexp.registry import scaleup_models

__all__ = ["attack_outputs", "fixed_gain_share", "still_detected"]

FPRS = (0.01, 0.001)

# The direction table each monotone detector was trained on (4-detectors/train/run.sh): its free features are those
# no edit of the threat model moves.
STEMS = {"monotone-features": "M_full-pre-control", "monotone-sums": "M_full-pre", "additions-only": "M_add-pre"}


################################################################################
# Attack outputs
################################################################################

def _read(paths: list[Path]) -> pl.DataFrame | None:
    """The concatenation of the parquets that exist (shards), or None."""
    frames = [pl.read_parquet(p) for p in paths if p.exists()]
    return pl.concat(frames, how="diagonal_relaxed") if frames else None


def attack_outputs(root: Path, escape: str = "none") -> pl.DataFrame:
    """Every stored attack output as (defense, attack, name, p_adv, usable): usable means valid and within budget.

    Args:
        root: The scale-up's output root.
        escape: `none` for the plain attacks, or an escape write (the adaptive search and the toolkit after it).

    Returns:
        One row per (defense, attack, file); `p_adv` is the score of the attack's end file (NaN when it has none).
    """
    att = root / "5-attacks"
    parts: list[pl.DataFrame] = []
    # The detectors' jobs and the leave-one-out folds (their defenses have names of their own); R19's donor control
    # (toolkit/donors-0) reuses the name `erdalt` and is read apart.
    tk_dirs = ([*sorted((att / "toolkit" / "main").glob("*")), *sorted((att / "toolkit" / "loo").glob("*"))]
               if escape == "none" else [att / "toolkit" / "escape" / escape])
    tk = _read([d / "results.parquet" for d in tk_dirs])
    if tk is not None:
        parts.append(tk.select("defense", "attack", "name", pl.col("p_adv").cast(pl.Float64),
                               (pl.col("ok") & pl.col("valid") & ~pl.col("over_budget")).alias("usable")))
    ad_dir = att / "adaptive" / escape
    ad = _read([ad_dir / "adaptive.parquet", *sorted(ad_dir.glob("shard-*/adaptive.parquet"))])
    if ad is not None:
        # The search keeps only candidates within the byte budget; its end file is extracted (--score real).
        parts.append(ad.select("defense", pl.lit("adaptive").alias("attack"), "name",
                               pl.col("p_adv_real").cast(pl.Float64).alias("p_adv"), pl.lit(True).alias("usable")))
    if escape == "none":
        mab = _read([att / "mab-malware" / "results.parquet", att / "mab-malware" / "expert" / "results.parquet"])
        if mab is not None:
            parts.append(mab.select("defense", pl.lit("mab-malware").alias("attack"), "name",
                                    pl.col("p_adv").cast(pl.Float64),
                                    (pl.col("has_output") & pl.col("ok") & pl.col("valid") & ~pl.col("over_budget"))
                                    .alias("usable")))
    if not parts:
        return pl.DataFrame(schema={"defense": pl.Utf8, "attack": pl.Utf8, "name": pl.Utf8, "p_adv": pl.Float64,
                                    "usable": pl.Boolean})
    return pl.concat(parts)


def still_detected(p_orig: dict[str, float], tau: float, outputs: pl.DataFrame, num_malware: int) -> dict[str, Any]:
    """The malware detected on the original and evaded by no usable output, over all `num_malware` malware.

    Args:
        p_orig: The detector's score of each evaluation malware (originals).
        tau: The threshold.
        outputs: This detector's outputs of one attack or a group of attacks (name, p_adv, usable).
        num_malware: The evaluation set's malware: the denominator.

    Returns:
        detected, evaded, still_detected, share (still_detected / num_malware), attacked (files with an output row).
    """
    detected = {n for n, p in p_orig.items() if p > tau}
    evaded = set(outputs.filter(pl.col("usable") & (pl.col("p_adv") <= tau))["name"].to_list()) & detected
    still = len(detected) - len(evaded)
    return {"detected": len(detected), "attacked": outputs["name"].n_unique(), "evaded": len(evaded),
            "still_detected": still, "share": still / num_malware if num_malware else None}


################################################################################
# R15 and R3
################################################################################

def fixed_gain_share(model_dir: Path, names: list[str], directions_dir: Path, stem: str) -> dict[str, Any]:
    """The share of a monotone GBDT's split gain on the features its table leaves free (no edit moves them)."""
    dropped = set((directions_dir / f"{stem}.neutralize.txt").read_text().splitlines()) - {""}
    constrained = {line.split("\t")[0] for line in (directions_dir / f"{stem}.monotone.tsv").read_text().splitlines()
                   if line.strip()}
    free = [j for j, n in enumerate(names) if n not in dropped and n not in constrained]
    gain = np.asarray(lightgbm.Booster(model_file=str(model_dir / "model.txt")).feature_importance("gain"), float)
    if gain.shape[0] != len(names):
        raise RuntimeError(f"{model_dir.as_posix()} has {gain.shape[0]} features, the store {len(names)}.")
    total = float(gain.sum())
    return {"stem": stem, "free_features": len(free), "gain_share": float(gain[free].sum()) / total if total else None}


def _logit(p: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    q = np.clip(p, 1e-15, 1 - 1e-15)
    out: npt.NDArray[np.float64] = np.log(q) - np.log1p(-q)
    return out


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, required=True, help="The scale-up's output root (OUT_ROOT).")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--files", type=Path, default=None, help="The evaluation set (default: the root's).")
    parser.add_argument("--max_drop", type=float, default=1.57, help="The hand table's maximum drop, in logits (R3).")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    files = args.files or args.root / "2-features" / "files" / "ts.parquet"
    malware = pl.read_parquet(files).filter(pl.col("label") == 1)["name"].to_list()
    models = {n: d for n, d in scaleup_models(args.root.as_posix()).items()
              if (Path(d.model) / "vl_predictions.parquet").exists()}
    print(f"{len(malware)} evaluation malware; {len(models)} trained detectors: {sorted(models)}", flush=True)

    # The originals' scores, from each detector's store (the rows its attacks were scored from).
    stores: dict[str, tuple[npt.NDArray[np.float32], list[str]]] = {}
    for store in sorted({d.features for d in models.values()}):
        X, meta = load_features(Path(store), "ts")
        row = dict(zip(meta["name"].to_list(), range(meta.height)))
        missing = [n for n in malware if n not in row]
        if missing:
            raise RuntimeError(f"{len(missing)} evaluation malware are not in {store}/ts: {missing[:3]}")
        stores[store] = (np.asarray(X[[row[n] for n in malware]], dtype=np.float32),
                         list(load_manifest(Path(store))["feature_names"]))

    outputs = {e: attack_outputs(args.root, e) for e in ("none", *ESCAPES)}
    report: dict[str, Any] = {"files": files.as_posix(), "malware": len(malware), "max_drop": args.max_drop,
                              "detectors": {}}
    detection_rows: list[dict[str, Any]] = []
    still_rows: list[dict[str, Any]] = []
    for name, det in models.items():
        mdir = Path(det.model)
        X, names = stores[det.features]
        p = np.asarray(load_detector(mdir, names).predict(X), dtype=np.float64)
        p_orig = dict(zip(malware, p.tolist()))
        pred = pl.read_parquet(mdir / "ts_predictions.parquet")
        entry: dict[str, Any] = {"auc": float(roc_auc_score(pred["label"].to_numpy(), pred["prob"].to_numpy()))}
        for fpr in FPRS:
            d = detection_at(mdir, fpr, "vl")
            tau = d["tau"]
            margin = _logit(p) - _logit(np.array([tau]))
            det_mask = p > tau
            row = {"detector": name, "fpr": fpr, "tau": tau, "test_tpr": d["tpr"], "test_fpr": d["fpr_ts"],
                   "auc": entry["auc"], "eval_detected": int(det_mask.sum()),
                   "eval_within_max_drop": int((det_mask & (margin <= args.max_drop)).sum()),
                   "eval_margin_median": float(np.median(margin[det_mask])) if det_mask.any() else None}
            detection_rows.append(row)
            entry[str(fpr)] = row
            for escape, out in outputs.items():
                mine = out.filter(pl.col("defense") == name)
                if escape != "none" and mine.height == 0:
                    continue
                groups = {a: mine.filter(pl.col("attack") == a) for a in sorted(set(mine["attack"].to_list()))}
                groups["any"] = mine
                for attack, rows in groups.items():
                    still_rows.append({"detector": name, "escape": escape, "fpr": fpr, "attack": attack,
                                       "malware": len(malware),
                                       **still_detected(p_orig, tau, rows, len(malware))})
        mine = outputs["none"].filter(pl.col("defense") == name)
        # A check, not a result: the toolkit's own clean scores (from the bytes, at attack time) against the store's.
        # They differ only if the store was built by another extractor than the attacks used.
        tk = _read([args.root / "5-attacks" / "toolkit" / "main" / name / "results.parquet"])
        if tk is not None and tk.height:
            clean = tk.unique("name").select("name", "p_clean")
            gap = np.abs(np.array([p_orig[n] for n in clean["name"].to_list()]) - clean["p_clean"].to_numpy())
            entry["clean_score_gap"] = float(gap.max())
            if gap.max() > 1e-4:
                print(f"  WARNING {name}: the store's scores differ from the attacks' by up to {gap.max():.4g}; was "
                      "the store built by the attacks' extractor?", flush=True)
        if name in STEMS:
            entry["fixed_gain"] = fixed_gain_share(mdir, names, args.root / "3-directions" / "loose", STEMS[name])
        report["detectors"][name] = entry
        print(f"{name:22s} AUC {entry['auc']:.4f}  TPR@1% {entry['0.01']['test_tpr']:.3f}  "
              f"TPR@0.1% {entry['0.001']['test_tpr']:.3f}  attack outputs {mine.height}", flush=True)

    pl.DataFrame(detection_rows).write_csv(args.outdir / "detection.csv")
    still = pl.DataFrame(still_rows) if still_rows else pl.DataFrame()
    still.write_csv(args.outdir / "still_detected.csv")
    if still.height:
        report["still_detected_after_any"] = (still.filter((pl.col("attack") == "any") & (pl.col("escape") == "none"))
                                              .select("detector", "fpr", "detected", "evaded", "still_detected",
                                                      "share").to_dicts())
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(f"Wrote {args.outdir.as_posix()}/{{report.json,detection.csv,still_detected.csv}}", flush=True)


if __name__ == "__main__":
    main()
