#!/bin/bash
# R18 (docs/evidence/r18-trial-competitor.md): what the import adder's two-way declaration costs the derived detector.
# catalogue.py declares the import and IAT directory entries (address and size) movable both ways by `imp` (the only
# operation that lowers them under the precondition, a_directions' per-operation signs on 24 pilot files). The new
# import table lies in a section added after the existing ones, so the two *addresses* can only rise; the sizes can
# fall (a recomputed inflated size; the IAT entry pointed at the new thunks only). This retrains the derived -loose
# detector with the two addresses monotone increasing instead of dropped, everything else as run 140.
#
# Hypothesis (Claude, before the run): under one point of TPR at 1% FPR gained (83.4 -> <84.4): trial's 4-point edge
# sits mostly in string counts and iat_size, and the trial detector puts 1.8% of its gain on iat_virtual_address.
#
# Result (Claude, 2026-11-14; NUM_WORKERS=8, 54 s with run 144 loading the machine): ROC-AUC / TPR at 1% / 0.1% FPR
#   -loose 0.98898 / 83.4 / 65.1; -loose-impaddr 0.98901 / 83.2 / 66.3; trial 0.99257 / 87.6 / 71.3.
#   Hypothesis held: no measurable gain (noise in both directions). The declaration's breadth costs nothing; trial's
#   edge rests on features that are lowerable (string counts, iat_size).
#
# Resources: one GBDT, NUM_WORKERS threads (~1 min at 16 on an idle machine).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"

S=artifacts/experiments/a_directions_derived_sums_loose
T=artifacts/experiments/r18_trial
F=artifacts/features/ember2024-sums-10-v2
M=artifacts/models/gbdt
ADDR='^datadirectories:(iat|import)_virtual_address$'

echo "(1/3) The variant table into $T/derived-impaddr.{neutralize.txt,monotone.tsv}"
grep -vE "$ADDR" $S/M_full-pre-control.neutralize.txt > $T/derived-impaddr.neutralize.txt
{ cat $S/M_full-pre-control.monotone.tsv
  grep -E "$ADDR" $S/M_full-pre-control.neutralize.txt | sed 's/$/\t1/'; } > $T/derived-impaddr.monotone.tsv

LOG=artifacts/logs/train_classic-gbdt-0-s10-mfull-feat-loose-impaddr.log
echo "(2/3) Training gbdt/seed-0-s10-mfull-feat-loose-impaddr. Log: $LOG"
python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads "$NUM_WORKERS" \
  --suffix=-s10-mfull-feat-loose-impaddr \
  --features $F \
  --neutralize $T/derived-impaddr.neutralize.txt \
  --monotone $T/derived-impaddr.monotone.tsv \
  &> "$LOG"

echo "(3/3) Test metrics (ROC-AUC, TPR at 1% and 0.1% FPR):"
for s in -s10-mfull-feat-loose -s10-mfull-feat-loose-impaddr -s10-mfull-feat-trial; do
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
