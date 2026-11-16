# Resume: the theory track, continued (first, choose a direction with the user)

**Update, session 75 (2026-11-16):** the direction is chosen: bounds on size (section 5). The mathematics note is
`docs/evidence/theory-analysis.md`, part F, and waits for the user's review and the four decisions of F.7. Start
there, not with section 1's choice; sections 2, 6, 8 and 9 still apply. The four small ideas (section 4) are set
aside by the user.

Written at the end of session 74 (2026-11-16). Self-contained; paste it into a fresh session or say "read
`docs/resume-prompt.md` and carry it out". The head-node session for the scale-up is a separate track:
`docs/resume-prompt-head-node.md`.

## 1. The job

The user wants **the theoretical contributions of the paper made stronger**. Session 74 audited the proofs and added
two things to §3.3. This session continues, and **its first business is a decision, made with the user: which
direction to work on.** Do not start on any direction before the user has chosen. The choices:

1. one of the four remaining ideas of session 74 (section 4);
2. **bounds on size instead of signs** (section 5), which the user called "an incredibly meaningful direction";
3. a new direction from brainstorming, if the user prefers to look further.

Open the session with a short message: where the theory stands (section 3, in a few lines), the choices with one
plain sentence each, and your recommendation with its reason. Then wait.

## 2. How to work (rules the last sessions paid for)

- **Read first:** `docs/status.md`, `PLAN.md` ("Thesis", next step 8, "Settled decisions"), then
  `docs/evidence/theory-analysis.md` in full (the record of session 74), then §3 and Appendices B-C of the
  manuscript (`_d_framework.tex`, `_i2_types.tex`, `_j_proofs.tex`). §2, §4 and §6 when the direction needs them.
  Paper numbers come from `manuscript/main.aux`.
- **Stay on theory.** No experiments, no detector training, no extractor changes. If an idea needs data, say what
  and why, and stop there. Reading code to check how the theory is used is fine. The manuscript is edited only with
  the user's approval, in the way of section 6.
- **Kill an idea cheaply before developing it.** Look for a counterexample on the extractor of Algorithm 1 (records,
  tokens, elements) first. Report a dead idea as dead, with its counterexample.
- **Check the graveyard and the archive before proposing or dismissing anything**, and then report both what failed
  earlier and what has changed since. An old negative result is not a verdict (memory
  `old-negative-results-are-not-verdicts`): in session 74 Claude dismissed bounds on size by pointing to direction
  A', and the user objected, rightly.
- **Say plainly when something is elementary, already published, or false.** Do not present elementary order theory
  or another field's standard result as ours. The user accepts small results that remove a premise or factor rules
  for reuse, when they are called what they are.
- **Plain language first, then mathematics.** One idea per paragraph. State a result so that its content is visible:
  in session 74 a lemma was first stated with a needless closed superset and read as obvious ("isn't a subset of a
  closed set closed?"; it is not). If the user finds a statement obvious, suspect the statement.
- **Do not promise.** Say what is proved, what is believed, and what is unknown, in those words.
- **One idea at a time**, reported after each. No option menus with invented names; no subagents.

## 3. Where the theory stands

`manuscript/main.aux` has: Definitions 1-10, Proposition 1 (*Exact side effects*), Theorem 1 (*Sound directions*),
**Lemma 1 (*Closure*)**, Corollary 1 (*Robustness*), Table 1 (the readout forms), Equation 11 (**the readout rule**),
Table 7 (the sign table, Appendix C).

- **The proofs were audited in session 74** and are correct. Seven small corrections are applied.
- **Lemma 1 (*Closure*), new.** If the population is the set of inputs on which some features stay at or below given
  values, and the derived table does not allow these features to rise, the population is closed under the threat
  model. So closure follows from covering and the table when the population is defined through items ("no item of an
  unwanted form").
- **The readout rule, new.** A readout rises with some of its sums, falls with others, and reads the rest in some
  other way; the feature's direction is the union of what they pass on. It replaces Table 1's six rules, defines the
  derived table (Definition 10), and covers totals, differences and means without new proofs. Unnumbered by the
  user's decision: it is a factoring of elementary rules for reuse, not a result.
- **The user approved both after a brief look and has not read them closely.** Expect comments on wording.
- **Where the theory is thin** (`theory-analysis.md`, part B): it is silent on item size; covering is checked on a
  corpus, not proven; the table is sound with nothing said about how loose it is; Corollary 1 is one-way;
  Proposition 1 has no consequence inside the theory; §5.3's finding has no statement behind it.

## 4. The remaining ideas of session 74

Each is in `theory-analysis.md`, part C, with the check on Algorithm 1 and the strongest argument against it. All are
elementary and of remark size; none is proved in writing yet.

- **C.3, item size.** The hoped-for monotone trade-off is **false both ways** (two counterexamples on record). What
  survives: tables from different item maps can be intersected; the one-item limit is the least sound table by
  definition; Proposition 1's delta only shrinks as items get finer. The user's stated interest. Touches the
  "tightness" that the mock lists as dropped.
- **C.4, the blind spot of a table learned from attacks.** It is exact for the attacks seen and silent on the same
  operations with other content; the derived table for the same operations with any content is the difference. A
  statement behind §5.3. Does not cover ERDALT's linear layer without the relational rule the user declined.
- **C.5, side effects and the host.** The same delta changes every additive sum by the same amount on every host;
  the host enters only through the sums a readout reads. A consequence of Proposition 1 that answers Pierazzi et
  al.'s two-hosts remark.
- **C.6, threat models add up.** The table of a union of threat models is the union of their tables, and on a
  population closed under both no combination of operations moves a feature where no single one does. Behind §5.4's
  per-operation reading; says what closure buys.

## 5. Bounds on size instead of signs

**Status: open, wanted by the user, not started.** The idea: bound how far a budget can move each sum and feature,
not only which way, so that a detector may also rely on features that a realistic budget cannot move far.

- **What was tried.** Direction A' (`docs/graveyard.md`, dropped 2026-11-02): a sound region per file and budget,
  with an exact solver over the trees. It certified nothing above 4 KB, against a budget of 5% of the file or 512 KB.
  The user: that was "at a much earlier point. A lot has changed since then."
- **What has changed since** (Claude's reading, untested): A' certified fragile detectors, and the question can now
  be what a *robust* detector may read beyond the one-sided features; A' bounded features and lost precision in the
  formulas, and detectors can now read the sums, where one added element moves one count by exactly one; the
  signature gives a place to state what each change costs; the readout rule maps a box of sums to the interval
  between two of its corners, unchanged.
- **Obstacles to design around, not verdicts:** the domain has no natural small budget; a header field or a presence
  bit covers its whole range with one write, and the pilot's price list puts most of the cost of robustness in the
  constraints for imports and header writes; the guarantee would be per file and budget, not for every file of the
  population.
- **How to start, if chosen:** as Sound Directions round 4 did. A short note that settles the mathematics (the
  objects in order, each with why the result needs it), a counterexample hunt on Algorithm 1, the user's review,
  and only then any thought of an experiment. Read `docs/archive/a-prime/` only to learn what failed and why.

## 6. How the manuscript was changed in session 74 (keep to it)

1. The idea is worked out in `docs/evidence/theory-analysis.md` (statement, proof, the check on Algorithm 1, what
   reading the code says about EMBER, proposed text).
2. On the user's go, the text goes into the manuscript **uncommitted**; the user sees it as rendered text with a
   list of the choices made, reviews, and approves the commit.
3. A statement that belongs to the framework gets its own environment in §3 (`\lemma`, `\theorem`, ...) with the
   proof in Appendix C. A paragraph in §3 that only points to the appendix was rejected ("splits the baby"): either
   the idea is part of the framework, or its mention is much shorter.
4. Prose with the project skill `paper-prose`; `make` and `make check` in `manuscript/`; small diffs.

## 7. Follow-ups that are not this session's work

Listed in `docs/status.md` and PLAN.md, next step 8 (c). Do them only if the user asks.

- The instance-level work for Lemma 1: the population's clauses as counts over items, the derived table rebuilt, the
  nine in-place and append operations confirmed, the four layout-moving operations decided. §4.4 still says closure
  is checked, and stays so until then.
- `monotone_violations` called in `4-detectors/train` before the scale-up trains; §5.1's blue sentence waits for it.
- Optional: the tighter rule for a normalized bin in `reach.py`.
- One overfull vertical box of 1 pt in Appendix D since the readout rule went in.

## 8. Settled; do not reopen without a strong, specific reason

- Closed in sessions 71-73: converses of Corollary 1 (false in general), bounds on the cost of robustness computed
  from data, feature engineering as theory, boosting rounds (500 for every detector). The record,
  `docs/archive/fable-cost-of-robustness.md`, is not read by default and not used for the paper.
- That every feature mapping meets Definition 5 is a property of the framework, not a gap (user, session 53b).
- The relational refinement of the sign table was declined as machinery without payoff on EMBER.
- The formalization is a contribution; be harsh but fair about novelty; credit foundations without a
  borrowed-versus-new ledger. Elegant fixes only, reusing a mechanism the framework has. Proofs carry the weight.
- The framework is format-free: no PE specifics in §3. No timing claims, no effort claims, no packing motivation, no
  sandbox execution, no extractor redesign for robustness.
- Cited work in its authors' terms, checked against the PDF in `papers/`.

## 9. Output and housekeeping

- Continue `docs/evidence/theory-analysis.md` with new parts (F onward) for this session's ideas; commit after each
  part. Do not push.
- At the end: `docs/status.md`, PLAN.md's next step 8, `docs/README.md` if a document was added, and this file
  rewritten for the session after.
