#!/bin/bash
# 3-C revised, second framing (docs/audit_plan.md), the go/no-go: in 200 held-out malware, scramble the bytes P names
# for each of the top 20 features by malware evidence (MalConv pushed forward, and the surrogate), against random bytes
# elsewhere in the same MalConv windows; MalConv re-scores. The verdict is printed at the end. Needs run 43.
# Smoke test: 24 files x 40 candidates in 36 s on 8 workers. Expected: about 3-5 min on 16 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_scramble-seed0.log
echo "3-C scramble test: 200 malware, 20 candidates per source, scored by MalConv (16 workers, about 3-5 min)."
echo "Output: artifacts/experiments/audit_scramble/seed-0/"
echo "Log:    $LOG   (the per-candidate summary and the go/no-go are at its end)"
OMP_NUM_THREADS=1 python scripts/audit_scramble.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 50 $LOG"
