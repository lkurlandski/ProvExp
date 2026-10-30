#!/bin/bash
# A' battery, the adaptive half (docs/direction-A-prime-mock.md, Table A'1's "attack battery" column): the C1-declared
# adaptive search of run 108 against the 10%-subsample detectors that the toolkit columns (run 105,
# artifacts/experiments/a1/toolkit-v2) and the solver (run 89) use, so that the battery is a per-file union over one set
# of models. Run 108 searched the full-data models (seed-0, and seed-0-pv, which is PV from all eight attacks), which
# are different detectors. The s10 models' 1,087 sums columns are neutralized (zero in every split), so the search pads
# its thrember vectors with zeros (`a1_adaptive.padded_booster`); the clean scores equal the toolkit's exactly (smoke).
# FOR ACADEMIC SECURITY RESEARCH ONLY: our C1-declared search against our own detectors on our own pilot samples.
# Hypothesis: few evasions of the reference (run 108: 4/49 on the full-data model), most of PV-seen and PV-all (16/22
# there; the hole is the same), so the battery's union is about 27/47 on the reference and 16-20/22 on each PV.
#
# Estimate: ~6-8 min (run 108 took ~6 min for four defenses).
# Ran 2026-10-30 (Claude, ~5 min). Result: ref 11/47 declared, 11 real; PV-seen 15/22 declared, 13 real; PV-all 16/22
# declared, 15 real. Battery union with the toolkit (real evasions only): ref 27/47, PV-seen 15/22, PV-all 15/22. The
# three declared-not-real cases are the engine's declared add-section leaving out the layout bytes (A4: the 40-byte
# section-table entry, which writes the name into the header, and the alignment padding): on 3caffa06 step 2 the PV
# model splits on byte-histogram bins that the header entry moves by ~3e-5, declared -1.40 vs real +0.09 in logit. Run
# 108's full-data models happened not to split there. Not a bug, but "declared equals real" does not hold in general;
# the solver encoding (A' step 4) must include the layout bytes in the edit.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
LOG=artifacts/logs/ap_battery_adaptive.log
echo "The C1-declared adaptive search against the 10% detectors. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir artifacts/experiments/ap_battery/adaptive \
  --features artifacts/features/ember2024-sums-10-v2 \
  --threat_model M_full \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense pv-all=$M/seed-0-s10-pv-all \
  --queries 100 \
  --seed 0 \
  &> "$LOG"

echo "Done. Adaptive: artifacts/experiments/ap_battery/adaptive/adaptive.json"
