#!/bin/bash
# R18 (docs/reviews/2026-11-12-body/rebuttal/triage.md; docs/resume-prompt-R18.md): the trial competitor. FOR ACADEMIC
# SECURITY RESEARCH ONLY: our own adaptive search and the published MAB-Malware against our own detectors, on the
# pilot test malware. Nothing is deployed.
#
# A practitioner who knows the twelve operations can learn their directions by trial (apply each, extract, look) instead
# of deriving them. Here a monotone detector is built on the trial table exactly as the derived detector is built on the
# derived one (lowered by some edit: dropped; raised only: monotone increasing; never moved: free), and both are attacked.
#
#   0. (Claude, session 60, done; skipped when the outputs exist) the trial table and its two detectors:
#      a. a stronger in-place trial than catalogue_checks' (every section renamed, all slack, DOS and header bytes,
#         zeros and printable), on the pilot, and on 600 of the 2,000 test files with donor imports (200 benign training
#         files, 20 libraries per file, our own import writer, not LIEF);
#      b. trial table = catalogue_checks' 2000-exact and pilot-loose-lief edits + (a); "-toolkit" adds the toolkit
#         outputs (run 133's 3,183 on training malware, run 78's on the pilot; population files only);
#      c. gbdt/seed-0-s10-mfull-feat-trial{,-toolkit}, trained as run 140 trained -s10-mfull-feat-loose.
#      The pilot probe was run by a scratch version of trial_probe.py (same edits, printable bytes seeded by the name
#      alone); regenerating (0a) draws other printable bytes. Each step took under 10 min (machine at load ~140).
#   1. The adaptive beam scoring by extraction (run 143's protocol: 2,000 candidates, beam 3) on the pilot malware each
#      of the three detectors detects: trial, trial-toolkit, and the derived -loose detector (paired, same protocol).
#   2. MAB-Malware (run 139's protocol) against the same three.
#
# Step 0's results (Claude, 2026-11-13; artifacts/experiments/r18_trial/report-final*.json). Modeled features only:
#   trial vs derived: never lowers a feature the derived table says no edit lowers (no soundness conflict); 66 features
#   the derived table marks lowerable it never lowered (62 string-pattern counts, iat_size, iat_virtual_address,
#   import_virtual_address, authenticode:parse_error); 86 raise-only features it never moved (84 import buckets).
#   With the toolkit: 179 features lowered that no operation lowers (LIEF's relayout, assumption A4; some outputs stop
#   being PE files), which trial cannot tell from the operations' effects.
#   TPR at 1% / 0.1% FPR: derived -loose 83.4 / 65.1; trial 87.6 / 71.3; trial-toolkit 53.1 / 36.5 (unconstrained
#   93.5 / 84.4). The trial detector puts 30.8% of its split gain on features the derived table marks lowerable (14.4%
#   modeled: iat_size 4.6, regex_https:// 2.1, iat_virtual_address 1.8; 16.4% parser warnings). Taking the warnings
#   from trial into the derived detector changes nothing (83.0 / 66.2), so the gap is the modeled features.
#   Smoke (100 candidates, 12 files): trial evaded 5/11, each by signature cloning (`ent`): the cloned certificate's
#   URLs raise strings:regex_https://, which trial never moved (random content holds no URL) and so left free;
#   trial-toolkit 0/3 but its score fell (min delta logit -0.93); derived 0/2, score never below the clean score.
#
# Hypothesis (Claude, before the run): trial evaded on 40-60% of the malware it detects, nearly all by `ent` through
#   regex_https:// and other string counts; derived 0 with its score never falling (Theorem 1); trial-toolkit evaded on
#   a few files (its table misses fewer features, but it is monotone in some the attack can lower: its score fell in
#   the smoke). MAB-Malware has no signature cloning: few or no evasions of any of the three.
# Reading (next R18 session): into this header, then the triage's R18 entry.
#
# Resources: one search per (detector, file), NUM_WORKERS processes (spawn; ~1 GB each), OMP_NUM_THREADS=1 each.
# Real extraction ~0.6 s per candidate on a loaded machine, so a file not evaded takes ~20 min: derived ~40 files at
# the full budget, trial-toolkit ~25, trial ~20: ~30 CPU-h, ~2 h with 16 workers. MAB-Malware ~20 min per detector.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
T=artifacts/experiments/r18_trial
F=artifacts/features/ember2024-sums-10-v2
OUT=artifacts/experiments/r18_trial/attacks
mkdir -p artifacts/logs "$OUT"

if [[ ! -f $T/probe-600.parquet ]]; then
  echo "(0a) The stronger trial: pilot, then 600 test files with donor imports. Log: artifacts/logs/r18_trial_probe.log"
  python scripts/trial_probe.py \
    --db "${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}/ts" \
    --files artifacts/experiments/e1/seed-0/zeros/files.parquet \
    --out $T/probe-pilot.parquet \
    --workers "$NUM_WORKERS" \
    &> artifacts/logs/r18_trial_probe.log
  python scripts/trial_probe.py \
    --db "${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}/ts" \
    --files $T/files-600.parquet \
    --donors 200 \
    --out $T/probe-600.parquet \
    --workers "$NUM_WORKERS" \
    &>> artifacts/logs/r18_trial_probe.log
fi
if [[ ! -f $T/trial-final-toolkit.neutralize.txt ]]; then
  echo "(0b) The trial tables. Log: artifacts/logs/r18_trial_table.log"
  python scripts/trial_table.py \
    --outdir $T \
    --probe $T/probe-pilot.parquet $T/probe-600.parquet \
    --tag=-final \
    &> artifacts/logs/r18_trial_table.log
  python scripts/trial_table.py \
    --outdir $T \
    --probe $T/probe-pilot.parquet $T/probe-600.parquet \
    --toolkit \
    --workers "$NUM_WORKERS" \
    --tag=-final-toolkit \
    &>> artifacts/logs/r18_trial_table.log
fi
for v in trial trial-toolkit; do
  if [[ ! -f $M/seed-0-s10-mfull-feat-$v/model.txt ]]; then
    echo "(0c) Training gbdt/seed-0-s10-mfull-feat-$v. Log: artifacts/logs/train_classic-gbdt-0-s10-mfull-feat-$v.log"
    python scripts/train_classic.py \
      --learner gbdt \
      --seed 0 \
      --num_threads "$NUM_WORKERS" \
      --suffix=-s10-mfull-feat-$v \
      --features $F \
      --neutralize $T/${v/trial/trial-final}.neutralize.txt \
      --monotone $T/${v/trial/trial-final}.monotone.tsv \
      &> artifacts/logs/train_classic-gbdt-0-s10-mfull-feat-$v.log
  fi
done

LOG=artifacts/logs/r18_trial_adaptive.log
echo "(1/2) The real-scored adaptive beam against trial, trial-toolkit and derived (~2 h). Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir $OUT/adaptive \
  --score real \
  --search beam \
  --queries 2000 \
  --checkpoints 200 1000 2000 \
  --beam 3 \
  --draws 2 \
  --patience 3 \
  --seed 0 \
  --threat_model M_full \
  --features $F \
  --defense trial=$M/seed-0-s10-mfull-feat-trial \
  --defense trial-toolkit=$M/seed-0-s10-mfull-feat-trial-toolkit \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat-loose \
  --sound mfull-feat \
  --num_workers "$NUM_WORKERS" \
  &> "$LOG"
tail -6 "$LOG"

LOG=artifacts/logs/r18_trial_mab.log
echo "(2/2) MAB-Malware against the same three (~1 h). Log: $LOG"
python scripts/mab_attack.py \
  --outdir $OUT/mab \
  --workdir $OUT/mab/work \
  --features $F \
  --defense trial=$M/seed-0-s10-mfull-feat-trial \
  --defense trial-toolkit=$M/seed-0-s10-mfull-feat-trial-toolkit \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat-loose \
  --max_pull 60 \
  --max_length 10 \
  --seed 0 \
  --num_workers "$NUM_WORKERS" \
  &> "$LOG"
grep -E "^\S+ +detected" "$LOG"
echo "Done. Reports: $OUT/adaptive/adaptive.json, $OUT/mab/table.json; read them against the hypothesis in this header."
