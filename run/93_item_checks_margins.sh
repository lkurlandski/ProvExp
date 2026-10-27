#!/bin/bash
# Derivation step 5, check G6 (docs/item-layer-design.md; assumption A3): random in-place writes (offset uniform over
# the file, 1-64 bytes, random or printable content; 20 per file), predicted by the C1 engine and compared with
# re-extraction bit for bit. Step 1: the 100 pilot files; step 2: 100 fresh files from the 2,000-file set (seed 1),
# since the first round of step 1 was used to fix a declaration.
# Hypothesis: every predicted write is exact; writes into headers, directories, import names, or the certificate
# table are flagged. First round: 1 failure in 1,561 (has_dynamic_relocs: pefile reads the dynamic relocation table
# the load configuration points to, outside the directory; added to the relocs item's locating ranges).
#
# Took ~75 s and ~45 s (2026-10-27). Result after the fix: pilot 1,560/1,560 predicted writes bit-exact (440 flagged:
# 334 structural, 97 certificate table, 9 import names); fresh 1,463/1,463 (537 flagged). G6 passes.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

D=artifacts/experiments/item_checks

echo "G6 on the 100 pilot files. Log: artifacts/logs/item_checks_margins_pilot.log"
python scripts/item_checks.py margins \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir $D/margins-pilot \
  --workers 16 \
  &> artifacts/logs/item_checks_margins_pilot.log

echo "G6 on 100 fresh files from the 2,000-file set. Log: artifacts/logs/item_checks_margins_2000_seed1.log"
python scripts/item_checks.py margins \
  --files artifacts/explanation_set/ts.parquet \
  --outdir $D/margins-2000-seed1 \
  --workers 16 \
  --limit 100 \
  --seed 1 \
  &> artifacts/logs/item_checks_margins_2000_seed1.log

echo "Done. Reports: $D/margins-pilot/report.json, $D/margins-2000-seed1/report.json"
