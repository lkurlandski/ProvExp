#!/bin/bash
# 3-C revised, post-mortem diagnostic (docs/experiments/audit.md): does MalConv's IG credit hold in the files it was found in?
# For the 20 candidates of run 41 and up to 200 explanation-set files each (where discovery found the pattern), the
# credited bytes are removed in place (padding, IG's baseline; and random bytes), and MalConv re-scores the file;
# control: random bytes elsewhere in the same MalConv window.
# Needs runs 39 and 40. Took 1 min on 16 workers (1,358 occurrences in 696 files); window-local scoring matches full
# forward passes to 1e-5 (smoke test, --check).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_inplace-seed0.log
echo "3-C in-place check: 20 candidates, up to 200 files each, scored by MalConv (16 workers, about 1 min)."
echo "Output: artifacts/experiments/audit_inplace/seed-0/"
echo "Log:    $LOG   (the per-candidate summary is at its end)"
OMP_NUM_THREADS=1 python scripts/audit_inplace.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: tail -n 30 $LOG"
