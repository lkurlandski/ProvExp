#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=file-store
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=0-00:45:00
#SBATCH --mem=48G
#
# The file store (session 69): the bytes of the files the attacks read again and again, in one SQLite file beside the
# lists, $OUT_ROOT/2-features/files/files.sqlite. The SimpleDB decompresses a ~500 MB shard for every file it reads
# (~1.4 s); an attack task loading 1,000 malware and 100 donors spent ~25 min on it with its other cores idle, and
# the material step read each training file once per attack. The scale-up's loaders (provexp.data.files) read only
# from the store, which FILE_STORE names (pipeline/common.sh), and stop if it or a file is missing: the step is
# required. Same bytes as the SimpleDB; each row's SHA-256 is checked on every read.
# Holds: the evaluation set (ts.parquet, 2,000 files), both donor sets, and the training files (tr.parquet, 20,000: the
# malware the defenses' material attacks, and all of them for the direction tables, 3-directions/derived; session 102:
# the SimpleDB is fast to iterate, slow to read by name). TRAINING=malware keeps only the malware, TRAINING=none
# none. Each shard is decompressed once.
# Input: the lists of 2-features/files. Output: files.sqlite and files.json (counts, size, seconds).
# Knobs: TRAINING (all, the default; malware; none), NUM_WORKERS (shard readers, ~1 GB of memory each; default 8 here).
# Cost: one shard read per distinct shard (~1.4 s each, up to ~530 per split). Job 1011150 (12,200 files, training
# malware only): 11 min on 8 workers, peak 32.5 GiB, 9.3 GB store; all training files: ~13 GB (estimate).
# Run it again after the lists change (it replaces the store).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
NUM_WORKERS="${NUM_WORKERS:-8}"
source pipeline/common.sh

FILES=$OUT_ROOT/2-features/files
mkdir -p "$FILES/logs"
LISTS=(--list "$FILES/ts.parquet=ts" --list "$FILES/tr-donors-0.parquet=tr" --list "$FILES/tr-donors-1.parquet=tr")
case "${TRAINING:-all}" in
  all) LISTS+=(--list "$FILES/tr.parquet=tr") ;;
  malware) LISTS+=(--list "$FILES/tr.parquet=tr:malware") ;;
  none) ;;
  *) echo "TRAINING must be all, malware or none, got ${TRAINING}" >&2; exit 1 ;;
esac

echo "Building the file store. Log: $FILES/logs/file-store.log"
python pipeline/2-features/file-store/build_store.py \
  --out "$FILES/files.sqlite" \
  "${LISTS[@]}" \
  --num_workers "$NUM_WORKERS" \
  &> "$FILES/logs/file-store.log"
echo "Done. Store: $FILES/files.sqlite"
