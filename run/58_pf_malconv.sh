#!/bin/bash
# M1: is the pushforward faithful on MalConv, the model the audit pushes forward? (docs/experiments/mocks.md, M1;
# revision plan item 10; Section 5.1's blue placeholder.)
#
# MalConv never computes the features, so each feature-space explanation of it is pulled back through P and its top
# bytes deleted with PB1's operator; MalConv scores every deleted file. Rankings: the pushforward of MalConv's IG (the
# method), the surrogate's TreeSHAP (the realistic alternative), random feature explanations (the floor); references
# IG per byte, IG over 256 windows, and random windows. PB1's 100 pilot files, seed 0.
# Hypothesis: pushforward > surrogate > random features; pushforward < IG itself (grouping into features blurs IG).
#
# Smoke-tested on 4 files (32 IG steps, 4 workers): 22 s, every deletion verified. Expect ~10 min here (cm_check,
# which does similar work, took ~10 min). GPU 1 for IG (pick another if busy), then 16 CPU workers. Run in tmux.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/pf-malconv-seed0.log
echo "M1, pushforward faithfulness on MalConv: 100 pilot files, IG on GPU 1, then 16 workers (~10 min)."
echo "Output: artifacts/experiments/pf_malconv/seed-0/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/pf_malconv.py \
  --seed 0 \
  --device cuda:1 \
  --ig_steps 256 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. The deletion table and the paired tests are at the end of $LOG."
