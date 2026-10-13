#!/bin/bash
# AU, where the realizable pushforward recipe loses its evasion (docs/experiments/audit.md, "Held-out evasion and
# realizability"): run 47's setup on the same 1,000 fresh held-out malware, plus the decomposition (--decompose): the
# realizable fields with random bytes (abnormal values), the free fields alone, and a null of unconfirmed free fields.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_evade_decompose-seed0.log
echo "AU decomposition: 1,000 fresh malware (as run 47), detected only (12 workers, about 8-10 min)."
echo "Output: artifacts/experiments/audit_evade/decompose-seed-0/"
echo "Log:    $LOG   (per-recipe rates with CIs and the paired tests are at its end)"
OMP_NUM_THREADS=1 python scripts/audit_evade.py \
  --seed 0 \
  --num_files 1000 \
  --detected_only \
  --random_retries 20 \
  --realizable \
  --decompose \
  --exclude artifacts/experiments/audit_scramble/seed-0/files.parquet \
  --run_name decompose-seed-0 \
  --num_workers 12 \
  &> "$LOG"

echo "Done. Summary: tail -n 45 $LOG"
