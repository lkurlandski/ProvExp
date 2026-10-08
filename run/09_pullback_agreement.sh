#!/bin/bash
# App-R material: how much the explainers agree before and after the pullback, net of a permutation control.
# Also saves the raw per-feature ambiguity and support used by the pilot report.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OMP_NUM_THREADS=1 python scripts/pullback_agreement.py --seed 0 --num_workers 16 \
  &> artifacts/logs/pullback_agreement-seed0.log
