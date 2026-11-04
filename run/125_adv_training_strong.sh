#!/bin/bash
# Table 7 (the detector table): adversarial training on the attacks that work, a fair version of run 122's baseline.
# Run 122 trained on Gimenez et al.'s four "seen" attacks at the low budget, which barely evade the undefended
# full-store detector (5/49), so it taught the model little. Here the training examples come from the toolkit attacks
# that do evade it (gamma_api 22/49 and header_fields 11/49 at the low budget) plus GAMMA section injection, the
# literature's headline attack on GBDTs, all at the GAMMA paper's budget (a_pv_attacks.BUDGETS["literature"]).
# FOR ACADEMIC SECURITY RESEARCH ONLY: published secml-malware attacks against our own undefended detector, on our own
# TRAINING samples, solely to build a standard adversarial-training defense to compare with the sound detectors.
# Nothing is deployed; adversarial files are written only to be re-featurized.
#
# Steps (as run 122, with the stronger training set):
#   1. GENERATE on ADV_MALWARE training malware x {gamma_api, header_fields, gamma_sections} at the literature budget.
#   2. RETRAIN the unconstrained GBDT with those rows appended (full store, as seed-0): seed-0-advtrain-strong.
#   3. EVALUATE: the Table 7 toolkit columns (all eight attacks, low budget; note gamma_api and header_fields are
#      "held-out" for PV but TRAINED ON here); the strong-toolkit column (run 124's protocol); the adaptive column
#      (union of the two search menus, as runs 108/119/122).
#
# Hypothesis: adversarial training now pays where it was trained: gamma_api and header_fields evasion fall well below
# the undefended 22/49 and 11/49, and the strong column falls too. The adaptive search, which uses edits the toolkit
# never makes (section names aimed at the model's trusted buckets, renames), still evades it at roughly the
# unconstrained rate (~20%), and it still carries no guarantee, unlike the monotone rows' 0%. Run run/124 first or
# alongside; the two do not depend on each other's outputs.
#
# Resources (smoke test 2026-11-04): generation ~60-200 s per (file, attack); 1,200 tasks: ~2.5 h at 16 workers
# (~1.7 h at 24). Retrain ~10 min (full store, ~30 GB peak). Toolkit eval ~20 min, strong eval ~30 min, adaptive
# ~20 min (single-process; OMP threads). ~3.5-4 h in all at 16 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
ADV_MALWARE="${ADV_MALWARE:-400}"

M=artifacts/models/gbdt
F=artifacts/features/ember2024
EVAL=artifacts/experiments/a1/advtrain-strong
GEN=$EVAL/generated
mkdir -p "$EVAL"

echo "(1/5) GENERATE adversarial training examples ($ADV_MALWARE malware x 3 attacks, literature budget). Log: artifacts/logs/a_advtrain_strong_generate.log"
python scripts/a_advtrain.py \
  --outdir "$GEN" \
  --features "$F" \
  --db /shared/datasets/EMBER-2024/data/tr \
  --model "$M/seed-0/model.txt" \
  --attacks gamma_api header_fields gamma_sections \
  --budget literature \
  --num_malware "$ADV_MALWARE" \
  --num_goodware 50 \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> artifacts/logs/a_advtrain_strong_generate.log
tail -6 artifacts/logs/a_advtrain_strong_generate.log
grep LOST artifacts/logs/a_advtrain_strong_generate.log || true

echo "(2/5) RETRAIN the unconstrained GBDT with the adversarial rows appended. Log: artifacts/logs/train_classic-gbdt-0-advtrain-strong.log"
python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads "$NUM_WORKERS" \
  --suffix=-advtrain-strong \
  --augment "$GEN" \
  &> artifacts/logs/train_classic-gbdt-0-advtrain-strong.log
tail -3 artifacts/logs/train_classic-gbdt-0-advtrain-strong.log

echo "    Test AUC, TPR at 1% and 0.1% FPR (undefended seed-0 for comparison):"
for s in "" "-advtrain-strong"; do
  python -c "
import json
import numpy as np, polars as pl
from sklearn.metrics import roc_curve
d = 'artifacts/models/gbdt/seed-0$s'
m = json.load(open(d + '/metrics.json'))
p = pl.read_parquet(d + '/ts_predictions.parquet')
fpr, tpr, _ = roc_curve(p['label'].to_numpy(), p['prob'].to_numpy())
print(f'  seed-0$s', round(m['ts_metrics']['roc'], 5), *[round(float(np.interp(f, fpr, tpr)), 4) for f in (0.01, 0.001)])
"
done

echo "(3/5) EVALUATE the toolkit columns (eight attacks, low budget). Log: artifacts/logs/a1_eval_advtrain_strong.log"
python scripts/a1_evaluate.py \
  --outdir "$EVAL/toolkit" \
  --defense advtrain-strong=$M/seed-0-advtrain-strong \
  --features "$F" \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> artifacts/logs/a1_eval_advtrain_strong.log
tail -4 artifacts/logs/a1_eval_advtrain_strong.log

echo "(4/5) EVALUATE the strong-toolkit column (GAMMA, literature budget; run 124's protocol). Log: artifacts/logs/a1_eval_advtrain_strong_literature.log"
python scripts/a1_evaluate.py \
  --outdir "$EVAL/toolkit-literature" \
  --defense advtrain-strong=$M/seed-0-advtrain-strong \
  --features "$F" \
  --attacks gamma_sections gamma_api \
  --seen gamma_sections gamma_api \
  --budget literature \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> artifacts/logs/a1_eval_advtrain_strong_literature.log
tail -4 artifacts/logs/a1_eval_advtrain_strong_literature.log

echo "(5/5) EVALUATE the adaptive column (union of the two search menus). Log: artifacts/logs/a1_adaptive_advtrain_strong.log"
: > artifacts/logs/a1_adaptive_advtrain_strong.log
echo "  twelve-op menu:"
python scripts/a1_adaptive.py \
  --outdir "$EVAL/adaptive-twelve" \
  --features "$F" \
  --threat_model M_full \
  --defense advtrain-strong=$M/seed-0-advtrain-strong \
  --queries 200 \
  --seed 0 \
  &>> artifacts/logs/a1_adaptive_advtrain_strong.log
echo "  append+add-section menu (run 108's):"
python scripts/a1_adaptive.py \
  --outdir "$EVAL/adaptive-appsec" \
  --features "$F" \
  --threat_model M_full \
  --operations app sec \
  --defense advtrain-strong=$M/seed-0-advtrain-strong \
  --queries 200 \
  --seed 0 \
  &>> artifacts/logs/a1_adaptive_advtrain_strong.log
tail -6 artifacts/logs/a1_adaptive_advtrain_strong.log

echo
echo "Table 7 adaptive cell (union: a file counts as evaded if either menu evades it):"
python - "$EVAL/adaptive-twelve/adaptive.parquet" "$EVAL/adaptive-appsec/adaptive.parquet" <<'PY'
import sys
import polars as pl
a = pl.read_parquet(sys.argv[1]).select(['name', 'evaded'])
b = pl.read_parquet(sys.argv[2]).select(['name', 'evaded']).rename({'evaded': 'evaded_b'})
j = a.join(b, on='name', how='full', coalesce=True).with_columns(
    (pl.col('evaded').fill_null(False) | pl.col('evaded_b').fill_null(False)).alias('either'))
det = j.height
print(f"  detected {det}; twelve-op {int(a['evaded'].sum())}; append+sec {int(b['evaded_b'].sum())}; "
      f"union {int(j['either'].sum())}/{det} = {100*j['either'].sum()/det:.0f}%")
PY
echo
echo "Done. Toolkit: $EVAL/toolkit/table.json; strong: $EVAL/toolkit-literature/table.json; adaptive under $EVAL/."
