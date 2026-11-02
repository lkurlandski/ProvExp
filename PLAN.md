# ProvExp Research Plan: Feature Provenance in Malware Classification

Living document, restarted 2026-10-22. The previous plan (explanation provenance for explainable ML, the pullback and
pushforward of explanations) is archived in `docs/archive/PLAN-explanation-provenance-2026-10-21.md`; why it was
abandoned is in `docs/graveyard.md`. Deadlines and conference cycles are not a planning constraint (user).

## Why we restarted (2026-10-22)

The explanation-provenance paper was built method first, with applications found afterwards. A simulated CCS review
(`docs/reviews/explanation-provenance/2026-10-21-ccs.md`) rated it weak reject; the user judged it far weaker (strong reject: not novel, no compelling
utility to the security community) and agreed with the diagnosis: where flat provenance is precise (named header
fields) it is not needed, where it would be needed (hashed and aggregate features) it is diffuse, and every
application landed on the first side. We had also misjudged our novelty by not grasping the related work.

## Thesis

**Simple feature provenance (which problem-space elements produce which features, through which items) bridges the
feature-problem space gap in malware classification.** Every line of work on realizable attacks and robust detectors
needs, for a file and a threat model, what the attacker can reach in feature space; each gets it by hand, from data,
or by running transformations. Instrumenting the extractor computes it automatically and, for most features,
exactly. One framework answers several problems that the literature treats separately.

Framing: a malware-classification paper, as generic to malware as possible (PE is the instance; avoid format minutiae
in the argument). Elements are any problem-space units (bytes, characters, tokens, packets).

## The model (`docs/feature-provenance-model.md`)

Three layers: the parse (elements -> items: membership and location), contributions (items -> sums, additive), the
readout (sums -> features: identity, normalization, entropy, max, presence). Edits are stated in bytes and translated
to item operations: content edits (exact), item-creating edits (local re-recognition), structural edits (flagged).
Claims to prove: C1 exact side effects; C2 coupling between features; C3 reachable sums under add-only threat models
(a sound over-approximation for verified training); C4 per-feature reachable directions (Incer et al.'s four cases,
automatically). Today's flat P is the projection of the model onto elements x features; it may serve as the intuitive
introduction and a simple baseline (writing decision for later).

## Directions (A is the core; each must survive its own screening or is dropped)

- **A. Threat models to feature space.** Side effects, coupling, reachable directions and regions computed from the
  instrumented extractor; uses: realizing feature-space attacks in the problem space (including hashed features that
  Severi et al. ruled out), and robust or verifiably robust detectors from derived constraints (Incer, Gimenez, Chen).
  Realistic baselines: Gimenez et al.'s perturbation-vector feature selection and Labaca-Castro et al.'s empirical
  per-feature probabilities, evaluated on **held-out** attack families; Severi et al.'s 17 hand-picked features;
  Rosenberg et al.'s hand-written modifiers.
- **B. Auditing raw-byte detectors for backdoors and shortcuts in feature vocabulary.** No trigger-identification
  defense for raw-byte models found (RAMP shows the attack; PBP purifies; Jigsaw and generic defenses). Competitor:
  Perasso et al.'s region overlay; B only has an edge for triggers in shared or hashed content. A variant: locating a
  feature-space trigger's bytes in poisoned training files.
- **C. Diagnosing evasion through disagreement between heterogeneous ensemble members.** Baseline: Smutz & Stavrou's
  mutual agreement (score disagreement); C must win where scores are silent (e.g., both members evaded) or classify
  the cause. PASA is the nearest attribution-based detector (not malware).
- **A' (chosen 2026-10-27, dropped 2026-11-02; `docs/graveyard.md`).** Realizable worst-case evaluation of a
  detector: an exact solver over edit choices, every feature computed through provenance, a proven floor beside the
  best real attack. Sound throughout, but certified budgets never exceed 4 KB (run 116) and appending on PV certifies
  only near-circularly; A already builds detectors these edits cannot move. Folded into A: the region's soundness for
  combined edits (run 111, 1,105 of 1,105) and the learned-constraints contrast (run 110). Record:
  `docs/direction-A-prime-plan.md`, Section 13.

## Next steps (2026-11-02, review done: plan the response)

The harsh simulated review of the body is done (`docs/reviews/2026-11-02-body.md`). Scores, assuming the
empty sections are written well: formal methods Weak reject, adversarial ML for malware Weak reject, systems security
Weak accept; likely reject with encouragement, borderline accept once its top risks are fixed. **Next (a fresh
session, `docs/resume-prompt.md`): turn the review into a plan with the user.** Triage each risk (fix now in `.tex`;
a new run; a framing decision for the user; reject, with the reason), then fold the agreed items into the order of
work below. No run, rewrite, or section draft before that plan is agreed.

The review's findings, in its order of weight (its Section 6 has the full register, R1-R16):
1. **Detector evaluation reads as tautological (R1).** The monotone rows' 0.0 is Corollary 1. The adaptive search uses
   two of twelve operations and evades the undefended model on 8%, against 53% for the held-out toolkit. Proposed:
   extend the search to every operation the engine predicts (go/no-go: beats GAMMA API on the unconstrained model);
   split the toolkit outputs into in-catalogue and out-of-catalogue (LIEF relayout) and make the latter the
   independent evidence; restore the "still detected after every attack" column (41/50 vs 20/50).
2. **The guarantee's conditions are unchecked (R2):** closure of the population (P1) and envelope stability off the
   corpus (P2), both in `docs/formalization.md` Section 9, minutes each.
3. **The hand table is the authors' own, and four of Table 6's seven errors lie outside the population (R3).** In the
   population the derived and hand tables give detectors differing in two features. Proposed: say so; consider
   reframing Table 6 (a decision for the user); add an independent hand analysis by instrumenting Gimenez et al.'s
   40-feature extractor (measured holes, an adaptive cell).
4. **One instance (R4):** a second built instance whose comparison is against constraints published by others, or a
   scope reduction now. Which domain stays unimportant.
5. **Misreading Pierazzi et al.'s eta (R5)** at `_d_framework.tex:12-21`: their side effects come from consolidation,
   which we declare per operation (R5); we compute the extractor's response.
6. Smaller: the novelty paragraph against IVM, provenance semirings, abstract interpretation (R6); routing as an attack
   surface and coverage on untruncated files (R7); expert set under additions as the headline comparison (R8); Theorem
   1's practical role and timing (R9); keyed-count sign entry wrong in general (R10); adaptive column on different
   models (R11); PV's 44.4% measured with the hand rules (R12); instrumentation cost (R13); exactness rows for all
   twelve operations (R14).

Effect on the order of work below: step 4 is done; step 5's adversarial-training row waits until the adaptive search
is strengthened (the review judges its synthetic 20% implausible against an attack that gets 8% on no defense).

## Next steps (2026-11-02, stock-take done: formalize the framework)

**Decided (user, 2026-11-02, after the stock-take):**
1. **Formalize the framework next**, in the PE malware domain. Work through *every* theorem we judge important (C1
   exact side effects, C2 coupling, C3 reachable region, C4 directions, the composition with a monotone classifier,
   and any others that turn up), not only those A rests on today; pruning or moving some to an appendix is a later
   writing decision. The user judges the formalization (a precise class of "sum-then-readout" extractors with
   per-kind obligations A1-A4 under which side effects, directions, and regions are computable) a significant
   contribution in itself; keep judging novelty harshly, but do not dismiss it as "incremental view maintenance plus
   sign analysis".
2. **A second domain later, as breadth** (e.g., a flow-statistics extractor for network traffic, which exercises
   every readout type). Applicability beyond malware is a strength, but establish the method and core contributions
   on PE malware first.
3. **"Several problems" is a goal, not a requirement.** A strong framework plus one application (A) with enough depth
   and breadth is a solid paper; tying in a second application is welcome if it comes.
4. Strengthening A (adversarial-training row, second toolkit, leave-one-out PV, scale, cost column) and screening B / C
   wait until the formal model is written; B / C are screened against what it offers them.
5. **Framing (user, later 2026-11-02): one strong paper**, direction A with the model as its framing section, not
   "several applications under one framework". The evaluation is organized around the model's claims: the computed
   answer is (i) correct, (ii) more correct than hand analysis, (iii) more complete than constraints learned from
   attacks, (iv) useful (sound detectors). The defense route (monotone classifiers) is Gimenez's and Incer's; the
   contribution is deriving the threat model's effects, and the detector shows why it matters.

**Revised (user, 2026-11-02, formalization review round 1; `docs/feedback.md`):**
- **Three domains, emphasized about equally for now**, replacing item 2's "second domain later": Windows executables
  with EMBER (built), Android apps with Drebin (the Android literature uses Drebin or small variants almost
  exclusively), and network traffic with CICFlowMeter (the most widely used flow features; CTU-13 with Chernikova and
  Oprea's FENCE features and their ~360 hand-written constraints is the candidate experimental instance and baseline,
  pending a deeper literature pass). Three domains would justify a single main application (A). Revisit if data is
  lacking, or if Drebin adds little beyond EMBER; then a different domain where adversarial examples are popular may
  replace it.
- **The formalization uses small real examples from the three domains throughout** (no toy formats), names its
  requirements by meaning (faithful recording, self-contained contributions, complete record of structure, changes stay
  near the edit, honest tools; formerly A0, A2, A1, A3, A4), and opens every section with its question and an example
  before definitions. A short algebraic remark (sums as a monoid homomorphism; Gray et al.'s algebraic vs holistic
  aggregates) explains why maxima need the item table and where the class ends.
- Data: PE and ELF raw files are local (EMBER-2024); EMBER-2024's APK/PDF records carry only format-agnostic features
  and no raw files. Raw APKs: AndroZoo (academic key). Traffic: public pcaps (CTU-13 / Stratosphere, CIC-IDS2017/2018,
  with Engelen et al.'s corrected CICFlowMeter).

**Reassessed (user, 2026-11-02, end of the formalization rounds).** `docs/formalization.md` reached 13,100 words,
mixing paper text, appendix proofs, and project notes; it is **frozen** as the reference and appendix source, and its
Section 10 is not written (each remaining result only if the mock needs it). Settled (user): the domain is
*adversarial examples in practical security tasks*; the framework is as agnostic as Pierazzi et al.'s; PE malware is
the inspiration, guidance, and main instance; other domains are breadth, as many as possible. This replaces "three
domains emphasized about equally" above. Paper text goes straight into `.tex`.

**Order of work (revised with the user, 2026-11-02):**
1. **Feasibility reading for breadth instances** (done 2026-11-02, `docs/status.md`: CTU-13/FENCE first, Drebin
   second, CICFlowMeter as the running example) (light, no code): per candidate domain (Android apps with Drebin;
   traffic with CICFlowMeter or CTU-13/FENCE; others if cheaper), whether raw data with labels, an open extractor, and
   an attack or hand-written constraints to compare against exist. Fold in the facts to verify (Drebin's API lists and
   permission map, CICFlowMeter's definitions, FENCE's constraint count, Pierazzi et al.'s wording). Output: which
   breadth instances the paper can show, and at what depth.
2. **Paper mock** (done 2026-11-02: `docs/paper-mock.md`; open: Drebin as instance, coupling row) (`docs/paper-mock.md`, at most two pages): contributions; section outline with a word budget per
   section (framework about 2,500 words); every table and figure with the model component behind each column, measured
   cells vs missing ones; the four-part evaluation above. Candidate extra rows, each with a go/no-go before code:
   coupling against Severi et al.'s hand exclusions; coverage weighted by attack success; the detector-gain share of the
   88 pefile-warning features outside the model.
3. **Body in `.tex`** (done 2026-11-02, this session): Section 3 framework (`manuscript/_d_framework.tex`, 2,568
   words against 2,500; proofs in Appendix A, `_j_proofs.tex`), Section 4 EMBER instance (`_e_instances.tex`, 1,038
   against 1,000), Section 5 evaluation (`_f_evaluation.tex`, ~1,900 against 3,000; the mock's Tables 1-3 are Tables
   5-7 of the PDF). The old manuscript is deleted; one file per section, empty stubs for the rest.
4. **Harsh simulated review of the body** (done 2026-11-02: `docs/reviews/2026-11-02-body.md`; next: plan the response, see
   "Next steps (2026-11-02, review done)" above), then the user's read of Sections 3-5; triage both together. Decision point (user): what the
   review says the paper needs (a second instance or not, further baselines, framing).
5. **Replace the synthetic cells** (each marked `% SYNTHETIC` in the source; `docs/status.md`, top block): the
   add-section exactness check and the cost bookkeeping (small; run directly); PV with 8 attacks under the fixed
   adaptive search; the adversarial-training row (a `run/` script for the user; next number 117).
6. **A's remaining gaps, by reviewer weight:** held-out attacks from a second toolkit (MAB-Malware); leave-one-out PV;
   scale (seeds 0-2, full splits, more malware; user's decision).
7. **The remaining sections:** Background (800 words), Related work (700), Discussion (500), then the introduction
   (1,000) and abstract last; Figure 1 of the mock (one edit becoming an item delta, adjusted sums, and new features,
   against re-extraction) in Section 3.
8. **A breadth instance**, if the review says the paper needs one: late and interchangeable; which domain does not
   matter (user, 2026-11-02).

The stock-take that led here: `docs/status.md` (2026-11-02, stock-take). Next session: `docs/resume-prompt.md`.

### Earlier: next steps (2026-11-02: A' dropped; pause and take stock)

A' dropped and folded into A (above). The user wants a pause: a deep look at what the project has accomplished before
choosing further work. The user leans toward formalizing the framework (the model and its claims, C1-C4) rather than
new applications (B, C) or strengthening A, and is open to the alternatives. Claude agrees, on the condition that every
definition and theorem serves A's results or predicts something checkable against re-extraction (the old direction
failed by building method first). Next:
1. **Stock-take, in a new session** (`docs/resume-prompt.md`): what is established (model, engines, direction A's results, what A'
   showed), what is claimed but unproven, and what the thesis needs.
2. Then decide the next work: formalization, A's gaps, or screening B / C.

### Earlier: next steps (2026-11-01, end of session: decide whether A' is salvaged)

Done this session: A' re-planned (`docs/direction-A-prime-plan.md`, adopted); step 1 built and run (`run/114`,
`run/115`): certificates only where the edits barely touch the detector (append on PV, partly circular) or at small
budgets (4 KB); the relaxation is too loose above a few KB; G2 untested (no adversarially trained rows). The user doubts
A' can give a practically useful result. Next:
1. **Read `run/116`** (running since 2026-11-01 16:37: containment on the `highspy` path, then the certified budget
   at 1-32 KB on the undefended model and PV), the evidence for the certified-budget salvage option.
2. **Decide A''s fate with the user** (`docs/resume-prompt.md`): salvage (in what form, for which reviewer-relevant
   claim, against what alternative), fold into A, or drop to the graveyard. Bring the evidence (plan Section 12) and
   judge by the screening criteria (the gap only provenance makes cheap, a realistic competitor, a falsifiable check).
3. If dropped or folded: return to A (scale-up, the adversarial-training baseline, a second toolkit) or screen B / C.

### Earlier: next steps (2026-11-01, planning session: A' re-planned)

A' plan adopted (`docs/direction-A-prime-plan.md`); `run/113` read (all 6 undecided). Next, in order (plan Section 6):
1. **Pre-check on PV (G1):** built (`scripts/ap_bracket.py`) and smoked (plan Section 9). **The user runs `run/114`**
   (~1.5 h); then read it, and raise the section-slot coverage (few files can take an added section) with the user.
2. **Hardened rows:** adversarial training on our search's edits and on the toolkit's outputs (`run/` scripts for the
   user), the battery re-run on each.
3. **Main table at pilot scale (G2, G3).** 4. Scale only when the user decides.

### Earlier: next steps (2026-11-01, end of session: A' to be re-planned from scratch)

Done this session: the tightening round (decision 7 option 1) built and tested (commits 7d002a4, ce584b8, 5b05181);
the histogram and most of the strings gap were realizer bugs, now fixed; a HiGHS presolve false infeasibility found and
guarded. Then the user and Claude re-evaluated check 1b: it tested certification on the undefended EMBER GBDT (failure
expected; EMBER models are known to be fragile), its 20% threshold was ungrounded, it counted undecided as failure,
and check 2 is not a prerequisite for certificates. The no-go does not decide A'; decision 7's remaining options
(expert-set row, Table A'2, tighter learned baseline, pause) are not to be chosen on its basis. The user doubts the
expert-set row's value (a little-cited paper) and Table A'2's novelty (Level Up, Chen et al.); option 3 is welcome as
a column. Next:
1. **Fresh planning and brainstorming session for A'** (new chat, `docs/resume-prompt.md`): settle the aim, the
   table with the model component behind each column, and a go/no-go that tests the claim on informative cases.
   Candidate starting point: compare hardenings (undefended, PV-seen/PV-all, adversarially trained, trained on
   realizable edits, monotone) by certified / evaded (battery and adaptive search) / undecided, with learned and
   budget-only constraints as the contrast. Main risk: tractability (the program is ~225 K variables, ~43 K binaries).
2. Read `run/113` (containment, the 6 files at 1,800 s, any evasion written) as input to that session.

### Earlier: next steps (2026-11-01: the tightening round built; `run/113` with the user)

Done: the user chose decision 7's option 1. Built (commits 7d002a4, ce584b8): section entropies tied to per-section
counts; the exact block model of the byte-entropy windows; realizer repairs (sections, blocks, string reserve,
knife-edge nudge); `scripts/ap_check2_realize.py`. The histogram and most of the strings gap turned out to be the
realizer. Diagnostic at 480 s: all 6 files undecided. Next:
1. **The user runs `run/113`** (~1 h): containment (must hold on every edit), the 6 files at 1,800 s, any evasion
   written as a file. Apply the stop rule: >= 3 solver evasions still not evading as files -> decision 7 option 2.
   If every file is undecided (proposed reading, to confirm): fake evasions gone, nothing certified, check 1b still a
   no-go -> decision 7 returns to the user with that result.
2. If evasions realize (check 2's 70%) on most of the 6: re-run check 1b in full on the tightened encoding (user).

### Earlier: next steps (2026-10-31: check 1b read, no-go; decision 7 with the user)

Done: check 1b (`run/112`, 1,800 s per solve, run by the user) read: of the 13 covered files, 0 certified, 6 solver
evasions, 7 undecided (go was >= 4 certified). All 6 evasions written as files (`ap_realize.realize`, re-extracted):
**0 of 6 evade** (real raw 3.40-6.76 vs the solver's 0.77-1.10; threshold 1.10). Attribution by feature group (one group
on the solver's sides, the rest on the written file's): byte-entropy 1.96-5.37, strings 2.15-4.50, section entropies
3.27-5.65 (4 files), histogram about unchanged; no group alone closes the gap, and looseness vs realizer weakness is not
yet separated. Both hypotheses failed (fewer evasions than the smoke's 3; byte-entropy the main carrier). Next:
1. **The user decides** among (recommended first): (a) one bounded tightening round — the exact block model of
   overlapping windows, a bound on added-section entropies, realizer repairs for strings and sections — re-measured on
   the 6 files, with a stop rule (if >= 3 still do not realize, go to (b)); (b) decision 7's option 3, lead A' with
   another use (expert-set row, or Table A'2 on our own byte-level edits); (c) option 2, the tighter learned baseline,
   as a sensitivity row only (~1 min); (d) pause A' for scaling A or the manuscript. A longer time limit is not a fix.
2. Then as decided; check 2 (>= 70% of solver evasions realize) stands at 0/6 today.

### Earlier: next steps (2026-10-30, fifth session: realizer built; two sound cuts; check 1b handed to the user)

Done: the realizer (`scripts/ap_realize.py`: windows shaped in adjacent pairs and laid out from high entropy down;
strings built per block carrying regex literals, spelled in mixed case); two sound cuts in the encoding: the upper side
of a window's entropy (`dominance_cuts`: a low-entropy window has one dominant nibble) and regex counts tied to the
characters they need (`regex_requirements`); containment (run 111) holds after each (1,105/1,105). The fourth session's
items 1-2 were dropped (already implied; unsound) and its "real looseness" reading was premature (naive file). On
2826a9a5 the solver went from an evasion realizing at 8.63 (naive) / 5.97 / 2.75 to undecided at 300 s. Decided (user):
check 1b before the exact block model of overlapping windows. Next, in order:
1. **Read check 1b** (`run/112`, ~30 min, run by the user): certified / undecided / solver-evaded per file, split by
   budget vs file size; record in the script's comments and the mock. Go: >= 4 of the 13 covered certified. A no-go goes
   to the user with decision 7's options (3: lead with another use; then 2: a tighter learned baseline).
2. **Every solver evasion: realize it** (`realize` on `solutions/{defense}_{file}.npy`), re-extract, score, attribute by
   group. Where byte-entropy still carries a gap: the exact block model of overlapping windows (user's earlier choice,
   deferred); where strings or histogram do: the realizer repairs below.
3. Realizer repairs for check 2: knife-edge histogram splits (nudge byte counts by one to match the solver's sides);
   section contents aimed at the solver's section entropies; `drop_tail` honored.
4. Check 2 (>= 70% of solver evasions realize), check 3 (expert set; user decision on instrumenting their extractor),
   Table A'1 at pilot scale.

### Earlier: next steps (2026-10-30, fourth session: per-row entropy cuts built)

Done: per-row Gibbs cuts tying each new byte-entropy window (appended-tail and header) to at least its row's nibble
entropy (`row_cuts`, `ROW_REFS`, `boundary_references`); the header windows made exact in their row (binary indicator +
`reachable_rows`); the gap-attribution logic kept as functions in `scripts/ap_check1b.py` (`sides_of`, `score_of`,
`attribute`); 160 tests pass. **The hypothesis that these close the byte-entropy gap failed:** on 2826a9a5 the solver
still evades (raw 1.09 vs real 8.63), and attribution shows the gap is real looseness in byte-entropy and strings, not
realization — a row's entropy is bounded but the joint placement of appended nibbles across rows and columns is not.
Code uncommitted; ruff/mypy and a containment re-run still owed. Next, in order (each sound, each re-measured on
2826a9a5 by a single-file scratch solve + `attribute`):
1. **Per-row column caps on the append windows** (confirm whether `colsum - 2*newnib` is per-(row,column) or pooled;
   if pooled, cap `we[r][col]` by the appended nibble supply of that column). Likeliest cause of the remaining
   byte-entropy points.
2. **An aggregate chord lower bound on the appended tail as one distribution** (as the overlay has), so low per-window
   entropy and the high-entropy aggregate cannot both be claimed.
3. A piecewise lower bound for the overlay and section entropies (section entropies still free in [0, 8]).
4. **The realizer** (`realize(choice) -> bytes`): strings as printable runs with a literal per matched regex, window
   runs per entropy row, section names from the name search. Now ordered *after* the entropy tightening (2826a9a5's
   gap is looseness, not realization). Needed for check 2.
5. Re-run containment (`run/111`, ~8 min) after the encoding changes; then the full check 1b as `run/112` (~30 min,
   for the user). A no-go goes to the user with decision 7's options (3, then 2).
6. Check 2 (>= 70% of solver evasions realize), check 3 (expert set; user decision), Table A'1.

### Earlier: next steps (2026-10-30, after A' steps 1-3)

Done: the A' reading list (no threat to the computed-mapping claim; `docs/literature-Aprime-2026-10-27.md`); the battery
measured on the 10% detectors the solver uses (run 109: union with the toolkit, unconstrained 27/47, PV-seen 15/22,
PV-all 15/22); check 1 (run 110) **failed its hypothesis**: learned regions certify nothing (0/47, 0/22) except in the
circular case (PV from the same attacks, 15/15 wrong). Decided (user, 2026-10-30): re-aim Table A'1 to "learned and
budget-only regions are vacuous or circular; only the computed region certifies" and build the encoding; the problem,
the four options, and the reasoning are in `docs/direction-A-prime-mock.md`, decision 7. Next, in order:
1. Step 4, the edit-choice encoding (append and add-section first), **including the layout bytes an added section
   brings** (section-table entry, padding; run 109 showed PV flips on them). Test: a fixed choice reproduces
   re-extraction (not only the declared prediction).
2. Check 1b (decision 7): the computed region certifies at least 20% of the unconstrained model's detected files the
   battery does not evade. Bring a no-go to the user (decision 7's options 3, then 2).
3. Check 2 (>= 70% of solver evasions realize), check 3 (expert set; user decision), Table A'1.

### Earlier: next steps (2026-10-30, start of session)

Done (`docs/status.md`): runs 107, 105, 106 read. G7 holds on 2,000 files (73,063 edits); step 9's C4 rows as
hypothesised (test metrics within noise, routed rows unevaded by seen attacks, M_full rows by held-out ones); the
expert-set row as mocked (monotone AUC 0.844, TPR 29% at 1% FPR, 8 of 50 pilot malware detected). Two bugs in the
adaptive search found and fixed (run 108; steps written by our own byte-level edit, decided by the user; unmodeled
pefile-warning features no longer NaN): unconstrained 4/49, PV 16/22, C4 rows 0; declared equals real. Next, the A'
pilot, in order (steps 1-3 cheap and each can stop the direction; bring any no-go to the user):
1. Reading list, harsh read: HRAT (`papers/HRAT2021.pdf`), Demontis et al. TDSC 2017, Šrndić & Laskov S&P 2014, arXiv
   2402.14988. Question for each: does it already compute edit-to-feature effects for an extractor of EMBER's kind
   (hashing, normalization, ratios, entropy)? Record in `docs/literature-Aprime-2026-10-27.md`.
2. Refresh `docs/direction-A-prime-mock.md` (note at its top): the engine exists, so the pilot uses it, not the hand
   predictors; the battery's measured cells change (toolkit-v2 plus run 108, per-file union); the expert row's facts
   (8 detected pilot malware; its extractor is not instrumented). Show the user the changes.
3. Check 1: learned constraints (per-feature directions and largest change seen in the toolkit's outputs) in the
   check-0 solver (`scripts/ap_check0_solver.py`) on PV; go if it certifies at least a third of the files the battery
   evades.
4. Build the edit-choice encoding (C3; not built yet): append and add-section first (bytes and byte counts; number of
   sections, bucket and sign per name, size, byte mix); linear features from the item table, safe bounds for ratios,
   normalized histograms, entropy. Test: a fixed choice reproduces the engine's prediction.
5. Check 2: solver evasions on the unconstrained GBDT, written with our byte-level edits, re-extracted; go at >= 70%.
6. Check 3, the expert set (decision for the user then): instrument their extractor (recommended) or encode it by hand;
   judge on its 8 detected pilot files or add files from the 2,000-file set.
7. Table A'1 at pilot scale (a `run/` script if over ~10 min).

### Earlier: next steps (2026-10-29, fourth session)

Done (`docs/status.md`): run 104 read (G1 exact, training inputs unchanged; G7 found five rare layouts, one the check's
own error, four closed by extending the precondition check with plain-layout clauses, decided by the user); step 9's
code (the scripts on the engines, the hand rules and predictors as test oracles; the engine's add-section removes the
overlay); the expert-set extractor (checked against the authors' code; quirks patched; upstream-issues item 6).
Running overnight (user): runs 107, 105, 106. Next, in order:
1. Read run 107 (G7 and the derivation on the 2,000 files with the plain-layout clauses). Any violation: witness it and
   close it by a general rule; if the training inputs change, run 105 must be redone.
2. Read run 105 (step 9: the six C4 models retrained, Table A1's C4 rows re-run on the C1 engine) against runs 99-100.
3. Read run 106 (the expert-set row: monotone and unconstrained GBDTs on the 40 features, toolkit columns) and write it
   into `docs/direction-A-expert-set.md` and the Table A1 design doc, under M_add and M_full.
4. The A' pilot (`docs/direction-A-prime-mock.md`), after the reading list (HRAT, Demontis et al. TDSC 2017, Šrndić &
   Laskov, arXiv 2402.14988; harsh read).

### Earlier: next steps (2026-10-29, third session)

Done (`docs/status.md`): run 102 read (holds on 2,000 files); step 6, the catalogue checks (G7, run 103): four
findings closed by general rules, including the user's decision to declare a section added after the overlay and to
count every unclaimed run past the headers as body. Next, in order:
1. Read run 104 (user): the re-featurized 10% sums store, G1, the derivation, and G7 on the 2,000-file set.
2. Step 9: switch the scripts to the engines, keep the hand rules and predictors as test oracles; regenerate the
   training inputs (overlay_size dropped, security_virtual_address up under M_add), retrain the C4 models (sums store
   v2 and full store) and re-run Table A1's C4 rows (user-run `run/` scripts, as runs 99-100).
3. The expert-set row of Table A1 (decided 2026-10-29: re-implement the 40 features on pefile with the quirks
   patched; report under M_add and M_full); the A' pilot. Reading: HRAT (`papers/HRAT2021.pdf`), Demontis et al.
   TDSC 2017, Šrndić & Laskov, arXiv 2402.14988.

### Earlier: next steps (2026-10-29, second session)

Done (`docs/status.md`): step 8, the sums re-encodings as items and identity readouts; every C4 direction is derived
(the hand rules remain only as G3's oracle). Pilot: G1 for sums exact, G3 for sums equal to the hand rules on every
cell under the precondition, training inputs unchanged (run 102 steps 1-2). Next, in order:
1. Read run 102's 2,000-file steps (the user runs them): G1 for sums, G3 for sums, and whether the `*-pre*` training
   inputs still equal run 99's (if not: explain and witness each change, then retrain in step 9).
2. Step 6: the catalogue checks (G7): the declared changes of app/sec/imp/ext/shf/ren/rdb/rsg against re-extraction,
   with adversarial parameter choices.
3. Step 9: switch the scripts to the engines, keep the hand rules and predictors as test oracles; if step 6 moves a
   direction, retrain the affected C4 models and re-run Table A1's C4 rows (user-run `run/` scripts).
4. The expert-set row of Table A1; the A' pilot.

### Earlier: next steps (2026-10-29)

Done (`docs/status.md`): runs 99-100 read (derived C4 rows: accuracy within noise of the hand-rule models, M_full
slightly better; routed rows evaded by nothing on passing files under M_full; Table A1 re-run recorded in
`docs/direction-A-A1-design.md`); every remaining class-1 witness built (run 101; all covered by the derived
directions); the adaptive search's split by the precondition check. Next, in order (recommended and accepted by the
user, 2026-10-29: step 8 before step 6, since it is small and finishes the automation, and step 6 then checks the
whole set):
1. Step 8: the sums re-encodings in the engine (item filters and identity readouts over sums; checked against
   `SumsFeatureExtractor`: G1 for sums, G3 for sums). Until then `a_directions.py --derive --extractor sums` keeps the
   hand rules for the re-encoded groups other than merged imports.
2. Step 6: the catalogue checks (G7): the declared changes of app/sec/imp/ext/shf/ren/rdb/rsg against re-extraction,
   with adversarial parameter choices.
3. Step 9: switch the scripts to the engines, keep the hand rules and predictors as test oracles; if steps 6 or 8
   move a direction, retrain the affected C4 models and re-run Table A1's C4 rows (user-run `run/` scripts).
4. The expert-set row of Table A1; the A' pilot.

### Earlier: next steps (2026-10-28)

Done (`docs/status.md`): per-structure locating ranges (runs 95-96); the C4 engine and `a_directions.py --derive`
(run 97: precondition variant = hand rules but for three explained features; strict variant degenerate); signature
witness (run 98). Next, in order:
1. **Decided (user):** failing files go to the unconstrained detector (coverage reported); >4 MB files stay; the
   strict detector is one sentence. The user runs `run/99` (retraining) and `run/100` (Table A1's toolkit columns with
   routed C4 rows); read them when done.
2. The remaining G3 witnesses: entry_name_hash under sec (entry point outside every section), Rich under ext and
   under hdr (a file without a Rich header), exports and relocations past the end.
3. Step 8 (sums re-encodings in the engine), step 6 (catalogue checks, G7), the expert-set row, the A' pilot.

### Earlier: next steps at the end of 2026-10-27 (fourth session)

Done in the fourth session (`docs/status.md`): found that appending can complete structures past the end of the file
(signature witness: `num_certs` 0 -> 1 on a truncated pilot malware file; the hand rules say authenticode only falls,
13-16% of the M_full C4 models' gain); decided strict directions plus a precondition row (user; keep complexity
down, the >4 MB exclusion is an option for later); fixed pefile's directory-parser crashes with one rule and
re-featurized the 394 affected stored files (run 94).

Next (in order, unless the user decides otherwise):
1. **Step 7, the C4 engine** (`reach.py`; `scripts/a_directions.py --derive`). First split `pe_locating` into
   per-structure locating ranges (now sound, since a directory crash no longer spreads; re-run G5 at the item level:
   a header flip that changes an item must lie in that item's members or locating ranges). Then the sign envelopes
   over the readouts (kind vocabulary checked on every recorded item; hash images by enumeration), unions per threat
   model, the output shape of run 76's `directions.csv`, and the disagreement report (G3) with witnesses: the
   signature case (rebuild this session's scratch witness as a script), `overlay_size` (run 88), then exports,
   relocation flags, entry name hash. Operations other than append and add_section: provisional deltas from the
   design doc until step 6.
2. **The precondition row**: the check "no locating range past the end of the file", a fallback detector of
   always-safe features, both as `run/` scripts for the user along with the retraining of the C4 models and the
   re-run of Table A1's C4 rows (toolkit part ~47 min). Keep it to one row and one sentence in the paper.
3. **Step 6, the catalogue**, from our own edit functions (`scripts/a1_adaptive.py`); the insertions last.
4. Then the expert-set row and the A' pilot (checks 1-3).

### Earlier: next steps at the end of 2026-10-27 (third session)

Done in the third session: **derivation steps 1-5, every check passing** (`docs/item-layer-design.md`, "Build status").
The item layer (`src/provexp/items.py`), the emitters and readouts for every EMBER group (pure additions to
`features.py`), locating ranges, and the C1 engine (`src/provexp/reach.py`) with per-group recognizers. G1 (bit-exact
on 100 + 2,000 files), G2 (projection = provenance), G5 (header byte flips), G4 (Table A0 reproduced, bit-equal to the
hand predictors), G6 (random in-place writes) all pass; G5 and G6 each needed one fix round (pefile rules found by the
checks themselves) and were confirmed on fresh files. Runs 90-93. Found: a pefile crash on a malformed debug directory
makes the extractor treat the file as not a PE (`docs/upstream-issues.md` item 5; not patched, recorded soundly).

Not done: step 6 (the edit catalogue: the remaining operations, their parameter domains, G7). The session's response
was stopped by the safety classifier while it read the attack toolkit's transformation code for the new A0 rows.

Next (in order, unless the user decides otherwise):
1. **Step 7, the C4 engine** (does not need step 6; add_section is already declared): sign envelopes over the
   readouts, the disagreement report against `scripts/a_directions.py` with witnesses (overlay_size first), then the
   user-run retraining of the C4 models and re-run of Table A1's C4 rows.
2. **Step 6, the catalogue**, built from our own edit functions (`scripts/a1_adaptive.py`) and the engine, framed as
   validating the feature model against re-extraction; the extend/shift insertions last.
3. Then, unchanged: the expert-set row, the A' pilot (checks 1-3), later items (cost column, adversarial training,
   second toolkit, leave-one-out PV, scale).
4. Optional speed-up if A' needs it: in-place predictions re-count the whole-file byte run (about one extraction on
   large files); adjusting only the written bytes' counts would make them local.

### Earlier: next steps at the end of 2026-10-27 (second session)

Done in the second session of 2026-10-27:
- **A' mock** (`docs/direction-A-prime-mock.md`): written by another session from a task prompt, then revised after
  review. Fixed: the "certificate" of our own C4 detector was circular (now a sanity check); battery cells use Table
  A1's measured numbers; the solver searches over *edit choices*, so every evasion is a concrete edit; Chen et al.
  (USENIX Sec 2020, PDF: edit -> over-approximated feature region -> verification) is the closest precedent and the
  novelty is stated against it; the main baseline is constraints learned from the toolkit attacks (predicted to give
  wrong certificates on PV), not Simonetto's constraints translated by hand; Gimenez et al.'s expert-set detector is
  the strongest row. **The user accepted all six recommendations:** lead with Table A'1 (realizable worst-case
  evaluation); solver over edit choices; rows unconstrained, PV-seen, PV-all, expert set, later adversarially trained
  (C4 as sanity check); report certified and realized numbers; Kantchelian's encoding first; checks 0-2 on the hand
  predictors, flagged.
- **A' check 0: go** (run 89, `scripts/ap_check0_solver.py`). Kantchelian's encoding with HiGHS via scipy, decision
  version: exact on all 25 (detector, file) pairs; every solve decided in <= 34 s on the 500-tree model. Finding:
  **directions alone certify nothing** on a non-monotone detector (all evadable in feature space even under M_add),
  so A'1's region needs C3's magnitude bounds within the byte budget; the edit-choice formulation gives them, and the
  learned-constraints baseline needs magnitudes too. An L0 stand-in (K = 1, 3) gives real proofs in 13-34 s.
- **Overlay gap settled** (run 88, `scripts/a_overlay_witness.py`): appending lowers `section:overlay_size` on 8 of
  100 pilot files; the `body_*` sums never drop (190 appends), because `sums.body_regions` clips overrunning sections
  at EOF. 7 of the 11 overrun files are cut at the dataset's 4 MB cap. Decision (user): pefile's rule is real
  behavior, no patch; only `overlay_size` becomes two-sided under appending, applied with the next C4 retraining.
- **Design doc decisions settled:** the five open decisions of `docs/item-layer-design.md` (see its end).
- **Order (user):** the derivation steps are done together, in order, not interleaved with other work.

Next:
1. **Derivation steps 1-6 in one stretch** (`docs/item-layer-design.md`, "Build order"): item table and readouts as
   data (1-3; checks G1 exactness on the pilot and on the 2,000-file set, G2 projection to today's provenance), locating
   ranges (4, G5), the C1 engine (5, G4: reproduce Table A0), the edit catalogue with parameter domains (6, G7). Natural
   stopping points: after step 3 (G1/G2) and after step 5 (G4). The effort table is in human days and far too high.
2. **Step 7, the C4 engine**, with the disagreement report against `scripts/a_directions.py` (the overlay case is the
   first expected disagreement, with its witness), then retrain the C4 models and re-run Table A1's C4 rows
   (`run/` scripts for the user; the toolkit part takes ~47 min).
3. **The expert-set row** (`docs/direction-A-expert-set.md`): re-implement Gimenez et al.'s 40 features on pefile,
   confirm the per-name overwrite reading on one file, patch quirks as pure additions, featurize the 10% store,
   train the monotone GBDT, run the A1 protocol under M_full and M_add. Also a row of Table A'1.
4. **A' pilot:** checks 1-3 of the mock (learned constraints with magnitudes on PV; realization of the solver's
   edit choices for append and add-section; the expert-set detector under computed M_full constraints).
5. Later, unchanged: cost column (after the derivation), adversarial-training row, second toolkit, leave-one-out PV,
   scale (user's decision).

### Earlier: next steps at the end of 2026-10-27 (first session)


Done on 2026-10-27:
- **Second application chosen: A'** (user agreed; B and C set aside for now: B's edge is narrow and drifts toward
  legibility, C's score-disagreement baseline is strong). A' literature read: `docs/literature-Aprime-2026-10-27.md`.
  Harsh read: the only new part is side effects and reachable constraints *computed from the extractor*; the attack,
  constrained-feature-space frameworks (Simonetto, Sheatsley, Bostani), and hash-bucket targeting (Rosenberg) are prior
  work. Strongest uses are probably evaluative/defensive (exact realizable worst-case evaluation; realizable
  examples for adversarial training, as in Bostani et al.'s Level Up), not attacks on undefended models.
- **Direction A's derivation is not yet automatic** (found this session): the C4 directions are hand-written per-group
  rules (`scripts/a_directions.py`) and the C1 predictors hand-coded per edit. Both A's novelty claim and A' rest on
  the automatic version. Design: `docs/item-layer-design.md` (item table, readouts as data, edit catalogue, C1/C4
  engines, checks G1-G7, build steps 1-9). The user approved pursuing it. Its effort estimate (14-19 working days) is
  in human days and far too high (user); expect a handful of sessions, bounded by the checks.
- **Soundness gap in Table A1 confirmed:** pefile ignores extents past EOF when locating the overlay, so appending can
  lower `section:overlay_size` (4 of 5 testable pilot files with a section past EOF, all malware). The M_full C4 rows
  constrain it up-only (0.9% / 0.25% of gain). The `body_*` sums (10.7% of the sums row's gain) may be affected too;
  not yet witnessed. Fix pending (design doc, open decision 2).
- **Expert-set row:** Gimenez et al.'s 40 features come from their own LIEF extractor (list from their code), not
  EMBER: `docs/direction-A-expert-set.md`. User decision: re-implement them (on pefile); report under our M_full as the
  priority and their add-only threat model for context. Reading their code suggests 12 of 40 features are lowerable
  under M_full and 23 more under M_add through per-name overwrite quirks (to confirm on one file; per the rules the
  row runs on a quirk-patched variant).
- **Cost column:** deferred until the derivation is automatic (today our side is "2 s plus hand-written rules"). PV's
  side: run 78, 398 attack runs on 50 files, ~12 min on 12 workers; toolkit columns (run 86) 2,088 runs in 47 min on 32
  workers.

Next:
1. **A' mock** (`docs/direction-A-prime-mock.md`), modeled on `docs/direction-A-mock.md`; bring it to the user before
   any A' code. Not yet written (the safety classifier stopped the draft on 2026-10-27; the user may have it produced
   by another session from the task prompt in `docs/resume-prompt.md`). Review it against the literature notes.
2. **Decide the design doc's open decisions with the user** (`docs/item-layer-design.md`, end): mirrors in
   `features.py`; strict vs precondition row for the overlay gap (and whether it is a pefile quirk to patch or real
   behavior); re-run A1's C4 rows now; G1 on 2,000 files; the syntactic regex test.
3. **Build the derivation, steps 1-3 first** (item table and readouts; checks G1/G2), which both A and A' need; the
   mock decides whether step 5 (C1 engine) or step 7 (C4 engine) comes next.
4. **Expert-set row:** re-implement the 40 features, confirm the quirk reading on one file, patch, featurize the 10%
   store (`run/` script for the user if > 10 min), train the monotone GBDT, run the A1 protocol under M_full and M_add.
5. Later, unchanged: adversarial-training row, second toolkit, leave-one-out PV, scale (user's decision).

### Earlier: next steps at the end of 2026-10-26

Done on 2026-10-26: **direction A is complete at pilot scale; Tables A1 and A2 are done** (assessment:
`docs/direction-A-summary.md`; tables: `docs/direction-A-A1-design.md`, "Result: Table A1/A2"). Every go/no-go check and
falsifiable outcome passed. 10% subsample, seed 0, 50 pilot malware, M_full, 1% FPR:
- **Table A1:** the four C4 rows are never moved by any attack (seen, held-out, adaptive; largest score change
  exactly 0.0). The M_full rows keep 86.7% (features) / 88.6% (sums) TPR vs 93.5% unconstrained and still detect
  40-41/50 pilot malware after every attack (unconstrained 20/50). PV from 4 (seen) or all 8 toolkit attacks holds
  against the toolkit but costs ~35 TPR points (56.2% / 53.8%) and is evaded by the adaptive search on 21/22 and 22/22
  (19-20/22 on real re-extraction): adding attacks does not close PV's hole.
- **Table A2:** the C1-guided search needs 24-42 queries and 3-4.5 extractions per file (toolkit: ~100 each);
  provenance-chosen section names (inverted section hash) take PV-seen from 11/22 (random names, run 87) to 21/22.
  On the unconstrained model, GAMMA API (adds imports; our search does not) is stronger (24/47 vs 14/47): context.
- **Fixes along the way:** secml-malware's shift attacks overwrite the MZ header on files whose first section has raw
  offset 0 (harness now counts non-PE outputs invalid; `docs/upstream-issues.md` item 4); the adaptive search
  materialized a random edit instead of the chosen one (fixed; plus targeted names, matched section props, the
  toolkit byte budget, and the real re-extracted score beside the declared one).
- Runs 83-87 (`run/`). Scripts: `scripts/a1_evaluate.py` (toolkit columns), `scripts/a1_adaptive.py` (adaptive search).

Next (agreed with the user 2026-10-26):
1. **Screen the second application on paper, three candidates side by side:** A' (realizing feature-space attacks in
   the problem space; see Directions), B, and C. For each: screening criteria, a mock of its paper table with the
   model component behind each column, a falsifiable go/no-go check, and a harsh read of the closest work on the same
   task. No code before a candidate passes; bring the mocks to the user.
2. **In parallel, the two cheap direction-A items that matter for novelty:** the expert-set row (Gimenez et al.'s 40
   hand-picked features: needs the paper, arXiv 2508.10038, in `papers/` or fetched with the user's OK; write out
   the mapping onto thrember v3 names for the user to check before training) and the cost-to-derive column
   (bookkeeping from run 78's attack runs vs one pass over the extractor).
3. **Later, on the user's decision (with the scale-up):** adversarial-training baseline row; held-out attacks from a
   second toolkit (MAB-Malware / Labaca-Castro et al.); leave-one-out PV (8 models); seeds 0-2 and full splits.
4. **Deferred:** the framework/theory section of the paper (waits until the applications are known; no manuscript
   edits before they survive screening); the Rich-header and import-adding C1 predictors (not needed for A1's claim).

### Earlier: Table A1 machinery (2026-10-24)
Sums re-encoding (`SumsFeatureExtractor`, 3,655 features; run 80: 10% store in 0.90 h), PV seen/held-out
(`a_pv_hole.py --tag`), the toolkit harness, and the C1-declared adaptive search were built; the five A1 decisions
are at the end of `docs/direction-A-A1-design.md`.

### Earlier: all three go/no-go checks for direction A passed (end of 2026-10-23)
- **Attack environment (no separate venv):** secml 0.15.6 + secml-malware 0.4.2 vendored under `third_party/` and
  patched to run in `env/` (Python 3.14, NumPy 2, LIEF 1.0); nothing broke because of Python 3.14 itself. All eight of
  Gimenez et al.'s black-box attacks run against our GBDT. Deps added to `requirements.txt`; see `third_party/README.md`.
- **Check 3 (run 77, accuracy):** sound monotone GBDTs keep most detection — test AUC 0.9957 / TPR@1%FPR 92.1% under
  M_add, 0.9930 / 87.4% under M_full, vs 0.9976 / 95.6% unconstrained. Better than predicted (`direction-A-threat-model.md` S4).
- **Check 2 (run 78, PV's hole): decisive GO.** Of the 1,736 features PV selection keeps (reproduction AUC 0.945 ≈
  Gimenez 0.938), 213 are C4-decreasable under M_full and carry **37.8% of the PV GBDT's split gain** — signed section
  buckets and string regexes, as hypothesised. The C4-sound GBDT (0.993) also beats PV on accuracy (S5).
- **Check 1 (run 79, Table A0): GO.** C1 predicts re-extraction exactly for the two non-structural classes wherever
  A1–A4 hold — append 89/89 A2-applicable, dos_overwrite 100/100; add-section predicts the declared count delta
  (NumberOfSections +1 on all 100) while SizeOfImage and the quantitative features are LIEF layout (A4), as the model
  says (S6).
- **A1 design drafted:** `docs/direction-A-A1-design.md` (rows/columns, one evasion protocol, the C1-guided adaptive
  attack, build order, falsifiable outcomes, five open decisions).

## Settled decisions (2026-10-22)

- The flat-P vs. richer-model question: a richer model is needed for A; the three-layer model is adopted as the
  working design (the "P + R" two-model version was rejected as vague).
- An item is the unit the extractor sums over, declared per feature (user agreed).
- Bytes and items are both kept: bytes are the interface, items the exact computation.
- Claim scope: whatever yields the strongest outcome; working answer: exact for content and item-creating edits,
  bounds through the readout, structural edits flagged, plus a measured coverage of real attacks.
- No need to engage database-theory provenance (semirings, aggregate provenance) beyond citation (user).
- "Feature provenance" is the name.
- No result rests on an implementation quirk of the extractor (user, 2026-10-22): quirks are patched by pure
  additions and every row, baselines included, runs on the patched variant; upstream reports in
  `docs/upstream-issues.md`.
- Coverage on paper (model doc, Section 6): of 34 transformations in secml-malware, Labaca-Castro et al., and
  MAB-Malware, 56% are content or item-creating edits, 38% structural with a delta the transformation declares, 6%
  (UPX) undeclared. **Adopted:** C1 covers declared structural edits, and "move" is a fourth item operation; with
  them 32/34 are exact or bounded. Coverage must still be weighted by attack success (UPX is the strongest in
  Labaca-Castro et al.).

## Assets carried over

The instrumented EMBER v3 extractor (`src/provexp/featuresets/ember2024/features.py`, exact feature reproduction,
~2x faster byte counts), `provexp` boxmatrix/provenance code, SimpleDB and feature store, trained GBDT and MalConv,
loader-safe edit rules and pools (`featuresets/ember2024/ablation.py`), the attack and audit scripts, the experimental
data under `artifacts/`. The item layer is implicit in the instrumentation today (`Contributions.add_item`); making it
explicit is the first engineering step once the plan is settled.

## Literature

`docs/literature-2026-10-22.md` (summaries of the papers read on 2026-10-22, with what each means for A, B, C);
`docs/literature-Aprime-2026-10-27.md` (the closest work on the A' task, and a harsh read).
`docs/related_work.md` is the old direction's survey (still useful for malware XAI and G-DeepSHAP).
