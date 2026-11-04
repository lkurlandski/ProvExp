"""
The adaptive cell and the M_full hole witnesses for the expert-set row (item 11; docs/direction-A-expert-set.md).

FOR ACADEMIC SECURITY RESEARCH ONLY: our own search against our own expert-set detector, on our own pilot malware, to
evaluate the defense (as runs 100 and 106).

The expert set is instrumented (provexp.featuresets.ember2024.expert), and the C4 derivation marks eleven of its forty
features as lowerable under M_full (rows 27 and 30-39 of docs/direction-A-expert-set.md): `modified_dos_stub`, lowered by
rewriting the DOS stub to the default one, and the ten section-name features, lowered by renaming a section. This script

    witnesses   for each derived hole, one of our own byte edits that lowers the feature (re-extracted), confirming the
                derived direction against the extractor;
    adaptive    a greedy search that lowers the detector's score with those two operations (rename a section, rewrite
                the DOS stub), scored by re-extracting the expert features -- the extractor is cheap, and C1 is exact,
                so re-extraction scoring gives the same scores as the prediction-scored search of the other Table 7 rows.

The search materializes edits with our own byte-level writers (loader-safe: a rename overwrites the name field, a DOS
rewrite overwrites the loader-ignored stub), so every reported evasion re-extracts by construction.
"""

from __future__ import annotations

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any
from typing import Optional

import lightgbm
import numpy as np
import pefile
import polars as pl

import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from a1_adaptive import rename_section  # noqa: E402
from a1_evaluate import calibrate_threshold  # noqa: E402
from a1_evaluate import make_extractor  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from provexp.featuresets.ember2024.expert import DEFAULT_DOS_STUB  # noqa: E402
from provexp.featuresets.ember2024.expert import DOS_HEADER_SIZE  # noqa: E402
from provexp.featuresets.ember2024.expert import SECTIONS  # noqa: E402
from provexp.featuresets.ember2024.features import PEFeatureExtractor  # noqa: E402
from provexp.data.paths import EMBER2024_DATA  # noqa: E402


__all__ = ["dos_to_default", "section_names", "candidates", "greedy_evade"]


UNKNOWN_NAME = ".adv"  # A name no watched-section family counts (moves a section out of the named features).


################################################################################
# The two hole operations, as loader-safe byte writers
################################################################################


def dos_to_default(data: bytes, pe: pefile.PE) -> Optional[bytes]:
    """
    Rewrite the DOS stub to the default one, so `modified_dos_stub` falls to 0 (the loader ignores the stub). Returns
    None when the stub region is not the default stub's length, so no rewrite can make the feature 0.
    """
    lfanew = int(pe.DOS_HEADER.e_lfanew)
    if max(lfanew, DOS_HEADER_SIZE) - DOS_HEADER_SIZE != len(DEFAULT_DOS_STUB):
        return None
    return data[:DOS_HEADER_SIZE] + DEFAULT_DOS_STUB + data[DOS_HEADER_SIZE + len(DEFAULT_DOS_STUB):]


def section_names(pe: pefile.PE) -> list[str]:
    """The section names (up to the first NUL), as the expert extractor reads them."""
    return [s.Name.split(b"\x00")[0].decode("latin-1") for s in pe.sections]


################################################################################
# The greedy adaptive search
################################################################################


def candidates(data: bytes) -> list[tuple[str, bytes]]:
    """
    The edited files to try from `data`: rewrite the DOS stub to the default, and rename each section to the unknown
    name (lowers that name's section features). Each is (op, new bytes); files our writers cannot edit are skipped.
    """
    try:
        pe = pefile.PE(data=data)
    except pefile.PEFormatError:
        return []
    out: list[tuple[str, bytes]] = []
    dos = dos_to_default(data, pe)
    if dos is not None and dos != data:
        out.append(("dos", dos))
    names = section_names(pe)
    for i, name in enumerate(names):
        if name != UNKNOWN_NAME:
            try:
                out.append(("ren", rename_section(data, i, UNKNOWN_NAME)))
            except (pefile.PEFormatError, ValueError):
                pass
    return out


def score(extractor: PEFeatureExtractor, booster: lightgbm.Booster, data: bytes) -> float:
    """The detector's malware probability for a file."""
    x = np.asarray(extractor.feature_vector(data), dtype=np.float32)  # type: ignore[no-untyped-call]
    return float(booster.predict(x[None, :])[0])


def greedy_evade(extractor: PEFeatureExtractor, booster: lightgbm.Booster, data: bytes, tau: float,
                 max_steps: int) -> dict[str, Any]:
    """
    Greedily apply the hole operations, each step taking the candidate that lowers the score most, until the score is
    at or below `tau` (evaded) or no candidate lowers it. Scores by re-extraction, so the result is the re-extracted one.
    """
    z = data
    p = score(extractor, booster, z)
    ops: list[str] = []
    queries = 0
    for _ in range(max_steps):
        if p <= tau:
            break
        best: Optional[tuple[float, str, bytes]] = None
        for op, new in candidates(z):
            queries += 1
            q = score(extractor, booster, new)
            if best is None or q < best[0]:
                best = (q, op, new)
        if best is None or best[0] >= p - 1e-12:
            break
        p, op, z = best[0], best[1], best[2]
        ops.append(op)
    return {"evaded": bool(p <= tau), "p_adv": p, "ops": ops, "queries": queries}


################################################################################
# The hole witnesses
################################################################################


def witness_holes(extractor: PEFeatureExtractor, malware: list[tuple[str, bytes]]) -> dict[str, dict[str, Any]]:
    """
    For each derived M_full hole, the first pilot file on which one of our own edits lowers the feature (re-extracted),
    confirming the derived direction. `modified_dos_stub` by the DOS rewrite; the section-name features by renaming.
    """
    names = extractor.feature_names  # the base extractor prefixes each with the group name ("expert:").
    # Per hole feature, how to lower it: rewrite the DOS stub; rename the named section away (targeting that name);
    # rename an unknown section to a known one (for the unknown-section features).
    hole: dict[int, tuple[str, Optional[str]]] = {names.index("expert:modified_dos_stub"): ("dos", None)}
    for s in SECTIONS:
        hole[names.index(f"expert:{s}_info")] = ("ren", s)
        hole[names.index(f"expert:{s}-size")] = ("ren", s)
    hole[names.index("expert:unknown_sections")] = ("ren-to-known", None)
    hole[names.index("expert:info_unknown_sections")] = ("ren-to-known", None)

    out: dict[str, dict[str, Any]] = {}
    for idx, (how, target) in hole.items():
        feat = names[idx]
        for name, data in malware:
            x0 = np.asarray(extractor.feature_vector(data), dtype=np.float32)  # type: ignore[no-untyped-call]
            if x0[idx] <= 0:
                continue
            edited = _witness_edit(data, how, target)
            if edited is None:
                continue
            x1 = np.asarray(extractor.feature_vector(edited), dtype=np.float32)  # type: ignore[no-untyped-call]
            if x1[idx] < x0[idx]:
                out[feat] = {"file": name[:16], "op": how, "before": float(x0[idx]), "after": float(x1[idx])}
                break
    return out


def _witness_edit(data: bytes, how: str, target: Optional[str]) -> Optional[bytes]:
    """The witness edit for a hole: rewrite the DOS stub, rename the `target` named section away, or rename an unknown one to known."""
    try:
        pe = pefile.PE(data=data)
    except pefile.PEFormatError:
        return None
    if how == "dos":
        return dos_to_default(data, pe)
    names = section_names(pe)
    if how == "ren":  # The named section `target` renamed away lowers its name's info and size.
        for i, name in enumerate(names):
            if name == target:
                return rename_section(data, i, UNKNOWN_NAME)
    if how == "ren-to-known":  # An unknown section renamed to a known name lowers the unknown-section features.
        for i, name in enumerate(names):
            if name not in SECTIONS:
                return rename_section(data, i, SECTIONS[0])
    return None


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True, help="The expert feature store the model was trained on.")
    parser.add_argument("--model", type=Path, required=True, help="The monotone expert model directory (model.txt, ts_predictions.parquet).")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--max_steps", type=int, default=12)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    extractor = make_extractor(args.features)
    booster = lightgbm.Booster(model_file=str(args.model / "model.txt"))
    pred = pl.read_parquet(args.model / "ts_predictions.parquet")
    tau = calibrate_threshold(pred["prob"].to_numpy(), pred["label"].to_numpy(), args.fpr)
    malware, _ = load_pilot(args.pilot_files, args.db)
    print(f"tau = {tau:.6f}; {len(malware)} pilot malware", flush=True)

    rows = []
    detected = 0
    evaded = 0
    for name, data in malware:
        p0 = score(extractor, booster, data)
        if p0 <= tau:
            continue
        detected += 1
        r = greedy_evade(extractor, booster, data, tau, args.max_steps)
        r["name"], r["p_clean"] = name, p0
        rows.append(r)
        evaded += int(r["evaded"])
    print(f"detected {detected}; evaded {evaded}/{detected}", flush=True)
    for r in rows:
        print(f"  {r['name'][:16]}  p {r['p_clean']:.4f} -> {r['p_adv']:.4f}  {'EVADED' if r['evaded'] else '-':8s} ops={r['ops']}", flush=True)

    witnesses = witness_holes(extractor, malware)
    print(f"\nHole witnesses ({len(witnesses)} of 11 found a lowering edit on the pilot malware):", flush=True)
    for feat, w in sorted(witnesses.items()):
        print(f"  {feat:24s} {w['op']:14s} {w['before']:.4g} -> {w['after']:.4g}  ({w['file']})", flush=True)

    out = {"tau": tau, "detected": detected, "evaded": evaded, "rows": rows, "witnesses": witnesses}
    (args.outdir / "expert_adaptive.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote {args.outdir / 'expert_adaptive.json'}", flush=True)


if __name__ == "__main__":
    main()
