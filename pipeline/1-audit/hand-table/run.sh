#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=hand-table
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --time=0-00:30:00
#SBATCH --mem=64G
#
# The files that show each error of the hand-written table (Section 5.2, Table 3): the structure witnesses (entry
# section, Rich header, relocations and exports past the end), the overlay and signature witnesses (appends past a
# truncated end), then the counts per error, split by the population. Needs 1-audit/population and
# 1-audit/catalogue-checks on the same FILES (the overlay-size and section-entropy rows come from the catalogue's edits).
# Every step reads the file store (FILE_STORE) and works over NUM_WORKERS processes. Scale-up job 1018606 (72 cores,
# 200 GB) took 108 min at 2% CPU: each step read its ~2,000 files one by one from the SimpleDB (~35 min a step) and
# the overlay and signature witnesses ran in one process; both fixed in session 85: 8 min on 16 cores, 48 GiB, every
# report identical (diag job 1138358).
# Output: $OUT_ROOT/1-audit/hand-table/ ({structure,overlay,signature}/, witness_counts.json).
# Knobs: FILES (default: the evaluation set of 2-features/files, 1,000 malware and 1,000 benign files).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

FILES="${FILES:-$OUT_ROOT/2-features/files/ts.parquet}"
OUT="${OUT:-$OUT_ROOT/1-audit/hand-table}"
mkdir -p "$OUT/logs"

echo "Step 1/4: structure witnesses. Log: $OUT/logs/structure.log"
python pipeline/1-audit/hand-table/structure_witness.py \
  --files "$FILES" \
  --outdir "$OUT/structure" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/structure.log"

echo "Step 2/4: overlay witness (appends past a truncated end). Log: $OUT/logs/overlay.log"
python pipeline/1-audit/hand-table/overlay_witness.py \
  --pilot_files "$FILES" \
  --outdir "$OUT/overlay" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/overlay.log"

echo "Step 3/4: signature witness (a certificate table completed by an append). Log: $OUT/logs/signature.log"
python pipeline/1-audit/hand-table/signature_witness.py \
  --files "$FILES" \
  --outdir "$OUT/signature" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/signature.log"

echo "Step 4/4: witness counts per error. Log: $OUT/logs/witness_counts.log"
python pipeline/1-audit/hand-table/witness_counts.py \
  --files "$FILES" \
  --audit "$OUT_ROOT/1-audit" \
  --hand_table "$OUT" \
  --outdir "$OUT" \
  &> "$OUT/logs/witness_counts.log"
echo "Done. Counts: $OUT/witness_counts.json"
