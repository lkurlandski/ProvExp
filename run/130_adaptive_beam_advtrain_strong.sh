#!/bin/bash
# Run 127's step 4, which it skipped because run 125's model did not exist yet: the beam search (5,000 candidates,
# M_full; run 127's protocol) against the adversarially trained detector of run 125 (seed-0-advtrain-strong), for
# Table 7's adaptive column. FOR ACADEMIC SECURITY RESEARCH ONLY: our own adaptive search against our own detector, on
# our own pilot samples.
#
# Hypothesis: about the rates of the other unconstrained GBDTs under the beam (unconstrained 25/49, run 122's
# adversarial training 20/48): ~20-25 of 49. Training on GAMMA API and header-field outputs does not reach the edits
# the search uses (section names aimed at trusted buckets, renames, imports); greedy already evades 12/49 (run 125).
#
# Result (read 2026-11-05): evaded 24/49 (49%; at 200 candidates 8, at 1,000 17, at 5,000 24); every evasion
# confirmed on re-extraction (evaded_real 24); 35 C1/real mismatches (pefile's unmodeled warning features), no LOST
# lines. Within the hypothesis. The beam evades all 12 files run 125's greedy menus evade (adaptive-twelve) and all 6
# of adaptive-appsec.
#
# Resources: 49 (defense, file) pairs at ~10-20 CPU-min each (run 127): ~45-60 min at 16 workers. Took 2,330 s
# (39 min) at 16 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/a1/adaptive-beam/advtrain-strong
LOG=artifacts/logs/a1_adaptive_beam_advtrain_strong.log

echo "Beam search (5,000 candidates, M_full) x run 125's adversarial training. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir "$OUT" \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense advtrain-strong=$M/seed-0-advtrain-strong \
  --search beam \
  --queries 5000 \
  --checkpoints 200 1000 5000 \
  --beam 3 \
  --draws 2 \
  --patience 3 \
  --seed 0 \
  --num_workers "$NUM_WORKERS" \
  &> "$LOG"
tail -4 "$LOG"
echo "Done. $OUT/adaptive.json"
