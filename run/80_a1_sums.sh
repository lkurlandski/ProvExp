#!/bin/bash
# Direction A, Table A1 prerequisite (docs/direction-A-A1-design.md, build step 1): the layer-2 re-encoding ("sums")
# features on a 10% subsample of every split (every 10th shard; shards are shuffled within a split), and the matched
# GBDTs trained on that store (seed 0, 16 threads):
#   1. unconstrained, thrember's features only (merged imports)      the reference on the subsample
#   2. M_add, C4 on features (the re-encoded groups dropped)          the as-is row, matched to the subsample
#   3. M_add, C4 on sums (every feature, re-encoded directions)       the "C4 on sums" row
#   4. M_full, C4 on features
#   5. M_full, C4 on sums
# Hypothesis: the subsample costs the as-is rows little (run 77 on the full splits: TPR@1%FPR 92.1% M_add, 87.4%
# M_full, vs 95.6% unconstrained); the sums recover part of the gap, more under M_full (8 points to recover) than under
# M_add (3.5), since they bring back the byte histograms, byte-entropy, strings, and section buckets as up-only.
#
# Estimate: featurization ~1-1.5 h at 16 workers (smoke test: one 1,024-file shard in 173 s on one worker, no failures;
# 283 shards in all; the sums extractor's strings pass repeats the regex scan); ~1-2 min per GBDT. The smoke shard
# matched the main store on every thrember feature except the imports of the 43/1,024 files that repeat a DLL (the
# merged descriptors).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

F=artifacts/features/ember2024-sums-10
D=artifacts/experiments/a_directions_sums

echo "Featurizing every 10th shard of ts, vl, tr with the sums extractor into $F. Log: artifacts/logs/featurize-sums-10.log"
python scripts/featurize.py \
  --extractor sums \
  --every 10 \
  --splits ts vl tr \
  --num_workers 16 \
  --outdir "$F" \
  &>> artifacts/logs/featurize-sums-10.log

echo "Writing the directions for the sums extractor into $D."
python scripts/a_directions.py \
  --hand \
  --extractor sums \
  --outdir "$D"

train() {  # suffix, then extra arguments
  local suffix=$1; shift
  local log=artifacts/logs/train_classic-gbdt-0$suffix.log
  echo "Training gbdt/seed-0$suffix. Log: $log"
  python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --features "$F" \
    --suffix="$suffix" \
    "$@" \
    &> "$log"
}

train -s10-ref         --neutralize $D/reencoded.neutralize.txt
train -s10-madd-feat   --neutralize $D/M_add-control.neutralize.txt   --monotone $D/M_add-control.monotone.tsv
train -s10-madd-sums   --neutralize $D/M_add.neutralize.txt           --monotone $D/M_add.monotone.tsv
train -s10-mfull-feat  --neutralize $D/M_full-control.neutralize.txt  --monotone $D/M_full-control.monotone.tsv
train -s10-mfull-sums  --neutralize $D/M_full.neutralize.txt          --monotone $D/M_full.monotone.tsv

echo "Test metrics (ROC-AUC, TPR at 1% and 0.1% FPR):"
for s in -s10-ref -s10-madd-feat -s10-madd-sums -s10-mfull-feat -s10-mfull-sums; do
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
