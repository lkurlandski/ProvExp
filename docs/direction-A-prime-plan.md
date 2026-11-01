# Direction A': the plan to complete it (adopted 2026-11-01)

Written after `run/113` (all 6 files undecided at 30 min) and **adopted by the user the same day** with the decisions
recorded in Section 7. Where this differs from `docs/direction-A-prime-mock.md`, this document wins; the mock keeps the
history (checks 0-2, 1b, decision 7, the re-evaluation). All numbers not marked *(measured)* are invented to show the
shape of the result.

## 1. What A' claims, in one paragraph

Malware detectors are evaluated against realistic edits by running attacks. That gives a lower bound on how
vulnerable a detector is, and says nothing about what the attacks missed. The alternative, verifying the detector in
feature space, says nothing useful either: with only a size budget, or with constraints learned from attack outputs,
the solver combines feature changes no file can produce and declares every file evadable (measured: checks 0 and 1).
**A' audits a detector by bracketing its worst case under a stated set of realistic edits.** For each file the
detector catches, the bracket is:

- **the ceiling**: the lowest score any real attack reached (the toolkit's eight attacks and our adaptive search, every
  evasion re-extracted from a real file). Below the threshold: the file is *evaded*.
- **the floor**: a proven lower bound on the lowest score *any* edit in the catalogue can reach, from an exact solver
  whose every feature is computed from the attacker's choices through provenance. Above the threshold: the file is
  *certified*.
- otherwise the file is **open**, and the gap between floor and ceiling says how much is unknown.

The claim: **only the computed region gives floors that are both sound and informative, and the brackets show which
hardening actually helps and where the usual shortcuts mislead.** Budget-only and learned regions give floors that are
vacuous (they certify nothing) or wrong (they certify files a real attack evades). That is something only feature
provenance makes cheap: the edits' effect on all 2,568 features, including hashed, normalized, ratio, and entropy
features, computed rather than written by hand, and checked against re-extraction.

What changes from the current mock:
- the headline is a **bracket per detector**, not "certified %"; open files are reported, not counted as failure;
- the rows are **hardened detectors**, not the undefended one (which stays as a reference row);
- the solver **minimizes the score** instead of answering yes/no, so a timeout still returns a proven floor;
- writing the solver's evasions as files is **dropped** (check 2): the ceiling comes from real attacks only;
- the expert-set row and Table A'2 as a standalone are **dropped** (user's doubts; see Decision 5).

## 2. Why this matters, and to whom

Defense papers for malware detectors (PV feature selection, adversarial training, monotone models) report robustness
as "the attacks we tried did not work". A reviewer cannot tell whether the defense is robust or the attacks were weak.
A bracket answers that: a certified file is robust against *every* edit in the catalogue, and an open file is honestly
marked as unknown. The audience is anyone who proposes or deploys a hardened detector and has to say how robust it is.

## 3. Novelty, judged harshly

- **Prior work, not claimed:** the exact solver for tree ensembles (Kantchelian et al.); verifying a malware detector
  against a region derived from edits (Chen et al. 2020, PDF); constraint frameworks (Simonetto, Sheatsley, Bostani);
  targeting hash buckets (Rosenberg); training on realizable examples (Level Up); bracketing attacks against
  verification is standard in robustness research generally.
- **Ours:** the region, computed from an extractor of EMBER's kind (hashing, normalization, ratios, entropies) for
  every feature, sound (it contains every real edit: 1,105 of 1,105, *measured*), and tied to the attacker's choices.
  Chen et al.'s features *are* PDF tree paths, so their mapping was immediate; ours is not, and that difference must
  be on the paper's first page.
- **Weak spot a reviewer will find:** if only near-monotone detectors (PV-style, A's own) ever certify, A' restates A.
  The adversarially trained rows are the test of whether A' says something A does not (Section 5, check G2).
- **Second weak spot:** the certificate is only as wide as the catalogue (append + up to 3 added sections within
  max(5% of the file, 512 KB)). That is the threat model, stated as such, as in A.

## 4. The main table (mock)

**Table A'1: the bracket per detector.** Pilot scale (10% subsample, seed 0, the 50 pilot malware), 1% FPR, the
catalogue above. "Detected" is the pilot malware each detector catches; the other cells count those files.

| Detector | TPR @ 1% FPR | Detected | Evaded (real attacks) | Certified: budget only | Certified: learned | **Certified: computed** | **Open** | Median solve |
|---|---|---|---|---|---|---|---|---|
| Undefended GBDT (reference) | 93.5% *(m)* | 47 | 27 *(m)* | 0 | 0 *(m)* | **0** *(m, 13 of 13 covered open)* | **20** | 30 min (limit) |
| PV, 4 seen attacks | 56.2% *(m)* | 22 | 15 *(m)* | 0 | 0 *(m)*; 15 wrong if circular† | **5** | **2** | 4 min |
| PV, all 8 attacks | 53.8% *(m)* | 22 | 15 *(m)* | 0 | 15 wrong† *(m)* | **5** | **2** | 4 min |
| Adversarially trained on our search's edits | 91% | 45 | 9 | 0 | 0 | **14** | **22** | 20 min |
| Adversarially trained on the toolkit | 90% | 44 | 12 | 0 | 0 | **8** | **24** | 25 min |
| A's sound detector (sanity) | 88.6% *(m)* | 41 | 0 *(m)* | 0 | — | 41 (by construction) | 0 | seconds |

† Circular: a PV model built from attack set S cannot be lowered in the features S never lowered, so a region learned
from S certifies it by construction, wrongly on every file the adaptive search evades (check 1, run 110). "Learned"
also gets the tighter 95th-percentile region as a sensitivity column (decision 7's option 2, welcome as a column).
*(m)* = measured; everything else invented. Covered = passes the catalogue's precondition (a plain layout the edits can
be written into); uncovered files are reported, not certified.

What the table must let us say (mock paper sentence): "Against edits an attacker can actually make, a hardened
detector's robustness can be bounded from both sides. Constraints learned from attacks certify nothing or certify the
wrong files; the region computed from the extractor certifies X% of files no attack evades, and shows that
adversarial training on [our edits / the toolkit] leaves Y% open, which attack-only evaluations would report as
robust."

**Figure A'1 (supporting): the brackets themselves.** One bar per file and detector, floor to ceiling, against the
threshold. It shows how wide "open" is: an open file whose floor sits just under the threshold is nearly certified,
one whose floor is far below is not.

**Section 4a. Per family and combined (decision 4).** For each detector, the same bracket computed three times: append
only, added sections only, and both together. Two readings:
- *Which edit family, and which features, keep a file open.* For an open file, the solver's best answer shows which
  feature groups carry the drop (attribution by group, as `scripts/ap_check1b.py` already does for evasions); per
  family, it shows which edit reaches them.
- *Coupling under combination (the angle A does not have).* A file certified against each family alone but open (or
  evaded) when they combine is a case where combined edits reach a region neither reaches alone. A's directions cannot
  see this: they say which way each feature moves, not how far two edits move features together. The count of such
  files per detector is a column of its own.

| Detector | Certified: append only | Certified: sections only | Certified: both | Certified alone, open together |
|---|---|---|---|---|
| PV, all 8 attacks | 7 | 6 | 5 | 1 |
| Adversarially trained (toolkit) | 18 | 12 | 8 | 4 |

(All invented.)

Components behind the columns:
- *TPR, detected*: the detector on the 10% test split and the pilot malware. No model component.
- *Evaded*: the toolkit's eight attacks plus the C1-guided adaptive search (claim C1: one edit's exact effect on the
  features), every evasion re-extracted; the ceiling is the lowest real score.
- *Certified, budget only*: the same solver with only the byte budget as the region (Kantchelian et al.).
- *Certified, learned*: the solver with each feature allowed to move by the largest (or 95th-percentile) change the
  toolkit produced (run 110's region).
- *Certified, computed*: the solver over the attacker's choices, each feature computed from them (claims C1 and C3: the
  effect of any combination of edits within a budget), with the nonlinear features bounded soundly; floor = the
  solver's proven bound.
- *Open*: detected, minus evaded, minus certified (computed).

## 5. The go/no-go (stated before anything runs)

Each check tests the claim on an informative case, keeps "open" separate from failure, and validates one stage.

- **G0. Soundness (a stage on its own).** The region contains every real edit (containment, run 111: holds, *measured*).
  No certificate on a file a real in-catalogue attack evades. Every certificate confirmed without presolve and once
  more by a re-solve with different solver settings. *Failure here stops everything; it is a bug, not a result.*
- **G1. Tractability on hardened detectors (the pre-check, Section 6, step 1).** On PV-seen and PV-all, the files no
  attack evades: at most half are open at 30 min. *Why this threshold:* above half open, the table says "unknown" more
  than anything else. *If it fails:* fall back to per-family certificates (append only; sections only), which are
  smaller programs; if those also fail, bring A' back to the user (pause or redirect to B/C).
- **G2. A' says something A does not.** On at least one detector that is *not* monotone in our directions (an
  adversarially trained one), the computed region certifies at least 10% of the files no attack evades, and leaves an
  open share the attacks would have called robust. *Why:* below that, only near-monotone detectors certify, and the
  table restates A. *If it fails:* report A' as a section of the A paper (the bracket for PV, the contrast with learned
  constraints), not as a second application.
- **G3. The contrast holds.** On every row, budget-only and learned regions certify no file the computed one does not,
  and any learned certificate on an evaded file is counted as wrong. *If it fails* (a learned region certifies
  soundly where ours is open): our region is not the only informative one, and the claim narrows to "computed, not
  learned, so no attacks needed".

Hypotheses, short: G1 passes on PV, because PV keeps only features attacks never lowered, so far fewer of its splits
sit on features the catalogue moves and the program shrinks; G2 is the real risk, since an adversarially trained GBDT
still splits on movable features and may stay open like the undefended one.

## 6. The work, in order

Each step names who runs it (Claude: under ~10 min; user: a `run/` script) and what it decides.

1. **Pre-check on PV (decides G1; ~1 day of work, then a ~20 min `run/` script).**
   - Switch the solve from yes/no to "minimize the score" and record HiGHS's proven bound (scipy's `milp` returns
     `mip_dual_bound`), so a timeout still gives a floor. Small change in `scripts/ap_check1b.py`.
   - A cheap first pass: each feature's reachable range from the encoding, each tree's lowest reachable leaf in that
     box, summed. A sound floor in seconds; files it certifies skip the solver.
   - A static count, in seconds: per detector, how many splits sit on features the catalogue can move. Predicts which
     detectors are tractable before any solve.
   - Run on the 7 + 7 PV files no attack evades, plus the undefended model's 13 as the reference (30 min each,
     parallel), for append only, sections only, and both (decision 4): `run/114`. Re-run containment (`run/111`) first if the encoding changed (it should not).
2. **Build the hardened rows (user runs; decides which rows exist).**
   - Adversarial training on our search's edits: the C1-guided adaptive search (Table A2's, 3-5 extractions per file)
     on a sample of training malware, the evasions it finds added to training, one GBDT. A `run/` script.
   - Adversarial training on the toolkit's outputs, the practitioner's version (decision 3: required); ~100
     extractions per file per attack, so hours.
   - The attack battery re-run on each new row (as run 105 and 109).
3. **The main table at pilot scale (decides G2, G3).** Brackets for every row, with the budget-only and learned
   columns (run 110's script, plus the 95th-percentile variant). `run/` script.
4. **Scale (only when the user decides):** 2,000 files, seeds 0-2.

Dropped from the earlier plan: check 2 (writing the solver's evasions as files); `scripts/ap_realize.py` stays in
the repo but is not on the critical path. The expert-set row (Decision 5).

## 7. Decisions (answered by the user, 2026-11-01)

- **1. Brackets** are the headline (accepted).
- **2. Rows:** start with the five recommended; further defenses are to be added later (user). Keep the pipeline
  generic over detectors so a new row is a model directory and a battery run.
- **3. Toolkit adversarial training: build it** (user: "we need it"). It becomes a row, not optional.
- **4. Per family *and* combined** (user): certify each edit family on its own (append only; sections only) and all
  together, to find whether individual features or edits are what keeps files open. This adds a per-family view to the
  table and the figure (Section 4a).
- **5. Expert-set row dropped** (accepted).
- **6. A' must explore another angle of the model, or it cannot stand on its own** (user: critical). Reading
  (Claude; to confirm): A rests on directions (which way an edit can push each feature, claim C4). A' must rest on what
  A does not use: how *far* features move and how they move *together* under combined edits (claims C2 and C3), and it
  must show a result that directions alone cannot. G2 tests this; the per-family vs combined comparison (Section 4a)
  is where it shows most directly. If G2 fails, A' folds into the A paper as a section.

The options as they were put to the user, each with an example and what it changes:

1. **The headline: brackets (recommended) or certificates.** Example: PV-all, 22 detected, 15 evaded, 5 certified,
   2 open. As a bracket, that is a complete answer ("68-77% vulnerable, proven"). As "certified %" it is 5/22, which
   reads as weak. Brackets tolerate open files; a certificate headline fails if few files certify.
2. **The rows.** Recommended: undefended (reference), PV-seen, PV-all, adversarially trained on our edits, A's sound
   detector (sanity). Adding toolkit adversarial training (Decision 3) or a monotone model changes how broad "which
   hardening helps" can be.
3. **Toolkit adversarial training: build it or not.** It is the defense practitioners actually use, so without it a
   reviewer asks "what about adversarial training?". It costs hours of attack runs on training malware (user-run). If
   skipped, only our own edits train the hardened row, which a reviewer may call self-serving.
4. **The catalogue for certificates: all edits together (current) or also per family.** Example: "no append of up to
   512 KB evades" is easier to solve and to read than "no append plus up to 3 sections evades". Per family is the
   fallback if G1 fails; doing both from the start doubles the solves.
5. **Drop the expert-set row (recommended).** You doubted its value (a little-cited paper), and the row needs its
   extractor instrumented before the solver can use it. Keeping it adds a defended detector built with hand-written
   constraints, the closest thing to "hand rules vs computed".
6. **Where A' lives in the thesis.** If G2 passes, A' is a second application with its own table. If G2 fails but G1
   passes, A' becomes a section of the A paper (brackets for PV, the learned-constraints contrast). Agreeing on this
   now means a G2 failure is not read as A' "dying".

## 8. Risks

- **Tractability** (main): the program is ~225 K variables, ~43 K binaries on a 4 MB file; the undefended model is
  open on all 13 files at 30 min (*measured*). The pre-check tests it where it matters, on hardened detectors.
- **Loose floors:** the solver's proven bound on big programs with many on/off switches is often far from the true
  minimum, so open files may look hopeless even when they are close. The cheap first pass and the figure make this
  visible rather than hiding it.
- **Only near-monotone detectors certify** (G2): then A' restates A; Decision 6 decides the fallback in advance.
- **Floating-point certificates:** confirmed twice (G0); an exact re-check remains future work, stated as such.

## 9. Step 1 built; smoke (2026-11-01)

Built: `scripts/ap_bracket.py` (the bracket per detector, family, and file; tests in `tests/test_ap_bracket.py`) and
`certify(..., minimize=True)` in `scripts/ap_encoding.py` (the solver minimizes the score below the threshold, so its
dual bound is a proven floor even at a timeout; infeasibility is still confirmed without presolve). Two cheap
quantities per file: the number of the detector's splits on features the family moves, and a per-tree floor (each
tree's lowest leaf with those splits free), which certifies without a solve when it clears the threshold. Every floor
is checked to lie at or below the file's clean score (the empty edit is reachable; a violation stops the run).

Smoke on the files no real attack evades (30 s per solve on PV, 10 s on the undefended model; `run/114` is the
1,800 s run, for the user):

| Detector | Moved splits: append / sections (of all) | Certified: append | Certified: sections | Certified: both |
|---|---|---|---|---|
| Undefended | 21,883 / 24,123 (of 31,500) | 0 / 13 | 0 / 9 | 0 / 13 |
| PV-seen | 1,367 / 5,458 (of 10,702) | 5 / 5 (1 by the cheap floor) | 0 / 3 | 2 / 5 |
| PV-all | 1,444 / 6,405 (of 10,711) | 6 / 6 | 0 / 1 | 5 / 6 |

(certified / covered; ~10 s per append certificate.) What it shows, and what it changes:
- **Tractability follows the moved splits.** Append moves 13% of PV's splits and 69% of the undefended model's; PV
  certifies in seconds, the undefended model does not. Sections move half of PV's splits and nothing certifies at 30 s.
- **Append certificates on PV are close to circular.** PV's attacks include padding (an append) and gamma_sections,
  so PV dropped the features they lower; certifying PV against appends partly restates how PV was built (as the
  learned region did in check 1). They still contrast with the non-circular learned region (learned from all eight
  attacks, it certified 0 of PV-seen's 22 files; run 110). The informative family on PV is sections, the one the
  adaptive search evades PV with.
- **Section coverage is thin.** Many files have no free section-table slot (PV-all 5 of 6 covered, PV-seen 2 of 5,
  undefended 4 of 13), so for them "both" is append only, and the per-family vs combined comparison (decision 4)
  reaches only the files with a slot. Making room (shifting the section data to grow the header) is an edit of the
  wider threat model, outside the catalogue; adding it would widen the coverage at the cost of a new encoding step.
  To raise with the user after `run/114`.
- **No proven floor on open files at 30 s** (HiGHS had not finished the root relaxation); whether 1,800 s gives
  useful floors is part of what `run/114` measures.

## 10. `run/114` read (2026-11-01): G1 passes for append, fails for sections

At 1,800 s the counts are the smoke's: append certifies every covered PV file in ~10 s and nothing on the undefended
model; on the 13 files that can take an added section (4 PV, 9 undefended) nothing is certified in any family that
includes sections. G0 holds. No open file has a floor: scipy's HiGHS wrapper drops the dual bound when the time limit
stops a MIP that found no feasible point, which is every open solve, so the bracket's lower end is missing (a tool
limitation, fixable by calling HiGHS so the bound survives).

The reading: certificates appear only where few of the detector's splits sit on features the edits move (append on
PV: 13%). Every detector that uses movable features (the undefended model under any family; PV under sections) is
open at 30 min. That is the main risk for G2: an adversarially trained GBDT uses all features, like the undefended
model, so as things stand it would be open too, and building those rows (hours of attack runs) would not decide G2.
Proposed before building them (each a short job): (1) recover the floors; (2) a budget sweep on the undefended model's
append family (does a small enough append certify? the largest certified budget per file is a "certified radius" in
bytes, a magnitude result A cannot give); (3) one added section instead of three on the 4 PV files with a slot.

## 11. Steps 1-3 after `run/114` (2026-11-01, `run/115`)

- **Floors recovered.** The solver now calls HiGHS directly (`highspy`), so a timeout keeps the dual bound; tested
  against scipy's `milp`; containment smoke 48 of 48.
- **Append-budget sweep, undefended model (300 s per solve):** 4 KB certifies 2 of 13, and the other 11 have real
  floors from -13.1 to 1.07 (three within about 1.0 of the threshold 1.10); 64 KB and 512 KB certify none, and their
  solves never finish the root LP relaxation, so the floor is only the cheap per-tree one (about -35).
- **One section instead of three on PV:** 0 of 4, no root LP in 300 s either.
- **Why (diagnostic on one file):** the program grows with the budget (58 K variables at 4 KB, 78 K at 64 KB, 223 K at
  512 KB; the block model of the byte-entropy windows has one block per KB), its LP relaxation takes 2 s / 6 min /
  over 7 min, and the relaxation's own floor falls from -0.04 to -10.8 between 4 and 64 KB (threshold 1.10). Above a
  few KB the relaxation is too loose to certify without exploring thousands of branches over ~25 K on/off choices. The
  obstacle at the plan's 512 KB budget is the formulation, not solver speed; a coarser (budget-independent) model of
  the windows would be smaller but looser still.

What this means for the plan. At the full budget, certificates exist only where the edits barely touch what the
detector uses (append on PV); every detector that relies on movable features stays open, with a floor no better than
the trivial one. A hardened detector that uses all features (adversarial training) would very likely behave the same
at 512 KB, so G2 as stated (at least 10% certified at the full budget) is unlikely to be met by building those rows.
What does work is small budgets: a per-file **certified budget** (the largest append, or section, proven not to evade)
is tractable up to roughly 16-32 KB and is a statement about how far the edits move the features, the angle A lacks.
Options for the user: (a) re-aim the headline to the certified budget per file and detector, with the attack ceiling
at the full budget beside it, and G2 as "adversarial training raises the certified budget"; (b) fold A' into A as a
section (PV's append certificates, the contrast with learned constraints); (c) invest in a different formulation for
large budgets (risky: the relaxation, not the solver, is what fails).
