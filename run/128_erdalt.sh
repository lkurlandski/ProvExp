#!/bin/bash
# Table 7's ERDALT row (docs/direction-A-mock.md, "ERDALT row"; user decision 2026-11-04): Gimenez et al.'s main
# method, an empirically robust detector (a learned linear post-processing L under a monotone network), ported from
# their public train_model.py following the paper (the output layer is projected too, so the network is monotone;
# docs/upstream-issues.md item 8). FOR ACADEMIC SECURITY RESEARCH ONLY: published secml-malware attacks and our own
# adaptive search against our own detectors, on our own pilot samples, to evaluate defenses. Nothing is deployed.
#
#   1. train ERDALT on the 10% sums store, reading thrember's 2,568 features (as the reference and PV-seen rows), from
#      the perturbation vectors of the 4 seen attacks: the 200 on the pilot malware PV-seen is selected from (run 78)
#      and run 122's 1,597 on 400 training malware (1,797 in all; their paper: 1,033). Deviations from their code,
#      forced by scale: batch 256 instead of 16; the epoch selected on our validation split (their criterion: < 5
#      negative entries of L delta, then the best ROC-AUC) instead of their test split. The logit is divided by a
#      temperature fitted on the validation split (provexp.models.erdalt.fit_temperature): the monotone network's logits
#      reach the thousands, so sigmoid(logit) is exactly 1.0 for many files; the rescaling changes no decision.
#   2. the hole: L against the derived M_full table (the monotone features row's), and the pilot gradients
#   3. the toolkit columns: the eight attacks at the low budget, seen = the 4 ERDALT learned from
#   4. the adaptive column: the beam search at 5,000 candidates, M_full (run 127's protocol)
#
# Hypothesis: ERDALT resists the attacks it learned from (seen <= ~10%; they report 96% robust), is evaded by the
# held-out attacks (~20-40%) and by the adaptive search (>= 50%); the hole is large, mostly in the features the table
# marks as moved both ways. Detection below the mock's: the 12-epoch smoke test reached validation AUC ~0.81 (the paper:
# 93.0% on their data).
#
# Resources: (1) one GPU, ~5 s per epoch, 310 epochs: ~26 min (smoke, Claude, 2026-11-04, L40S); (2) ~2 min; (3) 8
# attacks x ~40 files, ~20-30 min at 16 workers; (4) ~40 files x up to ~4 min, ~10-15 min at 16 workers. ~1-1.2 h in all.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"

F=artifacts/features/ember2024-sums-10-v2
MODEL=artifacts/models/erdalt/seed-0-s10-seen
OUT=artifacts/experiments/a_erdalt
SEEN="padding gamma_sections gamma_shift content_shift"

LOG=artifacts/logs/train_erdalt-0-s10-seen.log
echo "(1/4) Training ERDALT on $F (one GPU). Log: $LOG"
CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" OMP_NUM_THREADS=8 python scripts/train_erdalt.py \
  --features $F \
  --neutralize artifacts/experiments/a_directions_sums/reencoded.neutralize.txt \
  --deltas artifacts/experiments/a_pv/deltas.parquet \
  --adv_dir artifacts/experiments/a1/advtrain/generated \
  --attacks $SEEN \
  --suffix=-s10-seen \
  --epochs 310 \
  --batch_size 256 \
  --seed 0 \
  &> "$LOG"
grep -E "Temperature|WARNING|Test metrics" "$LOG"
python - "$MODEL" <<'PY'
import json, sys
import numpy as np, polars as pl
from sklearn.metrics import roc_curve
d = sys.argv[1]
m = json.load(open(d + "/metrics.json"))
p = pl.read_parquet(d + "/ts_predictions.parquet")
fpr, tpr, _ = roc_curve(p["label"].to_numpy(), p["prob"].to_numpy())
t = m["training"]
print(f"  AUC {m['ts_metrics']['roc']:.4f}, TPR at 1% FPR {np.interp(0.01, fpr, tpr):.4f}; epoch {t['epoch']}, "
      f"violations {t['violations']}, criterion met: {t['met_criterion']}, {m['minutes']:.0f} min")
PY

LOG=artifacts/logs/a_erdalt_hole.log
echo "(2/4) The hole: L against the derived M_full table. Log: $LOG"
OMP_NUM_THREADS=4 python scripts/a_erdalt_hole.py \
  --model $MODEL \
  --directions artifacts/experiments/a_directions_derived_sums_v2/M_full-pre-control \
  --outdir $OUT/hole \
  &> "$LOG"
head -30 "$LOG"

export OMP_NUM_THREADS=1
LOG=artifacts/logs/a1_eval_erdalt.log
echo "(3/4) Eight attacks x ERDALT on the pilot malware (seen: $SEEN). Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir $OUT/toolkit \
  --features $F \
  --defense erdalt=$MODEL \
  --seen $SEEN \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> "$LOG"
tail -3 "$LOG"

LOG=artifacts/logs/a1_adaptive_erdalt.log
echo "(4/4) The beam search (5,000 candidates, M_full) x ERDALT. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir $OUT/adaptive \
  --features $F \
  --threat_model M_full \
  --defense erdalt=$MODEL \
  --search beam \
  --queries 5000 \
  --checkpoints 200 1000 5000 \
  --beam 3 \
  --draws 2 \
  --patience 3 \
  --seed 0 \
  --num_workers "$NUM_WORKERS" \
  &> "$LOG"
tail -6 "$LOG"
echo "Done. $MODEL; $OUT/{hole/hole.json,toolkit/table.json,adaptive/adaptive.json}"
