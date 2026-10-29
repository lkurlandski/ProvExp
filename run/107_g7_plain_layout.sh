#!/bin/bash
# Derivation step 6 (G7) after run 104's findings: the precondition check also requires a plain layout
# (catalogue.plain_layout, decided by the user 2026-10-29): every section's virtual range within SizeOfImage,
# SizeOfImage at most what the sections need, headers that hold only the headers, and pefile's overlay starting where a
# section's raw data ends. G7's own edits now keep low-alignment images loader-safe (an added section's raw offset
# equals its virtual address; the gap insertions do not apply to them).
#   1. the derivation on the 2,000-file set with the new precondition (as run 104 step 3; ~10 min);
#   2. G7 on the 2,000-file set against step 1's directions (run 104 step 4 took 25 min).
# Smoke (Claude, 2026-10-29): the 11 files run 104 flagged pass G7 with run 104's directions (26 s); the clauses exclude
# 74 of the 2,000 files, 8 of the 1,682 that passed before; the pilot derivation's training inputs are byte-identical
# to the v2 ones (88 pilot files pass, as before), so run 105's inputs are unchanged.
# Hypothesis: G7 passes on every edit, strict and precondition variants; the derivation's training inputs equal the
# pilot's (a_directions_derived_sums_v2).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

D=artifacts/experiments/a_directions_derived_sums_2000_v3

echo "Derive the directions (with sums) on the 2,000-file set into $D. Log: artifacts/logs/a_directions_derived_sums_2000_v3.log"
python scripts/a_directions.py \
  --extractor sums \
  --files artifacts/explanation_set/ts.parquet \
  --outdir $D \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_sums_2000_v3.log

echo "G7 on the 2,000-file set. Log: artifacts/logs/catalogue_checks_2000_v3.log"
python scripts/catalogue_checks.py \
  --files artifacts/explanation_set/ts.parquet \
  --directions $D/directions_sums.csv \
  --outdir artifacts/experiments/catalogue_checks/2000-v3 \
  --workers 16 \
  &> artifacts/logs/catalogue_checks_2000_v3.log

echo "Training inputs against the pilot's (no output: identical):"
for f in $(cd artifacts/experiments/a_directions_derived_sums_v2 && ls M_*-pre*.*); do
  cmp artifacts/experiments/a_directions_derived_sums_v2/$f $D/$f || true
done

echo "Done. Report: artifacts/experiments/catalogue_checks/2000-v3/report.json"
