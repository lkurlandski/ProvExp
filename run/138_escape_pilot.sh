#!/bin/bash
# Escape pilot (meta-review 2026-11-12, R7; session 48): does a monotone detector applied to every file (no router)
# hold on files an attacker takes out of the population? Run 137 found single loader-ignored field writes that take
# every population file out (the certificate entry or the debug entry past the end of the file, SizeOfImage raised by
# one SectionAlignment). With the router, such a file goes to the unconstrained detector; the decision under test drops
# the router and scores every file with the monotone detector (proven on the population, measured outside it).
#
# Each pilot malware is first escaped (scripts/a1_adaptive.py --escape; files the write does not take out are left
# out), then attacked by the adaptive beam search over all twelve operations with every candidate written by our own
# edits and extracted with the sums extractor (--score real: no computed effects, nothing declined, header-field
# overwrites included). Detectors: Table 5's, on the 10% sums store, each at its own 1% FPR threshold:
#   unconstrained  seed-0-s10-ref (what the router sends an escaped file to: the routed system's result)
#   mfull-feat     the monotone detector on the features
#   mfull-sums     the monotone detector on the sums
# Step 1 escapes by the certificate entry, step 2 by SizeOfImage. The toolkit attacks are left for the scale-up.
#
# Hypothesis (fixed before the run): the monotone detectors are evaded on few escaped files (0-3 of ~40 each; their
# largest score drop small), since leaving the population opens only the side effects the table does not cover on
# incomplete or oversized files; the unconstrained detector ~40-50%, as on the population (run 127: 25/49 at 5,000).
# Reference points: smoke (Claude, 3 files, cert entry, 300 candidates): unconstrained 1/2, both monotone 0/2 with
# largest drop exactly 0.
#
# Reading (sessions 52-53; R7 record, docs/evidence/r7-population-escape.md §7). Denominators below are the files
# detected *after* the escape write, as the script counts them.
#   Step 1, certificate entry: unconstrained 40/48 (held); mfull-feat 1/41, mfull-sums 1/43 (count held, size failed:
#     -3.1 and -3.2 logits). Both are one signed file whose unescaped original neither detector detected: the escape
#     breaks the signature parse, an append restores it and the authenticode:* features rise (held "can only fall").
#   Step 2, SizeOfImage: unconstrained 35/47 (held); mfull-feat 0/40, mfull-sums 0/41 (held), every monotone search ran
#     its 2,000 candidates and its best was the unedited file (no candidate lowered the score). The write raises only
#     SizeOfImage, which the table already allows to rise (added sections); 7786 s.
#   End to end, from the unescaped originals (session 53, scratch check, no search): no write alone evades a detected
#     original for cert_entry (but it lowers the score on most files: security_size rises, held "can only fall";
#     median -0.11 / -0.25 logits), image_size (never lowers it) or arch_entry (raises it); the untested debug_entry
#     write alone evades 3/40 (mfull-feat) and 4/41 (mfull-sums), drops up to -3.1 / -4.1, median -1.0 logits, by
#     raising datadirectories:debug_size (all 50) and debug_virtual_address (37), both held "can only fall".
#   So the failures come from the escape writes themselves: loader-ignored writes to data-directory entries that the
#   threat model leaves out, moving the entry's own features against the table.
#
# Resources: one search per (detector, file), NUM_WORKERS processes (spawn; ~1 GB each). Real extraction costs ~0.6 s
# per candidate (smoke), so a file the search does not evade takes ~20 min at 2,000 candidates; ~130 (detector, file)
# pairs per step, most of them monotone pairs that run the full budget: ~40 CPU-h per step, ~2.5-3 h per step with 16
# workers (~5-6 h in all). OMP_NUM_THREADS=1 per worker.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/escape_pilot
LOG=artifacts/logs/escape_pilot.log
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
    --defense mfull-feat=$M/seed-0-s10-mfull-feat-pre-v2 \
    --defense mfull-sums=$M/seed-0-s10-mfull-sums-pre-v2 \
    --num_workers "$NUM_WORKERS" \
    &>> "$LOG"
  tail -5 "$LOG"
}

: > "$LOG"
echo "(1/2) Escape by the certificate entry, then the real-scored adaptive search (~2.5-3 h). Log: $LOG"
attack cert_entry
echo "(2/2) Escape by SizeOfImage, then the real-scored adaptive search (~2.5-3 h). Log: $LOG"
attack image_size
echo "Done. Reports: $OUT/{cert_entry,image_size}/adaptive.json"
