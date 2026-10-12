#!/bin/bash
# 3-C revised (docs/audit_plan.md): MalConv's Integrated Gradients (seed 0, 256 steps, as in 3-A) on the 2,000
# explanation-set files, one part per GPU (4 GPUs in parallel). Files already done are skipped on a re-run.
# Smoke test: 2.3 s per file of ~500 KB on one GPU; the set averages 1.2 MB, so about 45-60 min on 4 GPUs.
# Writes about 9.5 GB (4 bytes per input byte).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

echo "3-C MalConv IG: 2,000 files on GPUs 0-3 (about 45-60 min)."
echo "Output: artifacts/experiments/audit_discover/seed-0/ig/"
echo "Logs:   artifacts/logs/audit_ig-seed0-part{0,1,2,3}.log"
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
