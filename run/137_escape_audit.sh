#!/bin/bash
# Escape audit (meta-review 2026-11-12, R7 (a)): which single field writes, outside the threat model, take a file out of
# the population. 150 population files below 4 MB from the 2,000 test files (run 136's clause table); byte edits only,
# nothing is executed.
#
# Took ~1 min with 16 workers (session 48).
#
# Results (2026-11-12): each loader-ignored write takes 150 of 150 files out (93 benign, 57 malware): the certificate
# entry or the debug entry extended past the end of the file, the reserved architecture entry pointed past it (item and
# directory past the end), SizeOfImage raised by one SectionAlignment (image too large); the architecture entry pointed
# at the overlay takes out 22 of the 22 files with an overlay (overlay at a directory). Control: the last section's raw
# size past the end, 150 of 150.

set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
NUM_WORKERS="${NUM_WORKERS:-16}"

mkdir -p artifacts/logs
echo "Escape audit on 150 population files (~1 min). Log: artifacts/logs/escape_audit_pilot.log"
python scripts/escape_audit.py \
  --clauses artifacts/experiments/population_clauses/2000/files.parquet \
  --outdir artifacts/experiments/escape_audit/pilot \
  --n 150 \
  --seed 0 \
  --workers "$NUM_WORKERS" \
  &> artifacts/logs/escape_audit_pilot.log

tail -5 artifacts/logs/escape_audit_pilot.log
echo "Done. Report: artifacts/experiments/escape_audit/pilot/report.json"
