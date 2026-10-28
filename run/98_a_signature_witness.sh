#!/bin/bash
# G3 witness for the signature case (docs/item-layer-design.md, "structures past the end of the file"; rebuilt from
# the 2026-10-27 scratch witness): on every pilot file whose certificate table lies past its end, append zeros up to
# the table and a table copied from a signed pilot file (3 donors per file, smallest first), and re-extract.
# Hypothesis: 4294f2f053c2 reproduces num_certs 0 -> 1; the second file (48d9cc0c855f) may start its table inside the
# file and be skipped.
#
# Took ~2.7 min (2026-10-28). Result: both files have the table entirely past the end (the second file needs a 421 MB
# append, the first 4.9 MB). On all 6 (file, donor) pairs num_certs 0 -> 1 and chain_max_depth 0 -> 4; with timed
# donors, latest_signing_time rises and signing_time_diff moves both ways (-4.6e6 and +6.0e7 s). The hand rules let
# authenticode only fall (rsg); the derived strict table is two-sided, as the witnesses require.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

echo "Signature witness on the pilot files. Log: artifacts/logs/a_signature_witness.log"
python scripts/a_signature_witness.py \
  --outdir artifacts/experiments/a_signature_witness \
  &> artifacts/logs/a_signature_witness.log

echo "Done. Report: artifacts/experiments/a_signature_witness/report.json"
