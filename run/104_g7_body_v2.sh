#!/bin/bash
# Derivation step 6 (G7), after the body regions were redefined (user, 2026-10-29): the body is each section's mapped
# data plus every run past SizeOfHeaders that no section's raw data claims (gaps and the overlay alike), instead of the
# sections plus pefile's overlay. Reason (run 103, finding 4): a section added after the overlay swallows it under
# pefile's overlay rule, which made every body count fall; with the new regions the old overlay becomes a gap that
# keeps its bytes, and the catalogue declares the overlay's removal for sec/imp (thrember's overlay_size: up -> both
# under every threat model; overlay_entropy and max_entropy were already two-sided).
#   1. the 10% sums store, re-featurized with the new regions (as run 80, into a new directory; run 80 took 0.9 h);
#   2. G1 for sums on the 2,000-file set (as run 102; ~5 min);
#   3. the derivation on the 2,000-file set (as run 102; ~7 min);
#   4. G7 on the 2,000-file set against step 3's directions (the pilot took 135 s for 100 files: ~45-60 min).
# Pilot (Claude, 2026-10-29, `run/103_catalogue_checks.sh` steps re-run with the new regions): G1 for sums exact on
# 100/100; the re-encoded groups keep their directions (M_add/M_shift 1,083 up, M_full 683 up); G7 passes on every
# edit, strict and precondition variants alike. Training inputs vs run 99's: overlay_size dropped (was up) under all
# three threat models, security_virtual_address up (was fixed) under M_add; retraining is step 9.
# Hypothesis: G1 exact on every file; G7 passes on the 2,000 files too (the pilot's adversarial instances cover the
# declared operations; a rarer layout, e.g. a section inside the headers, could still show a violation).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

F=artifacts/features/ember2024-sums-10-v2

echo "Featurizing every 10th shard of ts, vl, tr with the sums extractor into $F. Log: artifacts/logs/featurize-sums-10-v2.log"
python scripts/featurize.py \
  --extractor sums \
  --every 10 \
  --splits ts vl tr \
  --num_workers 16 \
  --outdir "$F" \
  &>> artifacts/logs/featurize-sums-10-v2.log

export OMP_NUM_THREADS=1

echo "G1 (with sums) on the 2,000-file set. Log: artifacts/logs/item_checks_exact_sums_2000_v2.log"
python scripts/item_checks.py exact \
  --files artifacts/explanation_set/ts.parquet \
  --outdir artifacts/experiments/item_checks/exact-sums-2000-v2 \
  --workers 16 \
  --no_g2 \
  --sums \
  &> artifacts/logs/item_checks_exact_sums_2000_v2.log

echo "Derive the directions (with sums) on the 2,000-file set. Log: artifacts/logs/a_directions_derived_sums_2000_v2.log"
python scripts/a_directions.py \
  --derive \
  --extractor sums \
  --files artifacts/explanation_set/ts.parquet \
  --outdir artifacts/experiments/a_directions_derived_sums_2000_v2 \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_sums_2000_v2.log

echo "G7 on the 2,000-file set. Log: artifacts/logs/catalogue_checks_2000.log"
python scripts/catalogue_checks.py \
  --files artifacts/explanation_set/ts.parquet \
  --directions artifacts/experiments/a_directions_derived_sums_2000_v2/directions_sums.csv \
  --outdir artifacts/experiments/catalogue_checks/2000 \
  --workers 16 \
  &> artifacts/logs/catalogue_checks_2000.log

echo "Done. Reports: artifacts/experiments/item_checks/exact-sums-2000-v2/report.json," \
  "artifacts/experiments/catalogue_checks/2000/report.json"
