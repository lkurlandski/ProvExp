#!/bin/bash
# Table 7's adaptive column, PV rows (session 14): the two greedy menus of runs 108/119 against the 10%-store PV models
# (from all 8 attacks and from the 4 seen), so that their adaptive cells can be the union of all three searches like
# the other rows' (greedy append+add-section, greedy twelve-operation, run 127's beam). Run 127's beam alone evades the
# full-store PV on 14/22, while run 108's append+add-section greedy evades 16/22 of them, 6 of them files the beam
# misses: the beam's twelve-operation menu dilutes the section-name candidates PV's hole needs.
# FOR ACADEMIC SECURITY RESEARCH ONLY: our own adaptive search against our own detectors, on our own pilot samples.
#
# Hypothesis: as on the full-store PV, the append+add-section greedy evades most of the 22 (~16), and the union with
# the beam reaches ~18-20/22 for both PV models: PV from all 8 attacks does not close the hole.
#
# Resources: 22 files per model, 200 candidates per file; ~5 min per menu at 8 workers.
# Ran 2026-11-04 (Claude, NUM_WORKERS=8, 10 min). Hypothesis FAILED: on the 10%-store PV models the greedy menus evade
# fewer files than on the full-store PV and add nothing to the beam: pv-all twelve 12, appsec 10, beam 14, union 14/22
# (64%); pv-seen twelve 12, appsec 11, beam 15, union 15/22 (68%). The full-store PV's 16/22 under append+add-section
# does not carry over to the 10% models (fewer trusted section-hash buckets to aim at, presumably; not checked).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
NUM_WORKERS="${NUM_WORKERS:-16}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/a1/adaptive-greedy-pv-s10
LOG=artifacts/logs/a1_adaptive_greedy_pv_s10.log

greedy() {  # outdir, then extra arguments
  local out=$1; shift
  python scripts/a1_adaptive.py \
    --outdir "$OUT/$out" \
    --features artifacts/features/ember2024-sums-10-v2 \
    --threat_model M_full \
    --defense pv-all=$M/seed-0-s10-pv-all \
    --defense pv-seen=$M/seed-0-s10-pv-seen \
    --queries 200 \
    --seed 0 \
    --num_workers "$NUM_WORKERS" \
    "$@" \
    &>> "$LOG"
  tail -4 "$LOG"
}

: > "$LOG"
echo "(1/2) Greedy, twelve-operation menu (run 119's). Log: $LOG"
greedy twelve
echo "(2/2) Greedy, append+add-section menu (run 108's). Log: $LOG"
greedy appsec \
  --operations app sec

echo "Union with run 127's beam (a file counts as evaded if any search evades it):"
python - "$OUT" <<'PY'
import sys
import polars as pl
out = sys.argv[1]
runs = {"twelve": f"{out}/twelve/adaptive.parquet", "appsec": f"{out}/appsec/adaptive.parquet",
        "beam": "artifacts/experiments/a1/adaptive-beam/pv-s10/adaptive.parquet"}
for d in ("pv-all", "pv-seen"):
    sets = {k: set(pl.read_parquet(p).filter((pl.col("defense") == d) & pl.col("evaded"))["name"]) for k, p in runs.items()}
    n = pl.read_parquet(runs["beam"]).filter(pl.col("defense") == d).height
    union = set().union(*sets.values())
    print(f"  {d}: detected {n}; " + ", ".join(f"{k} {len(v)}" for k, v in sets.items()) + f"; union {len(union)}/{n}")
PY
