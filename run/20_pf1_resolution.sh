#!/bin/bash
# PF1's resolution trend (docs/pf1_plan.md, "Resolution trend"), in two steps:
#   1. PF1 again (run/18_pf1.sh's command), because feature_order now treats near-ties from round-off as ties
#      (2026-10-09): features with identical provenance got their order from 1e-13 differences, not the seeded
#      tie-break. About 10 min on 16 workers.
#   2. The window round trips of every native explainer at 64 windows to the bytes, with their deletion curves and
#      P's statistics at each resolution. Smoke test: 4 files in 19 s; the largest file (4 MB) takes about 45 s per
#      explainer and 4.4 GB of memory. About 10-15 min on 16 workers.
# Run in tmux. Nothing else should be running (16 workers, up to about 70 GB of memory).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
LOG_PF1=artifacts/logs/pf1-seed0-baselines-scores.log
LOG_RES=artifacts/logs/pf1_resolution-seed0-baselines-scores.log

echo "Step 1/2: PF1 with the tie fix (16 workers, about 10 min)."
echo "Log:    $LOG_PF1"
OMP_NUM_THREADS=1 python scripts/pf1.py \
  --run "$RUN" \
  --num_workers 16 \
  &> "$LOG_PF1"

echo "Step 2/2: the resolution trend, 64 windows to bytes (16 workers, about 10-15 min)."
echo "Output: artifacts/experiments/pf1/seed-0/$(basename $RUN)/resolution/"
echo "Log:    $LOG_RES"
OMP_NUM_THREADS=1 python scripts/pf1_resolution.py \
  --run "$RUN" \
  --num_workers 16 \
  &> "$LOG_RES"

echo "Done. Tables: tail -n 80 $LOG_RES (and the end of $LOG_PF1)"
