#!/bin/bash
# Derivation step 9: Table A1's C4 rows from the directions after step 6 (G7) and the new body regions (run 104).
# FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et al.'s published secml-malware attacks and our C1-declared search,
# against our own detectors, on our own pilot samples, to evaluate defenses (as runs 99-100).
#   0. the derived directions on the pilot (as run 99), for the full store (merged imports: `-pre-quirkfixed`) and in
#      the sums store's layout (`-pre`, `-pre-control`);
#   1. retrain the six C4 models of run 99 into `-v2` suffixes: on the re-featurized 10% sums store
#      (ember2024-sums-10-v2, run 104) and on the full store;
#   2. Table A1's toolkit columns with the routed v2 C4 rows (as run 100 step 1). The reference and PV-seen rows are run
#      81's models: they drop the re-encoded groups, whose features are the only ones run 104 changed;
#   3. the C1-declared adaptive search against the thrember-space defenses (as run 100 step 2), now on the C1 engine
#      (scripts/a1_adaptive.py, engine_predictors; the hand predictors are its test oracle). Its declared add-section
#      ends the file, so an old overlay no longer counts as the overlay (G7, finding 4).
# Step 0 (Claude, 2026-10-29, ~50 s each with 8 workers): the training inputs differ from run 99's in exactly two
# features, in both stores: section:overlay_size dropped under every threat model (was up: a section added after the
# overlay removes it), datadirectories:security_virtual_address up under M_add (was fixed: a section placed before the
# overlay moves the certificate table).
# Hypothesis: test metrics within noise of run 99 (one feature of little gain dropped, one added); the toolkit and
# adaptive columns as in run 100 (routed rows evaded by no seen attack on passing files, the M_full rows by no held-out
# one; the adaptive C4 rows 0 by construction).
#
# Estimate: training ~20 min (run 99); the toolkit columns ~2.4 h (run 100); the adaptive search ~20 min: ~3 h in all.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

S=artifacts/experiments/a_directions_derived_sums_v2
D=artifacts/experiments/a_directions_derived_v2
F=artifacts/features/ember2024-sums-10-v2
M=artifacts/models/gbdt

echo "Step 0: the derived directions (pilot) into $D and $S. Logs: artifacts/logs/a_directions_derived_v2.log," \
  "artifacts/logs/a_directions_derived_sums_v2.log"
python scripts/a_directions.py \
  --outdir $D \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_v2.log
python scripts/a_directions.py \
  --extractor sums \
  --outdir $S \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_sums_v2.log

train() {  # suffix, then extra arguments
  local suffix=$1; shift
  local log=artifacts/logs/train_classic-gbdt-0$suffix.log
  echo "Step 1: training gbdt/seed-0$suffix. Log: $log"
  python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --suffix="$suffix" \
    "$@" \
    &> "$log"
}
train -s10-madd-feat-pre-v2  --features $F --neutralize $S/M_add-pre-control.neutralize.txt  --monotone $S/M_add-pre-control.monotone.tsv
train -s10-madd-sums-pre-v2  --features $F --neutralize $S/M_add-pre.neutralize.txt          --monotone $S/M_add-pre.monotone.tsv
train -s10-mfull-feat-pre-v2 --features $F --neutralize $S/M_full-pre-control.neutralize.txt --monotone $S/M_full-pre-control.monotone.tsv
train -s10-mfull-sums-pre-v2 --features $F --neutralize $S/M_full-pre.neutralize.txt         --monotone $S/M_full-pre.monotone.tsv
train -a-madd-pre-qf-v2      --neutralize $D/M_add-pre-quirkfixed.neutralize.txt  --monotone $D/M_add-pre-quirkfixed.monotone.tsv
train -a-mfull-pre-qf-v2     --neutralize $D/M_full-pre-quirkfixed.neutralize.txt --monotone $D/M_full-pre-quirkfixed.monotone.tsv

echo "Test metrics (ROC-AUC, TPR at 1% and 0.1% FPR), run 99's models first:"
for s in -s10-madd-feat-pre -s10-madd-sums-pre -s10-mfull-feat-pre -s10-mfull-sums-pre -a-madd-pre-qf -a-mfull-pre-qf; do
  for v in "" -v2; do
    python -c "
import json, sys
import numpy as np, polars as pl
from sklearn.metrics import roc_curve
d = sys.argv[1]
m = json.load(open(d + '/metrics.json'))
p = pl.read_parquet(d + '/ts_predictions.parquet')
fpr, tpr, _ = roc_curve(p['label'].to_numpy(), p['prob'].to_numpy())
print(sys.argv[2], round(m['ts_metrics']['roc'], 5), *[round(float(np.interp(f, fpr, tpr)), 4) for f in (0.01, 0.001)])
" $M/seed-0$s$v "$s$v"
  done
done

export OMP_NUM_THREADS=1

LOG=artifacts/logs/a1_evaluate_v2.log
echo "Step 2: eight attacks x six defenses (four routed) on the pilot malware. Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir artifacts/experiments/a1/toolkit-v2 \
  --features $F \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense madd-feat=$M/seed-0-s10-madd-feat-pre-v2 \
  --defense madd-sums=$M/seed-0-s10-madd-sums-pre-v2 \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat-pre-v2 \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums-pre-v2 \
  --route madd-feat=ref \
  --route madd-sums=ref \
  --route mfull-feat=ref \
  --route mfull-sums=ref \
  --num_workers 16 \
  --seed 0 \
  &> "$LOG"

LOG=artifacts/logs/a1_adaptive_v2.log
echo "Step 3: the C1-declared adaptive search (C1 engine) with the v2 models. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive-v2 \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense unconstrained=$M/seed-0 \
  --defense pv=$M/seed-0-pv \
  --defense madd-feat=$M/seed-0-a-madd-pre-qf-v2 \
  --defense mfull-feat=$M/seed-0-a-mfull-pre-qf-v2 \
  --sound madd-feat mfull-feat \
  --queries 100 \
  --seed 0 \
  &> "$LOG"

echo "Done. Toolkit table: artifacts/experiments/a1/toolkit-v2/table.json"
echo "      Adaptive: artifacts/experiments/a1/adaptive-v2/adaptive.json"
