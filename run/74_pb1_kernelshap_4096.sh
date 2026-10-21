#!/bin/bash
# Sections 5.1/5.2 (GBDT): the missing KernelSHAP over 4,096 windows (8 coalitions per window, 32,770 queries per
# file), so that Figures 3-4 have KernelSHAP at every window count that occlusion and adaptive KernelSHAP have. Same
# files and configuration as run 66; everything run 66 computed (occlusion sweep, KernelSHAP at 64/256/1,024, adaptive
# KernelSHAP at every budget) is reused from its window_scores.npz, so pass 1 runs only KernelSHAP@4096; pass 2
# rescores every method (cheap). Output goes to a new directory (tag shared-ks4096); run 66's stays as it is.
# Hypothesis: KernelSHAP@4096 beats KernelSHAP@1024 (6.31) and adaptive@4096 (5.96) under deletion but stays below the
# byte-level pullback (8.03); pushed forward, it continues KernelSHAP's rise with resolution (0.68/0.75/0.83).
#
# Estimate: ~9-10 h on 16 workers. The script's own cost model predicts ~17 h but overestimates on this machine (a
# 2-file smoke of KernelSHAP@1024 ran 2.5-15x faster than predicted; run 66 predicted 12.6 h and took 3.9 h). Scaling
# run 66's actual time by its new work (32,770 vs. ~14,200 extractions per file) gives ~9 h; a refit of the cost model
# on the smoke gives ~10 h. The largest file is one task of ~6 h and starts first. --timeout 86400 (24 h per file),
# since run 66's 10 h could cut off the largest file on a loaded machine.
# Update (2026-10-20): byte counts now use numpy (features.byte_counter; identical features), 2.1x faster per query on
# a 4 MB file and 1.65x on a 0.18 MB file, so expect ~5 h (the largest file ~3 h). The estimates above predate it.
# Smoke-tested on 2 files (2 workers, 20 min): 21 pass-1 tasks reused, only KernelSHAP@4096 ran (19 min on the 0.18 MB
# file, 4x its time at 1,024 windows, as the refit predicts); kernelshap_k4096 and its pushforward are in curves.parquet.
# Result (2026-10-21): clean (100/100 ok, no failures or invalid points); took 8.1 h, not the ~5 h expected. Hypothesis
# held: KernelSHAP@4096 removes 7.17 log-odds (vs. 6.31 at 1,024 windows, adaptive@4096 5.96), below the byte-level
# pullback (8.03), which beats it on 59/100 files (p = 0.005) and at every budget. Pushed forward, it reaches 0.97 of
# TreeSHAP's evidence (0.68/0.75/0.83 at 64/256/1,024). Every run-66 number is reproduced exactly; scripts/paper_figures.py
# now reads this run.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/pb1-shared-ks4096-seed0.log
echo "Sections 5.1/5.2 (GBDT): KernelSHAP over 4,096 windows, 100 pilot files, 16 workers (~5 h)."
echo "Output: artifacts/experiments/e1/seed-0/zeros-typical-header-shared-ks4096/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/faithfulness.py \
  --seed 0 \
  --num_files 100 \
  --num_workers 16 \
  --header typical \
  --classifiers gbdt \
  --sweep_windows 64 1024 4096 \
  --kernelshap_samples 2048 \
  --kernelshap_windows 64 256 1024 4096 \
  --kernelshap_per_window 8 \
  --partition_budgets 64 256 1024 4096 \
  --partition_leaves 16384 \
  --pushforward \
  --trend_explainers treeshap_interventional \
  --tiebreak random \
  --timeout 86400 \
  --tag shared-ks4096 \
  --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
  --reuse_scores artifacts/experiments/e1/seed-0/zeros-typical-header-shared \
  &> "$LOG"

echo "Tables: artifacts/reports/pb1_tables-shared-ks4096.md"
python scripts/pb1_tables.py --seed 0 --fill zeros-typical-header-shared-ks4096 > artifacts/reports/pb1_tables-shared-ks4096.md
echo "Done."
