#!/bin/bash
# The cost of instrumentation over the 2,000-file explanation set: extraction time with and without provenance, and the
# size of P (boxes stored, nonzeros if expanded), at the median, the 95th percentile, and the truncation length.
# Hypothesis: a few times the reference extraction, growing with file size; P compact as boxes.
#
# Smoke-tested on 20 files. Took ~4 min with 8 workers (2026-10-19). Result: 0.19 s vs. 0.05 s (median file, 356 KB),
# 2.7 s vs. 0.4 s at 4 MB; ~7.8K / 92K boxes (Section 4.1). Timing is per process with 8 concurrent workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/provenance-cost.log
echo "Instrumentation cost: 2,000 files, 8 workers (~4 min)."
echo "Output: artifacts/experiments/provenance_cost/files.parquet"
echo "Log:    $LOG"
OMP_NUM_THREADS=1 python scripts/provenance_cost.py \
  --num_workers 8 \
  &> "$LOG"

echo "Done. The table is at the end of $LOG."
