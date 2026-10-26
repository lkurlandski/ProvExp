#!/bin/bash
# Direction A, Table A1's adaptive column, all six s10 defenses, with the strengthened search (2026-10-26): the chosen
# edit is now the one materialized (the old search re-drew a random edit, so steps did not compose), add-section names
# are targeted through the inverted section hash at the defense's most-used buckets (white-box attacker), the
# predicted properties match the materialized section, and the byte budget is the toolkit's max(5%, 512 KB). Supersedes
# runs 82/83. FOR ACADEMIC SECURITY RESEARCH ONLY: the C1-declared adaptive soundness test against our own detectors on
# our own pilot malware. A negative min_delta_logit on a --sound row is an A1-A4 bug (debug via Table A0).
#
# Took 38 min (2026-10-26): ref 24 min (most files use all 100 queries, each kept step is a LIEF write + re-extraction),
# pv-seen 5 min, each sound row ~2.3 min (stops after the first 12 candidates). Result: evaded (declared / real)
# ref 14/47 / 9, pv-seen 21/22 / 19, all four C4 rows 0 with min_delta_logit exactly 0.0.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=4

M=artifacts/models/gbdt
LOG=artifacts/logs/a1_adaptive_targeted.log

echo "Adaptive C1-declared search (targeted names), six s10 defenses, M_full. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive_targeted \
  --features artifacts/features/ember2024-sums-10 \
  --threat_model M_full \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense madd-feat=$M/seed-0-s10-madd-feat \
  --defense madd-sums=$M/seed-0-s10-madd-sums \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums \
  --sound madd-feat madd-sums mfull-feat mfull-sums \
  --queries 100 \
  --target_buckets 8 \
  --seed 0 \
  &> "$LOG"

echo "Done. Adaptive (targeted, C1-declared): artifacts/experiments/a1/adaptive_targeted/adaptive.json"
