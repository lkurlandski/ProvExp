# Direction A': mock of the paper's tables (2026-10-27)

**Refreshed 2026-10-30 (A' pilot, steps 1-3).** What changed since the first draft:
- The C1 and C4 engines exist (derivation steps 1-9), so the pilot uses the engine; decision 6's hand predictors are
  no longer needed. C3 (the edit-choice encoding with magnitude bounds) is described in the model but not built.
- **One set of detectors throughout:** the 10%-subsample GBDTs (`seed-0-s10-ref`, `-s10-pv-seen`, `-s10-pv-all`),
  which the toolkit columns (run 105, `artifacts/experiments/a1/toolkit-v2`) and check 0 (run 89) already use. The
  adaptive search was re-run on them (run 109); run 108's numbers are for the full-data models and are not mixed in.
- **The battery is measured** (per-file union of the eight toolkit attacks and the adaptive search, real re-extracted
  evasions only): unconstrained 27/47, PV-seen 15/22, PV-all 15/22.
- **Check 1 failed its hypothesis** (run 110): learned regions give wrong certificates only in the circular case, and
  certify nothing otherwise. Table A'1's contrast is re-aimed accordingly (decision 7, below); the first draft's
  "learned constraints give unsound certificates" reading is withdrawn.
- **The declared add-section leaves out layout bytes** (the section-table entry and padding; A4). Run 109 found three
  declared evasions on the PV models that do not hold on the written file (a split on byte-histogram bins the header
  entry moves). The solver's encoding (step 4) must include those bytes.
- The literature read for A' is complete (`docs/literature-Aprime-2026-10-27.md`): no threat to the computed-mapping
  claim; HRAT means "edit an intermediate structure, not the features" must not be claimed.
- Expert set: the monotone model measured AUC 0.844, TPR 29% at 1% FPR, detects 8 of the 50 pilot malware, evaded by no
  toolkit attack there; its extractor is not instrumented, so the engine cannot feed the solver for that row yet.

First draft written by a separate session from the task prompt in `docs/resume-prompt.md`; revised the same day after
review: the "independent certificate" of our own detector was circular; the battery numbers contradicted Table A1; the
step from a solver's answer to a real file was missing; Chen et al. (USENIX Security 2020) was missing; and the solver's
tractability was not checked first.

Numbers marked *(measured)* come from Table A1/A2 (`docs/direction-A-A1-design.md`). All other numbers are
**invented** to show the shape of the result; nothing for A' has been run. Modeled on `docs/direction-A-mock.md`.
Each column names the model component (`docs/feature-provenance-model.md`, claims C1-C4) that produces it, and the
go/no-go checks at the end say what would sink the direction. The protocol matches direction A: pilot scale (10%
subsample, seed 0, the 50 pilot malware), threat model M_full (`docs/direction-A-threat-model.md` Section 1: add,
append, overwrite, and shift edits that keep the file loadable), the detection threshold at 1% FPR, and the same
GBDT detectors.

A' is the flip side of A. A takes a threat model and asks which features it can move, so that it can *build* a sound
detector. A' takes the same threat model and asks an *evaluative* question: given any detector, what is its true
worst case against file edits an attacker can actually make? Its second use is hardening: does training on such
edits help? It measures detectors; it is not an attack tool.

## The pitch in plain terms

A practitioner who wants to know how robust a malware detector really is has four options today. Each falls short in
a different way:

1. **Run a battery of problem-space attacks** (GAMMA, MAB-Malware, the nine attacks Zainab et al. benchmark, our own
   C1-guided search). Every evasion found is real, so this gives a sound *lower bound*. But you never learn what the
   battery missed, and each toolkit attack costs ~100 re-extractions per file.
2. **Verify the detector in feature space** with an exact solver for tree ensembles (Kantchelian et al.'s
   mixed-integer program, or the verifiable-boosted-tree method). Given a region of feature vectors, this proves
   whether any of them evades: an *upper bound* on evasion. With only a size budget as the region, though, it counts
   vectors no file can produce (a negative count, a histogram that does not sum to one), so it reports almost every
   file as evadable. The bound is true but useless.
3. **Give the solver constraints written by hand or learned from data** (Simonetto et al.: 88 immutable features and
   7 relations for their PE feature set; Sheatsley et al. and Bostani et al. learn constraints from data). Hand
   constraints for a real extractor's 2,568 features, including the hashed and aggregate ones Severi et al. excluded
   outright, have not been written by anyone. Learned constraints only contain the changes the training attacks
   happened to make, and they lose how features move together (one edit changes many features at once, in fixed
   relationships); check 1 measured that they certify nothing or, where they certify, only by construction.
4. **Do what Chen et al. did for PDF** (USENIX Security 2020): map each file edit to an over-approximated set of
   feature vectors, then verify the detector against that set. This is exactly the right recipe, and it is the
   closest prior work on the same task. It was easy for them because their PDF features *are* paths in the file's
   object tree, so an edit's feature effect can be read off directly. For an extractor like EMBER, which hashes
   names, normalizes histograms, divides by the file size, and takes entropies, no such mapping exists.

A' supplies that mapping, computed from the instrumented extractor: for each edit in the threat model, which totals it
adds to and how each feature's formula turns those totals into feature values (C1 for one edit, C3 for any
combination of edits within a budget). The solver then searches over *edits*, not over feature vectors (Section
"How a solver's answer becomes a file"), so every evasion it reports comes with the edits that produce it, and
re-extraction confirms it. The only new part is the computed mapping. The attack idea, the exact solver, the
constrained-verification recipe (Chen et al.), the hash-bucket trick (Rosenberg et al.), and the constraint-framework
idea are all prior work (`docs/literature-Aprime-2026-10-27.md`).

**The security task, stated once.** Trustworthy robustness evaluation (and, second, hardening) of a malware detector
against evasion by edits an attacker can actually make. The realistic alternatives are options 1-3; option 4 is the
precedent we generalize. Only feature provenance makes the mapping cheap for an extractor of EMBER's kind: for every
feature, computed rather than written, and checked against re-extraction.

## How a solver's answer becomes a file

This is the hardest step of A', and it decides what the table can claim.

- **Over feature vectors (the obvious design, not recommended).** The solver picks a target feature vector inside the
  reachable region (C4's directions plus C3's per-feature ranges). But C1 goes the other way, from an edit to its
  features, and C3's region is loosened (counts relaxed to real numbers, ranges per item kind), so a point inside it
  need not come from any edit. Turning the target into a file then needs a separate search, which may fail, and a
  failure says nothing about whether the file was evadable.
- **Over edit choices (recommended).** The solver's variables are the attacker's choices in the edit catalogue:
  - how many sections to add, the hash bucket and sign each new name hits, and each section's size and byte mix;
  - how many bytes to append, and with what byte counts;
  - which header bytes to overwrite, and with what;
  - which imports to add, by bucket.

  Each feature is then computed from those choices. Sums, counts, and hash buckets are linear in the choices (C1:
  old totals plus what the added items contribute). Ratios, normalized histograms, and entropies are not linear, and
  are bounded soundly (C3, step 3: the mixing polytope for histograms, interval bounds for entropy). A tree's split
  on a linear feature becomes a linear constraint. A split on a bounded nonlinear feature is allowed whenever the
  bound permits it, which is what keeps the upper bound sound.
- **What each answer then means.** If the solver finds no evasion, no edit in the catalogue evades within the budget:
  a certificate. If it finds one, the answer *is* a list of edit choices. Materialize it (names through the inverted
  section hash as in Table A2, bytes with the chosen counts), re-extract, and keep it if the real file still evades.
  Only the nonlinear features can make a solver evasion fail to realize, and the gap between "certified evadable"
  and "realized" measures how loose those bounds are (check 2).

## Table A'1: realizable worst-case robustness (main result)

For each detector, the fraction of the pilot malware it detects for which some edit in M_full within the byte budget
evades it. The columns go from the loosest answer to ours. Protocol as Table A1: M_full, 1% FPR, byte cap max(5% of
file size, 512 KB).

| Detector | Attack battery: toolkit + our search (lower bound) | Solver, budget only | Solver, constraints learned from the toolkit | **Solver, computed (ours): certified / realized** | Solve time / file |
|---|---|---|---|---|---|
| Unconstrained GBDT | 57% (27/47) *(measured)* | 100% | 100% *(measured)* | **70% / 62%** | 4 min |
| PV, 4 seen attacks (Gimenez et al.) | 68% (15/22) *(measured)* | 100% | 100% *(measured)*; 0% if learned from its own 4 attacks† | **80% / 73%** | 3 min |
| PV, all 8 attacks | 68% (15/22) *(measured)* | 100% | 0% *(measured)*† | **80% / 73%** | 3 min |
| Expert set, monotone (Gimenez et al.'s 40 features) | 0/8 detected pilot files *(measured)* | 100% | — | **45% / 38%** | 1 min |
| C4 on sums (ours, from A): sanity check | 0% *(measured)* | 100% | 0% | 0% / 0% (by construction) | 1 min |

Detectors: the 10%-subsample GBDTs (runs 89, 105, 109, 110). "Learned" = each feature may move by up to the largest
decrease and increase the eight toolkit attacks produced on any pilot file (run 110). † Circular: PV built from attack
set S is monotone in exactly the features S never lowered, so a region learned from S certifies it by construction
(15 of 15 battery evasions certified as safe). All numbers outside the *(measured)* cells are invented. The shape to
read:

- **Learned regions are vacuous or circular** (measured, check 1). Learned from attacks other than the ones a defense
  was built from, they certify nothing (0/47, 0/22): pooled per-feature limits with no coupling between features are
  as loose as the byte budget alone. Learned from the same attacks, they certify PV on every file, wrongly on all 15
  the battery evades, which restates A's PV hole rather than adding to it. **The computed region must be the only one
  that certifies anything** on a non-monotone detector; that is untested until step 4 (decision 7).
- **Defended detectors built without our constraints are where A' says something new.** The expert-set row is the
  strongest case. Gimenez et al.'s detector is certified robust *under their own hand-written add-only threat model*.
  Under computed M_full constraints, the solver finds which of their assumptions fail (reading their code suggests 12
  of their 40 features can be lowered under M_full; `docs/direction-A-expert-set.md`), and the realized column shows
  real files that evade. Adversarially trained models (Table A'2) would be a further row of this kind.
- **The battery may understate the detectors** (57% found on the unconstrained one), and only the computed region
  says by how much. A' adds a certificate and the full count, not a stronger attack.
- **The C4-on-sums row is a sanity check, not evidence.** It is monotone in the same directions the solver uses, so
  0% is guaranteed. Its only value is catching a bug in the solver's encoding.

Components behind the columns:
- *Attack battery*: no model component; secml-malware's eight attacks plus the C1-guided adaptive search of Table A2,
  union per file (the measured cells are Table A1's "detected after every attack").
- *Solver, budget only*: the exact solver over the GBDT with only a box and the budget on the feature vector.
- *Solver, learned constraints*: the same solver, with each feature allowed to move by up to the largest decrease and
  increase the toolkit's adversarial outputs produced (Šrndić & Laskov's per-feature bounds; Bostani/Sheatsley-style
  learning). The realistic data-driven alternative (`scripts/ap_check1_learned.py`, run 110).
- *Solver, computed, certified*: the solver over edit choices, with features computed by C1 and nonlinear ones bounded
  by C3. Sound over the catalogue, so 0% here is a certificate against every edit in it.
- *Solver, computed, realized*: the certified evasions, materialized, re-extracted, and kept only if the real file
  still evades. A lower bound, tied to concrete files.
- *Solve time*: wall-clock per file, against ~100 re-extractions per file per toolkit attack. Check 0 decides whether
  it is minutes or hours.

Paper sentence this table must support (mock, re-aimed after check 1): "Constraints learned from attack outputs are
too loose to certify any file, because they lose how one edit moves many features together; where they do certify a
defense, it is only because the defense was built from the same attacks, and a cheap adaptive search evades it on 15
of 22. Computing the reachable set from the extractor keeps that coupling: it certifies files no other region can,
and every evasion the solver reports re-extracts as a real file. The same evaluation shows where a published certifiably robust detector's threat-model assumptions break under
a broader but realistic attacker."

## Table A'2: realizable examples for adversarial training (second use, not the main result)

The second use the literature names (Bostani et al.'s Level Up, for Android). Train the GBDT on the original data
plus the solver's realized evasions (or edits sampled from the catalogue, each realized and re-extracted), and
compare robustness and training cost against the alternatives a practitioner would use.

| Training | TPR @ 1% FPR (clean) | Held-out toolkit evasion | Solver worst case (Table A'1, realized) | Training cost |
|---|---|---|---|---|
| None (unconstrained) | 93.5% *(measured)* | 53% | 79% | none |
| Problem-space adversarial training (toolkit) | 92.0% | 15% | 60% | ~100 extractions per example |
| Feature-space, unrealistic perturbations | 90.1% | 44% | 75% | low (Dyrmishi et al.: barely helps) |
| **Realizable edits from the solver (ours)** | **92.6%** | **12%** | **35%** | one solve + one extraction per example |

All numbers invented except the measured TPR. Components: C1/C3 (the edits and their realizable feature vectors).
Baselines: problem-space adversarial training (the expensive realistic one) and unrealistic feature-space
adversarial training (the cheap one Dyrmishi et al. show fails). Level Up is the Android precedent; Chen et al. 2020
trained verifiably robust PDF classifiers with the same kind of region. The trained models become rows of Table A'1.

**Recommendation: lead with Table A'1.** It reuses A's detectors, needs no retraining for its main rows, and puts our
novelty exactly where the literature says it is: the computed mapping, fed to an off-the-shelf solver. Table A'2 is a
bigger lift (a training loop, retraining runs) and sits closer to Level Up and Chen et al.; keep it as the extension.

## Which part of the derivation A' needs first

A' rests on the automatic derivation in `docs/item-layer-design.md`. Today the directions (C4) are hand-written rules
(`scripts/a_directions.py`) and the side-effect predictors (C1) are hand-coded per edit (`scripts/a_c1_table0.py`,
`scripts/a1_adaptive.py`). The paper claim holds only once they are computed.

- **Steps 1-3 first** (the item table, the readouts as data, the exactness checks), as for A.
- **Then step 5, the C1 engine, extended to the edit-choice parameters (C3).** The solver over edit choices *is* this
  engine written as linear constraints, so it comes before the C4 engine. This reverses the first draft's order.
- **Step 7, the C4 engine, is needed only for the comparison with the hand rules and as a pre-filter** (features no
  edit can move drop out of the solver).

A pilot can start on today's hand-coded predictors (as Tables A1 and A2 did), clearly flagged, while the engine is
built. The paper's numbers wait for the engine.

## Realistic baselines (why these)

- **Attack battery** (secml-malware's eight attacks plus our C1-guided search; GAMMA and MAB-Malware are in it already
  or come with the second toolkit; Zainab et al.'s benchmark as the field's current state): what a practitioner runs
  today. A sound lower bound only.
- **Budget-only verification** (Kantchelian et al.; arXiv 2402.14988): included to show that the solver means nothing
  without a realistic region.
- **Constraints learned from attacks** (Sheatsley et al., Bostani et al.; Labaca-Castro et al.'s empirical
  probabilities): the realistic data-driven alternative to computing the constraints. It under-approximates, so its
  certificates can be wrong: the main falsifiable contrast.
- **Hand rules for EMBER** (our own `scripts/a_directions.py`, a careful expert's attempt over all 2,568 features).
  Not a column: computed and hand rules differ on few features (the overlay case is one), so the numbers would be
  close. The comparison is reported as a count of features whose direction differs, each with a witness file, which
  is the evidence that hand rules miss cases. Simonetto et al.'s constraints are for a different PE feature set;
  translating them onto EMBER by hand would be a strawman, so they are cited, not run.
- **Chen et al.** (USENIX Security 2020): the precedent for the recipe; not runnable on EMBER, which is the point.
- **Not a baseline:** Severi et al.'s 17 hand-picked features (cited as the clearest statement of the limitation A'
  lifts). Rosenberg et al.'s hash-bucket targeting is prior work and **must not be claimed** as ours.

## Go/no-go checks (falsifiable, before building anything)

Each is a short job on the pilot, on today's hand-coded predictors.

0. **The solver runs at our model's size.** Our GBDT has 500 trees of 64 leaves over 2,568 features. Run the
   budget-only exact solver on 5 pilot files with a 30-minute limit per file. This needs no provenance. *Go* if most
   files finish within the limit. *No-go:* switch to the verifiable-boosted-tree method, or report bounds from a
   time-limited solve (the solver's best bound is still sound), and bring it to the user before building anything
   else.
   **Result (run 89, 2026-10-27): go.** Kantchelian's encoding with HiGHS (through scipy, no new dependency;
   `scripts/ap_check0_solver.py`), decision version ("can the score go below the threshold?"), 5 detected pilot
   malware per detector:
   - the encoding reproduces the booster's score exactly on all 25 (detector, file) pairs;
   - every solve was decided within 34 s, on the largest model too (500 trees, 22,533 binaries, 32,000 leaves);
   - the C4 detectors are certified in 0.2 s, with no violation (they are monotone in the same directions; a check of
     the encoding, not evidence);
   - **directions alone certify nothing on a non-monotone detector**: under the M_full and even the M_add directions,
     all 15 (unconstrained, PV-seen, PV-all) are evadable in feature space, because a direction with no limit on
     magnitude lets a feature go anywhere on one side;
   - with a budget of at most K features changed, as a stand-in for a tight region, real proofs appear and stay
     fast: K = 1 certifies the unconstrained model on 5 of 5 (13-18 s) and PV-all on 1 of 5; K = 3 certifies the
     unconstrained model on 2 of 5 (23-34 s).

   Two consequences for the design. First, the computed region must bound *how far* each feature can move within the
   byte budget (C3), not only which way (C4); a directions-only column would read 100% for every non-monotone
   detector, like the budget-only one. The edit-choice formulation does this by construction. Second, the same holds
   for the learned-constraints baseline: its constraints need magnitudes too (the largest change the toolkit produced
   per feature), or check 1 is vacuous. Untested: proofs under the real edit-choice region, which has more structure
   (counts, buckets, histogram mixing) than an L0 budget; check 0 says the solver scale is not the obstacle.
1. **Learned constraints give wrong certificates.** Learn per-feature directions from the toolkit's adversarial
   outputs, run the solver on PV-seen, and compare with the battery's measured 21/22. *Go* if the learned-constraint
   solver certifies robust at least a third of the files the battery evades. *No-go:* if learned constraints already
   agree with the battery, data-driven constraints suffice for this use and the contrast with ours is thin; lead with
   the expert-set row or Table A'2 instead.
   **Result (run 110, 2026-10-30): hypothesis failed, in an unexpected direction.** The learned region is too loose,
   not too narrow. Learned from all eight attacks (2,014 features free), it certifies 0/22 on PV-seen and 0/47 on the
   unconstrained model; the solver finds a feature-space evasion for every file, in under 10 s. Wrong certificates
   appear only where the region is learned from the attacks the PV detector was built from (15/15 battery evasions
   certified), which holds by construction. Neither outcome the check anticipated occurred: the learned region does
   not agree with the battery, and it does not give wrong certificates outside the circular case. See decision 7.
2. **The solver's evasions realize.** On the unconstrained GBDT, encode the append and add-section edits as solver
   choices (the two edits with exact C1 predictors in Table A0), materialize each evasion, and re-extract. *Go* if at
   least 70% still evade. *No-go:* the nonlinear bounds are too loose; tighten them (C3 step 3) before calling the
   result realizable.
1b. **The computed region certifies** (added by decision 7, 2026-10-30, after check 1). Once append and add-section
   are in the solver (step 4, layout bytes included), on the unconstrained GBDT: *go* if the computed region certifies
   at least 20% of the files it detects that the battery does not evade (20 of 47 at pilot scale). *No-go:* the
   region is as loose as the learned one; A' is then a realizable lower bound only; revisit decision 7's options.
   **Smoke run (2026-10-30, third session; 300 s per solve, not the verdict):** of the 20 files, 7 fail the
   precondition (no certificate possible; at most 13 can be certified, so the go needs 4 of 13); 0 certified, 10
   undecided, 3 encoded evasions, of which the two append-only ones do not realize when written naively (real 5.0-9.2,
   threshold 1.1). Diagnosis: byte-entropy windows are loose; strings need a realizer that writes the chosen strings.
   **Tightening, first result (2026-10-30, fourth session):** per-row entropy cuts added for the new and header
   windows (`docs/direction-A-prime-encoding.md`, "Built: findings", fourth session); the hypothesis that they close
   the byte-entropy gap **failed**. On 2826a9a5 the solver still evades (raw 1.09 vs real 8.63); attribution shows the
   gap is real looseness (byte-entropy and strings), not a realization gap: tying each row's entropy down does not tie
   the joint placement of appended nibbles across rows and columns. *(Corrected in the fifth session: that comparison
   was with a naively written file, so it could not separate looseness from realization.)*
   **Tightening, second result (2026-10-30, fifth session):** a realizer that lays the solver's windows and strings out
   (`scripts/ap_realize.py`) and two sound cuts (a low-entropy window has one dominant nibble; regex counts need their
   characters). On 2826a9a5 the solver's answers realized at 5.97, then 2.75 (threshold 1.10), and after the second
   cut the solver found no evasion in 300 s. Smoke at 60 s on 7 covered files: all undecided, none evaded.
   **Result (`run/112`, 1,800 s per solve; read 2026-10-31): no-go.** Of the 13 covered files: 0 certified, 6 solver
   evasions (269-576 s; 2826a9a5 among them at 507 s), 7 undecided. The hypothesis (fewer evasions than the smoke's 3)
   failed. Written as files, **0 of 6 evade** (real raw 3.40-6.76 vs the solver's 0.77-1.10; threshold 1.10), so the
   evasions are artifacts of looseness or of the realizer, not attacks. The gap is spread: with one group's splits on
   the solver's sides, byte-entropy alone reaches 1.96-5.37, strings 2.15-4.50, section entropies 3.27-5.65; none
   reaches the threshold alone. Revisit decision 7 (with the user).
3. **The computed constraints matter on a defended detector built without them.** On the expert-set detector (once
   its row exists), the computed-constraint solver must find realized evasions on a material share (say 10% or more)
   of the files it detects. *No-go:* if their hand-written add-only assumptions already hold under M_full, the
   defended-detector story rests on PV alone; report it and weigh Table A'2.

Hypothesis for check 2: most evasions realize, because append and add-section mostly move linear features (counts,
buckets); failures concentrate where an evasion relies on a histogram or entropy feature.

**The overlay case** (`docs/item-layer-design.md`, "First row confirmed"): pefile ignores section data that runs past
the end of the file when it locates the overlay, so appending can lower `section:overlay_size` (8 pilot files; 7 of
the 11 overrun files are cut at the dataset's 4 MB cap). The `body_*` sums are not affected (checked on all 100 pilot
files). The constraints treat `overlay_size` as able to move both ways under appending. This is the extractor's
real behavior, not a bug to patch. It is one of the features where computed and hand rules differ, with a witness.

## Harsh notes on novelty

- **One thing is new:** the mapping from edits to feature values, computed from the extractor for every feature and
  checked against re-extraction. The attack, the exact solver (Kantchelian), constrained verification of a malware
  detector (Chen et al. 2020, for PDF), the constraint framework (Simonetto, Sheatsley, Bostani), the hash-bucket trick
  (Rosenberg), and realizable adversarial training (Level Up) are prior work. The paper says so and claims only the
  mapping.
- **"Chen et al. already did this."** For an extractor whose features are tree paths, where the mapping is immediate.
  Our contribution is the mapping for an extractor with hashing, normalization, ratios, and entropy, which is what
  real PE detectors use. If a reviewer reads Chen et al. as having solved the general case, A' has no novelty, so the
  paper must show what makes EMBER different (the readout types) in its first page.
- **"Given the constraints, verification is solved; you just supply them."** Yes, and supplying them is the open
  problem: learned ones give wrong certificates (check 1), hand ones miss cases (the overlay witness), and nobody has
  written them for EMBER's 2,568 features.
- **Only real once the derivation is automatic.** Until steps 1-3 and 5 of `docs/item-layer-design.md` exist, A' is
  "a solver with hand-coded edit predictors", the same critique A faces. The pilot may use them; the claim may not.
- **Against an undefended detector the result is mostly "very vulnerable"**, which the battery already shows. The
  value is on defended detectors built without our constraints (PV, the expert set, adversarially trained models).
  Our own C4 detector proves nothing here.
- **Our search already breaks PV.** For PV, A' adds the certificate and the contrast with learned constraints, not
  new evasions. Say so.
- **The certificate is only as wide as the catalogue.** "No edit in the catalogue evades" is not "no edit evades".
  The catalogue is the threat model (M_full), stated as such, as in A.
- **Tractability is unproven** (check 0). An engineering risk, not a novelty risk, but it can sink the main table.

## Decisions

The user accepted every recommendation below on 2026-10-27; they stand until the checks say otherwise.

1. **Which use leads the paper.** *Recommended: Table A'1 (exact evaluation); its contrast re-aimed by decision 7.* A'1 says "constraints learned from
   attacks certify a defense that a cheap search breaks; computed ones give certificates that hold and evasions that
   re-extract". A'2 says "training on realizable edits beats problem-space adversarial training at a fraction of the
   cost". A'1 reuses A's detectors; A'2 needs a training loop and is closer to Level Up and Chen et al.
2. **What the solver searches over.** *Recommended: edit choices* (how many sections, which bucket each name hits,
   how many bytes appended with what byte counts). Every evasion is then a concrete edit, and a failure to realize
   can only come from the nonlinear bounds. The alternative, searching over feature vectors, is simpler to encode but
   needs a separate search to find a file, and a failed search proves nothing.
3. **Which detectors are rows.** *Recommended: unconstrained, PV-seen, PV-all, the expert-set detector, and (with A'2)
   adversarially trained models; our C4 detector as a sanity check only.* The expert-set row depends on the
   expert-set re-implementation already planned for direction A.
4. **How to report the worst case.** *Recommended: both numbers* (certified evadable, realized), e.g. "79-88%".
   Tightening the nonlinear bounds to close the gap is more work and may not close much.
5. **Solver.** *Recommended: Kantchelian's mixed-integer program first*, with the verifiable-boosted-tree method as
   the fallback if check 0 fails.
6. **Pilot on today's hand-coded predictors, or wait for the engine.** *Recommended: run checks 0-2 now* on the hand
   predictors (check 0 needs none), clearly flagged; the paper's numbers come from the engine.
7. **After check 1 (user, 2026-10-30): re-aim Table A'1 and build the encoding.** Recorded in full so the choice can
   be revisited.

   *The problem.* The mock's main contrast was "learned constraints give wrong certificates; computed ones give
   correct ones". Check 1 (run 110) showed learned regions are vacuous instead. Two causes:
   - *pooling*: each feature's limit is the largest change seen on any file by any attack (one GAMMA run added ~400 KB
     of sections, so every file may grow by 400 KB);
   - *no coupling*: each feature moves independently, while a real edit moves many features together by tied amounts
     (appending zeros raises the size, raises the zero-byte share, and lowers every other share at once).

   The solver combines changes no single edit produces and beats every non-monotone detector. The only wrong
   certificates are circular (PV from attack set S, region learned from S) and restate direction A's PV hole. The
   reasoning error in the hypothesis: we assumed missing directions (too narrow) would dominate; missing coupling
   (too loose) dominates.

   *Options considered.*
   1. **Re-aim and build (chosen).** The contrast becomes "learned and budget-only regions are vacuous or circular;
      the computed region is the only one that certifies anything on a non-monotone detector, and its evasions
      realize". It rests on what provenance uniquely records: how one edit moves features together. New go/no-go
      after step 4 (append and add-section in the solver, layout bytes included): the computed region certifies at
      least 20% of the files the unconstrained model detects and the battery does not evade, and check 2's at least
      70% of solver evasions realize. Cost: the step-4 build before knowing. Risk: our region may also be loose
      (appending 5% of a file with chosen bytes moves the histogram; added sections steer the name buckets).
   2. **A tighter learned baseline first** (e.g., each feature's 95th-percentile change instead of the largest;
      ~1 min). It might give non-circular wrong certificates. Not chosen: adjusting a baseline until it fails risks a
      strawman; any per-feature box still lacks coupling, which is the actual argument. It stays available as a
      sensitivity row, reported whichever way it falls.
   3. **Lead A' with another use:** the expert-set row (does Gimenez et al.'s add-only certificate survive M_full?)
      or Table A'2 (training on realizable edits), with Table A'1 as support. Not chosen yet: both also need the
      encoding (the expert row needs its extractor instrumented as well), so step 4 comes first either way.
   4. **Pause A'** and spend the time on scaling A or the manuscript. Not chosen: check 0 showed tight regions do
      certify (an L0 budget of 1 feature certified the unconstrained model on 5/5 files), so the computed region has a
      real chance.

   *What each outcome of the new check means.* If the computed region certifies a material share, A' contributes the
   first worst-case robustness numbers for an EMBER-style detector that are both provable and tied to real files. If it
   certifies little, A' is a realizable worst-case lower bound (solver evasions that are exact edit lists and hold on
   real files), closer to "a better attack", which is weak against undefended detectors; then revisit options 3 and 2
   in that order.

   *Revisit this decision* if the step-4 go/no-go fails, or if a reviewer-facing argument needs a non-circular wrong
   certificate (then run option 2 as a sensitivity row).
