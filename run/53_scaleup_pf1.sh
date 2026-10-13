#!/bin/bash
# Seed-0 scale-up to 500 files, step 4 of 6: pushforward faithfulness (paper Section 5.1) on step 2's window scores,
# its resolution trend (64 windows to bytes; Table 2), and the instrumented-vs-black-box comparison of P. Needs step 2.
# pf1_resolution needs up to about 4.4 GB per worker on the largest files (about 70 GB at 16 workers).
# Expect about 50 min + 1.25 h + seconds.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-scaleup500
LOG_PF1=artifacts/logs/pf1-seed0-scaleup500.log
LOG_RES=artifacts/logs/pf1_resolution-seed0-scaleup500.log
REPORT=artifacts/reports/cp_blackbox-scaleup500.md

echo "Step 4/6 (a): pushforward faithfulness on $RUN (16 workers, about 50 min)."
echo "Output: artifacts/experiments/pf1/seed-0/zeros-typical-header-scaleup500/"
echo "Log:    $LOG_PF1"
OMP_NUM_THREADS=1 python scripts/pf1.py \
  --run "$RUN" \
  --num_workers 16 \
  &> "$LOG_PF1"

echo "Step 4/6 (b): the resolution trend, 64 windows to bytes (16 workers, about 1.25 h, up to ~70 GB of memory)."
echo "Output: artifacts/experiments/pf1/seed-0/zeros-typical-header-scaleup500/resolution/"
echo "Log:    $LOG_RES"
OMP_NUM_THREADS=1 python scripts/pf1_resolution.py \
  --run "$RUN" \
  --num_workers 16 \
  &> "$LOG_RES"

echo "Step 4/6 (c): instrumented vs. black-box P at 256 windows (seconds)."
echo "Report: $REPORT"
python scripts/cp_blackbox.py \
  --run "$RUN" \
  > "$REPORT"
echo "Done. Tables: tail -n 120 $LOG_PF1; tail -n 80 $LOG_RES; $REPORT"
