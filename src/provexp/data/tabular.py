"""
Feature matrices stored as one memory-mappable array per split, with an aligned metadata table.

Layout:
    root/
    ├── manifest.json        how the features were produced (extractor, versions, commit, row counts)
    └── {split}/
        ├── X.npy            float32 (N, d), memory-mappable; rows of samples that failed to extract are NaN
        ├── meta.parquet     one row per sample, in the same order as the rows of X
        └── parts/           per-shard metadata written during extraction (deleted once merged)

The metadata has at least the columns `row` (int), `name` (str, the SHA-256), `label` (int), `timestamp` (int), and
`status` (str, "ok" if the features were extracted successfully).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any
import json

import numpy as np
from numpy import typing as npt
import polars as pl


__all__ = [
    "FEATURES_FILE",
    "META_FILE",
    "MANIFEST_FILE",
    "load_features",
    "load_manifest",
]


FEATURES_FILE = "X.npy"
META_FILE = "meta.parquet"
MANIFEST_FILE = "manifest.json"


def load_features(root: Path | str, split: str, mmap: bool = True, only_ok: bool = False) -> tuple[npt.NDArray[np.float32], pl.DataFrame]:
    """
    Load the feature matrix and metadata of a split.

    Args:
        root: The root directory of the feature store.
        split: The name of the split, e.g., "tr".
        mmap: Whether to memory-map the feature matrix instead of reading it into memory.
        only_ok: Whether to drop the samples whose features failed to extract. This reads the selected rows into memory.

    Returns:
        The feature matrix, shape (N, d), and its metadata, with N rows in the same order.
    """
    directory = Path(root) / split
    X: npt.NDArray[np.float32] = np.load(directory / FEATURES_FILE, mmap_mode="r" if mmap else None)
    meta = pl.read_parquet(directory / META_FILE).sort("row")
    if meta.height != X.shape[0] or not np.array_equal(meta["row"].to_numpy(), np.arange(X.shape[0])):
        raise RuntimeError(f"The metadata in {directory.as_posix()} is not aligned with its feature matrix.")
    if only_ok:
        mask = (meta["status"] == "ok").to_numpy()
        X = np.asarray(X[mask])
        meta = meta.filter(pl.Series(mask))
    return X, meta


def load_manifest(root: Path | str) -> dict[str, Any]:
    """
    Load the manifest describing how a feature store was produced.
    """
    manifest: dict[str, Any] = json.loads((Path(root) / MANIFEST_FILE).read_text())
    return manifest
