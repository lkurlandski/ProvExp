"""
Table 7's toolkit evidence, split (review R1b, R1d): per attack, whether it is an operation of the catalogue or a LIEF
relayout, how often it evades each detector on files that pass the precondition, and whether its real outputs stay
inside the derived M_full table; per detector, how many detected pilot malware are still detected after every attack.

FOR ACADEMIC SECURITY RESEARCH ONLY: this only reads the results of published secml-malware attacks run against our own
detectors on our own pilot samples (runs 78, 105, 108).

The inputs:
    toolkit    a1_evaluate.py's results (run 105): eight attacks against the 10%-store detectors, the C4 rows routed
    adaptive   a1_adaptive.py's results (run 108): the C1-declared search against the full-store detectors (unrouted)
    deltas     a_pv_attacks.py's perturbation vectors (run 78): the eight attacks against the unconstrained GBDT,
               re-extracted with the quirk-fixed extractor
    table      the derived M_full table under the precondition, as the full-store detector consumes it
               (`*.monotone.tsv`: feature and allowed sign; `*.neutralize.txt`: dropped; every other feature is fixed)

An output respects the table when every feature it moves moves in an allowed direction: a monotone feature only with
its sign, a fixed feature not at all (the detector keeps it as an unconstrained input); a dropped feature may move
freely. A monotone detector cannot drop on such an
output, so the toolkit can evade it only through outputs that do not respect the table.

Outputs, in `{outdir}/`:
    split.json      per attack: catalogue status, outputs on passing files and how many respect the table, the features
                    the others move against it; per (detector, attack) evasion on passing files; per detector, files
                    still detected after every toolkit attack, and after every toolkit attack and the adaptive search

Usage:
    python scripts/a1_toolkit_split.py --outdir artifacts/experiments/a1/toolkit-split
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

__all__ = [
    "CATALOGUE",
    "respects",
]

# NOTE: how each secml-malware attack writes its edit (docs/status.md, 2026-11-02, the review's premises): six are
# byte-level edits of catalogue operations; GAMMA sections and GAMMA API go through LIEF's writer, which relays out the
# file (assumption A4).
CATALOGUE = {
    "padding": "app",
    "dos_extend": "ext",
    "content_shift": "shf",
    "gamma_shift": "shf",
    "format_exploit": "dos+ext+shf",
    "header_fields": "hdr",
    "gamma_sections": "LIEF (sec)",
    "gamma_api": "LIEF (imp)",
}

################################################################################
# The table
################################################################################


def load_table(prefix: Path, names: list[str]) -> np.ndarray:
    """The allowed sign per feature: +1 / -1 (monotone), 0 (fixed), or NaN (dropped: anything goes)."""
    mono = pl.read_csv(prefix.with_name(prefix.name + ".monotone.tsv"), separator="\t", has_header=False,
                       new_columns=["name", "sign"])
    dropped = set(prefix.with_name(prefix.name + ".neutralize.txt").read_text().split("\n")) - {""}
    sign = dict(zip(mono["name"].to_list(), mono["sign"].to_list()))
    unknown = (set(sign) | dropped) - set(names)
    if unknown:
        raise ValueError(f"{prefix}: {len(unknown)} features not in the deltas, e.g. {sorted(unknown)[:3]}")
    return np.array([np.nan if n in dropped else float(sign.get(n, 0)) for n in names])


def respects(delta: np.ndarray, allowed: np.ndarray) -> np.ndarray:
    """Per feature, whether the move is allowed (a NaN delta, a value appearing or vanishing, counts as a move)."""
    moved = (delta != 0) | np.isnan(delta)
    ok = np.isnan(allowed) | ~moved | ((allowed > 0) & (delta > 0)) | ((allowed < 0) & (delta < 0))
    return np.asarray(ok)


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--toolkit", type=Path, default=Path("artifacts/experiments/a1/toolkit-v2/results.parquet"))
    parser.add_argument("--adaptive", type=Path, default=Path("artifacts/experiments/a1/adaptive-v3/adaptive.parquet"))
    parser.add_argument("--deltas", type=Path, default=Path("artifacts/experiments/a_pv/deltas.parquet"))
    parser.add_argument("--table", type=Path,
                        default=Path("artifacts/experiments/a_directions_derived_v2/M_full-pre-quirkfixed"))
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    tk = pl.read_parquet(args.toolkit)
    passing = set(tk.filter(pl.col("precondition"))["name"].to_list())
    out: dict[str, Any] = {"inputs": {k: str(getattr(args, k)) for k in ("toolkit", "adaptive", "deltas", "table")}}

    # Per attack: outputs (run 78) that respect the table, on passing files.
    deltas = pl.read_parquet(args.deltas)
    names = [c for c in deltas.columns if ":" in c]
    allowed = load_table(args.table, names)
    attacks: dict[str, Any] = {}
    for atk in CATALOGUE:
        d = deltas.filter((pl.col("attack") == atk) & pl.col("name").is_in(passing))
        x = d.select(names).to_numpy()
        ok = respects(x, allowed[None, :])
        against = Counter(f"{names[j]} {'+' if x[i, j] > 0 else '-'}" for i, j in zip(*np.where(~ok)))
        bad = ~ok.all(axis=1)
        attacks[atk] = {
            "catalogue": CATALOGUE[atk],
            "outputs_passing": d.height,
            "respect_table": int((~bad).sum()),
            "respect_monotone_signs": int((ok | (allowed[None, :] == 0)).all(axis=1).sum()),
            "outside_table_files": d.filter(pl.Series(bad))["name"].str.slice(0, 10).to_list(),
            "outside_table_moves": against.most_common(10),
        }
    out["attacks"] = attacks
    out["respect_table_total"] = [sum(a["respect_table"] for a in attacks.values()),
                                  sum(a["outputs_passing"] for a in attacks.values())]
    # NOTE: the 2026-11-02 premise check counted only the monotone features' signs (284 of 288); a fixed feature is an
    # unconstrained input of the detector, so a move in one is outside the table too.
    out["respect_monotone_signs_total"] = sum(a["respect_monotone_signs"] for a in attacks.values())

    # Per (detector, attack): evasion on passing files (run 105).
    evasion: dict[str, Any] = {}
    for (defense,), g in tk.filter(pl.col("precondition")).group_by(["defense"], maintain_order=True):
        evasion[str(defense)] = {a: f"{int(x['evaded'].sum())}/{x.height}" for (a,), x in g.group_by(["attack"], maintain_order=True)}
        is_lief = pl.col("attack").is_in([a for a, c in CATALOGUE.items() if c.startswith("LIEF")])
        lief, byte = g.filter(is_lief), g.filter(~is_lief)
        evasion[str(defense)]["LIEF"] = f"{int(lief['evaded'].sum())}/{lief.height}"
        evasion[str(defense)]["catalogue"] = f"{int(byte['evaded'].sum())}/{byte.height}"
    out["evasion_passing"] = evasion

    # Per detector: still detected after every toolkit attack (all detected files, and passing ones).
    still: dict[str, Any] = {}
    per_file = tk.group_by(["defense", "name"]).agg(pl.col("evaded").any(), pl.col("precondition").first())
    for (defense,), g in per_file.group_by(["defense"], maintain_order=True):
        p = g.filter(pl.col("precondition"))
        still[str(defense)] = {"all": f"{int((~g['evaded']).sum())}/{g.height}",
                               "passing": f"{int((~p['evaded']).sum())}/{p.height}"}
    out["still_detected_toolkit"] = still

    # The adaptive search (run 108; full-store detectors, a different model family from the toolkit's).
    ad = pl.read_parquet(args.adaptive)
    out["adaptive"] = {str(d): f"{int(g['evaded_real'].sum())}/{g.height}"
                       for (d,), g in ad.group_by(["defense"], maintain_order=True)}

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "split.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
