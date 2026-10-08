#!/bin/bash
# PB2 and PF2 at pilot scale: explain the triggered and clean files with each poisoned model, then the metrics.
# A few minutes per trigger (KernelSHAP at 32,768 coalitions dominates), well under an hour for both.
#
# KernelSHAP needs its full 32,768 coalitions. At 512 it put 0.1% of its attribution change on the trigger's
# features instead of 51%, which looks exactly like "KernelSHAP misses the trigger" but is only sampling noise.
#
# trigger_explain.py keeps the files where the backdoor actually fired (the model's output only, never an
# explanation). The struct trigger fires on all 1,000 candidates; the content trigger on a minority.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for poison in struct content-marker; do
  OMP_NUM_THREADS=1 python scripts/trigger_explain.py --poison "artifacts/poison/$poison" \
    --num_files 50 --kernelshap_samples 32768 --num_workers 16 \
    &> "artifacts/logs/trigger_explain-$poison.log"
  OMP_NUM_THREADS=1 python scripts/trigger_tables.py --poison "artifacts/poison/$poison" --num_workers 16 \
    &> "artifacts/logs/trigger_tables-$poison.log"
done
