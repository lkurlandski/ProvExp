#!/bin/bash
# R7, PLAN.md step 2b (i): closure and exactness on the widened population (run 140's `--loose` table). G7, P1 and the
# item-level exactness check (runs 107, 117, 118) with `--loose`: the loose precondition, the operation `ent` (the
# certificate and debug entries zeroed, past the end, over the overlay, at a section, random), and every operation also
# applied to escaped copies of each population file: both entries ending far past the end (`far`), one byte past it
# (`near`: an append brings the extents back inside), and, on files with an overlay, the debug extent ending inside the
# overlay (`inside`).
#
# Hypothesis (Claude, 2026-11-13): directions and exactness hold, but closure fails through pefile's overlay rule
# (the overlay starts after the furthest data-directory extent within the file, debug included): an `ent` write
# pointing the debug extent into the overlay, and an append to a `near` copy, move the overlay's start and trip
# plain_layout's overlay clause.
#
# Found while smoke-testing (fixed, 2026-11-13): session 53's loose precondition exempted only the certificate table's
# items, not the overlay and file items located through the debug extent, so a debug entry past the end still failed
# it. Fixed by exempting all of LOOSE_PAST_END_KINDS; run 140's table, masks and population (89) are unchanged.
#
# Result (Claude, 2026-11-13): the hypothesis held in its failure. With plain_layout unchanged (smoke, 4 files), closure
# fails: the `near` copies leave under app/sec/imp (16 edits), as the debug extent comes back inside. A trial fix on the
# whole pilot (the overlay clause evaluated without the debug entry; ~16 min; reverted, not in the code) closes the
# population (0 leaving of 13,234 edits on passing files) but breaks soundness on the files it admits (`inside`, 46
# files): rdb grows the overlay (46 edits, outside rdb's column; inside M_full through `ent`), sec/imp before the
# overlay lower body_strings (7 edits, 1 file), shf's declaration is wrong on 1 file (3 edits), sec/imp declarations
# raise on 17 files. Everything else held: no violation and no wrong declaration on `orig`, `far`, `near` (one 4 MB
# file's declarations raise there); `ent` 0 violations in 1,834 edits. Root cause: pefile's overlay rule reads
# loader-ignored entries (debug; also the architecture entry, run 137's overlay_entry). Decision pending (user).
# The run below is the state after the revert (closure is expected to fail).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
NUM_WORKERS="${NUM_WORKERS:-16}"

echo "G7 + P1 + exactness on the widened population, pilot (~16 min). Log: artifacts/logs/catalogue_checks_pilot_loose.log"
nice -n 10 python scripts/catalogue_checks.py \
  --loose \
  --directions artifacts/experiments/a_directions_derived_sums_loose/directions_sums.csv \
  --outdir artifacts/experiments/catalogue_checks/pilot-loose \
  --workers "$NUM_WORKERS" \
  &> artifacts/logs/catalogue_checks_pilot_loose.log

tail -1 artifacts/logs/catalogue_checks_pilot_loose.log
echo "Done. Report: artifacts/experiments/catalogue_checks/pilot-loose/report.json (closed, pass, exact; <op>.leaving_population_instances)"
