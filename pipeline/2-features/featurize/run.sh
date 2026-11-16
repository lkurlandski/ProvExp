#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=featurize
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --time=2-00:00:00
#SBATCH --mem=200G
#
# Feature stores: every file of the splits through each extractor (EMBER's, the re-encoding over sums, the expert set).
# One SimpleDB shard (~1,024 files) per worker; an interrupted run resumes where it stopped.
# Output: $OUT_ROOT/2-features/<extractor>/ (features.npy, meta.parquet, manifest.json).
# Knobs: EXTRACTORS, SPLITS, EVERY (every K-th shard, a random subsample). SCALE-UP: the splits and subsample are a
# protocol item; the time and memory above are guesses until then.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

EXTRACTORS="${EXTRACTORS:-ember2024 sums expert}"
SPLITS="${SPLITS:-tr vl ts}"
EVERY="${EVERY:-1}"
OUT=$OUT_ROOT/2-features
mkdir -p "$OUT/logs"

for x in $EXTRACTORS; do
  echo "Featurizing with $x (splits $SPLITS, every $EVERY). Log: $OUT/logs/featurize-$x.log"
  python pipeline/2-features/featurize/featurize.py \
    --extractor "$x" \
    --splits $SPLITS \
    --every "$EVERY" \
    --num_workers "$NUM_WORKERS" \
    --outdir "$OUT/$x" \
    &> "$OUT/logs/featurize-$x.log"
done
echo "Done. Stores: $OUT/{${EXTRACTORS// /,}}"
