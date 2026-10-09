#!/bin/bash
# 3-B correctness spot-check (docs/shortcuts_plan.md): set a benign-pushing header field (run 22) to its flagged value
# in 200 held-out malware, through the real bytes -> parser -> feature path, and confirm the GBDT moves toward benign;
# a random value of the same width is the control. Validity check that the named bytes drive the feature, not an
# attack. Smoke test: 5 files in 4 s. Expect a few minutes on 16 workers (shard iteration dominates).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/shortcuts_setfield-seed0.log
echo "3-B set-field spot-check, 200 held-out malware files (16 workers, a few minutes)."
echo "Output: artifacts/experiments/shortcuts_setfield/seed-0/"
echo "Log:    $LOG   (the per-field summary is at its end)"
OMP_NUM_THREADS=1 python scripts/shortcuts_setfield.py \
  --seed 0 \
  --num_files 200 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 20 $LOG"
