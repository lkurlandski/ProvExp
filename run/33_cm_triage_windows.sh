#!/bin/bash
# 3-A, the realistic alternative for the triage (PLAN.md, 3-A (a)): the same split and deletions as run 32 with 256
# windows as units, on the 50 GBDT-flagged disagreements (where the byte-level validation is clean). The GBDT's window
# evidence is its pullback summed per window (isolates resolution), then its occlusion (no P: 256 extractions per
# file). Hypothesis: the oppose and agree bytes interleave within the first 1 KB, so windows merge them and deleting
# the window-level "oppose" set no longer makes MalConv flag selectively.
# Smoke test (occlusion): 4 files in 8 min on 4 workers. Expect about 3 min (pullback) + 15-20 min (occlusion).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for SOURCE in pullback occlusion; do
  LOG=artifacts/logs/cm_triage-seed0-zeros-w256-$SOURCE.log
  echo "Triage at 256 windows, the GBDT's window evidence from its $SOURCE (50 files, 32 workers)."
  echo "Output: artifacts/experiments/cm_triage/seed-0/zeros-w256-$SOURCE/"
  echo "Log:    $LOG   (the summary is at its end)"
  CUDA_VISIBLE_DEVICES=3 OMP_NUM_THREADS=1 python scripts/cm_triage.py \
    --seed 0 \
    --windows 256 \
    --gbdt_windows "$SOURCE" \
    --cells benign_gbdt_only malware_gbdt_only \
    --num_workers 16 \
    &> "$LOG"
done

echo "Done. Compare with the byte-level run: sed -n '/files ok/,/Where A/p' artifacts/logs/cm_triage-seed0-{zeros,zeros-w256-pullback,zeros-w256-occlusion}.log"
