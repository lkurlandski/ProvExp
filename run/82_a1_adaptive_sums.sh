#!/bin/bash
# Direction A, Table A1's adaptive column on the sums-space defenses (docs/direction-A-A1-design.md, step 4). Run after
# run 80 (the 10% sums store and the s10 models) and run 81 (which trains seed-0-s10-pv-seen). FOR ACADEMIC SECURITY
# RESEARCH ONLY: the C1-declared adaptive soundness test against our own detectors on our own pilot malware.
#
# The search scores each candidate edit (append, add-section) by its C1-predicted declared effect in the sums feature
# space (the attacker's reachable set under M); no file is written, so LIEF relayout (A4) never enters. The C4-sums
# rows (madd-sums, mfull-sums) are 0 by construction -- a negative min_delta_logit on one is an A1-A4 bug (debug via
# Table A0), not an evasion. The unconstrained reference and PV-seen are not marked --sound: a decrease there is just
# the search working, and PV-seen's is the hole check 2 measured realized adaptively.
#
# Estimate: C1 predictions only (no genetic engine); ~5-10 s per detected file, a few minutes for 50 malware x 4 defenses.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

M=artifacts/models/gbdt
LOG=artifacts/logs/a1_adaptive_sums.log

echo "Adaptive C1-declared search, sums space, M_full. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive_sums \
  --features artifacts/features/ember2024-sums-10 \
  --threat_model M_full \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense madd-sums=$M/seed-0-s10-madd-sums \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums \
  --sound madd-sums mfull-sums \
  --queries 100 \
  --seed 0 \
  &> "$LOG"

echo "Done. Adaptive (sums, C1-declared): artifacts/experiments/a1/adaptive_sums/adaptive.json"
