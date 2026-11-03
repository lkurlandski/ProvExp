#!/bin/bash
# Tier 2, item 11 (review R3c, R8): the C4 derivation, the adaptive cell, and the M_full hole witnesses for the
# expert-set row (scripts/a_expert_directions.py, scripts/a_expert_adaptive.py; docs/direction-A-expert-set.md). The
# expert set (Gimenez et al.'s 40 features) is now instrumented (provexp.featuresets.ember2024.expert: items() +
# readouts, G1 bit-exact), so the generic C4 engine reads it like the EMBER extractor and marks eleven of its forty
# features as lowerable under M_full (rows 27 and 30-39): modified_dos_stub (rewrite the DOS stub) and the ten
# section-name features (rename a section). The go/no-go check is built into a_expert_directions.py (holes == the
# reasoned 11). The adaptive/witness step:
#   witnesses   for each derived hole, one of our own byte edits that lowers the feature (re-extracted);
#   adaptive    a greedy search with those two operations (rename, DOS-stub rewrite) against the run-106 monotone expert
#               model, scored by re-extracting the expert features (the extractor is cheap, and C1 is exact, so this
#               gives the same scores as the prediction-scored search of the other Table 7 rows; every evasion
#               re-extracts by construction, as the search materializes the edits with our own loader-safe writers).
# FOR ACADEMIC SECURITY RESEARCH ONLY: our own search against our own detector, on our own pilot malware (as runs 100, 106).
#
# Hypothesis: the search evades the monotone expert model on at least one of the 8 pilot malware it detects (the holes
# are real and reachable); each of the 11 holes is witnessed by a lowering edit on the pilot malware.
#
# Single-process (no worker pool): NUM_WORKERS does not apply; OMP is pinned to keep it light. Runs in ~2 min on the
# pilot, well under the 10-minute self-run bound.
#
# Ran 2026-11-03 (Claude, pilot). Result: tau 0.7688; detected 8/50; EVADED 2/8 (both via rename; p just over tau to
# just under). Witnesses: 11 of 11 holes lowered by one of our own edits on the pilot malware (modified_dos_stub 1->0
# by the DOS rewrite; the ten section-name features to 0 by renaming). The go/no-go (>=1 in-population evasion) is met:
# the "certifiably robust by design" expert set is evaded under M_full via the derived rename hole. Report: the expert
# row's adaptive cell is M_add-sound (0; rename and DOS rewrite are not additions); the 2/8 is M_full, in the prose.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=2

F=artifacts/features/ember2024-expert-10
M=artifacts/models/gbdt/seed-0-s10-expert-mono
E=artifacts/experiments/a1/expert-adaptive

echo "Item 11, step 1: the C4 derivation and the go/no-go (11 holes = rows 27, 30-39)"
python scripts/a_expert_directions.py

echo "Item 11, step 2: the expert-set adaptive cell and hole witnesses -> $E/expert_adaptive.json"
python scripts/a_expert_adaptive.py \
  --features "$F" \
  --model "$M" \
  --outdir "$E"

echo "Done. Adaptive cell and witnesses: $E/expert_adaptive.json"
