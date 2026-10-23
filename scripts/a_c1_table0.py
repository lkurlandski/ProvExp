"""
Direction A, go/no-go check 1 (docs/direction-A-mock.md, Table A0): does C1 predict the edited file's features from
the item table of the original, without extracting the edited file?

C1 (docs/feature-provenance-model.md): for an edit that adds, removes, modifies, or moves a known set of items,
phi(z') = g(A(z) + sum of the touched items' contribution changes). We test it as the mock specifies: apply a
transformation to a pilot file, predict phi(z') with C1 from z alone, re-extract z', and compare feature by feature.
A pair "holds" if the prediction matches re-extraction within tolerance on every feature; mismatches are attributed
to the model's assumptions A1-A4.

This is not an attack: the only edit implemented here is appending attacker-chosen bytes at the end of the file (the
overlay-append transformation, Section 6 row 1 -- secml/GAMMA padding), the cleanest item-creating edit and the one
that exercises every readout kind through the file-size denominator. The appended block is prefixed with one
non-printable guard byte so no string straddles the old/new boundary (A3's margin, taken as a one-byte catalogue
restriction, docs C3 step 2); the predictor otherwise handles the appended block's own strings exactly.

Groups the predictor updates (all others are copied from z, unchanged by a pure overlay append):
    histogram    counts += bincount(appended); readout renormalizes every bin
    general      size += d; entropy recomputed from the new byte counts
    byteentropy  the windows that now fit past the old last window, read from (old tail + appended)
    strings      the appended block's own strings add to the counts; avlength and entropy follow from the readout
    section      every section's size_ratio scales by old_len/new_len; the overlay grows (size, ratio, entropy);
                 max/min entropy and size_ratio follow

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

__all__ = ["append_payload", "predict_append"]

ROOT = Path(__file__).resolve().parent.parent
_STRINGS = StringExtractor()  # type: ignore[no-untyped-call]


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


def predict_append(extractor: PEFeatureExtractor, z: bytes, appended: bytes) -> np.ndarray:
    """C1's prediction of phi(z + appended) from z alone (never extracting z').

    Args:
        extractor: The EMBER extractor.
        z: The original file bytes.
        appended: The bytes to append (a non-printable guard byte first).

    Returns:
        The predicted feature vector. Raises RuntimeError if z's windowing regime would change (too small a file).
    """
    pe = pefile.PE(data=z)
    raw: dict[str, Any] = {fe.name: fe.raw_features(z, pe) for fe in extractor.features}
    raw = {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in raw.items()}
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
    s = raw["strings"]
    total_len_old = s["avlength"] * s["numstrings"]
    total_len_add = add["avlength"] * add["numstrings"]
    s["numstrings"] += add["numstrings"]
    s["printables"] += add["printables"]
    s["printabledist"] = (np.asarray(s["printabledist"]) + np.asarray(add["printabledist"])).tolist()
    s["avlength"] = (total_len_old + total_len_add) / s["numstrings"] if s["numstrings"] else 0
    dist = np.asarray(s["printabledist"], dtype=np.float64)
    p = dist[dist > 0] / dist.sum() if dist.sum() > 0 else np.zeros(0)
    s["entropy"] = float(-(p * np.log2(p)).sum())
    merged = dict(s["string_counts"])
    for k, v in add["string_counts"].items():
        merged[k] = merged.get(k, 0) + v
    s["string_counts"] = {k: merged[k] for k in sorted(merged)}

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

    return np.asarray(extractor.process_raw_features(raw))  # type: ignore[no-untyped-call]


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
    names = extractor.feature_names
    group = [n.split(":", 1)[0] for n in names]
    # pefilewarnings has no items (docs/feature-provenance-model.md S7): it is outside the model, so it is excluded
    # from the exact-match test and its change is reported separately.
    modeled = np.array([g != "pefilewarnings" for g in group])

    df = pl.read_parquet(args.pilot_files).select("name", "label")
    if args.num_files is not None:
        df = df.head(args.num_files)
    reader = SimpleDBReader(SimpleDB(args.db, check=False))

    rows: list[dict[str, Any]] = []
    mism: list[dict[str, Any]] = []
    for r in df.iter_rows(named=True):
        z = bytes(reader.get(r["name"]).data)
        appended = append_payload(args.seed, args.append_size)
        start = time.time()
        try:
            overrun = has_overrun_section(pefile.PE(data=z))
            predicted = predict_append(extractor, z, appended)
            actual = np.asarray(extractor.feature_vector(z + appended))  # type: ignore[no-untyped-call]
            denom = np.maximum(np.abs(actual), 1.0)
            err = np.abs(predicted - actual) / denom
            bad = np.where((err > args.tol) & modeled)[0]
            warn_changed = bool(((err > args.tol) & ~modeled).any())
            rows.append({"name": r["name"], "transformation": "append", "exact": len(bad) == 0,
                         "num_mismatch": int(len(bad)), "max_rel_err": float(err[modeled].max()),
                         "overrun_section": overrun, "pefilewarnings_changed": warn_changed,
                         "seconds": time.time() - start})
            for j in bad:
                mism.append({"name": r["name"], "transformation": "append", "feature": names[j],
                             "group": group[j], "predicted": float(predicted[j]), "actual": float(actual[j])})
        except Exception as e:
            rows.append({"name": r["name"], "transformation": "append", "exact": False, "num_mismatch": -1,
                         "max_rel_err": float("nan"), "overrun_section": False,
                         "pefilewarnings_changed": False, "seconds": time.time() - start})
            print(f"  SKIP {r['name'][:12]}: {type(e).__name__}: {str(e)[:120]}", flush=True)

    rdf = pl.DataFrame(rows)
    pl.DataFrame(mism).write_parquet(args.outdir / "mismatches.parquet")
    rdf.write_parquet(args.outdir / "table0.parquet")
    ok = rdf.filter(pl.col("num_mismatch") >= 0)
    # A2-clean files: no section's raw data overruns the file (so no section contribution depends on |z|). This is
    # the set where C1 as stated applies; overrun files are reported separately and attributed to A2.
    clean = ok.filter(~pl.col("overrun_section"))
    overrun = ok.filter(pl.col("overrun_section"))
    mism_clean = [m for m in mism if m["name"] in set(clean["name"].to_list())]
    report = {
        "transformation": "append (overlay, guard byte + random payload)",
        "append_size": args.append_size,
        "tol": args.tol,
        "pairs": rdf.height,
        "predicted_ok": ok.height,
        "a2_clean_pairs": clean.height,
        "a2_clean_exact": int(clean["exact"].sum()),
        "a2_clean_exact_frac": float(clean["exact"].mean()) if clean.height else 0.0,  # type: ignore[arg-type]
        "overrun_pairs_A2_flagged": overrun.height,
        "overrun_exact": int(overrun["exact"].sum()),
        "pefilewarnings_changed": int(rdf["pefilewarnings_changed"].sum()),
        "mismatch_by_group_a2_clean": dict(Counter(m["group"] for m in mism_clean)),
        "mismatch_by_feature_top_a2_clean": dict(Counter(m["feature"] for m in mism_clean).most_common(15)),
        "mismatch_by_group_all": dict(Counter(m["group"] for m in mism)),
    }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
