#!/bin/bash
# §4.4: which clause of the population check each of the 2,000 test files fails (PLAN.md, decision 8 (iv), session 46).
# Separates the files outside the population into incomplete ones (something located past the end of the file) and
# complete ones with an unusual layout, by our copy's 4,000,000-byte truncation and by label.
#
# Took ~3 min with 16 workers (one read per SimpleDB shard).
#
# Results (2026-11-12): of the 1,670 files below 4 MB, 1,576 in the population, 87 incomplete (benign 13, malware 74),
# 7 unusual layouts (benign 1, malware 6). Of the 330 truncated files, 98 in the population, 231 incomplete, 1 unusual
# layout. Section 4.4: 94% / 5% / 0.4% of the test files we use; 5.4: 1.5% of the benign ones outside.

set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
NUM_WORKERS="${NUM_WORKERS:-16}"

mkdir -p artifacts/logs
echo "Population clauses on the 2,000 test files (~3 min). Log: artifacts/logs/population_clauses_2000.log"
python scripts/population_clauses.py \
  --files artifacts/explanation_set/ts.parquet \
  --outdir artifacts/experiments/population_clauses/2000 \
  --workers "$NUM_WORKERS" \
  &> artifacts/logs/population_clauses_2000.log

tail -20 artifacts/logs/population_clauses_2000.log
echo "Done. Report: artifacts/experiments/population_clauses/2000/report.json"
