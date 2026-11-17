"""
R18, the trial competitor (docs/reviews/2026-11-12-body/rebuttal/triage.md): the direction table a practitioner gets by
systematic trial (apply the operations, extract, look) instead of the derivation, and the files to train a monotone
detector on it exactly as the derived detectors are trained.

FOR ACADEMIC SECURITY RESEARCH ONLY. Reads stored edits and attack outputs; runs nothing.

Trial, per feature, over every observed edit on a file in the population:

    low     some edit lowered it                       -> dropped (neutralized), as the derived table drops lowerable ones
    up      some edit raised it and none lowered it    -> monotone increasing
    fixed   no edit moved it                           -> free

The sources are our own byte-level edits (catalogue_checks.py's edits.parquet, rows that pass the precondition and
parse; trial_probe.py's parquets, already restricted to the population) and, with `--toolkit`, the outputs of the eight
toolkit attacks on training malware in the population (run 133) and on the pilot (run 78). The toolkit writes through
LIEF, which relays out the file (assumption A4 of a1_adaptive.py), so its outputs carry changes no operation of the
threat model makes; the trial from our own edits alone is the clean competitor, the one with the toolkit the one a
practitioner using published tools would get.

The derived table is the monotone row's (`{stem}.neutralize.txt`, `{stem}.monotone.tsv` in --directions_dir):
neutralized features are lowerable, monotone ones raise-only, the rest fixed.

Outputs, in `{outdir}/`:
    trial_vs_derived{tag}.csv       one row per feature: group, derived, trial, the sources that lowered / raised it
    trial{tag}.neutralize.txt       for pipeline/4-detectors/train/train_classic.py --neutralize
    trial{tag}.monotone.tsv         for pipeline/4-detectors/train/train_classic.py --monotone
    report{tag}.json                derived x trial counts, overall and per group, warnings apart

Usage:
    PYTHONHASHSEED=0 python pipeline/3-directions/trial/trial_table.py --outdir artifacts/experiments/r18_trial \
        --probe artifacts/experiments/r18_trial/probe.parquet
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy import typing as npt
import polars as pl

from provexp.attacks.toolkit import ATTACKS
from provexp.attacks.toolkit import adv_deltas
from provexp.data.paths import EMBER2024_DATA
from provexp.data.paths import ROOT
from provexp.featuresets.ember2024.population import population

__all__ = ["derived_table", "trial_table"]

TOL = 1e-9
WARNINGS = "pefilewarnings"


################################################################################
# The two tables
################################################################################

def derived_table(directions_dir: Path, stem: str) -> tuple[list[str], dict[str, str], dict[str, str], list[str]]:
    """
    The feature names, their groups, the derived class of each (low, up, down, fixed), and the re-encoded features the
    row drops by construction (`reencoded.neutralize.txt`: the sums store's extra groups, absent from directions.csv),
    which the trial detector drops the same way.
    """
    t = pl.read_csv(directions_dir / "directions.csv", infer_schema_length=0)
    names = (t["group"] + ":" + t["name"]).to_list()
    group = dict(zip(names, t["group"].to_list()))
    neut = {ln.strip() for ln in (directions_dir / f"{stem}.neutralize.txt").read_text().splitlines() if ln.strip()}
    mono: dict[str, str] = {}
    for ln in (directions_dir / f"{stem}.monotone.tsv").read_text().splitlines():
        if ln.strip():
            f, s = ln.split("\t")
            mono[f] = s
    reencoded = [ln.strip() for ln in (directions_dir / "reencoded.neutralize.txt").read_text().splitlines() if ln.strip()]
    unknown = (neut | set(mono)) - set(names) - set(reencoded)
    if unknown:
        raise ValueError(f"{len(unknown)} features of {stem} are not in directions.csv: {sorted(unknown)[:5]}")
    cls = {f: "low" if f in neut else "up" if mono.get(f) == "1" else "down" if f in mono else "fixed" for f in names}
    return names, group, cls, sorted(neut & set(reencoded))


def _add_moves(moves: pl.DataFrame, low: dict[str, set[str]], up: dict[str, set[str]]) -> None:
    """Record a frame of (source, "feature +/-") rows."""
    for src, m in moves.iter_rows():
        f, s = m[:-2], m[-1]
        if f in low:
            (low if s == "-" else up)[f].add(src)


def _add_deltas(d: npt.NDArray[np.float32], attacks: npt.NDArray[Any], names: list[str], low: dict[str, set[str]],
                up: dict[str, set[str]]) -> None:
    """Record perturbation vectors (rows of d), each from the attack in `attacks`."""
    lo, hi = d < -TOL, d > TOL
    for j, f in enumerate(names):
        low[f].update(f"toolkit:{a}" for a in set(attacks[lo[:, j]].tolist()))
        up[f].update(f"toolkit:{a}" for a in set(attacks[hi[:, j]].tolist()))


def trial_table(names: list[str], edits: list[Path], probes: list[Path], toolkit: bool,
                workers: int) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """
    Per feature, the sources that lowered and raised it.

    Args:
        names: The feature names.
        edits: catalogue_checks.py edits.parquet files.
        probes: trial_probe.py parquets.
        toolkit: Whether to add the toolkit outputs (runs 133 and 78).
        workers: Workers for the population check of the attacked training malware.

    Returns:
        (lowered, raised): feature -> set of sources ("edit:<op>", "probe:<op>", "toolkit:<attack>").
    """
    low: dict[str, set[str]] = {f: set() for f in names}
    up: dict[str, set[str]] = {f: set() for f in names}
    for p in edits:
        e = (pl.scan_parquet(p).select("op", "precondition", "parses", "moves")
             .filter(pl.col("precondition") & pl.col("parses")).explode("moves").drop_nulls("moves")
             .select(("edit:" + pl.col("op")).alias("src"), "moves").unique().collect())
        _add_moves(e, low, up)
    for p in probes:
        e = (pl.read_parquet(p).explode("moves").drop_nulls("moves")
             .select(("probe:" + pl.col("op").str.replace(r"^ren\d+$", "ren")).alias("src"), "moves").unique())
        _add_moves(e, low, up)
    if toolkit:
        gen = ROOT / "artifacts/experiments/a1/advtrain/generated-seedperfile"
        files = pl.read_parquet(gen / "files.parquet").filter(pl.col("attack").is_in(list(ATTACKS)))
        d = adv_deltas(gen, ROOT / "artifacts/features/ember2024", list(ATTACKS), names)
        member = population(sorted(set(files["name"].to_list())), workers, db=EMBER2024_DATA / "tr")  # the pilot's files
        mask = np.array([member[n] for n in files["name"].to_list()])
        _add_deltas(d[mask], files["attack"].to_numpy()[mask], names, low, up)
        pv = pl.read_parquet(ROOT / "artifacts/experiments/a_pv/deltas.parquet")
        pmem = dict(pl.read_parquet(ROOT / "artifacts/experiments/a1/toolkit-derived/results.parquet")
                    .select("name", "precondition").unique("name").iter_rows())
        pv = pv.filter(pl.col("name").replace_strict(pmem, default=False))
        _add_deltas(pv.select(names).to_numpy().astype(np.float32), pv["attack"].to_numpy(), names, low, up)
    return low, up


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--directions_dir", type=Path,
                        default=ROOT / "artifacts/experiments/a_directions_derived_sums_loose")
    parser.add_argument("--stem", default="M_full-pre-control")
    parser.add_argument("--edits", type=Path, nargs="*",
                        default=[ROOT / "artifacts/experiments/catalogue_checks/2000-exact/edits.parquet",
                                 ROOT / "artifacts/experiments/catalogue_checks/pilot-loose-lief/edits.parquet"])
    parser.add_argument("--probe", type=Path, nargs="*", default=[])
    parser.add_argument("--toolkit", action="store_true", help="Add the toolkit outputs (LIEF-written; A4).")
    parser.add_argument("--tag", default="", help="Suffix of every output file.")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()

    names, group, derived, reencoded = derived_table(args.directions_dir, args.stem)
    low, up = trial_table(names, args.edits, args.probe, args.toolkit, args.workers)
    trial = {f: "low" if low[f] else "up" if up[f] else "fixed" for f in names}
    df = pl.DataFrame([{"feature": f, "group": group[f], "derived": derived[f], "trial": trial[f],
                        "lowered_by": " ".join(sorted(low[f])), "raised_by": " ".join(sorted(up[f]))} for f in names])
    args.outdir.mkdir(parents=True, exist_ok=True)
    df.write_csv(args.outdir / f"trial_vs_derived{args.tag}.csv")
    (args.outdir / f"trial{args.tag}.neutralize.txt").write_text("".join(f"{f}\n" for f in reencoded + [f for f in names if trial[f] == "low"]))
    (args.outdir / f"trial{args.tag}.monotone.tsv").write_text("".join(f"{f}\t1\n" for f in names if trial[f] == "up"))

    def counts(frame: pl.DataFrame) -> dict[str, int]:
        return {f"{r['derived']}->{r['trial']}": r["len"] for r in frame.group_by("derived", "trial").len().to_dicts()}

    modeled = df.filter(pl.col("group") != WARNINGS)
    diff = modeled.filter(pl.col("derived") != pl.col("trial"))
    report = {"stem": args.stem, "edits": [p.as_posix() for p in args.edits], "probe": [p.as_posix() for p in args.probe],
              "toolkit": args.toolkit, "all": counts(df), "modeled": counts(modeled),
              "warnings": counts(df.filter(pl.col("group") == WARNINGS)),
              "modeled_differences_by_group": diff.group_by("derived", "trial", "group").len()
              .sort("derived", "trial", "len", descending=[False, False, True]).to_dicts()}
    (args.outdir / f"report{args.tag}.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("all", "modeled", "warnings")}, indent=2))
    for r in report["modeled_differences_by_group"]:
        print(f"  derived {r['derived']:>5} -> trial {r['trial']:>5}  {r['group']:<16} {r['len']}")


if __name__ == "__main__":
    main()
