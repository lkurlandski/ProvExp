#!/bin/bash
# A' under review (docs/direction-A-prime-plan.md, Section 12): evidence for option (a), a certified budget per file
# (the largest append, or added-section content, proven not to evade). Run overnight before the decision session.
# Steps:
#   (1) containment (run 111) on the solver path changed this session (HiGHS called directly via highspy; a 48-edit
#       smoke held): every real edit must stay inside the region, or no certificate below can be trusted;
#   (2) the bracket at fixed budgets of 1, 4, 16, and 32 KB, 600 s per solve, on the files no attack evades:
#       the undefended GBDT, append only and sections only; PV-seen and PV-all, sections only (append already
#       certifies every covered PV file at 512 KB, run 114, so it certifies at every smaller budget too).
# Hypothesis: containment holds on every edit. The undefended model certifies most files at 1 KB, about a fifth at
# 4 KB (run 115: 2 of 13 at 300 s), and almost none at 16-32 KB; PV under sections certifies at 1-4 KB on most of its 4
# files with a slot. Reading for the decision: option (a) is worth discussing only if the certified budgets spread out
# (differ between files and detectors) rather than all sitting at 1-4 KB.
#
# Estimate: containment ~25 min on 32 workers (~50 min on 16); the sweep per budget ~2 rounds of 600 s (undefended,
# 22 solves) plus 1 round (PV, 4 solves) on 16 workers, ~30 min, so ~2 h for the four budgets.
# In all ~3 h on 16 workers (~2 h on 32: set --workers in run 111 and below).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
E=artifacts/experiments
OUT=$E/ap_bracket/budget
mkdir -p artifacts/logs

echo "Step 1: containment (run 111). Log: artifacts/logs/ap_containment.log"
bash run/111_ap_containment.sh
python -c "
import json, sys
r = json.load(open('$E/ap_containment/report.json'))
ok = r['contained'] == r['exact_ok'] == r['held_ok'] == r['edits_written']
print(f\"contained {r['contained']} of {r['edits_written']}; failing: {r['failing_features']}\")
sys.exit(0 if ok else 1)
"

for B in 1024 4096 16384 32768; do
  LOG=artifacts/logs/ap_bracket_budget_ref_$B.log
  echo "Step 2: undefended, append and sections, budget $B bytes. Log: $LOG"
  python scripts/ap_bracket.py \
    --outdir $OUT/ref_$B \
    --defense ref=$M/seed-0-s10-ref \
    --family append sections \
    --budget_frac 0 \
    --budget_min $B \
    --time_limit 600 \
    --workers 16 \
    &> "$LOG"
  LOG=artifacts/logs/ap_bracket_budget_pv_$B.log
  echo "Step 2: PV-seen and PV-all, sections, budget $B bytes. Log: $LOG"
  python scripts/ap_bracket.py \
    --outdir $OUT/pv_$B \
    --defense pv-seen=$M/seed-0-s10-pv-seen \
    --defense pv-all=$M/seed-0-s10-pv-all \
    --family sections \
    --budget_frac 0 \
    --budget_min $B \
    --time_limit 600 \
    --workers 16 \
    &> "$LOG"
done

echo "Done. Reports: $OUT/{ref,pv}_*/report.json"
