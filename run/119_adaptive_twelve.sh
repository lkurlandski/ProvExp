#!/bin/bash
# Tier 2, item 8 (review R1a, R11): the adaptive search over all twelve operations, on the pilot (scripts/a1_adaptive.py).
# Extends run 108's append+add-section search to every operation of the threat model. Each candidate is scored by the
# EXACT prediction of our own writer -- catalogue.predict_* for the structural operations (add section, add imports,
# rename, both removals; the two gap insertions are extracted, ~5x cheaper than predicting them) and reach.predict for
# the in-place overwrites (header fields, checksum, DOS region, slack) -- and the chosen step is materialized by that
# writer (never LIEF), so the predicted score equals the re-extracted score (item 7 / run 118). full_menu keeps run
# 108's targeted add-section exploration (~8 candidates per step) and adds the new operations on top, so adding them
# cannot weaken the search by starving it of section candidates.
#
# Each C4 (monotone) row is attacked UNDER ITS OWN THREAT MODEL, where it must stay 0 (the implementation check): the
# M_add detector under M_add, the M_full detector under M_full. The unconstrained and PV rows are attacked under
# M_full (the strongest attacker). A negative min_delta_logit on a --sound defense attacked under its own threat model
# is an A1-A4 bug (debug via Table A0); under a wider threat model it is just the search using an out-of-model edit.
#
# Hypothesis: with imports, rename, header, and DOS operations the search beats GAMMA API on the unconstrained model
# (go/no-go: at least ~half of the detected pilot malware, i.e. >=24 of ~49); PV recovers to run 108's ~16/22 (the new
# ops add to the add-section exploration, not replace it); the M_add row stays 0 under M_add and the M_full row stays 0
# under M_full, both with min_delta_logit exactly 0.
#
# a1_adaptive.py is single-process (one greedy search per file, no worker pool), so NUM_WORKERS does not apply here;
# set OMP threads instead. Estimate: run 108 (queries 100, append+sec only) took ~6 min; the fuller menu (~25
# candidates per step) at queries 200 is ~3-4x the per-file work -> ~20-30 min for the two invocations.
# Ran 2026-11-03 (Claude, OMP=4, ~17 min). Result:
#   unconstrained 10/49 (20%), up from run 108's 4/49 (8%): the new ops help, but short of GAMMA API's 24/47 (the
#     undefended model is robust to the loader-safe edit set -- for 40/49 files the search barely moves its score).
#   PV (4 attacks) 12/22 (55%), BELOW run 108's append+add-section 16/22 (73%): the extra operations mislead the
#     myopic greedy on PV's section-hash hole (not query-limited; q150 and q200 both 12). PV-cell framing pending the
#     user (keep run 108's 16 as the strongest of our search variants, vs report the twelve-op 12 uniformly).
#   mfull-feat 0/41 under M_full and madd-feat 0/47 under M_add, both min_delta_logit exactly 0.0: the C4 soundness
#     (implementation) check passes, each row attacked under its own threat model.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/a1/adaptive-twelve
LOG=artifacts/logs/a1_adaptive_twelve.log

echo "Item 8: the twelve-operation adaptive search. Log: $LOG"
echo "  (1/2) M_full: unconstrained, PV, mfull-feat (sound under M_full)."
python scripts/a1_adaptive.py \
  --outdir "$OUT/mfull" \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense unconstrained=$M/seed-0 \
  --defense pv=$M/seed-0-pv \
  --defense mfull-feat=$M/seed-0-a-mfull-pre-qf-v2 \
  --sound mfull-feat \
  --queries 200 \
  --seed 0 \
  &> "$LOG"

echo "  (2/2) M_add: madd-feat (sound under M_add)."
python scripts/a1_adaptive.py \
  --outdir "$OUT/madd" \
  --features artifacts/features/ember2024 \
  --threat_model M_add \
  --defense madd-feat=$M/seed-0-a-madd-pre-qf-v2 \
  --sound madd-feat \
  --queries 200 \
  --seed 0 \
  &>> "$LOG"

echo "Done. Reports: $OUT/mfull/adaptive.json and $OUT/madd/adaptive.json"
tail -8 "$LOG"
