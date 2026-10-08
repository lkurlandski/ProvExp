# Status

Last updated: 2026-10-08 (end of session). The evaluation mirrors the framework (`PLAN.md`, "Experiment IDs"):
1. characterizing P (CP), 2. the pullback (PB1, PB2), 3. the pushforward (PF1, PF2), 4. comparing classifiers (CM);
appendix App-L (localizability) and App-R (redundancy). Old IDs E1–E4 / A1–A3 survive only in pre-2026-10-08 docs and
in artifact paths (`artifacts/experiments/e1/` holds PB1). Work stays at pilot scale (~100 files, one seed).
`run/` holds the commands that produced everything in `artifacts/`; add a script there for every new experiment.

## Where we are

| | state |
|---|---|
| **CP** (characterizing P) | **done** at 2,000 files (`docs/cp_census.md`) plus coarsening on the pilot files. Remaining: instrumented vs. black-box P at window level, which `faithfulness.py` now saves. |
| **PB1** (pullback faithfulness and cost) | **done** at pilot scale, baselines included (`docs/pb1_pilot.md`). Gate 2 passed for the GBDT. |
| **PB2, PF2** (planted trigger) | **built, first results on 6 files** (`docs/trigger_plan.md`). A pilot-scale run on both triggers was started by the user at the end of the session (`run/16_trigger_pb2_pf2.sh`). |
| **PF1** (pushforward faithfulness) | designed, not built (`PLAN.md`, section 3). |
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
  all three explainers, at about 77% of the ceiling P permits, while any window-level method is bounded analytically
  at 0.0027 precision. Every explainer's top feature of 2,568 is one the trigger touches.
- **The runner's parallelism was rebuilt** to split one file's work (a single file was 4.1 h of the 6.1 h run), giving
  about 1.1 h on 64 workers against 4.1 h before at any worker count. Verified bit-exact against the baselines run
  and pinned by `tests/test_faithfulness.py`, whose tests were themselves checked against two injected bugs.

## Next (for Claude), on resume

1. **Read the pilot-scale PB2/PF2 results** the user started at the end of the session: the tables are in
   `artifacts/logs/trigger_tables-{struct,content-marker}.log`, the metrics in
   `artifacts/experiments/trigger/*/metrics-delta.parquet`. Compare the struct trigger against the 6-file numbers in
   `docs/trigger_plan.md`, and read the content trigger as the diffuse end of the provenance spectrum (its ceiling
   and window bounds will be very different: thousands of trigger bytes rather than 6). Write both into
   `docs/trigger_plan.md` and update `docs/status.md`.
2. **PF1** (the pushforward's faithfulness): the one experiment with no evidence yet, and claim 3 rests on it. Design
   it with the user first — the open question is the feature-space reference value for a deleted feature.
3. **CP's black-box comparison** (cheap: the window-level statistics of both provenances are already saved by any new
   `faithfulness.py` run).
4. **CM**, which needs MalConv explanations of the pilot files first.

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
