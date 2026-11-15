"""
The check that a derived direction table does not hang on the files it was built from: the table of one corpus (the
training files, the paper's table) against the table of another (the evaluation set).

The table's per-operation signs are unions over the corpus, so the check's question is whether the second corpus shows
a move the table lacks: a cell of the check table whose signs are not among the table's. A cell where the table has
more signs is harmless (the table allows a move the second corpus never showed). Cells are counted apart for the
population's variant (the `_pre` columns: the paper's table and the detectors' input) and the strict one.

Outputs `--out` (JSON): per variant, the cells that differ, those the table lacks (with the features), the features
whose direction under a threat model differs, and whether the detectors' input files (`*.neutralize.txt`,
`*.monotone.tsv`) are the same.

Usage:
    python pipeline/3-directions/derived/compare_tables.py --table artifacts/scaleup/3-directions/loose \
        --check artifacts/scaleup/3-directions/check/loose --out artifacts/scaleup/3-directions/check/loose.json
"""

from __future__ import annotations

from argparse import ArgumentParser
import csv
import json
from pathlib import Path
from typing import Any

from provexp.featuresets.ember2024.directions import OPS
from provexp.featuresets.ember2024.directions import THREAT_MODELS

__all__ = ["compare", "read_table"]

################################################################################
# Comparison
################################################################################


def read_table(directory: Path) -> dict[str, dict[str, str]]:
    """The rows of a directory's `directions_sums.csv`, by `group:name`."""
    with open(directory / "directions_sums.csv", newline="") as f:
        rows = {f"{row['group']}:{row['name']}": row for row in csv.DictReader(f)}
    if not rows:
        raise ValueError(f"No rows in {directory / 'directions_sums.csv'}.")
    return rows


def compare(table: dict[str, dict[str, str]], check: dict[str, dict[str, str]]) -> dict[str, Any]:
    """
    Compare two direction tables cell by cell.

    Args:
        table: The table under test (`read_table`).
        check: The table of the second corpus.

    Returns:
        Per variant (`population`, `strict`): the number of per-operation cells that differ, the cells the table lacks
        (`feature`, `op`, `table`, `check`), and the features whose direction differs per threat model.
    """
    if list(table) != list(check):
        raise ValueError("The two tables do not list the same features in the same order.")
    out: dict[str, Any] = {"features": len(table)}
    for variant, suffix in (("population", "_pre"), ("strict", "")):
        differing = 0
        lacking: list[dict[str, str]] = []
        for feature, row in table.items():
            for op in OPS:
                a, b = row[f"op_{op}{suffix}"], check[feature][f"op_{op}{suffix}"]
                differing += set(a) != set(b)
                if not set(b) <= set(a):
                    lacking.append({"feature": feature, "op": op, "table": a, "check": b})
        directions = {tm: [f"{f} {row[f'{tm}{suffix}']} -> {check[f][f'{tm}{suffix}']}" for f, row in table.items()
                           if row[f"{tm}{suffix}"] != check[f][f"{tm}{suffix}"]] for tm in THREAT_MODELS}
        out[variant] = {"cells": len(table) * len(OPS), "cells_differing": differing, "cells_table_lacks": lacking,
                        "directions_differing": directions}
    return out


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--table", type=Path, required=True, help="The table's directory (directions.py's --outdir).")
    parser.add_argument("--check", type=Path, required=True, help="The second corpus's table.")
    parser.add_argument("--out", type=Path, required=True, help="The report (JSON).")
    args = parser.parse_args()

    report = compare(read_table(args.table), read_table(args.check))
    stems = sorted(p.name for pattern in ("*.neutralize.txt", "*.monotone.tsv") for p in args.table.glob(pattern))
    report["detector_files_differing"] = [s for s in stems if not (args.check / s).is_file()
                                          or (args.table / s).read_bytes() != (args.check / s).read_bytes()]
    report["detector_files"] = len(stems)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    for variant in ("population", "strict"):
        r = report[variant]
        moved = sum(len(v) for v in r["directions_differing"].values())
        print(f"{variant:10s} cells differing {r['cells_differing']:,} of {r['cells']:,}; the table lacks "
              f"{len(r['cells_table_lacks']):,}; directions differing {moved}")
    print(f"detector files differing: {len(report['detector_files_differing'])} of {report['detector_files']}")
    covered = not report["population"]["cells_table_lacks"]
    print("The table covers the second corpus (population)." if covered else
          "NOT COVERED: the second corpus shows moves the table lacks (population); see the report.")


if __name__ == "__main__":
    main()
