#!/bin/bash
# Sections 5.1 and 5.2 (GBDT) under the shared protocol (docs/experiments/specs.md; implementation plan WP1-WP2):
# KernelSHAP over windows at 64/256/1,024 windows (8 coalitions per window; 256 reused from run 21) and adaptive
# KernelSHAP (Owen values over 16,384 leaf windows) at budgets matched to occlusion's 64/256/1,024/4,096 windows, plus
# the pushforward of every window explanation, TreeSHAP's resolution trend, and random feature explanations, all scored
# by deleting bytes. Occlusion and the legacy KernelSHAP at 256 windows are reused from run 21 (same files and config).
# KernelSHAP at 4,096 windows (~17 h more) is left for later: add 4096 to --kernelshap_windows and rerun with
# --reuse_scores pointing at this run's output, which then computes only what is missing.
# Hypotheses: adaptive KernelSHAP beats uniform windows at equal cost but stays below the byte-level pullback (5.1);
# pushed-forward window explanations rise with resolution and sit near TreeSHAP's own trend (5.2).
#
# Smoke-tested on 2 files (KernelSHAP 64 and 256, adaptive at 64 with 1,024 leaves): 1 min. Predicted ~120 worker-hours,
# ~7.6 h on 16 workers (the cost model; a file can take twice its prediction).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/pb1-shared-seed0.log
echo "Sections 5.1/5.2 (GBDT), shared protocol: 100 pilot files, 16 workers (~8 h)."
echo "Output: artifacts/experiments/e1/seed-0/zeros-typical-header-shared/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/faithfulness.py \
  --seed 0 \
  --num_files 100 \
  --num_workers 16 \
  --header typical \
  --classifiers gbdt \
  --sweep_windows 64 1024 4096 \
  --kernelshap_samples 2048 \
  --kernelshap_windows 64 256 1024 \
  --kernelshap_per_window 8 \
  --partition_budgets 64 256 1024 4096 \
  --partition_leaves 16384 \
  --pushforward \
  --trend_explainers treeshap_interventional \
  --tiebreak random \
  --timeout 36000 \
  --tag shared \
  --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
  --reuse_scores artifacts/experiments/e1/seed-0/zeros-typical-header-baselines-ties \
  &> "$LOG"

echo "Tables: artifacts/reports/pb1_tables-shared.md"
python scripts/pb1_tables.py --seed 0 --fill zeros-typical-header-shared > artifacts/reports/pb1_tables-shared.md
echo "Done."
