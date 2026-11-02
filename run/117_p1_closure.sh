#!/bin/bash
# P1, closure of the population (docs/formalization.md Section 9; review R2): G7 (run 107) re-run with the precondition
# evaluated on every edited file whose original passes it (catalogue_checks.py's `precondition_after` column; report
# keys `leaving_population` per operation and `closed`). The guarantee covers a file only while it passes the
# precondition, so an edit that takes a passing file to a failing one would break it.
# Pilot (Claude, 2026-11-02, artifacts/experiments/catalogue_checks/pilot-p1, 189 s): 0 of 3,188 edits on passing files
# leave the population, under all twelve operations; G7 still passes.
# Hypothesis: closed on the 2,000 files too (0 edits leaving the population); G7 passes as in run 107.
# Estimate: ~35 min (run 107's G7 took 25 min; the extra precondition per edit costs ~1.4x on the pilot).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

echo "G7 + P1 on the 2,000-file set (~35 min). Log: artifacts/logs/catalogue_checks_2000_p1.log"
python scripts/catalogue_checks.py \
  --files artifacts/explanation_set/ts.parquet \
  --directions artifacts/experiments/a_directions_derived_sums_2000_v3/directions_sums.csv \
  --outdir artifacts/experiments/catalogue_checks/2000-p1 \
  --workers 16 \
  &> artifacts/logs/catalogue_checks_2000_p1.log

tail -2 artifacts/logs/catalogue_checks_2000_p1.log
echo "Done. Report: artifacts/experiments/catalogue_checks/2000-p1/report.json (keys: closed, <op>.leaving_population)"
