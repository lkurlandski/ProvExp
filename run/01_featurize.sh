#!/bin/bash
# EMBER-2024 features for all three splits, into the feature store. Hours; run in tmux.
# featurize.log + featurize-resume.log: the first run was resumed after an interruption (the script is resumable).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for split in ts vl tr; do
  python scripts/featurize.py --split "$split" --num_workers 16 &>> artifacts/logs/featurize.log
done
