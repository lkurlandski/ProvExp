# Triage of the 2026-11-12-body register

Commit 2e4c350. Verdicts: decided, dismiss, cheap fix, investigate.

| Item | Risk (short) | Verdict | Group | Decision |
|---|---|---|---|---|
| R7 | routed system is a bypass | investigate | population | methodology: decision 11 stands; end-to-end number after run 143 |
| R1 | attacks weaker than published; adaptive attack misses an operation | investigate | attacks | methodology: decision 12 stands; one wording fix; MAB rerun optional |
| R2 | "sound" rests on tested premises | investigate | trust | argument + 4-byte record fix: draft confirmed (session 58); probe and vocabulary check not needed |
| R18 | learned baselines get less information | investigate | trial | investigate (before scale-up, step 2) |
| R6 | formal results are known techniques | cheap fix | | argument: session 50 stands; name self-maintainability |
| R4 | one instance for a class claim | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R20 | statistics cannot rank defenses | cheap fix | | methodology: thresholds from the validation split at scale-up |
| R11 | table cells from different detectors | dismiss | | no change: the full run fixes it |
| R19 | ERDALT port may be weak | investigate | erdalt | argument: training met the constraint, finding stands (session 58); donor control at scale-up |
| R3 | hand-analysis evidence thin | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R17 | Theorem 1 beyond its proof; class universal | cheap fix | | no change: session 53b stands (no universality sentence) |
| R15 | threat model scope; no named attacker | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R9 | what Proposition 1 enables | dismiss | | no change: settled (decision 12 (iii)) |
| R5 | Pierazzi et al. portrayed loosely | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R21 | prior work misattributed or missing | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R12 | counts include unmodeled features | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R14 | header-field overwrite never validated or used | investigate | attacks | methodology: covered by `--score real` (decision 12) |
| R8 | expert-set comparison | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R13 | instrumentation effort | cheap fix | | argument (after scale-up; wording not yet reviewed) |
| R16 | PE minutiae | dismiss | | no change: reviewers liked the parser facts |

## Groups to investigate

Order agreed with the user (session 58): trust and erdalt first (small checks), then trial (the realistic
competitor), then a last look at what else the scale-up needs, then the scale-up. The text fixes wait for the
scale-up's numbers.

GROUP population: R7
- Run 143 (escapes from the unescaped originals, then the full-menu search with `ent`): is any detected original
  evaded by either `-loose` monotone detector? One evasion means the widening of decision 11 is incomplete.
- After the widening, can any remaining clause of `precondition` or `plain_layout` still be triggered by a write the
  loader ignores (the escape audit of run 137 repeated against the loose population; the SizeOfImage raise is known to
  take every file out)? If yes, the guarantee there is measured, not proven, and the text must say for how many files.
- With one monotone detector scoring every file, what share of all attacked malware is still detected after any attack
  at a 1% (and 0.1%) system false-positive rate, files outside the population included? This is the number all three
  negative reviewers asked for; if the outside-population files are evaded often, the end-to-end claim weakens.

GROUP attacks: R1 R14
- With every candidate scored by extraction (`--score real`, header-field overwrites and declined DOS-stub edits
  included), does the adaptive attack evade the unconstrained, adversarially trained, PV or expert-set detectors
  noticeably more often than the stored beam runs? If adversarial training falls clearly further, §5.3's paragraph on
  it changes; if not, the coverage gap was harmless.
- MAB-Malware at Zainab et al.'s setting (0.1% FPR, no byte cap) against the unconstrained detector: does its rate move
  toward their 83%? If yes, the gap is the operating point and the byte limit, as decision 12 argues; if no, the
  harness hand-over weakens the attack and must be audited.
- The full beam against the monotone detector on the sums: does any population file show a score drop? The theorem
  says none; a drop would be an implementation error.

GROUP trust: R2
- A multi-byte marker probe (MZ, `PE\0\0`, Rich/DanS, known magic values written at every header and data-directory
  position of the pilot files): does any write change which items the parser finds without touching a recorded
  locating position? One hit means the record is incomplete and the guarantee unsound until fixed.
- On the whole test population below 4 MB, how many files carry a (kind, sum) pair, or an item kind at an overwritten
  position, that is absent from the 2,000-file vocabulary? If none, a per-file check costs nothing and the sample
  premise holds by construction; if many, "100 files give the same table as 2,000" overstates the coverage.
- In the code, is every in-place write of the catalogue either declined or off every locating position? If so,
  closure for overwrites follows from the record and needs testing only for the declared operations.

GROUP trial: R18
- A trial table built from the existing 73,063 catalogue edits and the toolkit outputs (a feature is lowerable if some
  edit lowered it): on how many modeled features does it differ from the derived table, and does a monotone detector
  built on it fall to the adaptive attack? If it matches the derived table where it matters and is not evaded, the
  computation-against-trial contrast of §5.2-5.3 reduces to completeness and cost, and must be reframed.
- Adversarial training iterated with the adaptive attack over all twelve operations (training malware, two rounds):
  does it still fall to an attack outside its loop (MAB-Malware, or a held-out operation)? If it holds, §5.3's
  adversarial-training paragraph must change.

GROUP erdalt: R19
- ERDALT: what share of its training perturbation vectors violate its positivity constraint (L(δ) < 0), and does
  training to a proper stopping point raise its AUC toward their 93% and change the 24/29? If training vectors violate
  it, the evasion by its own training attack is a training failure, not the gap the paper names.

## The items

### R7: the routed system is a bypass
**Verdict:** investigate. All four reviewers raise it and three make it their one change: files outside the population
went to an unconstrained detector that the attacks evade about half the time, flagging them instead costs 1.5% false
positives against a 1% budget, and the meta-review found that single loader-ignored field writes take any file out.
Every part of this holds, and the sentence "such files are rare among benign software, and so stand out"
(`_f_evaluation.tex:363`) is contradicted by the paper's own numbers and must go whatever else happens. Whether the
answer is a rewrite or a deeper change depends on what the attacks do once the router is gone, which only the stored
and running escape experiments can tell, hence the three questions of the group. The rate of malware outside the
population (about 11% against 1.5% of benign) is worth one sentence as a signal, never as the defense.
**Earlier decision:** decision 11 (PLAN.md; sessions 48-55): no router, one monotone detector scores every file; the
threat model gains `ent` and the population lets the certificate and debug data lie past the end; LIEF's overlay rule;
run 143 pending; agrees: removing a component answers the bypass more cleanly than any of the meta-review's
clause-by-clause patches, and the escape audit confirmed the fatal condition the meta-review named.
- [ ] After run 143 (R7 track): share of all attacked malware still detected after any attack, at 1% and 0.1% FPR, every file counted; remove "stand out" (`_f_evaluation.tex:363`).

### R1: the attacks are weaker than published, and the adaptive attack misses an operation
**Verdict:** investigate. Parts of this row restate our own result: a zero score drop on the monotone rows follows from
Corollary 1, so the text should call it a check of the implementation (`_f_evaluation.tex:350`, "confirms the
guarantee"), and that is a one-line wording fix. The real point is narrower and verified: the adaptive attack never
applied a header-field overwrite, the operation behind the additions detector's 12/43, so "combines any operations of
the full threat model" was false, and the comparative claim about adversarial training rests on that attack. The
existence results (PV by one rename, ERDALT, the expert set) do not depend on attack strength. Whether the comparative
claims survive is a fact about runs, hence the group's questions.
**Earlier decision:** decision 12 (PLAN.md, sessions 49 and 51): MAB-Malware run against every detector (read: 0/49 on
the undefended detector under the byte budget, 7/9 on PV by renames, 0 on the monotone rows), "evaded by any attack" in
the body, "stronger" dropped, `--score real` at the scale-up; agrees, with one gap: the distance to Zainab et al.'s
83% is explained by an argument (operating point, byte cap) rather than measured at their setting, and B will ask.
- [ ] Wording: the monotone rows' zero score drop is a check of the implementation, not a confirmation of the guarantee (`_f_evaluation.tex:350`).
- [ ] Decide before the scale-up: MAB-Malware also at Zainab et al.'s setting (0.1% FPR, no byte cap)? Optional.

### R2: "sound" rests on tested premises
**Verdict:** investigate. All four reviewers raise it, and it is A's one change. The writing part is a cheap fix that
fits decision 2: one paragraph listing what the EMBER guarantee trusts (contribution functions checked bit for bit,
declared changes checked by re-extraction, the locating-position record and its two correction rounds, the sample
vocabulary, closure), with counts and no lines of code, and "cannot be evaded" conditioned on it. A's request for a
sound dependency analysis of pefile reopens decision 2 (checked, not proven, is acceptable; the proof carries the
weight) and would be a research project; dismiss that part. What remains open is whether the cheap strengthenings
hold: a crafted Rich block already escaped single-byte probing once, so a multi-byte probe could find an unrecorded
rule, and the per-file vocabulary check (C-Q5) is free only if no test file needs it. Both are short checks with
outcomes that change what the paragraph can say.
- [x] Group trust: drafted (`rebuttal/trust.md`); the probe and the vocabulary check are not needed (code reading;
  attacked files are in the sample by construction).
- [ ] Before the scale-up's recount: extend the recorded Rich search range by the 4 key bytes past the marker (pure
  addition; `trust.md`, question 1). Expect no direction to change.
- [ ] After the scale-up: one paragraph (~120 words) at the end of §4.4 listing what the EMBER guarantee trusts, how
  each part is checked (with R13's counts), and the three facts of `trust.md`; §5's lead conditioned on it.

### R18: learned baselines get less information than the derivation
**Verdict:** investigate. Part of C-W3 restates the finding of §5.3: a defense learned from observed attacks cannot
tell which operations the attacks lacked, and that it falls to them is the point, not a flaw (and the defender learns
which operation to add only after an attacker used it). The part that holds is that the paper's thesis sets
computation against *trial*, and §5 never builds the competitor a practitioner who knows the twelve operations would
use: systematic trial over them. The 73,063 catalogue edits already form one, so the trial table and a detector on it
cost analysis, not new runs; this is the realistic-alternative test CLAUDE.md asks of every application, and I would
propose it without a reviewer. Iterative adversarial training is what four reviewers expect from the defender
(decision 6 scheduled exactly this revisit), but it is compute-heavy, so the cheap question goes first.
- [ ] Group trial: the trial table from the 73,063 catalogue edits and a monotone detector on it, after trust and erdalt; decide then whether iterated adversarial training joins the scale-up.

### R6: the formal results are known techniques
**Verdict:** cheap fix. All four say it and they are right: Proposition 1 is the delta rule of incremental view
maintenance plus the known need to keep the multiset for maxima and minima (self-maintainability, Mumick et al.), and
Theorem 1 is a sign abstraction. The answer is a paragraph that names what is classical and what is new (the class as
a modeling choice real extractors meet bit for bit, the delta and signature of a raw write computed from item tables
and locating positions, soundness over a population closed under the threat model), and a corrected §6 contrast with
incremental parsing, which also maps raw edits to affected nodes.
**Earlier decision:** session 50 (PLAN.md; `docs/evidence/r6-prior-work.md`): four citation edits in §3 and §6,
abstract interpretation now cited (`_d_framework.tex:440`, `_g_related_work.tex:100`); agrees, provided the edits also
name self-maintainability and retire the first claimed difference from incremental parsing.
- [ ] Name self-maintainability (Mumick et al.) where §3/§6 cite view maintenance; one phrase.

### R4: one instance for a claim about a class
**Verdict:** cheap fix. All four raise it, none as their one change, and which second domain and when is the authors'
settled call. What the text can fix now: §2's "for a broad class of feature mappings" (`_c_background.tex:79`) needs
the claims scoped "on EMBER" where they are measured, one sentence naming what falls outside the class
(order-dependent features, learned embeddings, raw-byte models), and §4's template stated as four format-free
questions, each with the check that answers it, so the recipe is visible without a second instance.

### R20: the statistical design cannot rank defenses
**Verdict:** cheap fix. Seeds 0-2, full splits and more attacked malware are the planned scale-up (settled), so that
part needs only the rebuttal's "the full run does this". Two parts are real and cost nothing: thresholds should come
from EMBER 2024's validation split rather than the benign test files (add it to the scale-up's protocol; no paper text,
per the no-protocol-hygiene rule), and the share of all attacked malware still detected after any attack is
computable from stored outputs and answers C's denominator objection with numbers that favor the monotone rows.
- [ ] Scale-up protocol: thresholds from EMBER 2024's validation split (no paper text).

### R11: cells of one table come from different detectors
**Verdict:** dismiss. Rebuttal: "The pilot tables mix a detector trained on the full training set with ones trained on a
10% subsample; the full run trains every detector of a table on one training set and attacks it with one protocol, and
each table reports one unconstrained detector." This is already step 3 of the plan and needs no new decision.

### R19: the ERDALT port may be judged weak
**Verdict:** investigate. Running the unmodified released code is settled (its output layer breaks the guarantee), so
that request is dismissed. What holds is that the port detects far less than the original (AUC .883 against 93.0%),
stopped after one epoch, and enforces positivity only as a soft penalty: if its training vectors already violate the
constraint, its fall to its own training attack is a training failure, not the unseen-vector limitation the paper
describes. That is one stored-data check, and it decides how §5.3's ERDALT paragraph reads.
- [x] Group erdalt: drafted (`rebuttal/erdalt.md`): 2 of 3,183 training vectors violate L(δ) ≥ 0, by < 4e-7; full
  310-epoch schedule ("one epoch" was a misreading); the evasions are unseen vectors.
- [ ] Scale-up: the donor-overlap control (GAMMA imports against ERDALT with the training donors; needs a donor-pool
  option in `a1_evaluate.py`; ~30 files, minutes).
- [ ] After the scale-up: §5.3 one sentence (training vectors all nonnegative, so the evasions are unseen vectors, what
  Gimenez et al.'s Proposition 3 excludes, credited); Appendix D one sentence on the training and both setups.

### R3: the hand-analysis evidence is thin
**Verdict:** cheap fix. The authors' own hand table cannot produce an evasion when detected malware sit far above the
threshold, so present it as the illustration of why hand analysis errs and give D-Q8's margins (how many detected
malware sit within the 1.57-logit maximum drop), from stored scores. Let the expert set carry the measured claim, with
the eleven lowerable features and their edits named (restoring the default stub; renaming); MAB-Malware's renames
(4/8, decision 12) already widen its evidence. Independent analysts writing blind tables cost far more than they add;
dismiss that part.

### R17: Theorem 1 is stated beyond its proof, and the class is universal
**Verdict:** cheap fix. A alone raises it, but it is A's lead weakness. Each part is a sentence: any mapping fits with
one item holding the whole input, and the results are informative when items are local; Theorem 1's hypothesis
(totally ordered monoids whose operation is monotone); the ratio's side condition carried into Definition 10, with why
it holds on EMBER. A-W3 (3), the sectionless-file hole, has a false premise (the minima are 0 on every file), but
Appendix D's "as 0 for a file without sections" (`_j2_ember.tex:17-18`) invited it and must be corrected.
**Earlier decision:** session 53b (PLAN.md, next step 2): the ratio's zero case and totally ordered monoids fixed,
locality not a gap; differs in part: locality is not a gap in the proof, but the universality sentence answers A's
claim that "broad class" is vacuous, which is about §2's class claim, and costs one sentence.

### R15: the threat model's scope; no named attacker
**Verdict:** cheap fix. The exclusions are settled (decision 9) and stay. Two writing fixes hold: name the attacker
once (binary only, structural edits, no recompilation, packing or code rewriting), and reword "much harder to apply
without breaking the program" (`_e_instances.tex:78`), which Lucas et al. 2021 contradict by preserving functionality
through conservative disassembly; the exclusion is our scope, not their failure. The monotone detector's split-gain
share on fixed features (D-W3) is a cheap number for that sentence. A LIEF rebuild operation is optional and lowest
priority; dismiss it for now.

### R9: what Proposition 1 enables
**Verdict:** dismiss, except one wording fix. No reviewer says Proposition 1 lacks a finding; C and D ask for timing,
which is settled out, and B calls the attack circular, which extraction-scored candidates remove. Rebuttal: "Proposition
1 states the exact side effects of an edit from its item delta; Pierazzi et al. estimated gadget side effects in advance
on a minimal app, and Proposition 1 gives them exactly on the actual host; the directions of Theorem 1 are its
decomposition applied to every edit at once." The wording fix is A-W5's: "exact" means exact given the delta, which the
instance computes for every edit it does not decline, with the declines reported in Table 9.
**Earlier decision:** decision 12 (iii) (PLAN.md, session 49): `--score real` at the scale-up and §2 stays as it is,
not to be raised again; agrees: the work-count proposal of the meta-review would edge toward the timing claim the user
excluded, and nothing in the reviews needs it.

### R5: Pierazzi et al. portrayed loosely
**Verdict:** cheap fix. One reviewer, but accuracy about cited work outranks a sharper argument, and Pierazzi or
Cortellazzi may review. §2 and §6 say side effects "generally cannot be computed in advance" (`_c_background.tex:35`,
`_g_related_work.tex:10`); give their reason (the side-effect function cannot be expressed in closed form), credit their
minimal-app estimate as the closest precedent of Proposition 1, which computes the same thing exactly on the host, and
cite the TOPS 2025 version.

### R21: prior work misattributed or missing
**Verdict:** cheap fix. "100 queries per file, as in Gimenez et al." (`_f_evaluation.tex:52`) is right only for their
released code; say so. Add a short paragraph on certified malware defenses (RS-Del, DRSM, Gibert et al., Giri et al.):
bounded byte edits or a feature radius against unbounded but typed edits, the question a reader will ask ("why not
smoothing?"). Cite Zainab et al., Kantchelian et al. and Calzavara et al. (verification of the model, not the
extractor), Lucas et al. 2024, Tsingenopoulos et al. and Cortellazzi et al., checking each against `papers/` first.

### R12: counts include unmodeled features
**Verdict:** cheap fix. Nobody raised it, but I would fix it unprompted: §5.3's "928 of the 1,070", "the other 142" and
PV's hole of "124 ... 38.8%" count the 88 parser warnings that §4.2 drops. The meta-review's recount (915 of 982; PV's
hole 56 modeled features carrying 36.2% of the gain) leaves the finding intact; use it, and check ERDALT's 90% the same
way. It also removes the ground under C-W3's "122 unconfirmed".

### R14: the header-field overwrite is never validated or used
**Verdict:** investigate. The operation is wholly declined by the computation (three of its fields lie in the Rich
header's search range), so it has no exactness row and the stored adaptive runs never used it. Scoring by extraction
brings it into the attack, which is the R1 question; whether it also deserves a narrower definition (fields outside the
Rich range, then predictable) depends on whether the extraction-scored attack finds anything with it. Either way,
Appendix D owes one sentence on why it is declined.
**Earlier decision:** decision 12 (iii) (PLAN.md): `--score real` covers all twelve operations, header-field overwrites
included; agrees: it makes the attack cover the threat model without redefining the operation.

### R8: the expert-set comparison
**Verdict:** cheap fix. Name the eleven lowerable features and the edit behind each, quote Gimenez et al.'s criterion
("difficult to change for an attacker with no access to the malware source code"), and add one sentence in Appendix D
that their features were re-implemented with two accumulation fixes and a byte comparison for the stub flag, since the
authors are likely reviewers and will see different numbers. Same edit as R3's naming.

### R13: instrumentation effort
**Verdict:** cheap fix. Lines of code and person-days are settled out (no effort claims); dismiss that part. The counts
of the trusted parts (item kinds, declarations, recorded locating rules) go into R2's paragraph, which is the honest
version of what C and D ask.

### R16: PE minutiae
**Verdict:** dismiss. No reviewer raised it, and A, C and D praise the parser facts in §5.2. Keep them where they
explain why a hand table errs; nothing to write.
