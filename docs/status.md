# Status

Last updated: 2026-10-09 (run 21 read). The evaluation mirrors the framework (`PLAN.md`, "Experiment IDs"):
1. characterizing P (CP), 2. the pullback (PB1, PB2), 3. the pushforward (PF1, PF2), 4. comparing classifiers (CM);
appendix App-L (localizability) and App-R (redundancy). Work stays at pilot scale (100 files, one seed) until the
pilot results and the claims are settled (user, 2026-10-09). `run/` holds the commands that produced everything in
`artifacts/`.

## Where we are

| | state |
|---|---|
| **CP** (characterizing P) | **done**: census at 2,000 files, coarsening and CP.3 at pilot scale (`docs/cp_census.md`). |
| **PB1** (pullback faithfulness and cost) | **done at pilot scale** (`docs/pb1_pilot.md`). The tie-break re-run (`run/21`) changed no conclusion: occlusion saturates at about 1.10 (1.11 at 4,096 windows, p = 0.40 vs. 1,024), the byte-level pullback stays at 1.67 (79–85/100 files vs. every direct baseline, p ≤ 6e-12), parity at 64–1,024 windows, the pullback ahead at 4,096. |
| **PB2, PF2** (planted trigger) | **done at pilot scale** (`docs/trigger_plan.md`). Struct: the 6 top-ranked bytes are the trigger's on 50/50 files. Content: precision 0.94 in the typical file, failing exactly where P says. PF2 reads r as a support. |
| **PF1** (pushforward faithfulness) | **done at pilot scale** (`docs/pf1_plan.md`). Required test passes; R = 0.31–0.40 for window-level sources; the resolution trend rises monotonically from 0.34 (64 windows) to 0.80 (bytes) as P's overlap falls, supporting claim 3 as reworded (option A). |
| **CM** (GBDT vs. MalConv) | designed, not built; next after PB1's re-read (the user decides when). |
| **App-L, App-R** | App-L done (`docs/appendix.md`); App-R's duplicate-feature sweep not run. |
| **The MLP** | set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | `_d_applications.tex` documents the theory, designs, and pilot results (updated 2026-10-09). Polishing is low priority until the full experiments exist (user). Do not try to compile it. |

## Run 21 (PB1 tie-break re-run): read 2026-10-09

Clean (100 `ok`, pass 1 reused, 0 invalid curve points, 15 min). Read against the rule fixed in advance
(`docs/pb1_baselines.md`, "Tie-break re-run"): all four readings stand. Pullback moved ≤ 0.003; occlusion at 4,096
windows 1.101 → 1.105 (vs. 1.097 at 1,024); matched-K parity and the 4,096 lead unchanged (p = 0.008, was 0.004);
the unsigned ranking still removes most of the overshoot. Costs are now run 17's: KernelSHAP over windows counts
2,050 extractions (run 12's 1,925 shared a cache with occlusion), so "1/1,900 of the cost" became "1/2,000". Results
written to `docs/pb1_pilot.md`, `PLAN.md`, and the manuscript (the "Pending" box removed). The paired comparisons not
in `pb1_tables.py` (best direct baseline, matched K) were computed ad hoc; they reproduce the pre-fix doc exactly on
run 12.

## Next (for Claude), on resume

1. **Not CM yet** (user): the work is being rethought at a high level first. The paper's structure is now framework /
   intrinsic evaluation / extrinsic applications (`PLAN.md`, "Paper structure"). Open, to discuss with the user:
   the pushforward application (C) that complements B; why the pullback is the right tool for B and how B is made
   useful to practitioners; what to do with ambiguity and overlap (`PLAN.md`, "Open questions").
2. Small, agreed: move the paired tests PB1 now computes ad hoc (each method vs. the best direct baseline; pullback vs.
   occlusion at the same window count) into `scripts/pb1_tables.py`.
3. Rewrite the claims (`PLAN.md`, "Thesis and claims") to fit the new structure, once the extrinsic core is settled.

## The 2026-10-09 session

- Run 21 read: PB1's conclusions survive random tie-breaks (above).
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

2026-10-09 (second review, after run 21):
- **Paper structure:** framework / intrinsic evaluation (lab-style: PB1, PF1, CP's theory) / extrinsic applications
  (A = CM, B = byte-level discovery of what a detector keys on via the pullback, C = a pushforward application, to
  be found). Adding EMBER v2 as a second feature set is not worth it (too similar to v3).
- **Trigger experiments (PB2, PF2) demoted**, kept for now, possibly removed later.
- **Round-trip matrices M, N stay** as theory; ambiguity and overlap undecided; **coverage, localizability, and the
  null element's share are not contributions** (explanation-specific; a pipeline limitation, not a finding).
- **Theory:** an axiomatic (Shapley-style) uniqueness result noted in `PLAN.md` as a possible strengthening, not now.
- **Hypotheses before experiments, briefly** (not elaborate pre-registered readings; `CLAUDE.md`).

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
