#!/bin/bash
# Tier 2, item 7 (review R14): item-level exactness for every item-stated operation (add section, add imports, both gap
# insertions, rename, both removals). Each operation is written by our own byte-level edit (catalogue.write_*) and
# declared item by item (catalogue.predict_*: the items it adds, removes, or modifies, and those it keeps although it
# writes or moves the bytes that locate them); the C1 engine (provexp.reach.predict_structural) predicts the features,
# which are compared with re-extracting the written file on all 2,480 modeled features (report keys `declared`,
# `declared_mismatches`, `declared_flags`, `exact`). The same run repeats G7 and P1 (runs 107, 117) on the same edits.
# Table 5's item-stated rows come from it.
# Hypothesis: 0 wrong (mismatch or error) under every operation; flags only where the declaration abstains (a forged
# Rich marker in a gap on a file without a Rich header; an entry point in no section; locating ranges past the end of a
# truncated file); G7 passes and the population stays closed, as in run 117.
# Pilot (Claude, 2026-11-03, artifacts/experiments/catalogue_checks/pilot-exact, 252 s): hypothesis held. 0 wrong of
# 2,120 declared edits (1,790 exact, 330 flagged); G7 passes, closed. Flags in the population: ext forged_rich on
# Rich-less files (28), sec/imp on files whose entry point is in no section (30); all other flags outside it.
# Estimate: ~60 min (run 117 took 36 min; the re-extraction and prediction per item-stated edit add about as much).
# Ran 2026-11-03 (Claude, NUM_WORKERS=24, 3436 s / 57 min). Result (read 2026-11-03): G7 passes, population closed.
# Item-stated exactness holds ON THE POPULATION: 0 wrong of 34,965 edits (33,730 exact, 1,235 flagged -- only the two
# by-design abstentions: section:entry 726, richheader:rich_pair 509). report exact=True (population), but
# exact_all_files=False: on 7 truncated out-of-population files (precondition=False) the declarations are wrong on 45
# edits (sec 8, imp 7, ext 21 [16 a split-range ValueError], shf 9); the precondition exists to exclude these.
# Table 5's item-stated rows use the in-population counts (user decision 2026-11-03: scope the rows to the population).
# catalogue_checks now computes `exact`/`declared` on the population and reports `declared_all`/`exact_all_files`.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
# Workers: NUM_WORKERS=32 run/118_item_exactness.sh (default 16).
NUM_WORKERS="${NUM_WORKERS:-16}"

echo "G7 + P1 + item-level exactness on the 2,000-file set (~60 min at 16 workers; using $NUM_WORKERS). Log: artifacts/logs/catalogue_checks_2000_exact.log"
python scripts/catalogue_checks.py \
  --files artifacts/explanation_set/ts.parquet \
  --directions artifacts/experiments/a_directions_derived_sums_2000_v3/directions_sums.csv \
  --outdir artifacts/experiments/catalogue_checks/2000-exact \
  --workers "$NUM_WORKERS" \
  &> artifacts/logs/catalogue_checks_2000_exact.log

tail -2 artifacts/logs/catalogue_checks_2000_exact.log
echo "Done. Report: artifacts/experiments/catalogue_checks/2000-exact/report.json (keys: exact [population], exact_all_files, <op>.declared, <op>.declared_all, <op>.declared_wrong_outside)"
