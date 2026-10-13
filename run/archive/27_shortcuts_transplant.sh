#!/bin/bash
# 3-B (docs/archive/shortcuts_plan.md): the transplant test. In 200 held-out malware (the files of run 24), write each of the
# top 20 pullback candidates into the bytes the file's own P assigns to its top feature (random bytes in the same place
# are the control), and append each of the top 20 mined 4-grams (run 25; the only placement without P).
# First run without --mined (2.1 min on 16 workers); this is the run with the mined 4-grams.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/shortcuts_transplant-seed0-gbdt.log
echo "3-B transplant: 200 held-out malware, 20 pullback candidates + 20 mined 4-grams (16 workers, about 3 min)."
echo "Output: artifacts/experiments/shortcuts_transplant/seed-0/gbdt/"
echo "Log:    $LOG   (the per-candidate summary is at its end)"
OMP_NUM_THREADS=1 python scripts/shortcuts_transplant.py \
  --seed 0 \
  --mined artifacts/experiments/shortcuts_train/seed-0/mined.parquet \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 45 $LOG"
