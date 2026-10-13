#!/bin/bash
# The planted-trigger testbed (PB2, PF2): poison 1% of the training malware, retrain, and validate, for both
# triggers. About 13 min + 3 min + a few minutes each.
#
# The trigger is written into the bytes and the features re-extracted, so the bytes, the provenance, and the model
# all see the same object. Only the poisoned rows are stored (about 200 MB), which train_classic.py --poison applies
# in memory; a copy of the training matrix would be 21 GB per trigger.
#
# Validation must show attack success >= 95%, clean ROC-AUC within 0.001 of 0.99759, and the trigger inert on the
# clean model. Outcome (docs/experiments/trigger.md, "Results"): struct passes everything; content-marker reaches 0.472,
# because a content trigger's effect scales with its share of the file.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OMP_NUM_THREADS=1 python scripts/trigger_poison.py --trigger struct --rate 0.01 --num_workers 16 \
  &> artifacts/logs/trigger_poison-struct.log
python scripts/train_classic.py --learner gbdt --seed 0 --poison artifacts/poison/struct \
  &> artifacts/logs/train_classic-gbdt-0-struct.log
OMP_NUM_THREADS=1 python scripts/trigger_validate.py --poison artifacts/poison/struct --num_files 500 --num_workers 16 \
  &> artifacts/logs/trigger_validate-struct.log

OMP_NUM_THREADS=1 python scripts/trigger_poison.py --trigger content --content marker --block_size 2048 --rate 0.01 --num_workers 16 \
  &> artifacts/logs/trigger_poison-content-marker.log
python scripts/train_classic.py --learner gbdt --seed 0 --poison artifacts/poison/content-marker \
  &> artifacts/logs/train_classic-gbdt-0-content-marker.log
OMP_NUM_THREADS=1 python scripts/trigger_validate.py --poison artifacts/poison/content-marker --num_files 500 --num_workers 16 \
  &> artifacts/logs/trigger_validate-content-marker.log
