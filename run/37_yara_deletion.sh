#!/bin/bash
# 3-C deletion check (docs/rules_plan.md): delete each rule's matched bytes (run 34's split rules, plus the crypto rules
# as representation-gap controls) with PB1's operator, against 20 concentration-matched reference sets (run 36's
# reference), and compare the GBDT's response with run 36's attribution-based categories. Needs runs 34 and 36.
# Smoke test: 4 files, 336 deletions in 113 s on 4 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/yara_deletion-seed0.log

echo "Deletion check on the pilot files, 32 workers (about 5-10 min)."
echo "Output: artifacts/experiments/yara_deletion/seed-0/"
echo "Log:    $LOG   (the check is at its end)"
OMP_NUM_THREADS=1 python scripts/yara_deletion.py \
  --seed 0 \
  --num_workers 32 \
  &> "$LOG"

echo "Done. Results: sed -n '/^## Deletion/,\$p' $LOG"
