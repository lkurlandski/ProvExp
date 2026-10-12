#!/bin/bash
# 3-C revised (docs/audit_plan.md), the realistic alternative: a LightGBM surrogate of MalConv (seed 0) on EMBER
# features, trained on the test files outside the explanation set to predict MalConv's log-odds, then interventional
# TreeSHAP on the 2,000 explanation-set files. Can run alongside run 39 (this uses CPUs, run 39 the GPUs).
# Took 2 min on 16 threads (training 79 s on 484,094 files, TreeSHAP 34 s). Fidelity: R^2 0.96 held out, 0.95 on
# the explanation set.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

LOG=artifacts/logs/audit_surrogate-seed0.log
echo "3-C surrogate: train on ~485k test files, TreeSHAP on 2,000 (16 threads, about 2 min)."
echo "Output: artifacts/experiments/audit_surrogate/seed-0/"
echo "Log:    $LOG   (the fidelity report is near its end)"
python scripts/audit_surrogate.py \
  --seed 0 \
  --num_threads 16 \
  &> "$LOG"

echo "Done. Summary: grep -v LightGBM $LOG | tail -n 30"
