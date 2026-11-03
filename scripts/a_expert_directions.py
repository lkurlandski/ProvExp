"""
The C4 derivation for the instrumented expert set (item 11; docs/direction-A-expert-set.md): the directions each
threat-model operation can move each of Gimenez et al.'s forty features, and the M_full holes (features the monotone
model constrains up that an edit can lower).

The expert extractor is instrumented (provexp.featuresets.ember2024.expert: items() + readouts), so the generic C4
engine (provexp.reach.directions) reads it like the EMBER extractor. The operations are the twelve of the full threat
model; their item changes over the expert kinds are:

    app/ext/shf   append and the two gap insertions change no expert feature (no section or import is added or removed,
                  and the features are offset-independent);
    sec/imp       add a section (any name) and add imports: the added items contribute up (counts, sums), no down;
    ren           rename a section: in place over the name field, which decides a section's family, so a named
                  section's info and size move to another family -- two-sided (the holes);
    dos           rewrite the DOS stub: the dos_stub item is rewritten, so modified_dos_stub is two-sided (its hole);
    rsg           remove the signature: adds the no_sig marker, so no_sig rises (up, not a hole);
    slk/hdr/chk/rdb   change no expert feature (slack is outside the mapped content the entropy reads; the header
                  fields, checksum, and debug directory are not expert features).

The in-place operations' byte regions and their item changes reuse catalogue.regions and reach.region_changes; the
structural ones are stated directly. Go/no-go (docs/direction-A-expert-set.md): the M_full holes are exactly rows 27 and
30-39 -- modified_dos_stub and the ten section-name features -- eleven of forty.
"""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import replace
from pathlib import Path

import pefile

import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from a1_evaluate import make_extractor  # noqa: E402
from provexp.featuresets.ember2024 import catalogue  # noqa: E402
from provexp.items import ItemTable  # noqa: E402
from provexp.reach import Change  # noqa: E402
from provexp.reach import FIXED  # noqa: E402
from provexp.reach import Signs  # noqa: E402
from provexp.reach import direction  # noqa: E402
from provexp.reach import directions  # noqa: E402
from provexp.reach import profile_kinds  # noqa: E402
from provexp.reach import region_changes  # noqa: E402


__all__ = ["STRUCTURAL", "REGION_OPS", "derive"]


# The structural operations as expert-kind changes (see the module docstring).
STRUCTURAL: dict[str, list[Change]] = {
    "app": [],
    "ext": [],
    "shf": [],
    "sec": [Change("add", "section")],
    "imp": [Change("add", "section"), Change("add", "import_desc")],
}
# The in-place operations whose regions and item changes come from the EMBER catalogue machinery (the byte regions are
# format-level; the expert item changes follow from them). rsg additionally adds the no_sig marker.
REGION_OPS = ("slk", "dos", "hdr", "chk", "ren", "rdb", "rsg")

# The reasoned M_full holes (docs/direction-A-expert-set.md, rows 27 and 30-39).
EXPECTED_HOLES = (
    "expert:modified_dos_stub", "expert:unknown_sections", "expert:info_unknown_sections",
    "expert:.text_info", "expert:.text-size", "expert:.data_info", "expert:.data-size",
    "expert:.rsrc_info", "expert:.rsrc-size", "expert:.rdata_info", "expert:.rdata-size",
)


def derive(files: list[bytes]) -> tuple[dict[str, list[Signs]], list[str], list[Signs]]:
    """
    The per-operation directions over the corpus, the feature names, and the M_full union per feature.

    Args:
        files: The corpus bytes (the item tables give the kinds' vocabulary and the in-place regions).

    Returns:
        (directions per operation, feature names, the M_full union of signs per feature).
    """
    extractor = make_extractor(ROOT / "artifacts/features/ember2024-expert-10")
    names = extractor.feature_names
    readouts = extractor.readouts

    tables, pes, datas = [], [], []
    for data in files:
        try:
            pe = pefile.PE(data=data)
        except pefile.PEFormatError:
            continue
        tables.append(extractor.item_table(data))
        pes.append(pe)
        datas.append(data)
    profiles, sizes = profile_kinds(tables)

    region_sets: dict[str, set[Change]] = {op: set() for op in REGION_OPS}
    for data, pe, table in zip(datas, pes, tables, strict=True):
        regions = catalogue.regions(pe, data, table)
        for op in REGION_OPS:
            region = regions.get(op, ())
            if not region:
                continue
            zero, declared, keep, _extra = catalogue.REGION_OPS[op]
            t = table if not keep else ItemTable(table.num_elements, table.families,
                                                 [replace(it, locating=()) for it in table.items])
            region_sets[op].update(region_changes(t, region, {}, zero=zero, declared=declared))

    changes: dict[str, list[Change]] = dict(STRUCTURAL)
    for op in REGION_OPS:
        changes[op] = list(region_sets[op])
    # Removing the signature adds the no_sig marker (sound and tight: no_sig rises, not a hole).
    if any(k == "no_sig" for _, k in profiles):
        changes["rsg"].append(Change("add", "no_sig"))

    dirs = directions(readouts, changes, profiles, sizes)
    union: list[Signs] = []
    for i in range(len(names)):
        s = FIXED
        for op in changes:
            s = s | dirs[op][i]
        union.append(s)
    return dirs, names, union


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "tests" / "data", help="Directory of PE files (the corpus).")
    args = parser.parse_args()
    files = [f.read_bytes() for f in sorted(args.data.glob("*/*")) if f.is_file()]
    print(f"{len(files)} files", flush=True)

    dirs, names, union = derive(files)
    holes = [names[i] for i in range(len(names)) if "-" in union[i]]
    print(f"\nM_full holes ({len(holes)} of {len(names)}):", flush=True)
    for name in holes:
        lowering = sorted(op for op in dirs if "-" in dirs[op][names.index(name)])
        print(f"  {name:32s} {direction(union[names.index(name)]):5s} lowered by {lowering}", flush=True)

    ok = tuple(holes) == EXPECTED_HOLES
    print(f"\nGo/no-go: holes {'==' if ok else '!='} the reasoned 11 (rows 27, 30-39): {'PASS' if ok else 'FAIL'}", flush=True)
    if not ok:
        print(f"  expected: {EXPECTED_HOLES}\n  got:      {tuple(holes)}", flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
