"""
Tests for reach.py (the C1 and C4 engines) and ItemTable.replace.
"""

from collections.abc import Sequence

import numpy as np
import pytest

from provexp.items import Identity
from provexp.items import Item
from provexp.items import ItemTable
from provexp.items import Max
from provexp.items import Min
from provexp.items import Normalized
from provexp.items import Opaque
from provexp.items import Ratio
from provexp.items import Term
from provexp.items import feature_hash
from provexp.reach import BOTH
from provexp.reach import DOWN
from provexp.reach import FIXED
from provexp.reach import UP
from provexp.reach import ByteEdit
from provexp.reach import Change
from provexp.reach import NotLocal
from provexp.reach import Vocabulary
from provexp.reach import directions
from provexp.reach import envelope
from provexp.reach import extension_monotone
from provexp.reach import hash_image
from provexp.reach import meets
from provexp.reach import predict
from provexp.reach import predict_declared
from provexp.reach import profile_kinds
from provexp.reach import readout_signs
from provexp.reach import region_changes


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


################################################################################
# C4
################################################################################


def _c4_table() -> ItemTable:
    """Two runs, a header slot, a hashed name, and a sized blob with a value attribute, for the vocabulary."""
    z = b"h.aa.aaa"
    items = _table(z).items
    for item in items:
        item.attrs["value"] = 2.0
    blob = Item("blob", terms=(
        Term("hashed", "names", index=1, value=1.0, sign=1, key="x", ranges=((1, 2),)),
        Term("add", "size", value=3, attr="size", ranges=((0, 3),), per_byte=True),
    ), attrs={"size": 3, "level": 0.5}, group="toy")
    return ItemTable(len(z), {"n": 1, "len": 1, "h": 1, "names": 4, "size": 1}, items + [blob])


@pytest.fixture(scope="module")
def vocab() -> tuple[dict[tuple[str, str], object], dict[str, int]]:
    return profile_kinds([_c4_table()])  # type: ignore[return-value]


class TestVocabulary:

    def test_profile(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        profiles, sizes = vocab
        assert set(profiles) == {("toy", "header"), ("toy", "run"), ("toy", "blob")}
        assert sizes["names"] == 4
        run = profiles[("toy", "run")]
        assert run.items == 2 and run.terms[("n", 0)].items == 2
        assert profiles[("toy", "blob")].growing == {"size"}

    def test_merge_equals_add(self) -> None:
        a, b = Vocabulary(), Vocabulary()
        a.add(_c4_table())
        b.merge(a)
        b.merge(a)
        c = Vocabulary()
        c.add(_c4_table())
        c.add(_c4_table())
        assert b.finish()[0][("toy", "run")].items == c.finish()[0][("toy", "run")].items == 4

    def test_split_index_checked(self) -> None:
        (b,), (sign,) = feature_hash(4, ["x"])
        right = 4 * (sign < 0) + int(b)
        ok = ItemTable(2, {"p": 8}, [Item("x", terms=(Term("split", "p", index=right, key="x"),), group="g")])
        profile_kinds([ok])
        wrong = ItemTable(2, {"p": 8}, [Item("x", terms=(Term("split", "p", index=(right + 4) % 8, key="x"),), group="g")])
        with pytest.raises(RuntimeError):
            profile_kinds([wrong])

    def test_conflicting_ops(self) -> None:
        t = ItemTable(2, {"n": 1}, [Item("x", terms=(Term("count", "n"),), group="g"), Item("x", terms=(Term("slot", "n", value=1),), group="g")])
        with pytest.raises(RuntimeError):
            profile_kinds([t])


class TestEnvelope:

    def test_add_remove(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        env = envelope([Change("add", "run")], *vocab)
        assert env.entry("n", 0) == UP and env.entry("len", 0) == UP and env.entry("h", 0) == FIXED
        env = envelope([Change("remove", "run")], *vocab)
        assert env.entry("n", 0) == DOWN

    def test_modify_keeps_unconditional_counts(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        env = envelope([Change("modify", "run")], *vocab)
        assert env.entry("n", 0) == FIXED and env.entry("len", 0) == BOTH

    def test_rewrite_keeps_element_counts(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        env = envelope([Change("rewrite", "blob")], *vocab)
        assert env.entry("size", 0) == FIXED and env.entry("names", 1) == BOTH
        assert env.kinds["blob"].attr("size") == FIXED and env.kinds["blob"].attr("level") == BOTH

    def test_grow(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        env = envelope([Change("grow", "blob")], *vocab)
        assert env.entry("size", 0) == UP and env.entry("names", 1) == FIXED
        assert env.kinds["blob"].attr("size") == UP and env.kinds["blob"].attr("level") == BOTH

    def test_hashed_add(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        # One key reaches one bucket with one sign; any key reaches every bucket with both.
        env = envelope([Change("add", "blob", keys=("x",))], *vocab)
        assert sum(1 for i in range(4) if env.entry("names", i)) == 1
        env = envelope([Change("add", "blob")], *vocab)
        assert all(env.entry("names", i) == BOTH for i in range(4))

    def test_split_add(self) -> None:
        # A key reaches the part of its bucket its hash sign picks, always up; any key reaches every part.
        (b,), (sign,) = feature_hash(4, ["x"])
        table = ItemTable(2, {"p": 8}, [Item("x", terms=(Term("split", "p", index=4 * (sign < 0) + int(b), value=2.0, key="x"),), group="g")])
        vocab = profile_kinds([table])
        env = envelope([Change("add", "x", keys=("x",))], *vocab)
        assert env.family("p") == [UP if i == 4 * (sign < 0) + b else FIXED for i in range(8)]
        assert envelope([Change("add", "x")], *vocab).family("p") == [UP] * 8
        assert envelope([Change("remove", "x")], *vocab).family("p") == [DOWN] * 8

    def test_unknown_kind(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        with pytest.raises(KeyError):
            envelope([Change("add", "nothing")], *vocab)

    def test_region_changes(self) -> None:
        table = _c4_table()
        # The header's locating range: flagged; a run's member: modified in the entries read there.
        kinds = {c.kind: c.how for c in region_changes(table, [(1, 2)], {})}
        assert kinds == {"header": "flag", "blob": "modify"}
        (c,) = region_changes(table, [(3, 4)], {})
        assert c.kind == "run" and dict(c.entries or ()) == {("n", 0): BOTH, ("len", 0): BOTH}
        assert region_changes(table, [], {"run": "flag"}) == []
        # An in-place write keeps the number of elements: the blob's size (a per-element count) is not modified.
        assert {c.kind for c in region_changes(table, [(0, 1)], {})} == {"header"}


class TestReadoutSigns:

    @pytest.mark.parametrize(
        "changes,readout,expected",
        [
            ([Change("add", "run")], Ratio(("len", 0), ("n", 0)), [BOTH]),
            ([Change("grow", "blob")], Ratio(("len", 0), ("size", 0)), [DOWN]),
            ([Change("add", "run")], Max(("run",), "value"), [UP]),
            ([Change("remove", "run")], Max(("run",), "value"), [DOWN]),
            ([Change("add", "run")], Min(("run",), "value"), [FIXED]),
            ([Change("add", "blob", keys=("x",))], Normalized("names", 4), None),
            ([Change("remove", "blob")], Opaque("blob", ("level",), (0.0,), ranges=((0.0, 1.0),)), [DOWN]),
            ([Change("add", "blob")], Opaque("blob", ("level",), (0.5,), ranges=((0.0, 1.0),)), [BOTH]),
        ],
    )
    def test_rules(self, vocab: tuple[dict, dict], changes: list[Change], readout: object, expected: list[frozenset[str]] | None) -> None:  # type: ignore[type-arg]
        signs = readout_signs(readout, envelope(changes, *vocab))  # type: ignore[arg-type]
        if expected is None:
            # One bucket moves with the key's hash sign: its share moves with it, the others' the other way.
            ((bucket, s),) = hash_image(4, ["x"]).items()
            expected = [s if i == bucket else (DOWN if s == UP else UP) for i in range(4)]
        assert signs == expected

    def test_directions(self, vocab: tuple[dict, dict]) -> None:  # type: ignore[type-arg]
        out = directions(READOUTS, {"op": [Change("add", "run")], "none": []}, *vocab)
        assert out == {"op": [UP, UP, FIXED], "none": [FIXED, FIXED, FIXED]}


class TestHelpers:

    @pytest.mark.parametrize(
        "pattern,expected",
        [("abc", True), ("abc\\b", False), ("^abc", True), ("abc$", False), ("a(?=b)", False), ("\\bC:/", True), ("\\b", False), (b"http://", True)],
    )
    def test_extension_monotone(self, pattern: str | bytes, expected: bool) -> None:
        assert extension_monotone(pattern) == expected

    @pytest.mark.parametrize("size", [10, 50, 256])
    def test_hash_image_covers(self, size: int) -> None:
        image = hash_image(size)
        assert len(image) == size and all(s == BOTH for s in image.values())
