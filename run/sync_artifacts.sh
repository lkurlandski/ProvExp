#!/bin/bash
# Run on ANOTHER server, from this repository's clone there: copy from the original server (gcis-mkwics-rl) the
# artifacts that run 127 reads, and check that the EMBER-2024 binaries are where the scripts will look for them.
# Not an experiment step (no number). Re-running it only transfers what changed.
#
#   run/sync_artifacts.sh                       # what run 127 needs (~160 MB), plus run 125's model if it exists
#   WITH_STORES=1 run/sync_artifacts.sh         # also the two feature stores (~32 GB): for runs that train models
#
# The dataset is not copied. The scripts read EMBER2024_DATA (default /shared/datasets/EMBER-2024/data;
# src/provexp/data/paths.py), the directory holding one SimpleDB per split (tr, vl, ts). Set it in ~/.bashrc on a
# machine where the dataset lives elsewhere, e.g. export EMBER2024_DATA=/home/lk3591/Documents/datasets/EMBER-2024/data
set -euo pipefail
cd "$(dirname "$0")/.."

SRC_HOST="${SRC_HOST:-lk3591@gcis-mkwics-rl.gccis.rit.edu}"
SRC="${SRC:-/scratch/lk3591/provexp}"
DST="${DST:-/scratch/lk3591/provexp}"

echo "Checking the artifacts symlink -> $DST."
if [ ! -e artifacts ] && [ ! -L artifacts ]; then
  ln -s "$DST" artifacts
fi
if [ "$(readlink -f artifacts)" != "$(readlink -f "$DST")" ]; then
  echo "artifacts points to $(readlink -f artifacts), not $DST; fix it or set DST." >&2
  exit 1
fi
mkdir -p "$DST/logs"

paths=(
  experiments/e1/seed-0/zeros/files.parquet
  features/ember2024/manifest.json
  features/ember2024-sums-10-v2/manifest.json
  models/gbdt/seed-0
  models/gbdt/seed-0-advtrain
  models/gbdt/seed-0-pv
  models/gbdt/seed-0-a-mfull-pre-qf-v2
  models/gbdt/seed-0-a-madd-pre-qf-v2
  models/gbdt/seed-0-s10-pv-all
  models/gbdt/seed-0-s10-pv-seen
)
if [ "${WITH_STORES:-0}" = 1 ]; then
  paths+=(features/ember2024 features/ember2024-sums-10-v2)
fi

echo "Copying ${#paths[@]} paths from $SRC_HOST:$SRC."
printf '%s\n' "${paths[@]}" | rsync -ar --info=progress2 --files-from=- "$SRC_HOST:$SRC/" "$DST/"

echo "Copying run 125's model, if it exists yet (run 127's step 4 skips it otherwise)."
printf '%s\n' models/gbdt/seed-0-advtrain-strong \
  | rsync -ar --ignore-missing-args --files-from=- "$SRC_HOST:$SRC/" "$DST/"

DATA="${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}"
echo "Checking the EMBER-2024 binaries in $DATA (EMBER2024_DATA)."
for split in tr vl ts; do
  if [ ! -d "$DATA/$split" ]; then
    echo "  missing: $DATA/$split. Set EMBER2024_DATA to the directory that holds tr, vl, and ts." >&2
    exit 1
  fi
done
echo "Done. Next: the smoke test in the run/127 discussion (3 files; expect 3/3 evaded at 500, 1,100, 50 queries)."
