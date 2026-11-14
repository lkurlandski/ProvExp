"""
Direction A, go/no-go check 1 (docs/archive/direction-A/direction-A-mock.md, Table A0): does C1 predict the edited file's features from
the item table of the original, without extracting the edited file?

C1 (docs/archive/framework/feature-provenance-model.md): for an edit that adds, removes, modifies, or moves a known set of items,
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

The C1 engine (provexp.reach, derivation step 5; docs/evidence/item-layer-design.md, check G4) predicts the same pairs from
the instrumented extractor's item table: append and dos_overwrite as byte edits (the engine itself flags writes to
locating ranges, e.g. an append that reaches a section running past the end of the file), add_section through the
catalogue's declaration. Its columns (`engine_*`) compare it with re-extraction and with the hand predictors.

Outputs, in `{outdir}/`:
    table0.parquet   one row per (file, transformation): exact match, num mismatching features, max abs error, timing
    mismatches.parquet   one row per (file, transformation, feature) that mismatched: predicted, actual, group
    report.json      per transformation: pairs, % exact, mismatching-feature counts by group and feature

Usage (smoke on five files):
    PYTHONHASHSEED=0 python pipeline/1-audit/hand-table/hand_table.py --outdir artifacts/experiments/a_c1 --num_files 5
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import pefile
import polars as pl

from provexp.data.paths import EMBER2024_DATA
from provexp.data.paths import ROOT
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.catalogue import add_section
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.hand import edit_add_section
from provexp.featuresets.ember2024.hand import edit_append
from provexp.featuresets.ember2024.hand import edit_dos_overwrite
from provexp.featuresets.ember2024.hand import predict_add_section
from provexp.featuresets.ember2024.hand import predict_append
from provexp.featuresets.ember2024.hand import predict_content_overwrite
from provexp.featuresets.ember2024.population import has_overrun_section
from provexp.items import ItemTable
from provexp.items import Readout
from provexp.reach import ByteEdit
from provexp.reach import Prediction
from provexp.reach import predict

__all__: list[str] = []



################################################################################
# Sums-space predictors (the four re-encoded groups on top of the thrember raw dict)
################################################################################


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
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
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
    # pefilewarnings has no items (docs/archive/framework/feature-provenance-model.md S7): it is outside the model, so it is excluded
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
