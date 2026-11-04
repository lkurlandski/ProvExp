#!/bin/bash
# Strong attacks (strategic review 2026-11-04, W2; resume step 5a): the adaptive search with a realistic scoring budget,
# against Table 7's rows (scripts/a1_adaptive.py --search beam). The greedy search of runs 108/119 draws ~25 random
# candidates per step, stops at the first step without an improvement, and is capped at 200 scored candidates; on the
# undefended model 24 of the 39 files it does not evade stall that way about a fifth of the way to the threshold, and 15
# run out of queries about halfway. The beam search keeps the 3 best files found so far, draws 2 menus per kept file per
# step (~150 candidates per step), restarts from the original file after 3 steps without a new best, and scores up to
# 5,000 candidates per file (evasion also reported at 200 and 1,000). Every kept file is written by our own byte-level
# edits (never LIEF) and re-extracted, so every score the search keeps is real. Same operations, byte budget (5% of the
# file, at least 512 KB), threshold (1% FPR), and models as Table 7's adaptive cells:
#   1. M_full, full store: unconstrained (seed-0), adversarial training (run 122), PV from 4 attacks (seed-0-pv), and the
#      monotone features row (sound under M_full);
#   2. M_add, full store: the monotone additions row (sound under M_add);
#   3. M_full, 10% sums store: PV from all 8 attacks (Table 7's synthetic 77% cell) and from the 4 seen attacks;
#   4. M_full, full store: run 125's adversarial training on the literature-budget attacks, if that model exists.
#
# Reference points (fixed before the run, 2026-11-04), on the undefended model's 49 detected pilot malware: the
# toolkit's 8 attacks together evade 27 (55%), the 6 that are catalogue operations 13 (27%; the other 14 files only via
# GAMMA's LIEF relayouts, outside the threat model), the greedy search 10 (20%). Zainab et al. 2026 (arXiv 2609.34456,
# Table XI) report at most 9.6% on EMBER-2024's own test malware (MAB-Malware; hard-label, 50 queries, 0.1% FPR).
# Hypothesis: unconstrained 35-45% at 5,000 (above the in-catalogue 27%, probably below the full toolkit's 55%: the
# undefended model barely moves under catalogue edits on most files); adversarial training about the same; PV ~100%
# (4 attacks) and ~95% (8 attacks); the monotone rows 0% with min_delta_logit exactly 0 on every file and candidate.
# Smoke (Claude, 2026-11-04, 3 files, 2,000 queries): the greedy refactor reproduces run 119 file for file; the beam
# evades all 3 (one the greedy did not, at 1,100 queries); 36-50 ms per candidate.
#
# Resources: one search per (defense, file), NUM_WORKERS processes (spawn; each loads the pilot, ~1 GB). A file that is
# not evaded spends all 5,000 queries (~4 min); the monotone rows never evade. ~400 (defense, file) pairs, ~20 CPU-h:
# ~1-1.5 h with 16 workers. OMP_NUM_THREADS=1 per worker.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/a1/adaptive-beam
LOG=artifacts/logs/a1_adaptive_beam.log

search() {  # outdir, then extra arguments
  local out=$1; shift
  python scripts/a1_adaptive.py \
    --outdir "$OUT/$out" \
    --search beam \
    --queries 5000 \
    --checkpoints 200 1000 5000 \
    --beam 3 \
    --draws 2 \
    --patience 3 \
    --seed 0 \
    --num_workers "$NUM_WORKERS" \
    "$@" \
    &>> "$LOG"
  tail -6 "$LOG"
}

: > "$LOG"
echo "(1/4) M_full, full store: unconstrained, advtrain, PV (4 attacks), mfull-feat. Log: $LOG"
search mfull \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense unconstrained=$M/seed-0 \
  --defense advtrain=$M/seed-0-advtrain \
  --defense pv=$M/seed-0-pv \
  --defense mfull-feat=$M/seed-0-a-mfull-pre-qf-v2 \
  --sound mfull-feat

echo "(2/4) M_add, full store: madd-feat. Log: $LOG"
search madd \
  --features artifacts/features/ember2024 \
  --threat_model M_add \
  --defense madd-feat=$M/seed-0-a-madd-pre-qf-v2 \
  --sound madd-feat

echo "(3/4) M_full, 10% sums store: PV from all 8 attacks and from the 4 seen. Log: $LOG"
search pv-s10 \
  --features artifacts/features/ember2024-sums-10-v2 \
  --threat_model M_full \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --defense pv-seen=$M/seed-0-s10-pv-seen

if [ -f "$M/seed-0-advtrain-strong/model.txt" ]; then
  echo "(4/4) M_full, full store: run 125's adversarial training. Log: $LOG"
  search advtrain-strong \
    --features artifacts/features/ember2024 \
    --threat_model M_full \
    --defense advtrain-strong=$M/seed-0-advtrain-strong
else
  echo "(4/4) skipped: $M/seed-0-advtrain-strong does not exist yet (run 125)."
fi

echo "Done. Reports: $OUT/{mfull,madd,pv-s10,advtrain-strong}/adaptive.json"
