#!/bin/bash
# Direction A, Table A1's toolkit columns (docs/direction-A-A1-design.md, build steps 2-3). Run after run 80 (it needs
# the 10% sums store and the s10 models). FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et al.'s published secml-malware
# attacks against our own detectors, on our own pilot samples, to evaluate defenses.
#   1. PV selection from the *seen* attacks only (quick split: padding, gamma_sections, gamma_shift, content_shift;
#      the formal version is leave-one-out), from run 78's perturbation vectors
#   2. train the PV-seen monotone GBDT on the same 10% store as the other rows (the re-encoded groups dropped too)
#   3. the eight attacks against six defenses (toolkit columns): s10 ref, PV-seen, C4 on features / sums under M_add
#      and M_full; 1% FPR thresholds, byte cap max(5%, 512 KB), re-extracted ground truth
#   4. the C1-declared adaptive search against the thrember-space defenses (the decisive column; 0 for the C4 rows by
#      construction, nonzero for the unconstrained reference; the sums-space predictors are the scoped remainder)
# Hypothesis: seen evasion ~0 for PV-seen and the C4 rows; held-out evasion > 0 for PV-seen (its hole: Rich header,
# DOS-stub string, section buckets, header fields: header_fields and format_exploit reach these), 0 for the M_full C4
# rows; the M_add C4 rows may be evaded by the M_full attacks (outside their threat model), which is not a failure.
#
# Estimate: step 1 seconds; step 2 ~1-2 min; step 3 ~1-2 h on 16 workers (run 78: 400 runs in ~12 min on 12 workers
# with thrember's extractor; here up to 6 x 400 runs, the sums extractor ~2x slower, monotone defenses stagnate
# early). Step 4 adds a few minutes (C1 predictions, no attack engine).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

F=artifacts/features/ember2024-sums-10
D=artifacts/experiments/a_directions_sums
P=artifacts/experiments/a_pv
M=artifacts/models/gbdt

echo "Step 1/3: PV selection from the seen attacks into $P/pv-seen.*"
python scripts/a_pv_hole.py \
  --deltas $P/deltas.parquet \
  --attacks padding gamma_sections gamma_shift content_shift \
  --tag=-seen \
  --outdir $P
cat $P/pv-seen.neutralize.txt $D/reencoded.neutralize.txt > $P/pv-seen-s10.neutralize.txt

LOG=artifacts/logs/train_classic-gbdt-0-s10-pv-seen.log
echo "Step 2/3: training gbdt/seed-0-s10-pv-seen on $F. Log: $LOG"
python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads 16 \
  --features $F \
  --suffix=-s10-pv-seen \
  --neutralize $P/pv-seen-s10.neutralize.txt \
  --monotone $P/pv-seen.monotone.tsv \
  &> "$LOG"

LOG=artifacts/logs/a1_evaluate.log
echo "Step 3/3: eight attacks x six defenses on the pilot malware. Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir artifacts/experiments/a1/toolkit \
  --features $F \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense madd-feat=$M/seed-0-s10-madd-feat \
  --defense madd-sums=$M/seed-0-s10-madd-sums \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums \
  --num_workers 16 \
  --seed 0 \
  &> "$LOG"

LOG=artifacts/logs/a1_adaptive.log
echo "Step 4/4: the C1-declared adaptive search (thrember-space defenses only; the sums-space predictors are the"
echo "  scoped remainder). Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense unconstrained=$M/seed-0 \
  --defense pv=$M/seed-0-pv \
  --defense madd-feat=$M/seed-0-a-madd-mono-qf \
  --defense mfull-feat=$M/seed-0-a-mfull-mono-qf \
  --sound madd-feat mfull-feat \
  --queries 100 \
  --seed 0 \
  &> "$LOG"

echo "Done. Toolkit table: artifacts/experiments/a1/toolkit/table.json"
echo "      Adaptive (C1-declared): artifacts/experiments/a1/adaptive/adaptive.json"
