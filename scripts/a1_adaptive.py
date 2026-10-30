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
from provexp.reach import predict

sys.path.insert(0, str(Path(__file__).parent))
from a_c1_table0 import has_overrun_section  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from catalogue_checks import add_section as write_section  # noqa: E402

__all__ = ["Donors", "HDR_FIELDS", "Operation", "add_imports", "add_section", "engine_predictors", "greedy_search",
           "lief_preserves", "bucket_names", "menu", "rename_section", "section_bucket", "set_header_fields", "zero_directory_entry"]

ROOT = Path(__file__).resolve().parent.parent

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


def _logit(p: float) -> float:
    p = min(max(p, 1e-12), 1 - 1e-12)
    return float(np.log(p / (1 - p)))


def greedy_search(booster: lightgbm.Booster, extractor: PEFeatureExtractor, z: bytes, tau: float, donors: Donors,
                  queries: int, candidates: int, seed: int, preds: PredictorSet, targets: list[tuple[int, int]],
                  names: dict[tuple[int, int], str], cap: int) -> dict[str, Any]:
    """
    Greedily apply the declared edit whose C1-predicted effect lowers the defense's score the most, until the
    declared score crosses below tau (evaded), no candidate helps, or the query or byte budget is spent.

    Each step predicts every candidate from the current (materialized) file and then applies exactly the chosen edit,
    so edits compose. The declared score is the clean logit plus the sum of the chosen steps' declared changes: the
    tool's layout effects between steps (A4, outside M) are excluded, as in the single-step case; the real score of
    the final file is reported alongside (`p_adv_real`, the A4 gap).

    Returns a summary row: evaded (declared), the declared and real adversarial probabilities, the query count, the
    operations chosen, the bytes added, and min_delta_logit (the most negative declared change of any candidate from
    any state -- the soundness probe for a C4 row).
    """
    tau_logit = _logit(tau)
    state = z
    p_state = float(booster.predict(extractor.feature_vector(state).reshape(1, -1))[0])  # type: ignore[no-untyped-call]
    logit_decl = _logit(p_state)
    ops_chosen: list[str] = []
    min_delta = 0.0
    used = added = 0
    rng = np.random.default_rng(seed)
    while used < queries and logit_decl > tau_logit:
        best: tuple[float, Operation] | None = None
        for op in menu(donors, rng, candidates, preds, targets, names):
            if used >= queries:
                break
            if added + op[3] > cap:
                continue
            used += 1
            try:
                phi = op[1](extractor, state)
            except Exception:
                continue
            delta = _logit(float(booster.predict(phi.reshape(1, -1))[0])) - _logit(p_state)
            min_delta = min(min_delta, delta)
            if best is None or delta < best[0]:
                best = (delta, op)
        if best is None or best[0] >= 0:
            break  # no candidate lowered the declared score; a sound monotone detector stops here
        try:
            state = best[1][2](state)
        except Exception:
            break
        logit_decl += best[0]
        added += best[1][3]
        ops_chosen.append(best[1][0])
        p_state = float(booster.predict(extractor.feature_vector(state).reshape(1, -1))[0])  # type: ignore[no-untyped-call]
    return {"evaded": bool(logit_decl <= tau_logit), "p_adv_c1": float(1 / (1 + np.exp(-logit_decl))),
            "p_adv_real": p_state, "evaded_real": bool(p_state <= tau), "queries": used, "ops": ",".join(ops_chosen),
            "num_ops": len(ops_chosen), "bytes_added": added, "min_delta_logit": min_delta, "tau_logit": tau_logit}


################################################################################
# Main
################################################################################

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
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--candidates", type=int, default=12)
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
    if manifest["feature_set"] != "ember2024 (thrember v3)":
        raise RuntimeError(f"Unexpected feature set {manifest['feature_set']} in {args.features.as_posix()}: the C1 "
                           "engine has no recognizers for the sums store's re-encoded groups yet.")
    extractor = merge_import_descriptors(PEFeatureExtractor())
    preds = engine_predictors(extractor)
    print(f"Scoring in thrember space ({extractor.dim} features).", flush=True)

    malware, goodware = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    donors = Donors(goodware)
    names = bucket_names()
    print(f"Pilot: {len(malware)} malware, {len(goodware)} goodware donors; threat model {args.threat_model}.",
          flush=True)

    rows: list[dict[str, Any]] = []
    for d, mdir in defenses.items():
        booster = lightgbm.Booster(model_file=str(mdir / "model.txt"))
        tau = _threshold(mdir / "ts_predictions.parquet", args.fpr)
        targets = [(b, sign) for b in target_buckets(booster, extractor.feature_names, args.target_buckets)
                   for sign in (-1, 1)]
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
            r = greedy_search(booster, extractor, data, tau, donors, args.queries, args.candidates, args.seed, preds,
                              targets, names, cap)
            r.update(defense=d, name=name, tau=tau, p_clean=p_clean, truncated=len(data) >= MAX_LENGTH,
                     overrun_section=overrun)
            rows.append(r)
        print(f"  {d}: tau={tau:.4f}, {time.time() - t0:.0f}s", flush=True)

    results = pl.DataFrame(rows)
    results.write_parquet(args.outdir / "adaptive.parquet")
    report: dict[str, Any] = {"threat_model": args.threat_model, "fpr": args.fpr, "queries": args.queries,
                              "candidates": args.candidates, "target_buckets": args.target_buckets,
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
