#!/bin/bash
# The directory-parser guard (features.py, "Correctness: a crash in one directory's parser loses only that directory";
# docs/upstream-issues.md, item 5): re-extract the rows both feature stores hold as not a PE (is_pe = 0) and rewrite
# those that change. The guard only stops crashes, so no row whose file parsed can change. Old values are kept in
# {store}/patches/directory_guard.old.npy.
# Hypothesis: 394 of the 1,235 non-PE rows of the full store change (re-parsed 2026-10-27: 76 debug-entry crashes,
# 304 dynamic relocation crashes, 14 others, all inside directory parsers), about a tenth of that in the sums store;
# the other 841 raise PEFormatError and stay non-PE.
#
# Took ~6 min (2026-10-27). Result: hypothesis held. Full store: 394 rows rewritten (tr 253, vl 41, ts 100) of 1,235
# non-PE rows; sums store: 47 (tr 35, vl 4, ts 8) of 124. None of the 100 pilot files is among them.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

echo "Full store. Log: artifacts/logs/refeaturize_nonpe.log"
python scripts/refeaturize_nonpe.py \
  --store artifacts/features/ember2024 \
  --extractor ember2024 \
  &> artifacts/logs/refeaturize_nonpe.log

echo "Sums store (every 10th shard). Log: artifacts/logs/refeaturize_nonpe_sums.log"
python scripts/refeaturize_nonpe.py \
  --store artifacts/features/ember2024-sums-10 \
  --extractor sums \
  &> artifacts/logs/refeaturize_nonpe_sums.log

echo "Done. Rows rewritten: artifacts/features/*/patches/directory_guard.parquet"
