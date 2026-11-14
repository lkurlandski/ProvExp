"""
Loading the attacked files: the detected malware and the goodware of a file list, as bytes.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader

__all__ = ["load_pilot"]


def load_pilot(pilot_files: Path, db_dir: Path) -> tuple[list[tuple[str, bytes]], list[tuple[str, bytes]]]:
    """The detected pilot malware and the pilot goodware, as (name, bytes) lists.

    Args:
        pilot_files: PB1's files.parquet (name, label, log_odds:gbdt).
        db_dir: The SimpleDB directory holding the bytes.

    Returns:
        (malware, goodware); malware is restricted to samples the GBDT already detects (log-odds > 0).
    """
    df = pl.read_parquet(pilot_files).select("name", "label", "log_odds:gbdt")
    reader = SimpleDBReader(SimpleDB(db_dir, check=False))
    malware = [(r["name"], bytes(reader.get(r["name"]).data))
               for r in df.filter((pl.col("label") == 1) & (pl.col("log_odds:gbdt") > 0)).iter_rows(named=True)]
    goodware = [(r["name"], bytes(reader.get(r["name"]).data))
                for r in df.filter(pl.col("label") == 0).iter_rows(named=True)]
    return malware, goodware
