#!/bin/bash
# Section 5.2 on MalConv under the shared protocol (docs/experiments/specs.md; implementation plan WP3): besides the
# pushforward of Integrated Gradients and the surrogate (run 58), MalConv's own window explanations, which use no
# gradients (occlusion at 64-4,096 windows, KernelSHAP over 64-1,024 windows, adaptive KernelSHAP at budgets matched
# to occlusion), each pushed forward and scored by deleting the bytes it points to. Same 100 files and operator.
# Hypothesis: every pushed-forward source beats random features; gradient-free sources at fine resolution still beat
# the surrogate (answering the circularity objection); IG's pushforward stays on top.
#
# Smoke-tested on 2 files (32 IG steps, small budgets, GPU 3): 1 min. Estimated 2-3 h: phase 1 on GPU 3 (~22K MalConv
# passes per file over ablated copies), phase 2 on 16 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/pf-malconv-shared-seed0.log
echo "Section 5.2 on MalConv, window sources: 100 pilot files, GPU 3, then 16 workers (~2-3 h)."
echo "Output: artifacts/experiments/pf_malconv/seed-0-shared/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/pf_malconv.py \
  --seed 0 \
  --device cuda:3 \
  --ig_steps 256 \
  --num_workers 16 \
  --occlusion_windows 64 256 1024 4096 \
  --kernelshap_windows 64 256 1024 \
  --kernelshap_per_window 8 \
  --partition_budgets 64 256 1024 4096 \
  --partition_leaves 16384 \
  --tag shared \
  &> "$LOG"

echo "Done. The deletion table and the paired tests are at the end of $LOG."
