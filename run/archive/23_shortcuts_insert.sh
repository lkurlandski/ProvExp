#!/bin/bash
# 3-B insertion test (docs/archive/shortcuts_plan.md), content increment: append the top benign-pushing string patterns
# (run/22) to held-out test malware the GBDT calls malware, verify the file still parses, re-extract and re-score,
# and compare the drop in the malware log-odds against random bytes of the same length. 200 files, 20 patterns.
# Smoke test: 3 files in 6 s. Expect a few minutes on 16 workers (shard iteration dominates).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/shortcuts_insert-seed0-treeshap_interventional.log
echo "3-B insertion test, strings, 200 held-out malware files (16 workers, a few minutes)."
echo "Output: artifacts/experiments/shortcuts_insert/seed-0/treeshap_interventional/"
echo "Log:    $LOG   (the per-pattern summary is at its end)"
OMP_NUM_THREADS=1 python scripts/shortcuts_insert.py \
  --seed 0 \
  --explainer treeshap_interventional \
  --direction benign \
  --groups strings \
  --num_patterns 20 \
  --min_files 10 \
  --num_files 200 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 40 $LOG"
