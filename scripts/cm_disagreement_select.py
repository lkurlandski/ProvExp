"""
3-A, disagreement triage (PLAN.md, 3-A): select test files on which the GBDT and MalConv disagree at their operating
thresholds.

Each model's threshold gives it a 1% false-positive rate. The four cells of disagreement are malware detected only by
the GBDT or only by MalConv, and benign files flagged only by the GBDT or only by MalConv; an equal number of files is
drawn at random from each. The output has the explanation set's columns, so that scripts/explain.py can explain it
(`--explanation_set`).

Outputs:
    {out}               one row per selected file: row, name, label, shard, position, size, cell, both log-odds
    {out}.json          the thresholds and the size of every cell in the test split

Usage:
    python scripts/cm_disagreement_select.py --seed 0 --per_cell 25
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
import polars as pl
import torch

from provexp.data.tabular import META_FILE
from provexp.data.utils import decode_sha256_tensor


__all__ = [
    "load_malconv_predictions",
]


ROOT = Path(__file__).parent.parent
CELLS = {
    "malware_gbdt_only": (1, True, False),
    "malware_malconv_only": (1, False, True),
    "benign_gbdt_only": (0, True, False),
    "benign_malconv_only": (0, False, True),
}


def load_malconv_predictions(directory: Path) -> pl.DataFrame:
    """MalConv's saved test predictions: name, label, and log-odds."""
    def load(f: str) -> torch.Tensor:
        return torch.load(directory / f, map_location="cpu")  # type: ignore[no-any-return]
    logits = load("logits.pt").double()
    return pl.DataFrame({"name": decode_sha256_tensor(load("names.pt")), "malconv_label": load("labels.pt").numpy(),
                         "malconv_log_odds": (logits[:, 1] - logits[:, 0]).numpy()})


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT and of MalConv.")
    parser.add_argument("--per_cell", type=int, default=25)
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--sample_seed", type=int, default=0)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--predictions", type=Path, default=ROOT / "artifacts" / "checkpoints-predictions")
    parser.add_argument("--out", type=Path, default=None, help="Default: artifacts/explanation_set/ts-disagreement-seed{seed}.parquet")
    args = parser.parse_args()
    out = args.out or ROOT / "artifacts" / "explanation_set" / f"ts-disagreement-seed{args.seed}.parquet"

    gbdt = pl.read_parquet(args.models / "gbdt" / f"seed-{args.seed}" / "ts_predictions.parquet")
    p = gbdt["prob"].to_numpy().clip(1e-15, 1 - 1e-15)
    gbdt = gbdt.with_columns(pl.Series("gbdt_log_odds", np.log(p / (1 - p))))
    malconv = load_malconv_predictions(args.predictions / f"malconv-seed{args.seed}")
    meta = pl.read_parquet(args.features / "ts" / META_FILE).select("row", "name", "label", "shard", "position", "size", "status")
    df = meta.join(gbdt.select("name", "gbdt_log_odds"), on="name").join(malconv, on="name")
    if df.height != meta.height or (df["label"] != df["malconv_label"]).any():
        raise RuntimeError(f"The predictions do not match the test split ({df.height} of {meta.height} files joined, or labels differ).")
    df = df.filter(pl.col("status") == "ok").drop("malconv_label", "status")

    # NOTE: neither model has saved validation predictions, so the thresholds come from the test split's benign files.
    # This is acceptable for selecting disagreements (it does not evaluate either model), not for reporting accuracy.
    benign = df.filter(pl.col("label") == 0)
    thresholds = {k: float(np.quantile(benign[f"{k}_log_odds"].to_numpy(), 1 - args.fpr)) for k in ("gbdt", "malconv")}
    df = df.with_columns((pl.col("gbdt_log_odds") > thresholds["gbdt"]).alias("gbdt_flags"),
                         (pl.col("malconv_log_odds") > thresholds["malconv"]).alias("malconv_flags"))
    counts: dict[str, int] = {}
    parts = []
    for cell, (label, g, m) in CELLS.items():
        members = df.filter((pl.col("label") == label) & (pl.col("gbdt_flags") == g) & (pl.col("malconv_flags") == m))
        counts[cell] = members.height
        if members.height < args.per_cell:
            raise RuntimeError(f"Cell {cell} has only {members.height} files.")
        parts.append(members.sample(args.per_cell, seed=args.sample_seed).with_columns(pl.lit(cell).alias("cell")))
    selected = pl.concat(parts).drop("gbdt_flags", "malconv_flags").sort("row")
    out.parent.mkdir(parents=True, exist_ok=True)
    selected.write_parquet(out)
    report = {"seed": args.seed, "fpr": args.fpr, "thresholds": thresholds, "cells": counts, "test_files": df.height,
              "per_cell": args.per_cell, "sample_seed": args.sample_seed}
    out.with_suffix(".json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"Wrote {selected.height} files to {out.as_posix()}.")


if __name__ == "__main__":
    main()
