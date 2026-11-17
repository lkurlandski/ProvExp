"""
Loading the attacked files: the detected malware and the goodware of a file list, as bytes.

The scale-up reads every file from the file store (`provexp.data.paths.file_store`), never from the SimpleDB: a missing
store or a file the store does not hold is an error, not a slow fallback. Only the pilot (`load_pilot`) reads the
SimpleDB, whose files the store does not hold.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import polars as pl

from provexp.data.filestore import FileStore
from provexp.data.paths import file_store
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader

__all__ = ["PROTOCOLS", "FileReader", "load_attacked", "load_donors", "load_evaluation", "load_pilot", "read_files"]


class FileReader:
    """Reads files by name from the file store; a name the store does not hold raises KeyError."""

    def __init__(self, store: Optional[Path] = None) -> None:
        """
        Args:
            store: The store; None reads the one FILE_STORE names (`provexp.data.paths.file_store`).
        """
        self.store = FileStore(file_store() if store is None else store)
        self.held = self.store.names()

    def check(self, names: list[str]) -> None:
        """Raise KeyError, naming how many and which, if the store does not hold every one of `names`."""
        missing = sorted(set(names) - self.held)
        if missing:
            raise KeyError(f"The file store {self.store.path.as_posix()} does not hold {len(missing)} of the "
                           f"{len(set(names))} files asked for, e.g. {missing[:3]}; rebuild it with "
                           "pipeline/2-features/file-store/run.sh after the lists change.")

    def get(self, name: str) -> bytes:
        """The bytes of one file."""
        return self.store.get(name)


def read_files(names: list[str], store: Optional[Path] = None) -> list[tuple[str, bytes]]:
    """
    The bytes of `names` from the file store, as (name, bytes) pairs in their order.

    Args:
        names: The files to read; all of them must be in the store (checked before any is read).
        store: The store; None reads the one FILE_STORE names.

    Returns:
        The files.
    """
    reader = FileReader(store)
    reader.check(names)
    return [(n, reader.get(n)) for n in names]


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


def load_evaluation(files: Path, donors: Optional[Path] = None) -> tuple[list[tuple[str, bytes]],
                                                                       list[tuple[str, bytes]]]:
    """The malware of a file list and the goodware of a donor list, from the file store (the scale-up).

    Unlike load_pilot, no malware is filtered here: each attack attacks only the malware its detector detects.

    Args:
        files: The file list (name, label): the evaluation list, or a list of training malware.
        donors: A donor list (name; goodware of the training split), or None for an attack that takes no donors.

    Returns:
        (malware, donors); donors is empty without a donor list.
    """
    names = pl.read_parquet(files).filter(pl.col("label") == 1)["name"].to_list()
    malware = read_files(names)
    return malware, ([] if donors is None else load_donors(donors))


def load_donors(donors: Path) -> list[tuple[str, bytes]]:
    """The goodware of a donor list (name; training goodware), from the file store, in the list's order.

    Args:
        donors: The donor list.

    Returns:
        The donors.
    """
    df = pl.read_parquet(donors)
    if "label" in df.columns and (df["label"] != 0).any():
        raise ValueError(f"The donor list {donors.as_posix()} holds files that are not goodware.")
    return read_files(df["name"].to_list())


# The two setups the attacks run under: the pilot's (the pilot list, its malware pre-filtered by the old GBDT, the
# pilot's test goodware as donors, thresholds on the test split) and the scale-up's (session 67: the evaluation list,
# every malware offered to each detector, a donor list of training goodware, thresholds on the validation split).
PROTOCOLS = {"pilot": "ts", "scaleup": "vl"}


def load_attacked(protocol: str, files: Path, db_dir: Path, donors: Optional[Path] = None,
                  need_donors: bool = True) -> tuple[list[tuple[str, bytes]], list[tuple[str, bytes]]]:
    """The malware an attack starts from and its goodware donors, under one of PROTOCOLS.

    Args:
        protocol: "pilot" (load_pilot; `donors` must be None) or "scaleup" (load_evaluation).
        files: The file list (pilot list or evaluation list).
        db_dir: The SimpleDB directory holding its bytes (the pilot only; the scale-up reads the file store).
        donors: The scale-up's donor list.
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
        return load_evaluation(files, donors)
    raise ValueError(f"protocol must be one of {tuple(PROTOCOLS)}, got {protocol!r}.")
