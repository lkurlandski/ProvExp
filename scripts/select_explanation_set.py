"""
Select the explanation set: a fixed, diverse subset of the test split that every explainer explains.

Near-duplicates are removed first, within each label (greedy TLSH deduplication in a seeded random order, computed on
the truncated bytes, as recorded by featurize.py), and the number of samples per malware family is capped (if the
released metadata is available, see build_metadata.py), so that a few prolific families cannot dominate the set and the
samples are closer to independent. Then an equal number of samples is drawn uniformly at random from each label.

The set is deliberately not stratified by size and not selected for dissimilarity, so that statistics computed on it
are representative of the test split within each label. The report compares its size distribution with the
population's; subgroups that turn out too small should be oversampled explicitly and reweighted.

Usage:
    python scripts/select_explanation_set.py --num_samples 2000
"""

from argparse import ArgumentParser
import json
from pathlib import Path

import numpy as np
import polars as pl

from provexp.data.tabular import META_FILE
from provexp.data.tlsh import greedy_dedup
from provexp.data.tlsh import parse_tlsh


ROOT = Path(__file__).parent.parent
# Upper bounds of the size bins, in bytes. The last bin holds the files truncated to 4,000,000 bytes.
SIZE_BINS = [2 ** 16, 2 ** 19, 4_000_000, 4_000_001]
SIZE_NAMES = ["<64KiB", "64KiB-512KiB", "512KiB-4MB", "truncated"]


def load_meta(features: Path, split: str, partial: bool) -> pl.DataFrame:
    directory = features / split
    if (directory / META_FILE).exists():
        meta = pl.read_parquet(directory / META_FILE)
    elif partial:
        meta = pl.concat([pl.read_parquet(p) for p in sorted((directory / "parts").glob("meta-*.parquet"))])
    else:
        raise FileNotFoundError(f"{directory / META_FILE} does not exist. Use --partial to select from the finished shards.")
    return meta.filter(pl.col("status") == "ok")


def deduplicate(meta: pl.DataFrame, threshold: int, seed: int) -> pl.DataFrame:
    """
    Keep one representative of each group of TLSH near-duplicates within each label, in a seeded random order (which
    is kept). Samples without a TLSH hash are kept.
    """
    meta = meta.sample(fraction=1.0, shuffle=True, seed=seed)
    parts = []
    for label in sorted(meta["label"].unique().to_list()):
        group = meta.filter(pl.col("label") == label)
        hashed = group.filter(pl.col("tlsh") != "")
        kept = greedy_dedup(parse_tlsh(hashed["tlsh"].to_list()), threshold, progress=True)
        parts.extend([hashed.filter(pl.Series(kept)), group.filter(pl.col("tlsh") == "")])
    return pl.concat(parts).sample(fraction=1.0, shuffle=True, seed=seed)


def size_bins(meta: pl.DataFrame) -> pl.DataFrame:
    expr = pl.when(pl.col("size") < SIZE_BINS[0]).then(pl.lit(SIZE_NAMES[0]))
    for upper, name in zip(SIZE_BINS[1:], SIZE_NAMES[1:], strict=True):
        expr = expr.when(pl.col("size") < upper).then(pl.lit(name))
    return meta.with_columns(expr.alias("size_bin"))


def composition(meta: pl.DataFrame) -> dict[str, dict[str, float]]:
    """The fraction of each label's samples in each size bin."""
    counts = meta.group_by(["label", "size_bin"]).len()
    totals = dict(meta.group_by("label").len().iter_rows())
    out: dict[str, dict[str, float]] = {}
    for label, size, n in counts.sort(["label", "size_bin"]).iter_rows():
        out.setdefault(str(label), {})[size] = round(n / totals[label], 4)
    return out


def main() -> None:
    parser = ArgumentParser(description="Select a fixed, diverse subset of the test split to explain.")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--metadata", type=Path, default=ROOT / "artifacts" / "metadata" / "ember2024.parquet")
    parser.add_argument("--split", type=str, default="ts")
    parser.add_argument("--num_samples", type=int, default=2000)
    parser.add_argument("--threshold", type=int, default=30, help="TLSH distance below which samples are near-duplicates.")
    parser.add_argument("--max_per_family", type=int, default=10, help="Requires the released metadata.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--outfile", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--partial", action="store_true", help="Select from the finished shards of an unfinished run.")
    args = parser.parse_args()

    meta = size_bins(load_meta(args.features, args.split, args.partial))
    report: dict[str, object] = {"candidates": meta.height, "population": composition(meta)}

    meta = deduplicate(meta, args.threshold, args.seed)
    report["after_dedup"] = dict(meta.group_by("label").len().sort("label").iter_rows())

    if args.metadata.exists():
        released = pl.read_parquet(args.metadata, columns=["name", "file_type", "family", "packer", "behavior"])
        meta = meta.join(released, on="name", how="left", maintain_order="left")
        # Cap each family, keeping the (already shuffled) order.
        meta = meta.with_columns(pl.int_range(pl.len()).over("family").alias("_rank"))
        meta = meta.filter(pl.col("family").is_null() | (pl.col("_rank") < args.max_per_family)).drop("_rank")
        report["after_family_cap"] = dict(meta.group_by("label").len().sort("label").iter_rows())
    else:
        print(f"WARN: {args.metadata.as_posix()} does not exist, so families are not capped.")

    # Sample uniformly at random within each label (the order is already a seeded shuffle).
    groups = meta.partition_by("label", as_dict=True)
    quota = args.num_samples // len(groups)
    for key, group in groups.items():
        if group.height < quota:
            raise RuntimeError(f"Label {key[0]} has only {group.height} candidates; {quota} were requested.")
    selected = pl.concat([group.head(quota) for group in groups.values()]).sort("row")
    report["selected"] = selected.height
    report["selection"] = composition(selected)

    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    selected.write_parquet(args.outfile)
    args.outfile.with_suffix(".json").write_text(json.dumps(report | vars(args), indent=2, default=str))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
