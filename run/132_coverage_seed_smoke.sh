#!/bin/bash
# §5.3, Phases 0 and 1 of docs/evidence/section-5.3-design.md. FOR ACADEMIC SECURITY RESEARCH ONLY: stored outputs of published
# secml-malware attacks against our own undefended detector, and one more run of one of them on our own training
# malware, to measure what observed attacks reveal. Nothing is deployed.
#
#   1. a_coverage.py (Phase 0, option O1): of the 1,070 features the derived table (M_full, precondition, quirk-fixed)
#      marks lowerable, which some toolkit output lowered (run 78's pilot vectors; runs 122 and 131 step 0 on 400
#      training malware), split by whether a toolkit operation can lower them; which of them our own edits lowered
#      (catalogue_checks, 2000-exact); PV's hole by the same split.
#   2. a_advtrain.py --seed_per_file (Phase 1 smoke): GAMMA section injection on 100 training malware with a seed per
#      (attack, file) instead of seed 0 for every run (the harness's default, after Gimenez et al.).
#
# Hypotheses (2026-11-11): (1) the gap is mostly not operations the toolkit lacks; what our edits lower and the toolkit
# never does is mostly section-name buckets. (2) With a seed per file, section injection lowers >= 45 of the 50
# section-size buckets in union (fixed seed: 13).
#
# Ran 2026-11-11 (Claude): step 1 2.2 min (16 workers for the population check), step 2 ~10 min at 16 workers.
# Results (artifacts/experiments/a_coverage/report.json):
#   (1) held. Only 2 of the 1,070 are lowerable only by operations the toolkit lacks (rename, removals, checksum,
#       slack, DOS stub); 88 are the parser warnings; 980 are lowerable by a toolkit operation. Toolkit coverage:
#       745 (pilot, 36 population files), 847 (training, 314 population files; growth 704/759/797/814 at 25/50/100/200
#       files). Our own edits lowered 915 of the 1,070; of those, 90 no toolkit output lowered (82 section-name, 4
#       header, 3 warnings, 1 string). gamma_sections lowers the same 13 size buckets on 314 training files as on 36
#       pilot files. PV-8's hole witnessed by our edits: 25.7% of gain, 22.3 points of it section-name buckets.
#   (2) held: 50/50 size, entropy and virtual-size buckets on 100 files (distinct sets 100); this one attack closes 71
#       of the 90-feature gap. Left: 8 entry-section-name buckets, 4 header fields, 1 string, 3 warnings, 3 others.
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
NUM_WORKERS="${NUM_WORKERS:-16}"
EMBER2024_DATA="${EMBER2024_DATA:-/shared/datasets/EMBER-2024/data}"
mkdir -p artifacts/logs

log=artifacts/logs/a_coverage.log
echo "(1/2) Coverage by source (~2 min). Log: $log"
OMP_NUM_THREADS=2 python scripts/a_coverage.py \
  --outdir artifacts/experiments/a_coverage \
  --db "$EMBER2024_DATA/tr" \
  --num_workers "$NUM_WORKERS" \
  &> "$log"
tail -3 "$log"

log=artifacts/logs/a_advtrain_smoke-seedperfile-gsec.log
echo "(2/2) GAMMA section injection, a seed per file, 100 training malware (~10 min). Log: $log"
OMP_NUM_THREADS=1 python scripts/a_advtrain.py \
  --outdir artifacts/experiments/a1/advtrain/smoke-seedperfile-gsec \
  --db "$EMBER2024_DATA/tr" \
  --attacks gamma_sections \
  --num_malware 100 \
  --num_goodware 50 \
  --num_workers "$NUM_WORKERS" \
  --seed 0 \
  --seed_per_file \
  &> "$log"
tail -2 "$log"
