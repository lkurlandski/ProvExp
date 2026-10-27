"""
Tests for reach.py (the C1 engine) and ItemTable.replace.
"""

from collections.abc import Sequence

import numpy as np
import pytest

from provexp.items import Identity
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Term
from provexp.reach import ByteEdit
from provexp.reach import NotLocal
from provexp.reach import meets
from provexp.reach import predict
from provexp.reach import predict_declared


################################################################################
# A toy extractor: runs of letters, each counted once, plus a located header item
################################################################################


def _runs(z: bytes, lo: int, hi: int) -> list[Item]:
    """Maximal runs of the letter 'a' in [lo, hi), each an item counted once."""
    out, i = [], lo
    while i < hi:
        if z[i] == ord("a"):
            j = i
            while j < hi and z[j] == ord("a"):
                j += 1
            out.append(Item("run", terms=(Term("count", "n", ranges=((i, j),)), Term("add", "len", value=j - i, ranges=((i, j),))), group="toy"))
            i = j
        else:
            i += 1
    return out


def _table(z: bytes) -> ItemTable:
    header = Item("header", terms=(Term("slot", "h", value=z[0], ranges=((0, 1),)),), locating=((0, 2),), group="toy")
    return ItemTable(len(z), {"n": 1, "len": 1, "h": 1}, [header] + _runs(z, 2, len(z)))


class Toy:
    def recognize(self, items: Sequence[Item], old: bytes, new: bytes, edit: ByteEdit) -> tuple[list[Item], list[Item]]:
        lo, hi = edit.lo, edit.lo + len(edit.content)
        while lo > 2 and new[lo - 1] == ord("a"):
            lo -= 1
        while hi < len(new) and new[hi] == ord("a"):
            hi += 1
        removed = [i for i in items if i.kind == "run" and meets(i.members, (lo, hi))]
        return removed, _runs(new, lo, hi)


READOUTS = [Identity("n"), Identity("len"), Identity("h")]


################################################################################
# Tests
################################################################################


class TestByteEdit:

    def test_kinds(self) -> None:
        z = b"abcdef"
        assert ByteEdit(6, 6, b"x").is_append(z) and ByteEdit(6, 6, b"x").touched(z) == (6, 7)
        assert ByteEdit(1, 3, b"xy").is_in_place() and ByteEdit(1, 3, b"xy").apply(z) == b"axydef"
        with pytest.raises(ValueError):
            ByteEdit(4, 8, b"").apply(z)

    @pytest.mark.parametrize("ranges,span,expected", [([(0, 2)], (2, 3), False), ([(0, 3)], (2, 3), True), ([], (0, 9), False)])
    def test_meets(self, ranges: list[tuple[int, int]], span: tuple[int, int], expected: bool) -> None:
        assert meets(ranges, span) is expected


class TestPredict:

    @pytest.mark.parametrize(
        "edit",
        [
            ByteEdit(5, 6, b"a"),       # joins two runs
            ByteEdit(3, 4, b"x"),       # splits a run
            ByteEdit(10, 10, b"aaxa"),  # append that extends the last run
            ByteEdit(2, 10, b"x" * 8),  # wipes every run
        ],
    )
    def test_matches_extraction(self, edit: ByteEdit) -> None:
        z = b"H\x00aaaxaaxa"
        p = predict(_table(z), z, edit, {"toy": Toy()})
        assert p.table is not None
        expected = _table(p.new)
        for f in ("n", "len", "h"):
            np.testing.assert_array_equal(p.table.sums[f], expected.sums[f])

    def test_flags_locating(self) -> None:
        z = b"H\x00aaa"
        p = predict(_table(z), z, ByteEdit(1, 2, b"\x01"), {"toy": Toy()})
        assert p.table is None and [i.kind for i in p.flagged] == ["header"]
        with pytest.raises(RuntimeError):
            p.features(READOUTS)

    def test_not_local(self) -> None:
        class Refuses:
            def recognize(self, items: Sequence[Item], old: bytes, new: bytes, edit: ByteEdit) -> tuple[list[Item], list[Item]]:
                raise NotLocal(list(items)[:1], "no")
        z = b"H\x00aaa"
        p = predict(_table(z), z, ByteEdit(3, 4, b"x"), {"toy": Refuses()})
        assert p.table is None and p.reason == "toy: no"

    def test_missing_recognizer(self) -> None:
        z = b"H\x00aaa"
        with pytest.raises(KeyError):
            predict(_table(z), z, ByteEdit(3, 4, b"x"), {})


class TestReplace:

    def test_incremental_equals_recomputed(self) -> None:
        key = np.arange(8, dtype=np.int64) % 3
        a = Item("a", terms=(Term("bins", "b", ranges=((0, 4),), bin_key=key), Term("hashed", "h", value=0.1, key="k")), group="g")
        b = Item("a", terms=(Term("bins", "b", ranges=((4, 8),), bin_key=key), Term("hashed", "h", value=0.2, key="k")), group="g")
        c = Item("a", terms=(Term("bins", "b", ranges=((2, 6),), bin_key=key), Term("hashed", "h", value=0.3, key="k")), group="g")
        t = ItemTable(8, {"b": 3, "h": 1}, [a, b])
        u = t.replace([a], [c])
        assert u.items == [c, b]  # the modified item keeps its place
        fresh = ItemTable(8, {"b": 3, "h": 1}, [c, b])
        for f in ("b", "h"):
            np.testing.assert_array_equal(u.sums[f], fresh.sums[f])

    def test_declared(self) -> None:
        z = b"H\x00aaa"
        t = _table(z)
        new_run = Item("run", terms=(Term("count", "n", ranges=((5, 6),)), Term("add", "len", value=1.0, ranges=((5, 6),))), group="toy")
        p = predict_declared(t, z + b"a", [], [new_run])
        assert p.table is not None and p.table.sums["n"][0] == 2 and p.table.num_elements == 6

    def test_rejects_foreign_items(self) -> None:
        t = _table(b"H\x00aaa")
        with pytest.raises(ValueError):
            t.replace([Item("x")], [])
