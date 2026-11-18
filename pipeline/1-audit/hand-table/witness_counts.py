"""
The files that show each error of the hand-written table (Section 5.2, Table 3's last column), counted from the
outputs of the audit steps on one file list.

Each error is a (feature, operation) cell where the hand table excludes a direction that a real edit, extracted again,
moves the feature in. This script counts, per error, the files on which our own edit shows it, split by whether the
original file is in the population (`1-audit/population`'s `in_population`):

    overlay size, add a section          catalogue checks: `sec` moves `section:overlay_size` (hand: fixed)
    entry section, add a section         structure witness `entry`: an entry-name feature changes (hand: fixed)
    Rich header, gap before PE header    structure witness `rich_ext` (hand: fixed)
    Rich header, overwrite header        structure witness `rich_hdr` (hand: fixed)
    overlay size, append                 overlay witness: the overlay shrinks (hand: up)
    certificates, append                 signature witness: an authenticode feature rises (hand: down)
    relocations, exports, append         structure witnesses `relocs`, `exports` (hand: fixed)
    section entropy, overwrite header    catalogue checks: `hdr` moves a section entropy feature (hand: fixed)

Outputs, in `{outdir}/`:
    witness_counts.json   per error: files checked, files with a witness in the population and outside it

Usage:
    python pipeline/1-audit/hand-table/witness_counts.py --files FILES --audit artifacts/scaleup/1-audit \
        --outdir artifacts/scaleup/1-audit/hand-table
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any

import polars as pl

__all__ = ["count"]


################################################################################
# Witnesses per error
################################################################################


def _catalogue(edits: pl.DataFrame, op: str, prefixes: tuple[str, ...]) -> set[str]:
    """Files where an edit of `op` on the original file moves a feature whose name starts with one of `prefixes`."""
    rows = edits.filter((pl.col("op") == op) & pl.col("applies"))
    if "base" in rows.columns:  # NOTE: `--loose` runs also edit escaped copies; only the originals count here.
        rows = rows.filter(pl.col("base") == "orig")
    return {r["name"] for r in rows.iter_rows(named=True) if any(m.startswith(prefixes) for m in (r["moves"] or []))}


def _structure(witnesses: pl.DataFrame, case: str) -> set[str]:
    """Files where the structure witness `case` changed a feature."""
    mine = witnesses.filter(pl.col("case") == case)
    return {r["name"] for r in mine.iter_rows(named=True) if r["changed"]}


def count(files: list[str], population: pl.DataFrame, witnesses: dict[str, set[str]]) -> dict[str, Any]:
    """
    Per error, the witnessed files in the population and outside it.

    Args:
        files: The file list the audit steps ran on.
        population: `1-audit/population`'s files.parquet (name, in_population).
        witnesses: The files that show each error.

    Returns:
        A dict keyed by error: files checked, witnesses in the population and outside it.
    """
    inside = set(population.filter(pl.col("in_population"))["name"].to_list())
    known = set(files)
    out: dict[str, Any] = {"files": len(files), "in_population": len(inside & known)}
    for error, names in witnesses.items():
        names &= known
        out[error] = {"in_population": len(names & inside), "outside": len(names - inside)}
    return out


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--files", type=Path, required=True, help="The file list the audit steps ran on (`name`).")
    parser.add_argument("--audit", type=Path, required=True, help="The audit stage's output root ($OUT_ROOT/1-audit).")
    parser.add_argument("--hand_table", type=Path, default=None,
                        help="The witnesses' folder (default: {audit}/hand-table).")
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    files = pl.read_parquet(args.files)["name"].to_list()
    population = pl.read_parquet(args.audit / "population" / "files.parquet")
    edits = pl.read_parquet(args.audit / "catalogue" / "edits.parquet")
    hand = args.hand_table if args.hand_table is not None else args.audit / "hand-table"
    structure = pl.read_parquet(hand / "structure" / "witnesses.parquet")
    overlay = pl.read_parquet(hand / "overlay" / "appends.parquet")
    signature = pl.read_parquet(hand / "signature" / "witnesses.parquet")

    entropy = ("section:entropy_hash_", "section:max_entropy", "section:min_entropy")
    witnesses = {
        "overlay_size/sec": _catalogue(edits, "sec", ("section:overlay_size ",)),
        "entry_section/sec": _structure(structure, "entry"),
        "rich_header/ext": _structure(structure, "rich_ext"),
        "rich_header/hdr": _structure(structure, "rich_hdr"),
        "overlay_size/app": set(overlay.filter(pl.col("overlay_after") < pl.col("overlay_before"))["name"].to_list()),
        "certificates/app": set(signature.filter(pl.col("rose").list.len() > 0)["name"].to_list()) if signature.height else set(),
        "relocations/app": _structure(structure, "relocs"),
        "exports/app": _structure(structure, "exports"),
        "section_entropy/hdr": _catalogue(edits, "hdr", entropy),
    }
    report = count(files, population, witnesses)
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "witness_counts.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
