# PB1 Baselines Pilot: What It Tests and What Each Outcome Means

Written 2026-10-08, **before** the results, so that the reading is decided in advance. Read this first when the run
finishes. Context: `docs/pb1_pilot.md` (the pilot), `PLAN.md` (PB1, model scope).

## The run

Started by the user on 2026-10-08 (about 4.8 h wall-clock on 16 workers; the slowest, 4 MB file sets it):

    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/faithfulness.py --seed 0 --num_files 100 --num_workers 16 \
      --header typical --sweep_windows 64 1024 4096 --kernelshap_samples 2048 --timeout 28800 --tag baselines \
      --files artifacts/experiments/e1/seed-0/zeros-typical-header/files.parquet \
      &> artifacts/logs/faithfulness-seed0-zeros-typical-baselines.log

Output: `artifacts/experiments/e1/seed-0/zeros-typical-header-baselines/`. Tables:
`python scripts/pb1_tables.py --fill zeros-typical-header-baselines`.

GBDT only, level 3 (the primary operator), the same 100 files as the pilot. New methods next to the pilot's:

| method | what it is | cost (extractions per file) |
|---|---|---|
| `occlusion_k64`, `occlusion_k1024`, `occlusion_k4096` | occlusion with 64, 1,024, 4,096 windows | J + 2 |
| `pullback_k64:*`, `pullback_k1024:*`, `pullback_k4096:*` | the pullback coarsened to the same windows | 1 |
| `kernelshap_windows` | KernelSHAP over the 256 windows, 2,048 coalitions, reference: the fully ablated file | ≤ 2,050 |
| `pullback_abs:*` | the byte-level pullback ranked by magnitude, regardless of sign | 1 |

## Why

After the pilot, the main claim is **window-level parity with occlusion at 1/135 of the cost**, and the byte-level
advantage (1.65× occlusion's gain at level 3) is secondary. Three gaps remained:

1. The byte-level advantage was measured against occlusion at **one** coarse granularity (256 windows, about 800
   bytes each for the median file). A reviewer will ask whether finer occlusion closes the gap. The sweep gives the
   faithfulness-vs.-cost curve that `PLAN.md` promises.
2. Occlusion was the **only** direct problem-space baseline. KernelSHAP over windows is the obvious second one.
3. The pilot's **overshoot** (deleting the top 50% of bytes removes more evidence than deleting everything; median
   3.5 at level 3) has a proposed but untested reading: a signed ranking deletes the supporting bytes and keeps the
   opposing ones. The unsigned ranking tests it.

## First: is the run healthy?

- `report.json`: 0 failed files (look for `timeout` in `status`), 0 or very few invalid curve points, no `warning`.
- `files.parquet`: `invalid_windows_k{J}` and `kernelshap_windows_failed` near 0; `kernelshap_windows_extractions`
  near 2,050 (fewer means duplicate coalitions, which is fine).
- **Reproducibility:** every curve point shared with `zeros-typical-header/` (the pilot's methods) must match exactly,
  as in the smoke test. If not, stop and find out why before reading anything else.

## The questions and what each outcome means

"Gain" below is gain / occlusion gain at 256 windows, as in `docs/pb1_pilot.md`. "Matches" means within about 0.05 of
each other and a paired Wilcoxon test that is not significant (p > 0.05); 100 files are a pilot, so read differences
of a few hundredths as noise.

### Q1. Does occlusion approach the byte-level pullback as the windows shrink, and at what cost?

Read the cost-vs.-faithfulness table: occlusion at 64 → 256 → 1,024 → 4,096 windows against the byte-level pullback
(about 1.67) and the pullback at each window count.

- **Occlusion at 4,096 windows stays clearly below the byte-level pullback.** The secondary claim stands as is:
  occlusion cannot reach byte resolution even at 4,098 extractions, against one for the pullback. Report the curve.
- **Occlusion catches up at 1,024 or 4,096 windows.** The byte-level advantage is a granularity effect, not extra
  information. The claim becomes a cost claim: the pullback gives byte resolution for one extraction, occlusion needs
  about J of them to match. Report the cost at which occlusion matches.
- **Also check parity at every granularity** (the main claim): the pullback coarsened to J windows vs. occlusion at J.
  If they match at every J, the main claim holds independent of the window count (T3, coarsening). If occlusion pulls
  ahead at fine J, the main claim must name the granularity at which it holds, and we discuss why with the user.

### Q2. Does KernelSHAP over windows beat occlusion?

- **It matches or beats occlusion.** It is a second, stronger direct baseline; the main claim is then stated against
  the best direct baseline (compare `pullback_k:*` with `kernelshap_windows`), at about 2,050 vs. 1 extractions.
- **It is clearly worse than occlusion.** Likely too few coalitions (2,048 for 256 players, 8 per player; the smoke
  test's 512 gave 0.49 on 4 files). Report it as a weaker baseline at its cost; discuss with the user whether more
  coalitions are worth the compute before scaling. Do not tune it silently.

### Q3. Does the unsigned ranking remove the overshoot?

Read the overshoot table: `pullback_abs:*` vs. `pullback:*` (median overshoot and the share of files above 0.5).

- **The overshoot drops to about the level of occlusion or the window-level pullback** (pilot, level 3: about
  0.3–0.5). Accept the signed-resolution reading: the overshoot shows that the pullback separates supporting from
  opposing evidence, not that it exploits artifacts. State it as such in `docs/pb1_pilot.md` and the paper.
- **The overshoot stays high.** The reading is wrong. Do not claim it; find out which bytes drive it (the top-ranked
  bytes at 50% under level 3) and discuss with the user before going further.
- The unsigned ranking's deletion area will be lower than the signed one's; that is expected (it also deletes
  opposing evidence) and is not a result in itself.

## After the answers

1. Refresh `docs/pb1_pilot.md` (a "Baselines" section) and `docs/status.md`; record the decisions.
2. Decide with the user how PB1 at scale handles the baselines: 2,000 files, seeds 0–2, level 3 (level 2 on a
   subset). The 4,096-window sweep on all 2,000 files would cost about 1,400 worker-hours, so it likely runs on a
   subset (e.g., 200–300 files) chosen before looking at results; KernelSHAP over windows likewise.
3. Then CP and the planted trigger (PB2, PF2); the MLP returns after the GBDT methodology is established.

## Tie-break re-run (2026-10-09; `run/21_pb1_tiebreak.sh`): reading fixed in advance

**Why.** Rankings broke ties by position in the file. At 1,024 and 4,096 windows a median 62% and 89% of occlusion's
windows score exactly 0 (occluding them changes nothing), so every budget past the few positive windows deleted zero
windows from the start of the file onward: position, not evidence, decided much of occlusion's curve (at 4,096
windows, the budgets from about 6% up). The pullback rarely ties (position decided a median < 0.5% of its selection).
Now ties are broken by a seeded permutation (of bytes for byte-level rankings, of whole windows for window-level ones),
and scores within 1e-9 (relative) count as tied. On 6 files, the change moved occlusion's curve points by up to
1.57 log-odds and the pullback's by at most 0.13; with `--tiebreak position` the new code reproduces the old curves
exactly. Pass 1 is reused from run 17 (the occlusion and KernelSHAP scores themselves do not change).

**Reading, against `artifacts/reports/pb1_tables-baselines.md`** (gains relative to occlusion at 256 windows):
1. *The pullback's numbers* (byte-level 1.67, coarsened 0.89-1.22) should move by at most about 0.05. More would be
   a bug: find it before reading anything else.
2. *Occlusion's saturation.* **Stands** if occlusion at 4,096 windows stays within 0.05 of occlusion at 1,024 and
   the byte-level pullback stays ahead of the best direct baseline (occlusion at any window count or KernelSHAP over
   windows) on most files (p < 0.01). **Revised** if occlusion at 4,096 rises clearly above 1,024 (> 0.05): then the
   plateau was partly an artifact of positional ties, and PB1 states "occlusion improves with resolution but stays
   below the byte-level pullback at 4,096 extractions per file" if the gap remains, or reports parity if it closes.
3. *Parity at equal granularity* (64, 256, 1,024 windows) and the lead at 4,096: re-read with the new numbers; a
   change of conclusion at any window count is reported as such.
4. *The overshoot*: re-read; the unsigned-ranking reading stands if it still removes most of the byte-level overshoot.
Any change in PB1's conclusions goes to `docs/pb1_pilot.md`, `PLAN.md`, and the manuscript (PB1 baselines).
