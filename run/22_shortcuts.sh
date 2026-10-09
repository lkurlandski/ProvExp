#!/bin/bash
# 3-B (docs/shortcuts_plan.md): the byte patterns the GBDT keys on, via the pullback of interventional TreeSHAP, on the
# 2,000-file explanation set: the top 256 credited bytes per file, split into spans that share a top feature, grouped
# by feature and content across files. Benign-pushing patterns (the focus), then malware-pushing ones (secondary).
# Smoke test: the 100 pilot files in 15 s on 16 workers. Expect a few minutes per direction on 32 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for DIRECTION in benign malware; do
  LOG=artifacts/logs/shortcuts-seed0-treeshap_interventional-$DIRECTION.log
  echo "3-B, $DIRECTION-pushing patterns, 2,000 files (32 workers, a few minutes)."
  echo "Output: artifacts/experiments/shortcuts/seed-0/treeshap_interventional-$DIRECTION/"
  echo "Log:    $LOG   (the top patterns are at its end)"
  OMP_NUM_THREADS=1 python scripts/shortcuts.py \
    --seed 0 \
    --explainer treeshap_interventional \
    --direction "$DIRECTION" \
    --num_workers 32 \
    &> "$LOG"
done

echo "Done. Top patterns: tail -n 120 artifacts/logs/shortcuts-seed0-treeshap_interventional-benign.log"
