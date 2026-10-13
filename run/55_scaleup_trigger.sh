#!/bin/bash
# Seed-0 scale-up, step 6 of 6: the planted triggers (paper Sections 4.2 and 5.2) on 250 backdoor-fired files per
# trigger (the pilot had 50): explain the triggered and clean files with each poisoned GBDT (KernelSHAP at 32,768
# coalitions dominates), then the pullback (trigger recovery) and pushforward (ground truth) metrics. Independent of
# steps 1-5. The content trigger fires on 548 of the 1,000 candidates, so 250 is within reach. Expect about 1-1.5 h (each trigger first
# triggers and scores all 1,000 candidates, about 10 min).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for POISON in struct content-marker; do
  echo "Step 6/6: trigger $POISON, 250 files (16 workers)."
  echo "Output: artifacts/experiments/trigger-scaleup250/$POISON/"
  echo "Logs:   artifacts/logs/trigger_{explain,tables}-scaleup250-$POISON.log"
  OMP_NUM_THREADS=1 python scripts/trigger_explain.py \
    --poison "artifacts/poison/$POISON" \
    --num_files 250 \
    --kernelshap_samples 32768 \
    --outdir artifacts/experiments/trigger-scaleup250 \
    --num_workers 16 \
    &> "artifacts/logs/trigger_explain-scaleup250-$POISON.log"
  OMP_NUM_THREADS=1 python scripts/trigger_tables.py \
    --poison "artifacts/poison/$POISON" \
    --outdir artifacts/experiments/trigger-scaleup250 \
    --num_workers 16 \
    &> "artifacts/logs/trigger_tables-scaleup250-$POISON.log"
done
echo "Done. Tables: tail -n 60 artifacts/logs/trigger_tables-scaleup250-*.log"
