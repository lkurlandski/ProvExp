#!/bin/bash
# The check that a reorganization of the code changed no computation: five computations of the pipeline on a small
# pilot slice, through their run.sh, compared with the old code's outputs of run/146_refactor_baseline.sh (tag
# pilot-final) by compare_outputs.py. Any difference is a bug in the move. ~10 min on 16 workers.
#   featurization (three extractors, two test shards); the direction tables, strict and loose; the catalogue check on
#   5 files; the extraction-scored adaptive search (3 malware, 200 candidates, with and without the debug-entry escape);
#   MAB-Malware (3 malware).
# Usage: pipeline/setup/identity_check.sh [old outputs, default artifacts/refactor-baseline/old]
set -euo pipefail
cd "$(dirname "$0")/../.."
OLD="${1:-artifacts/refactor-baseline/old}"
export OUT_ROOT="${OUT_ROOT:-artifacts/refactor-baseline/new-pipeline}"
# The steps skip outputs that exist (to resume on the cluster), so the check starts from an empty directory: a stale
# output would be compared instead of a fresh one.
if [[ -e $OUT_ROOT ]]; then
  if [[ $OUT_ROOT != artifacts/refactor-baseline/* ]]; then
    echo "$OUT_ROOT exists; give an OUT_ROOT that does not, or remove it." >&2
    exit 1
  fi
  echo "Removing the previous check's outputs, $OUT_ROOT."
  rm -rf "$OUT_ROOT"
fi

EXTRACTORS="ember2024 sums expert" SPLITS=ts EVERY=264 pipeline/2-features/featurize/run.sh
pipeline/3-directions/derived/run.sh
# The pilot's files and protocol (the steps default to the scale-up's evaluation set and protocol since session 67).
PILOT=artifacts/experiments/e1/seed-0/zeros/files.parquet
FILES=$PILOT CHAINED=0 NUM_FILES=5 pipeline/1-audit/catalogue-checks/run.sh
PROTOCOL=pilot MODELS=pilot DETECTORS="unconstrained monotone-sums" ESCAPE_DETECTORS="unconstrained monotone-sums" \
  ESCAPES="none debug_entry" SHARDS=1 EXPERT=0 QUERIES=200 CHECKPOINTS=200 NUM_MALWARE=3 SAVE_ROWS=1 pipeline/5-attacks/adaptive/run.sh
PROTOCOL=pilot MODELS=pilot SETTINGS=ours DETECTORS="unconstrained monotone-sums" NUM_MALWARE=3 \
  pipeline/5-attacks/mab-malware/run.sh

echo "Comparing $OLD with $OUT_ROOT:"
source env/bin/activate
python pipeline/setup/compare_outputs.py "$OLD" "$OUT_ROOT" \
  --map \
    features=2-features \
    directions=3-directions \
    catalogue=1-audit/catalogue \
    adaptive/plain=5-attacks/adaptive/none \
    adaptive/debug_entry=5-attacks/adaptive/debug_entry \
    mab=5-attacks/mab-malware \
  --rename \
    mfull-sums=monotone-sums
