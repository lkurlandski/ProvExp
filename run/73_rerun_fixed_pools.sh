#!/bin/bash
# Reruns after fixing audit_evade.benign_pools (2026-10-20): two benign ImageBase values above 2^63 overflowed the int64
# cast into a negative junk entry of the AMD64 pool; a file that drew it silently skipped that field (the write step
# rejects negative values). Pools now keep only values the float feature store holds exactly (0 <= v < 2^53). Reruns
# every experiment that draws from the pools and feeds the paper, each into a new directory (the old results stay):
# run 49 (6.2's loader-safe evasion and its paired tests), run 59 (Table 5, test-time mitigation; its no-defense row
# reproduces run 49), run 72 (6.1's Table 2; reuses run 72's IG, so no GPU work).
# Hypothesis: every number moves by at most a few tenths of a point (a junk draw is rare and only skips one field).
# Ran (2026-10-20, ~25 min): hypothesis held, and more strongly. Every estimate and p-value of runs 49, 59, and 72 is
# unchanged; only some bootstrap CI endpoints move by 0.1 point (resampling). No manuscript change.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_evade_broad_null-fixpools-seed0.log
echo "1/3 run 49 rerun: 1,000 held-out malware, loader-safe evasion (12 workers, ~10-12 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/audit_evade.py \
  --seed 0 \
  --num_files 1000 \
  --detected_only \
  --random_retries 20 \
  --realizable \
  --decompose \
  --broad_null \
  --exclude artifacts/experiments/audit_scramble/seed-0/files.parquet \
  --run_name broad-null-fixpools-seed-0 \
  --num_workers 12 \
  &> "$LOG"

LOG=artifacts/logs/audit-mitigate-fixpools-seed0.log
echo "2/3 run 59 rerun: test-time mitigation, 1,000 malware + 5,000 benign (16 workers, ~8 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/audit_mitigate.py \
  --seed 0 \
  --num_files 1000 \
  --num_benign 5000 \
  --num_random 5 \
  --random_retries 20 \
  --run_name fixpools-seed-0 \
  --num_workers 16 \
  &> "$LOG"

OUT=artifacts/experiments/cm_shared_edit_500_fixpools
echo "3/3 run 72 rerun: copying run 72's IG into $OUT/seed-0/ig."
mkdir -p "$OUT/seed-0/ig"
cp -n artifacts/experiments/cm_shared_edit_500/seed-0/ig/*.npy "$OUT/seed-0/ig/"
LOG=artifacts/logs/cm-shared-edit-500-fixpools-seed0.log
echo "3/3 run 72 rerun: 5 arms x 500 files on 16 workers (~5 min). Log: $LOG"
OMP_NUM_THREADS=1 python scripts/cm_shared_edit.py \
  --seed 0 \
  --num_files 500 \
  --num_fields 3 \
  --num_windows 4096 \
  --device cuda:3 \
  --num_workers 16 \
  --outdir "$OUT" \
  &> "$LOG"
echo "Done. Summaries: tail -n 55 of each log above."
