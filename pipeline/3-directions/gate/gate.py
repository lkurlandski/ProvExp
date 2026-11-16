"""
The gate between the derived tables and the detectors: fails unless the check of 3-directions/derived found the
evaluation set covered (session 70's rule: if it reports a move the tables lack, a differing population cell or a
differing detector input file, the user sees the cells and decides before any detector is trained).
"""

from __future__ import annotations

__all__ = [
    "problems",
]

import json
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any


################################################################################
# Gate
################################################################################

def problems(report: dict[str, Any]) -> list[str]:
    """What in one variant's check report (compare_tables.py's output) stops the detectors; empty: none."""
    out = []
    population = report["population"]
    if population["cells_table_lacks"]:
        out.append(f"NOT COVERED: the table lacks {len(population['cells_table_lacks'])} population cells")
    if population["cells_differing"]:
        out.append(f"{population['cells_differing']} population cells differ")
    moved = sum(len(v) for v in population["directions_differing"].values())
    if moved:
        out.append(f"{moved} population directions differ")
    if report["detector_files_differing"]:
        out.append(f"detector input files differ: {', '.join(report['detector_files_differing'])}")
    return out


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    parser.add_argument("--reports", type=Path, nargs="+", required=True, help="compare_tables.py's reports (JSON).")
    args = parser.parse_args()

    failed = False
    for path in args.reports:
        if not path.is_file():
            raise RuntimeError(f"No check report at {path} (3-directions/derived ran without its check?).")
        found = problems(json.loads(path.read_text()))
        for p in found:
            print(f"{path.name}: {p}")
        print(f"{path.name}: {'STOP' if found else 'covered, identical population cells and detector files'}")
        failed |= bool(found)
    if failed:
        print("The gate stops the detectors: show the user the cells (session 70's rule).")
        sys.exit(1)
    print("The gate passes.")


if __name__ == "__main__":
    main()
