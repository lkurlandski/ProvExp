#!/bin/bash
# A' decision 7, option 1 (user, 2026-11-01): one bounded tightening round, then re-solve and re-realize the 6 files
# whose check-1b evasions (run 112) did not realize. Stop rule: if 3 or more still do not evade as files, A' leads with
# another use (decision 7, option 2).
# The tightening (scripts/ap_encoding.py, scripts/ap_realize.py; each sound and tested):
#   1. each added section's own byte counts, tied to its entropy: Pinsker's inequality above (a near-maximal entropy is
#      near uniform in L1), every byte value present above log2(255), the dominant share below (min-entropy and the
#      binary entropy); Pinsker also on the file's, the overlay's, and the strings' entropies;
#   2. the exact block model of the overlapping byte-entropy windows: the new tail as 1 KB blocks with nibble counts,
#      window i = blocks i - 1 and i, one row per window, its counts split exactly by row; per window Gibbs, Pinsker,
#      Fano (above) and the dominant share (below); printable bytes outside strings need a separator per four;
#   3. the realizer: each section from its own counts; each block from the solver's block counts; the solver's string
#      characters reserved and written as strings; byte counts nudged onto the solver's side of the histogram splits
#      (the solver's counts are fractional and sit within the encoding's float32 tolerance of the thresholds).
# Hypothesis: section entropies and the histogram drop out of the gap (they did on the 3 files a 480 s diagnostic
# solve after step 1 evaded on: real 2.54-4.73 after the nudge, from 4.13-6.76); byte-entropy shrinks with the block
# model; strings remain the largest part. A 480 s diagnostic solve with all three steps (2026-11-01): all 6 undecided
# (program ~225 K variables, ~230 K rows, ~43 K binaries). Expected at 1,800 s: few or no solver evasions, most files
# undecided, no certificate; any evasion that is found comes closer to the threshold as a file than in run 112 but
# does not evade.
# Proposed reading (Claude, 2026-11-01; for the user to confirm): the stop rule counts solver evasions that do not
# evade as files; if there are none because every file is undecided, the round has removed the fake evasions but
# certified nothing, check 1b is still a no-go, and decision 7 returns to the user with that result.
#
# Steps: (1) containment (run 111; the encoding changed; it must hold on every edit, ~25 min: the block model made
# each check ~6x slower), (2) the 6 files at 1,800 s each in parallel (~32 min), (3) the evasions written as files
# and scored (~5 min).
# Estimate: ~1 h in all.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1

M=artifacts/models/gbdt
E=artifacts/experiments
OUT=$E/ap_tightening

echo "Step 1: containment (run 111). Log: artifacts/logs/ap_containment.log"
bash run/111_ap_containment.sh
python -c "
import json, sys
r = json.load(open('$E/ap_containment/report.json'))
ok = r['contained'] == r['exact_ok'] == r['held_ok'] == r['edits_written']
print(f\"contained {r['contained']} of {r['edits_written']}; failing: {r['failing_features']}\")
sys.exit(0 if ok else 1)
"

LOG=artifacts/logs/ap_tightening_solve.log
echo "Step 2: re-solve the 6 files (1,800 s each). Log: $LOG"
python scripts/ap_check1b.py \
  --outdir $OUT \
  --defense ref=$M/seed-0-s10-ref \
  --skip_battery_evaded \
  --names 6927e052 1161236b 511c7d1a 9613981f 2826a9a5 29718ff5 \
  --time_limit 1800 \
  --workers 16 \
  &> "$LOG"

LOG=artifacts/logs/ap_tightening_realize.log
echo "Step 3: the solver's evasions written as files and scored. Log: $LOG"
if ls $OUT/solutions/*.npy &> /dev/null; then
  python scripts/ap_check2_realize.py \
    --solutions $OUT/solutions \
    --outdir $OUT/realized \
    --defense ref=$M/seed-0-s10-ref \
    --workers 16 \
    &> "$LOG"
else
  echo "No solver evasions to write." | tee "$LOG"
fi

echo "Done. Solves: $OUT/report.json, $OUT/solves.parquet; written files: $OUT/realized/realized.parquet"
