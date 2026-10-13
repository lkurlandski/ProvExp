#!/bin/bash
# 3-C revised, the combined effect (docs/experiments/audit.md): in 200 held-out malware, scramble together the features each
# source confirmed in run 44 (pushforward; surrogate; their union) and, as the null, as many random locatable fields,
# then measure MalConv's drop and its evasion at the 1% FPR threshold. Needs run 44.
# Took 35 s on 16 workers (191 of 200 malware scored).
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
