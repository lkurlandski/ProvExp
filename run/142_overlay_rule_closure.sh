#!/bin/bash
# R7, PLAN.md step 2b (i), after run 141: closure and exactness on the widened population with LIEF's overlay rule
# (decided by the user, 2026-11-13; docs/evidence/r7-overlay-rule.md). Run 141 found that pefile's overlay rule (the
# overlay starts after the furthest section *or data-directory* extent) lets `ent` move the overlay's start, so the
# widened population was not closed. `features.py` now installs LIEF's rule in pefile at import (the overlay starts
# after the furthest section's raw data, none if that lies past the end); on the population the two rules agree.
#
# Step 0 (Claude, 2026-11-13, ~40 s, done): run 140's table re-derived in place with the new rule. Identical to the
# scratch table below; every mask of M_full (and its control) is byte-identical to run 140's, so the -loose models
# stand. The only cells that change are three of the strict (outside-population) `ren` column.
# Scratch check (Claude, 2026-11-13, 50 of the 100 pilot files, 15 min, pefile's method replaced at interpreter start):
# closed (0 of 6,812 edits on passing files leave), G7 passes (0 violations), exact (1,767 exact, 1,618 declined, 0
# wrong), including 26 files whose debug extent was pointed into the overlay.
# Hypothesis: the same on all 100 pilot files: closed, pass, exact.
# Estimate: ~30 min at 16 workers (the scratch run: 15 min for 50 files).
# Result (read in session 56; 17 min): closed and pass as predicted, exact NOT, through 16 errors (0 wrong). Bases: orig
# 100 files (89 in the population), far 89, near 89, inside 46 (every file with an overlay), all copies in the population;
# 0 of 13,326 edits on passing files leave it; 0 violations; `ent` applied on every passing file and base,
# debug_into_overlay on all 46 overlay files. Declared on passing files: 3,583 exact, 3,201 declined, 16 errors, 0 wrong
# (declines: far 1,557, near 1,557, orig 58, inside 29). The errors: one file (74aecb25...), far/near copies, `sec`/`imp`
# before the overlay. Its certificate table lies inside .rsrc; stretched past the end, it crosses the overlay's start,
# where the insertion lands; the catalogue declared it moved and moving it raised ValueError. Fixed (e0fa5b8): the engine
# declines an insertion that splits an item's members. Re-run on that file: exactly those 16 rows become declines, the
# rest unchanged, so the corrected tally is 3,583 exact, 3,217 declined, 0 wrong. Step 0's table matches the -loose
# models' monotone_constraints feature by feature.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
NUM_WORKERS="${NUM_WORKERS:-16}"
mkdir -p artifacts/logs

S=artifacts/experiments/a_directions_derived_sums_loose

echo "Step 0: the widened table with LIEF's overlay rule into $S (~1 min). Log: artifacts/logs/a_directions_derived_sums_loose.log"
python scripts/a_directions.py \
  --extractor sums \
  --loose \
  --outdir $S \
  --workers "$NUM_WORKERS" \
  &> artifacts/logs/a_directions_derived_sums_loose.log

echo "Step 1: G7 + P1 + exactness on the widened population, all pilot files (~30 min). Log: artifacts/logs/catalogue_checks_pilot_loose_lief.log"
nice -n 10 python scripts/catalogue_checks.py \
  --loose \
  --directions $S/directions_sums.csv \
  --outdir artifacts/experiments/catalogue_checks/pilot-loose-lief \
  --workers "$NUM_WORKERS" \
  &> artifacts/logs/catalogue_checks_pilot_loose_lief.log

tail -1 artifacts/logs/catalogue_checks_pilot_loose_lief.log
echo "Done. Report: artifacts/experiments/catalogue_checks/pilot-loose-lief/report.json (closed, pass, exact)"
