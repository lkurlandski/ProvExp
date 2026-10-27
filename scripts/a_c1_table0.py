"""
Direction A, go/no-go check 1 (docs/direction-A-mock.md, Table A0): does C1 predict the edited file's features from
the item table of the original, without extracting the edited file?

C1 (docs/feature-provenance-model.md): for an edit that adds, removes, modifies, or moves a known set of items,
phi(z') = g(A(z) + sum of the touched items' contribution changes). We test it as the mock specifies: apply a
transformation to a pilot file, predict phi(z') with C1 from z alone, re-extract z', and compare feature by feature.
A pair "holds" if the prediction matches re-extraction within tolerance on every feature; mismatches are attributed
to the model's assumptions A1-A4.

These are not attacks: the edits are loader-safe transformations from Section 6, implemented so their features can
be differenced. Two are implemented, one per non-structural class:
  - append (row 1, item-creating): attacker-chosen bytes at the end (secml/GAMMA padding), prefixed with one
    non-printable guard byte so no string straddles the old/new boundary (A3's margin as a one-byte catalogue
    restriction, docs C3 step 2). It drives every readout through the file-size denominator.
  - dos_overwrite (row 3, content): an in-place overwrite of the loader-ignored DOS-header fields, bytes [2, 60),
    leaving e_magic and e_lfanew intact so the PE header is still located. No parse change, no length change.

The predictor updates only the groups each edit can touch and copies the rest, reusing the extractor's own window
and string routines on local bytes (old tail + appended, or the edited window); it never re-parses z'. Append touches
histogram, general, byteentropy, strings, and section (size_ratios + the growing overlay + max/min). The content edit
touches histogram, general (entropy, start bytes), byteentropy (the overlapping window), strings (the local run), and
the header DOS fields.

The C1 engine (provexp.reach, derivation step 5; docs/item-layer-design.md, check G4) predicts the same pairs from
the instrumented extractor's item table: append and dos_overwrite as byte edits (the engine itself flags writes to
locating ranges, e.g. an append that reaches a section running past the end of the file), add_section through the
catalogue's declaration. Its columns (`engine_*`) compare it with re-extraction and with the hand predictors.

Outputs, in `{outdir}/`:
    table0.parquet   one row per (file, transformation): exact match, num mismatching features, max abs error, timing
    mismatches.parquet   one row per (file, transformation, feature) that mismatched: predicted, actual, group
    report.json      per transformation: pairs, % exact, mismatching-feature counts by group and feature

Usage (smoke on five files):
    PYTHONHASHSEED=0 python scripts/a_c1_table0.py --outdir artifacts/experiments/a_c1 --num_files 5
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np
import pefile
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import StringExtractor
from provexp.featuresets.ember2024.catalogue import add_section
from provexp.featuresets.ember2024.sums import BodyByteEntropyHistogram
from provexp.featuresets.ember2024.sums import BodyStrings
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor
from provexp.featuresets.ember2024.sums import body_regions
from provexp.featuresets.ember2024.sums import signed_bucket
from provexp.items import ItemTable
from provexp.items import Readout
from provexp.reach import ByteEdit
from provexp.reach import Prediction
from provexp.reach import predict

__all__ = ["append_payload", "predict_add_section_sums", "predict_append", "predict_append_sums"]

ROOT = Path(__file__).resolve().parent.parent
_STRINGS = StringExtractor()  # type: ignore[no-untyped-call]

# Fixed file offsets of the IMAGE_DOS_HEADER members EMBER reads as `header` features (each a little-endian uint16);
# e_magic (0) and e_lfanew (60, a uint32) are locating elements left untouched by the DOS-fields edit.
_DOS_OFFSETS = {"e_cblp": 2, "e_cp": 4, "e_crlc": 6, "e_cparhdr": 8, "e_minalloc": 10, "e_maxalloc": 12, "e_ss": 14,
                "e_sp": 16, "e_csum": 18, "e_ip": 20, "e_cs": 22, "e_lfarlc": 24, "e_ovno": 26, "e_oemid": 36,
                "e_oeminfo": 38}


def _byte_entropy(data: bytes) -> float:
    """Shannon entropy (base 2) of a byte string, matching EMBER's GeneralFileInfo/overlay formula."""
    if len(data) == 0:
        return 0.0
    n = len(data)
    h = 0.0
    for count in Counter(bytearray(data)).values():
        p = count / n
        h -= p * math.log(p, 2)
    return h


def has_overrun_section(pe: pefile.PE) -> bool:
    """True if any section's declared raw data runs past the end of the file.

    Such a section's content is clamped by the file length, so appending bytes extends it: its contribution depends
    on |z| (an A2 locality failure the model flags rather than predicts).
    """
    return any(s.PointerToRawData + s.SizeOfRawData > len(pe.__data__) for s in pe.sections)


def append_payload(seed: int, size: int) -> bytes:
    """A deterministic attacker payload: one non-printable guard byte, then `size` pseudo-random bytes.

    Args:
        seed: RNG seed.
        size: Number of random bytes after the guard byte.

    Returns:
        The bytes to append (length size + 1).
    """
    rng = np.random.default_rng(seed)
    return b"\x00" + rng.integers(0, 256, size=size, dtype=np.uint8).tobytes()


def _printable(b: int) -> bool:
    return 0x20 <= b <= 0x7f


def _empty_strings_raw() -> dict[str, Any]:
    return {"numstrings": 0, "avlength": 0.0, "printabledist": [0] * 96, "printables": 0, "entropy": 0.0,
            "string_counts": {}}


def _apply_string_delta(s: dict[str, Any], old: dict[str, Any], new: dict[str, Any]) -> None:
    """Apply the additive string-contribution change (new - old) to the file's string raw features, in place.

    The string aggregates are sums over strings (numstrings, the printable distribution, printables, per-regex
    counts); avlength and entropy are readouts recomputed from them. `old`/`new` are the string raw features of the
    affected local region before and after the edit, with no string crossing the region boundary.
    """
    total = s["avlength"] * s["numstrings"] + new["avlength"] * new["numstrings"] - old["avlength"] * old["numstrings"]
    s["numstrings"] += new["numstrings"] - old["numstrings"]
    s["printables"] += new["printables"] - old["printables"]
    s["printabledist"] = (np.asarray(s["printabledist"]) + np.asarray(new["printabledist"])
                          - np.asarray(old["printabledist"])).tolist()
    s["avlength"] = total / s["numstrings"] if s["numstrings"] else 0.0
    dist = np.asarray(s["printabledist"], dtype=np.float64)
    p = dist[dist > 0] / dist.sum() if dist.sum() > 0 else np.zeros(0)
    s["entropy"] = float(-(p * np.log2(p)).sum())
    merged: dict[str, int] = dict(s["string_counts"])
    for k, v in new["string_counts"].items():
        merged[k] = merged.get(k, 0) + v
    for k, v in old["string_counts"].items():
        merged[k] = merged.get(k, 0) - v
    s["string_counts"] = {k: merged[k] for k in sorted(merged) if merged[k] != 0}


def _raw_copy(extractor: PEFeatureExtractor, z: bytes, pe: pefile.PE) -> dict[str, Any]:
    raw: dict[str, Any] = {fe.name: fe.raw_features(z, pe) for fe in extractor.features}
    return {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in raw.items()}


def predict_append(extractor: PEFeatureExtractor, z: bytes, appended: bytes) -> np.ndarray:
    """C1's prediction of phi(z + appended) from z alone (never extracting z').

    Args:
        extractor: The EMBER extractor.
        z: The original file bytes.
        appended: The bytes to append (a non-printable guard byte first).

    Returns:
        The predicted feature vector. Raises RuntimeError if z's windowing regime would change (too small a file).
    """
    return np.asarray(extractor.process_raw_features(_append_raw(extractor, z, appended)))  # type: ignore[no-untyped-call]


def _append_raw(extractor: PEFeatureExtractor, z: bytes, appended: bytes) -> dict[str, Any]:
    """The raw-feature dict of `predict_append` before the readout, so the sums predictor can add its body groups."""
    pe = pefile.PE(data=z)
    raw = _raw_copy(extractor, z, pe)
    d = len(appended)
    old_len = len(z)
    new_len = old_len + d
    window, step = 2048, 1024
    if old_len < window or new_len < window:
        raise RuntimeError("file smaller than the byte-entropy window; windowing regime changes")

    # histogram: counts over the whole file gain the appended bytes.
    counts = np.asarray(raw["histogram"], dtype=np.int64)
    counts = counts + np.bincount(np.frombuffer(appended, dtype=np.uint8), minlength=256)
    raw["histogram"] = counts.tolist()

    # general: size grows; entropy is the entropy of the new byte distribution.
    raw["general"]["size"] = new_len
    probs = counts[counts > 0] / new_len
    raw["general"]["entropy"] = float(-(probs * np.log2(probs)).sum())

    # byteentropy: the existing windows are unchanged; add the windows that now fit past the old last window.
    be = np.asarray(raw["byteentropy"], dtype=np.int64).reshape(16, 16)
    old_last = ((old_len - window) // step) * step
    new_last = ((new_len - window) // step) * step
    if new_last > old_last:
        first_new = old_last + step
        tail = np.frombuffer(z[first_new:] + appended, dtype=np.uint8)
        for s in range(0, new_last - first_new + 1, step):
            block = tail[s:s + window]
            hbin, c = extractor.features[2]._entropy_bin_counts(block)  # type: ignore[attr-defined]  # real EMBER routine
            be[hbin, :] += c
    raw["byteentropy"] = be.flatten().tolist()

    # strings: the appended block's own strings add to the counts (no boundary merge: guard byte is non-printable).
    add = _STRINGS.raw_features(appended, None)  # type: ignore[no-untyped-call]
    _apply_string_delta(raw["strings"], _empty_strings_raw(), add)

    # section: SizeOfRawData is unchanged, so each size_ratio scales by old_len/new_len; the overlay grows.
    sec = raw["section"]
    if sec:
        scale = old_len / new_len
        for entry in sec["sections"]:
            entry["size_ratio"] *= scale
        # The overlay starts where the last section's raw data ends; appending extends it (or creates it when z had
        # none, in which case z ends at that offset, i.e. old_len). The offset does not move under an append.
        start = pe.get_overlay_data_start_offset()
        if start is None:
            start = old_len
        overlay_bytes = z[start:] + appended
        sec["overlay"] = {"size": len(overlay_bytes), "size_ratio": len(overlay_bytes) / new_len,
                          "entropy": _byte_entropy(overlay_bytes)}

    return raw


def predict_content_overwrite(extractor: PEFeatureExtractor, z: bytes, lo: int, hi: int, c: bytes) -> np.ndarray:
    """C1's prediction of phi(z') for an in-place overwrite of z[lo:hi] with c (same length), from z alone.

    A content edit touches no locating element and changes the file length by zero, so the parse is unchanged: only
    the byte items in [lo, hi) (histogram, byte-entropy windows overlapping the region, the string distribution) and
    the general entropy and start bytes move. Section/header/import/... groups are untouched.

    Args:
        extractor: The EMBER extractor.
        z: The original file bytes.
        lo, hi: The overwritten half-open byte range (must touch no locating element; the caller guarantees it).
        c: The replacement bytes, with len(c) == hi - lo.

    Returns:
        The predicted feature vector.
    """
    if len(c) != hi - lo:
        raise ValueError(f"content overwrite must preserve length: |c|={len(c)} != {hi - lo}")
    pe = pefile.PE(data=z)
    raw = _raw_copy(extractor, z, pe)
    old_len = len(z)
    window, step = 2048, 1024
    zp = z[:lo] + c + z[hi:]  # the edited bytes; only local slices are read (never re-extracted)

    # histogram: the overwritten bytes leave their old bins and enter their new ones.
    counts = np.asarray(raw["histogram"], dtype=np.int64)
    counts += np.bincount(np.frombuffer(c, dtype=np.uint8), minlength=256)
    counts -= np.bincount(np.frombuffer(z[lo:hi], dtype=np.uint8), minlength=256)
    raw["histogram"] = counts.tolist()

    # general: size unchanged; entropy from the new byte distribution; any of the first four bytes that were edited.
    probs = counts[counts > 0] / old_len
    raw["general"]["entropy"] = float(-(probs * np.log2(probs)).sum())
    for i in range(min(4, old_len)):
        if lo <= i < hi:
            raw["general"]["start_bytes"][i] = int(c[i - lo])

    # byteentropy: recompute only the windows that overlap [lo, hi).
    be = np.asarray(raw["byteentropy"], dtype=np.int64).reshape(16, 16)
    if old_len < window:
        hbin, cnt = extractor.features[2]._entropy_bin_counts(np.frombuffer(zp, dtype=np.uint8))  # type: ignore[attr-defined]
        be = np.zeros((16, 16), dtype=np.int64)
        be[hbin, :] += cnt
    else:
        for s in range(0, old_len - window + 1, step):
            if s < hi and s + window > lo:
                ho, co = extractor.features[2]._entropy_bin_counts(np.frombuffer(z[s:s + window], dtype=np.uint8))  # type: ignore[attr-defined]
                hn, cn = extractor.features[2]._entropy_bin_counts(np.frombuffer(zp[s:s + window], dtype=np.uint8))  # type: ignore[attr-defined]
                be[ho, :] -= co
                be[hn, :] += cn
    raw["byteentropy"] = be.flatten().tolist()

    # strings: recompute over the maximal printable run around [lo, hi) (A3's margin), diff against z.
    a = lo
    while a > 0 and _printable(z[a - 1]):
        a -= 1
    b = hi
    while b < old_len and _printable(z[b]):
        b += 1
    old_s = _STRINGS.raw_features(z[a:b], None)  # type: ignore[no-untyped-call]
    new_s = _STRINGS.raw_features(zp[a:b], None)  # type: ignore[no-untyped-call]
    _apply_string_delta(raw["strings"], old_s, new_s)

    # header: EMBER reads the DOS-header fields; recompute each uint16 member overwritten by the edit from its fixed
    # offset. (A content edit in the COFF/optional header would likewise need those fields' offsets; this edit is
    # confined to the DOS header, so only its members move.)
    if raw["header"]:
        for member, off in _DOS_OFFSETS.items():
            if lo <= off and off + 2 <= hi:
                raw["header"]["dos"][member] = int.from_bytes(zp[off:off + 2], "little")

    return np.asarray(extractor.process_raw_features(raw))  # type: ignore[no-untyped-call]


def predict_add_section(extractor: PEFeatureExtractor, z: bytes, name: str, content: bytes, props: list[str]) -> np.ndarray:
    """C1's prediction of phi(z') for a declared 'add a section (name, content, props)' edit, from z alone.

    This is a *declared structural* edit (docs/feature-provenance-model.md S3): the transformation states the item it
    adds. C1 predicts the delta that item declares -- a new section item, +1 to the section counts and the COFF
    NumberOfSections, and the section content's byte contributions (histogram, strings), treated as added at the end.
    What the declaration does NOT fix is the tool's file layout: the section-table entry bytes, alignment padding, the
    exact file length, SizeOfImage, and any data-directory relocation. Those are A4 (tool side effects), so this
    predictor leaves them at z's values and the Table A0 report attributes the resulting mismatches to A4.

    Args:
        extractor: The EMBER extractor.
        z: The original file bytes.
        name: The added section's name (<= 8 chars).
        content: The added section's raw content (the bytes whose histogram/strings we can predict).
        props: The section's characteristic names (e.g. ["MEM_READ", "MEM_WRITE", "CNT_INITIALIZED_DATA"]).

    Returns:
        The predicted feature vector for the declared delta.
    """
    return np.asarray(extractor.process_raw_features(_add_section_raw(extractor, z, name, content, props)))  # type: ignore[no-untyped-call]


def _add_section_raw(extractor: PEFeatureExtractor, z: bytes, name: str, content: bytes, props: list[str]) -> dict[str, Any]:
    """The raw-feature dict of `predict_add_section` before the readout (for the sums predictor's body groups)."""
    pe = pefile.PE(data=z)
    raw = _raw_copy(extractor, z, pe)
    old_len = len(z)
    new_len = old_len + len(content)  # declared length; the tool's alignment makes the true length A4
    window, step = 2048, 1024

    # histogram: the section content's bytes are counted wherever they sit (position-independent).
    counts = np.asarray(raw["histogram"], dtype=np.int64) + np.bincount(np.frombuffer(content, dtype=np.uint8), minlength=256)
    raw["histogram"] = counts.tolist()

    # general: declared size and the entropy of the new byte distribution (size itself is approximate: A4 alignment).
    raw["general"]["size"] = new_len
    probs = counts[counts > 0] / new_len
    raw["general"]["entropy"] = float(-(probs * np.log2(probs)).sum())

    # byteentropy: windows over the content as if appended at the old end (the tool's real offset/padding is A4).
    be = np.asarray(raw["byteentropy"], dtype=np.int64).reshape(16, 16)
    old_last = ((old_len - window) // step) * step
    new_last = ((new_len - window) // step) * step
    if old_len >= window and new_last > old_last:
        tail = np.frombuffer(z[old_last + step:] + content, dtype=np.uint8)
        for s in range(0, new_last - (old_last + step) + 1, step):
            hbin, c = extractor.features[2]._entropy_bin_counts(tail[s:s + window])  # type: ignore[attr-defined]
            be[hbin, :] += c
    raw["byteentropy"] = be.flatten().tolist()

    # strings: the content's own strings (no boundary merge assumed; the tool pads around the section).
    _apply_string_delta(raw["strings"], _empty_strings_raw(), _STRINGS.raw_features(content, None))  # type: ignore[no-untyped-call]

    # section: a new section item is declared; its size_ratio and all others use the declared new length.
    sec = raw["section"]
    if sec:
        for entry in sec["sections"]:
            entry["size_ratio"] *= old_len / new_len
        sec["sections"].append({
            "name": name.strip("\x00").lower(), "size": len(content), "entropy": _byte_entropy(content),
            "vsize": len(content), "size_ratio": len(content) / new_len,
            "vsize_ratio": len(content) / max(len(content), 1), "props": list(props),
        })
        if sec["overlay"]["size"]:  # the overlay keeps its bytes; only its ratio denominator grows
            sec["overlay"]["size_ratio"] = sec["overlay"]["size"] / new_len

    # header: the COFF section count rises by one (SizeOfImage is the tool's to set: A4).
    if raw["header"]:
        raw["header"]["coff"]["number_of_sections"] += 1

    return raw


################################################################################
# Sums-space predictors (the four re-encoded groups on top of the thrember raw dict)
################################################################################

_BE = BodyByteEntropyHistogram()
_BODY_STRINGS = BodyStrings()


def _body_string_delta(raw_bs: dict[str, Any], block: bytes) -> None:
    """Add the strings of `block` (a new body region or an overlay extension; no boundary merge) to body_strings."""
    # The thrember string routine on the block's own bytes (a new body region / overlay extension).
    add = _BODY_STRINGS._strings.raw_features(block, None)  # type: ignore[no-untyped-call]
    raw_bs["numstrings"] += add["numstrings"]
    raw_bs["printables"] += add["printables"]
    raw_bs["printabledist"] = (np.asarray(raw_bs["printabledist"]) + np.asarray(add["printabledist"])).tolist()
    merged: dict[str, int] = dict(raw_bs["string_counts"])
    for k, v in add["string_counts"].items():
        merged[k] = merged.get(k, 0) + v
    raw_bs["string_counts"] = merged


def _body_windows(block: bytes) -> np.ndarray:
    """The 16x16 byte/entropy counts over the full windows tiled from the start of `block` (BodyByteEntropy's rule)."""
    out = np.zeros((16, 16), dtype=np.int64)
    a = np.frombuffer(block, dtype=np.uint8)
    w, step = _BE._windows.window, _BE._windows.step
    for s in range(0, a.shape[0] - w + 1, step):
        hbin, c = _BE._windows._entropy_bin_counts(a[s:s + w])  # type: ignore[no-untyped-call]
        out[hbin, :] += c
    return out


def predict_append_sums(extractor: SumsFeatureExtractor, z: bytes, appended: bytes) -> np.ndarray:
    """C1's prediction of the sums feature vector after an overlay append, from z alone (the body groups are up-only).

    The appended bytes extend the overlay body region; the existing body regions and the section buckets are
    unchanged. Needs a clean file (no section whose declared raw data overruns the file); the caller guarantees it
    with `has_overrun_section`, as for the thrember append.
    """
    raw = _append_raw(extractor, z, appended)
    pe = pefile.PE(data=z)
    old_len = len(z)

    # body_histogram: the appended bytes are counted in the (extended) overlay region.
    counts = np.asarray(raw["body_histogram"], dtype=np.int64) + np.bincount(np.frombuffer(appended, dtype=np.uint8), minlength=256)
    raw["body_histogram"] = counts.tolist()

    # body_byteentropy: the overlay region grows from [start, old_len) to [start, old_len + |appended|); add the
    # windows that now fit past the old region end. The overlay starts where the sections' raw data ends (or at
    # old_len if z had no overlay, in which case the appended bytes are the whole new region).
    regions = body_regions(z, pe)
    ov_start = regions[-1][0] if regions and regions[-1][1] == old_len else old_len
    w, step = _BE._windows.window, _BE._windows.step
    old_last = ((old_len - ov_start - w) // step) * step if old_len - ov_start >= w else -step
    tail = z[ov_start + old_last + step:] + appended if old_last >= 0 else z[ov_start:] + appended
    be = np.asarray(raw["body_byteentropy"], dtype=np.int64).reshape(16, 16) + _body_windows(tail)
    # Subtract any windows of `tail` that were already counted (the overlap region before the append), i.e. windows
    # lying entirely in [ov_start + old_last + step, old_len). None do when we start past the last old window.
    raw["body_byteentropy"] = be.flatten().tolist()

    # body_strings: the appended block's own strings (the guard byte breaks any run at the old overlay's end).
    _body_string_delta(raw["body_strings"], appended)
    return np.asarray(extractor.process_raw_features(raw))  # type: ignore[no-untyped-call]


def predict_add_section_sums(extractor: SumsFeatureExtractor, z: bytes, name: str, content: bytes, props: list[str]) -> np.ndarray:
    """C1's prediction of the sums feature vector after a declared add-section, from z alone (body groups up-only).

    The section's content is a new body region (histogram, byte-entropy windows, strings add); the section's declared
    size/vsize/entropy and characteristics add into their name-keyed signed buckets' positive or negative parts. The
    tool's layout (padding, where the region actually lands) is A4, as in `predict_add_section`.
    """
    raw = _add_section_raw(extractor, z, name, content, props)

    counts = np.asarray(raw["body_histogram"], dtype=np.int64) + np.bincount(np.frombuffer(content, dtype=np.uint8), minlength=256)
    raw["body_histogram"] = counts.tolist()
    be = np.asarray(raw["body_byteentropy"], dtype=np.int64).reshape(16, 16) + _body_windows(content)
    raw["body_byteentropy"] = be.flatten().tolist()
    _body_string_delta(raw["body_strings"], content)

    # section_split: append the declared section so process_raw_features hashes it into the pos/neg bucket parts.
    sec = raw["section_split"]
    if sec:
        sec["sections"].append({"name": name.strip("\x00").lower(), "size": len(content),
                                "vsize": len(content), "entropy": _byte_entropy(content), "props": list(props)})
    return np.asarray(extractor.process_raw_features(raw))  # type: ignore[no-untyped-call]


def edit_add_section(z: bytes, seed: int) -> tuple[bytes, dict[str, Any]]:
    """Add a readable/writable section with random content via LIEF (secml/GAMMA-style), the declared delta known."""
    import lief

    lief.logging.disable()
    content = np.random.default_rng(seed).integers(0, 256, size=4096, dtype=np.uint8).tobytes()
    name, props = ".pv0", ["MEM_READ", "MEM_WRITE", "CNT_INITIALIZED_DATA"]
    pe = lief.PE.parse(list(z))
    if pe is None:
        raise RuntimeError("LIEF could not parse the file")
    s = lief.PE.Section(name)
    s.content = list(content)
    s.characteristics = (lief.PE.Section.CHARACTERISTICS.MEM_READ.value
                         | lief.PE.Section.CHARACTERISTICS.MEM_WRITE.value
                         | lief.PE.Section.CHARACTERISTICS.CNT_INITIALIZED_DATA.value)
    pe.add_section(s)
    zp = bytes(pe.write_to_bytes())
    return zp, {"name": name, "content": content, "props": props}


def edit_append(z: bytes, seed: int, append_size: int) -> tuple[bytes, dict[str, Any]]:
    """Overlay append: a non-printable guard byte then `append_size` random bytes (secml/GAMMA padding)."""
    appended = append_payload(seed, append_size)
    return z + appended, {"appended": appended}


def edit_dos_overwrite(z: bytes, seed: int) -> tuple[bytes, dict[str, Any]]:
    """In-place overwrite of the DOS header fields, bytes [2, 60) (secml partial DOS): loader-ignored, no parse change.

    Leaves e_magic ('MZ', [0, 2)) and e_lfanew ([60, 64)) intact, so the PE header is still located.
    """
    if len(z) < 64 or z[:2] != b"MZ":
        raise RuntimeError("not an MZ/PE file; DOS overwrite does not apply")
    c = np.random.default_rng(seed).integers(0, 256, size=58, dtype=np.uint8).tobytes()
    return z[:2] + c + z[60:], {"lo": 2, "hi": 60, "c": c}


################################################################################
# The C1 engine's columns (check G4)
################################################################################

_ENGINE_EMPTY: dict[str, Any] = {
    "engine_flagged": False, "engine_reason": "", "engine_exact": False, "engine_bit_exact": False,
    "engine_num_mismatch": -1, "engine_max_rel_err": float("nan"), "engine_vs_hand_max_rel": float("nan"),
    "engine_hand_bit_equal": False, "engine_groups_missed": [], "engine_seconds": float("nan"),
}


def _engine_columns(engine: Any, table: ItemTable, z: bytes, kw: dict[str, Any], actual: np.ndarray, hand: np.ndarray,
                    modeled: np.ndarray, tol: float, readouts: list[Readout], group: list[str]) -> dict[str, Any]:
    """The engine's prediction for one pair, compared with re-extraction and with the hand predictor."""
    start = time.time()
    p: Prediction = engine(table, z, kw)
    seconds = time.time() - start
    if p.table is None:
        return {**_ENGINE_EMPTY, "engine_flagged": True, "engine_reason": p.reason, "engine_seconds": seconds}
    y = p.features(readouts)
    err = np.abs(y - actual) / np.maximum(np.abs(actual), 1.0)
    bad = np.where((err > tol) & modeled)[0]
    vs_hand = np.abs(y - hand) / np.maximum(np.abs(hand), 1.0)
    return {
        "engine_flagged": False,
        "engine_reason": "",
        "engine_exact": len(bad) == 0,
        "engine_bit_exact": bool(np.all((y == actual)[modeled])),
        "engine_num_mismatch": int(len(bad)),
        "engine_max_rel_err": float(err[modeled].max()),
        "engine_vs_hand_max_rel": float(vs_hand[modeled].max()),
        "engine_hand_bit_equal": bool(np.all((y == hand)[modeled])),
        "engine_groups_missed": sorted({group[j] for j in bad}),
        "engine_seconds": seconds,
    }


def _engine_report(ok: pl.DataFrame) -> dict[str, Any]:
    """Per transformation: flags, exactness against re-extraction, and agreement with the hand predictor."""
    predicted = ok.filter(~pl.col("engine_flagged"))
    groups = Counter(g for gs in predicted["engine_groups_missed"].to_list() for g in gs)
    return {
        "flagged_pairs": int(ok["engine_flagged"].sum()),
        "flagged_where_hand_flag": int((ok["engine_flagged"] & ~ok["assumptions_hold"]).sum()),
        "flagged_where_hand_clean": int((ok["engine_flagged"] & ok["assumptions_hold"]).sum()),
        "flag_reasons": dict(Counter(ok.filter(pl.col("engine_flagged"))["engine_reason"].to_list()).most_common(5)),
        "predicted_pairs": predicted.height,
        "exact_tol": int(predicted["engine_exact"].sum()),
        "bit_exact": int(predicted["engine_bit_exact"].sum()),
        "pairs_with_group_missed": dict(groups),
        "max_rel_err_vs_hand": float(predicted["engine_vs_hand_max_rel"].max() or 0.0) if predicted.height else 0.0,  # type: ignore[arg-type]
        "bit_equal_to_hand": int(predicted["engine_hand_bit_equal"].sum()),
        "seconds_engine_median": float(predicted["engine_seconds"].median() or 0.0) if predicted.height else 0.0,  # type: ignore[arg-type]
    }


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_files", type=int, default=None)
    parser.add_argument("--append_size", type=int, default=4096)
    parser.add_argument("--tol", type=float, default=1e-4, help="Relative tolerance for a feature to count as matching.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    extractor = PEFeatureExtractor()
    readouts = extractor.readouts
    names = extractor.feature_names
    group = [n.split(":", 1)[0] for n in names]
    # pefilewarnings has no items (docs/feature-provenance-model.md S7): it is outside the model, so it is excluded
    # from the exact-match test and its change is reported separately.
    modeled = np.array([g != "pefilewarnings" for g in group])

    df = pl.read_parquet(args.pilot_files).select("name", "label")
    if args.num_files is not None:
        df = df.head(args.num_files)
    reader = SimpleDBReader(SimpleDB(args.db, check=False))

    # Each transformation names the edit (Section 6 row), how C1 predicts it, and the assumption whose failure takes a
    # file out of the clean set (reported separately, not counted against C1).
    transforms: list[dict[str, Any]] = [
        {"name": "append", "note": "overlay append, guard byte + random payload (Section 6 row 1; item-creating)",
         "edit": lambda z: edit_append(z, args.seed, args.append_size),
         "predict": lambda z, kw: predict_append(extractor, z, kw["appended"]),
         "engine": lambda t, z, kw: predict(t, z, ByteEdit(len(z), len(z), kw["appended"]), extractor.recognizers),
         "clean": lambda pe: not has_overrun_section(pe),
         "flag": "A2: a section's declared raw size overruns the file"},
        {"name": "dos_overwrite", "note": "in-place DOS-header overwrite, bytes [2,60) (Section 6 row 3; content)",
         "edit": lambda z: edit_dos_overwrite(z, args.seed),
         "predict": lambda z, kw: predict_content_overwrite(extractor, z, kw["lo"], kw["hi"], kw["c"]),
         "engine": lambda t, z, kw: predict(t, z, ByteEdit(kw["lo"], kw["hi"], kw["c"]), extractor.recognizers),
         "clean": lambda pe: True,
         "flag": None},
        {"name": "add_section", "note": "LIEF add R/W section, 4 KB random (Section 6 row 11; declared structural)",
         "edit": lambda z: edit_add_section(z, args.seed),
         "predict": lambda z, kw: predict_add_section(extractor, z, kw["name"], kw["content"], kw["props"]),
         "engine": lambda t, z, kw: add_section(extractor, t, z, kw["name"], kw["content"], kw["props"]),
         "clean": lambda pe: True,
         "flag": "A4: the tool's file layout (table entry, alignment, SizeOfImage, directory moves) is not declared"},
    ]

    rows: list[dict[str, Any]] = []
    mism: list[dict[str, Any]] = []
    for r in df.iter_rows(named=True):
        z = bytes(reader.get(r["name"]).data)
        table = extractor.item_table(z)
        for tf in transforms:
            start = time.time()
            try:
                clean = bool(tf["clean"](pefile.PE(data=z)))
                zp, kw = tf["edit"](z)
                predicted = tf["predict"](z, kw)
                actual = np.asarray(extractor.feature_vector(zp))  # type: ignore[no-untyped-call]
                denom = np.maximum(np.abs(actual), 1.0)
                err = np.abs(predicted - actual) / denom
                bad = np.where((err > args.tol) & modeled)[0]
                warn_changed = bool(((err > args.tol) & ~modeled).any())
                engine = _engine_columns(tf["engine"], table, z, kw, actual, predicted, modeled, args.tol, readouts, group)
                rows.append({"name": r["name"], "transformation": tf["name"], "exact": len(bad) == 0,
                             "num_mismatch": int(len(bad)), "max_rel_err": float(err[modeled].max()),
                             "assumptions_hold": clean, "pefilewarnings_changed": warn_changed,
                             "seconds": time.time() - start, **engine})
                for j in bad:
                    mism.append({"name": r["name"], "transformation": tf["name"], "feature": names[j],
                                 "group": group[j], "predicted": float(predicted[j]), "actual": float(actual[j])})
            except Exception as e:
                rows.append({"name": r["name"], "transformation": tf["name"], "exact": False, "num_mismatch": -1,
                             "max_rel_err": float("nan"), "assumptions_hold": False,
                             "pefilewarnings_changed": False, "seconds": time.time() - start, **_ENGINE_EMPTY})
                print(f"  SKIP {tf['name']} {r['name'][:12]}: {type(e).__name__}: {str(e)[:120]}", flush=True)

    rdf = pl.DataFrame(rows)
    pl.DataFrame(mism).write_parquet(args.outdir / "mismatches.parquet")
    rdf.write_parquet(args.outdir / "table0.parquet")

    report: dict[str, Any] = {"tol": args.tol, "append_size": args.append_size, "by_transformation": {}}
    for tf in transforms:
        t = rdf.filter(pl.col("transformation") == tf["name"])
        ok = t.filter(pl.col("num_mismatch") >= 0)
        clean = ok.filter(pl.col("assumptions_hold"))
        flagged = ok.filter(~pl.col("assumptions_hold"))
        tm = [m for m in mism if m["transformation"] == tf["name"]]
        tm_clean = [m for m in tm if m["name"] in set(clean["name"].to_list())]
        # Per modeled group, the number of predicted pairs on which C1 matches every feature of that group. For a
        # declared-structural edit this separates the declaration-determined groups (predicted) from the A4 residual.
        groups = sorted({g for g in group if g != "pefilewarnings"})
        files_with_grp_miss = {g: {m["name"] for m in tm if m["group"] == g} for g in groups}
        group_fully_predicted = {g: ok.height - len(files_with_grp_miss[g]) for g in groups}
        report["by_transformation"][tf["name"]] = {
            "note": tf["note"],
            "flag": tf["flag"],
            "pairs": t.height,
            "predicted_ok": ok.height,
            "assumptions_hold_pairs": clean.height,
            "exact_where_assumptions_hold": int(clean["exact"].sum()),
            "exact_frac_where_assumptions_hold": float(clean["exact"].mean()) if clean.height else 0.0,  # type: ignore[arg-type]
            "flagged_pairs": flagged.height,
            "flagged_still_exact": int(flagged["exact"].sum()) if flagged.height else 0,
            "pefilewarnings_changed": int(t["pefilewarnings_changed"].sum()),
            "group_fully_predicted_pairs": group_fully_predicted,
            "mismatch_by_group_clean": dict(Counter(m["group"] for m in tm_clean)),
            "mismatch_by_feature_top": dict(Counter(m["feature"] for m in tm).most_common(15)),
            "engine": _engine_report(ok),
        }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
