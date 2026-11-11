#!/bin/bash
# §5.3, Phase 2b (docs/section-5.3-design.md, §10.4): is PV-best's low detection a straw man? FOR ACADEMIC SECURITY
# RESEARCH ONLY: defenses built from published attacks on our own training samples. Nothing is deployed.
#
# Why: run 133's PV-best detects 26.2% at 1% FPR (PV-all 53.8%). On 4 training files gamma_shift and content_shift
# leave an import table pefile no longer parses; those 8 outputs (of 3,183) lower 75-321 import buckets each, and PV
# drops ~415 import features no edit in the threat model can lower. A careful defender would discard them. PV-clean
# leaves out every output that lowers >= 20 import features (exactly those 8) and is otherwise built as PV-best.
#
# Hypothesis (Claude, 2026-11-11): PV-clean detects about as much as PV-all (~50% at 1% FPR). **Failed.**
#
# Results (Claude ran it, 2026-11-11; selection ~1 min, training 20 s, hole ~1 min):
#   PV-clean keeps 1,490 features (PV-best 1,137, PV-all 1,736); test AUC 0.841, TPR 26.7% at 1% FPR, 9.5% at 0.1%
#   (PV-best 26.2%, 10.3%): the broken outputs are not the cause. Its hole: 125 features, 36.9% of its gain (PV-best
#   38.8%), led by the same features (entry-section-name bucket 1 10.1%, strings:regex_process 6.5%). The cause is
#   elsewhere: PV-all's single largest feature (31% of its gain) is the parser warning "Suspicious flags set for
#   section", which the derived table marks lowerable and which the shift, DOS and format attacks lower on training
#   files but never did on the pilot files PV-all was built from; PV-best/clean drop it. The remaining steps planned for
#   this script (toolkit, adaptive beam) were dropped: PV-clean is PV-best in all that matters.
#   Step 2, PV-free (Claude, after reading step 1; training 20 s): PV-clean's selection, but only the 1,035 kept
#   features some attack moved are constrained; the 455 never moved are left free. TPR 50.9% at 1% FPR, 33.8% at 0.1%.
#   PV constrains every feature no attack moved, and the largest is header:characteristics_DLL (24% of the unconstrained
#   model's gain), which no edit can move (the derived table leaves it free). Leaving them free recovers 24 points but is
#   unsound against any operation the attacks lacked; the derived detector on the same features: 87.3%.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

M=artifacts/models
GEN=artifacts/experiments/a1/advtrain/generated-seedperfile
PV=artifacts/experiments/a_pv/clean
mkdir -p $PV artifacts/logs

echo "(1/2) PV-clean: selection, training, its hole. Logs: artifacts/logs/*pv-clean*.log"
OMP_NUM_THREADS=4 python scripts/a_pv_hole.py \
  --adv_dir $GEN \
  --adv_features artifacts/features/ember2024 \
  --drop_import_loss 20 \
  --tag=-clean \
  --outdir $PV \
  > artifacts/logs/a_pv_hole-clean-select.log
cat $PV/pv-clean.neutralize.txt artifacts/experiments/a_directions_sums/reencoded.neutralize.txt \
  > $PV/pv-clean-s10.neutralize.txt
OMP_NUM_THREADS=16 python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads 16 \
  --features artifacts/features/ember2024-sums-10 \
  --suffix=-s10-pv-clean \
  --neutralize $PV/pv-clean-s10.neutralize.txt \
  --monotone $PV/pv-clean.monotone.tsv \
  &> artifacts/logs/train_classic-gbdt-0-s10-pv-clean.log
OMP_NUM_THREADS=4 python scripts/a_pv_hole.py \
  --adv_dir $GEN \
  --adv_features artifacts/features/ember2024 \
  --drop_import_loss 20 \
  --directions_dir artifacts/experiments/a_directions_derived_v2 \
  --variant pre-quirkfixed \
  --model $M/gbdt/seed-0-s10-pv-clean/model.txt \
  --tag=-clean \
  --outdir $PV/derived-pre \
  > artifacts/logs/a_pv_hole-clean.log
grep -E "pv_kept|gain_share_hole_over_pv" $PV/derived-pre/report-clean.json

echo "(2/2) PV-free: never-moved features left unconstrained (20 s). Log: artifacts/logs/train_classic-gbdt-0-s10-pv-free.log"
OMP_NUM_THREADS=16 python scripts/train_classic.py \
  --learner gbdt \
  --seed 0 \
  --num_threads 16 \
  --features artifacts/features/ember2024-sums-10 \
  --suffix=-s10-pv-free \
  --neutralize $PV/pv-clean-s10.neutralize.txt \
  --monotone $PV/pv-clean-free.monotone.tsv \
  &> artifacts/logs/train_classic-gbdt-0-s10-pv-free.log
