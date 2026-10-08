#!/bin/bash
# The GBDT and MLP for seeds 0-2. About 3 minutes per GBDT with every core (do not set OMP_NUM_THREADS=1 here).
# The GBDT treats the categorical features as numeric, because shap misencodes LightGBM categorical splits.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate

for seed in 0 1 2; do
  python scripts/train_classic.py --learner gbdt --seed "$seed" &> "artifacts/logs/train_classic-gbdt-$seed.log"
  python scripts/train_classic.py --learner mlp --seed "$seed" --device cuda:0 &> "artifacts/logs/train_classic-mlp-$seed.log"
done
