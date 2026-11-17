"""
Tests for provexp.data.filestore, its location (provexp.data.paths.file_store), and the loaders' use of it
(provexp.data.files): the scale-up reads only the store and stops when it or a file is missing.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3

import polars as pl
import pytest

from provexp.data.filestore import STORE_NAME
from provexp.data.filestore import FileStore
from provexp.data.files import FileReader
from provexp.data.files import load_donors
from provexp.data.files import load_evaluation
from provexp.data.files import read_files
from provexp.data.paths import file_store

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



class TestFileStoreLocation:

    def test_unset_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("FILE_STORE", raising=False)
        with pytest.raises(RuntimeError, match="FILE_STORE is not set"):
            file_store()

    def test_missing_store_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FILE_STORE", str(tmp_path / STORE_NAME))
        with pytest.raises(FileNotFoundError, match="No file store"):
            file_store()
        with pytest.raises(FileNotFoundError):
            FileReader()

    def test_set_and_present(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write(tmp_path / STORE_NAME, [])
        monkeypatch.setenv("FILE_STORE", str(tmp_path / STORE_NAME))
        assert file_store() == tmp_path / STORE_NAME


class TestFileReader:

    @pytest.fixture()
    def held(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, bytes]]:
        """Three files in a store FILE_STORE names, in a directory with no file list and no SimpleDB."""
        files = [b"MZ" + bytes([i]) * 50 for i in range(3)]
        _write(tmp_path / STORE_NAME, [_row(d) for d in files])
        monkeypatch.setenv("FILE_STORE", str(tmp_path / STORE_NAME))
        return [(_row(d)[0], d) for d in files]

    def test_reads_the_named_store(self, held: list[tuple[str, bytes]]) -> None:
        reader = FileReader()
        for name, data in held:
            assert reader.get(name) == data

    def test_missing_file_raises(self, held: list[tuple[str, bytes]]) -> None:
        with pytest.raises(KeyError):
            FileReader().get("missing")

    def test_read_files_checks_all_first(self, held: list[tuple[str, bytes]]) -> None:
        names = [n for n, _ in held]
        assert read_files(names) == held
        with pytest.raises(KeyError, match="does not hold 2 of the 4"):
            read_files(names[:2] + ["x", "y"])

    def test_loaders_read_the_store(self, held: list[tuple[str, bytes]], tmp_path: Path) -> None:
        names = [n for n, _ in held]
        files = tmp_path / "lists" / "round-1.parquet"  # a list anywhere: the store's location is not inferred from it
        files.parent.mkdir()
        pl.DataFrame({"name": names, "label": [1, 1, 0]}).write_parquet(files)
        donors = tmp_path / "lists" / "donors.parquet"
        pl.DataFrame({"name": names[2:], "label": [0]}).write_parquet(donors)
        malware, goodware = load_evaluation(files, donors)
        assert malware == held[:2] and goodware == held[2:]
        assert load_donors(donors) == held[2:]

    def test_loader_missing_file_raises(self, held: list[tuple[str, bytes]], tmp_path: Path) -> None:
        files = tmp_path / "ts.parquet"
        pl.DataFrame({"name": [held[0][0], "absent"], "label": [1, 1]}).write_parquet(files)
        with pytest.raises(KeyError, match="does not hold 1"):
            load_evaluation(files)
