#!/bin/bash
# A' step 4's test (docs/direction-A-prime-encoding.md, "The test"): the edit-choice encoding (scripts/ap_encoding.py)
# must contain the real file. Every pilot file (malware and goodware) the encoding covers, 12 random edits each (0-3
# added sections with random names, flags, and contents, then an append) plus the empty edit, written with our own
# byte-level edits and re-extracted. Checks per edit: the exact features equal re-extraction; the held-fixed features
# (the untouched groups, pefile's other warnings) are unchanged; with the choice fixed and every split (union over
# the three 10% detectors) on the re-extracted side, the program is feasible.
# Hypothesis: every check holds on every edit (the smoke test held on 35 edits of 7 files, after fixing a scaling bug
# that dropped tiny coefficients); the likeliest failures are strings at boundaries and other pefile warnings.
#
# Estimate: ~1,300 edits at 2-6 s each on 16 workers: ~3-6 min.
# Ran 2026-10-30 (Claude, 7 min 40 s): hypothesis holds. 85 of 100 files covered (12 fail the precondition, 1 low
# alignment, 2 under 4 KB); 1,105 edits written; contained 1,105, exact 1,105, held-fixed unchanged 1,105.
# Re-ran 2026-10-30 (Claude, fifth session, ~8 min), after the solver numerics, whole-number splits, entropy floor,
# tail-string merge rule, and the per-row entropy cuts with exact header-window rows: hypothesis holds again. 85 covered;
# 1,105 edits written; contained, exact, and held-fixed unchanged on all 1,105.
# Re-ran twice more (2026-10-30, fifth session, ~8 min each): after the pooled dominance cuts on the new windows, and
# after the regex character requirements on the strings: holds both times (1,105 of 1,105 on every check).
# Re-ran 2026-11-01 (Claude, ~8 min), after per-section byte counts tied to each added section's entropy (Pinsker
# above, the dominant share below; Pinsker also on the file's, the overlay's, and the strings' entropies): holds
# (1,105 of 1,105 on every check).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

E=artifacts/experiments
LOG=artifacts/logs/ap_containment.log
echo "Containment test of the edit-choice encoding. Log: $LOG"
python scripts/ap_containment.py \
  --outdir $E/ap_containment \
  --goodware \
  --edits 12 \
  --workers 16 \
  &> "$LOG"

echo "Done. Report: $E/ap_containment/report.json"
