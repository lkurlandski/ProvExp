"""
Copy a small, diverse set of executables from a SimpleDB into tests/data/ for testing.

The files are real executables, including malware, so tests/data/ is gitignored and must never be committed.

Layout:
    tests/data/
    ├── goodware/<sha256>
    ├── malware/<sha256>
    └── manifest.csv
"""

from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import warnings

import pandas as pd
import pefile
from tqdm import tqdm

from provexp.data.simpledb import Sample
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator


ROOT = Path(__file__).parent.parent
# EMBER-2024 binaries are truncated to their first 4,000,000 bytes (not 4 MiB).
MAX_LENGTH = 4_000_000


def categorize(sample: Sample) -> list[str]:
    """
    Return the categories of interest that a sample belongs to.
    """
    categories = ["any"]
    size = len(sample.data)
    if size < 2 ** 14:
        categories.append("tiny")
    if size >= MAX_LENGTH:
        categories.append("truncated")

    try:
        pe = pefile.PE(data=sample.data)
    except Exception:
        categories.append("unparsable")
        return categories

    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    if len(directories) > 4 and directories[4].Size > 0:
        categories.append("signed")
    if len(directories) > 14 and directories[14].Size > 0:
        categories.append("dotnet")
    if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        categories.append("exports")
    if pe.get_overlay_data_start_offset() is not None:
        categories.append("overlay")
    if pe.RICH_HEADER is None:
        categories.append("norich")
    if not hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        categories.append("noimports")
    if pe.FILE_HEADER.NumberOfSections == 0 or pe.FILE_HEADER.NumberOfSections > 16:
        categories.append("oddsections")
    return categories


def main() -> None:
    parser = ArgumentParser(description="Copy a small, diverse set of executables into tests/data/.")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "tests" / "data")
    parser.add_argument("--per_category", type=int, default=2, help="Number of files per category per label.")
    parser.add_argument("--num_shards", type=int, default=8, help="Number of shards to scan.")
    args = parser.parse_args()

    warnings.filterwarnings("ignore")
    db = SimpleDB(args.db, check=False)
    iterator = SimpleDBIterator(db)

    counts: dict[tuple[str, str], int] = defaultdict(int)
    records = []
    shards = list(range(min(args.num_shards, db.num_shards)))
    for sample in tqdm(iterator.iter(shards), total=sum(db.num_samples(shards)), desc="Scanning"):
        label = "malware" if sample.malware else "goodware"
        categories = categorize(sample)
        wanted = [c for c in categories if counts[(label, c)] < args.per_category]
        if not wanted:
            continue
        for c in categories:
            counts[(label, c)] += 1

        path = args.outdir / label / sample.name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(sample.data)
        records.append({"name": sample.name, "label": label, "size": len(sample.data), "categories": " ".join(categories)})

    pd.DataFrame(records).to_csv(args.outdir / "manifest.csv", index=False)
    print(f"Wrote {len(records)} files to {args.outdir.as_posix()}.")
    for (label, c), n in sorted(counts.items()):
        print(f"  {label:8} {c:12} {min(n, args.per_category)}")


if __name__ == "__main__":
    main()
