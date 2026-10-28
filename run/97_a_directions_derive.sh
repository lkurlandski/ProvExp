#!/bin/bash
# Derivation step 7: the directions (C4) computed from the item tables instead of the hand rules of run 76
# (docs/item-layer-design.md, component 5; scripts/a_directions.py --derive), and the comparison with them (G3).
# The kinds' term vocabulary and the in-place operations' changes come from the 100 pilot files; the structural
# operations' changes are the catalogue's provisional declarations (provexp.featuresets.ember2024.catalogue). Two
# variants: strict (appending may complete structures past the end of the file, on any file) and the precondition
# row's (`-pre`: files where no locating range lies past the end).
# Hypothesis (from a 20-file smoke test): the precondition variant equals the hand rules per threat model except the
# anticipated disagreements (the entry section's name hash under sec, the Rich header under ext) and security_size,
# where the hand rule over-approximates (an insertion moves the table, not its size); the strict variant leaves few
# features one-sided, because truncated headers, sections, and directories past the end make every PE-parsed group
# two-sided under append.
#
# Took ~25 s (2026-10-28). Result: the hypothesis held. Precondition variant per threat model (fixed/up/down/both):
# M_add 277/270/0/2021 (hand: 287/270/0/2011), M_full 203/271/10/2084 (hand: 203/271/9/2085); the differences are
# exactly entry_name_hash_* (sec, both), the Rich header (ext, both), and security_size (hand over-approximates).
# Strict variant: M_add keeps 44 features (43 fixed, size up), M_full 9 (6 of them constant). 88 of 100 pilot files
# pass the precondition; of the 12 that fail, 8 are cut at the dataset's 4,000,000-byte cap.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

echo "Derive the directions on the 100 pilot files. Log: artifacts/logs/a_directions_derived.log"
python scripts/a_directions.py \
  --derive \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir artifacts/experiments/a_directions_derived \
  --workers 16 \
  &> artifacts/logs/a_directions_derived.log

echo "Done. Outputs: artifacts/experiments/a_directions_derived (directions.csv, g3.json, g3_cells.csv)"
