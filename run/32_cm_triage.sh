#!/bin/bash
# 3-A, disagreement triage (PLAN.md, 3-A): 100 test files on which the GBDT and MalConv disagree at 1% FPR (25 per
# cell), explained by interventional TreeSHAP (about 10 s), then A's evidence split by how B reads it (blind / oppose /
# agree), each part deleted against same-size random parts of A's top set. Smoke test: 8 files in 1.3 min on 8
# workers. Expect about 5 min.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

SELECTION=artifacts/explanation_set/ts-disagreement-seed0.parquet
EXPLANATIONS=artifacts/explanations/ember2024-disagreement
LOG=artifacts/logs/cm_triage-seed0.log

echo "Step 1/3: select 25 disagreements per cell (thresholds and cell sizes in ${SELECTION%.parquet}.json)."
python scripts/cm_disagreement_select.py \
  --seed 0 \
  --per_cell 25

echo "Step 2/3: interventional TreeSHAP for the selected files (the explanation set's background)."
echo "Log:    artifacts/logs/explain-disagreement-seed0.log"
mkdir -p "$EXPLANATIONS"
cp artifacts/explanations/ember2024/background.parquet "$EXPLANATIONS"/
python scripts/explain.py \
  --seed 0 \
  --explainers treeshap_interventional \
  --explanation_set "$SELECTION" \
  --outdir "$EXPLANATIONS" \
  --device cuda:1 \
  --workers 16 \
  &> artifacts/logs/explain-disagreement-seed0.log

echo "Step 3/3: triage on 100 files, MalConv on GPU 1, then 16 workers (about 5 min)."
echo "Output: artifacts/experiments/cm_triage/seed-0/"
echo "Log:    $LOG   (the summary is at its end)"
CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=1 python scripts/cm_triage.py \
  --seed 0 \
  --num_workers 16 \
  &> "$LOG"

echo "Done. Summary: sed -n '/files ok/,\$p' $LOG"
