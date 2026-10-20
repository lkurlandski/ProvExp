# Status

**2026-10-20: overnight runs read; WP8 done for Sections 5 and 6.2; 6.1 is a NO-GO, directions under discussion
(analysis in `docs/experiments/cm.md`, "Attack transfer").**
- **run/66 (5.1/5.2, GBDT):** clean. Adaptive KernelSHAP beats occlusion only at 4,096 queries (5.96 vs 5.51, 70/100);
  below it at 64/256 queries (3.42 vs 4.79; 4.46 vs 5.07), about even at 1,024 (5.37 vs 5.47). KernelSHAP over 1,024 windows is the strongest
  direct method (6.31 at 8,194 queries) and beats the pullback summed into the same windows; the byte-level pullback
  (8.03, one extraction) beats it on 72/100 and adaptive@4096 on 81/100. Pushforward relative to TreeSHAP's pullback:
  KernelSHAP 0.68/0.75/0.83 (64/256/1k), adaptive 0.61/0.65/0.70/0.76, occlusion flat ~0.65, trend 0.64/0.63/0.70/0.79,
  bytes 1.00. Hypothesis half held (below the pullback: yes; adaptive beats occlusion at equal queries: only at 4,096).
- **run/67 (5.2, MalConv):** clean; hypothesis held. Gradient-free sources beat the surrogate (occlusion@1k 4.23,
  71/100; KernelSHAP@1k 4.69, 83/100; vs 3.28); IG pushforward on top (6.25).
- **run/68 (6.1 attack transfer): NO-GO.** MalConv evaded 81%; the GBDT never crosses its threshold and *rises* on
  78% of files (median +1.06 log-odds); only 5/100 drop by >1 log-odds. Pullback on E ranks the signed change best
  (Spearman 0.34, p = 5e-4, vs occlusion 0.18, |C| -0.18), but the bootstrap CI of the difference with occlusion spans 0
  ([-0.09, 0.41]). 6.1's text and table are still placeholders: **the user decides** (fallback option 1, or another).
- **run/69 (6.2 unfiltered audit): done, hypothesis failed (neutral-to-favorable for the paper).** Two script fixes
  (IG symlink; `--direction malware`, which the first rerun lacked: discovery wrote only the benign direction, kept in
  `audit-discover-unfiltered-benign-seed0.log`). Unfiltered candidates add hashed section entropies, byte-entropy bins,
  the DOS-stub message; none confirmed. MalConv: 8 of the 9 Table 3 fields confirmed again (IAT drops out of the top
  20); surrogate: the same 9 as before. No section/import/string reliance. The run's preset gate reads "no-go" (b: 4 of 8
  confirmed shared with the surrogate, exactly half), only because IAT left the top 20. Manuscript: 6.2 keeps the
  filtered protocol (Table 3 and the evasion/mitigation rest on it) and states the unfiltered run as a robustness
  sentence; the blue sentence is gone.
- **Run 70 (Appendix C):** exact, max difference 8.5e-14 over 2,000 files; filled.
- **Manuscript (commit b2aea56):** Figures 3-5 regenerated under byte deletion (`scripts/paper_figures.py`, new
  `pf_gbdt.dat`; Figure 3 adds KernelSHAP@1k and adaptive@4096); every `\synthetic` in Section 5 and Appendix C
  replaced. Wording changed where results changed direction: "as faithful as direct explanation at the same resolution"
  narrowed to "as faithful as occlusion" (KernelSHAP beats both at matched windows); adaptive pays off only with a large
  budget; the TreeSHAP trend is no longer called a bound (KernelSHAP exceeds it). The introduction (line 42) already says
  "as faithful as occlusion". Remaining blue: 6.1 (Table and paragraph), 6.2 (audit sentence; retrained row, deferred),
  the discussion's Android sentence (deferred).

**2026-10-19: manuscript reorganized** (user). Sections 5-6 were one per operator (Pulling Back / Pushing Forward);
now **5 Evaluating the Transfers** (`_e_evaluation.tex`: 5.1 pullback faithfulness and cost, 5.2 pushforward
faithfulness, 5.3 the planted trigger, both directions in one subsection) and **6 Security Applications**
(`_f_applications.tex`: shared setting, 6.1 comparing two detectors file by file, 6.2 auditing MalConv, 6.3 the two
together). Reasons: the paper is a method plus two security applications; the pushforward's "trigger" never tested the
pushforward (W6); the applications already cross operators; the field-level baselines (REVIEW risks 1-2) have a natural
home. Labels `sec:XML:PullbackTrigger`/`PushforwardTrigger` merged into `sec:XML:Trigger`; new `sec:XML:Evaluation`,
`Applications`, `Together`. Text otherwise unchanged except seams (section openers/closers, duplicated motivation
trimmed, intro's "three questions" and contribution pointers). `REVIEW.md`'s file:line references point to the old
files (`_e_pullback.tex`, `_f_pushforward.tex`).

**Experiment code written (2026-10-19), not yet run at scale.** WP0-WP5, WP7 (implementation plan): adaptive
KernelSHAP (shap PartitionExplainer) and a sparse window pushforward in the library; faithfulness.py extended for the
shared-protocol 5.1/5.2 (KernelSHAP at every budget, adaptive KernelSHAP, feature rankings scored by byte deletion);
pf_malconv.py for MalConv's window sources; featuresets/ember2024/attack.py (loader-safe DOS/stub/slack attack) and
cm_transfer.py for 6.1 attack transfer; cm_disagreement_select.py --both_detect; audit unfiltered via existing scripts.
All smoke-tested on GPU 3, lint + strict mypy clean, new unit tests pass. **Run scripts run/66-69 ready for the user**
(GPU 3, <=16 workers); run/66 ~8 h, run/67 ~2-3 h, run/68 gate ~15 min, run/69 ~12 min. Committed up to this point.

**Low-hanging fruit done (2026-10-19; commits 94708bb, ca5dbdb, 80aa47e):** Influence axiom as "computed from",
classifier renamed f, overclaims trimmed, identifiability result kept as a Section 3 illustration; theory coverage
(67% additive / 9% data-flow / 23% null of TreeSHAP's attribution; run 64) and instrumentation cost (0.19 vs 0.05 s
median, 2.7 vs 0.4 s at 4 MB; run 65; "adds little" corrected); related work checked against sources. **Adjudication
pre-check: likely no-go** (scores alone AUC 0.91, + triage 0.90 on 50 pilot files); WP6 on hold, the 6.1 placeholder
paragraph stays until the user decides. Run numbers in the implementation plan now start at 66. Next: decision on Part
B, then WP0.

**Manuscript carries the new methodology (fd814be)** with blue placeholders for every new result. **REVIEW
reassessed** (`docs/review-reassessment-2026-10-19.md`): every WP answers a named review risk; low-hanging fruit listed
(axiom and notation fix, overclaims, additive-share and worst-case numbers, adjudication pre-check on pilot files,
stronger attacker on the mitigated MalConv, related work, Part A covariates); open decision: keep the identifiability
result as an illustration in Section 3.

**Implementation plan (2026-10-19):** `docs/implementation-plan-2026-10-19.md`, WP0-WP8 (adaptive KernelSHAP and
query accounting; 5.1/5.2 reruns in one faithfulness run; 5.2 on MalConv; the 6.1 attack with a feasibility gate;
adjudication; the unfiltered audit; figures). Part B rewording approved by the user. Next: WP0.

**Specs finalized, round 3 (2026-10-19, commit dcf7928):** 6.1 = option 3 (white-box MalConv attack on the DOS
header, DOS stub, and section slack; does the GBDT's pullback on that region predict its confidence drop?) + option 2
reworded as adjudication of GBDT-only disagreements (scores vs. scores + triage shares), pending the user's OK. Next:
implementation plan for the reruns (5.1, 5.2) and 6.1.

**Specs round 2 (2026-10-19, user feedback; commit 228e5d5):** cut from the manuscript: the black-box P (3.3.1, 5.1,
intro, discussion, open science), 5.3 the planted trigger (archived; struct trigger kept as a worked example in a new
appendix), the naive translation. Decided for the reruns: one byte-deletion measurement and one cost unit (detector
queries + seconds) for 5.1 and 5.2; budgets 64/256/1,024/4,096 for every window method; adaptive KernelSHAP =
shap's PartitionExplainer; 5.2 mirrors 5.1; log-odds in Section 5, probabilities in Section 6. Open: which 6.1
option(s) (attack transfer with white-box GAMMA preferred; design first, no code yet). See `docs/experiments/specs.md`.

**Phase 1 drafted (2026-10-19):** `docs/experiments/specs.md` (one spec per experiment, comparison class under rule
(a), mocks). Surfaced: adaptive occlusion is the missing in-class baseline for 5.1; the naive translation on MalConv for
5.2; run 57 argues against full joint evasion in 6.1; the unfiltered audit is required under (a). Next: the user
reviews the specs, then Phase 2 (baseline rule) and the 6.1 brainstorm.

**Phase 0 done (2026-10-19):** field-occlusion oracle removed from 5.1 and Figure 3 (5.1 now compares format-agnostic
methods only; run 56 stays in `docs/experiments/pb1.md`); 6.3 deleted (the feature-by-feature comparison of the two
detectors is dropped, a two-sentence close ends 6.2). 16 pages, clean build.

**Next: `docs/plan-2026-10-19.md`** (research plan from REVIEW.md + the user's comments): Phase 0 cleanups
(remove the field oracle from 5.1, delete 6.3; awaiting a yes), Phase 1 per-experiment claim specs, Phase 2 one
baseline rule for the paper (brainstorm), Phase 3 rebuild Section 6 (shared setting; find/confirm/realize/act for both
applications), then theory consistency, the Android decision, and the final round.

Last updated: 2026-10-16 (end of session). **Section 3 now carries real theory (answer to W1, thin novelty).** Today:
- **Brainstorm** of directions for W1 (in chat; outcome in `docs/theory.md`). Kept: (A) a Shapley-grounded construction
  of P and (B) the pushforward as an inverse problem. Dropped: a "theory of resolution" and axiomatic uniqueness.
  Parked as possible case studies: bounds on what control of a byte set can do; naming a raw-byte model's units.
- **Coarsening out of Section 3** (user: weak, distracting). Granularity/P^G moved to a new **Section 4, "Experimental
  Setup"** (`manuscript/_d_setup.tex`: EMBER instrumentation and Table 1, data/models/explainers, deletion operator,
  windows of bytes), an experimental device only; the experiments that use it are unchanged.
- **P stays nonnegative** (user), with a short "Why provenance is nonnegative" paragraph in 3.3.
- **Run 61, go/no-go for the iterated pushforward** (`scripts/pf_inverse.py`, `run/61_pf_inverse.sh`, user ran it):
  recovering TreeSHAP from its pullback, R rises 0.80 -> 0.86 at bytes (93/100 files, p = 7e-17) and 0.36 -> 0.44 at
  256 windows (84/100), for all three explainers. Below the "toward 1" hypothesis: the limit matches the byte
  explanation exactly (residual ~1e-9) but misses 37% of the feature explanation, i.e., non-identifiable features.
  **A qualified go:** the theory explains the gap; the algorithmic gain is reliable but modest.
- **Section 3 rewritten** (`_c_method.tex`): 3.3 items, Definition Shapley Provenance, Proposition Additive Features
  (instrumentation = Shapley provenance for features additive over their items: fields, counts, histograms over a
  fixed denominator, one-sign hashed counts), the data-flow convention for entropies/averages/ratios/min-max, why
  nonnegative, 3.3.1 the black-box estimate; 3.4 Proposition Exact Pullback (linear model -> exact problem-space
  Shapley values; G-DeepSHAP's linear-chain result for a program), Definition and Proposition Exact Pushforward
  (iteration converges, conserves, recovers everything the bytes determine; one step exact without shared elements).
  Key modeling choice: the game holds each feature's context fixed (parse, denominators). Build clean, 16 pages.

- **Later the same day:** Section 3 feedback applied (Shapley 1953 cited; new background subsection 2.3 "Shapley
  Values"; definitions and propositions numbered separately; the exact pullback's baseline stated; paragraph splits).
  **Run 62** (identifiability ceiling, twins oracle): R at bytes 0.80 / 0.86 / 0.95 (one step / exact / twins oracle),
  at 256 windows 0.36 / 0.44 / 0.86: what the exact pushforward misses lies mostly in features with identical
  provenance. **Run 63** (MalConv): exact = one step (median area 6.25 both), both 1.9x the surrogate.
  **Decided (user):** the experiments keep the one-step pushforward, nothing reruns; Section 3 keeps Definition 7 and
  Proposition 3 as theory (what any pushforward can recover); Section 6.1 reports the exact form and the twins result
  in two sentences (GBDT and MalConv). Details: `docs/theory.md`, "The ceiling and MalConv".

- **Front and back matter updated** for the theory: abstract (now 232 words: Shapley-grounded P, exact pullback, the
  pushforward as the pullback's inverse, the mitigation), introduction (a new paragraph on the theory; contributions),
  "Our Position", a discussion paragraph "Beyond the exact cases", and the conclusion. Light-touch: the structure and
  results of these sections are unchanged.

- **Section 4 restructured** (`_d_setup.tex`): 4.1 Provenance for EMBER (items per feature group, null element),
  4.2 Data, Detectors, and Explainers (the explainer settings moved here from 5.1), 4.3 Measuring Faithfulness by
  Deletion (operator + evidence-removed protocol + ties, moved from 5.1), 4.4 Windows of Bytes. 17 pages; one 2 pt
  overfull vbox on the last page (float reflow, harmless).

- **Pre-submission review (2026-10-16, read-only):** `REVIEW.md` in the repo root (simulated CCS review, claim audit,
  threat models, risk register, action plan, draft abstract/contributions/threat models). Top risks: no per-field
  IG baseline for the audit/MalConv test (the oracle's parser map already exists), byte vs. field resolution
  unablated (W4), triage without a security outcome; synthetic blue results must go before submission.

**Current goal:** the user reads the revised front/back matter and Section 4; then reassess W7 (Android); the scale-up
last.

**Waiting on the user:** the black-box P's final place (now 3.3.1, maybe an appendix later); whether to keep the GBDT
window-pushforward test (a lab study need not be realistic).

**Appendix C drafted (2026-10-19):** "Checking the Exact Pullback" (`manuscript/_j3_exact_pullback.tex`), the
exactness check for Proposition 2 (review W2), with synthetic predicted numbers; Proposition 2 now points to it. The
script `scripts/exact_pullback_check.py` is still to write (light CPU, no pipeline; `docs/plan-2026-10-19.md` Phase 4
item 3). Synthetic numbers to replace: median l1 2e-3, data-flow agreement 0.74.

## Overnight runs launched 2026-10-19 (results expected 2026-10-20 a.m.)

The user is running, in one tmux chain (GPU 3, 16 workers): `run/66_pb1_shared.sh` (5.1/5.2 GBDT, ~8 h) ;
`run/67_pf_malconv_shared.sh` (5.2 MalConv window sources, ~2-3 h) ; `run/68_cm_transfer.sh` (6.1 attack transfer +
its feasibility read, ~15-20 min) ; `run/69_audit_unfiltered.sh` (6.2 unfiltered audit, ~12 min). Outputs:

- `artifacts/experiments/e1/seed-0/zeros-typical-header-shared/` and `artifacts/reports/pb1_tables-shared.md` (66)
- `artifacts/experiments/pf_malconv/seed-0-shared/` (67; table at the end of its log)
- `artifacts/experiments/cm_transfer/seed-0/{files,report}.parquet|json` (68)
- `artifacts/experiments/audit_discover_unfiltered/`, `audit_scramble_unfiltered/` (69)
- Logs in `artifacts/logs/`.

## Next (this thread) — WP8, after the overnight runs

1. **Read the results** (see the resume prompt). First checks: 66's pushforward table (does adaptive KernelSHAP stay
   below the byte-level pullback? does the pushforward of window sources rise with resolution?); 68's summary
   (`gbdt_drop_over_1.0`, `malconv_evaded`, per-predictor Spearman/AUC) — **the go/no-go for 6.1 attack transfer**; 69's
   confirmed features by group (any section/import/string features, not only header fields?).
2. **If 68 is a go:** keep attack transfer as 6.1's security outcome; replace the blue Table 4 and prose with the real
   numbers. **If no-go** (GBDT does not move): fall back to option 1 (controlled shared-reliance changes; specs.md).
3. **WP8:** regenerate Figures 3-5 and the 6.1/6.2 tables from the real data (`scripts/paper_figures.py` and the table
   scripts); replace the blue placeholders in Sections 5-6; `make` and `make check`. Figure 4 still shows old-protocol
   data and must be regenerated under byte deletion.
4. **Deferred, user decides:** KernelSHAP/adaptive at 4,096 windows and the scale-up (500 files); retraining MalConv
   (Table 5's blue row) and the stronger attacker on the mitigated model (rerun run/68's attack with the audited
   fields zeroed); W7 (Android second extractor); the front/back matter rewrite from the final results.

Earlier plan (superseded by tonight's runs): front/back matter feedback; refine Section 4; W7 then scale-up.

---

Previous session (2026-10-14):

**The self-review's main criticisms are answered with measured results, and
Sections 3-5 are revised for presentation.** Today, in order:
- **Run 56, field-occlusion oracle** (W2/W4): gain 0.91 at 124 extractions/file; the byte-level pullback beats it 88/100.
- **Run 57, B9** (triage vs. attack-caused disagreements): negative (design flaw: ~600 changed bytes in a ~19K-byte
  readout). Abandoned and cut from the paper (user: present what works).
- **Run 58, M1** (W5): pushed forward on MalConv, the pushforward removes 1.9x the surrogate's evidence (99/100 files),
  1.46x IG over windows, 2.7x random features. **Run 60**: same with random fill (2.0x, 99/99), closing W4.
- **Run 59, M3 test-time mitigation** (W6): zeroing the audited fields cuts the strongest loader-safe attack 16.8% ->
  8.2% (pushforward's 8 fields) / 2.9% (both methods' 12) at 2.0 / 3.5 pts of detection. Framed as a trade-off: the
  point is that the pushforward identifies actionable issues (user). Retraining half stays blue.
- **W6 writing:** comparison threat model (stand-ins), audit vs. surrogate backed by M1 ("use both").
- **Sections 3-5 revised** (`docs/review-sections-3-5-2026-10-14.md`, "Outcome"): three pgfplots result figures,
  conventions and audited-fields tables, validity fixes, sharper novelty, no self-deprecating labels.

**Current goal:** the user reads Sections 3-5 (pp. 3-11 of `manuscript/main.pdf`); then the same treatment for the
intro, abstract, discussion, and conclusion; then reassess W7 (a second extractor, Android) once the PE/EMBER
contributions are solid. The scale-up (2,000 files / 3 seeds, then 10K on the cluster) comes last.

## Where we are

| | state |
|---|---|
| **Manuscript** | `manuscript/` (CCS `acmart` `sigconf`, anonymous; `make`, `make check`: clean). Order: 1 Introduction (`_b`) / 2 Background and Related Work (`_b2`) / 3 Transferring Explanations with Provenance (`_c`; Figures 1-2 conceptual, Table 1 EMBER provenance conventions) / 4 Pulling Back to the Bytes (`_e`; setting; 4.1 with Figure 3 faithfulness vs. cost; 4.2 trigger; 4.3 comparison with Table 2 triage) / 5 Pushing Forward to the Features (`_f`; 5.1 on the GBDT with Figure 4 and on MalConv with Figure 5; 5.2 trigger; 5.3 audit with Table 3 audited fields and Table 4 mitigation) / 6 Discussion / 7 Conclusion; appendices. 14 pages. Figures are pgfplots (palette in `main.tex`; MalConv curve data from `scripts/paper_figures.py` -> `manuscript/assets/data/`). **Blue placeholders left:** the retrained-MalConv row of Table 4 and its sentence (5.3), the Android paragraph (discussion). **Not yet revised:** abstract, intro, discussion, conclusion (only number fixes). Numbers are pilot-scale. |
| **Pullback (PB1, PB2, CM)** | Pilot done (100 files; 50 per trigger; 25 per triage cell). 500-file seed-0 runs prepared: `run/51` (PB1 full baselines, GBDT + MLP), `run/52` (operator variants), `run/54` (CM: cross-deletion, shared, triage at 100/cell, window triage), `run/55` (triggers, 250 files each). |
| **Pushforward (PF1, PF2, AU)** | PF1/PF2 pilot done. **On MalConv (runs 58, 60, `docs/experiments/pf1.md`):** 1.9-2.0x the surrogate under both fills. **AU (runs 47-49, 59; `docs/experiments/audit.md`):** realizable evasion 12.4% vs. 6.0% null, surrogate 10.4%, union 18.4%; test-time mitigation 16.8 -> 2.9% strongest attack for 3.5 pts detection. Retraining MalConv (mitigation's second half) deferred to the cluster round. |
| **CP / theory** | Cut from the paper, archived (`manuscript/archive/`). |
| **The MLP** | **Cut from the manuscript body (2026-10-14)**; returns in future work. The code and runs keep it; the body carries only load-bearing results. |
| **Speed** | String features 2.1x faster, bit-identical. Deferred ideas (`docs/design.md`, "Deferred optimizations"): reuse the extractor's parse in `verify` (~15%); numpy byte counts for the entropies and vectorized byte-entropy windows (~30% together, needs copying thrember code or patching pefile; user: not now). |

## Next

1. **User reads Sections 3-5** and gives feedback; apply it.
2. **Front and back matter:** abstract, introduction, discussion, conclusion get the Sections 3-5 treatment (narrative,
   presentation, consistency with the revised body; results stay in the evaluation). Today's new results (MalConv
   faithfulness, mitigation, fields table) are only partly reflected there.
3. **Reassess W7** (generality): the Android second extractor (`docs/revision-plan.md`, item 12) is the largest
   remaining weakness and several sessions of work; decide scope once 1-2 are done (user: PE/EMBER first).
4. **Later:** MalConv retraining (Table 4's blue row); the scale-up (2,000 files / 3 seeds, then 10K on the cluster),
   which also enlarges the triage cells (W10); deferred optimizations before it; CCS Cycle A vs. B (user, open).

## Decisions

2026-10-14 (whole day):
- **B9 abandoned and cut** (user): negative results that do not support the method are not reported; restrictions are
  stated where they matter. Writing guidance saved as memory `paper-writing-style` (natural prose, no rigid rules, never
  call our method weak, Definitions 1-2 stay, no results-first reordering, be ambitious about the pushforward's novelty).
- **Mitigation framed as a trade-off** (user): the audit's value is identifying actionable issues, not a perfect defense.
- **Figures:** result figures added; Figures 1-2 kept with fixes (conservative, user's guidance).

2026-10-13 (night, end of session):
- **The user runs `run/50`-`55` on the code as-is** (no verify/parse change tonight). Two optimization ideas are noted
  for later in `docs/design.md`, "Deferred optimizations" (user asked).

2026-10-13 (night, seed-0 scale-up prepared):
- **Scale-up = 500 files, seed 0, full fidelity, GBDT + MLP** (user). Selection
  `artifacts/explanation_set/ts-scaleup500-seed0.parquet` (250/label, a superset of the 100 pilot files; written by
  `faithfulness.py --include ... --select_only`). Scripts `run/50`-`55`, all smoke-tested; the user runs them in tmux
  (16 CPUs, GPUs 2 and 3). Order: 50 (KernelSHAP, `explain.py --fill_missing` keeps the pilot rows) -> 51 (pullback
  faithfulness, ~12 h) -> 53 (pushforward) and 54 (comparison); 52 (operator variants) and 55 (triggers) need only 50 /
  nothing. ~20-24 h in all, run one after another.
- **String features 2.1x faster overall, bit-identical** (`features.py`, added at the end: one `finditer` per regex
  over the joined strings instead of 590k `re.search` calls; verified on 400 files and in `tests/test_ember2024.py`).
  The user rejected replacing pefile's / the entropy `Counter`s ("too much code to review"): only the string change and
  numpy for its per-character loop stay. The runner's cost model is now ~2x pessimistic.

2026-10-13 (evening, experiments: 1a/1b of the experiment plan):
- **Plan (user):** now 1a (realizability of AU's evasion) and 1b (significance on fresh, detected held-out malware);
  then a seed-0 scale-up to 2,000 files. Mitigation (1c) is a manuscript TODO, no code yet; real-attack transfer (1d)
  not now (maybe never). A later round (3 seeds, 10K files) runs on a cluster.
- **Run 47 done** (`docs/experiments/audit.md`, "Held-out evasion and realizability"). Run 46's rates were inflated
  (non-detected files counted; random draws that broke the parse dropped; evaluated on the confirmation files). On 902
  fresh detected malware: pushforward 19.7% vs. random 12.3% (+7.5 pts, p = 3e-14), surrogate 19.0%, union 30.6%.
  **Realizable (loader-safe) pushforward: 12.4%, not above random free fields (10.9%, p = 0.17);** realizable union
  18.4% (p = 2e-16). The manuscript's AU numbers are now wrong (22.5/16.5/24.6/35.1) and must be updated; how to frame
  realizability is for the user to decide. Proposed follow-ups (cheap): decompose the realizable loss (IAT exclusion
  vs. benign values in constrained fields) and a null that excludes the recipe's own fields.
- **Run 48 done:** realism costs the pushforward recipe 19.7 -> 12.4% (IAT/skips 3.4 pts, abnormal values 3.9 pts);
  against a null of loader-ignored fields that no method confirmed (4.4%), the realizable recipe is +8.0 pts
  (p = 3e-13). Run 47's "failure" came mostly from a null drawn half from the confirmed fields. Open: a broader null
  (all loader-ignored header fields), and whether to validate the loader classification by execution. User wants
  realistic perturbations only (CCS standard), so the paper's AU headline becomes the realizable numbers.
- **Run 49 done (broad null):** realizable pushforward 12.4% vs. 6.0% for as many other loader-ignored fields outside
  the DOS region (+6.4 pts, p = 3e-12) and 3.8% for all loader-ignored fields; realizable union 18.4%; realizable
  surrogate 10.4%. User: lead with the pushforward; no sandbox validation needed ("we don't break the files"). Manuscript
  AU numbers still to update (lower priority). Next: the seed-0 scale-up to 2,000 files (run/ scripts for the user).

2026-10-13 (evening, writing session, background/related work):
- Section 2 is now "Background and Related Work" (user): an overview of learning-based detection, post-hoc
  explanation, explaining malware detectors, transferring attributions, and an "Our Position" subsection with the
  three novelties (P for program extractors; the pushforward; detectors over different representations in one space
  -> triage and audit). The old standalone Related Work is archived (`archive/g_related_work_old.tex`).
- Notation (problem/feature space, Definitions 1-2, Figures 1-2) moved to Section 3.1 "Preliminaries". Figure 3 is
  input before 3.4 so the three figures do not stack on one page. Body ends on p. 11.

2026-10-13 (evening, writing session, polish pass 1; user's 7 criticisms):
- Intro rewritten in paper voice: research questions dropped, three compact contributions (method, pullback,
  pushforward). Figures 1-3 kept (user rejected a replacement overview figure); only their whitespace was tightened (Figure 2 panels fit their content; Figure 3 gaps and padding reduced; Figure 1 boxes slightly smaller).
- Section 2 is now Background (detectors: EMBER, GBDT, MalConv; explainers: SHAP, KernelSHAP, TreeSHAP, IG,
  occlusion; two spaces; faithfulness). Related Work moved to Section 3. The "Setting" subsection is gone: a short
  threat model opens each application (5.3 CM, 6.3 AU).
- Section 4 "Transferring Explanations with Provenance": theory first (P, pullback, pushforward), then constructing P
  (instrumentation, occlusion, granularity = coarsening as a paragraph, EMBER instance). Coarsening is kept because
  PF1 pushes window explanations through P over windows and PB1/CM's window controls use it.
- Experimental Setup dissolved: data/models open Section 5; explainer configs and the deletion operator in 5.1; the
  trigger in 5.2; EMBER instrumentation in 4.3. Desiderata and sigma-consistency archived. Bib: +lundberg2020local,
  +ke2017lightgbm.
- Short titles: 5 "Pulling Back to the Bytes", 6 "Pushing Forward to the Features". Body ends on p. 11 (limit 12).

2026-10-13 (evening, writing session, restructure):
- **Organized by operator** (user agreed): 1 Intro, 2 Background and Setting (spaces + a short Setting; the threat
  model is minor, user), 3 Explanation Provenance (P, **constructing P: instrumentation vs. occlusion**, transfers,
  coarsening), 4 Experimental Setup, 5 Pulling Explanations Back to the Bytes (faithfulness and cost incl.
  instrumented vs. black-box P; planted trigger; comparing two detectors), 6 Pushing Explanations Forward into
  Features (faithfulness; ground truth for feature explainers; auditing MalConv), 7 Related Work, 8 Discussion,
  9 Conclusion. PB2/PF2 stay in the body (user: high value as laboratory experiments).
- CM and AU made parallel (Motivation / What the operator adds / Design / three findings).
- Threats to Validity and per-application limitations folded into a light Discussion (user: no self-criticism);
  design caveats moved into the designs. Claims lists and the experiments/status table archived.
- Appendices B/C (soundness, completeness, independence), E, and the symbol table archived (user: not measured, no
  practical impact); conservation kept as one sentence per transfer.
- Body ends at the bottom of p. 12 (references start p. 13). Next: section-level writing.

2026-10-13 (evening, writing session, later):
- **CP and the theory cut from the paper (user).** Sections 3.4 (statistics of P), 3.5 (round trips, bounds,
  perfect-reconstruction theorems), and 4.2 (CP) moved to `manuscript/archive/` (not deleted). Kept: the coarsened-
  provenance definition (short, in 3.3) and the Bayes reading of D+ in the pushforward. The instrumented-vs-black-box
  comparison is replaced by PB1's black-box pullback (1.02-1.04 of occlusion at 256 windows). C2 dropped (C1-C3 now);
  claim 3 is "faithful up to its source's resolution" (no overlap); paper claims renumbered 1-4. The resolution table
  lost its overlap row.
- **"Framework" -> "method"** (user: not much of a framework left). Section 3 is now "Explanation Provenance". Body
  ends on p. 13 (from 15).
- **Evaluation split** into Section 4 "Evaluating the Transfers" (intrinsic) and Section 5 "Comparing and Auditing
  Detectors" (extrinsic), each with opening and closing transitions.

2026-10-13 (evening, writing session):
- **Missing sections drafted** in paper voice. New section 2, "System and Threat Model": the defender (owns detectors,
  instruments the extractor once, white-box explainers), the two tasks (triage, audit), the adversary the audit
  anticipates (malware author changing bytes; scrambling measures reliance, not a demonstrated attack), out of scope
  (attacks on explanations/extractor/training data; the planted trigger is a ground truth, not a threat; dynamic
  features). "Summary" renamed "Conclusion".
- **Abstract reports AU's 22.5% next to the 16.5% random-field baseline** (Claude's call for honesty; the margin is
  modest and a reviewer would find it). Abstract is ~270 words (trim later if needed).
- **Cut candidates (not applied; for the user):** the claims list + experiments/status table in `_d` (~0.5 p); the
  research questions in `_b` (~0.15 p); PB2/PF2 and the trigger setup to the appendix (~0.9 p); CP's instrumented-vs-
  black-box paragraph to the appendix (~0.25 p); parts of `_c` (perfect-reconstruction theorems, desiderata, one of the
  three framework figures) to the appendix (~1 p).

2026-10-13:
- **Venue switched to ACM CCS 2027, Cycle A** (user; prefers the ACM template to USENIX's). CfP not out; by CCS 2026,
  abstract ~Jan 7 and paper ~Jan 14, 2027 (about 12 days earlier than USENIX's Jan 26). Cycle A rejects cannot go to
  Cycle B. `manuscript/main.tex` is now a complete document on `acmart` `sigconf` (anonymous; body <= 12 pp; Open
  Science and Ethics appendices after the bibliography); built with `make` in `manuscript/`.
- **3-C revised (the audit) worked and is written up.** The working framing scrambles the bytes P names for the
  features MalConv's detection rests on (not forging benign content, which does not transfer; see `docs/graveyard.md`).
  Mitigation deferred (SSViT GPU work); the surrogate column is kept but we do not fit the narrative to it (user).
- **Manuscript updated** to add 3-C, reframe CM as the pullback's local use, rewrite claim 3 for the pushforward
  application, and remove Appendix F (promoted into 3-C's global comparison).
- **Repository cleanup:** 3-B and the rule-based 3-C (YARA) are archived (`scripts/archive/`, `run/archive/`); their
  full plan docs are summarized in `docs/graveyard.md` and removed from the tree (kept in history).
- **CLAUDE.md relaxed:** the "do not propose X" research prohibitions became "generally unproductive, raise with a
  reason" (`docs/graveyard.md`, "Directions the user has generally found unproductive").
- **Docs reorganized:** experiment docs merged/moved to `docs/experiments/`; "3-A/3-C" vocabulary retired (CM/AU
  canonical); `design_provexp.md` -> `design.md`.
- **Introduction rewritten** with two framing choices (user): (i) **framework + symmetry first** (applications are
  evidence); (ii) **claim the fuller vision** in the contributions -> this makes AU's mitigation, CM's real-attack
  transfer, and the scale-up load-bearing before submission.
- **LaTeX toolchain = user-space TeX Live + latexmk + pdflatex** (not tectonic, not conda). Installed in `~/texlive`; `manuscript/main.tex` is a complete document
  (preamble included) built with `make`.

2026-10-12 (latest):
- **The pushforward needs an extrinsic application**; the symmetry is the novelty (user). CM alone is not enough.
- **3-C revised adopted:** auditing MalConv for shortcuts through the pushforward (`docs/experiments/audit.md`). Go/no-go
  requires a confirmed shortcut (confirmation is cheap); discovery on the 2,000-file explanation set; MalConv
  mitigation out of scope.
- **Hand-built domain-specific aggregation (a PE parser) is not a realistic alternative**: tremendous manual effort for
  one format (user). The realistic alternative is the surrogate.
- The surrogate is trained on the test split outside the explanation set (only MalConv's test predictions exist); to
  be stated in the paper.

2026-10-12 (later):
- **3-C on hold** after failing the sniff test: as built it rests on the pullback and Pᵀ, not the pushforward. Next
  step is a mock-up of a pushforward-native task, or 3-C as an application of P (user decides).
- **Screening criterion 6: mock the result first** (`PLAN.md`, section 3).
- Packing is not a motivation or case study (user). Rule semantics do not matter to the method (a rule is a byte set
  from an outside detector) but matter to the story's realism (user and Claude agree); YARA-Forge only later, for
  realism. capa deferred.
- Long installs and setup steps go in `README.md`; the user runs them.

2026-10-12:
- **3-B dropped** as the pullback application; **CM is the pullback's application** (user). 3-C stays the
  pushforward's.
- **Screening criteria** for extrinsic applications (`PLAN.md`, section 3): needs what only P gives; a practical task;
  the realistic alternative named; a go/no-go check first; extra skepticism for ideas already ruled out.
- **Hand-mappable findings are acceptable** when P automates the mapping (CM's shared bytes are named header fields;
  "the whole point of computers is to automate things", user). State the caveat once.
- **CM scope:** problem-space only (shared reliance; disagreement triage, option 1: blind / oppose / agree); the
  feature-space comparison goes to the appendix until it has a use beyond being interesting; byte n-grams set aside.
  Real-attack transfer noted for the future. In the paper: "shared reliance", not "attack surface".
- **Stay on track:** analyses must serve the current task; no rabbit holes (user).

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
- **PF1 design** (`docs/experiments/pf1.md`): two references, the attributable-only check, the naive incidence sum, the
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
