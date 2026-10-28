#!/bin/bash
# Derivation step 7, prerequisite: per-structure locating ranges (docs/item-layer-design.md, "Build status"). The one
# shared set (`pe_locating`: every parsed item located through all ten directories' data) is split into header,
# section, and per-directory levels, sound since the pefile guard (run 94) keeps a directory's crash from ending the
# parse. Check G5 (assumption A1) again, on header bytes as in run 91 and, new, on bytes past the header region that
# the parse reads (up to 64 per data directory and per item kind): a flip that changes an item must lie in that item's
# member or locating ranges.
# Hypothesis: header flips still pass (the split only drops directory data that header flips cannot reach); directory
# flips may expose cross-structure reads.
#
# Round 1 (pilot, seed 0; fresh files from the 2,000-file set, seed 1; ~10 min in all): the hypothesis failed on
# both. Header: 11 flips in 11 signed files changed the certificate table (signify reads SizeOfOptionalHeader itself).
# Directories: 184 flips in 2 files added imports (pefile reads each thunk array through its terminating entry, and
# falls back to the import address table when the lookup table looks damaged). A smoke test before had found the
# import names (pefile records an unreadable name as "*invalid*" and aborts after too many). Fix, one rule for
# imports: every byte the import parse reads (descriptors, both thunk arrays through their terminators, names through
# their terminating zero) locates every import and library item; plus SizeOfOptionalHeader for the certificate
# table. The 22 failing flips then all pass.
# Round 2 (below): the pilot files again and 20 files not used for fixing (seed 2). Took ~7.5 min (2026-10-28).
# Result: 0 failures on all four (pilot: 18,944 header and 11,541 directory flips; fresh: 18,432 and 9,749). G5 passes.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

D=artifacts/experiments/item_checks

for region in header directories; do
  echo "G5 ($region) on 20 pilot files. Log: artifacts/logs/item_checks_locating_split_pilot_$region.log"
  python scripts/item_checks.py locating \
    --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
    --outdir $D/locating-split-pilot-$region \
    --region $region \
    --workers 16 \
    &> artifacts/logs/item_checks_locating_split_pilot_$region.log

  echo "G5 ($region) on 20 fresh files from the 2,000-file set. Log: artifacts/logs/item_checks_locating_split_2000_seed2_$region.log"
  python scripts/item_checks.py locating \
    --files artifacts/explanation_set/ts.parquet \
    --outdir $D/locating-split-2000-seed2-$region \
    --region $region \
    --workers 16 \
    --seed 2 \
    &> artifacts/logs/item_checks_locating_split_2000_seed2_$region.log
done

echo "Done. Reports: $D/locating-split-*/report.json"
