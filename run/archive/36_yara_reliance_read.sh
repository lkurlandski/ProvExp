#!/bin/bash
# 3-C reliance, the stricter reference (docs/rules_plan.md): run 35 again (its numbers unchanged), plus random sets
# drawn only from bytes whose provenance is as concentrated as the matched bytes', and the signed credit. For run 34's split rules, the GBDT's |TreeSHAP| pulled back onto each
# rule's matched bytes vs. 200 random byte sets with the same run lengths, and the determined features' credit on files
# where the rule fires vs. not. Needs run 34's output.
# Supersedes run 35's output (same directory).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/yara_reliance-seed0.log

echo "Reliance on rule matches, pilot files, 16 workers (about 1-2 min)."
echo "Output: artifacts/experiments/yara_reliance/seed-0/"
echo "Log:    $LOG   (the go/no-go is at its end)"
OMP_NUM_THREADS=1 python scripts/yara_reliance.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Results: sed -n '/^## Reliance/,\$p' $LOG"
