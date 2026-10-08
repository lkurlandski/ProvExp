#!/bin/bash
# PB1: the faithfulness pilot on 100 files, in its three operator variants. About 21 minutes each on 16 workers.
#
# zeros                   level 2: unprotected header fields zeroed, content bytes zeroed
# zeros-typical-header    level 3 (the primary operator): header fields take their most common training value
# random-typical-header   level 3 with random content bytes (robustness)
# random                  level 2 with random content bytes (the first robustness check)
#
# Run before 07's KernelSHAP step (which needs zeros/files.parquet) and again after it, so that the runs include
# the KernelSHAP pullback. The variant directories are named by --fill and --header.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OMP_NUM_THREADS=1 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16 \
  &> artifacts/logs/faithfulness-seed0-zeros.log
OMP_NUM_THREADS=1 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16 --header typical \
  &> artifacts/logs/faithfulness-seed0-zeros-typical.log
OMP_NUM_THREADS=1 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16 --fill random \
  &> artifacts/logs/faithfulness-seed0-random.log
OMP_NUM_THREADS=1 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16 --fill random --header typical \
  &> artifacts/logs/faithfulness-seed0-random-typical.log

for variant in zeros zeros-typical-header random-typical-header; do
  python scripts/pb1_tables.py --fill "$variant" > "artifacts/reports/pb1_tables-$variant.md"
done
