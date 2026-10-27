#!/bin/bash
# Direction A', go/no-go check 0 (docs/direction-A-prime-mock.md): can an exact solver (Kantchelian et al.'s
# mixed-integer encoding of the GBDT, HiGHS via scipy) decide "can this file's score go below the 1%-FPR threshold?"
# at our model sizes? 5 detected pilot malware per detector, decision version, 300 s per solve. No provenance needed.
# Hypothesis: the encoding reproduces the booster's score exactly; evasions are found in seconds; proofs that no
# evasion exists are the slow case (minutes or more on the 500-tree unconstrained model).
#
# Took ~2 min per step (2026-10-27). Result: encoding exact on all 25 (detector, file) pairs; every solve decided
# within 34 s (largest model: 22,533 binaries, 32,000 leaves). Directions alone (M_full, M_add) are too loose to
# certify anything on a non-monotone detector (all 15 evaded in feature space); the C4 detectors are certified in
# 0.2 s (monotone, no violation). With an L0 budget as a stand-in for a tight region: K=1 certifies the unconstrained
# model on 5/5 (13-18 s) and PV-all on 1/5; K=3 certifies the unconstrained model on 2/5 (23-34 s). Check 0: go.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
D=artifacts/experiments/ap_check0

echo "Step 1: encoding check + M_full directions, five detectors. Log: artifacts/logs/ap_check0_m_full.log"
python scripts/ap_check0_solver.py \
  --outdir $D/m_full \
  --decide \
  --time_limit 300 \
  --workers 12 \
  --regions fixed directions \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --defense sums=$M/seed-0-s10-mfull-sums \
  --defense feat=$M/seed-0-s10-mfull-feat \
  --sound sums feat \
  &> artifacts/logs/ap_check0_m_full.log

echo "Step 2: M_add directions (tighter). Log: artifacts/logs/ap_check0_m_add.log"
python scripts/ap_check0_solver.py \
  --outdir $D/m_add \
  --decide \
  --time_limit 300 \
  --workers 12 \
  --regions directions \
  --directions artifacts/experiments/a_directions_sums/M_add \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  &> artifacts/logs/ap_check0_m_add.log

for K in 1 3; do
  echo "Step 3: M_full directions with at most $K features changed. Log: artifacts/logs/ap_check0_m_full_l0_$K.log"
  python scripts/ap_check0_solver.py \
    --outdir $D/m_full_l0_$K \
    --decide \
    --time_limit 300 \
    --workers 6 \
    --regions directions \
    --max_changed $K \
    --defense ref=$M/seed-0-s10-ref \
    --defense pv-all=$M/seed-0-s10-pv-all \
    &> artifacts/logs/ap_check0_m_full_l0_$K.log
done

echo "Done. Reports: $D/*/report.json"
