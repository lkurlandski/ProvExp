#!/bin/bash
# W4 robustness: M1 (run 58) with random fill instead of zeros for the deleted content bytes, so that the pushforward's
# faithfulness on MalConv does not rest on one deletion operator (docs/experiments/pf1.md, "Pushforward faithfulness on
# MalConv"). Same 100 files, rankings, budgets, and seeds as run 58; the fill is seeded per (file, mask).
# Hypothesis: pushforward > surrogate > random features still holds; IG's own lead may shrink if zeros caused it.
#
# Smoke-tested on 4 files (32 IG steps, 4 workers): 21 s. Expect ~9 min, as run 58. GPU 1 for IG (pick another if
# busy), then 16 CPU workers. Run in tmux.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/pf-malconv-random-seed0.log
echo "M1 with random fill: 100 pilot files, IG on GPU 1, then 16 workers (~9 min)."
echo "Output: artifacts/experiments/pf_malconv/seed-0-random/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/pf_malconv.py \
  --seed 0 \
  --device cuda:1 \
  --ig_steps 256 \
  --num_workers 16 \
  --fill random \
  &> "$LOG"

echo "Done. The deletion table and the paired tests are at the end of $LOG."
