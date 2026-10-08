#!/bin/bash
# Compare our features against the released EMBER-2024 features, per split (docs/status.md, "Notes").
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

for split in tr vl ts; do
  python scripts/check_features.py --split "$split" &> "artifacts/logs/check_features-$split.log"
done
