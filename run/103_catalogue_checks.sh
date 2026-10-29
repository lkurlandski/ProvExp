#!/bin/bash
# Derivation step 6, the catalogue check G7 (docs/item-layer-design.md): every operation of the threat models applied
# to real files with our own byte-level edits, including adversarial parameters (repeated or case-variant DLL names,
# an import with no functions, empty, colliding, and case-variant section names, printable content next to strings,
# a forged Rich header in the DOS stub and in an inserted gap; a section's data after or before the overlay), each
# edited file re-extracted with the sums extractor, and every moved feature checked against the derived signs of its
# operation (strict variant on every file, precondition variant on the files that pass the check). For in-place edits
# and appends, the C1 engine also predicts the edited file (G6 with adversarial contents).
# Hypothesis: the in-place operations and append hold (their changes are derived from bytes, G5/G6 checked them); the
# declared structural operations (sec, imp, ext, shf) are where a declaration can miss something.
#
# Pilot, first pass (Claude, 2026-10-29; 128 s; directions of run 102's pilot step): in-place operations and append
# hold, C1 exact or flagged except 8 forged-Rich DOS writes. Four findings, each fixed by one rule except the last:
#   1. C1: a forged Rich block in the DOS stub of a file without a Rich header creates one (num_pairs 0 -> 2); no item
#      located it. Rule: a structure found by searching a range is located by that range also when the search finds
#      nothing (an empty rich_pair item). No feature value changes (G1 below).
#   2. Strict: adding a section or imports and the insertions lengthen the file, so they too can complete structures
#      past its end (12 failing files: section counts, overlay). Rule: every lengthening operation gets the past-end
#      flags, not just append. Changes only the strict variant.
#   3. A section placed before the overlay (as LIEF places it) moves the certificate table: security_virtual_address
#      up. Declared for sec (and so imp), as for the insertions. M_add (precondition): fixed -> up, which adds one
#      monotone constraint to the M_add C4 models (the only training-input change; retrain in step 9).
#   4. Open, for the user: a section placed after the overlay swallows it under pefile's overlay rule (overlay_size,
#      overlay_entropy, max_entropy down), and the old overlay bytes leave the body regions (body_* down). Every pilot
#      file with an overlay that passes the precondition (31). See docs/status.md.
# (Also fixed in the check itself: on a file whose last section runs past the end, "before the overlay" must mean past
# every section's raw data.)
# Second pass (after the fixes): strict variant holds everywhere; precondition variant holds except finding 4
# (124 sec + 120 imp edits, all after-overlay, 31 files); C1 exact or flagged on every in-place edit and append.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

echo "G1 (with sums) on the 100 pilot files after the Rich fix. Log: artifacts/logs/item_checks_exact_sums_pilot_g7.log"
python scripts/item_checks.py exact \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir artifacts/experiments/item_checks/exact-sums-pilot-g7 \
  --workers 16 \
  --no_g2 \
  --sums \
  &> artifacts/logs/item_checks_exact_sums_pilot_g7.log

echo "Derive the directions with the fixed catalogue (pilot). Log: artifacts/logs/a_directions_derived_sums_pilot_g7.log"
python scripts/a_directions.py \
  --derive \
  --extractor sums \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --outdir artifacts/experiments/a_directions_derived_sums_pilot_g7 \
  --workers 16 \
  &> artifacts/logs/a_directions_derived_sums_pilot_g7.log

echo "G7 on the 100 pilot files. Log: artifacts/logs/catalogue_checks_pilot.log"
python scripts/catalogue_checks.py \
  --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
  --directions artifacts/experiments/a_directions_derived_sums_pilot_g7/directions_sums.csv \
  --outdir artifacts/experiments/catalogue_checks/pilot \
  --workers 16 \
  &> artifacts/logs/catalogue_checks_pilot.log
