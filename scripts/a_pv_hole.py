"""
Direction A, go/no-go check 2 (docs/direction-A-mock.md), part 2 of 2: the hole in PV selection.

FOR ACADEMIC SECURITY RESEARCH ONLY. From the perturbation vectors of scripts/a_pv_attacks.py, reconstruct Gimenez
et al.'s perturbation-vector (PV) feature selection and compare it with the directions feature provenance computes
(C4, docs/direction-A-threat-model.md). The question this answers is defensive: does PV selection, derived from a
finite sample of attacks, keep features that an attacker *could* push down within the same threat model but that this
particular sample happened never to decrease? Those features are a hole: a monotone detector built on them is not
sound, though PV's own attacks never reveal it.

Definitions (per threat model M, quirk-fixed variant):
    PV-kept        = features whose perturbation is >= -tol across every observed perturbation vector (so PV, with a
                     monotone classifier, treats them as safe to rely on). Features no attack moved are PV-kept.
    C4-decreasable = features C4 proves an attacker can lower under M (direction "both" or "down").
    hole           = PV-kept AND C4-decreasable: the features PV wrongly trusts.

Go/no-go: GO if the hole carries a material share (>= 5%) of the PV-selected GBDT's total split gain; NO-GO if the
hole is empty or unused, in which case C4 buys nothing over PV here (bring to the user before dropping anything).

Outputs, in `{outdir}/`:
    hole.csv            one row per hole feature (threat model, name, group, min observed delta, gain, gain share)
    report.json         per threat model: |PV-kept|, |C4-decreasable|, |hole|, gain shares (hole / PV / all)
    pv.neutralize.txt   features a PV-selected GBDT drops (the complement of PV-kept), for scripts/train_classic.py
    pv.monotone.tsv     PV-kept features as monotone-increasing (+1), matching Gimenez et al.'s PV + monotone model

The gain share is read from --model: pass the PV-selected GBDT (trained from pv.neutralize.txt / pv.monotone.tsv) for
the decisive number; the default unconstrained GBDT gives an immediate preview of where the hole sits.

With `--attacks`, PV selection is derived from that subset of the attacks only (Table A1's "PV, seen" row; the quick
seen/held-out split of docs/direction-A-A1-design.md, with leave-one-out as the formal version), and `--tag` suffixes
every output file (e.g. `pv-seen.neutralize.txt`, `report-seen.json`).

Usage:
    python scripts/a_pv_hole.py --deltas artifacts/experiments/a_pv/deltas.parquet \
        --directions_dir artifacts/experiments/a_directions --outdir artifacts/experiments/a_pv
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path

import lightgbm
import numpy as np
import polars as pl

__all__ = ["decreasable_features", "pv_kept"]

ROOT = Path(__file__).resolve().parent.parent
THREAT_MODELS = ("M_add", "M_full")  # nested; M_full is the decisive one for the mock


def pv_kept(deltas: np.ndarray, names: list[str], tol: float) -> set[str]:
    """Features PV selection keeps: never decreased (within tol) across the observed perturbation vectors.

    Args:
        deltas: (num_pairs, num_features) perturbation vectors phi(z') - phi(z).
        names: Feature names, aligned with the columns of `deltas`.
        tol: A perturbation is counted as a decrease only if it is below -tol (float-noise guard).

    Returns:
        The set of PV-kept feature names. Features no attack moved are kept.
    """
    kept_mask = deltas.min(axis=0) >= -tol
    return {names[j] for j in range(len(names)) if bool(kept_mask[j])}


def decreasable_features(directions_dir: Path, tm: str) -> set[str]:
    """Features C4 proves decreasable under `tm` (quirk-fixed): direction "both" (dropped) or "down".

    Args:
        directions_dir: The a_directions output directory.
        tm: A threat-model name, e.g. "M_full".

    Returns:
        The set of C4-decreasable feature names.
    """
    both = set((directions_dir / f"{tm}-quirkfixed.neutralize.txt").read_text().split())
    down = set()
    for line in (directions_dir / f"{tm}-quirkfixed.monotone.tsv").read_text().splitlines():
        name, sign = line.split("\t")
        if sign.strip() == "-1":
            down.add(name)
    return both | down


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--deltas", type=Path, required=True)
    parser.add_argument("--directions_dir", type=Path, default=ROOT / "artifacts/experiments/a_directions")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=ROOT / "artifacts/models/gbdt/seed-0/model.txt",
                        help="GBDT whose split gain weights the hole; pass the PV-selected GBDT for the decisive read.")
    parser.add_argument("--tol", type=float, default=1e-6)
    parser.add_argument("--attacks", nargs="+", default=None, help="Derive PV from these attacks only (default: all).")
    parser.add_argument("--tag", type=str, default="", help="Suffix of the output files, e.g. '-seen'.")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    df = pl.read_parquet(args.deltas)
    if args.attacks is not None:
        unknown = set(args.attacks) - set(df["attack"].unique().to_list())
        if unknown:
            raise ValueError(f"Attacks not in {args.deltas.as_posix()}: {sorted(unknown)}")
        df = df.filter(pl.col("attack").is_in(args.attacks))
    meta = {"name", "attack", "p_clean", "p_adv"}
    names = [c for c in df.columns if c not in meta]
    deltas = df.select(names).to_numpy()
    group = {n: n.split(":", 1)[0] for n in names}

    booster = lightgbm.Booster(model_file=str(args.model))
    # The model stores features positionally (generic "Column_j" names); its order is the extractor index order, the
    # same order a_pv_attacks wrote the delta columns in (verified: directions index == extractor order == GBDT index).
    if booster.num_feature() != len(names):
        raise RuntimeError(f"The model has {booster.num_feature()} features, the deltas have {len(names)}.")
    gain = np.asarray(booster.feature_importance(importance_type="gain"), dtype=float)
    gain_total = float(gain.sum())
    gain_of = {names[j]: float(gain[j]) for j in range(len(names))}

    kept = pv_kept(deltas, names, args.tol)
    min_delta = {names[j]: float(deltas[:, j].min()) for j in range(len(names))}
    moved = {names[j] for j in range(len(names)) if bool((np.abs(deltas[:, j]) > args.tol).any())}

    report: dict[str, object] = {
        "attacks": sorted(df["attack"].unique().to_list()),
        "num_perturbation_vectors": int(deltas.shape[0]),
        "num_features": len(names),
        "tol": args.tol,
        "model": str(args.model),
        "features_moved_by_some_attack": len(moved),
        "pv_kept": len(kept),
    }
    hole_rows: list[dict[str, object]] = []
    for tm in THREAT_MODELS:
        decreasable = decreasable_features(args.directions_dir, tm)
        hole = kept & decreasable
        pv_gain = sum(gain_of[n] for n in kept)
        hole_gain = sum(gain_of[n] for n in hole)
        report[tm] = {
            "c4_decreasable": len(decreasable),
            "hole": len(hole),
            "hole_moved_by_an_attack": len(hole & moved),
            "hole_never_moved": len(hole - moved),
            "gain_share_hole_over_all": hole_gain / gain_total if gain_total else 0.0,
            "gain_share_hole_over_pv": hole_gain / pv_gain if pv_gain else 0.0,
            "verdict_go_if_ge_5pct": (hole_gain / pv_gain if pv_gain else 0.0) >= 0.05,
        }
        for n in sorted(hole, key=lambda n: -gain_of[n]):
            hole_rows.append({"threat_model": tm, "name": n, "group": group[n], "min_delta": min_delta[n],
                              "moved_by_attack": n in moved, "gain": gain_of[n],
                              "gain_share_over_pv": gain_of[n] / pv_gain if pv_gain else 0.0})

    t = args.tag
    pl.DataFrame(hole_rows).write_parquet(args.outdir / f"hole{t}.parquet")
    pl.DataFrame(hole_rows).write_csv(args.outdir / f"hole{t}.csv")
    (args.outdir / f"report{t}.json").write_text(json.dumps(report, indent=2))

    # Train files for the PV-selected monotone GBDT (Gimenez et al.'s PV + monotone model): drop all but PV-kept,
    # constrain the kept features monotone-increasing.
    dropped = [n for n in names if n not in kept]
    (args.outdir / f"pv{t}.neutralize.txt").write_text("\n".join(dropped) + "\n")
    (args.outdir / f"pv{t}.monotone.tsv").write_text("".join(f"{n}\t1\n" for n in names if n in kept))

    print(json.dumps(report, indent=2))
    print(f"\nWrote hole{t}.csv ({len(hole_rows)} rows) and PV train files to {args.outdir}/", flush=True)


if __name__ == "__main__":
    main()
