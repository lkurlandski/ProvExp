#!/bin/bash
# Leave-one-out for the defenses learned from attacks (docs/paper-mock.md, §5, "Revisions after the user's review";
# PLAN.md, decision 10). Replaces the fixed split (seen = padding, gamma_sections, gamma_shift, content_shift) of runs
# 81/100 (PV) and 128 (ERDALT), which held out the strongest attack. FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et
# al.'s published secml-malware attacks and our own adaptive search against our own detectors, on our own pilot
# samples, to evaluate defenses. Nothing is deployed.
#
#   0. Run 122 made attacked training malware for padding, gamma_sections, gamma_shift, content_shift only (~400
#      each). For balanced ERDALT folds, the same 400 training malware (same seed, same 50 donors, same undefended
#      model) are attacked with the other four, into a second directory; run 122's is left as it is. Skipped if its
#      report.json exists.
# For each of the eight toolkit attacks h (a fold):
#   1. PV: features never lowered by the other seven attacks (run 78's perturbation vectors on the pilot malware) are
#      kept, monotone; the rest are dropped. Trained as PV-seen was (run 81: the 10% store, the re-encoded groups
#      dropped); then h attacks the fold's model on the pilot malware it detects (a1_evaluate, low budget, the 1% FPR
#      threshold, re-extracted ground truth: the toolkit protocol of every other cell).
#   2. ERDALT: trained as in run 128 from the other seven attacks' vectors (the pilot ones and the training-malware ones
#      of run 122 and step 0), one model per visible GPU at a time (at most two); then h attacks the fold's model.
#   3. ERDALT from all eight attacks, and its adaptive cell: run 128's beam search (5,000 candidates, M_full). PV's
#      all-eight model and its adaptive cell exist (runs 85 and 127/129: 14/22).
#   4. The summary: per-fold and mean held-out evasion, and the files evaded by their held-out attack in any fold.
#
# Hypothesis (user): PV's held-out evasion stays well above 0, because each attack lowers features the others don't.
# Claude's expectation from the perturbation vectors (2026-11-10): mostly not. The attacks lower nearly the same
# features: of the ~600-720 each lowers, the number no other attack lowers is 49 (gamma_sections, all section
# features), 10 (gamma_api: imports, section, warnings), 0-3 for the other six. PV-seen's 4/22 held-out evasions all
# came from gamma_api. Expected: PV's gamma_api fold about 4/22, perhaps one or two gamma_sections evasions, the
# other folds 0; mean a few percent. ERDALT: the gamma_api and header_fields folds high (22/25 and 17/25 held out in
# run 128), the rest near 0; mean ~20-40%. ERDALT-8: adaptive about run 128's 20/25.
#
# Resources: (0) ~1.6k attack runs (gamma_api ~100 s each, the others ~25-35 s) then featurization: ~1.5 h at 16
# workers (run 122's four took 76 min at 24 workers). (1) per fold ~2 min training (16 threads) + one attack on ~22 files (gamma_api ~100 s per file, the others
# ~15-35 s) at 16 workers: ~25-35 min for the eight folds. (2) ~26 min per model on one GPU (run 128), nine models on
# two GPUs: ~2.2 h (~4 h on one). (3) the eight attacks ~5 min; the beam ~25 min. ~5 h in all on two GPUs.
# Smoke test (Claude, 2026-11-10, outputs in a scratch directory, machine at load ~45): (1) the gamma_api fold in full
#   at 8 workers: selection and training 2.5 min (test AUC 0.946; PV-seen 0.944), gamma_api 10 min; held-out 5/21
#   (24%; PV-seen 4/22), 2 more over the byte cap. (2) the padding fold at 3 epochs and 20,000 samples per split:
#   348 pilot + 1,197 training-malware vectors (exactly padding's removed); evaluation with one held-out attack
#   checked on run 128's model (4 files). (0) step 0 on 2 training malware: 8 attack runs in 43 s at 8 workers, all
#   valid; seed 0 draws the same 400 malware as run 122 (checked); training reads both directories (348 pilot + 1,197
#   + 8 vectors). The GPU choice: no setting -> GPUs 0 and 1; CUDA_VISIBLE_DEVICES=3 or GPUS=3 -> one lane on GPU 3.
#
# Ran 2026-11-10/11 (user, one lane on GPU 3, 16 workers): step 0 1,600 attack runs in 1.5 h (gamma_api 399/400,
# dos_extend 400, header_fields 400, format_exploit 387 valid); step 1 ~50 min for the eight PV folds; step 2 nine
# ERDALT models in 3.2 h on one GPU (~21 min each); the first step 3 crashed on a model-path bug (training wrote
# seed-0-loo-*, evaluation read seed-0-s10-loo-*; folders renamed, script fixed); rerun 2026-11-11: the eight folds
# ~55 min, the beam 24 min.
# Result (artifacts/experiments/a_loo/summary.json), held-out attack evading the fold's model:
#   PV: gamma_api 5/21, the other seven 0 (mean 3%; 5 files evaded in any fold). Claude's expectation held; the user's
#     hypothesis (well above 0) failed.
#   ERDALT: gamma_api 21/24 (no epoch met the criterion; epoch 181 kept), header_fields 10/25, gamma_shift 5/25,
#     content_shift 1/28, format_exploit 1/23, gamma_sections 0/24, dos_extend 0/25, padding 0/25 (mean 19%; 26 files
#     in any fold). Expected high on gamma_api and header_fields, near 0 elsewhere: held, except gamma_shift.
#   ERDALT-8 (criterion met at epoch 287; test AUC 0.871): the beam evades 17 of 24 (15 at 200, 17 at 1,000, 17 at
#     5,000; all confirmed on re-extraction). Expected about run 128's 20/25: held.
#   Caveat found in session 34 (docs/section-5.3-design.md, §3): every model here learns from vectors made with the
#   RNG reset to seed 0 before each run, and PV's and ERDALT's include the pilot (test) malware's vectors.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"
EMBER2024_DATA="${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}"
# GPUs for ERDALT training, comma-separated ids: $GPUS, else $CUDA_VISIBLE_DEVICES, else the first two nvidia-smi lists.
# One training lane per GPU, at most two.
if [[ -z "${GPUS:-}" ]]; then
  GPUS="${CUDA_VISIBLE_DEVICES:-$(nvidia-smi --query-gpu=index --format=csv,noheader | head -2 | paste -sd,)}"
fi
IFS=", " read -r -a GPU_IDS <<< "$GPUS"
if [[ ${#GPU_IDS[@]} -lt 1 ]]; then echo "No GPU found (set GPUS)." >&2; exit 1; fi

ATTACKS="gamma_sections gamma_api gamma_shift content_shift dos_extend header_fields padding format_exploit"
others() { local h=$1 a out=""; for a in $ATTACKS; do [[ $a != "$h" ]] && out="$out $a"; done; echo $out; }

P=artifacts/experiments/a_pv
D=artifacts/experiments/a_directions_sums
OUT=artifacts/experiments/a_loo
M=artifacts/models
F_PV=artifacts/features/ember2024-sums-10      # PV-seen's store (run 81)
F_ER=artifacts/features/ember2024-sums-10-v2   # ERDALT's store (run 128)
ADV=artifacts/experiments/a1/advtrain/generated            # run 122: the four attacks of the old seen set
ADV2=artifacts/experiments/a1/advtrain/generated-heldout   # step 0: the other four
mkdir -p $P/loo $OUT artifacts/logs

log=artifacts/logs/a_advtrain_generate-heldout.log
if [[ -f $ADV2/report.json ]]; then
  echo "(0/4) $ADV2 exists; skipping the generation."
else
  echo "(0/4) Attacked training malware for the four attacks run 122 lacks (~1.5 h). Log: $log"
  OMP_NUM_THREADS=4 python scripts/a_advtrain.py \
    --outdir $ADV2 \
    --features artifacts/features/ember2024 \
    --db "$EMBER2024_DATA/tr" \
    --model $M/gbdt/seed-0/model.txt \
    --attacks gamma_api dos_extend header_fields format_exploit \
    --num_malware 400 \
    --num_goodware 50 \
    --num_workers "$NUM_WORKERS" \
    --seed 0 \
    &> "$log"
  tail -6 "$log"
fi

echo "(1/4) PV, eight folds: selection, training, the held-out attack. Logs: artifacts/logs/*-pv-loo-<attack>.log"
for h in $ATTACKS; do
  seen=$(others $h)
  if [[ -f $OUT/pv/$h/table.json ]]; then echo "  fold $h: $OUT/pv/$h exists; skipping."; continue; fi
  log=artifacts/logs/train_classic-gbdt-0-s10-pv-loo-$h.log
  echo "  fold $h: PV selection and training. Log: $log"
  python scripts/a_pv_hole.py \
    --deltas $P/deltas.parquet \
    --attacks $seen \
    --tag=-loo-$h \
    --outdir $P/loo \
    > artifacts/logs/a_pv_hole-loo-$h.log
  cat $P/loo/pv-loo-$h.neutralize.txt $D/reencoded.neutralize.txt > $P/loo/pv-loo-$h-s10.neutralize.txt
  OMP_NUM_THREADS=16 python scripts/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --num_threads 16 \
    --features $F_PV \
    --suffix=-s10-pv-loo-$h \
    --neutralize $P/loo/pv-loo-$h-s10.neutralize.txt \
    --monotone $P/loo/pv-loo-$h.monotone.tsv \
    &> "$log"
  log=artifacts/logs/a1_eval-pv-loo-$h.log
  echo "  fold $h: $h against the fold's model. Log: $log"
  OMP_NUM_THREADS=1 python scripts/a1_evaluate.py \
    --outdir $OUT/pv/$h \
    --features $F_PV \
    --defense pv-loo-$h=$M/gbdt/seed-0-s10-pv-loo-$h \
    --attacks $h \
    --seen $seen \
    --num_workers "$NUM_WORKERS" \
    --seed 0 \
    &> "$log"
  grep "held-out" "$log" | tail -1
done

echo "(2/4) ERDALT, nine models (eight folds, all eight) on GPUs ${GPU_IDS[*]:0:2}. Logs: artifacts/logs/train_erdalt-0-s10-loo-*.log"
train_erdalt() {  # gpu, suffix, attacks...
  local gpu=$1 suffix=$2; shift 2
  local log=artifacts/logs/train_erdalt-0-s10$suffix.log
  if [[ -f $M/erdalt/seed-0-s10$suffix/ts_predictions.parquet ]]; then
    echo "  erdalt/seed-0-s10$suffix exists; skipping."
    return
  fi
  echo "  training erdalt/seed-0-s10$suffix on GPU $gpu. Log: $log"
  CUDA_VISIBLE_DEVICES=$gpu OMP_NUM_THREADS=8 python scripts/train_erdalt.py \
    --features $F_ER \
    --neutralize $D/reencoded.neutralize.txt \
    --deltas $P/deltas.parquet \
    --adv_dir $ADV $ADV2 \
    --attacks "$@" \
    --suffix="-s10$suffix" \
    --epochs 310 \
    --batch_size 256 \
    --seed 0 \
    &> "$log"
}
lane() {  # gpu, then fold names ("all8" for the model from all eight)
  local gpu=$1 h; shift
  for h in "$@"; do
    if [[ $h == all8 ]]; then train_erdalt "$gpu" -all8 $ATTACKS; else train_erdalt "$gpu" -loo-$h $(others $h); fi
  done
}
if [[ ${#GPU_IDS[@]} -ge 2 ]]; then
  lane "${GPU_IDS[0]}" all8 gamma_sections gamma_api gamma_shift content_shift &
  lane_a=$!
  lane "${GPU_IDS[1]}" dos_extend header_fields padding format_exploit &
  lane_b=$!
  wait $lane_a  # a failed lane stops the script (set -e)
  wait $lane_b
else
  lane "${GPU_IDS[0]}" all8 $ATTACKS
fi

echo "(3/4) ERDALT: each fold's held-out attack, then the beam search against ERDALT-8."
for h in $ATTACKS; do
  log=artifacts/logs/a1_eval-erdalt-loo-$h.log
  echo "  fold $h. Log: $log"
  OMP_NUM_THREADS=1 python scripts/a1_evaluate.py \
    --outdir $OUT/erdalt/$h \
    --features $F_ER \
    --defense erdalt-loo-$h=$M/erdalt/seed-0-s10-loo-$h \
    --attacks $h \
    --seen $(others $h) \
    --num_workers "$NUM_WORKERS" \
    --seed 0 \
    &> "$log"
  grep "held-out" "$log" | tail -1
done
log=artifacts/logs/a1_adaptive-erdalt-all8.log
echo "  the beam search (5,000 candidates, M_full) against ERDALT-8. Log: $log"
OMP_NUM_THREADS=1 python scripts/a1_adaptive.py \
  --outdir $OUT/erdalt-all8-adaptive \
  --features $F_ER \
  --threat_model M_full \
  --defense erdalt-all8=$M/erdalt/seed-0-s10-all8 \
  --search beam \
  --queries 5000 \
  --checkpoints 200 1000 5000 \
  --beam 3 \
  --draws 2 \
  --patience 3 \
  --seed 0 \
  --num_workers "$NUM_WORKERS" \
  &> "$log"
tail -6 "$log"

echo "(4/4) Summary: $OUT/summary.json"
python - $OUT "$ATTACKS" <<'PY'
import json, sys
from pathlib import Path
import polars as pl
out, attacks = Path(sys.argv[1]), sys.argv[2].split()
summary = {}
for d in ("pv", "erdalt"):
    folds, evaded_any = {}, set()
    for h in attacks:
        f = out / d / h / "table.json"
        if not f.exists():
            folds[h] = None
            continue
        g = next(iter(json.loads(f.read_text())["defenses"].values()))
        folds[h] = {"detected": g["detected"], **g["groups"]["held_out"]["all"]}
        r = pl.read_parquet(out / d / h / "results.parquet")
        evaded_any |= set(r.filter(pl.col("evaded"))["name"].to_list())
    rates = [v["rate"] for v in folds.values() if v and v["rate"] is not None]
    summary[d] = {"folds": folds, "mean_rate": sum(rates) / len(rates) if rates else None,
                  "files_evaded_in_any_fold": len(evaded_any)}
    print(f"{d}: mean held-out evasion {summary[d]['mean_rate']}; files evaded in any fold "
          f"{len(evaded_any)}")
    for h, v in folds.items():
        print(f"  {h:15s} {'missing' if v is None else f'{v['evaded']}/{v['files']}'}")
(out / "summary.json").write_text(json.dumps(summary, indent=2))
PY
echo "Done. $OUT/summary.json; ERDALT-8 adaptive: $OUT/erdalt-all8-adaptive/adaptive.json"
