# Status

Last updated: 2026-10-09 (end of session). The evaluation mirrors the framework (`PLAN.md`, "Experiment IDs"):
1. characterizing P (CP), 2. the pullback (PB1, PB2), 3. the pushforward (PF1, PF2), 4. comparing classifiers (CM);
appendix App-L (localizability) and App-R (redundancy). Work stays at pilot scale (100 files, one seed) until the
pilot results and the claims are settled (user, 2026-10-09). `run/` holds the commands that produced everything in
`artifacts/`.

## Where we are

| | state |
|---|---|
| **CP** (characterizing P) | **done**: census at 2,000 files, coarsening and CP.3 at pilot scale (`docs/cp_census.md`). |
| **PB1** (pullback faithfulness and cost) | done at pilot scale (`docs/pb1_pilot.md`), but **its curves are being re-run with random tie-breaks** (`run/21`): occlusion's numbers at 1,024–4,096 windows and its saturation at 1.10 are provisional. |
| **PB2, PF2** (planted trigger) | **done at pilot scale** (`docs/trigger_plan.md`). Struct: the 6 top-ranked bytes are the trigger's on 50/50 files. Content: precision 0.94 in the typical file, failing exactly where P says. PF2 reads r as a support. |
| **PF1** (pushforward faithfulness) | **done at pilot scale** (`docs/pf1_plan.md`). Required test passes; R = 0.31–0.40 for window-level sources; the resolution trend rises monotonically from 0.34 (64 windows) to 0.80 (bytes) as P's overlap falls, supporting claim 3 as reworded (option A). |
| **CM** (GBDT vs. MalConv) | designed, not built; next after PB1's re-read (the user decides when). |
| **App-L, App-R** | App-L done (`docs/appendix.md`); App-R's duplicate-feature sweep not run. |
| **The MLP** | set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | `_d_applications.tex` documents the theory, designs, and pilot results (updated 2026-10-09). Polishing is low priority until the full experiments exist (user). Do not try to compile it. |

## Waiting on the user: run 21 (`run/21_pb1_tiebreak.sh`, tmux, ~15–25 min on 32 workers)

**What it is for.** PB1's rankings broke ties by position in the file. At 1,024 and 4,096 windows a median 62% and 89%
of occlusion's windows score exactly 0, so position, not evidence, decided much of occlusion's deletion curves. The
fix (seeded random tie-breaks: of bytes for byte-level rankings, of whole windows for window-level ones; near-ties
within 1e-9 count as tied) is in `ablation.element_order` / `window_order` and `faithfulness.py --tiebreak random`.
Run 21 recomputes PB1's curves, reusing pass 1 (the per-window scores) from run 17.

**Checks:** the log (`artifacts/logs/faithfulness-seed0-zeros-typical-baselines-ties.log`) ends with "Wrote ..." and a
summary with 100 `ok`, "reused" for pass 1, and 0 invalid curve points; the tables are in
`artifacts/reports/pb1_tables-baselines-ties.md`, to compare with `artifacts/reports/pb1_tables-baselines.md` (the
same run before the fix, regenerated 2026-10-09; it reproduces the numbers in `docs/pb1_pilot.md`).

**Reading fixed in advance** (`docs/pb1_baselines.md`, "Tie-break re-run"): (1) the pullback's numbers move by at most
about 0.05, else a bug; (2) occlusion's saturation stands if 4,096 windows stay within 0.05 of 1,024 and the
byte-level pullback stays ahead of the best direct baseline (p < 0.01), else it is revised; (3) parity at equal
granularity re-read; (4) the overshoot re-read. Then update `docs/pb1_pilot.md` (remove the "pending" note),
`PLAN.md` (PB1), and the manuscript (PB1 baselines paragraph and its "Pending" box).

**Verified before the run:** with `--tiebreak position`, the reuse path reproduces run 17's curves exactly (6 files,
1,740 points, max difference 0). With random tie-breaks, occlusion's curve points moved by up to 1.57 log-odds, the
pullback's by at most 0.13.

## Next (for Claude), on resume

1. Read run 21 against the reading above and update the docs.
2. Take stock with the user: are the four claims and the contributions now supported at pilot scale (PLAN.md,
   "Thesis and claims", "Contributions", "Open questions")? Then CM: MalConv explanations of the pilot files
   (`explain/problem.py` has IG and occlusion), when the user decides.

## The 2026-10-09 session

- PB2/PF2 at pilot scale (50 files per trigger). Corrected a mislabeled "ceiling" (it was the round trip P ψ(1_T); the
  true bound is 1).
- PF1 designed, built, and run, with the resolution diagnostic and the resolution trend; claim 3 reworded (option A).
  Found and fixed round-off near-ties deciding PF1's rankings.
- CP.3 (instrumented vs. black-box statistics).
- A review of the stage (framework, claims, experiments): one correctness issue (PB1's positional tie-breaks, fixed,
  re-run pending) and several framing points, now in `PLAN.md` ("Open questions") and the docs.
- Docs streamlined: `docs/archive/` (Phase 2 plan and census), `docs/appendix.md` (App-L, App-R), condensed trigger
  and PF1 docs; `CLAUDE.md` updated (doc list, the tie-break rule, readings fixed in advance, `run/` script style).

## Decisions

2026-10-09:
- **Claim 3, option A:** the pushforward is faithful up to its source's resolution, a limit set by P's overlap; PF2
  carries "useful". TreeSHAP's window round trip counts only through its trend across resolutions.
- **PF1 design** (`docs/pf1_plan.md`): two references, the attributable-only check, the naive incidence sum, the
  criterion fixed in advance (above random and naive; R bands 0.8 / 0.5). No pushforward of triggered files.
- **PF2 reads r = ψ(1_T) as a support, not a target** (mass and top-k in supp(r)).
- **PF1's per-file reading dropped** (overlap at a fixed window count is mostly file size).
- **Rankings break ties by a seeded permutation**, never by position or index.
- **No scaling** until the pilot results and the claims are settled; manuscript polish is low priority.

2026-10-08:
- Evaluation structure and IDs (CP, PB1–2, PF1–2, CM; App-L, App-R). Pilot scale for most of the research.
- CP: ambiguity = entropy with effective support, overlap = 1 − M_jj, round-trip bounds, coarsening proposition.
- PB1: level 3 primary (level 2 robustness); main claim window-level parity, byte-level advantage secondary.
- The GBDT first; the MLP set aside temporarily.
- Trigger testbed: both triggers, dirty-label trigger → benign at 1%, long files overwritten, backdoor-fired filter.

2026-10-07:
- Framework domain-agnostic; experiments may use domain knowledge selectively (CLAUDE.md). No PE-structure analyses.
- Ambiguity and overlap *characterize P*; they were never meant to predict faithfulness.
- Localizability ℓ removed from the framework (an evaluation metric only); coverage κ kept. Ambiguity and overlap
  exclude unattributable features under the null policy.
- GBDT treats categorical features as numeric (shap misencodes LightGBM categorical splits).
- PB1 operator: level 2 = protect layout fields plus per-file breakers, zero the rest; level 3 = header fields take
  typical values; every ablated file verified. Insertion dropped. K = 256 windows.
- KernelSHAP: 32,768 samples, a 16-sample balanced background, `l1_reg=False`.

## Known issues and anomalies

- Interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11; suspected shap deep-tree bug; trees
  reach depth 37); PB1 excludes those files.
- 2 of 2,000 census files differ from the feature store in 2 `pefilewarnings` features (thrember's hash-seed bug).
- `pefilewarnings` features have no provenance (pefile does not say which bytes caused a warning); the top one carries
  about 5% of the GBDT's attribution.
- Occlusion cannot see zero or protected header bytes and creates fill artifacts (new entropy windows, pefile
  warnings); most of its windows at fine resolution change nothing (score exactly 0).
- One test file differs from the released features in all byte-entropy features (max diff 1.7e-4); not explained.

## Notes

- Untruncated files match the released EMBER features except `strings:entropy` (float32 round-off) and a rare,
  hash-seed-dependent pefile-warning choice (thrember bug). 13–16% of files are truncated.
- TLSH dedup at threshold 30 removed only ~6% of the first 32,765 test files; `data/tlsh.py` dedup is exact.
- The released JSONL lists some samples twice; `build_metadata.py` drops duplicates.
- Model test ROC-AUC (seed 0/1/2): GBDT 0.99759/0.99764/0.99763; MLP 0.99586/0.99551/0.99595.
- The machine: 2 sockets x 16 cores, hyperthreaded (64 logical CPUs), about 500 GB of memory.
