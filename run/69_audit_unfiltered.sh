#!/bin/bash
# Section 6.2, the unfiltered audit (implementation plan WP7): rerun discovery and scrambling-confirmation without the
# single-short-run requirement, so the pushforward can confirm features whose credited bytes are shared or scattered
# (section names, import/string buckets), not only contiguous header fields. --max_content is raised so a located run
# up to 100 KB counts; --max_runs 256 still excludes whole-file aggregates (histogram, byte-entropy). Reuses the IG of
# runs 38-39. GPU is not needed (the IG is cached); at most 16 workers.
# Hypothesis: some section/import/string features are confirmed, i.e., reliance the pushforward splits from shared
# bytes that summing attributions per parsed region would not separate.
#
# NOTE: --direction malware is required: confirmation reads {source}-malware (as runs 43-44); the first rerun omitted it.
# NOTE: grouping the confirmed features by type (header / section / import / string) for Table 3 is a follow-up on
# this run's output; not scripted here.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

# The IG of runs 38-39 lives in the filtered run's folder; discovery looks for it in its own --outdir.
echo "Linking the cached IG (runs 38-39) into the unfiltered output folder."
mkdir -p artifacts/experiments/audit_discover_unfiltered/seed-0
ln -sfn "$PWD/artifacts/experiments/audit_discover/seed-0/ig" artifacts/experiments/audit_discover_unfiltered/seed-0/ig

LOG=artifacts/logs/audit-discover-unfiltered-seed0.log
echo "Unfiltered discovery: 2,000 files, 16 workers (~7 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/audit_discover.py \
  --seed 0 \
  --phase discover \
  --direction malware \
  --max_content 100000 \
  --max_runs 256 \
  --num_workers 16 \
  --outdir artifacts/experiments/audit_discover_unfiltered \
  &> "$LOG"
echo "Discovery done: tail -n 100 $LOG"

LOG=artifacts/logs/audit-scramble-unfiltered-seed0.log
echo "Unfiltered confirmation: 200 malware, 16 workers (~5 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/audit_scramble.py \
  --seed 0 \
  --max_content 100000 \
  --discover artifacts/experiments/audit_discover_unfiltered \
  --outdir artifacts/experiments/audit_scramble_unfiltered \
  --num_workers 16 \
  &> "$LOG"
echo "Done. Confirmation summary: tail -n 50 $LOG"
