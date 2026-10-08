#!/bin/bash
# Stage-1 explanations of the explanation set (TreeSHAP path and interventional, IG, gradient x input), then
# KernelSHAP for the 100 PB1 files only (32,768 coalitions is far too slow for all 2,000).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

python scripts/explain.py --seed 0 --device cuda:0 --workers 16 &> artifacts/logs/explain-seed0.log

# Run after 11_pb1_pilot.sh, which creates the files.parquet that names the 100 files. About 5 min per model.
python scripts/explain.py --explainers kernelshap_gbdt kernelshap_mlp \
  --subset artifacts/experiments/e1/seed-0/zeros/files.parquet --workers 16 \
  &> artifacts/logs/explain-kernelshap-seed0.log
