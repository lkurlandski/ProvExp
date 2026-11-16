#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
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
# The same rule on the training split gives the learned defenses' material and the donors (session 67): 10,000
# training malware attacked once by the eight toolkit attacks (4-detectors/adversarial-training), and two disjoint
# sets of 100 training goodware as donors: set 0 for that material, set 1 for every attack on the evaluation set (no
# test file in the attacker's hands; R19's donor-overlap control attacks with set 0 instead).
# Output: $OUT_ROOT/2-features/files/ts.parquet (name, label, truncated, ...), tr.parquet, tr-donors-{0,1}.parquet,
# and a .json per list (the counts at each stage). ~1 min (ts) and ~7 min (tr).
# Knobs: FEATURES (a featurized store with ts/ and tr/meta.parquet; default the scale-up's), METADATA (the released
# metadata of build_metadata.py, for the family cap), NUM_SAMPLES (default 2000, half per label), NUM_TRAINING
# (default 20000, half per label), DONORS (per set, default 100), SEED.
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

echo "Training malware and donor sets from $FEATURES/tr. Log: $OUT/logs/files-tr.log"
python pipeline/2-features/files/select_files.py \
  --features "$FEATURES" \
  --metadata "$METADATA" \
  --split tr \
  --num_samples "${NUM_TRAINING:-20000}" \
  --complete_only \
  --donor_sets 2 \
  --donors_per_set "${DONORS:-100}" \
  --seed "${SEED:-0}" \
  --outfile "$OUT/tr.parquet" \
  &> "$OUT/logs/files-tr.log"
echo "Done. Lists: $OUT/tr.parquet, $OUT/tr-donors-{0,1}.parquet"
