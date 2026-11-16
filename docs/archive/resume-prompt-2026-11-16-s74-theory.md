# Resume: the theory session (proof audit first, then ideas to strengthen the theory)

Written at the end of session 73 (2026-11-16). Self-contained; paste it into a fresh session or say "read
`docs/resume-prompt.md` and carry it out". It is written for whichever model the user chooses. The head-node session
for the scale-up is a separate track: `docs/resume-prompt-head-node.md`.

## 1. The job, and its order

The user wants **the theoretical contributions of the paper made stronger**. This session does that in two stages,
and the order is fixed:

1. **The proof audit** (section 4). Complete it, write it to the output file, commit, and report to the user.
2. **Brainstorming how to improve the theory** (section 5), only after the audit and **together with the user**:
   present candidates briefly, let the user choose, and work out only what they choose.

The session's output is one findings file, `docs/evidence/theory-analysis.md`. **It does not edit the manuscript, the
code, `PLAN.md` or the pipeline, and it runs no experiments.** Anything that would change the paper is proposed as
old and new text and waits for the user.

## 2. What went wrong before, so that it is not repeated

Sessions 71-73 (Claude Fable 5.2) were meant to strengthen the theory and did not. The user's judgement: the work
went off the rails, produced poorly conceived ideas and unsuccessful experiments, and was confusing. Everything it
changed in the manuscript and the pipeline has been reverted (commit 3944894). Concretely:

- The session narrowed "strengthen the theory" to one question (what the monotone detector's cost in detection is a
  cost of), then drifted from mathematics into pilot experiments and a rewrite of §5.4.
- It proposed feature engineering as theory (sums "anchored" to content the attacker cannot write; verified
  signatures). The user rejected both outright: a feature that is robust only until the attacker finds the anchor is
  not a contribution, and extractor redesign is not what the paper is about.
- It compared detectors trained under different settings and reported pilot-subsample numbers as if they bore on the
  full training set. **Boosting rounds stay at 500 for every detector; do not reopen it.**
- It gave an estimate of "even odds" for a second theorem and then spent a session finding the statement false.

Rules that follow, for this session:

- **Stay on the theory of §3 and Appendices B-C.** No experiments, no extractor changes, no detector training. If an
  idea seems to need data, say what and why, and stop there.
- **Kill an idea cheaply before developing it.** For every candidate result, first look for a counterexample on the
  extractor of Algorithm 1 (records, tokens, elements). Several plausible statements die there in five minutes.
- **Tell the user early and plainly** when an idea is elementary, already published, or false. Do not present
  elementary order theory or another field's standard result as ours.
- **Plain language first**, then mathematics. Short. One idea per paragraph. No option menus with invented names.
- **Do not promise.** State what is proved, what is believed, and what is unknown, in those words.

## 3. What is already known (do not redo)

The record of sessions 71-73 is `docs/archive/fable-cost-of-robustness.md`. **Do not read it by default** and do not
take text from it into the paper; open a section only when checking one of the facts below.

- **A converse of Corollary 1 is false in general** (§9.4 there). "Every detector no edit can evade is monotone with
  respect to the table" fails on Algorithm 1 under "add a record": the score *size − records* cannot be evaded and is
  not monotone with respect to the table (compare 1 record of size 10 with 5 records of size 11). The cause is one
  item feeding two sums that move by amounts no identity ties. It holds only on blocks where every contribution is
  a unit count (the import buckets).
- **Unevadable is equivalent to "no single change of the signature lowers the score"** when every change can be
  carried out on its own. True, elementary, and the one-sided form of Proposition 1 of Wang et al., *Robust Learning
  against Relational Adversaries*, NeurIPS 2022 (`papers/wang2022robust.pdf`; not in `main.bib`).
- **Gimenez et al.'s Proposition 2 is already a converse** of an existential kind (every robust detector is a
  monotone one after a post-processing built from the classifier). §6 of the manuscript says so correctly.
- **The derived table on the sums is the least sound table** if every sign in it is witnessed by some edit (§9.5).
  Two-line proof; it is the "region's tightness" that the paper mock lists as dropped.
- **No bound on the cost of robustness can be computed from data without a learner** (§2.4): the in-sample ceiling
  is 100% for every class of unevadable detectors.
- **A relational refinement of the sign table** (evaluating a weighted total of sums on each change; the dual cone of
  the change vectors) is sound and was declined by the user as machinery without payoff on EMBER. It is what ERDALT's
  linear layer learns from examples.
- **Five small corrections to §3.3 and Appendix C** are written up with old and new text in
  `docs/evidence/proof-notes.md`. None is applied; the user decides each. The audit should confirm or correct them,
  not rediscover them.

## 4. Stage 1: the proof audit

Read fully, in this order: `manuscript/_c_background.tex` (§2), `manuscript/_d_framework.tex` (§3),
`manuscript/_i2_types.tex` (Appendix B), `manuscript/_j_proofs.tex` (Appendix C), `manuscript/_e_instances.tex` (§4,
for how the theory is used: signatures of operations stated as writes come from a record of the positions the parser
reads and are *checked* on a corpus, not proven), `manuscript/_g_related_work.tex` (§6), `docs/evidence/r6-prior-work.md`,
`docs/evidence/proof-notes.md`. Then `PLAN.md` ("Thesis", "Settled decisions") and `docs/paper-mock.md` (the
contributions and "Dropped from the paper"). Paper numbers come from `manuscript/main.aux`: Definitions 1-10,
Proposition 1 (*Exact side effects*), Theorem 1 (*Sound directions*), Corollary 1 (*Robustness*), Table 1 (the
readout rules), Table 7 (the sign table).

Check Proposition 1, Theorem 1 and Corollary 1, and everything they use: the sign table, the readout rules and the
ratio's side condition, the total-order hypothesis, pools and their neutral elements, replacements against removal
plus addition, sequences of edits and closure, the hashed-keys and patterns-under-extension paragraphs, and Appendix
B. For each, one of four verdicts:

- **Correct as stated**: one line.
- **Wrong**: the smallest counterexample.
- **A real gap**: right in spirit, but a careful formal-methods reviewer would ask for a change. The smallest fix, as
  old and new text.
- **Pedantic**: one line at the end, or dropped.

Then half a page, in plain language: what the three results say together, what is new in them stated as strongly as
is honest, and where the theory is thinner than the paper's claims. Write part A (audit) and part B (this half page)
to the output file, commit, and **report to the user before going on**.

## 5. Stage 2: ideas to strengthen the theory (with the user)

"Stronger" means: a result that says more, a result that covers more (a larger class of extractors, weaker
hypotheses), a result that gives a finding of §5 a theoretical footing, or a cleaner formulation that makes the
existing results easier to appreciate.

Open questions the original prompt raised and that have **not** been worked on:

- **Learned versus derived constraints.** §5.3 finds that defenses learned from observed attacks miss edits they
  never saw. Is there a short general statement behind it, so that 5.3 is a consequence and not only an observation?
- **Closure and populations.** Theorem 1 needs a population closed under the threat model, and one write outside the
  threat model can take an input out. What can be said without closure, or about the largest population on which a
  table is sound?
- **Item size and locality** (the user's stated interest). Items are hierarchical and the framework applies at every
  granularity. Is there a precise statement of the trade-off between coarse and fine items, such as a monotonicity
  result across refinements of the item map?
- **The class itself.** Which extractors are sum-then-readout, what falls outside, and is there a characterization or
  a clean extension?
- **Proposition 1's own weight.** What does exactness enable beyond Theorem 1, for instance in relation to Pierazzi
  et al.'s side-effect vector? No timing claims.
- **A richer abstract domain than signs** (bounds on magnitude). Weigh it against the user's dislike of machinery and
  against the declined relational rule.

Already closed, see section 3: converses of Corollary 1, tightness of the table, bounds on the cost of robustness.

How to run this stage: give the user a short list (at most six candidates; for each: the statement in plain words,
whether you believe it and why, the check on Algorithm 1, what it would change in the paper, its cost in new
concepts, and the strongest argument against it). The user chooses. Only then attempt a proof or a counterexample,
one idea at a time, reporting after each. A clean failure is reported as a failure.

## 6. Settled; do not reopen without a strong, specific reason

- The formalization is a contribution; be harsh but fair about novelty. Credit foundations as foundations, never as
  a borrowed-versus-new ledger that concedes each result (the novelty is the combination).
- Elegant fixes only, for gaps a real reader cares about; prefer reusing a mechanism the framework has over a new
  hypothesis or clause. Loophole findings no reader cares about are not problems.
- Proofs carry the weight: no machinery or pages for assumptions that are checked on a corpus.
- The framework is format-free: no PE specifics in §3. The domain is adversarial examples in practical security tasks.
- No timing claims, no effort claims, no packing motivation, no sandbox execution, no extractor redesign for
  robustness.
- Dropped earlier for complexity, not for being wrong (the mock's "Dropped from the paper"): coupling, the region's
  tightness, a cost theorem, the old Theorems 2-3. Bringing one back needs an explicit argument and the user's yes.
- Portray cited work in its authors' terms and check every claim about it against the PDF in `papers/`; mark
  anything from memory as such.

## 7. Output and housekeeping

- `docs/evidence/theory-analysis.md`: A. proof audit; B. the theory in brief; C. candidate ideas (after the user has
  seen A and B); D. proofs or counterexamples for the ideas the user chose; E. what to do next, in a few sentences.
  Commit after each part. Do not push.
- At the end, update `docs/status.md` (its "Waiting on the user" entry for the proof notes and its session log).
- Do not spawn subagents.
