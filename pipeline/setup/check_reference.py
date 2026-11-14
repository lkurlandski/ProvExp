"""
Re-extract a few test files with each extractor and compare the vectors bit for bit with the reference in
pipeline/setup/reference/ (this server's vectors, from run/146's featurization). A difference on a new system means
its environment computes different features (library versions, architecture): fix it before featurizing there.

The reference holds only feature vectors and file names (the binaries are read from EMBER2024_DATA, never committed).

Usage:
    python pipeline/setup/check_reference.py                      # check
    python pipeline/setup/check_reference.py --write --stores artifacts/refactor-baseline/old/features
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import polars as pl

from provexp.data.paths import EMBER2024_DATA
from provexp.data.paths import ROOT
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.data.tabular import FEATURES_FILE
from provexp.data.tabular import META_FILE
from provexp.featuresets.ember2024.expert import ExpertFeatureExtractor
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

__all__: list[str] = []

# As in pipeline/2-features/featurize/featurize.py.
EXTRACTORS: dict[str, type[PEFeatureExtractor]] = {
    "ember2024": PEFeatureExtractor,
    "sums": SumsFeatureExtractor,
    "expert": ExpertFeatureExtractor,
}
REFERENCE = ROOT / "pipeline" / "setup" / "reference"


def write(stores: Path, split: str, num_files: int) -> None:
    """The reference from feature stores built by featurize.py: `num_files` rows spread over the store."""
    meta = pl.read_parquet(stores / "ember2024" / split / META_FILE)
    ok = meta.filter(pl.col("status") == "ok")
    rows = ok["row"].to_numpy()[np.linspace(0, ok.height - 1, num_files).round().astype(int)]
    names = meta["name"].to_numpy()[rows].tolist()
    REFERENCE.mkdir(parents=True, exist_ok=True)
    for x in EXTRACTORS:
        m = pl.read_parquet(stores / x / split / META_FILE)
        if m["name"].to_list() != meta["name"].to_list():
            raise RuntimeError(f"The stores of ember2024 and {x} hold different files.")
        X = np.load(stores / x / split / FEATURES_FILE, mmap_mode="r")
        np.save(REFERENCE / f"{x}.npy", np.asarray(X[rows]))
    (REFERENCE / "files.json").write_text(json.dumps({"split": split, "names": names}, indent=2) + "\n")
    print(f"Wrote the reference for {len(names)} files to {REFERENCE.as_posix()}.")


def check(db: Path) -> bool:
    """Whether every extractor reproduces the reference bit for bit."""
    spec = json.loads((REFERENCE / "files.json").read_text())
    reader = SimpleDBReader(SimpleDB(db / spec["split"], check=False))
    data = [bytes(reader.get(n).data) for n in spec["names"]]
    good = True
    for x, cls in EXTRACTORS.items():
        extractor = cls()
        ref = np.load(REFERENCE / f"{x}.npy")
        X = np.stack([extractor.feature_vector(z) for z in data]).astype(np.float32)  # type: ignore[no-untyped-call]
        same = [X[i].tobytes() == ref[i].tobytes() for i in range(len(data))]
        print(f"{x:<10} {sum(same)}/{len(same)} files bit-identical")
        for i in np.where(~np.array(same))[0]:
            diff = np.where(X[i].view(np.uint32) != ref[i].view(np.uint32))[0]
            names = [extractor.feature_names[j] for j in diff[:5]]
            print(f"    {spec['names'][i]}: {len(diff)} features differ, e.g. {names}")
        good &= all(same)
    return good


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA, help="Contains one SimpleDB per split.")
    parser.add_argument("--write", action="store_true", help="Write the reference instead of checking.")
    parser.add_argument("--stores", type=Path, default=None, help="--write: the directory of the three stores.")
    parser.add_argument("--split", default="ts")
    parser.add_argument("--num_files", type=int, default=32)
    args = parser.parse_args()
    warnings.filterwarnings("ignore")
    if args.write:
        if args.stores is None:
            raise ValueError("--write needs --stores.")
        write(args.stores, args.split, args.num_files)
        return
    if not check(args.db):
        print("FAILED: this environment computes different features.")
        sys.exit(1)
    print("Featurization matches the reference.")


if __name__ == "__main__":
    main()
