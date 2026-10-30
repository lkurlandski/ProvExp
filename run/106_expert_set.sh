#!/bin/bash
# Direction A, Table A1's expert-set row (docs/direction-A-expert-set.md; decided 2026-10-29): Gimenez et al.'s 40
# features, re-implemented on pefile with their two assign-instead-of-accumulate quirks patched
# (provexp.featuresets.ember2024.expert), and the monotone GBDT with all 40 constrained increasing, as they train it.
# FOR ACADEMIC SECURITY RESEARCH ONLY: their published secml-malware attacks against our own detectors, on our own
# pilot samples, to evaluate defenses (as runs 81 and 100).
#   1. featurize the 10% store (the same shards as ember2024-sums-10) with the expert extractor;
#   2. train the monotone model (`-s10-expert-mono`) and an unconstrained one on the same 40 features (`-s10-expert`);
#   3. Table A1's toolkit columns for both (unrouted: their guarantee does not rest on our precondition check).
# The row is read under M_add and M_full from the per-attack results (table.json): once patched, the set is sound under
# M_add (as its authors argue) but not under M_full (12 of the 40 features can be lowered by renaming a section,
# overwriting slack, or rewriting the DOS stub).
# Re-implementation (Claude, 2026-10-29): on the 45 test files every feature equals their LIEF code's (run with assign)
# except where the parsers disagree (pefile fails on one file, misses a resource directory on one and nine imports on
# another; LIEF names one ordinal import on two). Their `modified_dos_stub` compares a LIEF memoryview with a list, so
# with our LIEF it is constant 1; ours compares bytes.
# Hypothesis (from the mock): the monotone model far below the derived C4 rows (AUC ~0.80, TPR@1%FPR ~30%; theirs was
# 76.2% AUC on another dataset), the unconstrained one higher (theirs 92.3%); toolkit evasion of the monotone model
# low (0-5%), with any evasion from the M_full attacks (DOS header, section renaming), none from the M_add ones.
#
# Estimate: featurization ~12-20 min (smoke test: 2 ts shards in 42 s on 2 workers; ~280 shards on 16 workers);
# training ~2 min each; the toolkit columns for two defenses ~30-60 min (run 100: six defenses in 2.4 h).
# Ran 2026-10-29 (started by the user, overnight): featurization 13 min, training 1 min, toolkit 10 min. Result (read
# 2026-10-30): the monotone model as the mock predicted: AUC 0.844, TPR 29.1% at 1% FPR, 14.8% at 0.1% (it saturates:
# validation AUC flat at ~0.855 from round 10, no positive-gain split left; best iteration 15). Unconstrained on the same
# 40 features: AUC 0.978, 75.1% / 56.1%. At its 1% FPR threshold the monotone model detects only 8 of the 50 pilot
# malware, and no attack evades it on those 8 (0/8 under M_add and M_full). The unconstrained one: 40 detected, evaded
# on 24/40 by the M_add attacks (GAMMA API 24, GAMMA sections 3) and 25/40 by all attacks (one format_exploit run).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

F=artifacts/features/ember2024-expert-10
M=artifacts/models/gbdt
E=artifacts/experiments/a1/expert

echo "Step 1: featurizing every 10th shard of ts, vl, tr with the expert extractor into $F. Log: artifacts/logs/featurize-expert-10.log"
python scripts/featurize.py \
  --extractor expert \
  --every 10 \
  --splits ts vl tr \
  --num_workers 16 \
  --outdir "$F" \
  &>> artifacts/logs/featurize-expert-10.log

mkdir -p $E
python -c "
from provexp.featuresets.ember2024.expert import ExpertFeatureExtractor
print(''.join(f'{n}\t1\n' for n in ExpertFeatureExtractor().feature_names), end='')
" > $E/all-up.monotone.tsv

train() {  # suffix, then extra arguments
  local suffix=$1; shift
  local log=artifacts/logs/train_classic-gbdt-0$suffix.log
  echo "Step 2: training gbdt/seed-0$suffix. Log: $log"
  python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --features $F \
    --suffix="$suffix" \
    "$@" \
    &> "$log"
}
train -s10-expert
train -s10-expert-mono --monotone $E/all-up.monotone.tsv

echo "Test metrics (ROC-AUC, TPR at 1% and 0.1% FPR):"
for s in -s10-expert -s10-expert-mono; do
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

export OMP_NUM_THREADS=1

LOG=artifacts/logs/a1_evaluate_expert.log
echo "Step 3: eight attacks x two defenses on the pilot malware. Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir $E/toolkit \
  --features $F \
  --defense expert=$M/seed-0-s10-expert \
  --defense expert-mono=$M/seed-0-s10-expert-mono \
  --num_workers 16 \
  --seed 0 \
  &> "$LOG"

echo "Done. Toolkit table: $E/toolkit/table.json"
