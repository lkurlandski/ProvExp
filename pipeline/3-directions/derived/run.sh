#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=directions
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=0-01:30:00
#SBATCH --mem=280G
#
# The derived direction tables over the re-encoding over sums (Theorem 1): per threat model, the direction each
# operation can move each feature, from the item tables of the files; `strict` for the population before R7's widening,
# `loose` with the certificate and debug entries writable and their data allowed past the end (the paper's tables).
# The corpus (protocol, session 70): the tables are built from training files (the 20,000 of 2-features/files/tr.parquet:
# the defender's data, never the files the detectors are evaluated on), then rebuilt from the evaluation set
# (ts.parquet) as a check, and compare_tables.py reports whether the evaluation set shows a move the tables lack.
# Output: $OUT_ROOT/3-directions/{strict,loose}/ (directions_sums.csv, <threat model>.{neutralize.txt,monotone.tsv}),
# the check's tables $OUT_ROOT/3-directions/check/{strict,loose}/ and its reports check/{strict,loose}.json.
# Knobs: FILES and CHECK_FILES (the corpus and the check's; CHECK_FILES="" skips it), DB and CHECK_DB (a SimpleDB to
# read them from instead of the file store, which holds both lists since session 102), LIMIT (only the first N files
# of each list; smoke tests).
# Cost (job 1011166, 2026-11-16): 54 min on 72 cores, 38 CPU-h, peak 200.5 GiB (memory: the vocabularies); job
# 1243542 (2026-11-20, with hgr, from the SimpleDB): 55 min, 38 CPU-h, peak 240.5 GiB.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

OUT=$OUT_ROOT/3-directions
LISTS=$OUT_ROOT/2-features/files
FILES="${FILES:-$LISTS/tr.parquet}"
DB="${DB:-}"
CHECK_FILES="${CHECK_FILES-$LISTS/ts.parquet}"
CHECK_DB="${CHECK_DB:-}"
LIMIT="${LIMIT:-0}"
mkdir -p "$OUT/logs"

derive() {  # variant, file list, database (empty: the file store), output directory, log
  LOOSE=()
  if [[ $1 == loose ]]; then LOOSE=(--loose); fi
  READ=()
  if [[ -n $3 ]]; then READ=(--db "$3"); fi
  python pipeline/3-directions/derived/directions.py \
    --extractor sums \
    "${LOOSE[@]}" \
    --files "$2" \
    "${READ[@]}" \
    --limit "$LIMIT" \
    --outdir "$4" \
    --workers "$NUM_WORKERS" \
    &> "$5"
}

for variant in strict loose; do
  echo "Direction table ($variant) from $FILES. Log: $OUT/logs/directions-$variant.log"
  derive "$variant" "$FILES" "$DB" "$OUT/$variant" "$OUT/logs/directions-$variant.log"
  if [[ -n $CHECK_FILES ]]; then
    echo "The check's table ($variant) from $CHECK_FILES. Log: $OUT/logs/check-$variant.log"
    derive "$variant" "$CHECK_FILES" "$CHECK_DB" "$OUT/check/$variant" "$OUT/logs/check-$variant.log"
    python pipeline/3-directions/derived/compare_tables.py \
      --table "$OUT/$variant" \
      --check "$OUT/check/$variant" \
      --out "$OUT/check/$variant.json"
  fi
done
echo "Done. Tables: $OUT/{strict,loose}/directions_sums.csv"
