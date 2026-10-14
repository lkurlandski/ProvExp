#!/bin/bash
# CM, triage tied to a decision (docs/experiments/cm.md, "Triage tied to a decision"; revision plan B9).
#
# Does the disagreement triage distinguish an attack-caused disagreement from an organic one? Two populations of
# GBDT-only-flagged malware, run through the same blind/oppose/agree split (A = GBDT, B = MalConv):
#   organic   malware the GBDT detects and MalConv misses on its own.
#   evasion   malware both detect, with the shared set S (the bytes both rely on) scrambled loader-safe, kept where
#             MalConv then falls to/below its 1%-FPR threshold while the GBDT holds.
# Hypothesis: the evasion population carries more of the GBDT's evidence in "oppose" (bytes both rely on that MalConv
# now reads the other way) than the organic one. If it does not, fall back to reframing the readout (docs/experiments/cm.md).
#
# Single process, one GPU. 200 candidate malware from the explanation set; IG recomputed per kept file at 256 steps.
# Ran on GPU 1 (per the user): 36.8 min, 32 organic and 87 evasion files. Result: no separation (oppose 0.26 vs. 0.28,
# p = 0.14); see docs/experiments/cm.md, "Result (run 57)".
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/cm-triage-evasion-seed0.log
echo "CM triage tied to a decision: organic vs. shared-reliance-evasion, 200 candidate malware, GPU 1 (~37 min)."
echo "Output: artifacts/experiments/cm_triage_evasion/seed-0/"
echo "Log:    $LOG   (follow with: tail -f $LOG)"
OMP_NUM_THREADS=1 python scripts/cm_triage_evasion.py \
  --seed 0 \
  --device cuda:1 \
  --num_files 200 \
  --ig_steps 256 \
  &> "$LOG"

echo "Done. The blind/oppose/agree table and the evasion-vs-organic p-values are at the end of $LOG."
echo "Read: does 'oppose' separate the two populations? If yes, the triage label is a defender's decision."
