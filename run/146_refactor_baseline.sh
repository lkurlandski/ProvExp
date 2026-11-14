#!/bin/bash
# The refactoring session (2026-11-14; docs/resume-prompt.md, item 6): outputs of the code *before* the move into
# pipeline/ and src/provexp/ (tag `pilot-final`), on a small pilot slice. The reorganized code must reproduce them byte
# for byte; any difference is a bug in the move. Five pieces, one per kind of computation the move touches:
#   (1) featurization, all three extractors (EMBER, the re-encoding over sums, the expert set), two test shards;
#   (2) the derived direction tables over sums, strict and `--loose`, on the pilot files;
#   (3) one catalogue check (`--loose`: closure, soundness, exactness), first 5 pilot files;
#   (4) the extraction-scored adaptive beam search, 3 detected malware, 200 candidates, two detectors, with and without
#       an escape write, rows saved;
#   (5) MAB-Malware, 3 malware, two detectors.
# Run twice (OUT=.../old and OUT=.../old-repeat) to learn which output fields vary between identical runs (timings).
# Ran 2026-11-14 (Claude) at b223fcd, ~20 min each: old and old-repeat agree on all 61 files but timing fields
# (hypothesis held); the library move (185212e, OUT=.../new-lib) matched too. The scripts it calls left scripts/ in
# the pipeline/ move; to re-run it, check out 185212e. Its successor is pipeline/setup/identity_check.sh.
#
# Hypothesis: the two old runs agree on every output except timing fields.
#
# Resources: NUM_WORKERS processes (default 16); ~10 min in all.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
NUM_WORKERS="${NUM_WORKERS:-16}"
OUT="${OUT:-artifacts/refactor-baseline/old}"
LOGS=$OUT/logs
M=artifacts/models/gbdt
F=artifacts/features/ember2024-sums-10-v2
mkdir -p "$LOGS"

echo "(1/5) Featurization, two test shards per extractor. Logs: $LOGS/featurize-*.log"
for x in ember2024 sums expert; do
  python scripts/featurize.py \
    --extractor $x \
    --splits ts \
    --every 264 \
    --num_workers 2 \
    --outdir "$OUT/features/$x" \
    &> "$LOGS/featurize-$x.log" &
done
wait

echo "(2/5) Direction tables over sums, strict and loose. Logs: $LOGS/directions-*.log"
python scripts/a_directions.py \
  --extractor sums \
  --outdir "$OUT/directions/strict" \
  --workers "$NUM_WORKERS" \
  &> "$LOGS/directions-strict.log"
python scripts/a_directions.py \
  --extractor sums \
  --loose \
  --outdir "$OUT/directions/loose" \
  --workers "$NUM_WORKERS" \
  &> "$LOGS/directions-loose.log"

echo "(3/5) Catalogue check, loose, 5 pilot files. Log: $LOGS/catalogue.log"
python scripts/catalogue_checks.py \
  --loose \
  --directions "$OUT/directions/loose/directions_sums.csv" \
  --num_files 5 \
  --outdir "$OUT/catalogue" \
  --workers "$NUM_WORKERS" \
  &> "$LOGS/catalogue.log"

adaptive() {  # tag, then extra arguments
  local tag=$1; shift
  python scripts/a1_adaptive.py \
    --outdir "$OUT/adaptive/$tag" \
    --score real \
    --search beam \
    --queries 200 \
    --checkpoints 200 \
    --beam 3 \
    --draws 2 \
    --patience 3 \
    --seed 0 \
    --threat_model M_full \
    --num_malware 3 \
    --features $F \
    --defense unconstrained=$M/seed-0-s10-ref \
    --defense mfull-sums=$M/seed-0-s10-mfull-sums-loose \
    --sound mfull-sums \
    --save_rows \
    --num_workers "$NUM_WORKERS" \
    "$@" \
    &> "$LOGS/adaptive-$tag.log"
}
echo "(4/5) Adaptive search, extraction-scored, plain and after the debug-entry escape. Logs: $LOGS/adaptive-*.log"
adaptive plain
adaptive debug_entry --escape debug_entry

echo "(5/5) MAB-Malware, 3 malware. Log: $LOGS/mab.log"
python scripts/mab_attack.py \
  --outdir "$OUT/mab" \
  --workdir "$OUT/mab/work" \
  --features $F \
  --defense unconstrained=$M/seed-0-s10-ref \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums-loose \
  --max_pull 60 \
  --max_length 10 \
  --num_malware 3 \
  --seed 0 \
  --num_workers "$NUM_WORKERS" \
  &> "$LOGS/mab.log"

echo "Done. Outputs in $OUT"
