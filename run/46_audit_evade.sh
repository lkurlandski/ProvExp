#!/bin/bash
# 3-C revised, the combined effect (docs/audit_plan.md): in 200 held-out malware, scramble together the features each
# source confirmed in run 44 (pushforward; surrogate; their union) and, as the null, as many random locatable fields,
# then measure MalConv's drop and its evasion at the 1% FPR threshold. Needs run 44.
# Smoke test: 24 malware x 4 recipes in 10 s on 8 workers. Expected: about 2-3 min on 16 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_evade-seed0.log
echo "3-C evade: 200 malware, 4 recipes scrambled together, scored by MalConv (16 workers, about 2-3 min)."
echo "Output: artifacts/experiments/audit_evade/seed-0/"
echo "Log:    $LOG   (the per-recipe drop and evasion are at its end)"
OMP_NUM_THREADS=1 python scripts/audit_evade.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 20 $LOG"
