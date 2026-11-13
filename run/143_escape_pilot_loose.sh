#!/bin/bash
# Escape pilot, widened population (R7, PLAN.md step 2b (iii); after run 142). The successor to run 138. Run 138 found
# that a loader-ignored write to a data-directory entry outside the threat model (the debug entry past the end, the
# certificate entry) moved that entry's own features against the monotone detectors' table, evading them (the debug
# write alone evaded 3/40 and 4/41 end to end). The user chose the full widening: `ent` (the certificate and debug
# entries set to any value) joined M_full, the population lets the data they locate lie past the end, and the detectors
# were retrained on the widened table (the `-loose` models; run 140). This run tests the widening end to end.
#
# Each pilot malware is escaped by one loader-ignored field write (scripts/escape_audit.py: cert_entry, image_size,
# debug_entry), then attacked by the adaptive beam search over all of M_full -- which now includes `ent` -- with every
# candidate written by our own byte edits and extracted (--score real: no computed effects, nothing declined). The
# escape write is the attack's fixed first move, itself an `ent` edit (cert_entry/debug_entry) or an add-section side
# effect (image_size, SizeOfImage); detection and evasion are counted from the UNESCAPED original (detected original,
# undetected end file), since the escape is now part of the threat model (a1_adaptive.py --escape, R7). Detectors, on
# the 10% sums store, each at its own 1% FPR threshold:
#   unconstrained  seed-0-s10-ref         (the reference detector, no guarantee)
#   mfull-feat     seed-0-s10-mfull-feat-loose  (the monotone detector on the features, widened population)
#   mfull-sums     seed-0-s10-mfull-sums-loose  (the monotone detector on the sums, widened population)
#
# Hypothesis (fixed before the run): no detected original is evaded by either monotone `-loose` detector, by any of the
# three escape writes (evaded 0, min_delta_logit 0, evaded_by_escape 0), since every escape write is now a threat-model
# edit and the detector is sound on the widened population the escaped files lie in. The unconstrained detector ~40-60%,
# as on the population (run 138: 40/48, 35/47). Reference points: run 138 (certificate 1/41 and 1/43, SizeOfImage 0/40
# and 0/41, from the escaped files, before the widening; the debug write untested there but evading 3/40 and 4/41 end to
# end). Smoke (Claude, 6 files, debug_entry, 60 queries): unconstrained 3/5, mfull-sums 0/5 (+0.0000, 0 by escape).
#
# Reading (next R7 session): into this header, docs/evidence/r7-population-escape.md §7 and its log, PLAN.md step 2b
# (iii), docs/status.md. Expect the monotone columns at or near 0; a non-zero one is read against in_population and
# evaded_by_escape (a miss on a file outside the loose population is not a guarantee violation; report it either way).
#
# Resources: one search per (detector, file), NUM_WORKERS processes (spawn; ~1 GB each). Real extraction costs ~0.6 s
# per candidate, so a file the search does not evade takes ~20 min at 2,000 candidates; ~3 escapes x ~130 (detector,
# file) pairs, most of them monotone pairs that run the full budget: ~5-6 h with 16 workers. OMP_NUM_THREADS=1 per
# worker. The toolkit attacks (MAB-Malware) are left for the scale-up.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/escape_pilot_loose
LOG=artifacts/logs/escape_pilot_loose.log
mkdir -p artifacts/logs

attack() {  # escape write
  python scripts/a1_adaptive.py \
    --outdir "$OUT/$1" \
    --escape "$1" \
    --score real \
    --search beam \
    --queries 2000 \
    --checkpoints 200 1000 2000 \
    --beam 3 \
    --draws 2 \
    --patience 3 \
    --seed 0 \
    --threat_model M_full \
    --features artifacts/features/ember2024-sums-10-v2 \
    --defense unconstrained=$M/seed-0-s10-ref \
    --defense mfull-feat=$M/seed-0-s10-mfull-feat-loose \
    --defense mfull-sums=$M/seed-0-s10-mfull-sums-loose \
    --sound mfull-feat mfull-sums \
    --num_workers "$NUM_WORKERS" \
    &>> "$LOG"
  tail -6 "$LOG"
}

: > "$LOG"
echo "(1/3) Escape by the certificate entry, then the real-scored adaptive search (~1.5-2 h). Log: $LOG"
attack cert_entry
echo "(2/3) Escape by SizeOfImage, then the real-scored adaptive search (~1.5-2 h). Log: $LOG"
attack image_size
echo "(3/3) Escape by the debug entry, then the real-scored adaptive search (~1.5-2 h). Log: $LOG"
attack debug_entry
echo "Done. Reports: $OUT/{cert_entry,image_size,debug_entry}/adaptive.json"
