#!/bin/bash
# PF1 (docs/experiments/pf1.md): the pushforward's faithfulness by feature-space deletion of the GBDT, on the window scores
# saved by run/17_pf1_window_scores.sh, with the resolution diagnostic (window round trips; added 2026-10-09).
# The first run (without the diagnostic) took 6 min on 8 workers; with it, about 10 min on 16.
# Run only after the checks in docs/status.md ("When run 17 finishes") pass. Re-run by run/20_pf1_resolution.sh after
# the tie fix in feature_order (2026-10-09).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
LOG=artifacts/logs/pf1-seed0-baselines-scores.log
echo "PF1: feature-space deletion of every method on the window scores of $RUN (16 workers, about 10 minutes)."
echo "Output: artifacts/experiments/pf1/seed-0/$(basename $RUN)/"
echo "Log:    $LOG   (the tables are at its end)"

OMP_NUM_THREADS=1 python scripts/pf1.py \
  --run "$RUN" \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Tables: tail -n 120 $LOG"
