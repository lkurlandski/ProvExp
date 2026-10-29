#!/bin/bash
# Derivation step 8 (docs/item-layer-design.md, "The re-encodings come for free"): the four re-encoded groups of
# `SumsFeatureExtractor` (body byte counts, body byte/entropy windows, body strings, the split section buckets) record
# their items and read them as identity readouts over sums, so C4 derives their directions instead of the hand rules.
# Two checks, each on the 100 pilot files (run by Claude, 2026-10-29) and on the 2,000-file set (this script):
#   G1 for sums: the readouts over the sums extractor's item table reproduce its feature vector bit for bit;
#   G3 for sums: the derived directions of the re-encoded groups against the hand rules' re-encoded signs (run 80).
# The derivation also rewrites the training inputs in the sums store's layout ({tm}-pre[-control].{neutralize,
# monotone}); if they equal run 99's, no C4 model needs retraining.
# Hypothesis (from the pilot, where both held): G1 exact on every file; the precondition variant equals the hand rules
# on every (feature, operation) cell of the re-encoded groups, so the training inputs equal run 99's. The strict
# variant makes the re-encoded groups two-sided under append (sections and directories past the end), as it does
# thrember's groups.
#
# Pilot (2026-10-29): G1 exact on 100/100 files (27 s); derivation 36 s: precondition variant equal to the hand rules
# on every cell of the re-encoded groups (M_add/M_shift 1,083 up, 4 both; M_full 683 up, 404 both); thrember's groups
# unchanged per threat model from run 97 (17 fewer over-approximated cells); training inputs identical to run 99's.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

# Steps 1-2 (pilot) were run by Claude; steps 3-4 (2,000 files) are for the user.
echo "G1 (with sums) on the 100 pilot files. Log: artifacts/logs/item_checks_exact_sums_pilot.log"
python scripts/item_checks.py exact \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir artifacts/experiments/item_checks/exact-sums-pilot \
  --workers 16 \
  --no_g2 \
  --sums \
  &> artifacts/logs/item_checks_exact_sums_pilot.log

echo "Derive the directions (with sums) on the 100 pilot files. Log: artifacts/logs/a_directions_derived_sums_pilot.log"
python scripts/a_directions.py \
  --derive \
  --extractor sums \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir artifacts/experiments/a_directions_derived_sums_pilot \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_sums_pilot.log

echo "G1 (with sums) on the 2,000-file set. Log: artifacts/logs/item_checks_exact_sums_2000.log"
python scripts/item_checks.py exact \
  --files artifacts/explanation_set/ts.parquet \
  --outdir artifacts/experiments/item_checks/exact-sums-2000 \
  --workers 16 \
  --no_g2 \
  --sums \
  &> artifacts/logs/item_checks_exact_sums_2000.log

echo "Derive the directions (with sums) on the 2,000-file set. Log: artifacts/logs/a_directions_derived_sums_2000.log"
python scripts/a_directions.py \
  --derive \
  --extractor sums \
  --files artifacts/explanation_set/ts.parquet \
  --outdir artifacts/experiments/a_directions_derived_sums_2000 \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_sums_2000.log

echo "Done. Reports: artifacts/experiments/item_checks/exact-sums-2000/report.json," \
  "artifacts/experiments/a_directions_derived_sums_2000/g3.json (\"sums\")"
