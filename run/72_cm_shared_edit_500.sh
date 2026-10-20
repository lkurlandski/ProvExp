#!/bin/bash
# Section 6.1 at 500 files: run 71's shared-field edits on the first 500 both-detected malware (a superset of run 71's
# 100), to settle whether the GBDT's pullback predicts its drop under MalConv-guided field edits better than windows
# (run 71: Spearman 0.47 vs. 0.25, per-arm CIs of the difference reaching about -0.01). Step 0 is skipped (it passed in
# run 71). Reuses run 71's IG for its 100 files; IG for the other 400 on GPU 3 (~13 min), then the edits on 16 workers
# (~10 min). Run 68's context row covers only its 100 files.
# Hypothesis: the pullback's lead over windows (rho 0.45 vs. 0.20 pooled) holds, with CIs clear of zero.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

OUT=artifacts/experiments/cm_shared_edit_500
echo "Reusing run 71's IG: copying it into $OUT/seed-0/ig."
mkdir -p "$OUT/seed-0/ig"
cp -n artifacts/experiments/cm_shared_edit/seed-0/ig/*.npy "$OUT/seed-0/ig/"

LOG=artifacts/logs/cm-shared-edit-500-seed0.log
echo "500 files: IG for the new 400 on GPU 3 (~13 min), then 5 arms x 500 files on 16 workers (~10 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/cm_shared_edit.py \
  --seed 0 \
  --num_files 500 \
  --num_fields 3 \
  --num_windows 4096 \
  --device cuda:3 \
  --num_workers 16 \
  --outdir "$OUT" \
  &> "$LOG"
echo "Done: tail -n 50 $LOG"
