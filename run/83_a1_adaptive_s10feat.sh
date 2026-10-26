#!/bin/bash
# Direction A, Table A1's adaptive column on the s10 features-as-is defenses (madd-feat, mfull-feat), so every A1 row
# uses the same s10 models as the toolkit columns (run 81's step 4 used the full-data run-77 models). Run after runs
# 80-82. FOR ACADEMIC SECURITY RESEARCH ONLY: the C1-declared adaptive soundness test against our own detectors on our
# own pilot malware.
#
# Scored in the sums space (the store these models were trained on, with the extra groups neutralized); both rows are
# --sound, so a negative min_delta_logit is an A1-A4 bug. Took ~5 min (2026-10-26): evaded 0, min_delta_logit 0.0 on both.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=4

M=artifacts/models/gbdt
LOG=artifacts/logs/a1_adaptive_s10feat.log

echo "Adaptive C1-declared search, s10 features-as-is defenses, M_full. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive_s10feat \
  --features artifacts/features/ember2024-sums-10 \
  --threat_model M_full \
  --defense madd-feat=$M/seed-0-s10-madd-feat \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat \
  --sound madd-feat mfull-feat \
  --queries 100 \
  --seed 0 \
  &> "$LOG"

echo "Done. Adaptive (s10 features, C1-declared): artifacts/experiments/a1/adaptive_s10feat/adaptive.json"
