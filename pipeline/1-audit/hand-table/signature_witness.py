"""
Witness for the signature case of G3 (docs/evidence/item-layer-design.md, "structures past the end of the file"): can appending
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
    PYTHONHASHSEED=0 python pipeline/1-audit/hand-table/signature_witness.py --outdir artifacts/experiments/a_signature_witness
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from multiprocessing import get_context
from pathlib import Path
from typing import Any
from typing import Optional
import warnings

import numpy as np
import pefile
import polars as pl

from provexp.data.files import FileReader
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import fix_quirks

__all__ = ["security_entry", "complete", "main"]

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
# Workers
################################################################################


_W: dict[str, Any] = {}


def _init_worker(donors: list[tuple[str, bytes]], num_donors: int) -> None:
    """Open the file store and build the extractor once per worker."""
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    extractor = fix_quirks(PEFeatureExtractor())
    names = extractor.feature_names
    _W.update(reader=FileReader(), extractor=extractor, names=names, donors=donors, num_donors=num_donors,
              auth=[i for i, n in enumerate(names) if n.startswith("authenticode:")])


def _scan(name: str) -> tuple[str, Optional[tuple[int, int, int]], Optional[bytes]]:
    """One file: (name, its certificate table's (offset, size, file length) if the table runs past the end, its table
    if it is a signed donor)."""
    bytez = _W["reader"].get(name)
    entry = security_entry(bytez)
    if entry is None:
        return name, None, None
    offset, size = entry
    if offset + size > len(bytez):
        return name, (offset, size, len(bytez)), None
    if _W["extractor"].feature_vector(bytez)[_W["auth"][0]] > 0:
        return name, None, bytez[offset:offset + size]
    return name, None, None


def _complete_file(task: tuple[str, int, int]) -> list[dict[str, Any]]:
    """The witness rows of one target: its table filled in from each fitting donor."""
    name, offset, size = task
    extractor, names, auth = _W["extractor"], _W["names"], _W["auth"]
    bytez = _W["reader"].get(name)
    before = extractor.feature_vector(bytez)
    fitting = [d for d in _W["donors"] if len(d[1]) <= size][: _W["num_donors"]]
    rows: list[dict[str, Any]] = []
    for donor, table in fitting:
        # Appending must start at the end of the file; a table that starts inside it is not this case.
        if offset < len(bytez):
            continue
        after = extractor.feature_vector(complete(bytez, offset, size, table))
        row: dict[str, Any] = {"name": name, "donor": donor, "offset": offset, "size": size,
                               "appended": offset + size - len(bytez), "donor_size": len(table)}
        for i in auth:
            short = names[i].split(":", 1)[1]
            row[f"{short}_before"] = float(before[i])
            row[f"{short}_after"] = float(after[i])
        row["rose"] = [names[i] for i in auth if after[i] > before[i]]
        rows.append(row)
    return rows


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--files", type=Path, default=Path("artifacts/experiments/e1/seed-0/zeros/files.parquet"))
    parser.add_argument("--workers", type=int, default=16, help="Processes, one file at a time each.")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--donors", type=int, default=3, help="Donor tables tried per file, smallest first.")
    args = parser.parse_args()

    df = pl.read_parquet(args.files)
    if "status" in df.columns:
        df = df.filter(pl.col("status") == "ok")
    files = sorted(df["name"].to_list())
    FileReader().check(files)  # the scale-up's files come from the file store (FILE_STORE)

    targets: list[tuple[str, int, int, int]] = []  # name, offset, size, file length
    donors: list[tuple[str, bytes]] = []
    with get_context("spawn").Pool(args.workers, initializer=_init_worker, initargs=([], 0)) as pool:
        for name, entry, table in pool.imap(_scan, files, chunksize=4):
            if entry is not None:
                targets.append((name, *entry))
            elif table is not None:
                donors.append((name, table))
    donors.sort(key=lambda d: len(d[1]))
    print(f"{len(targets)} files with a certificate table past the end, {len(donors)} signed donors", flush=True)

    rows: list[dict[str, Any]] = []
    with get_context("spawn").Pool(args.workers, initializer=_init_worker, initargs=(donors, args.donors)) as pool:
        for part in pool.imap(_complete_file, [t[:3] for t in targets]):
            for row in part:
                print(f"{row['name'][:12]} + {row['donor'][:12]}: {row['rose']}", flush=True)
            rows += part

    args.outdir.mkdir(parents=True, exist_ok=True)
    out = pl.DataFrame(rows) if rows else pl.DataFrame()
    out.write_parquet(args.outdir / "witnesses.parquet")
    rose = [r for r in rows if r["rose"]]
    report = {
        "files_with_table_past_end": len(targets),
        "files_with_table_starting_inside": sum(offset < length for _, offset, _, length in targets),
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
