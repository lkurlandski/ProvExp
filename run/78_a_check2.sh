#!/bin/bash
# Direction A, go/no-go check 2 (docs/direction-A-mock.md): does Gimenez et al.'s perturbation-vector (PV) feature
# selection leave a hole that feature provenance (C4) predicts? FOR ACADEMIC SECURITY RESEARCH ONLY: this reproduces
# published black-box attacks against our own detector, on our own pilot samples, solely to evaluate a defense.
#
#   1. a_pv_attacks.py: run the eight secml-malware attacks (Gimenez et al.'s set, low budget: population 10, 10
#      iterations) on the 50 detected pilot malware against our GBDT, re-extract with the quirk-fixed extractor, and
#      record the perturbation vectors. ~400 attack runs; gamma_api dominates (~45 s/file). ~12 min on 12 workers.
#   2. a_pv_hole.py: PV-kept = features never decreased in the sample; C4-decreasable from run 76; the hole is their
#      intersection, weighted by the GBDT's split gain. Writes the PV-selected GBDT's train files (pv.*).
#   3. (decisive gain share) train the PV-selected monotone GBDT on the full splits, then re-run a_pv_hole.py against
#      it. The step-2 read uses the unconstrained GBDT as a preview.
#
# Hypothesis (docs/direction-A-threat-model.md): the hole is large and carries well over 5% of the PV GBDT's gain,
# concentrated in signed section buckets and import features no secml attack lowers. GO if >= 5%.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

D=artifacts/experiments/a_pv
LOG=artifacts/logs/a_pv_attacks-seed0.log

echo "Step 1/3: eight attacks on 50 pilot malware (~12 min, 12 workers). Log: $LOG"
python scripts/a_pv_attacks.py \
  --outdir "$D" \
  --num_workers 12 \
  --seed 0 \
  &> "$LOG"

echo "Step 2/3: PV hole, previewed against the unconstrained GBDT."
python scripts/a_pv_hole.py \
  --deltas "$D/deltas.parquet" \
  --directions_dir artifacts/experiments/a_directions \
  --outdir "$D"

echo "Step 3/3: train the PV-selected monotone GBDT, then re-read the hole against it."
LOG2=artifacts/logs/train_classic-gbdt-0-pv.log
echo "  training (full splits, ~6 min). Log: $LOG2"
python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads 16 \
  --suffix=-pv \
  --neutralize "$D/pv.neutralize.txt" \
  --monotone "$D/pv.monotone.tsv" \
  &> "$LOG2"
python scripts/a_pv_hole.py \
  --deltas "$D/deltas.parquet" \
  --directions_dir artifacts/experiments/a_directions \
  --model artifacts/models/gbdt/seed-0-pv/model.txt \
  --outdir "$D"

echo "Done. Hole report: $D/report.json ; hole features: $D/hole.csv"
