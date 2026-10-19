#!/bin/bash
# Section 6.1 Part A, attack transfer (implementation plan WP4+WP5): a functionality-preserving perturbation of
# MalConv confined to loader-ignored bytes (DOS header, DOS stub, section slack), and whether the GBDT's pullback on
# the original file predicts how much the GBDT's score also drops. The printed summary is also the feasibility read:
# the "go" signal is that the GBDT drop exceeds 1 log-odds (--drop_delta) on a non-trivial share of files, and the
# pullback predicts it better than occlusion over windows or the number of bytes changed. If the GBDT does not move,
# fall back to option 1 (docs/experiments/specs.md).
#
# Smoke-tested on 6 files (GPU 3): end to end in ~1 min. The 256-window GBDT occlusion is the temporary stand-in for
# the best window method of Section 5.1 (run 66). GPU 3, at most 16 workers; ~15-20 min for 100 files.
# For the scale-up, raise --num_files to 500 (and --both_detect to match).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

# Malware both detectors detect, excluding the explanation set and the audit's held-out files.
SEL=artifacts/explanation_set/ts-both-detect-seed0.parquet
echo "Selecting both-detected malware (excluding the explanation set)..."
python scripts/cm_disagreement_select.py \
  --seed 0 \
  --both_detect 600 \
  --exclude artifacts/explanation_set/ts.parquet \
  --out "$SEL"

LOG=artifacts/logs/cm-transfer-seed0.log
echo "Attack transfer: 100 files on GPU 3, 16 workers (~15-20 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/cm_transfer.py \
  --seed 0 \
  --device cuda:3 \
  --num_workers 16 \
  --num_files 100 \
  --max_iterations 50 \
  --per_iteration 64 \
  --selection "$SEL" \
  &> "$LOG"

echo "Done. Summary (read gbdt_drop_over_1.0, malconv_evaded, and the per-predictor Spearman/AUC):"
tail -n 30 "$LOG"
