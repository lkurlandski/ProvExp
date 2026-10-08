#!/bin/bash
# CP: the statistics of P coarsened to the window counts of PB1's sweep, on the 100 PB1 files. About 3 minutes.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OMP_NUM_THREADS=1 python scripts/cp_coarsening.py \
  --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
  --num_workers 6 \
  &> artifacts/logs/cp_coarsening-seed0.log
