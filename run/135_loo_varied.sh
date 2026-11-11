#!/bin/bash
# §5.3: leave-one-out, done the fair way (docs/section-5.3-design.md, §10.5). FOR ACADEMIC SECURITY RESEARCH ONLY:
# Gimenez et al.'s published secml-malware attacks against our own detectors, on our own training and pilot samples,
# to evaluate defenses. Nothing is deployed.
#
# Why: run 131's folds learned from vectors made with the RNG reset to seed 0 before every run (GAMMA's section names
# the same on every file), and PV's and ERDALT's included the pilot (test) malware's vectors. Run 133 fixed both for
# the defenses built from all eight attacks; this redoes leave-one-out on the same footing. Every fold learns only
# from run 133's outputs (a seed per (attack, file), 400 training malware, training goodware donors) minus the held-out
# attack, and is then attacked by the held-out attack with a seed per file on the pilot malware it detects (pilot
# goodware donors). The all-eight models are run 133's PV-best and ERDALT-best; nothing new to train for them.
#
# For each of the eight toolkit attacks h (a fold):
#   1. PV: Gimenez et al.'s selection from the other seven attacks' vectors (a_pv_hole --attacks), trained as PV-best
#      (10% sums store, re-encoded groups dropped); then h against the fold's model (a1_evaluate --seed_per_file).
#   2. ERDALT: trained as ERDALT-best from the other seven attacks' vectors, one training lane per visible GPU
#      (CUDA_VISIBLE_DEVICES, else every GPU nvidia-smi lists), the folds dealt round-robin.
#   3. h against each ERDALT fold's model.
#   4. Summary: per fold, held-out evasion and detection; files evaded in any fold.
# Every step skips when its output exists, so the script can be rerun after an interruption.
#
# Hypotheses (Claude, 2026-11-11, before the run):
#   PV: held-out evasion low in every fold (0-2 files each, most folds 0): the eight attacks lower nearly the same
#     features (run 131: 0-3 features unique to six of them), so holding one out reveals little; what gets through
#     PV-best is an operation none of them has (rename, run 133). gamma_api is the likeliest exception (run 131: 5/21).
#     Caveat: PV-best detects only 9 pilot files, so each fold judges on ~10 files.
#   ERDALT: high where the held-out attack writes values the other seven never produced, gamma_api (imports from other
#     donors; ERDALT-best saw them and still let 24/29 through) and header_fields (run 131: 10/25); near 0 for padding,
#     dos_extend, gamma_sections; mean ~20-40%.
#
# Resources (from runs 131 and 133): (1) per fold ~1 min selection and training + the held-out attack on ~10 files
# (gamma_api ~100 s per file, the others ~15-35 s) at 16 workers: ~15-25 min for the eight folds. (2) ~21-26 min per
# model on one GPU, eight models: ~3.3 h on one GPU, ~1.7 h on two, ~50 min on four. (3) the held-out attack on ~25-30 files per fold:
# ~40-60 min for the eight. ~2.5-4.5 h in all.
# Smoke (Claude, 2026-11-11, outputs in a scratch directory): (1) the gamma_api fold's selection from the other seven
#   (2,784 vectors = 3,183 - gamma_api's 399; 1,153 features kept), training 20 s, gamma_api on 12 pilot malware with
#   a seed per file (1 detected, counted as held-out, not evaded; 3 min at 4 workers). (2) the padding fold's ERDALT,
#   2 epochs on 20,000 samples per split: 2,783 vectors (= 3,183 - padding's 400), the seven attacks recorded.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"
# ERDALT trains one model per visible GPU at a time: the devices in CUDA_VISIBLE_DEVICES, else every GPU nvidia-smi
# lists.
if [[ -n "${CUDA_VISIBLE_DEVICES+set}" ]]; then
  IFS=", " read -r -a GPU_IDS <<< "$CUDA_VISIBLE_DEVICES"
else
  mapfile -t GPU_IDS < <(nvidia-smi --query-gpu=index --format=csv,noheader)
fi
if [[ ${#GPU_IDS[@]} -lt 1 ]]; then echo "No visible GPU (CUDA_VISIBLE_DEVICES)." >&2; exit 1; fi

ATTACKS="gamma_sections gamma_api gamma_shift content_shift dos_extend header_fields padding format_exploit"
others() { local h=$1 a out=""; for a in $ATTACKS; do [[ $a != "$h" ]] && out="$out $a"; done; echo $out; }

M=artifacts/models
F_FULL=artifacts/features/ember2024
F_PV=artifacts/features/ember2024-sums-10      # PV-best's store (run 133)
F_ER=artifacts/features/ember2024-sums-10-v2   # ERDALT-best's store (run 133)
DS=artifacts/experiments/a_directions_sums
GEN=artifacts/experiments/a1/advtrain/generated-seedperfile   # run 133's outputs
PV=artifacts/experiments/a_pv/vloo
OUT=artifacts/experiments/a_loo_varied
mkdir -p $PV $OUT artifacts/logs
if [[ ! -f $GEN/report.json ]]; then echo "Run 133's outputs ($GEN) are missing." >&2; exit 1; fi

echo "(1/4) PV, eight folds: selection, training, the held-out attack. Logs: artifacts/logs/*-pv-vloo-<attack>.log"
for h in $ATTACKS; do
  seen=$(others $h)
  if [[ -f $OUT/pv/$h/table.json ]]; then echo "  fold $h: $OUT/pv/$h exists; skipping."; continue; fi
  log=artifacts/logs/train_classic-gbdt-0-s10-pv-vloo-$h.log
  if [[ ! -f $M/gbdt/seed-0-s10-pv-vloo-$h/model.txt ]]; then
    echo "  fold $h: PV selection and training. Log: $log"
    OMP_NUM_THREADS=4 python scripts/a_pv_hole.py \
      --adv_dir $GEN \
      --adv_features $F_FULL \
      --attacks $seen \
      --tag=-vloo-$h \
      --outdir $PV \
      > artifacts/logs/a_pv_hole-vloo-$h.log
    cat $PV/pv-vloo-$h.neutralize.txt $DS/reencoded.neutralize.txt > $PV/pv-vloo-$h-s10.neutralize.txt
    OMP_NUM_THREADS=16 python scripts/train_classic.py \
      --learner gbdt \
      --seed 0 \
      --num_threads 16 \
      --features $F_PV \
      --suffix=-s10-pv-vloo-$h \
      --neutralize $PV/pv-vloo-$h-s10.neutralize.txt \
      --monotone $PV/pv-vloo-$h.monotone.tsv \
      &> "$log"
  fi
  log=artifacts/logs/a1_eval-pv-vloo-$h.log
  echo "  fold $h: $h against the fold's model. Log: $log"
  OMP_NUM_THREADS=1 python scripts/a1_evaluate.py \
    --outdir $OUT/pv/$h \
    --features $F_PV \
    --defense pv-vloo-$h=$M/gbdt/seed-0-s10-pv-vloo-$h \
    --attacks $h \
    --seen $seen \
    --num_workers "$NUM_WORKERS" \
    --seed 0 \
    --seed_per_file \
    &> "$log"
  grep "held-out" "$log" | tail -1
done

echo "(2/4) ERDALT, eight folds on GPUs ${GPU_IDS[*]}. Logs: artifacts/logs/train_erdalt-0-s10-vloo-*.log"
train_erdalt() {  # gpu, held-out attack
  local gpu=$1 h=$2
  local log=artifacts/logs/train_erdalt-0-s10-vloo-$h.log
  if [[ -f $M/erdalt/seed-0-s10-vloo-$h/ts_predictions.parquet ]]; then
    echo "  erdalt/seed-0-s10-vloo-$h exists; skipping."
    return
  fi
  echo "  training erdalt/seed-0-s10-vloo-$h on GPU $gpu. Log: $log"
  CUDA_VISIBLE_DEVICES=$gpu OMP_NUM_THREADS=8 python scripts/train_erdalt.py \
    --features $F_ER \
    --neutralize $DS/reencoded.neutralize.txt \
    --adv_dir $GEN \
    --adv_features $F_FULL \
    --attacks $(others $h) \
    --suffix=-s10-vloo-$h \
    --epochs 310 \
    --batch_size 256 \
    --seed 0 \
    &> "$log"
}
lane() {  # gpu, then held-out attacks
  local gpu=$1 h; shift
  for h in "$@"; do train_erdalt "$gpu" "$h"; done
}
LANES=()
i=0
for h in $ATTACKS; do  # the folds dealt round-robin over the visible GPUs
  LANES[$((i % ${#GPU_IDS[@]}))]+=" $h"
  i=$((i + 1))
done
pids=()
for k in "${!LANES[@]}"; do
  lane "${GPU_IDS[$k]}" ${LANES[$k]} &
  pids+=($!)
done
for p in "${pids[@]}"; do
  wait "$p"  # a failed lane stops the script (set -e)
done

echo "(3/4) ERDALT: each fold's held-out attack. Logs: artifacts/logs/a1_eval-erdalt-vloo-<attack>.log"
for h in $ATTACKS; do
  if [[ -f $OUT/erdalt/$h/table.json ]]; then echo "  fold $h: $OUT/erdalt/$h exists; skipping."; continue; fi
  log=artifacts/logs/a1_eval-erdalt-vloo-$h.log
  echo "  fold $h. Log: $log"
  OMP_NUM_THREADS=1 python scripts/a1_evaluate.py \
    --outdir $OUT/erdalt/$h \
    --features $F_ER \
    --defense erdalt-vloo-$h=$M/erdalt/seed-0-s10-vloo-$h \
    --attacks $h \
    --seen $(others $h) \
    --num_workers "$NUM_WORKERS" \
    --seed 0 \
    --seed_per_file \
    &> "$log"
  grep "held-out" "$log" | tail -1
done

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
    print(f"{d}: mean held-out evasion {summary[d]['mean_rate']}; files evaded in any fold {len(evaded_any)}")
    for h, v in folds.items():
        print(f"  {h:15s} {'missing' if v is None else f'{v['evaded']}/{v['files']} (detected {v['detected']})'}")
(out / "summary.json").write_text(json.dumps(summary, indent=2))
PY
echo "Done. Read $OUT/summary.json against the hypotheses in this header."
