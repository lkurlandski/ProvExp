#!/bin/bash
# A' step 1, the pre-check (docs/direction-A-prime-plan.md, Section 6; decides G1): the bracket of each detector's
# worst case under the edit catalogue, per family (append only; up to 3 added sections only) and combined, on the
# pilot malware each detector catches and no real attack evades. The floor is the solver's proven bound (it minimizes
# the score, so a timeout still gives a floor); the ceiling is the lowest real score of the toolkit and the adaptive
# search. Rows: the undefended GBDT (reference), PV-seen, PV-all (the 10% detectors).
#
# Smoke (Claude, 2026-11-01; 30 s per solve on PV, 10 s on the undefended model), files no attack evades:
#   - splits on features the family moves (of all the detector's splits): append 1,367-1,444 of ~10,700 on PV
#     (13%), 21,883 of 31,500 on the undefended model (69%); sections 5,458-6,405 on PV (51-60%), 24,123 undefended.
#   - append only: PV-all 6 of 6 covered certified, PV-seen 5 of 5 (1 by the cheap per-tree floor), ~10 s each;
#     undefended 0 of 13 at 10 s.
#   - sections only: 0 certified anywhere at 30 s (PV-all 0/1, PV-seen 0/3, undefended 0/9); no proven floor yet.
#   - coverage: many files have no free section-table slot (PV-all 5 of 6 covered, PV-seen 2 of 5, undefended 4 of
#     13), so for them "both" is append only; the precondition leaves out 1-2 PV files and 7 undefended ones.
#   - no certificate on an evaded file; every floor at or below the clean score.
# Hypothesis for 1,800 s: append stays certified on PV and stays open on the undefended model (69% of its splits are
# on moved features); sections only and both certify a minority of the PV files that have a free slot (the adaptive
# search evades PV through added sections, so the files it did not evade are the ones near the edge); the undefended
# model has no certificate in any family. G1 (at most half of the covered files open on PV) then passes for append and
# fails for sections and both.
#
# Estimate: ~45 solves that do not finish early (undefended 35, PV ~8) at 1,800 s on 16 workers: ~3 rounds, ~1.5 h.
# (32 workers ran run 113 without trouble; with 32, ~1 h.)
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
E=artifacts/experiments
mkdir -p artifacts/logs

LOG=artifacts/logs/ap_bracket_precheck.log
echo "Brackets per detector and family (1,800 s per solve). Log: $LOG"
python scripts/ap_bracket.py \
  --outdir $E/ap_bracket/precheck \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --family append sections both \
  --time_limit 1800 \
  --workers 16 \
  &> "$LOG"

echo "Done. Report: $E/ap_bracket/precheck/report.json; per file: $E/ap_bracket/precheck/brackets.parquet"
