#!/bin/bash
# Direction A, Table A1: a PV row built from *all eight* toolkit attacks (run 78's perturbation vectors, pv.*), trained
# on the same 10% store as the other rows, and the targeted adaptive search against it (as run 84). FOR ACADEMIC
# SECURITY RESEARCH ONLY: the C1-declared adaptive test against our own detectors on our own pilot malware.
# Hypothesis: the adaptive search evades PV-all about as often as PV-seen (21/22 in run 84): the targeted section names
# reach features that none of the eight attacks happened to lower, so observing more attacks does not close the hole.
#
# Took ~7 min (2026-10-26): training ~2 min, the adaptive search 5 min. Result: PV-all test AUC 0.944, TPR@1%FPR
# 53.8%; adaptive evaded 22/22 declared, 20/22 on re-extraction, median 4.6 KB added and 24 queries. Hypothesis held.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=4

F=artifacts/features/ember2024-sums-10
D=artifacts/experiments/a_directions_sums
P=artifacts/experiments/a_pv
M=artifacts/models/gbdt

cat $P/pv.neutralize.txt $D/reencoded.neutralize.txt > $P/pv-all-s10.neutralize.txt

LOG=artifacts/logs/train_classic-gbdt-0-s10-pv-all.log
echo "Step 1/2: training gbdt/seed-0-s10-pv-all on $F. Log: $LOG"
python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads 16 \
  --features $F \
  --suffix=-s10-pv-all \
  --neutralize $P/pv-all-s10.neutralize.txt \
  --monotone $P/pv.monotone.tsv \
  &> "$LOG"

LOG=artifacts/logs/a1_adaptive_pv_all.log
echo "Step 2/2: targeted adaptive search against PV-all. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive_pv_all \
  --features $F \
  --threat_model M_full \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --queries 100 \
  --target_buckets 8 \
  --seed 0 \
  &> "$LOG"

echo "Done. Adaptive (PV-all): artifacts/experiments/a1/adaptive_pv_all/adaptive.json"
