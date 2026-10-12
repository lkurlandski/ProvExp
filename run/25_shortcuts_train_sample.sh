#!/bin/bash
# 3-B (docs/shortcuts_plan.md): on a training sample (50 random training shards, 50 benign + 50 malware files from
# each, 5,000 files), the prevalence by label of the top 100 benign-pushing discovery patterns at their feature's
# bytes, and the baseline without P: label-skewed byte 4-grams (exact document frequencies, ranked by chi-squared).
# Holds 16 GB of 4-gram counters in shared memory; reads about 55 GB of shards.
# Smoke test: 2 shards x 3 files per label in 1.5 min on 2 workers. Took 9.3 min on 16 workers (8.3 min of I/O).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/shortcuts_train_sample-seed0.log
echo "3-B training sample: 5,000 training files, pattern prevalence and mined 4-grams (16 workers, about 10 min)."
echo "Output: artifacts/experiments/shortcuts_train/seed-0/"
echo "Log:    $LOG   (prevalence and the top 4-grams are at its end)"
OMP_NUM_THREADS=1 python scripts/shortcuts_train_sample.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 90 $LOG"
