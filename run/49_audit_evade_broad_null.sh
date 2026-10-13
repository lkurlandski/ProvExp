#!/bin/bash
# AU, a broader null for the realizable recipes (docs/experiments/audit.md, "Held-out evasion and realizability"): run
# 48's setup on the same 1,000 fresh held-out malware, plus --broad_null: random draws from every loader-ignored field
# of the EMBER header, data-directory, Rich-header, and certificate features that no source confirmed (83 fields in the
# classification), with and without the DOS region (DOS header, stub, Rich header).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/audit_evade_broad_null-seed0.log
echo "AU broad null: 1,000 fresh malware (as runs 47-48), detected only (12 workers, about 10-12 min)."
echo "Output: artifacts/experiments/audit_evade/broad-null-seed-0/"
echo "Log:    $LOG   (per-recipe rates with CIs and the paired tests are at its end)"
OMP_NUM_THREADS=1 python scripts/audit_evade.py \
  --seed 0 \
  --num_files 1000 \
  --detected_only \
  --random_retries 20 \
  --realizable \
  --decompose \
  --broad_null \
  --exclude artifacts/experiments/audit_scramble/seed-0/files.parquet \
  --run_name broad-null-seed-0 \
  --num_workers 12 \
  &> "$LOG"

echo "Done. Summary: tail -n 55 $LOG"
