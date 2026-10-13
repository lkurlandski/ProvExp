#!/bin/bash
# Seed-0 scale-up, step 5 of 6: comparing the GBDT and MalConv (paper Section 4.3).
#   (a) cross-deletion and (b) shared reliance on step 2's 500 files, reusing its GBDT occlusion scores (needs step 2);
#   (c) disagreement triage on 100 disagreements per cell (4 cells: 400 files; the pilot had 25), byte level with zero
#       and random fill, then (d) at 256 windows on the two GBDT-flagged cells (200 files), the GBDT's window evidence
#       from its pullback and from its occlusion. (c)-(d) do not need step 2.
# MalConv runs on GPU 3. Expect about 2.5-3.5 h on 16 workers in all.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

RUN=artifacts/experiments/e1/seed-0/zeros-typical-header-scaleup500
SELECTION=artifacts/explanation_set/ts-disagreement-scaleup-seed0.parquet
EXPLANATIONS=artifacts/explanations/ember2024-disagreement-scaleup
export CUDA_VISIBLE_DEVICES=3

echo "Step 5/6 (a): cross-deletion on 500 files (GPU 3, 16 workers, about 50 min)."
echo "Output: artifacts/experiments/cm_check-scaleup500/seed-0/"
echo "Log:    artifacts/logs/cm_check-seed0-scaleup500.log"
OMP_NUM_THREADS=1 python scripts/cm_check.py \
  --seed 0 \
  --pb1_run "$RUN" \
  --outdir artifacts/experiments/cm_check-scaleup500 \
  --num_workers 16 \
  &> artifacts/logs/cm_check-seed0-scaleup500.log
python scripts/cm_tables.py \
  --run artifacts/experiments/cm_check-scaleup500/seed-0 \
  > artifacts/reports/cm_tables-scaleup500.md

echo "Step 5/6 (b): shared reliance on 500 files (GPU 3, 16 workers, about 30 min)."
echo "Output: artifacts/experiments/cm_shared-scaleup500/seed-0/"
echo "Log:    artifacts/logs/cm_shared-seed0-scaleup500.log"
OMP_NUM_THREADS=1 python scripts/cm_shared.py \
  --seed 0 \
  --pb1_run "$RUN" \
  --outdir artifacts/experiments/cm_shared-scaleup500 \
  --num_workers 16 \
  &> artifacts/logs/cm_shared-seed0-scaleup500.log

echo "Step 5/6 (c): select 100 disagreements per cell and explain them with interventional TreeSHAP."
echo "Selection: $SELECTION   Log: artifacts/logs/explain-disagreement-scaleup-seed0.log"
python scripts/cm_disagreement_select.py \
  --seed 0 \
  --per_cell 100 \
  --out "$SELECTION"
mkdir -p "$EXPLANATIONS"
cp artifacts/explanations/ember2024/background.parquet "$EXPLANATIONS"/
python scripts/explain.py \
  --seed 0 \
  --explainers treeshap_interventional \
  --explanation_set "$SELECTION" \
  --outdir "$EXPLANATIONS" \
  --device cuda \
  --workers 16 \
  &> artifacts/logs/explain-disagreement-scaleup-seed0.log
for FILL in zeros random; do
  LOG=artifacts/logs/cm_triage-seed0-scaleup-$FILL.log
  echo "Step 5/6 (c): triage on 400 files, $FILL fill (GPU 3, 16 workers, about 20 min). Log: $LOG"
  OMP_NUM_THREADS=1 python scripts/cm_triage.py \
    --seed 0 \
    --selection "$SELECTION" \
    --explanations "$EXPLANATIONS" \
    --fill "$FILL" \
    --outdir artifacts/experiments/cm_triage-scaleup \
    --num_workers 16 \
    &> "$LOG"
done
for SOURCE in pullback occlusion; do
  LOG=artifacts/logs/cm_triage-seed0-scaleup-zeros-w256-$SOURCE.log
  echo "Step 5/6 (d): triage at 256 windows, GBDT evidence from its $SOURCE, 200 GBDT-flagged files. Log: $LOG"
  OMP_NUM_THREADS=1 python scripts/cm_triage.py \
    --seed 0 \
    --selection "$SELECTION" \
    --explanations "$EXPLANATIONS" \
    --windows 256 \
    --gbdt_windows "$SOURCE" \
    --cells benign_gbdt_only malware_gbdt_only \
    --outdir artifacts/experiments/cm_triage-scaleup \
    --num_workers 16 \
    &> "$LOG"
done
echo "Done. Outputs: artifacts/experiments/cm_{check,shared}-scaleup500/seed-0/, cm_triage-scaleup/seed-0/*; tables: artifacts/reports/cm_tables-scaleup500.md"
