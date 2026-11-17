"""
A small SQLite store of the files the attacks read again and again (the evaluation set, the donor sets), for fast
random access.

The SimpleDB holds each file inside a ~500 MB compressed shard, so reading one file decompresses its whole shard (about
1.4 s, session 69); an attack task that loads 1,000 malware and 100 donors spends ~25 minutes on it, with the node's
other cores idle, and reads ~0.5 TB from the shared filesystem. The store holds the same bytes, one row per file, read
in milliseconds. It is built once (`build_store`, each shard decompressed once) and opened read-only; each row carries
the file's SHA-256, checked on every read. Where it lives is one setting, FILE_STORE (`provexp.data.paths.file_store`);
the loaders (`provexp.data.files`) read only from it, with no fallback to the SimpleDB.
"""

from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Sequence
import hashlib
from multiprocessing import get_context
import os
from pathlib import Path
import sqlite3

import polars as pl
import zstandard as zstd

from provexp.data.simpledb import SimpleDB

__all__ = ["STORE_NAME", "FileStore", "build_store"]


################################################################################
# Reading
################################################################################


# The store's file name (pipeline/common.sh's FILE_STORE is $OUT_ROOT/2-features/files/files.sqlite).
STORE_NAME = "files.sqlite"


class FileStore:
    """A read-only view of a store built by `build_store`."""

    def __init__(self, path: Path) -> None:
        if not Path(path).exists():
            raise FileNotFoundError(f"No file store at {Path(path).as_posix()}.")
        self.path = Path(path)
        # NOTE: `immutable=1` turns off SQLite's file locking, which is unreliable on network filesystems; the store is
        # never written after it is built (`build_store` writes a temporary file and renames it into place).
        uri = Path(path).resolve().as_uri() + "?mode=ro&immutable=1"
        self._db = sqlite3.connect(uri, uri=True, check_same_thread=False)

    def names(self) -> set[str]:
        """The names of the files the store holds."""
        return {r[0] for r in self._db.execute("SELECT name FROM files")}

    def get(self, name: str) -> bytes:
        """The bytes of one file; raise KeyError if the store does not hold it, RuntimeError if they are corrupt."""
        row = self._db.execute("SELECT sha256, data FROM files WHERE name = ?", (name,)).fetchone()
        if row is None:
            raise KeyError(f"The store {self.path.as_posix()} does not hold {name}.")
        sha, data = row
        if hashlib.sha256(data).hexdigest() != sha:
            raise RuntimeError(f"The bytes of {name} in {self.path.as_posix()} do not match their SHA-256.")
        return bytes(data)

    def close(self) -> None:
        """Close the connection."""
        self._db.close()


################################################################################
# Building
################################################################################


def _read_shard(task: tuple[str, int, list[str]]) -> list[tuple[str, bytes]]:
    """The files `names` of one shard, read as `SimpleDBReader.get` reads them (one decompression per shard)."""
    root, shard, names = task
    db = SimpleDB(Path(root), check=False)
    blob = db.files_data[shard].read_bytes()
    if blob.startswith(b"\x28\xb5\x2f\xfd"):
        blob = zstd.decompress(blob)
    size = pl.read_csv(db.files_size[shard]).filter(pl.col("name").is_in(names))
    return [(n, blob[o:o + s]) for n, o, s in size.select("name", "offset", "size").iter_rows()]


def _locate(db_dir: Path, names: Iterable[str]) -> dict[int, list[str]]:
    """The shard of each name, as {shard: names}; raise if a name is not in the SimpleDB."""
    wanted = set(names)
    db = SimpleDB(db_dir, check=False)
    by_shard: dict[int, list[str]] = {}
    for i, path in enumerate(db.files_size):
        shard = pl.read_csv(path, columns=["name"])["name"]
        found = shard.filter(shard.is_in(list(wanted)))
        if len(found):
            by_shard[i] = found.to_list()
    missing = wanted - {n for v in by_shard.values() for n in v}
    if missing:
        raise KeyError(f"{len(missing)} names are not in {db_dir.as_posix()}, e.g. {sorted(missing)[:3]}.")
    return by_shard


def build_store(path: Path, lists: Sequence[tuple[Sequence[str], Path]], workers: int) -> int:
    """
    Write a store holding the files of `lists`, read from their SimpleDBs with each shard decompressed once.

    Args:
        path: The store to write (replaced atomically if it exists).
        lists: (names, SimpleDB directory) pairs; a name listed twice is stored once.
        workers: Processes reading shards (each holds one decompressed shard, up to ~1 GB, in memory).

    Returns:
        The number of files stored.
    """
    if workers < 1:
        raise ValueError(f"workers must be positive, got {workers}.")
    tasks = []
    for names, db_dir in lists:
        tasks += [(str(db_dir), shard, found) for shard, found in sorted(_locate(Path(db_dir), names).items())]
    tmp = Path(f"{path}.tmp-{os.getpid()}")
    tmp.unlink(missing_ok=True)
    db = sqlite3.connect(tmp)
    db.execute("CREATE TABLE files (name TEXT PRIMARY KEY, sha256 TEXT NOT NULL, data BLOB NOT NULL)")
    n = 0
    with get_context("spawn").Pool(workers) as pool:
        for rows in pool.imap_unordered(_read_shard, tasks):
            for name, data in rows:
                sha = hashlib.sha256(data).hexdigest()
                # The SimpleDB names a file by its SHA-256; only a truncated file (4,000,000 bytes) differs.
                if sha != name and len(data) != 4_000_000:
                    raise RuntimeError(f"The bytes read for {name} have SHA-256 {sha}.")
                n += db.execute("INSERT OR IGNORE INTO files VALUES (?, ?, ?)", (name, sha, data)).rowcount
    db.commit()
    db.close()
    tmp.replace(path)
    return n
