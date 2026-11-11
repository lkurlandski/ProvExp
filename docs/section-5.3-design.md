# §5.3 *What Observed Attacks Miss*: experimental design (working document)

Started 2026-11-11 (session 34). We iterate on this document until the experimental design and its preliminary results
are strong enough to write §5.3's prose with confidence. Nothing here is decided until it is marked **Agreed** with a
date. Input: the session-33 record `docs/evidence/held-out-attacks-perspectives.md`. Compiled numbering (checked in
`manuscript/main.aux`, 2026-11-11): §5.3 *What Observed Attacks Miss*, Table 4 the detector table
(`tab:eval:detectors`).

## 1. What §5.3 has to show

§2 says that knowledge learned from observed attacks "covers only what those attacks did", and the thesis says the
computed directions are "more complete than constraints learned from attacks". In the framework's terms: every attack
output is one point the threat model can reach, so the directions read off a set of outputs are a subset of the
derived table's. §5.3 tests this on EMBER as a chain of four claims:

- **(a) The gap.** The attacks a defender has run leave part of what the threat model's edits can do unseen.
- **(b) Inheritance.** A defense that learns what to trust from those attacks trusts some of that unseen part.
- **(c) Exploitability.** An attacker who stays inside the threat model can use it.
- **(d) Named in advance.** The derivation lists the unseen part, and what each defense trusts in it, before any
  attack runs.

(d) is what makes this our finding rather than "adaptive attacks break defenses". A defender's point of view adds two
questions the section should answer: *would the defense's usual evaluation have revealed the gap?* and *would running
more, or more varied, attacks have closed it?*

## 2. What exists

**The draft** (`manuscript/_f_evaluation.tex`) is out of date. §5.3 holds only the learned-region paragraph; the PV,
ERDALT and adversarial-training paragraphs are still the session-29 text inside the old §5.4; Table 4 has seen /
held-out / adaptive columns with the fixed split's held-out values; §5.1 announces leave-one-out under a
`% SYNTHETIC` comment.

**The plan and mock** (PLAN.md decision 10; `docs/paper-mock.md` §5, item 5.3, and "Revisions after the user's
review"): the finding (learned defenses inherit two errors: per-feature ranges contain evasions no edit produces, and
the attacks never take some directions edits can take; more attacks do not close the gap), C2 first, then the learned
region, PV, ERDALT, adversarial training, and a new audit table (one row per defense: how its trust was set, what the
derivation flags, held-out, adaptive). Leave-one-out for PV and ERDALT; adaptive cells on the models built from all
eight attacks.

**The code and runs behind it:**

| Piece | Code, run | What it computes | Numbers |
|---|---|---|---|
| Perturbation vectors | `a_pv_attacks.py`, run 78 | the eight secml-malware attacks at Gimenez et al.'s low budget (~100 queries, 30 donors), the RNG reset to seed 0 before every run, on the 50 detected **pilot malware, which are test files**; donors from the 50 pilot goodware | 398 vectors |
| PV selection | `a_pv_hole.py`, runs 81, 85 | features no vector lowered are kept, monotone; the rest dropped | PV-4 (`s10-pv-seen`) TPR 56.2%, PV-8 (`s10-pv-all`) 53.8% |
| PV's hole | `a_pv_hole.py` → `a_pv/derived-pre/` | kept features the derived table (M_full, precondition, quirk-fixed) marks lowerable; their share of the model's split gain | PV-4: 327 features, 77.5% of gain, 44.4% without the parser warnings; PV-8: 291, 72.0%, 37.8% (read from the full-store `seed-0-pv`) |
| Coverage (C2) | ad hoc in session 33, no script | of the 1,070 derived-lowerable features, those some toolkit output lowered, on the 36 pilot files in the population | 745 (70%) |
| Toolkit against defenses | `a1_evaluate.py`, runs 86, 100, 131 | attacks on the pilot malware each defense detects; 1% FPR threshold; byte cap; every output re-extracted | PV-4 held-out 4/22; leave-one-out in §2.1 |
| Adaptive search | `a1_adaptive.py --search beam`, runs 127-130 | white-box beam over the twelve operations; candidates scored by Proposition 1, kept files re-extracted; section names aimed at the 8 buckets with the most split gain **in the model** (gradients for ERDALT), not chosen from the derivation | PV-4 15/22, PV-8 14/22, ERDALT-4 20/25, adversarial training 24/49, undefended 25/49, monotone rows 0 |
| ERDALT | `train_erdalt.py`, runs 128, 131 | Gimenez et al.'s linear layer under a monotone network, from the pilot vectors and the training-malware vectors (runs 122, 131 step 0) | ERDALT-4: TPR 61.1%; its four attacks 0/25 (on the files it trained on); held-out 23/25; adaptive 20/25 |
| ERDALT's audit | `a_erdalt_hole.py`, run 128 | entries of the linear layer a sufficient soundness rule forbids (no weight on both-ways features, signs on up/down ones) | 89.7% of the layer's weight |
| Learned region | `ap_check1_learned.py`, run 110 (from A') | per-feature [min, max] of the toolkit's changes as the region of an exact tree solver | informative cells certify 0 of 47 and 0 of 22; circular cells (region and PV from the same attacks) certify 22/22 |
| Adversarial training | `a_advtrain.py`, runs 125, 130 | the undefended GBDT retrained with gamma_api, header_fields and gamma_sections outputs (literature budget) on 400 training malware | gamma_api 22 → 11 of 49; all eight together 27 → 15; adaptive 24/49 |

### 2.1 Run 131, leave-one-out (state at 09:50, 2026-11-11)

PV: gamma_api fold 5/21; the other seven folds 0. ERDALT: gamma_api 21/24, header_fields 10/25, gamma_shift 5/25,
content_shift 1/28, format_exploit 1/23, gamma_sections 0/24, dos_extend 0/25, padding 0/25. The adaptive search
against ERDALT-8 is running (24 files detected).

## 3. Where the draft, the plan and mock, and the code disagree

1. **Which malware the defenses learn from.** The draft says "We run the attacks on the training malware". The code
   runs them on the 50 pilot malware, which are test files, and then evaluates PV on the same files (the A1 design's
   "first pass"). ERDALT also trains on these vectors (run 128: 200 of its 1,797; run 131: the seven seen attacks'
   pilot vectors beside the training-malware ones). Only adversarial training uses training malware alone.
   *Consequence:* the "seen attacks evade 0%" checks hold by construction on those files, and the draft sentence is
   false.
2. **The toolkit uses the same section names on every file.** secml-malware's section injection draws random 8-letter
   names (`c_gamma_sections_evasion.py`, `init_starting_point`), but `a_pv_attacks.run_attack` resets the RNG to seed 0
   before every run (following, per its comment, Gimenez et al.'s `attack_experiment.py`; not re-verified in their
   repository). Checked on run 78's vectors: across the 50 files, gamma_sections lowered 13 section-size buckets in
   all (median 12 per file, 6 distinct sets), 16 entropy buckets and 22 virtual-size buckets. Runs 122 and 131's step 0
   also use seed 0, so attacking more files adds no names. *Consequence:* the section-name part of PV's hole comes
   from the harness's fixed seed, not from what section injection can reach. Neither the plan nor the mock knows
   this.
3. **What PV's hole is made of.** The draft and the mock say "most of it in section-name hash buckets". By
   `a_pv/derived-pre/hole-seen.csv` (PV-4, 44.4 points of gain without the parser warnings): section-name buckets 17.3,
   strings 14.5, Rich header 11.3, header 0.8, entry-section name 0.4. PV-8 (37.8 points): section-name buckets 21.6,
   strings 13.2, Rich header 1.2, header 1.0, entry-section name 0.6. "Most" holds for PV-8 only; strings are about a
   third either way. The parser warnings carry another 33-34% of the gain (one warning about 30%).
4. **The adaptive search compared with the toolkit.** PLAN.md decision 10(c) and the draft set the adaptive search's
   51% on the undefended detector beside the toolkit's 53% ("about as often"). Run 127's header: the eight toolkit
   attacks together evade 27/49, but 14 of these only through GAMMA's LIEF relayouts, which lie outside the threat
   model; the six attacks that are catalogue operations evade 13/49. *Consequence:* within the threat model the
   adaptive search (25/49) evades about twice as many files as the toolkit, so "the search is not simply stronger"
   does not hold as stated.
5. **The learned region.** The mock's 5.3.1 says "per-feature ranges contain evasions no edit produces". Run 110 shows
   that the solver finds feature-space evasions in the learned box on all 47 files, of which our attacks realize 27;
   the other 20 are not shown to be unrealizable. Its own reading: informative cells give no certificate; wrong ones
   appear only where the region and the defense come from the same attacks, "which restates A's PV hole". Any
   per-feature region ignores that one edit moves many features together, the derived directions included (check 0:
   directions alone certify nothing on a non-monotone detector), so the draft's "computed directions avoid both
   failures" is wrong for the first failure.
6. **ERDALT's audit.** The draft: "89.7% of the layer's weight lies on features the table shows an edit can lower
   ... shows why". `a_erdalt_hole.py` applies a sufficient rule column by column (no weight at all on a both-ways
   feature). ERDALT's layer is designed to combine fragile features into robust ones (Gimenez et al., §5.3, on the byte
   and string features), so a weight that breaks the rule is not shown to be a hole: the derivation cannot vouch for
   the layer, and only the adaptive search shows a hole. The script's docstring overclaims the same way ("Every other
   entry is a direction the attacks ERDALT learned from did not cover").
7. **Units differ across the claims.** C2's denominator (1,070) counts the 88 parser warnings as lowerable; PV's 44.4%
   leaves them out; ERDALT's 89.7% includes them. PV-8's hole share is read from the full-store model, its Table 4 row
   from the 10% model.
8. **Adversarial training's split.** Table 4's footnote: its seen/held-out columns keep PV's old split, and two of the
   held-out attacks are ones it trained on. Under leave-one-out it has no held-out definition. It trains on three
   chosen attacks (those that evade the undefended detector, plus section injection, at the literature budget; a
   reasoned choice, run 125), while PV and ERDALT would learn from all eight.
9. **PV-4.** The mock's audit table keeps "PV with 4 and 8 attacks"; with the fixed split gone, PV-4 has no role.

## 4. Strengths

- **PV's hole is structural and computed before any attack.** PV is monotone in every feature it keeps, so every kept
  feature the derivation marks lowerable is one along which an edit can lower its score, on files in the population.
- **It answers a published claim in its authors' terms.** Gimenez et al. build PV and ERDALT from 1,033 adversarial
  examples, evaluate them against the same eight attacks, report PV 100% and ERDALT 96% robust, and say ERDALT
  converges to a robust classifier "with enough adversarial examples". They run no held-out or adaptive test.
- **The adaptive search does not use the derivation.** It aims section names by the model's own split gain or
  gradients, and every evasion is re-extracted, so the derivation's prediction and the search's confirmation are
  separate.
- **A control:** the same search moves the derived monotone detectors' scores by exactly 0 on every file and
  candidate, so its success elsewhere comes from what those defenses trust, not from search strength alone.
- **Run 131 shows that the toolkit's attacks agree with one another** (PV resists the held-out attack in seven of
  eight folds). That is evidence that a defender's usual evaluation would not reveal a gap.
- **Untapped:** the derived table exists per operation (`a_directions_derived_v2/directions.csv`, columns `op_*`), so
  the gap can be split into what the toolkit's own operations can lower and what only the other operations can. That
  separates "the attacks did not exhaust their own operations" from "the threat model is wider than the toolkit".

## 5. Weaknesses, most serious first

1. **For PV-8, the largest part of the hole is an artifact of the harness's fixed seed** (§3, item 2). A reviewer who
   reads the harness, or reruns it with another seed, closes most of the section-name hole. The finding has to survive
   a defender who varies seeds and donors.
2. **Part of the gap holds by construction.** Six of the twelve operations appear in no toolkit attack: overwriting
   the DOS header and stub, slack, and the checksum, renaming, and the two removals. The header-field attack writes
   only the timestamp, the symbol-table fields, and the linker, OS and image versions
   (`create_indexes_for_header_fields_manipulations`). "A defense built from attacks that never rename is evaded by
   renaming" is close to a tautology. The non-trivial claim, that the attacks do not exhaust their own operations, is
   untested in isolation: run 108's append-and-add-section search evaded PV-4 on 16/22, but through the seed-bound
   buckets.
3. **The defenses learn from the test files** (§3, item 1): a leak in the defenses' favor, and a false sentence in the
   draft.
4. **Within the threat model, the adaptive search is stronger than the toolkit** (§3, item 4): white-box, 5,000
   candidates, and a PE-specific name heuristic built after the hole was found. "You built the attack for the hole"
   is the first thing a reviewer will say; the monotone control answers only part of it.
5. **ERDALT's evidence is weaker than PV's.** Its audit is a sufficient rule, not a hole (§3, item 6), and it fails
   even between overlapping attacks (gamma_api fold 21/24), which points at our port as much as at the gap: the output
   layer also constrained, batches of 256, the epoch chosen on validation, the gamma_api fold missing its stopping
   criterion, TPR 61%.
6. **The learned region adds nothing beyond PV's hole** (§3, item 5) and costs the most machinery (an exact MILP
   encoding of the trees).
7. **The held-out numbers measure the toolkit, not the defense** (the user's objection, confirmed by C2 and run 131);
   any summary over folds is our choice.
8. **Adversarial training carries nothing the derivation computes**; "holds where trained, falls to an adaptive
   attack" is the known pattern.
9. **Small cells and a weak detector:** 22-25 files per cell; PV detects 22 of 50 (TPR 54%).
10. **"More attacks do not close the gap"** rests on PV-4 → PV-8, at the same seed, on the same files.

**What a reviewer attacks first:** the adaptive search (4), then triviality (2), then the seed once they read the
harness (1), then the leak and ERDALT's fidelity (3, 5).

## 6. Numbers that depend on our choices

- *Ours:* the files the defenses learn from (test pilot); the seed (fixed at 0, copied from Gimenez et al.); the donors
  (pilot goodware, 30); the number of attacked files (50); the threat model's breadth (from the literature, §4.3);
  the adaptive search and its name heuristic; any summary over folds; adversarial training's three attacks.
- *Not ours:* the eight attacks and their low budget (Gimenez et al.'s); EMBER's train/test split.

## 7. Options

Each: what it measures, its cost, what it lets the section claim, the hypothesis, its weak point.

- **O1. Coverage by source, on existing outputs.** For each derived-lowerable feature, whether some toolkit output
  lowered it, in three classes: lowerable by the toolkit's own operations (append, add a section, add imports, the
  two gaps, header fields), lowerable only by the other six, and the parser warnings (no items; the derivation leaves
  them free). Per attack and in union, on the pilot vectors and on the 400 training malware (runs 122, 131 step 0).
  The same split for PV-4's and PV-8's holes, as shares of gain.
  *Cost:* a script (C2 has none); minutes. *Claim:* "of what the toolkit's own operations can lower, the attacks
  lowered X%; of what only the other operations can lower, none". *Hypothesis:* the other-operations class is about
  0, apart from GAMMA's relayout effects; within the toolkit's operations coverage is high except the section-name
  buckets and some strings; the training outputs lower the same section buckets as the pilot (same seed). *Weak
  point:* it measures the attacks, not a defense, so it needs O3.
- **O2. Varied observation.** Rerun the toolkit with a different seed per (file, attack) on the 400 training malware,
  with training goodware as donors (a pure addition to `a_advtrain.py`, e.g. `--seed_per_file`). Coverage as the
  number of attacked files grows (25 to 400), fixed seed against per-file seeds.
  *Cost:* gamma_sections alone on 100 files, about 5 min (a smoke I can run); all eight on 400 files, about 2.5-3 h
  at 16 workers (step 0 took ~1.5 h for four attacks). *Claim:* how much of the gap varied runs close, and what never
  closes. *Hypothesis:* per-file seeds cover nearly every section-name bucket within about 100 files; strings and the
  Rich header rise little; the other-operations class stays at 0. *Weak point:* more attack runs; worth it only if O1
  shows the gap within the toolkit's operations is mostly the seed-bound buckets.
- **O3. The best defense a defender could build with the toolkit: tested as published, audited, confirmed.** PV and
  ERDALT from O2's outputs only (all eight attacks, per-file seeds, training malware). For each defense:
  (i) its own eight attacks on the pilot test malware, with fresh seeds (Gimenez et al.'s protocol on new files; for
  ERDALT, also the fidelity check against their 96%);
  (ii) the derivation's audit, split by source as in O1 (PV: share of gain; ERDALT: "cannot vouch", no hole claim);
  (iii) the adaptive search with the full menu;
  (iv) the same search restricted to the toolkit's operations (`--operations app sec imp ext shf hdr`) and to the
  other six.
  *Cost:* about 1 h of coding (PV selection from `X.npy` and the clean training rows); a run script of about 3-4 h
  (PV: training 2 min, toolkit ~30 min, three searches ~25 min each; ERDALT: 26 GPU-min, toolkit ~30 min, search
  ~25 min). *Claim:* "the defense passes its own evaluation on new files; the derivation names N trusted features
  edits can lower, carrying W% of its gain, M of them lowerable only by operations the attacks lack; the search evades
  it on K of 22, and on K' using only the attacks' own operations". *Hypothesis:* PV-best keeps fewer features (TPR a
  few points under 53.8%); its own attacks evade 0-2 files; its hole falls to about 15-25% of gain without the
  warnings, mostly strings and header fields; the full search still evades a third or more, mostly through operations
  the toolkit lacks; restricted to the toolkit's operations, a few files at most. *Weak point:* it may remove most of
  PV's adaptive result; then the PV finding narrows to operations the attacks lack (O5 decides whether to go further).
- **O4. Leave-one-out's role.** (a) Drop it. (b) One sentence with every fold's value for PV and ERDALT, as evidence
  that the toolkit's attacks agree with one another (no mean, no worst fold). (c) A column (no: weakness 7). If kept,
  rebuild the folds from O2's outputs for consistency (PV about 40 min; ERDALT about 4 GPU-hours, or PV only).
  *Suggestion:* (b) from run 131 as it is, or (a) if O3 makes it redundant.
- **O5. MAB-Malware as a ninth member of the pool** (perspective 6 of the record). *Go/no-go without running it:*
  O1/O3's split by source shows which of PV-best's hole features only renaming, the removals and the checksum
  (MAB-Malware's operations) can lower, and how much gain they carry; integrate only if that share is material.
  *Cost:* large (their code against our models). *Claim:* whether a second, independent toolkit closes the gap.
- **O6. The learned region:** one clause ("constraints learned from the same attacks certify the defense, by
  construction, on files the search evades") or nothing. No new run.
- **O7. Adversarial training:** keep run 125 (the attacks that evade, a reasoned choice) without its held-out column,
  or retrain on all eight attacks for consistency with O3 (from runs 122 and 131's step 0, low budget; ~10 min
  retraining plus evaluation). Either way it is one paragraph: it holds where trained and does not slow the adaptive
  search.
- **O8. All subsets, or keep-one, with trained models** (perspectives 4, 7): not recommended; O1 gives their
  information about the attacks, and O3 covers the defense side.

## 8. Suggested course of action

- **Phase 0 (existing outputs; Claude; minutes).** O1; read run 131 when it finishes. *Decision point with the user:*
  how much of the gap, and of PV's hole, lies within the toolkit's own operations, and how much of that is the
  seed-bound buckets.
- **Phase 1 (smoke; Claude; ~5 min).** gamma_sections with per-file seeds on 100 training malware: does per-file
  seeding cover the section-name buckets? If it does, the published protocol's PV hole is partly an artifact, and O2
  and O3 are needed before §5.3 can claim anything about PV.
- **Phase 2 (run script for the user; ~5-7 h in all).** O2 (all eight attacks, per-file seeds, training malware),
  then O3 for PV and ERDALT, and O7 if chosen.
- **Phase 3 (with the user).** Settle the claim, the audit table's columns and units, leave-one-out's role (O4) and the
  learned region (O6); then draft §5.3 in blocks with `paper-prose`.

**What the section can claim under each outcome** (to agree before Phase 2):

- *PV-best's hole lies within the toolkit's operations and the restricted search realizes it:* the strong finding.
  Observed attacks, even varied, do not exhaust their own operations, and the derivation names what they leave.
- *Varied runs close the within-toolkit gap, but a hole remains in operations the toolkit lacks and the full search
  realizes it:* a defense learned from one toolkit inherits that toolkit's operations. The derivation covers
  operations no implemented attack uses, from their definitions alone, and tells the defender when the observation is
  complete.
- *PV-best is not evaded:* the PV finding reduces to the published protocol's fixed seed and cannot carry the section.
  §5.3 then rests on coverage by source, ERDALT, and the cost of observation, and its claim must be narrowed with the
  user (memory `dont-reframe-research-claims`).

## 9. Open questions for the user

1. May I run Phase 0 now, and Phase 1's smoke after it?
2. Should the defenses follow Gimenez et al.'s protocol as published (fixed seed), or the strongest version a defender
   could run (per-file seeds)? Suggested: the strongest, with one sentence that the published protocol reuses the same
   section names on every file.
3. Adversarial training: keep run 125's three attacks, or retrain on all eight (O7)?
4. Leave-one-out: drop it, or one sentence (O4)?

**The user's answers (2026-11-11):** (1) yes, run Phases 0 and 1; (2) do what is best for the research, not
necessarily what prior work did; (3) fix any gap in the design that would undermine the results, running long jobs in
the background meanwhile; (4) leave-one-out's role is Claude's call, and may wait for more preliminary results.

## 10. Results of Phases 0 and 1 (2026-11-11; `run/132_coverage_seed_smoke.sh`)

**Phase 0** (`scripts/a_coverage.py`, `artifacts/experiments/a_coverage/`). Hypothesis held.

- *By operation, the gap is not the threat model's breadth.* Of the 1,070 lowerable features, 980 can be lowered by
  an operation some toolkit attack implements, 88 are parser warnings, 2 only by the other operations. The per-operation
  table is coarse here (adding a section can move almost any feature), so the witnessed operations below are the better
  guide.
- *The derived table is fairly tight.* Our own edits (catalogue_checks, 2,000 test files, every edit re-extracted)
  lowered 915 of the 1,070. The 155 they never lowered: 78 warnings, 67 strings, 5 header, 3 data directories, 2
  others.
- *More files close part of the gap at the same seed.* Toolkit coverage: 745 on the 36 pilot files in the population,
  847 on the 314 training malware in it (704, 759, 797, 814 at 25, 50, 100, 200 files: still rising, flattening).
- *What our edits lower and the toolkit never did* (pilot and training together): 90 features. 82 section features
  (34 size, 26 entropy, 11 virtual-size buckets, 8 entry-section-name buckets, 2 characteristics, 1 empty-name count),
  4 header fields, 3 warnings, 1 string.
- *The fixed seed, confirmed at scale:* gamma_sections lowers the same 13 section-size buckets on 314 training files as
  on 36 pilot files.
- *PV's hole, as witnessed by our edits:* PV-4: 36.5% of gain (section 17.7, Rich header 11.3, strings 5.3, warnings
  1.4, header 0.7); PV-8: 25.7% (section 22.3, Rich header 1.2, warnings 1.1, header 0.9, strings 0.2). Of the
  strings part of PV-4's hole (14.5 points), only 5.3 is witnessed.

**Phase 1** (gamma_sections, seed per file, 100 training malware). Hypothesis held: the union of lowered buckets is
50/50 for size, entropy and virtual size (100 distinct sets; fixed seed on 399 files: 13, 21, 33). This one attack
closes 71 of the 90-feature gap. Left: the 8 entry-section-name buckets, the empty-name count and 2 characteristics
buckets (all lowered by our edits only through *rename*, which no toolkit attack implements: MAB-Malware's operation),
4 header fields (timestamp-adjacent fields the toolkit's header attack writes but never lowered: they are usually 0 on
the files it attacked), 3 warnings, 1 string.

**Run 131, finished** (`artifacts/experiments/a_loo/summary.json`). PV folds: gamma_api 5/21, the other seven 0 (files
evaded in any fold: 5). ERDALT folds: gamma_api 21/24, header_fields 10/25, gamma_shift 5/25, content_shift 1/28,
format_exploit 1/23, gamma_sections, dos_extend, padding 0 (files evaded in any fold: 26). ERDALT-8 (from all eight
attacks, criterion met at epoch 287, test AUC 0.871) is evaded by the adaptive search on **17 of 24** (15 at 200
candidates, 17 at 1,000).

### 10.1 What this changes

1. **PV's adaptive result, as it stands, rests mostly on the harness's fixed seed.** Its witnessed hole is 22 of 25
   points section-name buckets, and one attack run with a seed per file covers them. A PV built from varied runs would
   drop those buckets. The 14/22 cannot carry §5.3 against a reviewer who reads the harness. This is now weakness 1,
   measured.
2. **Weakness 2 (the gap by construction) mostly dissolves,** with one exception that matters: renaming lowers the
   entry-section-name buckets, and no toolkit attack renames. That is the clean case of "an operation the observed
   attacks lack", and it is small (11 features; its gain in PV unknown until PV-best exists).
3. **What observation done well still misses is small on EMBER:** 19 witnessed features after Phase 1, plus whatever
   lies in the 155 lowerable features our edits never lowered (67 of them strings) that a PV would keep. Whether a
   defense built from varied runs is still evadable is the open question, and only Phase 2 answers it.
4. **ERDALT looks like a different finding.** ERDALT-8 learned from all eight attacks and is still evaded on 17/24,
   and the held-out attacks evade it in five of eight folds, including folds whose attack lowers nearly the same
   features as the seen ones (gamma_shift 5/25, content_shift 1/28). Its constraint holds on the observed perturbation
   vectors, not on the directions those vectors come from, so what it misses is not features no attack lowered but
   vectors no attack produced. That would hold under varied runs too; Phase 2 tests it.
5. **The completeness argument gains weight.** The same eight attacks reveal 70% of the lowerable features under the
   published protocol and nearly all of what our edits lower when varied over 300 files; nothing in the observations
   tells the defender which situation they are in. The derivation gives the complete list in one pass, and is the only
   way to know that observation is complete.

### 10.2 What §5.3 could claim now (to settle with the user; memory `dont-reframe-research-claims`)

- *If PV-best (Phase 2) is still evaded:* the plan's finding stands, now on a fair design.
- *If PV-best is not evaded, but ERDALT-best is:* §5.3's finding moves from "the attacks did not lower these features"
  to two parts. (i) Observed coverage depends on incidental choices invisible to the defender (the published protocol:
  70%, a hole, 14/22 evaded; varied runs: nearly complete), and the derivation is the certificate of completeness. (ii)
  A defense that learns from the observed vectors themselves (ERDALT) fails on vectors the attacks did not produce,
  even with complete feature coverage.
- *If neither is evaded:* the observed-attacks finding on EMBER is about cost and certainty only, and the claim must be
  narrowed.

### 10.3 Phase 2, revised

Needed in every case above: the toolkit's eight attacks with a seed per file on the 400 training malware (training
goodware donors; about 2.5-3 h at 16 workers). From those outputs only (no pilot vectors): PV-best and ERDALT-best;
for each, (i) the eight attacks with a seed per file on the pilot test malware (needs `--seed_per_file` in
`a1_evaluate.py`), (ii) the derivation's audit with the witnessed split of §10, (iii) the adaptive beam with the full
menu. The search restricted to the toolkit's operations (O4) loses its purpose (weakness 2 dissolved) and is dropped;
the gap's operations are read from the witnesses instead. Leave-one-out stays out of Phase 2: run 131's folds already
answer what it can (decision deferred, per the user). Adversarial training (O7): retrain on all eight per-file-seed
outputs, so every defense learns from the same observations.

**Scripted:** `run/133_varied_observation.sh` (2026-11-11; the user launches runs over ~10 minutes). Hypotheses in its
header. It also re-runs the toolkit with a seed per file against the *old* PV-all and ERDALT-8, which shows what
re-running the very attacks a defense was built from, with other seeds, does to it.

### 10.4 Results of Phase 2 (run 133, ~4.8 h; run 134, Claude, ~3 min)

Per-hypothesis detail in run 133's header. In plain terms:

| Defense (all from the same 3,183 varied outputs on 400 training malware) | TPR at 1% FPR | Toolkit, seed per file | Adaptive beam |
|---|---|---|---|
| Undefended GBDT (full store) | 95.6% | 25/49 | (run 127) |
| Adversarially trained | 95.6% | 12/50 | 23/50 |
| PV-best (Gimenez et al.'s rule) | 26.2% | 0/9 | **4/9, each one rename** |
| PV-all (old: seed 0, pilot files) | 53.8% | 1/22 | (14/22, run 127) |
| ERDALT-best | 62.7% | **24/29, all gamma_api** | 22/29 |
| ERDALT-8 (old; saw pilot vectors) | 59.7% | 6/24, all header_fields | (17/24, run 131) |
| Derived monotone detector, same 10% store | 89.7% sums, 87.3% features | 0 in population (§5.4) | 0 |

1. **Coverage (hypothesis held).** Varied runs lower 928 of the 1,070 lowerable features on the training files in the
   population (seed 0: 847). Of the 90 features our edits lower and the toolkit never did, 20 remain: the
   entry-section-name buckets (rename only), a few header fields, 3 warnings.
2. **PV-best is still evaded, and exactly where §10.1 said it would be.** All four of its adaptive evasions are one
   rename of the entry section, found within the first 50 candidates. Its hole (124 features, 38.8% of its gain) is led
   by entry-section-name bucket 1 (12.8%); witnessed by our edits 20.6%, nearly all section-name and characteristics
   buckets. Renaming is not in the toolkit (MAB-Malware has it); the derived table lists those buckets as lowerable
   before any attack runs. The attacks re-run with a seed per file evade it on none of its 9 files. Caveat: 9 files.
3. **PV built well detects little (not predicted).** PV-best detects 26.2% at 1% FPR (PV-all 53.8%; the derived
   detector on the same store and features 87.3%). Not a straw man: leaving out the 8 broken shift outputs (run 134,
   PV-clean) gives 26.7%. Two causes, both "observation cannot tell the cases apart". (i) PV-all's largest feature (a
   parser warning, 31% of its gain) is lowerable; the attacks lower it on training files, never did on the pilot
   files PV-all was built from; PV-best drops it. (ii) PV constrains every feature no attack moved; the largest,
   `header:characteristics_DLL` (24% of the unconstrained model's gain), cannot be moved by any edit, and the derived
   table leaves it free. PV-free (never-moved features left unconstrained; not Gimenez et al.'s rule, and unsound
   against any operation the attacks lack) recovers to 50.9%. The remaining ~36 points to the derived detector are
   not decomposed (PV drops features only out-of-model side effects lower, e.g. `RELOCS_STRIPPED`, export sizes).
4. **The old PV-all is not broken by re-randomized attacks:** 1/22. Its weakness was the search (14/22), not the seed
   of the attacks it saw. This corrects §10.1(1): the fixed seed shaped PV-all's *hole*, but PV-best, built without
   it, keeps the rename part of the hole and is still evaded.
5. **ERDALT fails on the attack it was trained against, with other donors.** gamma_api takes its imports from goodware
   donors; the evaluation uses pilot goodware, ERDALT-best's training used training goodware: 24/29 evaded. ERDALT-8,
   which saw vectors made with the pilot donors, 0/24 on gamma_api. Its constraint holds on the observed vectors, not
   on the next ones the same attack makes. Caveat for a reviewer: ERDALT's scores pile at a floor (every evasion ends
   at p = 0.49966, tau 0.49968; temperature 748), so our reproduction (AUC 0.88, TPR 62.7%) may be weaker than theirs.
6. **Adversarial training** halves the toolkit's evasion (25 → 12 of ~50) at no cost in detection; the search still
   evades 23/50 (as predicted).

### 10.5 What §5.3 can claim (recommendation, to settle with the user)

The first case of §10.2 holds, in a sharper form than the draft's. Proposed finding: *a defense learned from
observed attacks inherits what the attacks did not do, and nothing in the observations says what that is.* Evidence,
in the order a paragraph would give it:

- **Coverage is invisible to the defender:** the same eight attacks reveal 745 lowerable features under the published
  protocol and 928 when varied over 400 training files; the derived table lists all 1,070 in one pass.
- **An operation the attacks lack becomes the hole:** PV built from 3,183 varied outputs is evaded on 4 of 9 files by
  one rename, through features the derived table names in advance.
- **Unmoved is not unmovable:** observation cannot separate features the threat model can lower, features it cannot
  move, and features only out-of-model side effects moved, so PV either trusts what it should not (PV-all: hole, 14/22)
  or constrains and drops what it need not (PV-best: 26.2% against the derived detector's 87.3% on the same features).
- **Constraining vectors does not constrain directions:** ERDALT is evaded by its own training attack with other donors
  (24/29) and by the search (22/29).
- **Adversarial training** helps against the toolkit and not against the search (12/50 against 23/50).

What it should not claim: that the fixed seed alone made PV evadable (it shaped PV-all's hole, but the rename hole
survives varied runs), or a number for PV's hole from the seed-0 runs. Audit table: these rows, plus leave-one-out
redone the fair way (**run 135**, the user agreed 2026-11-11: folds from run 133's outputs minus the held-out attack,
which then attacks the fold's model with a seed per file; a sentence in the body, the per-fold table in the appendix);
run 131's seed-0 folds are retired. Open, all optional: more pilot files for PV-best's 9 (the scale-up), decomposing the last ~36 points of
PV's accuracy gap, and whether ERDALT's score floor needs a better reproduction before a reviewer sees 24/29.

## 11. Log

- **2026-11-11 (session 34): created.** A first analysis was given in the chat from the draft. At the user's request it
  was re-assessed against the plan, the mock and the code; §3 lists the disagreements. Two of them overturn points of
  the first analysis: attacking more files at the same seed adds no section names (the first analysis expected
  coverage to grow with files), and within the threat model the adaptive search evades about twice as many files as
  the toolkit (the first analysis used the 51% against 53% comparison as a control).
- **2026-11-11 (session 34): Phases 0 and 1 run** (run 132; §10). The PV hole is mostly the harness's fixed seed; the
  gap is not the threat model's breadth (except rename); ERDALT-8 evaded 17/24; Phase 2 revised (§10.3).
  The user agrees this is mostly bad news for §5.3 as planned; Phase 2 scripted as run 133, for the user to run.
- **2026-11-11 (session 34): Phase 2 read** (run 133, launched by the user; run 134, PV-clean and PV-free, by Claude;
  §10.4-10.5). PV-best is still evaded, 4/9, each by one rename; PV built from varied runs detects 26.2% (not
  predicted; not the broken outputs; partly the never-moved features it constrains); ERDALT-best evaded 24/29 by its
  own gamma_api with other donors; adversarial training 12/50 toolkit, 23/50 search. §10.2's first case holds;
  recommendation in §10.5, to settle with the user.
- **2026-11-11 (session 34): leave-one-out kept, redone fairly.** The user agreed with §10.5's framing but not with
  dropping leave-one-out ("still a very powerful and interesting experiment"); run 135 scripted and smoke-tested.
- **2026-11-11 (session 39): 5.3 drafted** from §10.5 (commits 7a2ceff, 9d0369f, 035d977). The user cut the
  learned-region paragraph and the audit table (tables to be remade later) and ruled out seed details in the paper,
  so the 847-vs-928 comparison (same 314 training files; the plan's "745" was the 36 pilot files) and PV-all's 14/22
  stay in this document only. Run 135's PV folds: 0 evaded in all eight (detected 9, 9, 8, 9, 19, 9, 9, 9; gamma_api
  0/9, against the predicted 1-2). ERDALT folds pending, in blue in the draft.
