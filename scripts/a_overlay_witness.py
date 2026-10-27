"""
Witness for the overlay gap (docs/item-layer-design.md, "First row confirmed"): can appending bytes lower
`section:overlay_size` or any `body_*` sum?

pefile's `get_overlay_data_start_offset` skips any section or data-directory extent that runs past the end of the
file. Appending enough bytes to bring such an extent inside the file can move the overlay start later, so the overlay
shrinks although bytes were only added. This script tests that on the pilot files: for every extent past EOF (within
`--cap` bytes), append just enough to cover it (and 4,096 bytes more), plus a plain 4,096-byte append as a control,
then compare the overlay size and every raw count of the three body groups (`sums.py`) before and after.

The payload is one non-printable guard byte followed by random bytes, so no string straddles the old/new boundary
(the regex-extension case is a separate question, decided syntactically in the C4 engine).

Outputs, in `{outdir}/`:
    appends.parquet   one row per (file, append size): extent kinds past EOF, overlay size before and after, and per
                      body group the number of counts that dropped and their total drop
    report.json       files tested, files with an extent past EOF, files where overlay_size dropped, max body drops

Usage:
    PYTHONHASHSEED=0 python scripts/a_overlay_witness.py --outdir artifacts/experiments/a_overlay_witness
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any
from typing import Optional

import numpy as np
import pefile
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.sums import BodyByteEntropyHistogram
from provexp.featuresets.ember2024.sums import BodyByteHistogram
from provexp.featuresets.ember2024.sums import BodyStrings

__all__ = [
    "extents_past_eof",
    "overlay_size",
    "main",
]

ROOT = Path(__file__).resolve().parents[1]
CONTROL = 4096


################################################################################
# Helpers
################################################################################


def parse(bytez: bytes) -> Optional[pefile.PE]:
    """Parse a file the way the extractor does, or return None."""
    try:
        return pefile.PE(data=bytez)
    except Exception:
        return None


def overlay_size(bytez: bytes, pe: pefile.PE) -> int:
    """The overlay size thrember reads: the file length minus pefile's overlay start (0 without an overlay)."""
    start = pe.get_overlay_data_start_offset()
    return 0 if start is None else len(bytez) - int(start)


def extents_past_eof(pe: pefile.PE, n: int) -> list[tuple[str, int]]:
    """
    The extents pefile's overlay rule considers whose end lies past the end of the file.

    Args:
        pe: the parsed file.
        n: the file length.

    Returns:
        (kind, end) pairs: kind is "section" or "dir{index}" (the security directory is skipped, as pefile does).
    """
    out: list[tuple[str, int]] = []
    for section in pe.sections:
        out.append(("section", int(section.PointerToRawData + section.SizeOfRawData)))
    security = pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_SECURITY"]
    for idx, directory in enumerate(pe.OPTIONAL_HEADER.DATA_DIRECTORY):
        if idx == security or directory.Size == 0:
            continue
        try:
            out.append((f"dir{idx}", int(pe.get_offset_from_rva(directory.VirtualAddress) + directory.Size)))
        except pefile.PEFormatError:
            continue
    return [(kind, end) for kind, end in out if end > n]


def body_counts(bytez: bytes, pe: pefile.PE) -> dict[str, np.ndarray]:
    """The raw counts of the three body groups."""
    types = [BodyByteHistogram(), BodyByteEntropyHistogram(), BodyStrings()]
    return {
        t.name: np.asarray(t.process_raw_features(t.raw_features(bytez, pe)), dtype=np.float64)  # type: ignore[no-untyped-call]
        for t in types
    }


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--cap", type=int, default=8 * 2**20, help="Largest append tried, in bytes.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.cap < CONTROL:
        raise ValueError(f"--cap must be at least {CONTROL}, got {args.cap}.")

    rng = np.random.default_rng(args.seed)
    df = pl.read_parquet(args.pilot_files).select("name", "label")
    reader = SimpleDBReader(SimpleDB(args.db, check=False))
    rows: list[dict[str, Any]] = []
    for name, label in df.iter_rows():
        bytez = reader.get(name).data
        pe = parse(bytez)
        if pe is None:
            continue
        n = len(bytez)
        past = extents_past_eof(pe, n)
        sizes = {CONTROL}
        for _, end in past:
            if end - n + CONTROL <= args.cap:
                sizes |= {end - n + 1, end - n + CONTROL}
        before, ov0 = body_counts(bytez, pe), overlay_size(bytez, pe)
        for d in sorted(sizes):
            edited = bytez + b"\x00" + rng.integers(0, 256, d - 1, dtype=np.uint8).tobytes()
            pe2 = parse(edited)
            if pe2 is None:
                continue
            after = body_counts(edited, pe2)
            row: dict[str, Any] = {
                "name": name, "label": label, "size": n, "kinds": ",".join(sorted({k for k, _ in past})),
                "append": d, "overlay_before": ov0, "overlay_after": overlay_size(edited, pe2),
            }
            for group in before:
                drop = np.clip(before[group] - after[group], 0, None)
                row[f"drops_{group}"] = int((drop > 1e-9).sum())
                row[f"dropped_{group}"] = float(drop.sum())
            rows.append(row)

    out = pl.DataFrame(rows)
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_parquet(args.outdir / "appends.parquet")
    past_files = out.filter(pl.col("kinds") != "")
    report = {
        "files": out["name"].n_unique(),
        "appends": out.height,
        "files_with_extent_past_eof": past_files["name"].n_unique(),
        "of_which_at_size_cap_4000000": past_files.filter(pl.col("size") == 4_000_000)["name"].n_unique(),
        "files_overlay_size_dropped": out.filter(pl.col("overlay_after") < pl.col("overlay_before"))["name"].n_unique(),
        "max_body_drops": {c: int(out[c].max()) for c in out.columns if c.startswith("drops_")},  # type: ignore[arg-type]
    }
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
