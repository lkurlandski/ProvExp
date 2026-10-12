#!/bin/bash
# 3-C go/no-go (PLAN.md, 3-C): generic YARA rules (Yara-Rules packers/, crypto/, antidebug_antivm/, capabilities/) on
# PB1's 100 pilot files; for each rule's matched bytes S, the features S computes (P^T 1_S), the pushforward's profile,
# and the GBDT's TreeSHAP credit S carries. Needs yara-python and the rules (README.md, "External tools for 3-C").
# Smoke test: 6 files in 37 s on 6 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/yara_check-seed0.log

echo "YARA go/no-go on 100 pilot files, 16 workers (a few minutes)."
echo "Output: artifacts/experiments/yara_check/seed-0/"
echo "Log:    $LOG   (the go/no-go is at its end)"
OMP_NUM_THREADS=1 python scripts/yara_check.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Go/no-go: sed -n '/^## Coverage/,\$p' $LOG"
