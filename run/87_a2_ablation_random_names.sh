#!/bin/bash
# Direction A, Table A2's ablation: the run-84 adaptive search with *random* section names (--target_buckets 0) instead
# of names chosen through the inverted section hash, against the unconstrained reference and both PV rows. Everything
# else (exact composition of chosen edits, byte budget, 100 queries) is unchanged, so the gap to runs 84/85 is what the
# provenance-chosen names contribute. FOR ACADEMIC SECURITY RESEARCH ONLY: the C1-declared adaptive test against our
# own detectors on our own pilot malware.
# Hypothesis: random names evade PV far less often than targeted names (21/22 and 22/22 in runs 84/85), since a random
# name lands in a high-gain bucket with a negative sign with probability ~ (8/50) x 1/2 per candidate.
#
# Took 34 min (2026-10-26; ref 23 min, PV rows ~5-6 min each). Result (declared / real): ref 15/47 / 6, PV-seen
# 11/22 / 9, PV-all 15/22 / 13, vs targeted 14/47, 21/22, 22/22. Hypothesis held only partly: targeting doubles
# PV-seen evasion and adds 7 files on PV-all, but random names already evade PV often (its hole is broad), and on the
# unconstrained reference targeting adds nothing.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=4

M=artifacts/models/gbdt
LOG=artifacts/logs/a2_ablation_random_names.log

echo "Adaptive search with random section names (ablation), ref + PV rows, M_full. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive_random_names \
  --features artifacts/features/ember2024-sums-10 \
  --threat_model M_full \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --queries 100 \
  --target_buckets 0 \
  --seed 0 \
  &> "$LOG"

echo "Done. Adaptive (random names): artifacts/experiments/a1/adaptive_random_names/adaptive.json"
