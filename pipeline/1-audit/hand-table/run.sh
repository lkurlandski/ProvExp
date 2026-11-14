#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=hand-table
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=1-00:00:00
#SBATCH --mem=32G
#
# The files that show each error of the hand-written table (Section 5.2, Table 3): the structure witnesses (entry
# section, Rich header, relocations and exports past the end), the overlay and signature witnesses (appends past a
# truncated end), then the counts per error, split by the population. Needs 1-audit/population and
# 1-audit/catalogue-checks on the same FILES (the overlay-size and section-entropy rows come from the catalogue's edits).
# The overlay and signature witnesses run in one process (pilot: runs 88, 98, minutes on 100 files); the time above is
# a guess until the file list is decided.
# Output: $OUT_ROOT/1-audit/hand-table/ ({structure,overlay,signature}/, witness_counts.json).
# Knobs: FILES (required; SCALE-UP: decided with the user), DB.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

: "${FILES:?Set FILES to the file list of the audit (parquet: name, label, truncated).}"
DB="${DB:-$EMBER2024_DATA/ts}"
OUT=$OUT_ROOT/1-audit/hand-table
mkdir -p "$OUT/logs"

echo "Step 1/4: structure witnesses. Log: $OUT/logs/structure.log"
python pipeline/1-audit/hand-table/structure_witness.py \
  --files "$FILES" \
  --db "$DB" \
  --outdir "$OUT/structure" \
  --workers "$NUM_WORKERS" \
  &> "$OUT/logs/structure.log"

echo "Step 2/4: overlay witness (appends past a truncated end). Log: $OUT/logs/overlay.log"
python pipeline/1-audit/hand-table/overlay_witness.py \
  --pilot_files "$FILES" \
  --db "$DB" \
  --outdir "$OUT/overlay" \
  &> "$OUT/logs/overlay.log"

echo "Step 3/4: signature witness (a certificate table completed by an append). Log: $OUT/logs/signature.log"
python pipeline/1-audit/hand-table/signature_witness.py \
  --files "$FILES" \
  --db "$DB" \
  --outdir "$OUT/signature" \
  &> "$OUT/logs/signature.log"

echo "Step 4/4: witness counts per error. Log: $OUT/logs/witness_counts.log"
python pipeline/1-audit/hand-table/witness_counts.py \
  --files "$FILES" \
  --audit "$OUT_ROOT/1-audit" \
  --outdir "$OUT" \
  &> "$OUT/logs/witness_counts.log"
echo "Done. Counts: $OUT/witness_counts.json"
