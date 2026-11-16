#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=file-store
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=0-06:00:00
#SBATCH --mem=32G
#
# The file store (session 69): the bytes of the files the attacks read again and again, in one SQLite file beside the
# lists, $OUT_ROOT/2-features/files/files.sqlite. The SimpleDB decompresses a ~500 MB shard for every file it reads
# (~1.4 s); an attack task loading 1,000 malware and 100 donors spent ~25 min on it with its other cores idle, and
# the material step read each training file once per attack. The loaders (provexp.data.files) read from the store
# whatever it holds and fall back to the SimpleDB, so the step is optional and the results do not depend on it (same
# bytes; each row's SHA-256 is checked on every read).
# Holds: the evaluation set (ts.parquet, 2,000 files), both donor sets, and the training malware the defenses' material
# attacks (tr.parquet's label-1 rows, 10,000; MATERIAL=0 leaves them out). Each shard is decompressed once.
# Input: the lists of 2-features/files. Output: files.sqlite and files.json (counts, size, seconds).
# Knobs: MATERIAL (default 1), NUM_WORKERS (shard readers, ~1 GB of memory each; default 8 here).
# Cost: one shard read per distinct shard (~1.4 s each, up to ~530 per split), ~1-3 h on 8 workers (estimate); size
# ~10-15 GB with the material (estimate; the evaluation set and donors alone ~2-3 GB). SCALE-UP TO CONFIRM.
# Run it again after the lists change (it replaces the store).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
NUM_WORKERS="${NUM_WORKERS:-8}"
source pipeline/common.sh

FILES=$OUT_ROOT/2-features/files
mkdir -p "$FILES/logs"
LISTS=(--list "$FILES/ts.parquet=ts" --list "$FILES/tr-donors-0.parquet=tr" --list "$FILES/tr-donors-1.parquet=tr")
if [[ "${MATERIAL:-1}" == 1 ]]; then LISTS+=(--list "$FILES/tr.parquet=tr:malware"); fi

echo "Building the file store. Log: $FILES/logs/file-store.log"
python pipeline/2-features/file-store/build_store.py \
  --out "$FILES/files.sqlite" \
  "${LISTS[@]}" \
  --num_workers "$NUM_WORKERS" \
  &> "$FILES/logs/file-store.log"
echo "Done. Store: $FILES/files.sqlite"
