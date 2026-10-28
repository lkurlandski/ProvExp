"""
Witness for the signature case of G3 (docs/item-layer-design.md, "structures past the end of the file"): can appending
bytes raise the authenticode features, which the hand rules let only fall?

pefile and signify read the certificate table at the file offset the SECURITY directory entry gives. Where that table
lies past the end of the file (on the pilot files, files cut at the dataset's 4 MB cap), the extractor sees no
signature. Appending zeros up to the table's offset, then a certificate table copied from a signed file (zero-padded to
the declared size), completes it. This script does that for every pilot file whose table lies past its end, with each
signed pilot file whose table fits in the declared size as a donor (the smallest first, up to --donors), re-extracts,
and records the authenticode features before and after.

Outputs, in `{outdir}/`:
    witnesses.parquet   one row per (file, donor): the table's offset and size, bytes appended, and each authenticode
                        feature before and after
    report.json         files with a table past the end, witnesses where a feature rose, and the features that rose

Usage:
    PYTHONHASHSEED=0 python scripts/a_signature_witness.py --outdir artifacts/experiments/a_signature_witness
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any
from typing import Optional
import warnings

import numpy as np
import pefile
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors

__all__ = [
    "security_entry",
    "complete",
    "main",
]

warnings.filterwarnings("ignore", category=SyntaxWarning)

SECURITY = 4


################################################################################
# Helpers
################################################################################


def security_entry(bytez: bytes) -> Optional[tuple[int, int]]:
    """The certificate table's file offset and size, or None if the file has none (or does not parse)."""
    try:
        pe = pefile.PE(data=bytez, fast_load=True)
    except (pefile.PEFormatError, AttributeError):
        return None
    directories = pe.OPTIONAL_HEADER.DATA_DIRECTORY
    if len(directories) <= SECURITY or not directories[SECURITY].Size:
        return None
    return int(directories[SECURITY].VirtualAddress), int(directories[SECURITY].Size)


def complete(bytez: bytes, offset: int, size: int, table: bytes) -> bytes:
    """Append zeros up to `offset`, then `table` zero-padded to `size`: the file with its certificate table filled in."""
    if offset < len(bytez):
        raise ValueError(f"The table starts at {offset}, inside the file ({len(bytez)} bytes).")
    if len(table) > size:
        raise ValueError(f"The donor table ({len(table)} bytes) exceeds the declared size ({size}).")
    return bytez + bytes(offset - len(bytez)) + table + bytes(size - len(table))


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--files", type=Path, default=Path("artifacts/experiments/e1/seed-0/zeros/files.parquet"))
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--donors", type=int, default=3, help="Donor tables tried per file, smallest first.")
    args = parser.parse_args()

    reader = SimpleDBReader(SimpleDB(args.db, check=False))
    extractor = merge_import_descriptors(PEFeatureExtractor())
    names = extractor.feature_names
    auth = [i for i, n in enumerate(names) if n.startswith("authenticode:")]
    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")

    targets: list[tuple[str, bytes, int, int]] = []
    donors: list[tuple[str, bytes]] = []
    for name in sorted(df["name"].to_list()):
        bytez = reader.get(name).data
        entry = security_entry(bytez)
        if entry is None:
            continue
        offset, size = entry
        if offset + size > len(bytez):
            targets.append((name, bytez, offset, size))
        elif extractor.feature_vector(bytez)[auth[0]] > 0:  # type: ignore[no-untyped-call]
            donors.append((name, bytez[offset:offset + size]))
    donors.sort(key=lambda d: len(d[1]))
    print(f"{len(targets)} files with a certificate table past the end, {len(donors)} signed donors", flush=True)

    rows: list[dict[str, Any]] = []
    for name, bytez, offset, size in targets:
        before = extractor.feature_vector(bytez)  # type: ignore[no-untyped-call]
        fitting = [d for d in donors if len(d[1]) <= size][: args.donors]
        for donor, table in fitting:
            # Appending must start at the end of the file; a table that starts inside it is not this case.
            if offset < len(bytez):
                continue
            after = extractor.feature_vector(complete(bytez, offset, size, table))  # type: ignore[no-untyped-call]
            row: dict[str, Any] = {"name": name, "donor": donor, "offset": offset, "size": size, "appended": offset + size - len(bytez), "donor_size": len(table)}
            for i in auth:
                short = names[i].split(":", 1)[1]
                row[f"{short}_before"] = float(before[i])
                row[f"{short}_after"] = float(after[i])
            row["rose"] = [names[i] for i in auth if after[i] > before[i]]
            rows.append(row)
            print(f"{name[:12]} + {donor[:12]}: {row['rose']}", flush=True)

    args.outdir.mkdir(parents=True, exist_ok=True)
    out = pl.DataFrame(rows) if rows else pl.DataFrame()
    out.write_parquet(args.outdir / "witnesses.parquet")
    rose = [r for r in rows if r["rose"]]
    report = {
        "files_with_table_past_end": len(targets),
        "files_with_table_starting_inside": sum(offset < len(b) for _, b, offset, _ in targets),
        "signed_donors": len(donors),
        "witnesses": len(rows),
        "witnesses_where_a_feature_rose": len(rose),
        "files_where_a_feature_rose": len({r["name"] for r in rose}),
        "features_that_rose": sorted({f for r in rose for f in r["rose"]}),
        "max_appended": int(np.max([r["appended"] for r in rows])) if rows else 0,
    }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
