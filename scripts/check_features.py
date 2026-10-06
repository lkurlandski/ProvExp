"""
Compare our EMBER-2024 features (computed on binaries truncated to 4,000,000 bytes) with the released ones (computed
on the full binaries, read from SSViT's tabular shards).

For files that were not truncated, the features should be identical; any difference points to drift in the
environment (e.g., pefile, signify, or scikit-learn versions). For truncated files, the report shows which features
change because of the truncation.

Known, benign differences on untruncated files:
  - strings:entropy differs by a few float32 ulps (~1e-6) in about a third of files, from a newer numpy.
  - In about 0.1% of files, a pefile warning maps to a different but overlapping pattern, because thrember matches
    warnings by iterating over a set of strings, whose order depends on the interpreter's hash seed. Run
    featurize.py with PYTHONHASHSEED=0 to make this deterministic across runs.

Usage:
    python scripts/check_features.py --split ts
    python scripts/check_features.py --split ts --partial    # while featurize.py is still running
"""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

from provexp.data.tabular import FEATURES_FILE
from provexp.data.tabular import META_FILE
from provexp.featuresets.ember2024.features import PEFeatureExtractor


ROOT = Path(__file__).parent.parent


def load_ours(features: Path, split: str, partial: bool) -> tuple[np.ndarray, pl.DataFrame]:
    directory = features / split
    X = np.load(directory / FEATURES_FILE, mmap_mode="r")
    if (directory / META_FILE).exists():
        meta = pl.read_parquet(directory / META_FILE)
    elif partial:
        meta = pl.concat([pl.read_parquet(p) for p in sorted((directory / "parts").glob("meta-*.parquet"))])
    else:
        raise FileNotFoundError(f"{directory / META_FILE} does not exist. Use --partial to check the finished shards.")
    return X, meta.filter(pl.col("status") == "ok")


def load_released(tabular: Path, split: str, names: set[str]) -> dict[str, np.ndarray]:
    released = {}
    for shard in tqdm(sorted((tabular / split).glob("shard_*.npz")), desc="Loading released features"):
        data = np.load(shard, allow_pickle=True)
        shard_names = data["names"]
        keep = np.flatnonzero(np.isin(shard_names, list(names)))
        if keep.size:
            F = data["features"]
            released.update({str(shard_names[i]): F[i] for i in keep})
    return released


def main() -> None:
    parser = ArgumentParser(description="Compare our EMBER-2024 features with the released ones.")
    parser.add_argument("--split", type=str, default="ts")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--tabular", type=Path, default=Path("/home/lk3591/Documents/code/SSViT/tabular/ember2024"))
    parser.add_argument("--outfile", type=Path, default=None)
    parser.add_argument("--partial", action="store_true", help="Check the finished shards of an unfinished run.")
    parser.add_argument("--limit", type=int, default=None, help="Check at most this many samples.")
    args = parser.parse_args()

    X, meta = load_ours(args.features, args.split, args.partial)
    if args.limit is not None:
        meta = meta.head(args.limit)
    released = load_released(args.tabular, args.split, set(meta["name"].to_list()))
    names = PEFeatureExtractor().feature_names

    counts: Counter[str] = Counter()
    mismatched_untruncated: Counter[str] = Counter()
    max_abs_diff: dict[str, float] = {}
    changed_truncated: Counter[str] = Counter()
    examples: list[str] = []
    for row, name, truncated in meta.select("row", "name", "truncated").iter_rows():
        if name not in released:
            counts["missing_released"] += 1
            continue
        ours, theirs = X[row], released[name]
        diff = ~((ours == theirs) | (np.isnan(ours) & np.isnan(theirs)))
        if truncated:
            counts["truncated"] += 1
            counts["truncated_changed"] += int(diff.any())
            changed_truncated.update(names[j] for j in np.flatnonzero(diff))
        else:
            counts["untruncated"] += 1
            counts["untruncated_mismatched"] += int(diff.any())
            for j in np.flatnonzero(diff):
                mismatched_untruncated[names[j]] += 1
                max_abs_diff[names[j]] = max(max_abs_diff.get(names[j], 0.0), abs(float(ours[j]) - float(theirs[j])))
            if diff.any() and len(examples) < 10:
                examples.append(name)

    def by_group(counter: Counter[str]) -> dict[str, int]:
        groups: Counter[str] = Counter()
        for feature, n in counter.items():
            groups[feature.split(":")[0]] += n
        return dict(groups.most_common())

    report = {
        "split": args.split,
        "partial": args.partial,
        "counts": dict(counts),
        "untruncated_mismatched_features": {f: {"count": n, "max_abs_diff": max_abs_diff[f]} for f, n in mismatched_untruncated.most_common(30)},
        "untruncated_mismatched_examples": examples,
        "truncated_changed_features": dict(changed_truncated.most_common(30)),
        "truncated_changed_by_group": by_group(changed_truncated),
    }
    print(json.dumps(report, indent=2))
    outfile = args.outfile or ROOT / "artifacts" / "reports" / f"check_features_{args.split}.json"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
