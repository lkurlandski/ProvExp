#!/bin/bash
# How much of the GBDT's attribution lies on features whose provenance is exactly their Shapley provenance (additive
# features, Proposition Additive Features) vs. the data-flow convention vs. the null element. Existing explanations and
# the census's attributable.npy; no files are read.
# Hypothesis: most attributable attribution sits on additive features (fields, counts, hashed counts).
#
# Took seconds (2026-10-19). Result: interventional TreeSHAP 67% additive, 9% data-flow, 23% null (Section 4.1).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

echo "Attribution by provenance kind (seed 0, 2,000 files); prints a table."
python scripts/theory_coverage.py \
  --seed 0
