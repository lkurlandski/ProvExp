#!/bin/bash
# Pushforward faithfulness on MalConv (run 58) with the exact pushforward added as a ranking (docs/theory.md, Pillar B):
# does the exact form remove more of MalConv's evidence than the one-step pushforward the audit uses today? Same 100
# files, zeros fill, budgets, and seeds as run 58; the other rankings reproduce run 58.
# Hypothesis: a small, consistent gain over one step (as run 61's 0.80 -> 0.86), both well above the surrogate.
#
# Smoke-tested on 4 files (32 IG steps, 4 workers): 29 s. Took 14 min (2026-10-16): IG on GPU 1 203 s, 16 workers
# 628 s. Result: exact = one step (median area 6.25 both, ratio 1.00), both 1.9x the surrogate (docs/theory.md).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/pf-malconv-exact-seed0.log
echo "Exact pushforward on MalConv: 100 pilot files, IG on GPU 1, then 16 workers (~14 min)."
echo "Output: artifacts/experiments/pf_malconv/seed-0-exact/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/pf_malconv.py \
  --seed 0 \
  --device cuda:1 \
  --ig_steps 256 \
  --num_workers 16 \
  --exact \
  &> "$LOG"

echo "Done. The deletion table and the paired tests are at the end of $LOG."
