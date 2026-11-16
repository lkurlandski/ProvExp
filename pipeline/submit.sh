#!/bin/bash
# Submits the whole scale-up (pipeline/README.md's order) as SLURM jobs chained by dependencies: a job starts only after
# every job it reads from has finished without error (afterok; with --kill-on-invalid-dep, a failure cancels everything
# downstream instead of leaving it pending). Run on the cluster's head node, from the repository root:
#
#     bash pipeline/submit.sh
#
# The setup is assumed done (SETUP.md; pipeline/setup/check.sh passed; the lists and the file store built). The
# feature stores: if 2-features/{sums,expert} are not finished, the chain waits for a running `featurize` job (or
# submits one). Every step skips what is already done, so after a crash: fix it, then rerun this script (finished
# work is skipped by each step; a step still running must be cancelled first, or left out with SKIP).
# The gate (3-directions/gate) stops every detector, attack and result if the derived tables' check is not clean
# (session 70's rule): read the check with the user, decide, then rerun this script.
# Knobs: SKIP (steps to leave out, e.g. SKIP="1-audit/item-checks 4-detectors/price-list"), DRY=1 (print, submit
# nothing). The job IDs are written to logs/submit-<date>.txt.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT_ROOT="${OUT_ROOT:-artifacts/scaleup}"
SKIP="${SKIP:-}"
DRY="${DRY:-0}"
mkdir -p logs
RECORD=logs/submit-$(date +%Y%m%d-%H%M%S).txt

if ! command -v sbatch &> /dev/null; then echo "No sbatch here: run this on the cluster." >&2; exit 1; fi

submit() {  # step, then "deps" (space-separated job IDs, may be empty), then sbatch's extra arguments; prints the ID
  local step=$1 deps=$2 id; shift 2
  if [[ " $SKIP " == *" $step "* ]]; then echo "  (skipped: $step)" >&2; echo ""; return; fi
  local args=(--parsable --kill-on-invalid-dep=yes)
  deps=$(echo "$deps" | xargs)
  if [[ -n $deps ]]; then args+=("--dependency=afterok:${deps// /:}"); fi
  if [[ $DRY == 1 ]]; then
    id="[$step${DETECTORS:+:${DETECTORS// /,}}]"  # the dry run's stand-in for a job ID
  else
    id=$(sbatch "${args[@]}" "$@" "pipeline/$step/run.sh" | cut -d";" -f1)
  fi
  echo "$id  $step  ${*}  after: ${deps:-none}" | tee -a "$RECORD" >&2
  echo "$id"
}

echo "Submitting the scale-up (record: $RECORD)."

# 2. The feature stores: done, running, or submitted now.
F=""
if [[ ! -f $OUT_ROOT/2-features/sums/manifest.json || ! -f $OUT_ROOT/2-features/expert/manifest.json ]]; then
  F=$(squeue -h -u "$USER" -n featurize -o %i | head -1)
  if [[ -n $F ]]; then
    echo "$F  2-features/featurize  (already running)" | tee -a "$RECORD"
  else
    F=$(EXTRACTORS="sums expert" submit 2-features/featurize "")
  fi
fi

# 3 and 1. The direction tables, their gate, and the extractor audits (none reads the feature stores).
D=$(submit 3-directions/derived "")
G=$(submit 3-directions/gate "$D")
P=$(submit 1-audit/population "")
I=$(submit 1-audit/item-checks "")
E=$(submit 1-audit/escapes "$P")
V=$(submit 1-audit/deviations "$P")
C=$(submit 1-audit/catalogue-checks "$D")
H=$(submit 1-audit/hand-table "$P $C")
T=$(submit 3-directions/trial "$C")

# 4. The detectors. The trial detector trains apart, so that the material does not wait for the trial table.
TR=$(DETECTORS="unconstrained monotone-features monotone-sums additions-only expert-set" \
  submit 4-detectors/train "$F $G")
TT=$(DETECTORS="trial" submit 4-detectors/train "$TR $T $G" --job-name=train-trial)
AT=$(submit 4-detectors/adversarial-training "$TR")
L=$(submit 4-detectors/learned "$AT")
IT=$(submit 4-detectors/iterated "$L")
PL=$(submit 4-detectors/price-list "$TR")

# 5. The attacks, on every detector.
DETS="$TR $TT $L $IT"
K=$(submit 5-attacks/toolkit "$DETS")
A=$(submit 5-attacks/adaptive "$DETS")
M=$(submit 5-attacks/mab-malware "$DETS")

# 6. The tables.
R=$(submit 6-results "$K $A $M $PL $I $E $V $H")

echo "Submitted. Watch with: squeue -u $USER   (a failed job's log: logs/<name>_<id>.out)"
