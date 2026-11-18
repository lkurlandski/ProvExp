"""
The adaptive attack: a greedy or beam search over the threat model's operations, with goodware donors, scoring each
candidate by its computed side effects or (`RealEngine`) by extracting it. One search per (detector, file) in a pool.
"""

from __future__ import annotations

import json
from pathlib import Path
import struct
import time
from typing import Any
from typing import Callable
from typing import Optional
from typing import Sequence

import lightgbm
import numpy as np
import pefile
from sklearn.utils import murmurhash3_32

from provexp.attacks.validity import output_invalid
from provexp.attacks.validity import structure
from provexp.data.files import load_donors
from provexp.data.files import load_pilot
from provexp.featuresets.ember2024 import catalogue
from provexp.featuresets.ember2024.edits import add_section as write_section
from provexp.featuresets.ember2024.edits import entry_write
from provexp.featuresets.ember2024.edits import past_end as past_end_edit
from provexp.featuresets.ember2024.escapes import WRITES as ESCAPES
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import field_range
from provexp.featuresets.ember2024.features import fix_quirks
from provexp.featuresets.ember2024.population import has_overrun_section
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.items import ItemTable
from provexp.models.erdalt import ERDALTDetector
from provexp.models.erdalt import is_erdalt
from provexp.reach import ByteEdit
from provexp.reach import Prediction
from provexp.reach import predict

__all__ = ["Donors", "Engine", "HDR_FIELDS", "Operation", "RealEngine", "THREAT", "add_imports", "add_section",
           "beam_search", "bucket_names", "engine_predictors", "full_menu", "greedy_search", "lief_preserves", "menu",
           "padded_booster", "prepare_files", "rename_section", "section_bucket", "set_header_fields",
           "target_buckets", "zero_directory_entry"]


# The threat models' operation sets (pipeline/3-directions/derived/directions.py): additions, gap insertions, in-place overwrites.
ADD, INSERT, OVERWRITE = ("app", "sec", "imp"), ("ext", "shf"), ("slk", "dos", "hdr", "chk", "ren", "rdb", "rsg", "ent")


THREAT = {"M_add": ADD, "M_shift": ADD + INSERT, "M_full": ADD + INSERT + OVERWRITE}


# The loader-ignored header fields (the threat model's `hdr`, matching pipeline/3-directions/derived/directions.py's `header` group).
HDR_FIELDS = (("FILE_HEADER", "TimeDateStamp"), ("FILE_HEADER", "NumberOfSymbols"),
              ("FILE_HEADER", "PointerToSymbolTable"), ("OPTIONAL_HEADER", "MajorImageVersion"),
              ("OPTIONAL_HEADER", "MinorImageVersion"), ("OPTIONAL_HEADER", "MajorLinkerVersion"),
              ("OPTIONAL_HEADER", "MinorLinkerVersion"), ("OPTIONAL_HEADER", "MajorOperatingSystemVersion"),
              ("OPTIONAL_HEADER", "MinorOperatingSystemVersion"))


DEBUG_ENTRY, SECURITY_ENTRY = 6, 4


class Donors:
    """Section names and contents, DOS stubs, header-field values, checksums, and imports taken from the goodware."""

    def __init__(self, goodware: list[tuple[str, bytes]]) -> None:
        self.sections: list[tuple[str, bytes, int]] = []
        self.stubs: list[bytes] = []
        self.fields: list[dict[str, int]] = []
        self.checksums: list[int] = []
        self.imports: list[tuple[str, list[str]]] = []
        self.certificates: list[bytes] = []  # WIN_CERTIFICATE blobs from signed donors (for signature cloning, `ent`)
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
            dd = pe.OPTIONAL_HEADER.DATA_DIRECTORY
            if len(dd) > SECURITY_ENTRY and dd[SECURITY_ENTRY].VirtualAddress and dd[SECURITY_ENTRY].Size:
                cert = data[dd[SECURITY_ENTRY].VirtualAddress: dd[SECURITY_ENTRY].VirtualAddress + dd[SECURITY_ENTRY].Size]
                if cert:
                    self.certificates.append(cert)
            for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
                names = [i.name.decode() for i in entry.imports if i.name]
                if names:
                    self.imports.append((entry.dll.decode(), names[:20]))
        if not (self.sections and self.stubs and self.imports):
            raise RuntimeError("The donor pool has no sections, stubs, or imports.")


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


def target_buckets(booster: lightgbm.Booster, feature_names: list[str], k: int,
                   X: Optional[np.ndarray] = None) -> list[int]:
    """The k section-hash buckets the defense relies on most (split gain summed over the size/vsize/entropy hashes).

    The adaptive attacker knows the defense (white-box, the strongest adaptive setting); a name in a bucket moves that
    bucket's three features together, by the section's size, virtual size, and entropy, with the name's sign. A neural
    defense (ERDALT) has no split gain; its importance is the mean gradient magnitude over `X` (the pilot malware).
    """
    if isinstance(booster, ERDALTDetector):
        if X is None:
            raise ValueError("A neural defense needs X to rank the buckets.")
        gain = dict(zip(booster.feature_names, booster.sensitivity(X)))
    else:
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

    @property
    def dim(self) -> int:
        """The length of `score`'s vectors."""
        return int(self.ext.dim)

    def score(self, z: bytes) -> np.ndarray:
        """The feature vector of a written file, by extraction."""
        return np.asarray(self.ext.feature_vector(z))  # type: ignore[no-untyped-call]

    def append(self, z: bytes, blob: bytes) -> tuple[np.ndarray, bytes, int]:
        """Score and write an append (`reach.predict`; the prediction matches re-extraction, run 107)."""
        p = predict(self.table(z), z, ByteEdit(len(z), len(z), blob), self.ext.recognizers)
        return self._fill(z, p.features(self.ext.readouts)), z + blob, len(blob)

    def declared(self, z: bytes, p: Optional[Prediction]) -> tuple[np.ndarray, bytes, int]:
        """Score and write a declared structural operation (`catalogue.predict_*`); raise if it abstains or is flagged."""
        if p is None or p.table is None:
            raise RuntimeError("the declaration does not apply or was flagged")
        return self._fill(z, p.features(self.ext.readouts)), p.new, max(0, len(p.new) - len(z))

    def structural(self, z: bytes, predict: Callable[[], Optional[Prediction]],
                   write: Callable[[], Optional[bytes]]) -> tuple[np.ndarray, bytes, int]:
        """A declared structural operation, given as its `catalogue.predict_*` and its `catalogue.written_*`."""
        return self.declared(z, predict())

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
        return self._fill(z, p.features(self.ext.readouts)), old, max(0, len(old) - len(z))


def _apply(z: bytes, edits: list[ByteEdit]) -> bytes:
    for e in edits:
        z = e.apply(z)
    return z


class RealEngine(Engine):
    """
    Scores every candidate by extracting the file our writer produces, with `vector` (the defenses' store), and never
    declines one: for files outside the population, where the computed effects do not hold (meta-review 2026-11-12, R7),
    and for the edits the computation declines (the header-field overwrites, most DOS-region overwrites).
    The item table is still used, but only to locate the regions the in-place operations write.
    """

    def __init__(self, extractor: PEFeatureExtractor, vector: PEFeatureExtractor) -> None:
        super().__init__(extractor)
        self.vector = vector

    @property
    def dim(self) -> int:
        """The length of `score`'s vectors (the defenses' store)."""
        return int(self.vector.dim)

    def score(self, z: bytes) -> np.ndarray:
        """The defenses' feature vector of `z`, by extraction."""
        return np.asarray(self.vector.feature_vector(z))  # type: ignore[no-untyped-call]

    def append(self, z: bytes, blob: bytes) -> tuple[np.ndarray, bytes, int]:
        """Write and extract an append."""
        return self.score(z + blob), z + blob, len(blob)

    def declared(self, z: bytes, p: Optional[Prediction]) -> tuple[np.ndarray, bytes, int]:
        """Write and extract a structural operation, flagged or not (the prediction carries the written file)."""
        if p is None:
            raise RuntimeError("the operation does not apply")
        return self.score(p.new), p.new, max(0, len(p.new) - len(z))

    def structural(self, z: bytes, predict: Callable[[], Optional[Prediction]],
                   write: Callable[[], Optional[bytes]]) -> tuple[np.ndarray, bytes, int]:
        """Write and extract a structural operation; only the written file is needed, so nothing is predicted."""
        new = write()
        if new is None:
            raise RuntimeError("the operation does not apply")
        return self.score(new), new, max(0, len(new) - len(z))

    def inplace(self, z: bytes, edits: list[ByteEdit]) -> tuple[np.ndarray, bytes, int]:
        """Write and extract a chain of in-place overwrites."""
        if not edits:
            raise RuntimeError("no edits")
        new = _apply(z, edits)
        return self.score(new), new, max(0, len(new) - len(z))


def _sec_candidate(engine: Engine, name: str, content: bytes) -> Candidate:
    """Add a data section named `name` with donor `content` (catalogue.predict_add_section; our own writer)."""
    raw = name.encode()[:8]

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.structural(
            z,
            lambda: catalogue.predict_add_section(engine.ext, engine.table(z), z, raw, content, DATA_CHARACTERISTICS,
                                                  False),
            lambda: catalogue.written_add_section(z, raw, content, DATA_CHARACTERISTICS, False))

    return ("sec", len(content), thunk)


def _imp_candidate(engine: Engine, library: str, functions: list[str]) -> Candidate:
    """Add an import of donor `functions` from `library` (catalogue.predict_add_imports: a new import section)."""
    lib, fns = library.encode(), [f.encode() for f in functions][:20]

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.structural(z, lambda: catalogue.predict_add_imports(engine.ext, engine.table(z), z, lib, fns, False),
                                 lambda: catalogue.written_add_imports(z, lib, fns, False))

    return ("imp", 1 << 16, thunk)


def _ren_candidate(engine: Engine, name: str) -> Candidate:
    """Rename the first section to `name` (catalogue.predict_rename; in place, no length change)."""
    raw = name.encode()[:8]

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.structural(z, lambda: catalogue.predict_rename(engine.ext, engine.table(z), z, 0, raw),
                                 lambda: catalogue.written_rename(z, 0, raw))

    return ("ren", 0, thunk)


def _rm_candidate(engine: Engine, op: str, index: int) -> Candidate:
    """Remove a data-directory entry: debug (`rdb`) or security (`rsg`) (catalogue.predict_zero_entry; in place)."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        return engine.structural(z, lambda: catalogue.predict_zero_entry(engine.ext, engine.table(z), z, index),
                                 lambda: catalogue.written_zero_entry(z, index))

    return (op, 0, thunk)


def _ent_zero_candidate(engine: Engine) -> Candidate:
    """Zero the certificate and debug data-directory entries (`catalogue_checks._entry_write`; in place, 16 bytes)."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        pe = pefile.PE(data=z, fast_load=True)
        if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= max(DEBUG_ENTRY, SECURITY_ENTRY):
            raise RuntimeError("no certificate or debug entry")
        edits = [entry_write(pe, i, 0, 0) for i in (SECURITY_ENTRY, DEBUG_ENTRY)]
        return engine.inplace(z, edits)

    return ("ent", 0, thunk)


def _ent_past_end_candidate(engine: Engine, index: int) -> Candidate:
    """Point the certificate (`index` 4) or debug (6) entry past the end of the file (`_past_end`; in place, 8 bytes)."""

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        pe = pefile.PE(data=z, fast_load=True)
        e = past_end_edit(pe, index, len(z), len(z))
        if e is None:
            raise RuntimeError("the entry cannot be pointed past the end")
        return engine.inplace(z, [e])

    return ("ent", 0, thunk)


def _ent_clone_candidate(engine: Engine, cert: bytes) -> Candidate:
    """
    Signature cloning (`ent`): append a signed donor's certificate (8-byte aligned) and point the security entry at it,
    so the file parses as signed (the certificate table is located by a file offset, not an RVA). An append then an
    in-place entry write, both our own byte edits (`entry_write`).
    """

    def thunk(z: bytes) -> tuple[np.ndarray, bytes, int]:
        pe = pefile.PE(data=z, fast_load=True)
        if len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) <= SECURITY_ENTRY:
            raise RuntimeError("no security entry")
        pad = (8 - len(z) % 8) % 8
        appended = b"\x00" * pad + cert
        edits = [ByteEdit(len(z), len(z), appended), entry_write(pe, SECURITY_ENTRY, len(z) + pad, len(cert))]
        return engine.inplace(z, edits)

    return ("ent", len(cert) + 7, thunk)  # the bound covers the alignment padding (at most 7 bytes)


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
        return engine.score(written.new), written.new, len(gap)

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
    if "ent" in ops:
        out.append(_ent_zero_candidate(engine))
        for index in (SECURITY_ENTRY, DEBUG_ENTRY):
            out.append(_ent_past_end_candidate(engine, index))
        if donors.certificates:
            out.append(_ent_clone_candidate(engine, donors.certificates[int(rng.integers(len(donors.certificates)))]))
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
    p_state = float(booster.predict(engine.score(state).reshape(1, -1))[0])
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
        p_state = float(booster.predict(engine.score(state).reshape(1, -1))[0])
    return {"evaded": bool(logit_decl <= tau_logit), "p_adv_c1": float(1 / (1 + np.exp(-logit_decl))),
            "p_adv_real": p_state, "evaded_real": bool(p_state <= tau), "queries": used, "ops": ",".join(ops_chosen),
            "num_ops": len(ops_chosen), "bytes_added": added, "min_delta_logit": min_delta, "tau_logit": tau_logit,
            "_best": state}


# A file the beam keeps: its real logit, its bytes, the bytes added so far, and the operations that produced it.
BeamState = tuple[float, bytes, int, tuple[str, ...]]


def _tie_order(logits: Sequence[float], rng: np.random.Generator, rtol: float = 1e-9) -> list[int]:
    """Indices sorted by logit (ascending), ties within `rtol` (relative) broken by a seeded permutation."""
    perm = rng.permutation(len(logits))
    order = sorted(perm.tolist(), key=lambda i: logits[i])
    out: list[int] = []
    group: list[int] = []
    for i in order:
        if group and abs(logits[i] - logits[group[0]]) > rtol * max(1.0, abs(logits[group[0]])):
            out += [group[j] for j in rng.permutation(len(group))]
            group = []
        group.append(i)
    out += [group[j] for j in rng.permutation(len(group))]
    return out


def beam_search(booster: lightgbm.Booster, engine: Engine, z: bytes, tau: float,
                make_menu: Callable[[np.random.Generator], list[Candidate]], queries: int, seed: int, cap: int,
                beam: int = 3, draws: int = 2, patience: int = 3, checkpoints: Sequence[int] = (200, 1000, 5000)
                ) -> dict[str, Any]:
    """
    Beam search over the threat model's operations with restarts, until a file's score crosses below tau (evaded) or
    the query budget is spent.

    Each step scores `draws` fresh menus from every kept file (each candidate by the exact prediction of our own
    writer, as in `greedy_search`), merges the children with the kept files, and keeps the `beam` lowest-scoring
    distinct files (ties broken by a seeded permutation). Each kept child is re-extracted, so the beam always holds real
    scores, and a child whose predicted score crosses tau counts only if its re-extracted score does too. After
    `patience` steps without a new best score, the beam restarts from the original file; the best file found so far is
    kept for the result.

    Args:
        booster: The defense.
        engine: The C1 engine over the instrumented extractor.
        z: The malware's bytes.
        tau: The defense's threshold (detected means p > tau).
        make_menu: Builds one random menu of candidates.
        queries: The scoring budget (candidates scored, in all).
        seed: Seeds the menus and the tie-breaking.
        cap: The byte budget (bytes added, in all).
        beam: Files kept per step.
        draws: Menus drawn per kept file per step.
        patience: Steps without a new best score before a restart.
        checkpoints: Query counts at which to report whether the file was evaded by then.

    Returns:
        A summary row, with the columns of `greedy_search` plus `queries_to_evade`, `restarts`, `steps`,
        `mismatches` (kept children whose re-extracted score differs from the prediction by more than 1e-6 in logit),
        and `evaded_at_{q}` for each checkpoint.
    """
    if beam < 1 or draws < 1 or patience < 1:
        raise ValueError(f"beam, draws, and patience must be positive, got {beam}, {draws}, {patience}.")
    tau_logit = _logit(tau)
    rng = np.random.default_rng(seed)

    def real(x: bytes) -> float:
        return _logit(float(booster.predict(engine.score(x).reshape(1, -1))[0]))

    start: BeamState = (real(z), z, 0, ())
    kept: list[BeamState] = [start]
    best = start
    used = steps = restarts = stalled = mismatches = 0
    min_delta = 0.0
    evade_at: Optional[int] = None
    while used < queries and best[0] > tau_logit:
        steps += 1
        children: list[tuple[float, bytes, int, tuple[str, ...]]] = []
        for parent in kept:
            for _ in range(draws):
                for name, maxbytes, thunk in make_menu(rng):
                    if used >= queries:
                        break
                    if parent[2] + maxbytes > cap:
                        continue
                    used += 1
                    try:
                        phi, written, nbytes = thunk(parent[1])
                    except Exception:
                        continue
                    pred = _logit(float(booster.predict(phi.reshape(1, -1))[0]))
                    min_delta = min(min_delta, pred - parent[0])
                    children.append((pred, written, parent[2] + nbytes, parent[3] + (name,)))
        pool = kept + children
        order = _tie_order([s[0] for s in pool], rng)
        seen: set[bytes] = set()
        nxt: list[BeamState] = []
        for i in order:
            s = pool[i]
            if s[1] in seen:
                continue
            seen.add(s[1])
            if i >= len(kept):  # a child: replace its predicted score with the re-extracted one
                r = real(s[1])
                mismatches += int(abs(r - s[0]) > 1e-6)
                s = (r, s[1], s[2], s[3])
            nxt.append(s)
            if len(nxt) == beam:
                break
        kept = sorted(nxt, key=lambda s: s[0])
        if kept[0][0] < best[0] - 1e-9 * max(1.0, abs(best[0])):
            best, stalled = kept[0], 0
        else:
            stalled += 1
        if best[0] <= tau_logit:
            evade_at = used
            break
        if stalled >= patience:
            kept, stalled, restarts = [start], 0, restarts + 1
    row: dict[str, Any] = {
        "evaded": bool(best[0] <= tau_logit), "p_adv_c1": float(1 / (1 + np.exp(-best[0]))),
        "p_adv_real": float(1 / (1 + np.exp(-best[0]))), "evaded_real": bool(best[0] <= tau_logit), "queries": used,
        "ops": ",".join(best[3]), "num_ops": len(best[3]), "bytes_added": best[2], "min_delta_logit": min_delta,
        "tau_logit": tau_logit, "queries_to_evade": evade_at, "restarts": restarts, "steps": steps,
        "mismatches": mismatches, "_best": best[1]}
    for q in checkpoints:
        row[f"evaded_at_{q}"] = evade_at is not None and evade_at <= q
    return row


################################################################################
# Setup: the per-file work before the search
################################################################################

# One prepared file: (name, the file the search starts from, the unescaped original, the original's feature vector,
# the start's, whether the original is in the loose population, whether the start is).
Prepared = tuple[str, bytes, bytes, np.ndarray, np.ndarray, bool, bool]

_S: dict[str, Any] = {}


def _init_setup(score: str, escape: str) -> None:
    """Build the setup's extractors once per process."""
    import lief
    lief.logging.disable()
    extractor = fix_quirks(PEFeatureExtractor())
    _S.clear()
    _S.update(extractor=extractor, vector=SumsFeatureExtractor() if score == "real" else extractor, escape=escape)


def _prepare_file(data: bytes) -> Optional[tuple[Optional[bytes], np.ndarray, np.ndarray, bool, bool]]:
    """
    One file's setup: the escape write (if any), the feature vectors, and the loose population checks.

    Returns:
        (the escaped file, or None without an escape; the original's vector; the start's; the original's and the
        start's loose population checks), or None for a file the escape leaves out (it cannot be written, or the
        written file is still in the strict population, so the escape did not take it out).
    """
    extractor, vector, escape = _S["extractor"], _S["vector"], _S["escape"]
    if escape != "none":
        try:
            out = ESCAPES[escape](pefile.PE(data=data), len(data))
        except Exception:  # noqa: BLE001
            out = None
        if out is None or catalogue.passes_precondition(extractor, out):
            return None
        v_orig = vector.feature_vector(data)
        in_pop = catalogue.passes_precondition(extractor, data, loose=True)
        v_start = vector.feature_vector(out)
        return out, v_orig, v_start, in_pop, catalogue.passes_precondition(extractor, out, loose=True)
    v_orig = vector.feature_vector(data)
    in_pop = catalogue.passes_precondition(extractor, data, loose=True)
    return None, v_orig, v_orig, in_pop, in_pop


def prepare_files(malware: list[tuple[str, bytes]], score: str, escape: str, num_workers: int) -> list[Prepared]:
    """
    The setup of every file, over `num_workers` processes (in this process when 1), in the input's order.

    Each file is extracted once here, whatever the number of defenses; the defenses' scores are then a prediction per
    defense on these vectors.

    Args:
        malware: (name, bytes) of the files to attack.
        score: "real" (the sums extractor's vectors) or "predicted" (the thrember extractor's).
        escape: An escape write of `ESCAPES`, or "none".
        num_workers: Processes.

    Returns:
        The prepared files, without those the escape leaves out.
    """
    if escape != "none" and escape not in ESCAPES:
        raise ValueError(f"Unknown escape {escape!r}; expected one of {sorted(ESCAPES)} or 'none'.")
    if num_workers < 1:
        raise ValueError(f"num_workers must be >= 1, got {num_workers}.")
    blobs = [data for _, data in malware]
    if num_workers == 1 or len(blobs) <= 1:
        _init_setup(score, escape)
        results = [_prepare_file(b) for b in blobs]
    else:
        from multiprocessing import get_context
        with get_context("spawn").Pool(min(num_workers, len(blobs)), initializer=_init_setup,
                                       initargs=(score, escape)) as pool:
            results = pool.map(_prepare_file, blobs, chunksize=max(1, len(blobs) // (4 * num_workers)))
    prepared: list[Prepared] = []
    for (name, data), r in zip(malware, results):
        if r is not None:
            out, v_orig, v_start, in_pop, start_in_pop = r
            prepared.append((name, data if out is None else out, data, v_orig, v_start, in_pop, start_in_pop))
    return prepared


_W: dict[str, Any] = {}


def _init_worker(config: dict[str, Any], malware: Optional[list[tuple[str, bytes]]] = None,
                 goodware: Optional[list[tuple[str, bytes]]] = None) -> None:
    """Build the extractor, engine, donors, and bucket names once per process; boosters load lazily per defense."""
    import lief
    lief.logging.disable()
    if goodware is None:  # a worker process: only the donors are needed, read as the main process read them
        if config.get("protocol", "pilot") == "pilot":
            _, goodware = load_pilot(config["pilot_files"], config["db"])
        else:
            goodware = load_donors(config["donors"])
    extractor = fix_quirks(PEFeatureExtractor())
    engine = RealEngine(extractor, SumsFeatureExtractor()) if config.get("score") == "real" else Engine(extractor)
    _W.clear()
    _W.update(config=config, extractor=extractor, engine=engine, donors=Donors(goodware),
              names=bucket_names(), boosters={})


def _lost(task: tuple[str, str, float, list[tuple[int, int]], str, bytes, float, bool, bool]) -> None:
    """A search given up by the watchdog (over its limit, or its worker died): no row; the caller lists it as lost."""
    return None


def _attack_file(task: tuple[str, str, float, list[tuple[int, int]], str, bytes, float, bool, bool]) -> dict[str, Any]:
    """Run the configured search on one detected file against one defense."""
    defense, mdir, tau, targets, name, data, p_orig, in_pop, start_in_pop = task
    cfg, engine = _W["config"], _W["engine"]
    if mdir not in _W["boosters"]:
        _W["boosters"][mdir] = padded_booster(Path(mdir), engine.dim)
    booster = _W["boosters"][mdir]

    def make_menu(rng: np.random.Generator) -> list[Candidate]:
        return full_menu(engine, _W["donors"], rng, targets, _W["names"], cfg["ops"])

    p_clean = float(booster.predict(engine.score(data).reshape(1, -1))[0])
    try:
        overrun = has_overrun_section(pefile.PE(data=data))
    except Exception:
        overrun = False
    cap = max(int(cfg["budget_frac"] * len(data)), cfg["budget_min"])
    t0 = time.time()
    if cfg["search"] == "beam":
        r = beam_search(booster, engine, data, tau, make_menu, cfg["queries"], cfg["seed"], cap, beam=cfg["beam"],
                        draws=cfg["draws"], patience=cfg["patience"], checkpoints=cfg["checkpoints"])
    else:
        r = greedy_search(booster, engine, data, tau, make_menu, cfg["queries"], cfg["seed"], cap)
    best_file = r.pop("_best")
    # The paper's validity rule (provexp.attacks.validity): the end file counts only if both parsers read it and lose
    # nothing the start file had (start files the parsers do not read were left out before the search).
    invalid = ""
    if best_file != data:
        original, why = structure(data)
        invalid = (output_invalid(original, best_file) or "") if original is not None else f"start file: {why}"
    r.update(valid=not invalid, invalid_reason=invalid)
    if cfg.get("save_rows"):
        # The best file's re-extracted feature row, in the store's layout (`--score real`), for adversarial training.
        r["phi"] = engine.score(best_file).astype(np.float32).tolist()
    r.update(defense=defense, name=name, tau=tau, p_clean=p_clean, p_orig=p_orig, in_population=in_pop,
             start_in_population=start_in_pop, evaded_by_escape=bool(p_clean <= tau), truncated=len(data) >= MAX_LENGTH,
             overrun_section=overrun, seconds=time.time() - t0)
    return r


class _Padded(lightgbm.Booster):
    """A booster on a store that extends the thrember features with neutralized columns, scored on thrember vectors."""

    def __init__(self, model_file: str, dim: int) -> None:
        super().__init__(model_file=model_file)
        self.pad = self.num_feature() - dim

    def predict(self, data: Any, *args: Any, **kwargs: Any) -> Any:
        x = np.asarray(data, dtype=np.float64)
        return super().predict(np.hstack([x, np.zeros((x.shape[0], self.pad))]), *args, **kwargs)


def padded_booster(mdir: Path, dim: int) -> Any:
    """Load a defense; a model on more than the `dim` thrember features must have every extra column neutralized.

    `train_classic.py --neutralize` sets those columns to zero in every split, so padding the engine's vectors with
    zeros reproduces exactly what the model saw (e.g. the `seed-0-s10-*` models on the sums store, whose 1,087 sums
    columns are neutralized), and the search can score them.
    """
    if is_erdalt(mdir):
        return ERDALTDetector(mdir)  # its own layout is the thrember features (train_erdalt.py drops the rest)
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


MAX_LENGTH = 4_000_000
