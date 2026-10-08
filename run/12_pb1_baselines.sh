#!/bin/bash
# PB1's remaining baselines on the same 100 files: occlusion at 64/1,024/4,096 windows (the cost-faithfulness
# curve), KernelSHAP over the 256 windows, and the unsigned pullback ranking (the overshoot test).
#
# This took 6.1 h on 16 workers before the runner was restructured to parallelize within a file; with the current
# runner it should be about 4 h on 16 workers and about 1 h on 64 (docs/pb1_plan.md, "Cost and progress reporting").
# The script prints its predicted cost before starting. Run in tmux.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OMP_NUM_THREADS=1 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 48 \
  --header typical --sweep_windows 64 1024 4096 --kernelshap_samples 2048 --timeout 28800 --tag baselines \
  --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
  &> artifacts/logs/faithfulness-seed0-zeros-typical-baselines.log

python scripts/pb1_tables.py --fill zeros-typical-header-baselines > artifacts/reports/pb1_tables-baselines.md
