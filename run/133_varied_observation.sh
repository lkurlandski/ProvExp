#!/bin/bash
# §5.3, Phase 2 (docs/section-5.3-design.md, §10.3): the defenses learned from attacks, rebuilt the fair way. FOR
# ACADEMIC SECURITY RESEARCH ONLY: published secml-malware attacks and our own adaptive search against our own
# detectors, on our own training and pilot samples, to evaluate defenses. Nothing is deployed.
#
# Why: runs 78, 122 and 131 reset the RNG to seed 0 before every attack run (Gimenez et al.'s protocol), so GAMMA's
# section names are the same on every file, and PV and ERDALT also learned from the pilot (test) malware. Run 132
# showed that a seed per file lets one attack cover every section-name bucket, closing most of what PV's hole rests on.
# Here every defense learns from the same observations: the eight toolkit attacks, a seed per (attack, file), on 400
# training malware with training goodware as donors; nothing from the test files.
#
#   1. Generate: the eight attacks, seed per file, 400 training malware (low budget, against the undefended model).
#   2. PV-best: selection from step 1's vectors, trained as PV-seen/PV-all were (10% sums store, re-encoded groups
#      dropped); then its hole against the derived table (M_full, precondition, quirk-fixed), weighted by its gain.
#   3. Coverage of step 1's outputs and PV-best's hole split by source and witnessed by our edits (a_coverage).
#   4. ERDALT-best: trained as run 128/131 from step 1's vectors only, on the first GPU of $GPUS; its layer's audit.
#   5. Adversarial training from step 1's outputs (full store, appended, as run 125).
#   6. The eight attacks, seed per file, on the pilot malware each defense detects (its authors' evaluation, on new
#      files), against: PV-best and the old PV-all (10% sums store); ERDALT-best and the old ERDALT-8 (v2 store); the
#      adversarially trained and the undefended full-store GBDTs. The old models show what re-running the attacks they
#      were built from with other seeds does to them.
#   7. The adaptive beam (5,000 candidates, M_full; run 127's protocol) against PV-best, ERDALT-best, and the
#      adversarially trained model.
# Every step skips when its output exists, so the script can be rerun after an interruption.
#
# Hypotheses (Claude, 2026-11-11, before the run):
#   (1) Coverage of the lowerable set on the training malware in the population rises from 847 (seed 0) to >= 900; of
#       the 90 features our edits lower and the toolkit never did, >= 70 are lowered now; the entry-section-name
#       buckets (rename only) stay unlowered.
#   (2) PV-best keeps fewer features than PV-all (1,736) and loses a few points of TPR (PV-all 53.8%); its hole,
#       witnessed by our edits and without the warnings, falls from 24.6% of gain to <= 10%.
#   (6) The old PV-all is evaded by its own attacks re-run with other seeds (gamma_sections above all) on several of its
#       22 files; PV-best on 0-2. ERDALT-best on its own attacks: a few files (their paper: 96% robust).
#   (7) The beam against PV-best: well below PV-all's 14/22, perhaps 0-5; against ERDALT-best: still high (>= 12 of
#       ~24), since ERDALT constrains the observed vectors, not the directions; adversarial training about run 130's
#       24/49.
#
# Resources (estimates from runs 122, 125, 128, 130, 131): (1) 3,200 attack runs, ~3.5 h at 16 workers (step 0 of run
# 131: four attacks in 1.5 h; run 122: four in 76 min at 24 workers); (2) ~5 min; (3) ~3 min; (4) ~26 min on one GPU;
# (5) ~10 min, ~30 GB peak; (6) ~1,500 attack runs, ~1.2 h; (7) ~95 (defense, file) pairs, ~1.5 h. ~7 h in all.
# Smoke (Claude, 2026-11-11): PV selection from training-malware vectors (a_pv_hole --adv_dir) on run 132's 100
# gamma_sections vectors; a1_evaluate --seed_per_file on 6 pilot files with gamma_sections against PV-all (1 detected,
# not evaded, score 0.958 -> 0.891). a_advtrain --seed_per_file is run 132's step 2.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"
EMBER2024_DATA="${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}"
if [[ -z "${GPUS:-}" ]]; then
  GPUS="${CUDA_VISIBLE_DEVICES:-$(nvidia-smi --query-gpu=index --format=csv,noheader | head -1)}"
fi
GPU="${GPUS%%,*}"

ATTACKS="gamma_sections gamma_api gamma_shift content_shift dos_extend header_fields padding format_exploit"
M=artifacts/models
F_FULL=artifacts/features/ember2024
F_PV=artifacts/features/ember2024-sums-10      # PV-seen's and PV-all's store (runs 81, 85)
F_ER=artifacts/features/ember2024-sums-10-v2   # ERDALT's store (runs 128, 131)
DS=artifacts/experiments/a_directions_sums
DV2=artifacts/experiments/a_directions_derived_v2
GEN=artifacts/experiments/a1/advtrain/generated-seedperfile
PV=artifacts/experiments/a_pv/best
OUT=artifacts/experiments/a_varied
mkdir -p $PV $OUT artifacts/logs

log=artifacts/logs/a_advtrain_generate-seedperfile.log
if [[ -f $GEN/report.json ]]; then
  echo "(1/7) $GEN exists; skipping the generation."
else
  echo "(1/7) The eight attacks, a seed per file, on 400 training malware (~3.5 h). Log: $log"
  OMP_NUM_THREADS=1 python scripts/a_advtrain.py \
    --outdir $GEN \
    --features $F_FULL \
    --db "$EMBER2024_DATA/tr" \
    --model $M/gbdt/seed-0/model.txt \
    --attacks $ATTACKS \
    --num_malware 400 \
    --num_goodware 50 \
    --num_workers "$NUM_WORKERS" \
    --seed 0 \
    --seed_per_file \
    &> "$log"
  tail -10 "$log" | grep -v -i semaphore
fi

if [[ -f $M/gbdt/seed-0-s10-pv-best/model.txt ]]; then
  echo "(2/7) PV-best exists; skipping."
else
  echo "(2/7) PV-best: selection, training, its hole. Logs: artifacts/logs/*pv-best*.log"
  OMP_NUM_THREADS=4 python scripts/a_pv_hole.py \
    --adv_dir $GEN \
    --adv_features $F_FULL \
    --tag=-best \
    --outdir $PV \
    > artifacts/logs/a_pv_hole-best-select.log
  cat $PV/pv-best.neutralize.txt $DS/reencoded.neutralize.txt > $PV/pv-best-s10.neutralize.txt
  OMP_NUM_THREADS=16 python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --features $F_PV \
    --suffix=-s10-pv-best \
    --neutralize $PV/pv-best-s10.neutralize.txt \
    --monotone $PV/pv-best.monotone.tsv \
    &> artifacts/logs/train_classic-gbdt-0-s10-pv-best.log
fi
OMP_NUM_THREADS=4 python scripts/a_pv_hole.py \
  --adv_dir $GEN \
  --adv_features $F_FULL \
  --directions_dir $DV2 \
  --variant pre-quirkfixed \
  --model $M/gbdt/seed-0-s10-pv-best/model.txt \
  --tag=-best \
  --outdir $PV/derived-pre \
  > artifacts/logs/a_pv_hole-best.log
grep -E "pv_kept|gain_share_hole_over_pv" artifacts/logs/a_pv_hole-best.log

log=artifacts/logs/a_coverage-seedperfile.log
echo "(3/7) Coverage of the varied outputs; PV-best's hole by source and witness (~3 min). Log: $log"
OMP_NUM_THREADS=2 python scripts/a_coverage.py \
  --outdir $OUT/coverage \
  --adv_dir $GEN \
  --adv_features $F_FULL \
  --db "$EMBER2024_DATA/tr" \
  --holes $PV/derived-pre/hole-best.csv artifacts/experiments/a_pv/derived-pre/hole.csv \
  --num_workers "$NUM_WORKERS" \
  &> "$log"
grep -E "^(train_population|witnessed|pv_hole_witnessed)" "$log" | cut -c1-400

log=artifacts/logs/train_erdalt-0-s10-best.log
if [[ -f $M/erdalt/seed-0-s10-best/ts_predictions.parquet ]]; then
  echo "(4/7) ERDALT-best exists; skipping the training."
else
  echo "(4/7) ERDALT-best on GPU $GPU (~26 min). Log: $log"
  CUDA_VISIBLE_DEVICES=$GPU OMP_NUM_THREADS=8 python scripts/train_erdalt.py \
    --features $F_ER \
    --neutralize $DS/reencoded.neutralize.txt \
    --adv_dir $GEN \
    --adv_features $F_FULL \
    --attacks $ATTACKS \
    --suffix=-s10-best \
    --epochs 310 \
    --batch_size 256 \
    --seed 0 \
    &> "$log"
  tail -3 "$log"
fi
OMP_NUM_THREADS=4 python scripts/a_erdalt_hole.py \
  --model $M/erdalt/seed-0-s10-best \
  --directions artifacts/experiments/a_directions_derived_sums_v2/M_full-pre-control \
  --outdir $OUT/erdalt-best-hole \
  &> artifacts/logs/a_erdalt_hole-best.log
head -20 artifacts/logs/a_erdalt_hole-best.log

log=artifacts/logs/train_classic-gbdt-0-advtrain-seedperfile.log
if [[ -f $M/gbdt/seed-0-advtrain-seedperfile/model.txt ]]; then
  echo "(5/7) The adversarially trained model exists; skipping."
else
  echo "(5/7) Adversarial training on the varied outputs (full store, ~10 min, ~30 GB). Log: $log"
  OMP_NUM_THREADS=16 python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --suffix=-advtrain-seedperfile \
    --augment $GEN \
    &> "$log"
  tail -3 "$log"
fi

echo "(6/7) The eight attacks, a seed per file, on the pilot malware (~1.2 h). Logs: artifacts/logs/a1_eval-varied-*.log"
evaluate() {  # tag, store, defense specs...
  local tag=$1 store=$2; shift 2
  local log=artifacts/logs/a1_eval-varied-$tag.log
  if [[ -f $OUT/toolkit-$tag/table.json ]]; then echo "  $tag exists; skipping."; return; fi
  echo "  $tag. Log: $log"
  OMP_NUM_THREADS=1 python scripts/a1_evaluate.py \
    --outdir $OUT/toolkit-$tag \
    --features $store \
    "$@" \
    --seen $ATTACKS \
    --num_workers "$NUM_WORKERS" \
    --seed 0 \
    --seed_per_file \
    &> "$log"
  grep -E "detected" "$log" | cut -c1-200
}
evaluate pv $F_PV \
  --defense pv-best=$M/gbdt/seed-0-s10-pv-best \
  --defense pv-all=$M/gbdt/seed-0-s10-pv-all
evaluate erdalt $F_ER \
  --defense erdalt-best=$M/erdalt/seed-0-s10-best \
  --defense erdalt-all8=$M/erdalt/seed-0-s10-all8
evaluate full $F_FULL \
  --defense advtrain-best=$M/gbdt/seed-0-advtrain-seedperfile \
  --defense unconstrained=$M/gbdt/seed-0

echo "(7/7) The adaptive beam (5,000 candidates, M_full). Logs: artifacts/logs/a1_adaptive-varied-*.log"
adaptive() {  # tag, store, defense spec
  local tag=$1 store=$2 spec=$3
  local log=artifacts/logs/a1_adaptive-varied-$tag.log
  if [[ -f $OUT/adaptive-$tag/adaptive.json ]]; then echo "  $tag exists; skipping."; return; fi
  echo "  $tag. Log: $log"
  OMP_NUM_THREADS=1 python scripts/a1_adaptive.py \
    --outdir $OUT/adaptive-$tag \
    --features $store \
    --threat_model M_full \
    --defense "$spec" \
    --search beam \
    --queries 5000 \
    --checkpoints 200 1000 5000 \
    --beam 3 \
    --draws 2 \
    --patience 3 \
    --seed 0 \
    --num_workers "$NUM_WORKERS" \
    &> "$log"
  grep -E "detected" "$log" | tail -1
}
adaptive pv-best $F_PV pv-best=$M/gbdt/seed-0-s10-pv-best
adaptive erdalt-best $F_ER erdalt-best=$M/erdalt/seed-0-s10-best
adaptive advtrain-best $F_FULL advtrain-best=$M/gbdt/seed-0-advtrain-seedperfile

echo "Done. Outputs under $OUT/ and $PV/; read them against the hypotheses in this header."
