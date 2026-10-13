#!/bin/bash
# CP: the provenance census of the explanation set. About 30 minutes on 16 workers.
#
# Run twice: the first census (now census-2026-10-07/) used the previous definitions of ambiguity and overlap, which
# saturated; the second uses the definitions adopted on 2026-10-08 and also writes the group confusion matrix, the
# spectrum of M, the element-side statistics, and each explanation's round-trip bound (docs/experiments/cp.md).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

# The first census is kept for comparison; move it aside rather than overwriting it.
if [ -d artifacts/explanations/ember2024/seed-0/census ] && \
   ! grep -q statistics artifacts/explanations/ember2024/seed-0/census/report.json 2>/dev/null; then
  mv artifacts/explanations/ember2024/seed-0/census artifacts/explanations/ember2024/seed-0/census-2026-10-07
fi

OMP_NUM_THREADS=1 python scripts/provenance_census.py --seed 0 --num_workers 16 \
  &> artifacts/logs/provenance_census-seed0-v2.log
python scripts/cp_tables.py --seed 0 > artifacts/reports/cp_tables-seed0.md
