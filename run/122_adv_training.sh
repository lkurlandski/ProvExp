#!/bin/bash
# Tier 2, item 10 (review step 5, R1a): the adversarial-training row of Table 7 (the detector table). Replaces the
# synthetic row. FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et al.'s published secml-malware attacks against our own
# undefended detector, on our own TRAINING samples, solely to build a standard adversarial-training defense and
# compare it with the sound detectors. Nothing is deployed; adversarial files are written only to be re-featurized.
#
# Protocol (the honest, fair-baseline version the user chose, 2026-11-03: ~400 training malware x the 4 "seen" attacks):
#   1. GENERATE adversarial examples on ADV_MALWARE training malware with the four PV "seen" attacks (padding,
#      gamma_sections, gamma_shift, content_shift), featurize each valid file (scripts/a_advtrain.py).
#   2. RETRAIN the unconstrained GBDT with those rows APPENDED to the training split (train_classic.py --augment;
#      a pure addition, unlike --poison which replaces). Full store, merged imports, as the undefended detector.
#   3. EVALUATE: test AUC and TPR at 1% FPR; the toolkit seen/held-out columns (a1_evaluate.py, all 8 attacks on the
#      pilot, "seen" = the 4 trained-on attacks); and the adaptive column (a1_adaptive.py) as the UNION of the two
#      search menus the other Table 7 rows use (append+add-section, run 108; the full twelve-op menu, run 119).
#
# Hypothesis (report honestly whatever it shows -- the review judged the synthetic 20% adaptive plausible since our
# search gets only 10/49 on the undefended model, so adversarial training is expected to be *competitive with, not
# better than*, the unconstrained row against the adaptive search, and strictly worse than the sound 0%): adversarial
# training drives the "seen" toolkit column near 0, helps little on held-out, and the adaptive search still evades it
# at roughly the unconstrained rate (~20%), because the undefended model is already robust to the loader-safe edits and
# adversarial training adds no guarantee. If instead it comes out competitive with the monotone 0% rows, report that.
#
# Resources: generation is the cost driver (secml-malware ~0.06 CPU-h per file-attack; ADV_MALWARE x 4 attacks). At
# ADV_MALWARE=400 and 16 workers: generation ~6-7 h, the toolkit eval ~1.5 h (~47 detected pilot malware x 8 attacks),
# retrain ~7 min (full store, ~30 GB peak), the adaptive search ~12 min (single-process). ~8-9 h in all, an overnight
# job. a1_adaptive is single-process (NUM_WORKERS does not apply there); OMP threads instead.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
ADV_MALWARE="${ADV_MALWARE:-400}"

M=artifacts/models/gbdt
F=artifacts/features/ember2024
GEN=artifacts/experiments/a1/advtrain/generated
EVAL=artifacts/experiments/a1/advtrain
mkdir -p "$EVAL"

echo "(1/4) GENERATE adversarial training examples ($ADV_MALWARE malware x 4 seen attacks). Log: artifacts/logs/a_advtrain_generate.log"
python scripts/a_advtrain.py \
  --outdir "$GEN" \
  --features "$F" \
  --db /shared/datasets/EMBER-2024/data/tr \
  --model "$M/seed-0/model.txt" \
  --num_malware "$ADV_MALWARE" \
  --num_goodware 50 \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> artifacts/logs/a_advtrain_generate.log
tail -6 artifacts/logs/a_advtrain_generate.log

echo "(2/4) RETRAIN the unconstrained GBDT with the adversarial rows appended. Log: artifacts/logs/train_classic-gbdt-0-advtrain.log"
python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads "$NUM_WORKERS" \
  --suffix=-advtrain \
  --augment "$GEN" \
  &> artifacts/logs/train_classic-gbdt-0-advtrain.log
tail -3 artifacts/logs/train_classic-gbdt-0-advtrain.log

echo "    Test AUC, TPR at 1% and 0.1% FPR (undefended seed-0 for comparison):"
for s in "" "-advtrain"; do
  python -c "
import json, sys
import numpy as np, polars as pl
from sklearn.metrics import roc_curve
d = 'artifacts/models/gbdt/seed-0$s'
m = json.load(open(d + '/metrics.json'))
p = pl.read_parquet(d + '/ts_predictions.parquet')
fpr, tpr, _ = roc_curve(p['label'].to_numpy(), p['prob'].to_numpy())
print(f'  seed-0$s', round(m['ts_metrics']['roc'], 5), *[round(float(np.interp(f, fpr, tpr)), 4) for f in (0.01, 0.001)])
"
done

echo "(3/4) EVALUATE toolkit columns (seen / held-out) on the pilot. Log: artifacts/logs/a1_eval_advtrain.log"
python scripts/a1_evaluate.py \
  --outdir "$EVAL/toolkit" \
  --defense advtrain=$M/seed-0-advtrain \
  --features "$F" \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> artifacts/logs/a1_eval_advtrain.log
tail -4 artifacts/logs/a1_eval_advtrain.log

echo "(4/4) EVALUATE the adaptive column (union of the two search menus). Log: artifacts/logs/a1_adaptive_advtrain.log"
: > artifacts/logs/a1_adaptive_advtrain.log
echo "  twelve-op menu:"
python scripts/a1_adaptive.py \
  --outdir "$EVAL/adaptive-twelve" \
  --features "$F" \
  --threat_model M_full \
  --defense advtrain=$M/seed-0-advtrain \
  --queries 200 \
  --seed 0 \
  &>> artifacts/logs/a1_adaptive_advtrain.log
echo "  append+add-section menu (run 108's):"
python scripts/a1_adaptive.py \
  --outdir "$EVAL/adaptive-appsec" \
  --features "$F" \
  --threat_model M_full \
  --operations app sec \
  --defense advtrain=$M/seed-0-advtrain \
  --queries 200 \
  --seed 0 \
  &>> artifacts/logs/a1_adaptive_advtrain.log
tail -6 artifacts/logs/a1_adaptive_advtrain.log

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
echo "Done. Toolkit table: $EVAL/toolkit/table.json; adaptive reports under $EVAL/."
