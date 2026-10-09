#!/bin/bash
# PF1 (docs/pf1_plan.md): the pushforward's faithfulness by feature-space deletion of the GBDT, on the window scores
# saved by run/17_pf1_window_scores.sh. About 12 s per file on the smoke test, so a few minutes on 8 workers.
# Run only after the checks in docs/status.md ("When run 17 finishes") pass.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
LOG=artifacts/logs/pf1-seed0-baselines-scores.log
echo "PF1: feature-space deletion of every method on the window scores of $RUN (8 workers, a few minutes)."
echo "Output: artifacts/experiments/pf1/seed-0/$(basename $RUN)/"
echo "Log:    $LOG   (the tables are at its end)"

OMP_NUM_THREADS=1 python scripts/pf1.py \
  --run "$RUN" \
  --num_workers 8 \
  &> "$LOG"

echo "Done. Tables: tail -n 120 $LOG"
