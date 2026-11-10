#!/bin/bash
# Leave-one-out for the defenses learned from attacks (docs/paper-mock.md, §5, "Revisions after the user's review";
# PLAN.md, decision 10). Replaces the fixed split (seen = padding, gamma_sections, gamma_shift, content_shift) of runs
# 81/100 (PV) and 128 (ERDALT), which held out the strongest attack. FOR ACADEMIC SECURITY RESEARCH ONLY: Gimenez et
# al.'s published secml-malware attacks and our own adaptive search against our own detectors, on our own pilot
# samples, to evaluate defenses. Nothing is deployed.
#
# For each of the eight toolkit attacks h (a fold):
#   1. PV: features never lowered by the other seven attacks (run 78's perturbation vectors on the pilot malware) are
#      kept, monotone; the rest are dropped. Trained as PV-seen was (run 81: the 10% store, the re-encoded groups
#      dropped); then h attacks the fold's model on the pilot malware it detects (a1_evaluate, low budget, the 1% FPR
#      threshold, re-extracted ground truth: the toolkit protocol of every other cell).
#   2. ERDALT: trained as in run 128 from the other seven attacks' vectors (the pilot ones and run 122's training-malware
#      ones, which exist for padding, gamma_sections, gamma_shift, content_shift only), two models at a time on two
#      GPUs; then h attacks the fold's model.
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
# Resources: (1) per fold ~2 min training (16 threads) + one attack on ~22 files (gamma_api ~100 s per file, the others
# ~15-35 s) at 16 workers: ~25-35 min for the eight folds. (2) ~26 min per model on one GPU (run 128), nine models on
# two GPUs: ~2.2 h. (3) the eight attacks ~5 min; the beam ~25 min. ~3.5 h in all.
# Smoke test (Claude, 2026-11-10, outputs in a scratch directory, machine at load ~45): (1) the gamma_api fold in full
#   at 8 workers: selection and training 2.5 min (test AUC 0.946; PV-seen 0.944), gamma_api 10 min; held-out 5/21
#   (24%; PV-seen 4/22), 2 more over the byte cap. (2) the padding fold at 3 epochs and 20,000 samples per split:
#   348 pilot + 1,197 training-malware vectors (exactly padding's removed); evaluation with one held-out attack
#   checked on run 128's model (4 files).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"
GPUS="${GPUS:-0 1}"  # two GPU ids, one training lane each

ATTACKS="gamma_sections gamma_api gamma_shift content_shift dos_extend header_fields padding format_exploit"
others() { local h=$1 a out=""; for a in $ATTACKS; do [[ $a != "$h" ]] && out="$out $a"; done; echo $out; }

P=artifacts/experiments/a_pv
D=artifacts/experiments/a_directions_sums
OUT=artifacts/experiments/a_loo
M=artifacts/models
F_PV=artifacts/features/ember2024-sums-10      # PV-seen's store (run 81)
F_ER=artifacts/features/ember2024-sums-10-v2   # ERDALT's store (run 128)
mkdir -p $P/loo $OUT artifacts/logs

echo "(1/4) PV, eight folds: selection, training, the held-out attack. Logs: artifacts/logs/*-pv-loo-<attack>.log"
for h in $ATTACKS; do
  seen=$(others $h)
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

echo "(2/4) ERDALT, nine models (eight folds, all eight) on GPUs $GPUS. Logs: artifacts/logs/train_erdalt-0-s10-loo-*.log"
train_erdalt() {  # gpu, suffix, attacks...
  local gpu=$1 suffix=$2; shift 2
  local log=artifacts/logs/train_erdalt-0-s10$suffix.log
  echo "  training erdalt/seed-0-s10$suffix on GPU $gpu. Log: $log"
  CUDA_VISIBLE_DEVICES=$gpu OMP_NUM_THREADS=8 python scripts/train_erdalt.py \
    --features $F_ER \
    --neutralize $D/reencoded.neutralize.txt \
    --deltas $P/deltas.parquet \
    --adv_dir artifacts/experiments/a1/advtrain/generated \
    --attacks "$@" \
    --suffix="$suffix" \
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
read -r GPU_A GPU_B <<< "$GPUS"
lane "$GPU_A" all8 gamma_sections gamma_api gamma_shift content_shift &
lane "$GPU_B" dos_extend header_fields padding format_exploit &
wait

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
