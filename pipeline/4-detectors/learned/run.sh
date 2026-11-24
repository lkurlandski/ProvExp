#!/bin/bash
#SBATCH --account=admalware
#SBATCH --partition=tigris
#SBATCH --constraint=gg
#SBATCH --job-name=learned
#SBATCH --output=./logs/%x_%j.out
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=36
#SBATCH --time=0-01:00:00
#SBATCH --mem=160G
#
# The defenses learned from the toolkit attacks' outputs (§5.3, Table 4; Appendix D, Table 10), every one from the same
# material (4-detectors/adversarial-training, merged here first) and on the full training split's complete files:
#   adversarial-training   the unconstrained detector retrained with every valid output appended (label 1)
#   pv                     Gimenez et al.'s PV: the features some output lowered dropped (selected among EMBER's
#                          features, the re-encoding's sums dropped as for unconstrained), the rest monotone increasing
#   erdalt                 Gimenez et al.'s ERDALT from the outputs' perturbation vectors, on a GPU, rescaled to keep
#                          their method's effect on our data (session 94; docs/erdalt-diagnosis-plan.md; Appendix D).
#                          Theirs: 24,000 training files at batch 16 (~1,500 steps per epoch), 310 epochs (~465,000
#                          steps), 1,033 vectors, std scale. Ours: 1.76M files at batch 256 (~6,900 steps per epoch),
#                          ~78,700 vectors (fewer in a fold). Rescaled: the schedule to their number of steps (68
#                          epochs, per step); w2 x 1,033 / our vectors (the penalty sums over every vector, so it weighs
#                          per step what theirs did); the criterion < 5 violated entries x our vectors / 1,033 (the
#                          same rate per vector, < 381 for all of them); the learning rate's patience 20 epochs ->
#                          4 (~30,000 steps, theirs); the input scale max(std, 0.9999 quantile of |x - mean|) per
#                          feature, since their std, fitted on 24,000 files, lets a few of our 1.76M heavy-tailed
#                          files dominate the monotone network (still linear per feature: Proposition 3 holds).
#   pv-loo-<a>, erdalt-loo-<a>   the leave-one-out folds: PV and ERDALT learned without attack <a>'s outputs (Table 10)
# PV's selection (pv_hole.py) also reports its hole against the derived table (M_full, features), weighted by the
# unconstrained detector's gain; 6-results reads it for §5.3.
# Two parts (PART: gbdt, erdalt, or both, the default), submitted as separate jobs because they need different machines:
#   gbdt     the GBDTs on the CPU, one at a time with every core (the header: a CPU node, 36 cores; ~25 min measured)
#   erdalt   one ERDALT model per visible GPU (CUDA_VISIBLE_DEVICES; unset: all), each a single process that keeps one
#            core busy feeding its GPU and loads the store (peak ~96 GB, ~35 GiB while training; ~6.7 h on a GH200)
# As a job array, task i trains only the i-th ERDALT model (erdalt, then the eight erdalt-loo-<a>). pipeline/submit.sh
# submits the gbdt part at the header's size and the erdalt part as an array of 9 on GPU nodes with 2 cores each.
# Whichever job arrives first merges the material, under a lock. A model whose predictions exist is skipped.
# Inputs: 4-detectors/material/shards (4-detectors/adversarial-training), 4-detectors/unconstrained (4-detectors/train),
# 2-features/sums, 3-directions/loose.
# Output: $OUT_ROOT/4-detectors/<name>/ (the registry's names); PV's selections in 4-detectors/pv-selection/.
# Knobs: PART (gbdt, erdalt, or all; default all), DEFENSES (default "adversarial-training pv erdalt loo"), SHARDS (the material's, default 10), EPOCHS (ERDALT,
# default 68), LIMIT (files per split; smoke tests).
# Two clusters training the same ERDALT models (session 111; tigris forward, sporc reverse, the first to start a model
# trains it), knobs for the erdalt part:
#   ORDER=reverse   array task i trains the (N-1-i)-th model instead of the i-th
#   CLAIMS=<dir>    on the shared file system: a task trains a model only if it takes its claim (mkdir <dir>/<name>,
#                   atomic; the owner's cluster, job and time inside), and skips a model claimed elsewhere. A claim
#                   stays after a failure: remove it to train that model again.
#                   When a task ends and every ERDALT model is complete (vl_predictions.parquet, written last), it
#                   releases the held jobs listed in <dir>/release and cancels the still-pending tasks of the arrays in
#                   <dir>/cancel (one "<cluster> <job id>" per line; scontrol/scancel -M), which would only skip.
#   ERDALT_SCRIPT   the trainer (default pipeline/4-detectors/train/train_erdalt.py; a stand-in for smoke tests)
# A model that fails makes the job exit 1 (after the rest has run), so a failure shows in sacct. Cost (scale-up, sessions 78 and 94): ERDALT ~10 min loading and
# ~5.7 min per epoch on a GH200, ~6.7 h per model at 68 epochs, nine of them in parallel; the ten GBDTs ~25 min in all.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/../../..}"
source pipeline/common.sh

PART="${PART:-all}"
DEFENSES="${DEFENSES:-adversarial-training pv erdalt loo}"
case $PART in all | gbdt | erdalt) ;; *) echo "Unknown PART $PART (gbdt erdalt all)." >&2; exit 1 ;; esac
SHARDS="${SHARDS:-10}"
EPOCHS="${EPOCHS:-68}"
ATTACKS="gamma_sections gamma_api gamma_shift content_shift dos_extend header_fields padding format_exploit"
SUMS=$OUT_ROOT/2-features/sums
DIR=$OUT_ROOT/3-directions/loose
OUT=$OUT_ROOT/4-detectors
MAT=$OUT/material
SEL=$OUT/pv-selection
mkdir -p "$OUT/logs" "$SEL"
LIMIT_ARG=()
if [[ -n "${LIMIT:-}" ]]; then LIMIT_ARG=(--limit "$LIMIT"); fi
others() { local h=$1 a out=""; for a in $ATTACKS; do [[ $a != "$h" ]] && out="$out $a"; done; echo $out; }
wants() { [[ " $DEFENSES " == *" $1 "* ]]; }

TASK="${SLURM_ARRAY_TASK_ID:-}"  # empty: every model in this job
ORDER="${ORDER:-forward}"
case $ORDER in forward | reverse) ;; *) echo "Unknown ORDER $ORDER (forward reverse)." >&2; exit 1 ;; esac
CLAIMS="${CLAIMS:-}"
ERDALT_SCRIPT="${ERDALT_SCRIPT:-pipeline/4-detectors/train/train_erdalt.py}"

mkdir -p "$MAT"
exec 9> "$MAT/.merge.lock"
flock 9  # array tasks: one merges, the others wait for it and then find the merge done
if [[ ! -f $MAT/sums/X.npy ]]; then
  echo "Merging the material's $SHARDS shards. Log: $OUT/logs/material-merge.log"
  python pipeline/4-detectors/adversarial-training/attack_training.py \
    --outdir "$MAT" \
    --merge \
    --num_shards "$SHARDS" \
    &> "$OUT/logs/material-merge.log"
  tail -1 "$OUT/logs/material-merge.log"
fi
flock -u 9

# ERDALT, in the background: one lane per visible GPU, the jobs dealt round-robin.
ERDALT_JOBS=()
GBDT_DEFENSES=$DEFENSES
if [[ $PART == gbdt ]]; then DEFENSES=""; fi
if [[ $PART == erdalt ]]; then GBDT_DEFENSES=""; fi
if wants erdalt; then ERDALT_JOBS+=("erdalt:$ATTACKS"); fi
if wants loo; then for h in $ATTACKS; do ERDALT_JOBS+=("erdalt-loo-$h:$(others "$h")"); done; fi
ALL_ERDALT=("${ERDALT_JOBS[@]}")
if [[ -n $TASK ]]; then  # an array task: its one model, if any
  if [[ $ORDER == reverse ]]; then TASK=$((${#ERDALT_JOBS[@]} - 1 - TASK)); fi
  if [[ $TASK -ge 0 && $TASK -lt ${#ERDALT_JOBS[@]} ]]; then ERDALT_JOBS=("${ERDALT_JOBS[$TASK]}"); else ERDALT_JOBS=(); fi
fi
if [[ -n "${CUDA_VISIBLE_DEVICES+set}" ]]; then
  IFS=", " read -r -a GPU_IDS <<< "$CUDA_VISIBLE_DEVICES"
else
  mapfile -t GPU_IDS < <(nvidia-smi --query-gpu=index --format=csv,noheader 2> /dev/null || true)
fi
claim() {  # model name; succeeds if this job now owns the model (always, without CLAIMS)
  [[ -z $CLAIMS ]] && return 0
  mkdir -p "$CLAIMS"
  if mkdir "$CLAIMS/$1" 2> /dev/null; then
    echo "${SLURM_CLUSTER_NAME:-$(hostname)} ${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-none}}_${SLURM_ARRAY_TASK_ID:-} ($ORDER) $(hostname) $(date -Is)" \
      > "$CLAIMS/$1/owner"
    return 0
  fi
  sleep 2  # the owner writes its file right after the mkdir
  echo "  $1 claimed by $(cat "$CLAIMS/$1/owner" 2> /dev/null || echo "an unknown job"); skipping."
  return 1
}
erdalt_lane() {  # lane index; trains every lane-th job on its GPU; fails if one of them failed
  local lane=$1 i job name attacks log failed=0
  for ((i = lane; i < ${#ERDALT_JOBS[@]}; i += ${#GPU_IDS[@]})); do
    job=${ERDALT_JOBS[$i]}; name=${job%%:*}; attacks=${job#*:}
    log=$OUT/logs/train-$name.log
    if [[ -f $OUT/$name/ts_predictions.parquet ]]; then echo "  $name exists; skipping."; continue; fi
    claim "$name" || continue
    echo "  $name on GPU ${GPU_IDS[$lane]}. Log: $log"
    # shellcheck disable=SC2086
    CUDA_VISIBLE_DEVICES=${GPU_IDS[$lane]} python "$ERDALT_SCRIPT" \
      --features "$SUMS" \
      --neutralize "$DIR/reencoded.neutralize.txt" \
      --adv_dir "$MAT/sums" \
      --adv_features "$SUMS" \
      --attacks $attacks \
      --model_dir "$OUT/$name" \
      --complete_only \
      --epochs "$EPOCHS" \
      --schedule_per_step \
      --input_scale quantile \
      --reference_vectors 1033 \
      --scale_criterion \
      --lr_patience 4 \
      --batch_size 256 \
      --seed 0 \
      "${LIMIT_ARG[@]}" \
      &> "$log" || { echo "  $name FAILED; see $log"; failed=1; }
  done
  return $failed
}
LANES=()
if [[ ${#ERDALT_JOBS[@]} -gt 0 ]]; then
  if [[ ${#GPU_IDS[@]} -lt 1 ]]; then echo "No visible GPU for ERDALT (CUDA_VISIBLE_DEVICES)." >&2; exit 1; fi
  echo "ERDALT: ${#ERDALT_JOBS[@]} models on GPUs ${GPU_IDS[*]}, in the background."
  for ((lane = 0; lane < ${#GPU_IDS[@]}; lane++)); do
    OMP_NUM_THREADS=2 erdalt_lane "$lane" &
    LANES+=($!)
  done
fi

gbdt() {  # name, then train_classic's arguments
  local name=$1; shift
  local log=$OUT/logs/train-$name.log
  if [[ -f $OUT/$name/model.txt ]]; then echo "  $name exists; skipping."; return; fi
  echo "  Training $name. Log: $log"
  python pipeline/4-detectors/train/train_classic.py \
    --learner gbdt \
    --seed 0 \
    --complete_only \
    --features "$SUMS" \
    --model_dir "$OUT/$name" \
    --num_threads "$NUM_WORKERS" \
    "${LIMIT_ARG[@]}" \
    "$@" \
    &> "$log"
}

pv() {  # name, tag, attacks...
  local name=$1 tag=$2; shift 2
  if [[ ! -f $SEL/pv$tag.monotone.tsv ]]; then
    echo "  PV selection$tag from the outputs of $*. Log: $OUT/logs/pv-selection$tag.log"
    python pipeline/6-results/pv_hole.py \
      --adv_dir "$MAT/sums" \
      --adv_features "$SUMS" \
      --exclude "$DIR/reencoded.neutralize.txt" \
      --attacks "$@" \
      --directions_dir "$DIR" \
      --variant pre-control \
      --model "$OUT/unconstrained/model.txt" \
      --tag="$tag" \
      --outdir "$SEL" \
      &> "$OUT/logs/pv-selection$tag.log"
    cat "$SEL/pv$tag.neutralize.txt" "$DIR/reencoded.neutralize.txt" > "$SEL/pv$tag-sums.neutralize.txt"
  fi
  gbdt "$name" \
    --neutralize "$SEL/pv$tag-sums.neutralize.txt" \
    --monotone "$SEL/pv$tag.monotone.tsv"
}

DEFENSES=$GBDT_DEFENSES
if [[ -n $DEFENSES ]]; then echo "GBDTs on the CPU, $NUM_WORKERS threads."; fi
if wants adversarial-training; then
  gbdt adversarial-training \
    --neutralize "$DIR/reencoded.neutralize.txt" \
    --augment "$MAT/sums"
fi
# shellcheck disable=SC2086
if wants pv; then pv pv "" $ATTACKS; fi
if wants loo; then
  # shellcheck disable=SC2046
  for h in $ATTACKS; do pv "pv-loo-$h" "-loo-$h" $(others "$h"); done
fi

ERDALT_FAILED=0
if [[ ${#LANES[@]} -gt 0 ]]; then
  echo "Waiting for the ERDALT lanes."
  for pid in "${LANES[@]}"; do wait "$pid" || ERDALT_FAILED=1; done
fi
if [[ -n $CLAIMS && $ERDALT_FAILED == 0 ]]; then  # the last model done: release the dependents, drop the leftovers
  missing=0
  for job in "${ALL_ERDALT[@]}"; do [[ -f $OUT/${job%%:*}/vl_predictions.parquet ]] || missing=$((missing + 1)); done
  if [[ $missing -gt 0 ]]; then
    echo "ERDALT: $missing of ${#ALL_ERDALT[@]} models not complete yet; nothing to release."
  else
    echo "ERDALT: all ${#ALL_ERDALT[@]} models complete."
    if [[ -f $CLAIMS/release ]]; then
      while read -r cluster id || [[ -n ${cluster:-} ]]; do
        [[ -z ${id:-} ]] && continue
        echo "  Releasing $id on $cluster."
        scontrol -M "$cluster" release "$id" || echo "  (release of $id on $cluster failed; released already?)"
      done < "$CLAIMS/release"
    fi
    if [[ -f $CLAIMS/cancel ]]; then
      while read -r cluster id || [[ -n ${cluster:-} ]]; do
        [[ -z ${id:-} ]] && continue
        echo "  Cancelling the pending tasks of $id on $cluster."
        scancel -M "$cluster" --state=PENDING "$id" || echo "  (scancel of $id on $cluster failed)"
      done < "$CLAIMS/cancel"
    fi
  fi
fi
if [[ $ERDALT_FAILED != 0 ]]; then
  echo "ERDALT: a model FAILED (above); exiting 1." >&2
  exit 1
fi
echo "Done. Models: $OUT/<name>/; PV's selections and holes: $SEL/"
