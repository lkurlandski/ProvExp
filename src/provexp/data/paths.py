"""
Where the datasets live, overridable per machine through environment variables.
"""

from __future__ import annotations
import os
from pathlib import Path

__all__ = ["EMBER2024_DATA", "EMBER2024_TABULAR", "ROOT", "file_store"]

# The repository root (this file is src/provexp/data/paths.py; the package is installed editable).
ROOT = Path(__file__).resolve().parents[3]

# The EMBER-2024 binaries: one SimpleDB per split ({tr,vl,ts}), truncated to 4,000,000 bytes.
EMBER2024_DATA = Path(os.environ.get("EMBER2024_DATA", "/shared/datasets/EMBER-2024/data"))
# The EMBER-2024 release's tabular files (metadata; pipeline/2-features/files/build_metadata.py).
EMBER2024_TABULAR = Path(os.environ.get("EMBER2024_TABULAR", "/shared/datasets/EMBER-2024-tabular"))


def file_store() -> Path:
    """
    The file store the scale-up's attacks and defenses read their files from (`provexp.data.filestore`).

    Its location is the environment variable FILE_STORE, which pipeline/common.sh sets to
    $OUT_ROOT/2-features/files/files.sqlite (built by pipeline/2-features/file-store). There is no fallback: reading
    the files one by one from the SimpleDB decompresses a whole shard per file (~1.4 s), which silently cost
    `iterated` ~20 min per round (session 82), so a missing setting or store is an error.

    Returns:
        The store's path.
    """
    value = os.environ.get("FILE_STORE")
    if not value:
        raise RuntimeError("FILE_STORE is not set: it names the file store (pipeline/common.sh sets it to "
                           "$OUT_ROOT/2-features/files/files.sqlite; source it or export FILE_STORE).")
    path = Path(value)
    if not path.is_file():
        raise FileNotFoundError(f"No file store at FILE_STORE={path.as_posix()}; build it with "
                                "pipeline/2-features/file-store/run.sh or copy it there.")
    return path
