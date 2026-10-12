#!/bin/bash
# 3-B mitigation (docs/shortcuts_plan.md): neutralize the features carried by the confirmed artifact candidates (runs
# 26, 27; the rule is in scripts/shortcuts_tables.py), retrain the GBDT, and re-run the transplant test against it.
# Ran 2026-10-12: 6 features; training 3 min on every core; transplant 2 min on 16 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LIST=artifacts/experiments/shortcuts_mitigation/seed-0/neutralize.txt
echo "3-B mitigation: the features to neutralize -> $LIST"
python scripts/shortcuts_tables.py \
  --seed 0 \
  --write_neutralize "$LIST" \
  > /dev/null

LOG=artifacts/logs/train_classic-gbdt-0-neutral.log
echo "Retraining the GBDT without them (every core, about 3 min). Log: $LOG"
python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --neutralize "$LIST" \
  --suffix=-neutral \
  &> "$LOG"

LOG=artifacts/logs/shortcuts_transplant-seed0-neutral.log
echo "Transplant test against the mitigated GBDT (16 workers, about 2 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/shortcuts_transplant.py \
  --seed 0 \
  --model artifacts/models/gbdt/seed-0-neutral/model.txt \
  --tag neutral \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Tables: python scripts/shortcuts_tables.py --seed 0"
