#!/bin/bash
# R7, option 5 in its final form (user, session 53): the certificate and debug entries join the threat model and the
# population. Run 138 and the end-to-end check (R7 record §7) showed that the escape writes are loader-ignored writes
# to those two data-directory entries, outside the threat model, that move the entries' own features against the table
# (the debug write alone evades 3/40 and 4/41 monotone detections). Here:
#   0. the direction table derived with `--loose`: a new overwrite `ent` (both entries set to any value) in M_full, and
#      the population widened so that the data located through the two entries may lie past the end (lengthening the
#      file may then complete it). Without `--loose` the derivation reproduces a_directions_derived_sums_v2 exactly
#      (checked by Claude, 2026-11-13);
#   1. the two monotone M_full detectors retrained on the widened table, as run 105 trained the -v2 ones;
#   2. the detection cost: AUC and TPR at 1% and 0.1% FPR, -v2 against -loose.
#
# Step 0 (Claude, 2026-11-13, ~40 s): ten features become two-sided in both variants (authenticode:* seven,
# datadirectories:{security_size, debug_size, debug_virtual_address}), nothing else changes; the pilot's population
# grows from 88 to 89 of 100 files.
# Hypothesis: the ten freed features cost 0.3-1 point of TPR at 1% FPR and somewhat more at 0.1% (run 126 priced the
# signature and debug rewrites at 0.4 points each).
#
# Result (Claude, 2026-11-13, ~2.5 min): the hypothesis failed; the cost is about four times the prediction. TPR at 1%
# and 0.1% FPR (unconstrained 93.5%, 84.4%): features 87.2% -> 83.4% (-3.8), 71.0% -> 65.1% (-5.9); sums 89.6% ->
# 85.7% (-3.9), 74.8% -> 68.1% (-6.6); AUC 0.9922 -> 0.9890 and 0.9935 -> 0.9906. Split (scratch models, deleted
# after): freeing only the two debug features costs 87.2 -> 87.1 and 89.6 -> 89.0 at 1% (71.0 -> 68.8, 74.8 -> 73.9 at
# 0.1%), so the certificate entry carries nearly all of it. Why: with the certificate entry writable, the attacker can
# point it at an appended certificate (signature cloning), so the signature features must become two-sided, and
# signatures are a strong benign signal. One seed, pilot-scale table.
#
# Refreshed (Claude, 2026-11-13, run 142 step 0): the table in $S re-derived with LIEF's overlay rule
# (docs/evidence/r7-overlay-rule.md); three cells of the strict `ren` column change, every mask is byte-identical, so
# the -loose models trained here stand.
#
# Resources: NUM_WORKERS sets the derivation's workers and LightGBM's threads; ~1 min per model with 16.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"

S=artifacts/experiments/a_directions_derived_sums_loose
F=artifacts/features/ember2024-sums-10-v2
M=artifacts/models/gbdt
mkdir -p artifacts/logs

echo "Step 0: the widened direction table into $S. Log: artifacts/logs/a_directions_derived_sums_loose.log"
python scripts/a_directions.py \
  --extractor sums \
  --loose \
  --outdir $S \
  --workers "$NUM_WORKERS" \
  &> artifacts/logs/a_directions_derived_sums_loose.log

train() {  # suffix, then extra arguments
  local suffix=$1; shift
  local log=artifacts/logs/train_classic-gbdt-0$suffix.log
  echo "Step 1: training gbdt/seed-0$suffix. Log: $log"
  python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads "$NUM_WORKERS" \
    --suffix="$suffix" \
    --features $F \
    "$@" \
    &> "$log"
}
train -s10-mfull-feat-loose \
  --neutralize $S/M_full-pre-control.neutralize.txt \
  --monotone $S/M_full-pre-control.monotone.tsv
train -s10-mfull-sums-loose \
  --neutralize $S/M_full-pre.neutralize.txt \
  --monotone $S/M_full-pre.monotone.tsv

echo "Step 2: test metrics (ROC-AUC, TPR at 1% and 0.1% FPR):"
for s in -s10-ref -s10-mfull-feat-pre-v2 -s10-mfull-feat-loose -s10-mfull-sums-pre-v2 -s10-mfull-sums-loose; do
  python -c "
import json, sys
import numpy as np, polars as pl
from sklearn.metrics import roc_curve
d = sys.argv[1]
m = json.load(open(d + '/metrics.json'))
p = pl.read_parquet(d + '/ts_predictions.parquet')
fpr, tpr, _ = roc_curve(p['label'].to_numpy(), p['prob'].to_numpy())
print(sys.argv[2], round(m['ts_metrics']['roc'], 5), *[round(float(np.interp(f, fpr, tpr)), 4) for f in (0.01, 0.001)])
" $M/seed-0$s "$s"
done
echo "Done."
