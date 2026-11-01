#!/bin/bash
# A' step 1, follow-ups to run 114 (docs/direction-A-prime-plan.md, Section 11), on the files no attack evades, with
# the solver now calling HiGHS directly (the dual bound survives a timeout):
#   (2) the undefended GBDT, append only, at fixed budgets of 4 KB, 64 KB, and 512 KB (does a small append certify?);
#   (3) PV-seen and PV-all, one added section instead of three (is the number of sections what blocks the solver?).
# Hypotheses: every open solve now has a floor; 4 KB certifies most of the undefended model's 13 files, 64 KB some,
# 512 KB none; one section certifies a minority of the 4 PV files with a free slot.
#
# Ran 2026-11-01 (Claude, 300 s per solve, all four in parallel, ~6 min):
#   - floors: reported now, but at 64 KB and above (and for one section) no solve finished its root LP relaxation in
#     300 s (0 nodes), so the floor is the cheap per-tree one (-32 to -37; threshold 1.10). At 4 KB: real floors.
#   - undefended, append: 4 KB certifies 2 of 13 (180-265 s); floors of the other 11 range -13.1 to 1.07 (3 within
#     ~1.0 of the threshold); 64 KB 0 of 13; 512 KB 0 of 13. Hypothesis failed for 4 KB (2, not most).
#   - PV, one section: 0 of 4, no root LP in 300 s. Hypothesis failed.
# Diagnostic (Claude, scratch script, not kept): the LP relaxation alone on 6927e052, undefended, append: 58 K / 62 K /
# 78 K / 223 K variables at 4 / 16 / 64 / 512 KB (the block model of the byte-entropy windows grows with the budget);
# solved by simplex in 2 / 40 / 371 s / not in 420 s, by interior point in 6 / 28 / 133 s / not in 420 s; the LP's
# floor is -0.04 / -4.1 / -10.8 (threshold 1.10). So above a few KB the relaxation is both slow and far too loose to
# certify without heavy branching: the obstacle at large budgets is the relaxation, not only solver speed.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
OUT=artifacts/experiments/ap_bracket
mkdir -p artifacts/logs

for B in 4096 65536 524288; do
  LOG=artifacts/logs/ap_bracket_ref_append_$B.log
  echo "Undefended, append only, budget $B bytes. Log: $LOG"
  python scripts/ap_bracket.py \
    --outdir $OUT/ref_append_$B \
    --defense ref=$M/seed-0-s10-ref \
    --family append \
    --budget_frac 0 \
    --budget_min $B \
    --time_limit 300 \
    --workers 13 \
    &> "$LOG" &
done
LOG=artifacts/logs/ap_bracket_pv_sections_k1.log
echo "PV, one added section. Log: $LOG"
python scripts/ap_bracket.py \
  --outdir $OUT/pv_sections_k1 \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --family sections \
  --max_sections 1 \
  --time_limit 300 \
  --workers 4 \
  &> "$LOG" &
wait
echo "Done. Reports: $OUT/{ref_append_*,pv_sections_k1}/report.json"
