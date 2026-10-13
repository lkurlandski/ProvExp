#!/bin/bash
# 3-C revised (docs/experiments/audit.md), confirmation: 3-B's transplant scored by MalConv. In 200 held-out malware, write
# each of the top 20 candidates (in >= 10 files) at the bytes the file's own P assigns to its feature, against random
# bytes in the same place. First the pushforward's candidates (the go/no-go), then the surrogate's (the mock's
# "unconfirmed" column). Needs run 40.
# Took 2 min on 16 workers (about 1 min per source).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for source in malconv surrogate; do
  LOG=artifacts/logs/audit_transplant-seed0-$source.log
  echo "3-C transplant ($source candidates, scored by MalConv): 200 malware, 20 candidates (16 workers)."
  echo "Output: artifacts/experiments/shortcuts_transplant/seed-0/malconv-$source/"
  echo "Log:    $LOG   (the per-candidate summary is at its end)"
  OMP_NUM_THREADS=1 python scripts/shortcuts_transplant.py \
    --seed 0 \
    --scorer malconv \
    --patterns artifacts/experiments/audit_discover/seed-0/$source-benign/patterns.parquet \
    --tag malconv-$source \
    --num_workers 16 \
    &> "$LOG"
done

echo "Done. Summaries: tail -n 30 artifacts/logs/audit_transplant-seed0-*.log"
