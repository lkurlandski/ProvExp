#!/bin/bash
# Table 7 (the detector table): a "strong toolkit" column, the GAMMA attacks at the GAMMA paper's budget (Demetrio et
# al., TIFS 2021: population 10, ~510 queries, 75 donor sections; a_pv_attacks.BUDGETS["literature"]) instead of
# Gimenez et al.'s low one (~100 queries, 30 donors). Answers the question the low budget leaves open: are the sound
# detectors' 0% and the baselines' numbers an artifact of weak attacks? FOR ACADEMIC SECURITY RESEARCH ONLY: published
# secml-malware attacks against our own detectors, on our own pilot samples, to evaluate defenses. Nothing is deployed.
#
# Attacks: gamma_sections (benign-section injection, the literature's headline attack on GBDTs) and gamma_api (benign
# import injection, the toolkit attack that evades most at the low budget: 22/49). Both are additions, so they lie in
# both the full and the additions threat model. Evasion is reported within the byte cap (max(5%, 512 KB), as every
# Table 7 cell) and without it ("uncapped" in table.json), since GAMMA's own size control is a penalty, not a cap.
#
# Two calls, one per feature store: (1) the full-store detectors (unconstrained seed-0, run 122's adversarial training);
# (2) the 10%-subsample detectors of Table 7 (reference, PV, the monotone rows routed to the reference, as run 105).
#
# Hypothesis: the unconstrained detectors lose noticeably more than at the low budget (gamma_api well above 22/49 in
# the cap-free count), the monotone rows stay at 0% on files in their population (the guarantee does not depend on the
# attack's budget), and gamma_sections stays weak: the smoke test (3 files) found injected sections RAISE the score of
# this detector even at ~1 MB, so a larger budget may not help that attack.
#
# Resources: smoke test (2026-11-04) ~100-200 s per (file, attack), 2-3x the low budget (searches stop after 5 rounds
# without improvement). ~194 tasks in call (1), ~388 in call (2): ~2-2.5 h at 16 workers, ~1.5 h at 24.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/a1/toolkit-literature
ATTACKS="gamma_sections gamma_api"

LOG=artifacts/logs/a1_eval_literature_fullstore.log
echo "(1/2) GAMMA at the literature budget x the full-store detectors (unconstrained, adversarial training). Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir "$OUT/fullstore" \
  --features artifacts/features/ember2024 \
  --defense unconstrained=$M/seed-0 \
  --defense advtrain=$M/seed-0-advtrain \
  --attacks $ATTACKS \
  --seen $ATTACKS \
  --budget literature \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> "$LOG"
tail -4 "$LOG"

LOG=artifacts/logs/a1_eval_literature_s10.log
echo "(2/2) GAMMA at the literature budget x the 10%-subsample detectors (reference, PV, monotone). Log: $LOG"
python scripts/a1_evaluate.py \
  --outdir "$OUT/s10" \
  --features artifacts/features/ember2024-sums-10-v2 \
  --defense ref=$M/seed-0-s10-ref \
  --defense pv-seen=$M/seed-0-s10-pv-seen \
  --defense mfull-feat=$M/seed-0-s10-mfull-feat-pre-v2 \
  --defense mfull-sums=$M/seed-0-s10-mfull-sums-pre-v2 \
  --defense madd-sums=$M/seed-0-s10-madd-sums-pre-v2 \
  --route mfull-feat=ref \
  --route mfull-sums=ref \
  --route madd-sums=ref \
  --attacks $ATTACKS \
  --seen $ATTACKS \
  --budget literature \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  &> "$LOG"
tail -8 "$LOG"

echo
echo "Strong-toolkit column (within the byte cap / uncapped), per detector:"
python - "$OUT/fullstore/table.json" "$OUT/s10/table.json" <<'PY'
import json, sys
for path in sys.argv[1:]:
    for d, e in json.load(open(path))["defenses"].items():
        g = e["groups"]["all"]
        per = {k: v["evaded"] for k, v in e["per_attack"].items()}
        print(f"  {d:14s} detected {e['detected']:2d}  capped {g['all']['evaded']:2d}  uncapped {g['uncapped']['evaded']:2d}  "
              f"in population (capped) {g['precondition']['evaded']}/{g['precondition']['files']}  per attack {per}")
PY
echo "Done. Tables: $OUT/fullstore/table.json, $OUT/s10/table.json"
