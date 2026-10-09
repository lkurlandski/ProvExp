# Status

Last updated: 2026-10-09 (PF1 and CP.3 results in; claim 3 to discuss). The evaluation mirrors the framework (`PLAN.md`, "Experiment IDs"):
1. characterizing P (CP), 2. the pullback (PB1, PB2), 3. the pushforward (PF1, PF2), 4. comparing classifiers (CM);
appendix App-L (localizability) and App-R (redundancy). Old IDs E1–E4 / A1–A3 survive only in pre-2026-10-08 docs and
in artifact paths (`artifacts/experiments/e1/` holds PB1). Work stays at pilot scale (~100 files, one seed).
`run/` holds the commands that produced everything in `artifacts/`; add a script there for every new experiment.

## Where we are

| | state |
|---|---|
| **CP** (characterizing P) | **done** at 2,000 files plus coarsening and CP.3 (instrumented vs. black-box statistics at 256 windows: ambiguity agrees where T1 says; overlap saturated at window level) (`docs/cp_census.md`). |
| **PB1** (pullback faithfulness and cost) | **done** at pilot scale, baselines included (`docs/pb1_pilot.md`). Gate 2 passed for the GBDT. |
| **PB2, PF2** (planted trigger) | **done at pilot scale** (50 files per trigger; `docs/trigger_plan.md`, "Pilot-scale results"). Struct: precision at \|T\| = 1 on 50/50 files. Content: 0.94 on the typical file, failing exactly where P says it must. PF2 reads r as a support (decided 2026-10-09; tables updated). |
| **PF1** (pushforward faithfulness) | **done at pilot scale, with the resolution trend** (`docs/pf1_plan.md`). Required test passes; R = 0.31–0.40 for window sources. R attainable rises monotonically 0.34 → 0.80 from 64 windows to bytes as P's overlap falls 0.99 → 0.41; bound holds everywhere. Supports claim 3 as reworded (option A). |
| **CM** (GBDT vs. MalConv) | designed, not built; MalConv explanations of the pilot files are not computed yet. |
| **The MLP** | set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | framework and evaluation sections follow the current structure; `_d_applications.tex` carries the designs and pilot numbers. Do not try to compile it (no LaTeX here). |

## The session's results

- **PB1 baselines** (6.1 h, healthy, the pilot's 13,000 shared curve points reproduced exactly). **Occlusion
  saturates at 1.10** and never approaches the byte-level pullback's 1.67 (80–81/100 files, p ≈ 1e-12); parity holds
  at 64, 256, and 1,024 windows and the pullback *leads* at 4,096; KernelSHAP over windows matches the best occlusion
  at 1,925 extractions; the **overshoot** is explained (unsigned ranking removes three quarters, the rest grows with
  resolution in every method family).
- **The trigger testbed.** The struct trigger (3 header fields, 6 bytes) passes everything: attack success 1.000,
  +16.7 log-odds, clean ROC unchanged, fires on all 1,000 explanation-set malware files. The content trigger reaches
  only 0.472, because **a content trigger's effect scales with its share of the file** (0.92 below 50 KB, 0.29 above
  1 MB) while the struct trigger is at 1.000 at every size.
- **PB2/PF2 first results** (6 files, struct): the **6 top-ranked bytes of 614,000 are exactly the trigger's**, for
  all three explainers (the "77% of the ceiling" read here was wrong: corrected 2026-10-09), while any window-level method is bounded analytically
  at 0.0027 precision. Every explainer's top feature of 2,568 is one the trigger touches.
- **The runner's parallelism was rebuilt** to split one file's work (a single file was 4.1 h of the 6.1 h run), giving
  about 1.1 h on 64 workers against 4.1 h before at any worker count. Verified bit-exact against the baselines run
  and pinned by `tests/test_faithfulness.py`, whose tests were themselves checked against two injected bugs.

## Run 20 (2026-10-09): done and verified

PF1 re-run with the tie fix (numbers moved ≤ 0.01 in R) and the resolution trend: R attainable rises monotonically
from 0.34 (64 windows) to 0.80 (bytes) as P's overlap falls from 0.99 to 0.41; CP's bound holds 2,400/2,400. The per-file
correlation of overlap and R (ρ −0.43 to −0.82) is mostly file size and fails the size check: dropped. Option A is supported
(`docs/pf1_plan.md`, "Results (run 20)").

## Run 17 (2026-10-09): done and verified

`run/17_pf1_window_scores.sh` finished in 138 min on 32 workers: 100/100 files ok, curves equal to the baselines run
exactly, window scores complete, x equal to the feature store. CP.3 (`run/19`) and PF1 (`run/18`) ran on it (by the
user); results in `docs/cp_census.md` and `docs/pf1_plan.md`.

## Next (for Claude), on resume

1. ~~Read the pilot-scale PB2/PF2 results~~ done 2026-10-09 (`docs/trigger_plan.md`), and the follow-ups in
   `trigger_tables.py` (round trip renamed, true bound added, PF2 under the support reading) are done and re-run.
2. **PF1** (the pushforward's faithfulness): the one experiment with no evidence yet, and claim 3 rests on it. Design
   it with the user first — designed 2026-10-09 (`docs/pf1_plan.md`). `faithfulness.py` now writes
   `window_scores.npz` (per-window occlusion at every window count, KernelSHAP over windows, x and the fully ablated
   file's features; `load_window_scores`). Next: check the user's `run/17_pf1_window_scores.sh` run (its curves
   should equal the baselines run's exactly), then build the PF1 script (success criterion fixed: `docs/pf1_plan.md`, decision 5).
3. **CP's black-box comparison:** `scripts/cp_blackbox.py` built (2026-10-09); runs on run 17's `provenance.npz`
   (`run/19_cp_blackbox.sh`). Expectation from T1: ambiguity agrees where the columns agree; overlap need not, since
   it depends on the other features through D.
4. **CM**, which needs MalConv explanations of the pilot files first.

## Decisions made on 2026-10-09

- **Claim 3, option A:** the pushforward is faithful up to its source's resolution, a limit predicted by P's overlap;
  PF2 carries "useful". The TreeSHAP window round trip counts only through its trend across window counts.

- **No scaling yet** (user): experiments stay on the pilot subset until the preliminary results are solid and the
  claims and contributions are clear. CM is close but not next.

- **PF1 design** as in `docs/pf1_plan.md` (two references, attributable-only variant, naive incidence-sum baseline,
  success criterion fixed in advance: beat random and the naive baseline, then R = area ratio to TreeSHAP with cut-offs 0.8 / 0.5). No pushforward of triggered files.
- **PF2 reads r = ψ(1_T) as a support, not a target:** mass on supp(r) and top-k in supp(r); cosine and Spearman
  against r dropped as faithfulness scores (manuscript, PLAN, `docs/trigger_plan.md`).

## Decisions made on 2026-10-08

- **Evaluation structure and IDs** as above (user's proposal; CM promoted from the appendix; localizability to the
  appendix, forward-referenced from the pullback section).
- **Pilot scale:** 80–90% of the research on the ~100-file pilot subset (one seed) before scaling; PB1 at scale is
  paused.
- **CP:** ambiguity = entropy with effective support, overlap = 1 − M_jj, round-trip bounds, coarsening proposition
  (all in the manuscript); the spectrum is for our own insight; resolution after the baselines.
- **PB1:** level 3 primary (level 2 robustness); main claim window-level parity, byte-level advantage secondary;
  baselines pilot (occlusion sweep, KernelSHAP over windows, unsigned ranking) before PB1 at scale.
- **The GBDT is the first classifier we experiment with.** The framework stays general-purpose (P does not depend on
  the classifier). Setting the MLP aside is temporary: it returns once the GBDT methodology is established, starting
  from the pilot's diagnosis (`PLAN.md`, "Model scope" and "Second classifier: the MLP").

## Decisions made on 2026-10-07 (see `PLAN.md` and the docs named)

- **Framework domain-agnostic; experiments may use domain knowledge selectively** (CLAUDE.md). Do not propose
  PE-structure analyses.
- **Plan (superseded 2026-10-08):** three claims + a measurement; core experiments E1–E4, appendix A1–A3.
  Manipulability dropped.
- **Statistics:** ambiguity and overlap *characterize P* (how sharply and separately an explanation can be placed);
  they were never meant to predict faithfulness. (The saturating definitions were replaced on 2026-10-08; see above.)
- **Localizability ℓ removed from the framework** (explanation-specific); coverage κ kept. ℓ stays an evaluation helper
  (`Provenance.localizability`).
- **Ambiguity/overlap exclude unattributable features** under the null policy (code and manuscript).
- **GBDT treats categorical features as numeric** (shap misencodes LightGBM categorical splits); ROC-AUC unchanged.
- **PB1 operator:** level 2 = protect the layout fields (`LAYOUT_FIELDS`) plus fields that break each file (per-file
  sweep), zero everything else, header bytes never random; level 3 = header fields take typical values
  (`header_typical_values.json`). Every ablated file is verified at runtime. **Insertion dropped** (blank file far from
  real files; scattered bytes do not rebuild structures; explanations use another reference). K = 256 windows.
- **KernelSHAP:** 32,768 samples, a 16-sample balanced background, `l1_reg=False` (shap's default keeps ~10 features).

## Known issues and anomalies

- Interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11; suspected shap deep-tree bug; trees
  reach depth 37); `treeshap_interventional` warns; PB1 excludes those files.
- 2 of 2,000 census files differ from the feature store in 2 `pefilewarnings` features (thrember's hash-seed bug).
- Black-box vs. instrumented P agree exactly for additive feature groups and differ for non-additive ones (strings,
  entropy windows, hashed imports/exports; total variation 0.44–0.67). Occlusion cannot see zero or protected header
  bytes and creates fill artifacts (new entropy windows, pefile warnings).
- `pefilewarnings` features have no provenance (pefile does not say which bytes caused a warning); the top one carries
  about 5% of the GBDT's attribution.

## Documents

- `PLAN.md`: plan, claims, experiments, timeline, gates, open questions.
- `docs/pilot.md`: census (Gate 1). `docs/pb1_plan.md` and `docs/pb1_pilot.md`: PB1 design and results (Gate 2).
- `docs/related_work.md`, `docs/design_provexp.md`, `docs/plan_phase2.md` (Phase 2, complete).
- Scripts: `explain.py` (stage-1 and KernelSHAP), `provenance_census.py`, `pullback_agreement.py`, `pilot_tables.py`,
  `discover_protected_fields.py`, `header_typical_values.py`, `faithfulness.py`, `pb1_tables.py`.

## Notes

- Untruncated files match the released EMBER features except `strings:entropy` (float32 round-off) and a rare,
  hash-seed-dependent pefile-warning choice (thrember bug). 13–16% of files are truncated.
- TLSH dedup at threshold 30 removed only ~6% of the first 32,765 test files.
- The released JSONL lists some samples twice; `build_metadata.py` drops duplicates.
- `data/tlsh.py` dedup is exact for any threshold.
- One test file differs from the released features in all byte-entropy features (max diff 1.7e-4); not yet explained.
- Model test ROC-AUC (seed 0/1/2): GBDT 0.99759/0.99764/0.99763; MLP 0.99586/0.99551/0.99595.
