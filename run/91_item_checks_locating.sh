#!/bin/bash
# Derivation step 4, check G5 (docs/item-layer-design.md; assumption A1): flip every byte of the header region (XOR
# 0xFF, at most 1,024 bytes per file) of 20 files and re-parse. Every item that appears, disappears, or moves must
# have the flipped byte among its recorded locating ranges, and every item whose contributions change must have it
# among its member or locating ranges. Step 1: 20 pilot files (seed 0); step 2: 20 fresh files from the 2,000-file
# set (seed 1), since the first round of step 1 was used to fix the declarations.
# Hypothesis (first round): a few unrecorded locating fields. Held: 1,385 failures at 55 (file, byte) pairs, from
# three pefile rules: it stops reading the section table at the first implausible header (so a section depends on
# the headers before it), any non-PEFormatError exception in a directory parse ends the whole parse (a bogus debug
# directory size raises AttributeError; docs/upstream-issues.md item 5), and SizeOfImage bounds the relocations.
#
# Took ~2 min per step (2026-10-27). Result after the fix: 0 failures on 18,944 flips (1,567 changed the parse) on
# the pilot files, and 0 on 18,944 flips (1,595 changed the parse) on the fresh files. G5 passes.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

D=artifacts/experiments/item_checks

echo "G5 on 20 pilot files. Log: artifacts/logs/item_checks_locating_pilot.log"
python scripts/item_checks.py locating \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir $D/locating-pilot \
  --workers 16 \
  &> artifacts/logs/item_checks_locating_pilot.log

echo "G5 on 20 fresh files from the 2,000-file set. Log: artifacts/logs/item_checks_locating_2000_seed1.log"
python scripts/item_checks.py locating \
  --files artifacts/explanation_set/ts.parquet \
  --outdir $D/locating-2000-seed1 \
  --workers 16 \
  --seed 1 \
  &> artifacts/logs/item_checks_locating_2000_seed1.log

echo "Done. Reports: $D/locating-pilot/report.json, $D/locating-2000-seed1/report.json"
