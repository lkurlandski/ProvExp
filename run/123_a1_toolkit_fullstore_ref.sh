#!/bin/bash
# Table 7 (the detector table): the toolkit columns (detected / seen / held-out) for the UNDEFENDED full-store GBDT
# (seed-0), the model the adversarial-training row (run 122) was retrained from and the model the adaptive column of
# the unconstrained row already uses (runs 108, 119). Until now the unconstrained row's toolkit columns came from the
# 10%-subsample reference (seed-0-s10-ref, run 86), so the adversarial-training row had no like-for-like reference.
# FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et al.'s published secml-malware attacks against our own detector, on
# our own pilot samples, to evaluate defenses. Same protocol and arguments as run 122 step 3.
#
# Hypothesis: close to the s10 reference (47 detected, seen 17%, held-out 53%), since the full-store model is the same
# learner on ten times the data; seen clearly above run 122's 8% (adversarial training removes most seen evasions).
#
# Resources: ~384 attack runs; run 122's identical step took 563 s on 24 workers, so ~15 min on 16.
# Measured (2026-11-04, 16 workers): 18 min, no LOST tasks.
#
# Result (Table 7, new row "unconstrained, full training set"): 49/50 detected, seen 5/49 = 10%, held-out 26/49 = 53%
# (gamma_api 22, header_fields 11 by attack). Hypothesis half held: close to s10 on held-out, but seen is NOT clearly
# above adversarial training's 8% (4/48), so adversarial training changes little on the pilot.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/a1/toolkit-fullstore-ref
LOG=artifacts/logs/a1_eval_fullstore_ref.log

echo "Eight attacks x the undefended full-store GBDT on the pilot malware. Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir "$OUT" \
  --defense unconstrained=$M/seed-0 \
  --features artifacts/features/ember2024 \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> "$LOG"
tail -4 "$LOG"
echo "Done. Toolkit table: $OUT/table.json"
