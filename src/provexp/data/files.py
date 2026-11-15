"""
Loading the attacked files: the detected malware and the goodware of a file list, as bytes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader

__all__ = ["PROTOCOLS", "load_attacked", "load_evaluation", "load_pilot"]


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


def load_evaluation(files: Path, db_dir: Path, donors: Optional[Path] = None,
                    donor_db_dir: Optional[Path] = None) -> tuple[list[tuple[str, bytes]], list[tuple[str, bytes]]]:
    """The malware of an evaluation list and the goodware of a donor list, as (name, bytes) lists (the scale-up).

    Unlike load_pilot, no malware is filtered here: each attack attacks only the malware its detector detects.

    Args:
        files: The evaluation list (pipeline/2-features/files: name, label).
        db_dir: The SimpleDB directory holding its bytes (the test split).
        donors: A donor list (name; goodware of the training split), or None for an attack that takes no donors.
        donor_db_dir: The SimpleDB directory holding the donors' bytes (required with `donors`).

    Returns:
        (malware, donors); donors is empty without a donor list.
    """
    names = pl.read_parquet(files).filter(pl.col("label") == 1)["name"].to_list()
    reader = SimpleDBReader(SimpleDB(db_dir, check=False))
    malware = [(n, bytes(reader.get(n).data)) for n in names]
    if donors is None:
        return malware, []
    if donor_db_dir is None:
        raise ValueError("A donor list needs the SimpleDB directory of its split (donor_db_dir).")
    donor_df = pl.read_parquet(donors)
    if "label" in donor_df.columns and (donor_df["label"] != 0).any():
        raise ValueError(f"The donor list {donors.as_posix()} holds files that are not goodware.")
    donor_reader = SimpleDBReader(SimpleDB(donor_db_dir, check=False))
    goodware = [(n, bytes(donor_reader.get(n).data)) for n in donor_df["name"].to_list()]
    return malware, goodware


# The two setups the attacks run under: the pilot's (the pilot list, its malware pre-filtered by the old GBDT, the
# pilot's test goodware as donors, thresholds on the test split) and the scale-up's (session 67: the evaluation list,
# every malware offered to each detector, a donor list of training goodware, thresholds on the validation split).
PROTOCOLS = {"pilot": "ts", "scaleup": "vl"}


def load_attacked(protocol: str, files: Path, db_dir: Path, donors: Optional[Path] = None,
                  donor_db_dir: Optional[Path] = None, need_donors: bool = True) -> tuple[list[tuple[str, bytes]],
                                                                                         list[tuple[str, bytes]]]:
    """The malware an attack starts from and its goodware donors, under one of PROTOCOLS.

    Args:
        protocol: "pilot" (load_pilot; `donors` must be None) or "scaleup" (load_evaluation).
        files: The file list (pilot list or evaluation list).
        db_dir: The SimpleDB directory holding its bytes.
        donors: The scale-up's donor list.
        donor_db_dir: The SimpleDB directory holding the donors.
        need_donors: Whether the attack draws on donors (the scale-up then requires a donor list).

    Returns:
        (malware, goodware donors).
    """
    if protocol == "pilot":
        if donors is not None:
            raise ValueError("The pilot protocol takes its donors from the pilot list; drop --donors.")
        return load_pilot(files, db_dir)
    if protocol == "scaleup":
        if need_donors and donors is None:
            raise ValueError("The scale-up protocol needs a donor list (--donors).")
        return load_evaluation(files, db_dir, donors, donor_db_dir)
    raise ValueError(f"protocol must be one of {tuple(PROTOCOLS)}, got {protocol!r}.")
