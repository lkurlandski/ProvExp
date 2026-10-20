#!/bin/bash
# Section 6.1, editing the shared fields (docs/experiments/specs.md, "Part A'"; replaces run 68's attack transfer as the
# result): loader-safe edits to 3 fields per file, chosen by the GBDT's pullback and MalConv's IG together, against the
# same number of fields chosen by windows, by one detector, or at random. Run 68's 100 both-detected malware.
# Hypothesis: the shared fields make both detectors drop on the most files; MalConv's own fields barely move the GBDT.
# Outcome (2026-10-20, 1.7 + 1.6 min): shared 32% both-drop vs. random 6%, but MalConv-only 37% (hypothesis failed in
# its comparative part); the pullback predicts the GBDT's drop under MalConv-only edits (rho 0.47 vs. windows 0.25).
# Step 0 (--check) records candidates and evidence only; step 1 edits. Runtimes: IG ~5 min on GPU 3 (100 files),
# check ~2 min, edits ~4 min on 16 workers (only windows that hold a candidate field are occluded).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/cm-shared-edit-check-seed0.log
echo "Step 0, feasibility: IG for 100 files on GPU 3, then candidates and evidence (~7 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/cm_shared_edit.py \
  --seed 0 \
  --check \
  --num_files 100 \
  --num_fields 3 \
  --device cuda:3 \
  --num_workers 16 \
  &> "$LOG"
echo "Check done: tail -n 30 $LOG"

LOG=artifacts/logs/cm-shared-edit-seed0.log
echo "Step 1, the edits: 5 arms x 100 files, GBDT occlusion over 4,096 windows, 16 workers (~4 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/cm_shared_edit.py \
  --seed 0 \
  --num_files 100 \
  --num_fields 3 \
  --num_windows 4096 \
  --device cuda:3 \
  --num_workers 16 \
  &> "$LOG"
echo "Done: tail -n 50 $LOG"
