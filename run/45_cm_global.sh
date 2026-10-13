#!/bin/bash
# 3-C revised, the global comparison (docs/audit_plan.md): MalConv's per-byte IG (run 39) pushed forward into the
# EMBER features of all 2,000 explanation-set files, then both detectors' global reliance (mean |attribution| and mean
# signed) compared feature by feature against the GBDT's interventional TreeSHAP. Needs run 39. Replaces Appendix F.
# Took 7 min for the push on 16 workers; compare is seconds. 2,214 of 2,568 features are aggregates (no locatable bytes).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/cm_global-seed0.log
echo "3-C global comparison: push MalConv's IG forward (2,000 files, 16 workers, about 7 min), then compare."
echo "Output: artifacts/experiments/cm_global/seed-0/"
echo "Log:    $LOG   (the top features of each detector and the rank correlations are at its end)"
{
  OMP_NUM_THREADS=1 python scripts/cm_global.py --seed 0 --phase push --num_workers 16
  python scripts/cm_global.py --seed 0 --phase compare
} &> "$LOG"

echo "Done. Summary: tail -n 60 $LOG"
