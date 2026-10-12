#!/bin/bash
# 3-A first check (PLAN.md, 3-A): do the GBDT and MalConv rely on the same bytes, and does the answer change at byte
# level, which only the pullback makes affordable for the GBDT? Reuses PB1's 100 pilot files, operator, and GBDT
# occlusion scores (run 21); MalConv IG and occlusion on one GPU, then agreement and cross-deletion on the CPU.
# Smoke test: 6 files in 2.5 min on 6 workers (a 4 MB file takes about 2 min alone). Expect about 10 min.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/cm_check-seed0.log

echo "3-A check: 100 pilot files, MalConv on GPU 1, then 16 workers (about 10 min)."
echo "Output: artifacts/experiments/cm_check/seed-0/"
echo "Log:    $LOG   (the summary tables are at its end)"
CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=1 python scripts/cm_check.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 50 $LOG"
