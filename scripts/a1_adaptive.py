"""
Direction A, Table A1's adaptive column (docs/direction-A-A1-design.md): a soundness test for our monotone detectors.

FOR ACADEMIC SECURITY RESEARCH ONLY. This is a defense-evaluation harness. A sound monotone detector (the C4 rows)
carries a guarantee: no loader-safe edit in the threat model M (docs/direction-A-threat-model.md, Section 1) can lower
its score. This script checks that guarantee on our own pilot samples against our own detectors, by trying the edits M
allows and recording whether any lowers the score. For a C4 row the expected result is "no edit helps" (0 by
construction, Gimenez Prop. 1 + C4 + A1-A4); a decrease below -1e-6 is an A1-A4 bug to debug against Table A0, not an
evasion. For the PV-seen row, which is sound only against the attacks it was built from, the same search realizes the
hole check 2 measured. Nothing is deployed; files are written only so their features can be re-extracted and re-scored.

The search decides by C1 predictions of each candidate edit's *declared* effect (the attacker's reachable set under M;
decided 2026-10-24), never by re-extracting a written file: the declared effect leaves out the layout bytes (padding,
the section-table entry, SizeOfImage; A4), so a real re-extraction would mix M effects with the layout's. The C4 rows
are therefore 0 by construction here; the C1-vs-reextraction gap (A4) is reported alongside (`p_adv_real`). Each
chosen step is materialized by our own byte-level edit (scripts/catalogue_checks.py), exactly the declared operation,
so the next step starts from the file the declaration describes. This part provides the material (goodware donors),
the loader-safe edits, and the greedy search over C1.

Every edit keeps the original content in place -- each section's raw data, the overlay, the DOS header and stub, and
the header fields it does not itself set -- so it stays inside M and does not exploit the writing tool's layout
choices; `lief_preserves` checks this for the LIEF edits.

Outputs, in `{outdir}/`:
    adaptive.parquet   one row per (defense, file): the C1-declared result (evaded, queries, best op sequence,
                       min_delta_logit = the most negative score change any candidate's declared effect produced)
    adaptive.json      per defense: detected, evaded (C1-declared), rate by truncation, min_delta_logit, and any
                       C4-row soundness violation (min_delta_logit < -1e-6: an A1-A4 bug, debug via Table A0)

Usage (smoke):
    PYTHONHASHSEED=0 python scripts/a1_adaptive.py --outdir /tmp/a1a --num_malware 2 --queries 30 \
        --threat_model M_full --defense pv-seen=artifacts/models/gbdt/seed-0-pv \
        --features artifacts/features/ember2024
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
import struct
import sys
import time
from typing import Any
from typing import Callable
from typing import Optional
from typing import Sequence

import lightgbm
import numpy as np
import pefile
from sklearn.utils import murmurhash3_32

from provexp.data.tabular import load_manifest
from provexp.featuresets.ember2024 import catalogue
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.items import ItemTable
from provexp.reach import ByteEdit
from provexp.reach import Prediction
from provexp.reach import predict

sys.path.insert(0, str(Path(__file__).parent))
from a_c1_table0 import has_overrun_section  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from catalogue_checks import add_section as write_section  # noqa: E402

__all__ = ["Donors", "Engine", "HDR_FIELDS", "Operation", "add_imports", "add_section", "engine_predictors",
           "full_menu", "greedy_search", "lief_preserves", "bucket_names", "menu", "rename_section", "section_bucket",
           "set_header_fields", "zero_directory_entry"]

ROOT = Path(__file__).resolve().parent.parent

# The threat models' operation sets (scripts/a_directions.py): additions, gap insertions, in-place overwrites.
ADD, INSERT, OVERWRITE = ("app", "sec", "imp"), ("ext", "shf"), ("slk", "dos", "hdr", "chk", "ren", "rdb", "rsg")
THREAT = {"M_add": ADD, "M_shift": ADD + INSERT, "M_full": ADD + INSERT + OVERWRITE}

# The loader-ignored header fields (the threat model's `hdr`, matching scripts/a_directions.py's `header` group).
HDR_FIELDS = (("FILE_HEADER", "TimeDateStamp"), ("FILE_HEADER", "NumberOfSymbols"),
              ("FILE_HEADER", "PointerToSymbolTable"), ("OPTIONAL_HEADER", "MajorImageVersion"),
              ("OPTIONAL_HEADER", "MinorImageVersion"), ("OPTIONAL_HEADER", "MajorLinkerVersion"),
              ("OPTIONAL_HEADER", "MinorLinkerVersion"), ("OPTIONAL_HEADER", "MajorOperatingSystemVersion"),
              ("OPTIONAL_HEADER", "MinorOperatingSystemVersion"))
DEBUG_ENTRY, SECURITY_ENTRY = 6, 4


################################################################################
# Donors: goodware material the edits draw on (as the GAMMA attacks do)
################################################################################

class Donors:
    """Section names and contents, DOS stubs, header-field values, checksums, and imports taken from the goodware."""

    def __init__(self, goodware: list[tuple[str, bytes]]) -> None:
        self.sections: list[tuple[str, bytes, int]] = []
        self.stubs: list[bytes] = []
        self.fields: list[dict[str, int]] = []
        self.checksums: list[int] = []
        self.imports: list[tuple[str, list[str]]] = []
        for _, data in goodware:
            try:
                pe = pefile.PE(data=data)
            except Exception:
                continue
            for s in pe.sections:
                body = s.get_data()[:65536]
                if body:
                    self.sections.append((s.Name.rstrip(b"\x00").decode(errors="ignore"), body, int(s.Characteristics)))
            self.stubs.append(data[2:pe.DOS_HEADER.e_lfanew])
            self.fields.append({f"{h}.{f}": int(getattr(getattr(pe, h), f)) for h, f in HDR_FIELDS})
            self.checksums.append(int(pe.OPTIONAL_HEADER.CheckSum))
            for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
                names = [i.name.decode() for i in entry.imports if i.name]
                if names:
                    self.imports.append((entry.dll.decode(), names[:20]))
        if not (self.sections and self.stubs and self.imports):
            raise RuntimeError("The donor pool has no sections, stubs, or imports.")


################################################################################
# In-place byte edits (loader-ignored fields; no parse change, no length change)
################################################################################

def _overwrite(data: bytes, lo: int, content: bytes) -> bytes:
    """`data` with `content` written at offset `lo`, keeping the length (content must fit)."""
    if lo + len(content) > len(data):
        raise ValueError("The content does not fit at this offset.")
    return data[:lo] + content + data[lo + len(content):]


def _pack_field(structure: Any, field: str, value: int) -> tuple[int, bytes]:
    """The file offset of a pefile structure field and `value` packed to its width (little-endian)."""
    lo, hi = field_range(structure, field)
    fmt = {1: "<B", 2: "<H", 4: "<I", 8: "<Q"}[hi - lo]
    return lo, struct.pack(fmt, value & ((1 << (8 * (hi - lo))) - 1))


def set_header_fields(data: bytes, pe: pefile.PE, values: dict[str, int]) -> bytes:
    """Set the loader-ignored header fields (`HDR_FIELDS`) to `values` (keyed "STRUCT.field"); in place."""
    out = data
    for (struct_name, field), key in zip(HDR_FIELDS, (f"{h}.{f}" for h, f in HDR_FIELDS)):
        lo, packed = _pack_field(getattr(pe, struct_name), field, values[key])
        out = _overwrite(out, lo, packed)
    return out


def set_checksum(data: bytes, pe: pefile.PE, value: int) -> bytes:
    """Set OPTIONAL_HEADER.CheckSum to `value`; in place (the loader does not verify it for non-drivers)."""
    lo, packed = _pack_field(pe.OPTIONAL_HEADER, "CheckSum", value)
    return _overwrite(data, lo, packed)


def zero_directory_entry(data: bytes, pe: pefile.PE, index: int) -> bytes:
    """Zero a data-directory entry's RVA and size (e.g. DEBUG or SECURITY): removes the feature, keeps the length."""
    entry = pe.OPTIONAL_HEADER.DATA_DIRECTORY[index]
    out = _overwrite(data, entry.get_file_offset(), b"\x00" * 8)
    return out


def overwrite_dos_stub(data: bytes, pe: pefile.PE, stub: bytes) -> bytes:
    """
    Overwrite the DOS header fields [2, 60) and the stub [64, e_lfanew) with `stub`, keeping e_magic ("MZ", [0, 2))
    and e_lfanew ([60, 64)) so the PE header is still located (the threat model's `dos` operation).
    """
    lfanew = pe.DOS_HEADER.e_lfanew
    room = (60 - 2) + max(0, lfanew - 64)
    content = (stub + b"\x00" * room)[:room]
    out = _overwrite(data, 2, content[:58])
    if lfanew > 64 and len(content) > 58:
        out = _overwrite(out, 64, content[58:])
    return out


################################################################################
# Structural edits via LIEF (add a section / imports, rename a section)
################################################################################

def _characteristics(code: bool) -> int:
    """A section's characteristics: executable code, or readable/writable initialized data."""
    import lief

    c = lief.PE.Section.CHARACTERISTICS
    if code:
        return int(c.MEM_READ.value | c.MEM_EXECUTE.value | c.CNT_CODE.value)
    return int(c.MEM_READ.value | c.MEM_WRITE.value | c.CNT_INITIALIZED_DATA.value)


def add_section(data: bytes, name: str, content: bytes, code: bool) -> bytes:
    """Add a section with the given name, content, and kind (via LIEF), returning the rewritten file."""
    import lief

    pe = lief.PE.parse(list(data))
    if pe is None:
        raise RuntimeError("LIEF could not parse the file.")
    section = lief.PE.Section(name[:8])
    section.content = list(content)
    section.characteristics = _characteristics(code)
    pe.add_section(section)
    return bytes(pe.write_to_bytes())


def add_imports(data: bytes, library: str, functions: list[str]) -> bytes:
    """Add an import of `functions` from `library` (via LIEF), returning the rewritten file."""
    import lief

    pe = lief.PE.parse(list(data))
    if pe is None:
        raise RuntimeError("LIEF could not parse the file.")
    lib = pe.add_import(library)
    for function in functions:
        lib.add_entry(function)
    config = lief.PE.Builder.config_t()
    config.imports = True
    config.overlay = True
    return bytes(pe.write_to_bytes(config))


def rename_section(data: bytes, index: int, name: str) -> bytes:
    """Rename the section at `index` to `name` (<= 8 bytes), in place -- an overwrite of the name field."""
    pe = pefile.PE(data=data)
    if index >= len(pe.sections):
        raise ValueError(f"The file has only {len(pe.sections)} sections.")
    offset = pe.sections[index].get_file_offset()
    return _overwrite(data, offset, (name.encode()[:8].ljust(8, b"\x00")))


def lief_preserves(original: bytes, edited: bytes, op: str) -> bool:
    """
    Whether a LIEF edit kept the file inside the threat model: the original section bodies, the overlay, the DOS
    header and stub, and (for add-section / add-imports) the original sections' names are all still present unchanged.

    LIEF may relayout the file (A4); M only sanctions the declared change, so an edit that moved or rewrote existing
    content is rejected and not counted. The check is conservative: it requires every original section's data to
    appear verbatim in the edited file and the DOS stub to be byte-identical.
    """
    try:
        a, b = pefile.PE(data=original), pefile.PE(data=edited)
    except Exception:
        return False
    if edited[:2] != b"MZ" or original[2:original.find(b"PE\x00\x00")] not in edited:
        return False
    edited_bodies = {bytes(s.get_data()) for s in b.sections}
    for s in a.sections:
        body = bytes(s.get_data())
        if body and not any(body in eb for eb in edited_bodies):
            return False
    if op != "ren":
        edited_names = {s.Name for s in b.sections}
        if not all(s.Name in edited_names for s in a.sections):
            return False
    return True


################################################################################
# The greedy C1 search (declared effects only)
#
# NOTE: the search covers append and add-section, both in M_add and so in every threat model. They reach the
# histogram, byte-entropy, string, and section-bucket parts of PV selection's hole (check 2). Their declared effects
# come from the C1 engine (provexp.reach.predict for the append, catalogue.add_section for the declared section, over
# the instrumented extractor's item table; derivation step 9). The hand predictors of scripts/a_c1_table0.py remain
# only as the engine's test oracle (tests/test_a1_adaptive.py). The engine flags an append where a structure lies past
# the end of the file (the files that fail the precondition check); the search then skips that candidate. The
# re-encoded groups of the sums store have no recognizers yet, so the search runs against the thrember-space
# defenses only (as since run 100), and its evasion is a conservative lower bound.
################################################################################

# An edit the search can try: its name, the C1 predictor of its declared effect phi(z'), the function that
# materializes exactly that edit on the bytes, and the bytes it adds (for the byte budget).
Operation = tuple[str, Callable[[PEFeatureExtractor, bytes], np.ndarray], Callable[[bytes], bytes], int]
# The (append, add-section) C1 predictors: (extractor, z, blob) and (extractor, z, name, content, props).
PredictorSet = tuple[Callable[..., np.ndarray], Callable[..., np.ndarray]]
# The properties of an added data section, as the extractor reads them from add_section(..., code=False), and its
# characteristics as the byte-level edit writes them.
DATA_PROPS = ["CNT_INITIALIZED_DATA", "MEM_READ", "MEM_WRITE"]
DATA_CHARACTERISTICS = 0xC0000040
SECTION_BUCKETS = 50
BUCKET_GROUPS = ("section:size_hash_", "section:vsize_hash_", "section:entropy_hash_")


def engine_predictors(extractor: PEFeatureExtractor) -> PredictorSet:
    """
    The (append, add-section) C1 predictors from the engine, over `extractor`'s item table.

    Each step of the search predicts every candidate from the same state, so the item table of the last state is kept.
    A flagged prediction raises RuntimeError (`Prediction.features`), which the search counts as a query and skips.
    The features no readout models (pefile's warnings) are NaN in the engine's vector; they keep the state's values,
    as in the hand predictors.

    Args:
        extractor: The instrumented extractor whose feature vectors the defense scores.

    Returns:
        The two predictors, with the signatures `menu` calls.
    """
    last: dict[str, Any] = {}

    def _table(z: bytes) -> ItemTable:
        if last.get("z") is not z:
            last["z"], last["table"], last["x"] = z, extractor.item_table(z), None
        table: ItemTable = last["table"]
        return table

    def _fill(z: bytes, y: np.ndarray) -> np.ndarray:
        # NOTE: a NaN would read as a missing value, which a GBDT sends down its default branch: the unmodeled warning
        # features then moved the unconstrained model's declared score by up to ~3 in logit (run 108's first try).
        missing = np.isnan(y)
        if missing.any():
            if last["x"] is None:
                last["x"] = extractor.feature_vector(z)  # type: ignore[no-untyped-call]
            y = np.where(missing, last["x"], y)
        return y

    def _append(ext: PEFeatureExtractor, z: bytes, blob: bytes) -> np.ndarray:
        table = _table(z)
        return _fill(z, predict(table, z, ByteEdit(len(z), len(z), blob), ext.recognizers).features(ext.readouts))

    def _section(ext: PEFeatureExtractor, z: bytes, name: str, content: bytes, props: list[str]) -> np.ndarray:
        table = _table(z)
        return _fill(z, catalogue.add_section(ext, table, z, name, content, props).features(ext.readouts))

    return _append, _section


def section_bucket(name: str) -> tuple[int, int]:
    """The (bucket, sign) a section name's (name, value) pairs land in, as the extractor's signed FeatureHasher."""
    h = int(murmurhash3_32(name.strip("\x00").lower(), positive=False))
    return abs(h) % SECTION_BUCKETS, (-1 if h < 0 else 1)


def bucket_names() -> dict[tuple[int, int], str]:
    """One short section name per (bucket, sign): the provenance of the section-hash features, inverted."""
    table: dict[tuple[int, int], str] = {}
    letters = [chr(c) for c in range(0x61, 0x7b)]
    for a in letters:
        for b in letters:
            for c in letters:
                table.setdefault(section_bucket(f".{a}{b}{c}"), f".{a}{b}{c}")
    if len(table) < 2 * SECTION_BUCKETS:
        raise RuntimeError(f"Only {len(table)} of {2 * SECTION_BUCKETS} (bucket, sign) pairs have a name.")
    return table


def target_buckets(booster: lightgbm.Booster, feature_names: list[str], k: int) -> list[int]:
    """The k section-hash buckets the defense relies on most (split gain summed over the size/vsize/entropy hashes).

    The adaptive attacker knows the defense (white-box, the strongest adaptive setting); a name in a bucket moves that
    bucket's three features together, by the section's size, virtual size, and entropy, with the name's sign.
    """
    gain = dict(zip(feature_names, booster.feature_importance("gain")))
    score = [sum(float(gain.get(f"{g}{b}", 0.0)) for g in BUCKET_GROUPS) for b in range(SECTION_BUCKETS)]
    return [int(b) for b in np.argsort(score, kind="stable")[::-1][:k]]


def menu(donors: Donors, rng: np.random.Generator, candidates: int, preds: PredictorSet,
         targets: list[tuple[int, int]], names: dict[tuple[int, int], str]) -> list[Operation]:
    """
    A finite candidate set of declared edits, each with its C1 predictor and the function that materializes it.

    Append candidates vary the payload (random bytes, one repeated byte value, donor content) to move the byte
    histogram and string features different ways. Add-section candidates are mostly *targeted*: a name chosen from the
    inverted section hash to land in one of the defense's most-used buckets with a chosen sign (`targets`), with donor
    content of two sizes; the rest use a random name.
    """
    predict_app, predict_sec = preds
    ops: list[Operation] = []

    def _append(blob: bytes) -> Operation:
        return ("app", lambda ext, z: predict_app(ext, z, blob), lambda z: z + blob, len(blob))

    def _section(op: str, name: str, content: bytes) -> Operation:
        # NOTE: the step is materialized by our own byte-level edit, exactly the declared add-section (the section ends
        # the file, so an overlay before it is no longer one), not by LIEF: LIEF puts the section before the overlay and
        # keeps it, so every later step would claim the overlay's removal again (run 105). A file whose headers have no
        # room for another section header cannot take the edit in place; the candidate is skipped.
        def _predict(ext: PEFeatureExtractor, z: bytes) -> np.ndarray:
            if write_section(z, name.encode(), content, DATA_CHARACTERISTICS, before_overlay=False) is None:
                raise RuntimeError("No room for another section header.")
            return predict_sec(ext, z, name, content, DATA_PROPS)

        def _write(z: bytes) -> bytes:
            written = write_section(z, name.encode(), content, DATA_CHARACTERISTICS, before_overlay=False)
            if written is None:
                raise RuntimeError("No room for another section header.")
            return written[0]

        return (op, _predict, _write, len(content))

    size = int(rng.choice([4096, 65536]))
    ops.append(_append(b"\x00" + rng.integers(0, 256, size=size, dtype=np.uint8).tobytes()))
    ops.append(_append(b"\x00" + bytes([int(rng.integers(0, 256))]) * size))
    if donors.sections:
        ops.append(_append(b"\x00" + donors.sections[int(rng.integers(len(donors.sections)))][1][:size]))
    n_targeted = max(0, candidates - len(ops) - 1)
    picks = [int(i) for i in rng.permutation(len(targets))[:n_targeted]]
    for i in picks:
        content = donors.sections[int(rng.integers(len(donors.sections)))][1]
        ops.append(_section("sec", names[targets[i]], content[: int(rng.choice([4096, 65536]))]))
    while len(ops) < candidates:
        name = "." + "".join(chr(int(c)) for c in rng.integers(0x61, 0x7b, size=3))
        ops.append(_section("sec", name, donors.sections[int(rng.integers(len(donors.sections)))][1][:4096]))
    return ops[:candidates]


################################################################################
# The twelve-operation search (item 8): exact predictions, materialized by the catalogue's writers
#
# Item 7 made every structural operation's effect predictable exactly (run 118: 0 wrong of the declared edits), so the
# search can score every operation of the threat model (docs/direction-A-threat-model.md), not just append and
# add-section. Each candidate is scored by the exact prediction of our own byte-level edit -- catalogue.predict_* for
# the structural operations (add section, add imports, rename, both removals; the two gap insertions are simply
# extracted, ~5x cheaper than predicting them) and reach.predict for the in-place overwrites (header fields, checksum,
# DOS region, slack) -- so the predicted score equals the re-extracted score of the file the step writes, and the
# chosen step is materialized by exactly that writer (never LIEF). The monotone (C4) rows stay 0 by construction: a
# sound detector's score cannot fall under any operation of M.
################################################################################

# A candidate edit: its operation name, an upper bound on the bytes it adds (checked against the byte budget before it
# is scored), and a thunk that, given the current file, returns (predicted feature vector, written file, bytes added)
# or raises to skip (the operation does not apply, or its prediction was flagged).
Candidate = tuple[str, int, Callable[[bytes], tuple[np.ndarray, bytes, int]]]


class Engine:
    """Caches the current file's item table and feature vector so every candidate of a step scores from one state."""

    def __init__(self, extractor: PEFeatureExtractor) -> None:
        self.ext = extractor
        self._z: bytes | None = None
        self._table: ItemTable | None = None
        self._x: np.ndarray | None = None

    def table(self, z: bytes) -> ItemTable:
        """The item table of `z` (recomputed only when the file changes)."""
        if self._z is not z:
            self._z, self._table, self._x = z, self.ext.item_table(z), None
        assert self._table is not None
        return self._table

    def _fill(self, z: bytes, y: np.ndarray) -> np.ndarray:
        # The features no readout models (pefile's warnings) are NaN in a prediction; keep the state's values, as a
        # NaN would read as missing and send a GBDT down its default branch (run 108).
        missing = np.isnan(y)
        if missing.any():
            self.table(z)
            if self._x is None:
                self._x = np.asarray(self.ext.feature_vector(z))  # type: ignore[no-untyped-call]
            y = np.where(missing, self._x, y)
        return y

    def append(self, z: bytes, blob: bytes) -> tuple[np.ndarray, bytes, int]:
        """Score and write an append (`reach.predict`; the prediction matches re-extraction, run 107)."""
        p = predict(self.table(z), z, ByteEdit(len(z), len(z), blob), self.ext.recognizers)
        return self._fill(z, p.features(self.ext.readouts)), z + blob, len(blob)

    def declared(self, z: bytes, p: Optional[Prediction]) -> tuple[np.ndarray, bytes, int]:
        """Score and write a declared structural operation (`catalogue.predict_*`); raise if it abstains or is flagged."""
        if p is None or p.table is None:
            raise RuntimeError("the declaration does not apply or was flagged")
        return self._fill(z, p.features(self.ext.readouts)), p.new, max(0, len(p.new) - len(z))

    def inplace(self, z: bytes, edits: list[ByteEdit]) -> tuple[np.ndarray, bytes, int]:
        """Score and write a chain of in-place overwrites (`reach.predict`); raise if any step is flagged."""
        table, old, p = self.table(z), z, None
        for e in edits:
            p = predict(table, old, e, self.ext.recognizers)
            if p.table is None:
                raise RuntimeError(f"flagged: {p.reason}")
            old, table = p.new, p.table
        if p is None:
            raise RuntimeError("no edits")
        return self._fill(z, p.features(self.ext.readouts)), old, 0


def _apply(z: bytes, edits: list[ByteEdit]) -> bytes:
    for e in edits:
        z = e.apply(z)
    return z


def _sec_candidate(engine: Engine, name: str, content: bytes) -> Candidate:
    """Add a data section named `name` with donor `content` (catalogue.predict_add_section; our own writer)."""
    raw = name.encode()[:8]

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.declared(z, catalogue.predict_add_section(engine.ext, engine.table(z), z, raw, content,
                                                                 DATA_CHARACTERISTICS, False))

    return ("sec", len(content), thunk)


def _imp_candidate(engine: Engine, library: str, functions: list[str]) -> Candidate:
    """Add an import of donor `functions` from `library` (catalogue.predict_add_imports: a new import section)."""
    lib, fns = library.encode(), [f.encode() for f in functions][:20]

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.declared(z, catalogue.predict_add_imports(engine.ext, engine.table(z), z, lib, fns, False))

    return ("imp", 1 << 16, thunk)


def _ren_candidate(engine: Engine, name: str) -> Candidate:
    """Rename the first section to `name` (catalogue.predict_rename; in place, no length change)."""
    raw = name.encode()[:8]

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.declared(z, catalogue.predict_rename(engine.ext, engine.table(z), z, 0, raw))

    return ("ren", 0, thunk)


def _rm_candidate(engine: Engine, op: str, index: int) -> Candidate:
    """Remove a data-directory entry: debug (`rdb`) or security (`rsg`) (catalogue.predict_zero_entry; in place)."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.declared(z, catalogue.predict_zero_entry(engine.ext, engine.table(z), z, index))

    return (op, 0, thunk)


def _hdr_candidate(engine: Engine, values: dict[str, int]) -> Candidate:
    """Set the loader-ignored header fields (`HDR_FIELDS`) to a donor's values (reach.predict; in place)."""
    keys = [f"{h}.{f}" for h, f in HDR_FIELDS]

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        pe = pefile.PE(data=z, fast_load=True)
        edits = []
        for (struct_name, field), key in zip(HDR_FIELDS, keys):
            lo, packed = _pack_field(getattr(pe, struct_name), field, int(values[key]))
            edits.append(ByteEdit(lo, lo + len(packed), packed))
        return engine.inplace(z, edits)

    return ("hdr", 0, thunk)


def _chk_candidate(engine: Engine, value: int) -> Candidate:
    """Set OPTIONAL_HEADER.CheckSum to a donor's value (reach.predict; in place)."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        pe = pefile.PE(data=z, fast_load=True)
        lo, packed = _pack_field(pe.OPTIONAL_HEADER, "CheckSum", int(value))
        return engine.inplace(z, [ByteEdit(lo, lo + len(packed), packed)])

    return ("chk", 0, thunk)


def _region_edits(z: bytes, table: ItemTable, group: str, content: bytes, offset: int) -> list[ByteEdit]:
    """Overwrite the catalogue's in-place region for `group` with donor `content` (`offset` maps the DOS stub)."""
    pe = pefile.PE(data=z)
    edits = []
    for lo, hi in catalogue.regions(pe, z, table)[group]:
        seg = content[lo - offset: hi - offset] if offset else content[:hi - lo]
        seg = (seg + b"\x00" * (hi - lo))[: hi - lo]
        edits.append(ByteEdit(lo, hi, seg))
    return edits


def _dos_candidate(engine: Engine, stub: bytes) -> Candidate:
    """Overwrite the DOS region (bytes 2-59 and the stub) with a donor's stub (reach.predict; in place)."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        edits = _region_edits(z, engine.table(z), "dos", stub, 2)
        if not edits:
            raise RuntimeError("no DOS region")
        return engine.inplace(z, edits)

    return ("dos", 0, thunk)


def _slk_candidate(engine: Engine, content: bytes) -> Candidate:
    """Overwrite the sections' slack with donor `content` (reach.predict; in place)."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        edits = _region_edits(z, engine.table(z), "slk", content, 0)
        if not edits:
            raise RuntimeError("no slack")
        return engine.inplace(z, edits)

    return ("slk", 0, thunk)


def _gap_candidate(engine: Engine, op: str, at_pe_header: bool, kind: int, donor: bytes) -> Candidate:
    """Insert a FileAlignment-sized gap before the PE header (`ext`) or the first section's data (`shf`); extracted."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        pe = pefile.PE(data=z, fast_load=True)
        fa = pe.OPTIONAL_HEADER.FileAlignment or 0x200
        if kind == 0:
            gap = b"\x00" * fa
        elif kind == 1:
            gap = (donor + b"\x00" * fa)[:fa]
        else:
            gap = np.random.default_rng(fa).integers(0, 256, fa, dtype=np.uint8).tobytes()
        written = catalogue.write_gap(z, at_pe_header, gap)
        if written is None:
            raise RuntimeError("the gap does not apply")
        phi = np.asarray(engine.ext.feature_vector(written.new))  # type: ignore[no-untyped-call]
        return phi, written.new, len(gap)

    return (op, 1 << 16, thunk)


def _append_candidates(donors: Donors, rng: np.random.Generator, engine: Engine) -> list[Candidate]:
    size = int(rng.choice([4096, 65536]))
    blobs = [b"\x00" + rng.integers(0, 256, size=size, dtype=np.uint8).tobytes(),
             b"\x00" + bytes([int(rng.integers(0, 256))]) * size]
    if donors.sections:
        blobs.append(b"\x00" + donors.sections[int(rng.integers(len(donors.sections)))][1][:size])
    return [("app", len(blob), (lambda b: lambda z: engine.append(z, b))(blob)) for blob in blobs]


def full_menu(engine: Engine, donors: Donors, rng: np.random.Generator, targets: list[tuple[int, int]],
              names: dict[tuple[int, int], str], ops: Sequence[str], sec_targeted: int = 8) -> list[Candidate]:
    """
    A candidate set spanning every operation of the threat model (`ops`), each scored by the exact prediction of our
    own writer and materialized by that writer. Targeted section names and renames aim at the defense's most-used
    section-hash buckets (`targets`); donor material (sections, stubs, header fields, checksums, imports) comes from the
    goodware, as the GAMMA attacks draw on it.

    `sec_targeted` keeps the add-section exploration (and so the reachable set of the histogram, string, and
    section-hash features) as broad as the append/add-section-only search of run 108 -- the new operations are added
    on top of it, not in place of it, so adding them cannot weaken the search by starving it of section candidates.
    """
    out: list[Candidate] = []
    if "app" in ops:
        out += _append_candidates(donors, rng, engine)
    if "sec" in ops and donors.sections:
        for i in (int(x) for x in rng.permutation(len(targets))[:sec_targeted]):
            content = donors.sections[int(rng.integers(len(donors.sections)))][1][: int(rng.choice([4096, 65536]))]
            out.append(_sec_candidate(engine, names[targets[i]], content))
        name = "." + "".join(chr(int(c)) for c in rng.integers(0x61, 0x7b, size=3))
        out.append(_sec_candidate(engine, name, donors.sections[int(rng.integers(len(donors.sections)))][1][:4096]))
    if "imp" in ops and donors.imports:
        for _ in range(2):
            library, functions = donors.imports[int(rng.integers(len(donors.imports)))]
            out.append(_imp_candidate(engine, library, functions))
    if "ren" in ops:
        for i in (int(x) for x in rng.permutation(len(targets))[:3]):
            out.append(_ren_candidate(engine, names[targets[i]]))
    if "hdr" in ops and donors.fields:
        out.append(_hdr_candidate(engine, donors.fields[int(rng.integers(len(donors.fields)))]))
    if "chk" in ops and donors.checksums:
        out.append(_chk_candidate(engine, int(donors.checksums[int(rng.integers(len(donors.checksums)))])))
    if "dos" in ops and donors.stubs:
        out.append(_dos_candidate(engine, donors.stubs[int(rng.integers(len(donors.stubs)))]))
    if "slk" in ops and donors.sections:
        out.append(_slk_candidate(engine, donors.sections[int(rng.integers(len(donors.sections)))][1]))
    for op, at in (("ext", True), ("shf", False)):
        if op in ops:
            donor = donors.sections[int(rng.integers(len(donors.sections)))][1] if donors.sections else b""
            out.append(_gap_candidate(engine, op, at, int(rng.integers(0, 3)), donor))
    for op, index in (("rdb", DEBUG_ENTRY), ("rsg", SECURITY_ENTRY)):
        if op in ops:
            out.append(_rm_candidate(engine, op, index))
    return out


def _logit(p: float) -> float:
    p = min(max(p, 1e-12), 1 - 1e-12)
    return float(np.log(p / (1 - p)))


def greedy_search(booster: lightgbm.Booster, engine: Engine, z: bytes, tau: float,
                  make_menu: Callable[[np.random.Generator], list[Candidate]], queries: int, seed: int, cap: int
                  ) -> dict[str, Any]:
    """
    Greedily apply the edit whose predicted effect lowers the defense's score the most, until the score crosses below
    tau (evaded), no candidate helps, or the query or byte budget is spent.

    Each step scores every candidate from the current (materialized) file by the exact prediction of our own writer
    (`make_menu` builds them), then applies exactly the chosen edit, so edits compose. Because every operation is now
    predicted exactly (item 7), the predicted score of the written file equals its re-extracted score (up to the
    warning features, which no readout models); `p_adv_c1` (the predicted score) and `p_adv_real` (re-extraction of
    the final file) therefore agree, and a gap between them is a prediction bug, not A4.

    Returns a summary row: evaded (predicted), the predicted and real adversarial probabilities, the query count, the
    operations chosen, the bytes added, and min_delta_logit (the most negative predicted change of any candidate from
    any state -- the soundness probe for a C4 row).
    """
    tau_logit = _logit(tau)
    state = z
    p_state = float(booster.predict(engine.ext.feature_vector(state).reshape(1, -1))[0])  # type: ignore[no-untyped-call]
    logit_decl = _logit(p_state)
    ops_chosen: list[str] = []
    min_delta = 0.0
    used = added = 0
    rng = np.random.default_rng(seed)
    while used < queries and logit_decl > tau_logit:
        best: tuple[float, str, bytes, int] | None = None
        for name, maxbytes, thunk in make_menu(rng):
            if used >= queries:
                break
            if added + maxbytes > cap:
                continue
            used += 1
            try:
                phi, written, nbytes = thunk(state)
            except Exception:
                continue
            delta = _logit(float(booster.predict(phi.reshape(1, -1))[0])) - _logit(p_state)
            min_delta = min(min_delta, delta)
            if best is None or delta < best[0]:
                best = (delta, name, written, nbytes)
        if best is None or best[0] >= 0:
            break  # no candidate lowered the score; a sound monotone detector stops here
        _, name, state, nbytes = best
        logit_decl += best[0]
        added += nbytes
        ops_chosen.append(name)
        p_state = float(booster.predict(engine.ext.feature_vector(state).reshape(1, -1))[0])  # type: ignore[no-untyped-call]
    return {"evaded": bool(logit_decl <= tau_logit), "p_adv_c1": float(1 / (1 + np.exp(-logit_decl))),
            "p_adv_real": p_state, "evaded_real": bool(p_state <= tau), "queries": used, "ops": ",".join(ops_chosen),
            "num_ops": len(ops_chosen), "bytes_added": added, "min_delta_logit": min_delta, "tau_logit": tau_logit}


################################################################################
# Main
################################################################################

class _Padded(lightgbm.Booster):
    """A booster on a store that extends the thrember features with neutralized columns, scored on thrember vectors."""

    def __init__(self, model_file: str, dim: int) -> None:
        super().__init__(model_file=model_file)
        self.pad = self.num_feature() - dim

    def predict(self, data: Any, *args: Any, **kwargs: Any) -> Any:
        x = np.asarray(data, dtype=np.float64)
        return super().predict(np.hstack([x, np.zeros((x.shape[0], self.pad))]), *args, **kwargs)


def padded_booster(mdir: Path, dim: int) -> lightgbm.Booster:
    """Load a defense; a model on more than the `dim` thrember features must have every extra column neutralized.

    `train_classic.py --neutralize` sets those columns to zero in every split, so padding the engine's vectors with
    zeros reproduces exactly what the model saw (e.g. the `seed-0-s10-*` models on the sums store, whose 1,087 sums
    columns are neutralized), and the search can score them.
    """
    booster = lightgbm.Booster(model_file=str(mdir / "model.txt"))
    n = booster.num_feature()
    if n == dim:
        return booster
    neutralized = set(json.loads((mdir / "metrics.json").read_text()).get("neutralized") or [])
    missing = sorted(set(range(dim, n)) - neutralized)
    if n < dim or missing:
        raise RuntimeError(f"{mdir.as_posix()}: {n} features, of which {len(missing)} past the {dim} thrember ones are "
                           "not neutralized; the C1 engine cannot score it.")
    return _Padded(str(mdir / "model.txt"), dim)


def _parse_defenses(specs: list[str]) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for spec in specs:
        name, _, path = spec.partition("=")
        if not name or not path:
            raise ValueError(f"Expected name=model_dir, got {spec!r}.")
        out[name] = Path(path)
    return out


def _threshold(pred_file: Path, fpr: float) -> float:
    import polars as pl

    pred = pl.read_parquet(pred_file)
    good = np.sort(pred.filter(pl.col("label") == 0)["prob"].to_numpy())[::-1]
    return float(good[min(int(fpr * good.size), good.size - 1)])


def main() -> None:
    import polars as pl

    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--sound", nargs="*", default=[], help="Defense names that carry the C4 guarantee (a negative "
                        "min_delta_logit on one is an A1-A4 bug; on any other defense it is just the search working).")
    parser.add_argument("--features", type=Path, required=True, help="The feature store the defenses were trained on.")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--threat_model", choices=["M_add", "M_shift", "M_full"], default="M_full")
    parser.add_argument("--operations", nargs="*", default=None, help="Restrict to these operation names "
                        "(default: every operation of the threat model).")
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--candidates", type=int, default=12, help="Kept for compatibility; the full menu self-sizes.")
    parser.add_argument("--target_buckets", type=int, default=8, help="Section-hash buckets the targeted names aim at.")
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--num_malware", type=int, default=None)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    import lief
    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)
    defenses = _parse_defenses(args.defense)

    manifest = load_manifest(args.features)
    extractor = merge_import_descriptors(PEFeatureExtractor())
    if manifest["feature_names"][: extractor.dim] != extractor.feature_names:
        raise RuntimeError(f"The store {args.features.as_posix()} ({manifest['feature_set']}) does not start with the "
                           "thrember features: the C1 engine has no recognizers for other layouts.")
    engine = Engine(extractor)
    ops = tuple(args.operations) if args.operations else THREAT[args.threat_model]
    print(f"Scoring in thrember space ({extractor.dim} features); operations {','.join(ops)}.", flush=True)

    malware, goodware = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    donors = Donors(goodware)
    names = bucket_names()
    print(f"Pilot: {len(malware)} malware, {len(goodware)} goodware donors; threat model {args.threat_model}.",
          flush=True)

    rows: list[dict[str, Any]] = []
    for d, mdir in defenses.items():
        booster = padded_booster(mdir, extractor.dim)
        tau = _threshold(mdir / "ts_predictions.parquet", args.fpr)
        targets = [(b, sign) for b in target_buckets(booster, extractor.feature_names, args.target_buckets)
                   for sign in (-1, 1)]

        def make_menu(rng: np.random.Generator, targets: list[tuple[int, int]] = targets) -> list[Candidate]:
            return full_menu(engine, donors, rng, targets, names, ops)

        t0 = time.time()
        for name, data in malware:
            phi0 = extractor.feature_vector(data)  # type: ignore[no-untyped-call]
            p_clean = float(booster.predict(phi0.reshape(1, -1))[0])
            if p_clean <= tau:
                continue  # attack only what this defense detects
            try:
                pe = pefile.PE(data=data)
                overrun = has_overrun_section(pe)
            except Exception:
                overrun = False
            cap = max(int(args.budget_frac * len(data)), args.budget_min)
            r = greedy_search(booster, engine, data, tau, make_menu, args.queries, args.seed, cap)
            r.update(defense=d, name=name, tau=tau, p_clean=p_clean, truncated=len(data) >= MAX_LENGTH,
                     overrun_section=overrun)
            rows.append(r)
        print(f"  {d}: tau={tau:.4f}, {time.time() - t0:.0f}s", flush=True)

    results = pl.DataFrame(rows)
    results.write_parquet(args.outdir / "adaptive.parquet")
    report: dict[str, Any] = {"threat_model": args.threat_model, "operations": list(ops), "fpr": args.fpr,
                              "queries": args.queries, "target_buckets": args.target_buckets,
                              "budget_frac": args.budget_frac, "budget_min": args.budget_min, "seed": args.seed,
                              "defenses": {}}
    for d in defenses:
        r = results.filter(pl.col("defense") == d)
        detected = r.height
        evaded = int(r["evaded"].sum()) if detected else 0
        worst = float(r["min_delta_logit"].min() or 0.0) if detected else 0.0  # type: ignore[arg-type]
        report["defenses"][d] = {
            "detected": detected, "evaded": evaded, "rate": (evaded / detected) if detected else None,
            "min_delta_logit": worst,
            "evaded_real": int(r["evaded_real"].sum()) if detected else 0,
            "carries_guarantee": d in args.sound,
            "soundness_violation": (d in args.sound) and worst < -1e-6,
            "rate_truncated": _rate(r.filter(pl.col("truncated"))),
            "rate_untruncated": _rate(r.filter(~pl.col("truncated"))),
        }
        v = report["defenses"][d]
        flag = "  *** C4 SOUNDNESS VIOLATION (debug via Table A0)" if v["soundness_violation"] else ""
        print(f"{d:16s} detected {detected:2d}  evaded {evaded:2d} (C1-declared)  min_delta_logit {worst:+.4f}{flag}",
              flush=True)
    (args.outdir / "adaptive.json").write_text(json.dumps(report, indent=2))
    print(f"Wrote {args.outdir}/adaptive.parquet and adaptive.json", flush=True)


def _rate(r: Any) -> Any:
    if r.height == 0:
        return None
    return int(r["evaded"].sum()) / r.height


MAX_LENGTH = 4_000_000


if __name__ == "__main__":
    main()
