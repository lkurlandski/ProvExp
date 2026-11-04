"""
The price of each operation: training inputs for monotone GBDTs under the full catalogue minus one operation (or a
group of operations), and the table of their test metrics.

`derive` reads the per-operation signs of a derived direction table in the sums layout (`directions_sums.csv`, columns
`op_<op>_pre`), composes each variant's threat model with `a_directions.direction`, and writes
`{variant}.neutralize.txt` and `{variant}.monotone.tsv` as `a_directions.py` does. It checks that the full catalogue
reproduces the table's own `M_full_pre` column and the files training used, and skips variants whose training inputs
equal the full catalogue's. `table` prints AUC and TPR at 1% and 0.1% FPR for the trained models.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from sklearn.metrics import roc_curve

from a_directions import OPS
from a_directions import direction

__all__ = ["variants", "derive", "table"]


################################################################################
# Variants
################################################################################

# Operations that overwrite header bytes in place (the DOS header and stub, header fields, the checksum).
OVERWRITES = ("dos", "hdr", "chk")


def variants() -> dict[str, tuple[str, ...]]:
    """The threat models: the full catalogue, the full catalogue minus each operation, and minus the overwrites."""
    out: dict[str, tuple[str, ...]] = {"M_full": OPS}
    for op in OPS:
        out[f"M_full-no-{op}"] = tuple(o for o in OPS if o != op)
    out["M_full-no-overwrites"] = tuple(o for o in OPS if o not in OVERWRITES)
    return out


################################################################################
# Derive
################################################################################

def _files(rows: list[dict[str, str]], ops: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """The neutralize and monotone lines for one threat model."""
    drop, mono = [], []
    for row in rows:
        signs = {op: row[f"op_{op}_pre"] for op in OPS}
        d = direction(signs, ops)
        key = f"{row['group']}:{row['name']}"
        if d == "both":
            drop.append(key)
        elif d in ("up", "down"):
            mono.append(f"{key}\t{1 if d == 'up' else -1}")
    return drop, mono


def derive(directions: Path, reference: Path, outdir: Path) -> list[str]:
    """
    Write the training inputs of every variant that differs from the full catalogue.

    Args:
        directions: a `directions_sums.csv` with `op_<op>_pre` and `M_full_pre` columns.
        reference: the directory holding the `M_full-pre.{neutralize.txt,monotone.tsv}` training used.
        outdir: where the variants' files go.

    Returns:
        The variants written, the full catalogue first.
    """
    rows = pl.read_csv(directions, infer_schema_length=0).fill_null("").to_dicts()
    for row in rows:
        signs = {op: row[f"op_{op}_pre"] for op in OPS}
        if direction(signs, OPS) != row["M_full_pre"]:
            raise RuntimeError(f"{row['group']}:{row['name']}: composed {direction(signs, OPS)}, "
                               f"table {row['M_full_pre']}")
    full_drop, full_mono = _files(rows, OPS)
    ref_drop = (reference / "M_full-pre.neutralize.txt").read_text().splitlines()
    ref_mono = (reference / "M_full-pre.monotone.tsv").read_text().splitlines()
    if full_drop != ref_drop or full_mono != ref_mono:
        raise RuntimeError(f"The composed full catalogue differs from {reference}'s training inputs")
    outdir.mkdir(parents=True, exist_ok=True)
    written, summary = [], {}
    for name, ops in variants().items():
        drop, mono = _files(rows, ops)
        if name != "M_full" and drop == full_drop and mono == full_mono:
            print(f"{name}: same training inputs as M_full, skipped")
            continue
        (outdir / f"{name}.neutralize.txt").write_text("".join(n + "\n" for n in drop))
        (outdir / f"{name}.monotone.tsv").write_text("".join(m + "\n" for m in mono))
        regained = sorted(set(full_drop) - set(drop))
        groups: dict[str, int] = {}
        for key in regained:
            groups[key.split(":")[0]] = groups.get(key.split(":")[0], 0) + 1
        summary[name] = {"neutralized": len(drop), "monotone": len(mono), "regained": len(regained),
                         "regained_by_group": groups}
        print(f"{name}: {len(drop)} neutralized, {len(mono)} monotone, {len(regained)} regained {groups}")
        written.append(name)
    (outdir / "variants.json").write_text(json.dumps(summary, indent=2) + "\n")
    (outdir / "variants.txt").write_text("".join(n + "\n" for n in written))
    return written


################################################################################
# Table
################################################################################

def _metrics(model: Path) -> dict[str, Any]:
    """AUC and TPR at 1% and 0.1% FPR on the test split."""
    m = json.loads((model / "metrics.json").read_text())
    p = pl.read_parquet(model / "ts_predictions.parquet")
    fpr, tpr, _ = roc_curve(p["label"].to_numpy(), p["prob"].to_numpy())
    return {"auc": m["ts_metrics"]["roc"], "tpr_1": float(np.interp(0.01, fpr, tpr)),
            "tpr_01": float(np.interp(0.001, fpr, tpr))}


def table(models: list[tuple[str, Path]], out: Path) -> None:
    """Print and save the metrics of each (label, model directory), with the TPR difference from the first."""
    rows = []
    for label, path in models:
        if not (path / "metrics.json").exists():
            print(f"{label}: missing ({path})")
            continue
        rows.append({"variant": label, **_metrics(path)})
    base = rows[0]["tpr_1"] if rows else 0.0
    print(f"{'variant':28s} {'AUC':>7s} {'TPR@1%':>7s} {'vs first':>8s} {'TPR@0.1%':>8s}")
    for r in rows:
        r["delta_tpr_1"] = r["tpr_1"] - base
        print(f"{r['variant']:28s} {r['auc']:7.4f} {100 * r['tpr_1']:6.1f}% {100 * r['delta_tpr_1']:+7.1f} "
              f"{100 * r['tpr_01']:7.1f}%")
    out.write_text(json.dumps(rows, indent=2) + "\n")


################################################################################
# Main
################################################################################

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("derive")
    p.add_argument("--directions", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    p = sub.add_parser("table")
    p.add_argument("--model", action="append", required=True, help="label=path, the first is the baseline")
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "derive":
        derive(args.directions, args.reference, args.outdir)
    else:
        models = []
        for item in args.model:
            if "=" not in item:
                raise ValueError(f"--model expects label=path, got {item!r}")
            label, path = item.split("=", 1)
            models.append((label, Path(path)))
        table(models, args.out)


if __name__ == "__main__":
    main()
