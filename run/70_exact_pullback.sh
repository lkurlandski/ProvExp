#!/bin/bash
# Appendix C, "Checking the Exact Pullback" (implementation plan Phase 4.3): verify Proposition Exact Pullback in the
# setting it covers. A logistic regression over EMBER's additive features is pulled back through P and compared, byte
# by byte, with the closed-form pipeline Shapley value (the raw contributions times beta). The two should agree to
# numerical precision on every file. Single process, low priority, no GPU; safe to run beside other jobs.
# Hypothesis: max difference <= 1e-9 over the whole explanation set (the proposition holds and the construction
# implements it). A nonzero difference would point to a normalization/baseline/item-to-byte bug.
#
# Smoke-tested on 8 files (max diff 3.5e-13). The whole explanation set (2,000 files) is single-threaded; ~20-30 min.
# NOTE: this is Appendix C's first paragraph only. The data-flow cost (second paragraph) needs a per-feature Shapley
# sampler for the non-additive features and is not implemented yet (docs/plan-2026-10-19.md, Phase 4).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0

LOG=artifacts/logs/exact-pullback.log
echo "Exact-pullback check: whole explanation set, single process (~20-30 min). Log: $LOG"
OMP_NUM_THREADS=2 nice -n 10 python scripts/exact_pullback_check.py \
  --num_files 0 \
  --train_sample 50000 \
  &> "$LOG"

echo "Done. Verdict and errors:"; tail -n 20 "$LOG"
