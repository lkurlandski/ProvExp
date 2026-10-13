# Status

Last updated: 2026-10-13 (evening; writing session: all sections drafted). The framework and intrinsic evaluation are done at pilot
scale; both extrinsic applications are done and written up. The repository was reorganized (experiment docs under
`docs/experiments/`, dropped threads archived, dead ideas in `docs/graveyard.md`). The two applications: **the pullback
compares two detectors per file** (CM / Comparison, `docs/experiments/cm.md`), and **the pushforward audits a raw-byte
detector across a corpus** (AU / Audit, `docs/experiments/audit.md`). `run/` holds the commands that produced
everything in `artifacts/` (active runs 01-21, 30-33, 38-46; dropped runs in `run/archive/`).

**Current goal: finish a rough draft of the manuscript for ACM CCS 2027 Cycle A, then decide on the scale-up.** The
venue switched from USENIX to CCS (2026-10-13). The manuscript builds locally on the CCS template (`cd manuscript &&
make`). Introduction and related work are written; abstract, discussion, conclusion, threat model, and the ethics and
open-science appendices remain; the document is still in dissertation-chapter voice and its body runs to page 14
against CCS's 12-page limit. See `docs/resume-prompt.md`.

## Where we are

| | state |
|---|---|
| **1. Framework** | Definitions and modest theory in `manuscript/_c_framework.tex`. Round-trip matrices M, N kept as theory; ambiguity and overlap have no demonstrated use (undecided); coverage and the null element's share are not contributions. A Shapley-style uniqueness result is noted as a possible strengthening, not pursued. |
| **2. Intrinsic: PB1** (pullback faithfulness, cost) | Done at pilot scale (`docs/experiments/pb1.md`): parity with the best direct baseline at 64-1,024 windows, ahead at 4,096; at byte level 1.67x occlusion. |
| **2. Intrinsic: PF1** (pushforward faithfulness) | Done at pilot scale (`docs/experiments/pf1.md`): R = 0.31-0.40 for window-level sources; the resolution trend rises 0.34 -> 0.80 (bytes). |
| **2. Intrinsic: CP** | Census, coarsening, CP.3 done (`docs/experiments/cp.md`). |
| **2. Intrinsic: PB2, PF2** (planted triggers) | Done at pilot scale (`docs/experiments/trigger.md`); demoted, possibly removed later. |
| **CM. Comparison (pullback, local)** | Done at pilot scale, written up (runs 30-33; `docs/experiments/cm.md`; `manuscript/_d_applications.tex`). GBDT vs. MalConv byte by byte: shared reliance (bytes both rely on, in the header; window-level comparison without P misses them) and disagreement triage (GBDT-only verdicts rest on header bytes MalConv reads the other way; visible only at byte level). Reframed as the pullback's *local* use. Deferred: seeds 1-2; real-attack transfer. |
| **AU. Audit (pushforward, global)** | **Done** (runs 38-46; `docs/experiments/audit.md`; `manuscript/_d_applications.tex`). MalConv's IG pushed forward into the EMBER features, aggregated over the 2,000-file explanation set. The working framing scrambles the bytes P names for the features MalConv's detection rests on: 9 of 20 confirmed outside the DOS header; scrambling them evades 22.5% of detected malware at 1% FPR (surrogate 24.6%, union 35.1%, random 16.5%). Global comparison with the GBDT (replaces the old Appendix F): MalConv leans on whole-file aggregates, the two detectors' localizable rankings barely agree (Spearman 0.10), only the checksum shared at the top. Mitigation (zero the fields; retrain) deferred (SSViT GPU work). |
| **Appendix** | App-L a stated limitation; App-R's duplicate-feature sweep not run; the byte-set control bound accepted, not started. Old Appendix F (feature-space comparison) removed, promoted into AU. |
| **The MLP** | Set aside temporarily; returns after the GBDT methodology is established. |
| **Manuscript** | CCS template (`acmart` `sigconf`, anonymous), builds with `make` in `manuscript/` (18 pp; **body to p. 15 vs. a 12-page limit**). All sections drafted (2026-10-13, evening): abstract (`_a`), introduction (`_b`), system and threat model (`_b2`, new section 2), framework (`_c`), intrinsic evaluation (`_d_evaluation`, Section 4 "Evaluating the Transfers"), applications (`_d_applications`, Section 5 "Comparing and Auditing Detectors"), related work (`_d2`), discussion (`_e`), conclusion (`_f`), Ethical Considerations (`_h`) and Open Science (`_i`) appendices. Load-bearing TODOs marked in `_e` (AU mitigation, CM real-attack transfer, scale). Still in chapter voice in `_b`/`_c`/`_d` (research questions, internal experiments table, "this chapter"); cuts of ~3.3 pages to be decided with the user. |

## Next

1. ~~Write the missing sections~~ (done 2026-10-13 evening; TODOs inside: anonymized repo URL, binary access terms,
   final numbers after the scale-up).
2. **Chapter->paper pass (next):** first agree the cuts with the user (~3.3 pages: candidates in the 2026-10-13
   evening decisions below); voice, structure, and length (cut ~2-3 pages to reach the 12-page body; discuss the cuts
   with the user). Check that every contribution (C1-C4) maps to evidence that has been run. Ask before changing what
   a claim is for.
3. **Then scale up** (only once the draft convinces us the plan is solid, when the user decides): all 2,000 files,
   seeds 0-2; up to ~48 h on 16 cores for the CPU work plus GPU time for MalConv's IG and any AU retrain. Tightens the
   pilot numbers (esp. AU's 22.5% evasion, CM) with seed variance; does not change the argument. Nothing is scaled yet.
4. **Deferred pieces, now load-bearing** (the intro claims the fuller vision): AU's **mitigation** (test-time field
   zeroing + a retrain) and CM's **real-attack transfer**, both needing SSViT GPU work; and the MLP's return. Do not
   let the intro overclaim relative to what is run.
5. **Open decision (user):** CCS Cycle A (~mid-Jan 2027) or Cycle B (~late April 2027); a Cycle A reject cannot go to
   Cycle B.

## Decisions

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
