#!/bin/bash
# Table A1's adaptive column after the search fix (decided by the user, 2026-10-30): each chosen add-section step is
# materialized by our own byte-level edit (scripts/catalogue_checks.py: the section ends the file, as the engine
# declares it), not by LIEF, which kept the overlay and let every later step claim its removal again (run 105). A
# candidate whose file has no room for another section header is skipped. Same defenses and arguments as run 105 step 3.
# Second fix (found on the first try, 2026-10-30): the engine leaves the features no readout models (pefile's 88
# warning flags) NaN, which the unconstrained and PV models read as missing values; the search's predictors now fill
# them from the current file, as the hand predictors did. First try (own edit only): unconstrained 21/49 declared, 3 of
# them realized; PV 21/22; C4 rows 0. Its declared drops came from the NaNs (e.g. 303ef5c997: four appends, declared
# 0.23, real 0.99999; every non-warning feature equal to re-extraction).
# FOR ACADEMIC SECURITY RESEARCH ONLY: our C1-declared search against our own detectors on our own pilot samples.
# Hypothesis (second run): declared and real scores now differ only by the add-section's layout bytes; the
# unconstrained row near run 100's 10/49 (files with an overlay may stay above it: removing
# it once is a real M_add move); PV 22/22; both C4 rows 0 with min_delta_logit exactly 0.
#
# Estimate: run 105 step 3 took ~6 min.
# Ran 2026-10-30 (Claude, ~6 min). Result: unconstrained 4/49, PV 16/22, both C4 rows 0 (0/47, 0/41; min_delta_logit
# exactly 0). Declared and real scores now agree (median |p_real - p_declared| < 1e-4; every declared evasion is real,
# 4/4 and 16/16), so the earlier "layout bytes" gap was the NaN bug too. Below run 100 (10/49, 22/22) because 10 of the 49
# detected pilot malware have no room for another section header (only appends; 5 of PV's 6 losses, the sixth ends at
# 0.817 vs tau 0.811), and because run 100's steps started from LIEF's relayout, which our edit does not do.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
LOG=artifacts/logs/a1_adaptive_v3.log
echo "The C1-declared adaptive search, steps written by our own edit. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/a1/adaptive-v3 \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense unconstrained=$M/seed-0 \
  --defense pv=$M/seed-0-pv \
  --defense madd-feat=$M/seed-0-a-madd-pre-qf-v2 \
  --defense mfull-feat=$M/seed-0-a-mfull-pre-qf-v2 \
  --sound madd-feat mfull-feat \
  --queries 100 \
  --seed 0 \
  &> "$LOG"

echo "Done. Adaptive: artifacts/experiments/a1/adaptive-v3/adaptive.json"
