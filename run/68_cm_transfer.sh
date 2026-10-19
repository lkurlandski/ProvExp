#!/bin/bash
# Section 6.1 Part A, attack transfer (implementation plan WP4 gate + WP5): a functionality-preserving perturbation of
# MalConv confined to loader-ignored bytes (DOS header, DOS stub, section slack), and whether the GBDT's pullback on
# the original file predicts how much the GBDT's score also drops. Also the feasibility gate: the "go" criterion is
# that the GBDT drop exceeds 1 log-odds on a non-trivial share of files (--drop_delta).
# Hypothesis: the pullback's evidence on the editable region predicts the GBDT drop better than occlusion over windows
# or the number of bytes changed. Gate risk: the GBDT may not move, in which case fall back to option 1 (specs.md).
#
# Smoke-tested on 6 files (10 iterations, GPU 3): 1 min, end to end. The GBDT occlusion baseline (256 windows) is the
# temporary stand-in for the best window method of Section 5.1 (run 66). GPU 3, at most 16 workers.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

# The selection: malware both detectors detect, excluding the explanation set and the audit's held-out files.
SEL=artifacts/explanation_set/ts-both-detect-seed0.parquet
echo "Selecting both-detected malware (excluding the explanation set)..."
python scripts/cm_disagreement_select.py \
  --seed 0 \
  --both_detect 600 \
  --exclude artifacts/explanation_set/ts.parquet \
  --out "$SEL"

# Gate: 50 files first. Read gbdt_drop_over_1.0 and malconv_evaded in the printed summary before the full run.
LOG=artifacts/logs/cm-transfer-gate-seed0.log
echo "Gate: 50 files on GPU 3, 16 workers (~15 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/cm_transfer.py \
  --seed 0 \
  --device cuda:3 \
  --num_workers 16 \
  --num_files 50 \
  --max_iterations 50 \
  --per_iteration 64 \
  --selection "$SEL" \
  --tag gate \
  &> "$LOG"
echo "Gate summary:"; tail -n 30 "$LOG"

# Full run (100 at pilot; raise --num_files to 500 for the scale-up). Comment out until the gate passes.
# LOG=artifacts/logs/cm-transfer-seed0.log
# echo "Full: 100 files on GPU 3, 16 workers. Log: $LOG"
# OMP_NUM_THREADS=1 python scripts/cm_transfer.py \
#   --seed 0 --device cuda:3 --num_workers 16 --num_files 100 \
#   --max_iterations 50 --per_iteration 64 --selection "$SEL" \
#   &> "$LOG"
# tail -n 30 "$LOG"
