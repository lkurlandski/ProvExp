"""
Where the datasets live, overridable per machine through environment variables.
"""

from __future__ import annotations
import os
from pathlib import Path

__all__ = ["EMBER2024_DATA", "EMBER2024_TABULAR"]

# The EMBER-2024 binaries: one SimpleDB per split ({tr,vl,ts}), truncated to 4,000,000 bytes.
EMBER2024_DATA = Path(os.environ.get("EMBER2024_DATA", "/shared/datasets/EMBER-2024/data"))
# The EMBER-2024 release's tabular files (metadata; scripts/build_metadata.py).
EMBER2024_TABULAR = Path(os.environ.get("EMBER2024_TABULAR", "/shared/datasets/EMBER-2024-tabular"))
