#!/bin/bash
# 3-A, the shared attack surface (PLAN.md, 3-A): the bytes in both models' top 1% / 5% (GBDT pullback, MalConv IG),
# deleted against exclusive and random sets of the same size, with where they lie and which GBDT features they carry.
# Also the paired cross-deletion tables of run 30. Smoke test: 6 files in about 2 min on 6 workers. Expect ~6 min.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/cm_shared-seed0.log
TABLES=artifacts/reports/cm_tables.md

echo "Step 1/2: run 30's cross-deletion, paired by file."
echo "Tables: $TABLES"
python scripts/cm_tables.py \
  --run artifacts/experiments/cm_check/seed-0 \
  > "$TABLES"

echo "Step 2/2: shared bytes on 100 pilot files, MalConv on GPU 1, then 16 workers (about 6 min)."
echo "Output: artifacts/experiments/cm_shared/seed-0/"
echo "Log:    $LOG   (the summary is at its end)"
CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=1 python scripts/cm_shared.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: sed -n '/^## q/,\$p' $LOG"
