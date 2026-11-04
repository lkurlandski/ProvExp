#!/bin/bash
# Tier 2, item 9 (review R3a): a detector on the HAND direction table, attacked by the twelve-operation adaptive
# search (scripts/a1_adaptive.py), to test whether the hand table's in-population error is exploitable.
#
# The hand M_full detector (seed-0-a-mfull-mono-qf, run 77) and the derived M_full detector
# (seed-0-a-mfull-pre-qf-v2, run 105) are trained on the SAME full store (merged imports), the SAME samples, and the
# SAME monotone/neutralize counts (1305 / 1060); they differ in their training inputs by exactly TWO features:
#   section:overlay_size       hand: monotone +1 ("up")   | derived: neutralized (both -- add-section after the
#                                                            overlay removes it; G7 run 103)
#   datadirectories:security_size  hand: neutralized       | derived: monotone -1 ("down" -- removing the signature)
# So no retrain is needed: seed-0-a-mfull-mono-qf IS the hand counterpart of the derived model item 8 attacked
# (run 119, 0/41 under M_full). We re-run the identical twelve-op search against it.
#
# Hypothesis: the search, adding a section after the overlay, LOWERS the hand detector's score (impossible on the
# derived model, which saw min_delta_logit exactly 0.0) and evades it on >= 1 in-population file. The security_size
# difference cannot be exploited (neutralized = safe); the overlay_size "up" constraint is unsound because add-section
# absorbs the overlay, so overlay_size falls and the non-decreasing model's score drops.
# Go/no-go: at least one IN-POPULATION evasion. Otherwise: report the in-population difference as immaterial to the
# detector (honesty row).
#
# a1_adaptive.py is single-process (one greedy search per file), so NUM_WORKERS does not apply; set OMP threads.
# Estimate: run 119 attacked 3 defenses (112 detected files total) in ~17 min at queries 200 -> ~9 s/file; the hand
# model detects ~41 of the ~49 pilot malware -> ~6-7 min for the search, plus the labeling step (<1 min).
set -euo pipefail
cd "$(dirname "$0")/.."
source env/bin/activate
export PYTHONHASHSEED=0
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"

M=artifacts/models/gbdt
OUT=artifacts/experiments/a1/hand-table
LOG=artifacts/logs/a1_hand_table.log

echo "Item 9: the twelve-op adaptive search against the HAND M_full detector. Log: $LOG"
python scripts/a1_adaptive.py \
  --outdir "$OUT" \
  --features artifacts/features/ember2024 \
  --threat_model M_full \
  --defense mfull-mono-hand=$M/seed-0-a-mfull-mono-qf \
  --queries 200 \
  --seed 0 \
  &> "$LOG"
tail -4 "$LOG"

echo
echo "Labeling evasions by the plain-layout population (in-population vs out-of-population)."
python - "$OUT/adaptive.parquet" <<'PY'
import sys
import polars as pl
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.catalogue import passes_precondition
from provexp.data.simpledb import SimpleDB, SimpleDBReader
from provexp.data.paths import EMBER2024_DATA

df = pl.read_parquet(sys.argv[1])
extractor = merge_import_descriptors(PEFeatureExtractor())
reader = SimpleDBReader(SimpleDB(EMBER2024_DATA / "ts", check=False))

rows = []
for r in df.iter_rows(named=True):
    z = bytes(reader.get(r["name"]).data)
    rows.append({**r, "in_population": passes_precondition(extractor, z)})
out = pl.DataFrame(rows)

det = out.height
evaded = out.filter(pl.col("evaded"))
lowered = out.filter(pl.col("min_delta_logit") < -1e-6)
print(f"detected {det}; evaded {evaded.height}; score lowered (min_delta_logit<0) on {lowered.height}")
print(f"in-population detected {out.filter(pl.col('in_population')).height}; "
      f"in-population evaded {evaded.filter(pl.col('in_population')).height}; "
      f"out-of-population evaded {evaded.filter(~pl.col('in_population')).height}")
print("\nevaded files:")
if evaded.height:
    print(evaded.select(['name','in_population','p_clean','tau','min_delta_logit','queries','num_ops','ops',
                         'overrun_section','truncated']).to_dicts())
print("\nscore-lowered (whether or not evaded), op sequence and in_population:")
print(lowered.select(['name','in_population','evaded','min_delta_logit','ops']).to_dicts())
PY
