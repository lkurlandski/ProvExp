#!/bin/bash
# Section 6.1, Table 2: a second window baseline, the GBDT's KernelSHAP over 4,096 windows (8 coalitions per window,
# 32,770 queries per file, as in Section 5.1, where it is the strongest direct method; run 74), next to occlusion. Run
# 72 again on the same 500 both-detected malware with --kernelshap; everything else is deterministic, so every run-72
# number should reproduce exactly (a check). Reuses run 72's IG (no GPU needed). New output directory; run 72's stays.
# Hypothesis: KernelSHAP predicts the GBDT's drop under MalConv-guided edits better than occlusion (rho 0.21) but well
# below the pullback (0.48), around 0.25-0.35: the fields are a few bytes next to other header content the GBDT reads,
# and a window of ~300 bytes spreads one value over all of it however well it is explained. If KernelSHAP reaches the
# pullback, 6.1's claim weakens: stop and decide before writing. The manuscript carries predicted values in blue
# (rho 0.31, AUC 0.65, CI of the rho difference 0.09-0.26).
#
# Estimate: ~32 h on 16 workers. Run 74's KernelSHAP@4096 times fit 0.0026 s per byte + 290 s per file; these 500 files
# average 1.3 MB (144 over 2 MB), giving ~512 CPU-hours; the largest file is ~3 h. Smoke-tested (2026-10-21) on 3
# files (3.5 KB, 4 KB, 60 KB) with run 72's IG, 3 workers: KernelSHAP 141/162/394 s per file (the model predicts
# ~300/300/450 s), no failed coalitions, and every run-72 column reproduced exactly.
# Phase 1b caches KernelSHAP per file in $OUT/seed-0/kernelshap/; if the run is interrupted, rerun this script and it
# resumes there (the edits of phase 2 take ~10 min).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OUT=artifacts/experiments/cm_shared_edit_500_ks
echo "Reusing run 72's IG: copying it into $OUT/seed-0/ig."
mkdir -p "$OUT/seed-0/ig"
cp -n artifacts/experiments/cm_shared_edit_500/seed-0/ig/*.npy "$OUT/seed-0/ig/"

LOG=artifacts/logs/cm-shared-edit-500-ks-seed0.log
echo "Section 6.1: KernelSHAP over 4,096 windows on 500 files, 16 workers (~32 h)."
echo "Log: $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/cm_shared_edit.py \
  --seed 0 \
  --num_files 500 \
  --num_fields 3 \
  --num_windows 4096 \
  --kernelshap \
  --kernelshap_per_window 8 \
  --device cpu \
  --num_workers 16 \
  --outdir "$OUT" \
  &> "$LOG"
echo "Done: tail -n 50 $LOG"
