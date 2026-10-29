#!/bin/bash
# Direction A, Table A1's toolkit columns re-run with the derived C4 rows (run 99) as precondition-row detectors.
# Run after run 99. FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et al.'s published secml-malware attacks against our
# own detectors, on our own pilot samples, to evaluate defenses (as run 81).
# Each C4 row is routed (`--route`): a file that passes the precondition check (nothing the parse is located through
# lies past the end of the file; catalogue.precondition) is scored by the C4 model, any other by the unconstrained
# reference, each at its own 1% FPR threshold; the check is made on every file the attack queries. table.json splits
# every group by whether the original file passes the check (the guarantee covers those; the others are the
# reference's). The reference and PV-seen rows are run 81's models, unrouted.
# Step 2: the C1-declared adaptive search against the thrember-space defenses (as run 81 step 4) with the derived models;
# unrouted, so its C4 rows hold for the files that pass the check, and the failing files fall to the unconstrained
# row (read its per-file results for them).
# Hypothesis: seen and held-out evasion of the routed C4 rows on passing files as in run 81 (0 for M_full); on failing
# files (12 of the pilot malware, 8 truncated) as for the reference; the adaptive column 0 on passing files by
# construction.
#
# Estimate: as run 81's toolkit part (~47 min on 16 workers) plus the check per query (smoke test: 2 files, padding,
# routed runs 0.7-4 s vs 0.7-2 s unrouted), ~1-1.5 h; the adaptive search a few minutes.
# Ran 2026-10-28 (started by the user): 1,920 attack runs in 2.4 h on 16 workers; adaptive ~20 min. Result: as
# hypothesised on passing files (38/50 pilot malware): seen 0 for every routed row, held-out 0/28 and 0/30 for M_full
# (M_add 9/33 and 16/32, all header_fields, outside M_add). Failing files: every routed row 0/12 seen, 1/12 held-out
# (one file, header_fields, reference branch) against the reference's own 4/12 (three GAMMA API runs that the routed
# search does not find). Adaptive: unconstrained 10/49, PV 22/22, both C4 rows 0/45 (0/12 on failing files, where the
# unconstrained model is also 0/12). Details: docs/direction-A-A1-design.md, "Re-run with derived directions".
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

F=artifacts/features/ember2024-sums-10
M=artifacts/models/gbdt

LOG=artifacts/logs/a1_evaluate_derived.log
echo "Step 1/2: eight attacks x six defenses (four routed) on the pilot malware. Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir artifacts/experiments/a1/toolkit-derived \
  --features $F \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense madd-feat=$M/seed-0-s10-madd-feat-pre \
  --defense madd-sums=$M/seed-0-s10-madd-sums-pre \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat-pre \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums-pre \
  --route madd-feat=ref \
  --route madd-sums=ref \
  --route mfull-feat=ref \
  --route mfull-sums=ref \
  --num_workers 16 \
  --seed 0 \
  &> "$LOG"

LOG=artifacts/logs/a1_adaptive_derived.log
echo "Step 2/2: the C1-declared adaptive search with the derived models. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive-derived \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense unconstrained=$M/seed-0 \
  --defense pv=$M/seed-0-pv \
  --defense madd-feat=$M/seed-0-a-madd-pre-qf \
  --defense mfull-feat=$M/seed-0-a-mfull-pre-qf \
  --sound madd-feat mfull-feat \
  --queries 100 \
  --seed 0 \
  &> "$LOG"

echo "Done. Toolkit table: artifacts/experiments/a1/toolkit-derived/table.json"
echo "      Adaptive: artifacts/experiments/a1/adaptive-derived/adaptive.json"
