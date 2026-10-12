#!/bin/bash
# 3-B (docs/shortcuts_plan.md): over the 2,000-file explanation set, the credit toward benign of the top 20 pullback
# candidates (at their feature's bytes, and at any occurrence) and of the top 20 mined 4-grams (run 25; at any
# occurrence), and the features each candidate's bytes carry (the input to mitigation, run 28).
# First run without --mined (4.0 min on 16 workers); this is the run with the mined 4-grams.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/shortcuts_reliance-seed0.log
echo "3-B reliance: 2,000 explanation-set files, pullback candidates and mined 4-grams (16 workers, about 4 min)."
echo "Output: artifacts/experiments/shortcuts_reliance/seed-0/"
echo "Log:    $LOG"
OMP_NUM_THREADS=1 python scripts/shortcuts_reliance.py \
  --seed 0 \
  --mined artifacts/experiments/shortcuts_train/seed-0/mined.parquet \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: grep -A 45 '^Best-occ' $LOG"
