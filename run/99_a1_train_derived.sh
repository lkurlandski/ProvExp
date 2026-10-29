#!/bin/bash
# Direction A, Table A1's C4 rows from the derived directions (derivation step 7; run 97): retrain the six sound
# monotone GBDTs with the precondition row's directions (the user chose, 2026-10-28: files that fail the precondition
# check go to the unconstrained detector, the >4 MB files stay, and the strict detector is one sentence, not a row).
#   on the 10% sums store (as run 80):  M_add / M_full, C4 on features (`-control`) and C4 on sums
#   on the full store (as run 77):      M_add / M_full, C4 on features with merged imports (the adaptive search's)
# The derived directions differ from the hand rules behind runs 77 and 80 only in the 10 entry_name_hash features
# (dropped under M_add: an added executable section can become the entry section) and security_size (constrained
# down under M_full instead of dropped); the re-encoded groups keep their hand rules until step 8.
# Hypothesis: test metrics within noise of runs 77 and 80 (one constrained feature more under M_full, ten dropped under
# M_add, all of little gain).
#
# Estimate: ~1-2 min per s10 model, ~6-7 min per full-store model (run 77; ~30 GB peak memory): ~20 min in all.
# Ran 2026-10-28 (started by the user), ~20 min. Result: as hypothesised. Test AUC / TPR@1% hand -> derived: s10 M_add
# feat 0.9946/91.2% -> 0.9945/90.9%, sums 0.9953/92.4% -> 0.9953/92.3%; M_full feat 0.9919/86.7% -> 0.9924/88.1%,
# sums 0.9930/88.6% -> 0.9935/89.9%; full store M_add 0.9957/92.1% -> 0.9957/92.0%, M_full 0.9930/87.4% -> 0.9934/88.6%
# (M_full slightly better: security_size kept, constrained down).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

S=artifacts/experiments/a_directions_derived_sums
D=artifacts/experiments/a_directions_derived

echo "Writing the derived directions in the sums store's layout into $S. Log: artifacts/logs/a_directions_derived_sums.log"
python scripts/a_directions.py \
  --derive \
  --extractor sums \
  --outdir $S \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_sums.log

train() {  # suffix, then extra arguments
  local suffix=$1; shift
  local log=artifacts/logs/train_classic-gbdt-0$suffix.log
  echo "Training gbdt/seed-0$suffix. Log: $log"
  python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --suffix="$suffix" \
    "$@" \
    &> "$log"
}

F=artifacts/features/ember2024-sums-10
train -s10-madd-feat-pre  --features $F --neutralize $S/M_add-pre-control.neutralize.txt  --monotone $S/M_add-pre-control.monotone.tsv
train -s10-madd-sums-pre  --features $F --neutralize $S/M_add-pre.neutralize.txt          --monotone $S/M_add-pre.monotone.tsv
train -s10-mfull-feat-pre --features $F --neutralize $S/M_full-pre-control.neutralize.txt --monotone $S/M_full-pre-control.monotone.tsv
train -s10-mfull-sums-pre --features $F --neutralize $S/M_full-pre.neutralize.txt         --monotone $S/M_full-pre.monotone.tsv
train -a-madd-pre-qf      --neutralize $D/M_add-pre-quirkfixed.neutralize.txt  --monotone $D/M_add-pre-quirkfixed.monotone.tsv
train -a-mfull-pre-qf     --neutralize $D/M_full-pre-quirkfixed.neutralize.txt --monotone $D/M_full-pre-quirkfixed.monotone.tsv

echo "Test metrics (ROC-AUC, TPR at 1% and 0.1% FPR), with the hand-rule models of runs 77 and 80 for comparison:"
for s in -s10-madd-feat -s10-madd-feat-pre -s10-madd-sums -s10-madd-sums-pre -s10-mfull-feat -s10-mfull-feat-pre \
         -s10-mfull-sums -s10-mfull-sums-pre -a-madd-mono-qf -a-madd-pre-qf -a-mfull-mono-qf -a-mfull-pre-qf; do
  python -c "
import json, sys
import numpy as np, polars as pl
from sklearn.metrics import roc_curve
d = sys.argv[1]
m = json.load(open(d + '/metrics.json'))
p = pl.read_parquet(d + '/ts_predictions.parquet')
fpr, tpr, _ = roc_curve(p['label'].to_numpy(), p['prob'].to_numpy())
print(sys.argv[2], round(m['ts_metrics']['roc'], 5), *[round(float(np.interp(f, fpr, tpr)), 4) for f in (0.01, 0.001)])
" artifacts/models/gbdt/seed-0$s "$s"
done
