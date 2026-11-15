#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=files
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=0-04:00:00
#SBATCH --mem=32G
#
# The scale-up's evaluation set (decided with the user, session 67): 1,000 malware and 1,000 benign files of the test
# split, drawn only from the files our copy holds in full (below 4,000,000 bytes), TLSH near-duplicates removed within
# each label, at most 10 files per malware family, seed 0. Every attack runs on its malware and every 1-audit step on
# all of it (their FILES default to this list). The draw reads only the byte-level columns of a featurized store's
# meta (status, size, truncated, TLSH), which do not depend on the extractor's patches, so any store of the test split
# gives the same list.
# Output: $OUT_ROOT/2-features/files/ts.parquet (name, label, truncated, ...) and ts.json (the counts at each stage).
# Knobs: FEATURES (a featurized store with ts/meta.parquet; default the scale-up's), METADATA (the released metadata
# of build_metadata.py, for the family cap), NUM_SAMPLES (default 2000, half per label), SEED.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

FEATURES="${FEATURES:-$OUT_ROOT/2-features/ember2024}"
METADATA="${METADATA:-artifacts/metadata/ember2024.parquet}"
OUT=$OUT_ROOT/2-features/files
mkdir -p "$OUT/logs"

echo "Evaluation set from $FEATURES/ts. Log: $OUT/logs/files.log"
python pipeline/2-features/files/select_files.py \
  --features "$FEATURES" \
  --metadata "$METADATA" \
  --split ts \
  --num_samples "${NUM_SAMPLES:-2000}" \
  --complete_only \
  --seed "${SEED:-0}" \
  --outfile "$OUT/ts.parquet" \
  &> "$OUT/logs/files.log"
echo "Done. List: $OUT/ts.parquet"
