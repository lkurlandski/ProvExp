#!/bin/bash
# A' go/no-go check 1b (docs/direction-A-prime-mock.md, decision 7): does the computed region certify? The exact solver
# over the edit-choice encoding (scripts/ap_encoding.py: up to 3 added sections, then an append, budget max(5%, 512 KB))
# on the unconstrained 10% detector, for the detected files the battery (toolkit run 105 + adaptive run 109) does not
# evade. Go if it certifies at least 20% of them (4 of 20; 7 fail the precondition, so 4 of the 13 covered).
# Hypothesis (2026-10-30, after the per-row, dominance, and regex-character cuts): still a no-go, but fewer solver
# evasions than the smoke run's 3; a certificate, if any, on a large file (budget small against the file). On 2826a9a5
# (4 MB) the solver went from an evasion in 111 s to undecided at 300 s after the last two cuts.
# Smoke (2026-10-30, fifth session, first 30 pilot malware, 60 s): 12 solves, 5 fail the precondition, 7 undecided,
# none evaded (the smoke before the cuts found 3 quick evasions). Evading solutions are saved under solutions/ for
# check 2. Smoke at 300 s (2026-10-30, before tightening): 0 certified, 10 undecided, 3 solver evasions.
#
# Result (run 2026-10-30 by the user, read 2026-10-31): NO-GO, hypothesis failed (more evasions, not fewer). Of the 13
# covered files: 0 certified, 6 solver evasions (found in 269-576 s, incl. 2826a9a5 at 507 s), 7 undecided at 1,800 s.
# By budget: budget > file 5 files (0 / 2 evaded / 3 undecided); budget within file 8 (0 / 4 / 4). The undecided are
# the smaller files (82 KB-1.8 MB, one 4 MB). Wall ~32 min.
# Realized (scratch driver, 2026-10-31; ap_realize.realize, re-extracted): 0 of 6 evade. Real raw 3.40-6.76 against the
# solver's 0.77-1.10 and the threshold 1.10. No single group closes the gap: with only its splits on the solver's
# sides, byte-entropy gives 1.96-5.37, strings 2.15-4.50, sections 3.27-5.65 (4 files), histogram ~unchanged.
#
# Estimate: 13 solves in parallel, 1,800 s limit each: ~30 min wall.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
E=artifacts/experiments
LOG=artifacts/logs/ap_check1b.log
echo "Check 1b: the computed region in the exact solver. Log: $LOG"
python scripts/ap_check1b.py \
  --outdir $E/ap_check1b \
  --defense ref=$M/seed-0-s10-ref \
  --skip_battery_evaded \
  --time_limit 1800 \
  --workers 16 \
  &> "$LOG"

echo "Done. Report: $E/ap_check1b/report.json"
