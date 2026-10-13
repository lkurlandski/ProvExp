#!/bin/bash
# Seed-0 scale-up to 500 files (docs/status.md, 2026-10-13), step 1 of 6: KernelSHAP (32,768 coalitions) of the GBDT
# and the MLP for the 500 files of artifacts/explanation_set/ts-scaleup500-seed0.parquet (250 per label, a superset of
# the 100 pilot files; written by faithfulness.py --include ... --select_only). --fill_missing keeps the pilot's 100
# rows and explains only the 400 new ones. Everything after this needs it. Expect about 1.5-2 h on 16 workers (smoke
# test: about 100 s per file and model on one worker).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/explain-kernelshap-scaleup500-seed0.log
echo "Step 1/6: KernelSHAP of the GBDT and MLP for the 400 new files (16 workers, GPU 2, about 1.5-2 h)."
echo "Output: artifacts/explanations/ember2024/seed-0/kernelshap_{gbdt,mlp}.npy (rows filled in place)"
echo "Log:    $LOG"
CUDA_VISIBLE_DEVICES=2 python scripts/explain.py \
  --seed 0 \
  --explainers kernelshap_gbdt kernelshap_mlp \
  --subset artifacts/explanation_set/ts-scaleup500-seed0.parquet \
  --fill_missing \
  --device cuda \
  --workers 16 \
  &> "$LOG"

echo "Done. Check the end of $LOG: '400 of 500 rows' would mean nothing was missing."
