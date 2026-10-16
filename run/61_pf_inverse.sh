#!/bin/bash
# Go/no-go for the iterated pushforward (docs/theory.md, Pillar B), pilot files, seed 0: recover each GBDT explainer's
# explanation from its pullback (one step, Landweber iterates, the conjugate-gradient limit) at the bytes and at 256
# windows, scored by PF1's feature-space deletion test. Took 17 min on 16 workers (2026-10-16; the last, largest
# files dominate). Run in tmux.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-scores
LOG=artifacts/logs/pf_inverse-seed0.log

echo "Inverse pushforward go/no-go (16 workers, about 17 min)."
echo "Log:    $LOG"
OMP_NUM_THREADS=1 python scripts/pf_inverse.py \
  --run "$RUN" \
  --resolutions 0 256 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Tables: tail -n 80 $LOG"
