# Implementation plan (2026-10-19)

> **Build status (2026-10-19).** WP0-WP5 and WP7 implemented, smoke-tested, lint + strict mypy clean; WP6 dropped. Run
> scripts: `run/64` (theory coverage, done), `run/65` (instrumentation cost, done), `run/66` (Sections 5.1/5.2 GBDT),
> `run/67` (5.2 MalConv window sources), `run/68` (6.1 attack transfer: selection + gate, then uncomment the full
> run), `run/69` (6.2 unfiltered audit). Nothing long has been run yet; the user launches 66-69 (GPU 3, <=16 workers).
> WP8 (figures, manuscript) comes after the results.

How to build what `docs/experiments/specs.md` (final, round 3) specifies. Work packages (WP) in dependency order; each
lists the code, a smoke test, the `run/` script it produces, its cost, and the hypothesis it tests. Constraints from
CLAUDE.md apply throughout: pilot scale (100 files, seed 0) unless stated, at most 16 workers and 2 GPUs, smoke-test on
a slice and hand the user the run script for anything over ~10-15 minutes, ties broken by seeded permutation, ruff and
strict mypy before each commit, code in the style of the existing modules.

## Order at a glance

| # | work package | where | needs | first run (est.) |
|---|---|---|---|---|
| WP0 | shared infrastructure: adaptive KernelSHAP, query counting | `src/provexp/ablation.py`, `scripts/faithfulness.py` | — | smoke only |
| WP1 | 5.1 rerun: four budgets, KernelSHAP and adaptive KernelSHAP at each | `scripts/faithfulness.py` | WP0 | ~4 h CPU |
| WP2 | 5.2 on the GBDT under byte deletion (same run as WP1) | `scripts/faithfulness.py` | WP0 | in WP1 |
| WP3 | 5.2 on MalConv: window sources, byte deletion | `scripts/pf_malconv.py` | WP0 | ~1 h GPU |
| WP4 | 6.1 Part A: the attack and its feasibility gate | new module + `scripts/cm_attack.py` | — | ~15 min GPU (gate) |
| WP5 | 6.1 Part A: the full experiment | `scripts/cm_attack.py`, `scripts/cm_transfer.py` | WP4 gate, WP1 | ~2 h |
| ~~WP6~~ | ~~6.1 Part B: adjudication~~ (dropped) | — | — | — |
| WP7 | 6.2: unfiltered audit, section names, 0.1% FPR | `scripts/audit_*` | — | ~3 h |
| WP8 | figures and manuscript | `scripts/paper_figures.py`, `manuscript/` | results | — |
| later | KernelSHAP at 4,096; retraining MalConv; MalConv seeds 1-2; scale-up | — | user decides | long |

WP1-WP3 (Section 5) go first: 6.1's baseline is "the best window method of 5.1". WP4's gate goes early in parallel
(GPU), because Part A carries the most risk. WP4-WP5 can use occlusion at 256 windows as the temporary window
baseline (user) until WP1 names the best one.

---

## WP0. Shared infrastructure

1. **Adaptive KernelSHAP over windows** (`kernelshap_partition` next to `kernelshap_windows` in
   `scripts/faithfulness.py`, or in `provexp.ablation` if WP3 also needs it, which it does: put it in the library and
   keep it domain-agnostic).
   - Players: L leaf windows (equal windows of the file; L = 16,384, finer than the largest budget, so adaptivity has
     room). Hierarchy: a balanced binary tree over contiguous leaves, written as a scipy linkage matrix. Masker:
     `shap.maskers.Partition` over a background of zeros (player absent = ablated) with that clustering; the model
     function maps a 0/1 player mask to the scorer, as `kernelshap_windows` does. Budget: `max_evals` matched to
     occlusion's queries at each budget (66 / 258 / 1,026 / 4,098). Seeded (`np.random.seed` around the call, since
     the queue breaks ties with `np.random.randn()`).
   - Output: one value per leaf, spread evenly over the leaf's bytes, as the other window methods.
   - Smoke: 2 small files; check that values sum to f(x) − f(ablated) (Owen efficiency), that it stops at
     `max_evals`, and the query count. Unit test in
     `tests/test_ablation.py` on a toy additive scorer, where Owen values are exact.
   - Risk: `shap.maskers.Partition` may insist on its own data handling for tabular inputs; fallback is a minimal
     custom `shap.maskers.Masker` subclass with a `clustering` attribute. Settle in the smoke test.
2. **Query and time accounting.** Every method records its detector queries per file (extractions for the GBDT;
   forward/backward passes for MalConv) and wall-clock seconds in `files.parquet`, under one column naming scheme, so
   5.1, 5.2, and 6.1 report the same cost unit.
3. **No other library change.** The pullback, pushforward, coarsening, and deletion operator already exist.

## WP1. Section 5.1 rerun (`scripts/faithfulness.py`)

- **Changes.** `--kernelshap_windows 64 256 1024 [4096]` runs KernelSHAP at each budget with `8K + 2` coalitions
  (today it runs only at `--num_windows`); `--partition_budgets 64 256 1024 4096` runs WP0's adaptive KernelSHAP at
  matched query budgets. Reuse pass 1 (`--reuse_scores`) for the occlusion sweep already computed in run 21/56, so
  occlusion is not recomputed. The field oracle and the black-box estimate stay as code but are not run or reported.
- **Run.** `run/66_pb1_shared.sh`: 100 pilot files, seed 0, level-3 operator, zeros fill, budgets 64/256/1,024 for
  KernelSHAP (4,096 deferred: ~32,800 queries per file, ~8-10 h), all four for adaptive KernelSHAP. Then the random-fill
  variant (`run/67_pb1_shared_random.sh`), deletion only. Estimated ~4 h for the first at 16 workers (KernelSHAP at
  1,024 dominates: 8,194 queries per file).
- **Hypothesis.** Adaptive KernelSHAP improves on uniform windows at equal queries but stays below the byte-level
  pullback (occluding small windows changes the features too little to rank them, the saturation seen at 1,024
  windows).
- **Output used later.** The best window method (by evidence removed at 256-matched cost) becomes 6.1's baseline.

## WP2. Section 5.2 on the GBDT under byte deletion (same script, same run)

- **Change.** For each window explanation computed in WP1 (occlusion, KernelSHAP, adaptive KernelSHAP, at each
  budget), add the ranking P·ψ(b): push it forward through P coarsened to its windows, pull the result back to the
  bytes, and score it with the same deletion curve. Add TreeSHAP's resolution trend: TreeSHAP pulled back, summed over
  K windows, pushed forward, pulled back (K = 64 ... 4,096 and bytes). Random feature explanations, pulled back, as the
  floor. All in `faithfulness.py` pass 2, so every ranking shares files, operator, seeds, and cost accounting. The
  reference (TreeSHAP itself) is 5.1's byte-level pullback curve.
- **Cost.** About 13 deletion budgets per ranking, ~40 rankings: ~520 extra extractions per file, minutes per file.
- **Hypothesis.** The pushforward of a window explanation keeps more of the reference the finer its windows; the
  direct explainers sit close to TreeSHAP's own resolution trend (as under the old protocol).
- **Retire.** `scripts/pf1.py` and `scripts/pf1_resolution.py` (feature-space deletion) move to `scripts/archive/`
  once WP2 reproduces the trend; their runs stay documented in `docs/experiments/pf1.md`.

## WP3. Section 5.2 on MalConv (`scripts/pf_malconv.py`)

- **Changes.** Add problem-space sources besides IG: MalConv occlusion at the four budgets (exact, `malconv_occlusion`
  with `blocks` chosen per file so the window count matches the budget), KernelSHAP over windows and adaptive
  KernelSHAP (WP0) at the four budgets, MalConv queries batched on the GPU. Push each forward, pull back, delete bytes,
  MalConv scores (the existing protocol). Drop the naive translation. Record queries.
- **Run.** `run/68_pf_malconv_shared.sh`, 100 pilot files, one GPU; KernelSHAP at 1,024 on 4 MB inputs is the cost
  driver (~8,200 forward passes per file). Estimate after the smoke test.
- **Hypothesis.** The pushforward of IG stays on top among summaries into features; window sources pushed forward
  fall between it and random features, rising with resolution; the surrogate stays at about half of IG's pushforward.

## WP4. Section 6.1 Part A: the attack and its feasibility gate

- **Editable region** (`src/provexp/featuresets/ember2024/attack.py`, PE-aware experiment code like `ablation.py`):
  `editable_region(data) -> BoolArray` marks the DOS header from offset 2 up to `e_lfanew` (exclusive of offsets
  0x3C-0x3F), the DOS stub from 0x40 to the PE header (the Rich header included), and section slack
  (`[PointerToRawData + VirtualSize, PointerToRawData + SizeOfRawData)` where the virtual size is smaller), clipped to
  the 4,000,000-byte truncation. Tests in `tests/test_ember2024_attack.py` on the fixtures: region bounds, no overlap
  with headers or section data in use, and that a random rewrite of the region passes `verify` with an unchanged
  layout.
- **Attack** (`scripts/cm_attack.py`): white-box, on MalConv's byte embeddings. Each iteration takes the gradient of
  the malware log-odds with respect to the embeddings at editable positions and, for the m positions with the largest
  predicted decrease, replaces the byte with the value whose embedding most decreases the linearized log-odds (the
  embedding-gradient method with projection to the nearest byte). Budget: a fixed number of queries (N iterations),
  stopping early once MalConv falls below its 1% FPR threshold (user, 2026-10-19: the usual protocol). Seeded. Every adversarial file is verified and re-featurized; output: the
  adversarial bytes' positions C, MalConv's and the GBDT's log-odds before and after.
- **Defaults to settle in the smoke test:** m = 64 positions per iteration, N = 50 iterations (a few seconds per file
  on a GPU).
- **Feasibility gate (run before WP5; ~50 files, ~15 min on one GPU, `run/69_cm_attack_gate.sh`).** Report MalConv's
  evasion rate and the distribution of the GBDT's drop. **Go** if the GBDT's drop varies enough to predict: at least
  ~20% of files lose more than 1 log-odds (fixed now, before the run). **No-go:** fall back to option 1 (the
  controlled shared-reliance changes) and tell the user before building more.
- **Hypothesis for the gate.** MalConv is evaded on most files (DOS-header and slack attacks are known to work on
  MalConv); the GBDT moves on a minority, mostly files with a Rich header in the stub, which EMBER reads.

## WP5. Section 6.1 Part A: the full experiment

- **Population** (`scripts/cm_disagreement_select.py`, a new `--both_detect` mode): held-out test malware detected by
  both models at their 1% FPR thresholds, excluding the explanation set and the audit's files; 100 for the pilot.
- **Inputs on the original files.** TreeSHAP (interventional) via `scripts/explain.py --subset`; P from the
  instrumented extractor; the window baseline's evidence (occlusion at 256 windows until WP1 names the best method).
- **Analysis** (`scripts/cm_transfer.py`). Predictors per file: the GBDT's pullback evidence for malware summed over
  the editable region E (primary) and over the changed bytes C (diagnostic); the window method's evidence over the
  windows overlapping E; |C|. Outcome: the GBDT's drop. Spearman ρ; AUC for the drop above the fixed threshold;
  bootstrap CIs. Probabilities for the headline (share of files falling below the GBDT's threshold, median probability
  drop).
- **Run.** `run/70_cm_transfer.sh` (attack on the population, then the analysis). ~1-2 h with one GPU and 16 workers.
- **Reuse for 6.2.** The same attack with the audited fields zeroed before scoring (`--mitigated`) gives the stronger
  attacker on the mitigated MalConv, once the user decides it is in.

## WP6. Section 6.1 Part B: adjudication (DROPPED 2026-10-19 after the pilot pre-check; kept for the record)

- **Population** (`cm_disagreement_select.py`): GBDT-only disagreements on the held-out test split, 100 malware and
  100 benign, disjoint from the 25-per-cell pilot files.
- **Inputs.** MalConv IG (GPU), the GBDT's TreeSHAP pullback, triage shares (factor the share computation out of
  `scripts/cm_triage.py` into a function both scripts use), and the window-level triage from the baseline method.
- **Analysis** (`scripts/cm_adjudicate.py`). Logistic regression predicting "the GBDT is right", repeated stratified
  5-fold cross-validation: (i) the two detectors' log-odds, (ii) plus the blind and oppose shares (agree is the
  remainder), (iii) as (ii) from window-level triage. Metrics: AUC; the share of GBDT false positives removed at 99%
  recall of GBDT-only malware, with the threshold chosen on training folds and the outcome reweighted to the test
  split's base rate (29,267 : 1,547).
- **Run.** `run/71_cm_adjudicate.sh`. ~1 h (IG on 200 files; occlusion at 256 windows, 258 queries per file).
- **Hypothesis.** (ii) beats (i) and (iii): the oppose share marks GBDT detections MalConv argues against on the same
  content (pilot: malware), the blind share GBDT evidence MalConv does not see (pilot: false positives).

## WP7. Section 6.2

1. **Unfiltered discovery** (`scripts/audit_discover.py`, `scripts/audit_scramble.py`): `--max_content` set to no limit (a
   single contiguous run is no longer required) while `--max_runs 256` stays, so aggregates such as the byte histogram,
   whose content cannot be located, remain excluded; the confirmation control generalizes from "as many random bytes in the same
   convolution window" to one random byte in the same 512-byte window per assigned byte, which reduces to today's rule
   for contiguous fields. Group the confirmed features by type (header field, section, import, string, aggregate).
   `run/72_audit_unfiltered.sh`, reusing the IG of runs 39/43 (no GPU). Hypothesis: some section, import, or string
   features are confirmed, i.e., reliance the pushforward splits out of shared bytes.
2. **Section names in the rulebook** (`scripts/audit_evade.py`): renaming a section is loader-safe; add it, report the
   probability drop next to evasion. Part of run 70's follow-up, `run/73_audit_evade_sections.sh`.
3. **0.1% FPR** from existing scores (`audit_evade.py`, `audit_mitigate.py` table modes): no new run.
4. **Later, user decides:** retraining MalConv with the fields zeroed (GPU, outside this repository's training
   code); MalConv seeds 1-2 (IG on 2,000 files per seed, then discovery and evasion); the stronger attacker (WP5's
   `--mitigated`).

## WP8. Figures and manuscript

- `scripts/paper_figures.py`: Figure 3 with the four budgets and adaptive KernelSHAP, y-axis "Evidence removed
  (log-odds)"; Figure 4 as the pushforward's mirror of Figure 3 under byte deletion; Figure 5 with the window sources.
  Tables for 6.1 Parts A and B.
- Manuscript: Section 4 states the one measurement, the one cost unit, and the log-odds-to-probability conversion;
  Sections 5.1-5.2 rewritten on the new results; Section 6 gets the shared setting (Phase 3a of the plan) and the new
  6.1; 6.2 gains the unfiltered audit. The shared setting is writing only and can be done any time.

## Decisions (user, 2026-10-19)

1. Part A: test the prediction on the log-odds drop, report the headline in probabilities; settle the presentation once
   the results are in.
2. Attacks run for a fixed query budget and stop early at evasion.
3. Adaptive KernelSHAP: 16,384 leaf windows.
