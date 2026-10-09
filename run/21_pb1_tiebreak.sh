#!/bin/bash
# PB1's curves again, with rankings that break ties by a seeded random permutation instead of by position in the file
# (2026-10-09; docs/pb1_baselines.md, "Tie-break re-run"). At 1,024 and 4,096 windows most occlusion windows score
# exactly 0, so position decided a large part of occlusion's curves. Pass 1 (the occlusion sweep and KernelSHAP over
# windows) is reused from run/17, which only changes pass 2; with --tiebreak position this reproduces run 17's curves
# exactly (checked on 6 files). Expect about 15-25 min on 32 workers (one 4 MB file takes about 10 min alone).
# Run in tmux.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

REUSE=artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
LOG=artifacts/logs/faithfulness-seed0-zeros-typical-baselines-ties.log
TABLES=artifacts/reports/pb1_tables-baselines-ties.md

echo "Step 1/2: PB1 curves with random tie-breaks, pass 1 reused from $REUSE (32 workers, about 15-25 min)."
echo "Output: artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-ties/"
echo "Log:    $LOG"
OMP_NUM_THREADS=1 python scripts/faithfulness.py \
  --seed 0 \
  --num_files 100 \
  --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
  --header typical \
  --sweep_windows 64 1024 4096 \
  --kernelshap_samples 2048 \
  --timeout 28800 \
  --tiebreak random \
  --reuse_scores "$REUSE" \
  --tag baselines-ties \
  --num_workers 32 \
  &> "$LOG"

echo "Step 2/2: the PB1 tables."
echo "Tables: $TABLES"
python scripts/pb1_tables.py \
  --fill zeros-typical-header-baselines-ties \
  > "$TABLES"

echo "Done. Compare $TABLES with artifacts/reports/pb1_tables-baselines.md"
