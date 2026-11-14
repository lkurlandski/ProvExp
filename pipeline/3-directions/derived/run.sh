#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=sporc
#SBATCH --job-name=directions
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=0-04:00:00
#SBATCH --mem=32G
#
# The derived direction tables over the re-encoding over sums (Theorem 1): per threat model, the direction each
# operation can move each feature, from the item tables of the files; `strict` for the population before R7's widening,
# `loose` with the certificate and debug entries writable and their data allowed past the end (the paper's tables).
# Output: $OUT_ROOT/3-directions/{strict,loose}/ (directions_sums.csv, <threat model>.{neutralize.txt,monotone.tsv}).
# Knobs: FILES (the file list, default the script's: the pilot files). SCALE-UP: the file list is a protocol item.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

OUT=$OUT_ROOT/3-directions
mkdir -p "$OUT/logs"
FILES_ARG=()
if [[ -n "${FILES:-}" ]]; then FILES_ARG=(--files "$FILES"); fi

for variant in strict loose; do
  LOOSE=()
  if [[ $variant == loose ]]; then LOOSE=(--loose); fi
  echo "Direction table ($variant). Log: $OUT/logs/directions-$variant.log"
  python pipeline/3-directions/derived/directions.py \
    --extractor sums \
    "${LOOSE[@]}" \
    "${FILES_ARG[@]}" \
    --outdir "$OUT/$variant" \
    --workers "$NUM_WORKERS" \
    &> "$OUT/logs/directions-$variant.log"
done
echo "Done. Tables: $OUT/{strict,loose}/directions_sums.csv"
