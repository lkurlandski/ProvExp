#!/bin/bash
# 3-C revised (docs/audit_plan.md): per file, MalConv's IG pushed forward into the EMBER features (the method) and the
# surrogate's TreeSHAP (the alternative); the top 20 features by benign credit, keyed by (feature, content) and grouped
# across the 2,000 files. Needs runs 38 and 39.
# Smoke test: 6 files in 10 s on 6 workers. Expected: about 10 min on 32 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_discover-seed0.log
echo "3-C discovery: 2,000 files, MalConv pushed forward and the surrogate (32 workers, about 10 min)."
echo "Output: artifacts/experiments/audit_discover/seed-0/{malconv,surrogate}-benign/"
echo "Log:    $LOG   (the top patterns of each source are at its end)"
OMP_NUM_THREADS=1 python scripts/audit_discover.py \
  --seed 0 \
  --phase discover \
  --num_workers 32 \
  &> "$LOG"

echo "Done. Summary: tail -n 100 $LOG"
