"""
Select the explanation set: a fixed, diverse subset of the test split that every explainer explains.

Near-duplicates are removed first (greedy TLSH deduplication in a seeded random order, computed on the truncated bytes,
as recorded by featurize.py), so that a few prolific families cannot dominate the set and the samples are closer to
independent. The remaining samples are then sampled uniformly within strata of label x size, optionally capping the
number of samples per malware family (if the released metadata is available, see build_metadata.py).

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
    """Keep one representative of each group of TLSH near-duplicates. Samples without a TLSH hash are kept."""
    meta = meta.sample(fraction=1.0, shuffle=True, seed=seed)
    hashed = meta.filter(pl.col("tlsh") != "")
    kept = greedy_dedup(parse_tlsh(hashed["tlsh"].to_list()), threshold, progress=True)
    return pl.concat([hashed.filter(pl.Series(kept)), meta.filter(pl.col("tlsh") == "")])


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

    meta = load_meta(args.features, args.split, args.partial)
    report: dict[str, object] = {"candidates": meta.height}

    meta = deduplicate(meta, args.threshold, args.seed)
    report["after_dedup"] = meta.height

    size_bin = pl.when(pl.col("size") < SIZE_BINS[0]).then(pl.lit(SIZE_NAMES[0]))
    for upper, name in zip(SIZE_BINS[1:], SIZE_NAMES[1:], strict=True):
        size_bin = size_bin.when(pl.col("size") < upper).then(pl.lit(name))
    meta = meta.with_columns(size_bin.alias("size_bin"))
    if args.metadata.exists():
        released = pl.read_parquet(args.metadata, columns=["name", "file_type", "family", "packer", "behavior"])
        meta = meta.join(released, on="name", how="left")
        # Cap each family, keeping the (already shuffled) order.
        meta = meta.with_columns(pl.int_range(pl.len()).over("family").alias("_rank"))
        meta = meta.filter(pl.col("family").is_null() | (pl.col("_rank") < args.max_per_family)).drop("_rank")
        report["after_family_cap"] = meta.height
    else:
        print(f"WARN: {args.metadata.as_posix()} does not exist, so families are not capped.")

    # Sample uniformly within each stratum, giving the leftover quota of small strata to the others.
    strata = meta.partition_by(["label", "size_bin"], as_dict=True)
    quota = args.num_samples // len(strata)
    chosen = []
    leftover = 0
    for key in sorted(strata, key=lambda k: strata[k].height):
        take = min(strata[key].height, quota + leftover)
        leftover = quota + leftover - take
        chosen.append(strata[key].head(take))
    selected = pl.concat(chosen).sort("row")
    report["selected"] = selected.height
    report["strata"] = {f"{label}/{size}": n for label, size, n in selected.group_by(["label", "size_bin"]).len().sort(["label", "size_bin"]).iter_rows()}

    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    selected.write_parquet(args.outfile)
    args.outfile.with_suffix(".json").write_text(json.dumps(report | vars(args), indent=2, default=str))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
