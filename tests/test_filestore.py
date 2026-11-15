"""
Tests for provexp.data.filestore and the loaders' use of it (provexp.data.files).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3

import polars as pl
import pytest

from provexp.data.filestore import STORE_NAME
from provexp.data.filestore import FileStore
from provexp.data.filestore import store_beside
from provexp.data.files import FileReader

__all__: list[str] = []


################################################################################
# Helpers
################################################################################


def _write(path: Path, rows: list[tuple[str, str, bytes]]) -> None:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE files (name TEXT PRIMARY KEY, sha256 TEXT NOT NULL, data BLOB NOT NULL)")
    db.executemany("INSERT INTO files VALUES (?, ?, ?)", rows)
    db.commit()
    db.close()


def _row(data: bytes) -> tuple[str, str, bytes]:
    sha = hashlib.sha256(data).hexdigest()
    return sha, sha, data


################################################################################
# FileStore
################################################################################


class TestFileStore:

    def test_reads_what_it_holds(self, tmp_path: Path) -> None:
        files = [b"MZ" + bytes([i]) * 100 for i in range(3)]
        _write(tmp_path / STORE_NAME, [_row(d) for d in files])
        store = FileStore(tmp_path / STORE_NAME)
        assert store.names() == {_row(d)[0] for d in files}
        for d in files:
            assert store.get(_row(d)[0]) == d
        with pytest.raises(KeyError):
            store.get("missing")

    def test_corrupt_bytes_raise(self, tmp_path: Path) -> None:
        name, sha, _ = _row(b"original")
        _write(tmp_path / STORE_NAME, [(name, sha, b"changed")])
        with pytest.raises(RuntimeError):
            FileStore(tmp_path / STORE_NAME).get(name)

    def test_store_beside(self, tmp_path: Path) -> None:
        assert store_beside(tmp_path / "ts.parquet") is None
        _write(tmp_path / STORE_NAME, [])
        assert store_beside(tmp_path / "ts.parquet") == tmp_path / STORE_NAME


class TestFileReader:

    def test_prefers_the_store(self, tmp_path: Path) -> None:
        data = b"MZ held in the store"
        name = _row(data)[0]
        _write(tmp_path / STORE_NAME, [_row(data)])
        pl.DataFrame({"name": [name], "label": [1]}).write_parquet(tmp_path / "ts.parquet")
        # The SimpleDB directory does not exist: a read that fell back to it would fail.
        reader = FileReader(tmp_path / "ts.parquet", tmp_path / "no-simpledb")
        assert reader.get(name) == data
