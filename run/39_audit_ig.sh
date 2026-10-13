#!/bin/bash
# 3-C revised (docs/audit_plan.md): MalConv's Integrated Gradients (seed 0, 256 steps, as in 3-A) on the 2,000
# explanation-set files, one part per GPU (2 GPUs in parallel). Files already done are skipped on a re-run.
# Took 33 min on GPUs 0-1 (about 2 s per file); completeness gap median 0.009, max 0.03 log-odds.
# Writes about 9.5 GB (4 bytes per input byte).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

echo "3-C MalConv IG: 2,000 files on GPUs 0-1 (about 35 min)."
echo "Output: artifacts/experiments/audit_discover/seed-0/ig/"
echo "Logs:   artifacts/logs/audit_ig-seed0-part{0,1}.log"
for part in 0 1; do
  CUDA_VISIBLE_DEVICES=$part python scripts/audit_discover.py \
    --seed 0 \
    --phase ig \
    --part $part \
    --num_parts 2 \
    &> "artifacts/logs/audit_ig-seed0-part$part.log" &
done
wait

echo "Done. Check: tail -n 1 artifacts/logs/audit_ig-seed0-part*.log"
