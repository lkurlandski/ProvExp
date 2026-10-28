#!/bin/bash
# Re-run the item-layer checks after splitting the locating ranges per structure (run 95): G1 exactness on the pilot
# files (as run 90), G4 Table A0 with the C1 engine (as run 92), and G6 random in-place writes on the pilot files (as
# run 93), each into a new directory so that the earlier results stay.
# Hypothesis: G1 unchanged (only locating ranges changed); G6 still exact, with fewer writes flagged (writes into
# directories without items, e.g. debug or resources, no longer meet every item's locating ranges); G4's append row
# may flag one or two files beyond the 11 overrun files (certificate tables and unmappable directory addresses past the
# end of the file are now recorded as locating).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

D=artifacts/experiments/item_checks

echo "G1 + G2 on the 100 pilot files. Log: artifacts/logs/item_checks_exact_pilot_split.log"
python scripts/item_checks.py exact \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir $D/exact-pilot-split \
  --workers 16 \
  &> artifacts/logs/item_checks_exact_pilot_split.log

echo "G4: Table A0 with the C1 engine, 100 pilot files. Log: artifacts/logs/a_c1_engine_split.log"
python scripts/a_c1_table0.py \
  --outdir artifacts/experiments/a_c1_engine_split \
  &> artifacts/logs/a_c1_engine_split.log

echo "G6 on the 100 pilot files. Log: artifacts/logs/item_checks_margins_pilot_split.log"
python scripts/item_checks.py margins \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir $D/margins-pilot-split \
  --workers 16 \
  &> artifacts/logs/item_checks_margins_pilot_split.log

echo "Done. Reports: $D/exact-pilot-split, artifacts/experiments/a_c1_engine_split, $D/margins-pilot-split (report.json)"
