"""
Tests for items.py.
"""

import math

import numpy as np
import pytest
from sklearn.feature_extraction import FeatureHasher

from provexp.boxmatrix import BoxMatrix
from provexp.items import BitTest
from provexp.items import DistinctCount
from provexp.items import Entropy
from provexp.items import Identity
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Lookup
from provexp.items import Max
from provexp.items import Min
from provexp.items import Normalized
from provexp.items import Opaque
from provexp.items import Outside
from provexp.items import Positive
from provexp.items import Ratio
from provexp.items import Term
from provexp.items import evaluate
from provexp.items import feature_hash
from provexp.items import merge_ranges
from provexp.items import project


def dense(C: BoxMatrix) -> np.ndarray:
    return C.to_dense()


################################################################################
# Helpers
################################################################################


class TestMergeRanges:

    @pytest.mark.parametrize(
        "ranges,expected",
        [
            ([], ()),
            ([(3, 3)], ()),
            ([(5, 7), (0, 2)], ((0, 2), (5, 7))),
            ([(0, 4), (2, 6), (6, 8)], ((0, 8),)),
        ],
    )
    def test_merge(self, ranges: list[tuple[int, int]], expected: tuple[tuple[int, int], ...]) -> None:
        assert merge_ranges(ranges) == expected


class TestFeatureHash:

    def test_matches_feature_hasher(self) -> None:
        keys = ["", ".text", ".rsrc", "kernel32.dll", "a" * 40]
        bucket, sign = feature_hash(50, keys)
        X = FeatureHasher(50, input_type="string").transform([[k] for k in keys]).toarray()
        for i in range(len(keys)):
            expected = np.zeros(50)
            expected[bucket[i]] = sign[i]
            np.testing.assert_array_equal(X[i], expected)

    def test_empty(self) -> None:
        bucket, sign = feature_hash(8, [])
        assert bucket.shape == sign.shape == (0,)


################################################################################
# Terms and items
################################################################################


class TestTerm:

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"op": "nope", "family": "f"},
            {"op": "count", "family": "f", "value": 2.0},
            {"op": "add", "family": "f", "value": -1.0},
            {"op": "hashed", "family": "f", "value": 1.0},
            {"op": "add", "family": "f", "sign": -1},
            {"op": "bins", "family": "f"},
            {"op": "count", "family": "f", "bin_key": np.zeros(3, dtype=np.int64)},
            {"op": "count", "family": "f", "index": -1},
        ],
    )
    def test_invalid(self, kwargs: dict[str, object]) -> None:
        with pytest.raises(ValueError):
            Term(**kwargs)  # type: ignore[arg-type]

    def test_amount(self) -> None:
        assert Term("hashed", "f", value=3.0, sign=-1, key="k").amount == -3.0
        assert Term("add", "f", value=3.0).amount == 3.0

    def test_bin_counts(self) -> None:
        key = np.array([0, 1, 1, 2, 0, 1], dtype=np.int64)
        t = Term("bins", "f", ranges=((0, 2), (3, 6)), bin_key=key)
        np.testing.assert_array_equal(t.bin_counts(3), [2, 2, 1])
        with pytest.raises(IndexError):
            t.bin_counts(2)

    def test_members(self) -> None:
        item = Item(
            "x",
            terms=(Term("count", "f", ranges=((4, 6),)), Term("add", "g", value=1.0, ranges=((5, 9),))),
            attr_ranges={"a": (((0, 1),),)},
        )
        assert item.members == ((0, 1), (4, 9))


class TestItemTable:

    def test_validation(self) -> None:
        with pytest.raises(KeyError):
            ItemTable(10, {}, [Item("x", terms=(Term("count", "f"),))])
        with pytest.raises(IndexError):
            ItemTable(10, {"f": 1}, [Item("x", terms=(Term("count", "f", index=1),))])
        with pytest.raises(IndexError):
            ItemTable(10, {"f": 1}, [Item("x", terms=(Term("count", "f", ranges=((5, 11),)),))])

    def test_sums(self) -> None:
        key = np.array([0, 1, 1, 0], dtype=np.int64)
        items = [
            Item("a", terms=(Term("count", "n"), Term("add", "s", value=2.5))),
            Item("a", terms=(Term("count", "n"), Term("add", "s", value=1.0), Term("slot", "f", index=1, value=-7.0))),
            Item("b", terms=(Term("hashed", "h", index=2, value=4.0, sign=-1, key="k"),
                             Term("hashed", "h", index=2, value=1.0, key="j"))),
            Item("c", terms=(Term("bins", "v", index=1, ranges=((0, 4),), bin_key=key),)),
        ]
        table = ItemTable(4, {"n": 1, "s": 1, "f": 2, "h": 3, "v": 3}, items)
        np.testing.assert_array_equal(table.sums["n"], [2])
        np.testing.assert_array_equal(table.sums["s"], [3.5])
        np.testing.assert_array_equal(table.sums["f"], [0, -7])
        np.testing.assert_array_equal(table.sums["h"], [0, 0, -3])
        np.testing.assert_array_equal(table.sums["v"], [0, 2, 2])
        assert table.written == {("f", 1)}

    def test_slot_written_twice(self) -> None:
        items = [Item("a", terms=(Term("slot", "f", value=1.0),)), Item("a", terms=(Term("slot", "f", value=2.0),))]
        with pytest.raises(ValueError):
            ItemTable(0, {"f": 1}, items).sums

    def test_key_counts(self) -> None:
        items = [Item("l", terms=(Term("keyed", "k", index=i, key=k),)) for i, k in [(1, "a"), (0, "b"), (1, "a")]]
        table = ItemTable(0, {"k": 2}, items)
        assert table.key_counts("k") == {"a": (1, 2), "b": (0, 1)}

    def test_concatenate_and_filter(self) -> None:
        t1 = ItemTable(5, {"f": 1}, [Item("a", terms=(Term("count", "f"),))])
        t2 = ItemTable(5, {"g": 1}, [Item("b", terms=(Term("count", "g"),))])
        t = ItemTable.concatenate([t1, t2])
        assert len(t) == 2 and t.families == {"f": 1, "g": 1}
        assert [i.kind for i in t.filter(lambda i: i.kind == "b").items] == ["b"]
        with pytest.raises(ValueError):
            ItemTable.concatenate([t1, t1])
        with pytest.raises(ValueError):
            ItemTable.concatenate([t1, ItemTable(6, {}, [])])


################################################################################
# Readouts
################################################################################


def _strings_table() -> tuple[bytes, ItemTable]:
    """Two "strings" with counts, lengths, and character bins, as a string extractor would record them."""
    z = b"\x00abcab\x00\x00ccc\x00"
    key = np.frombuffer(z, dtype=np.uint8).astype(np.int64) - ord("a")
    items = []
    for lo, hi in [(1, 6), (8, 11)]:
        items.append(Item("string", terms=(
            Term("count", "num", ranges=((lo, hi),)),
            Term("add", "len", value=hi - lo, ranges=((lo, hi),), per_byte=True),
            Term("bins", "chars", ranges=((lo, hi),), bin_key=key),
        )))
    return z, ItemTable(len(z), {"num": 1, "len": 1, "chars": 3}, items)


class TestReadouts:

    def test_identity_ratio_normalized_entropy(self) -> None:
        _, table = _strings_table()
        readouts = [
            Identity("num"),
            Ratio(("len", 0), ("num", 0)),
            Normalized("chars", 3, precision="float64"),
            Normalized("chars", 3, precision="float32"),
            Entropy("chars", precision="python"),
            Entropy("chars", precision="numpy"),
        ]
        x = evaluate(table, readouts)
        c = np.array([2, 2, 4])
        H = -sum(p * math.log2(p) for p in c / 8)
        np.testing.assert_allclose(x, [2, 4, *(c / 8), *(c / 8), H, H], rtol=1e-6)

    def test_ratio_default(self) -> None:
        table = ItemTable(0, {"a": 1, "b": 1}, [])
        assert evaluate(table, [Ratio(("a", 0), ("b", 0), default=-1.0)])[0] == -1.0

    def test_normalized_empty(self) -> None:
        table = ItemTable(0, {"v": 2}, [])
        assert np.all(np.isnan(evaluate(table, [Normalized("v", 2, precision="float32")])))
        np.testing.assert_array_equal(evaluate(table, [Normalized("v", 2, precision="float64")]), [0, 0])

    def test_max_min(self) -> None:
        items = [
            Item("s", attrs={"e": 3.0}, attr_ranges={"e": (((0, 2),),)}),
            Item("s", attrs={"e": 5.0}, attr_ranges={"e": (((2, 4),),)}),
            Item("o", attrs={"e": 5.0}, attr_ranges={"e": (((4, 8),),)}),
        ]
        table = ItemTable(8, {"size": 1}, items + [Item("f", terms=(Term("add", "size", value=10.0),))])
        x = evaluate(table, [Max(("s",), "e"), Max(("s", "o"), "e", divide_by=("size", 0)), Min(("s", "o"), "e")])
        np.testing.assert_array_equal(x, np.array([5, 0.5, 0], dtype=np.float32))
        P = dense(project(table, [Max(("s", "o"), "e"), Min(("s", "o"), "e")]))
        np.testing.assert_allclose(P[:, 0], [0, 0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25])
        assert not P[:, 1].any()

    def test_distinct_count(self) -> None:
        items = [
            Item("lib", terms=(Term("keyed", "k", index=1, key="a", ranges=((0, 2),)),)),
            Item("lib", terms=(Term("keyed", "k", index=1, key="a", ranges=((4, 6),)),)),
            Item("lib", terms=(Term("keyed", "k", index=0, key="b", ranges=((2, 4),)),)),
        ]
        table = ItemTable(6, {"k": 2}, items)
        readouts = [DistinctCount("k"), DistinctCount("k", 2, per_bucket=True)]
        np.testing.assert_array_equal(evaluate(table, readouts), [2, 1, 1])
        P = dense(project(table, readouts))
        np.testing.assert_allclose(P[:, 0], [0.25, 0.25, 0.5, 0.5, 0.25, 0.25])
        np.testing.assert_allclose(P[:, 1], [0, 0, 0.5, 0.5, 0, 0])
        np.testing.assert_allclose(P[:, 2], [0.25, 0.25, 0, 0, 0.25, 0.25])

    def test_fields(self) -> None:
        items = [Item("field", terms=(Term("slot", "hdr", index=1, value=0b0110, ranges=((2, 4),)),))]
        table = ItemTable(4, {"hdr": 2}, items)
        readouts = [
            BitTest(("hdr", 1), (1, 2, 4, 8)),
            Lookup(("hdr", 1), {6: 3.0}),
            Lookup(("hdr", 0), {0: 3.0}, absent=-1.0),
            Positive(("hdr", 1), scale=128.0),
        ]
        np.testing.assert_array_equal(evaluate(table, readouts), [0, 1, 1, 0, 3, -1, 128])
        P = dense(project(table, readouts))
        for col in range(5):
            np.testing.assert_allclose(P[:, col], [0, 0, 0.5, 0.5])
        assert not P[:, 5:].any()

    def test_opaque_and_outside(self) -> None:
        readouts = [Opaque("sig", ("a", "b"), (0.0, 1.0)), Outside(3)]
        x = evaluate(ItemTable(2, {}, []), readouts)
        np.testing.assert_array_equal(x[:2], [0, 1])
        assert np.all(np.isnan(x[2:]))
        item = Item("sig", attrs={"a": 7, "b": 9}, attr_ranges={"a": (((0, 1),), ((1, 2),)), "b": ()})
        table = ItemTable(2, {}, [item])
        np.testing.assert_array_equal(evaluate(table, readouts)[:2], [7, 9])
        np.testing.assert_allclose(dense(project(table, readouts))[:, 0], [1, 1])
        with pytest.raises(ValueError):
            evaluate(ItemTable(2, {}, [item, item]), readouts)


class TestProject:

    def test_strings(self) -> None:
        z, table = _strings_table()
        readouts = [Identity("num"), Ratio(("len", 0), ("num", 0)), Normalized("chars", 3), Entropy("chars")]
        P = dense(project(table, readouts))
        assert P.shape == (len(z), 6)
        expected = np.zeros((len(z), 6))
        for lo, hi in [(1, 6), (8, 11)]:
            expected[lo:hi, 0] = 1 / (hi - lo)
            expected[lo:hi, 1] = 1
            expected[lo:hi, 5] = 1
            for i in range(lo, hi):
                expected[i, 2 + z[i] - ord("a")] = 1
        np.testing.assert_allclose(P, expected)

    def test_bins_need_whole_family(self) -> None:
        _, table = _strings_table()
        with pytest.raises(ValueError):
            project(table, [Identity("chars", 1, 2)])
