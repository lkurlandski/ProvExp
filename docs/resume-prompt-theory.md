# Resume: the theory track, bounds on size (the user's review of the note comes first)

Written at the end of session 75 (2026-11-16). Self-contained; paste it into a fresh session or say "read
`docs/resume-prompt-theory.md` and carry it out". The main line (the scale-up running on tigris) is a separate track
with its own prompt, `docs/resume-prompt.md`; do not mix the two.

## 1. The job

The user wants **the theoretical contributions of the paper made stronger**. In session 75 the user chose the
direction: **bounds on size instead of signs** ("the right direction"; earlier, "an incredibly meaningful
direction"). Bound how far a budget can move each sum and feature, not only which way, so that a detector may also
rely on features that a realistic budget cannot move far.

Session 75 wrote the mathematics note: `docs/evidence/theory-analysis.md`, **part F**. The user has seen only a
summary of it and has not answered its four questions. **This session opens with the user's review of the note and
those answers (section 4). Do not develop anything further before them.**

Open with a short message: the statement in plain words (section 3, a few lines), what is against it, and the four
questions. Then wait.

## 2. How to work (rules the last sessions paid for)

- **Read first:** `docs/status.md`, `PLAN.md` ("Thesis", next step 8, "Settled decisions"), then
  `docs/evidence/theory-analysis.md` parts B, E and F in full (A, C, D when needed), then §3 and Appendix C of the
  manuscript (`_d_framework.tex`, `_j_proofs.tex`). Paper numbers come from `manuscript/main.aux`.
- **Stay on theory.** No experiments, no detector training, no extractor changes. If an idea needs data, say what
  and why, and stop there. Reading code is fine; reading stored results needs the user's go (question 2 below). The
  manuscript is edited only with the user's approval, in the way of section 6.
- **Kill an idea cheaply before developing it:** look for a counterexample on Algorithm 1 first, and report a dead
  idea as dead, with its counterexample.
- **An old negative result is not a verdict.** The user asked that `docs/archive/a-prime/` be read "with a heavy
  grain of salt (its very possible there are mistakes and poor reasoning here)". Part F.2 records where its
  reasoning does not hold up. Do not cite A' as settling anything.
- **Say plainly when something is elementary, already published, or false.** Do not promise: say what is proved,
  what is believed, and what is unknown, in those words.
- **Plain language first, then mathematics.** One idea per paragraph. If the user finds a statement obvious, suspect
  the statement.
- **One idea at a time**, reported after each. No option menus with invented names; no subagents.
- The four small ideas of session 74 (`theory-analysis.md` C.3-C.6: item size, the blind spot of a learned table,
  side effects and the host, threat models add up) are **set aside by the user**, who may pursue them alone or in
  another session. Do not raise them.

## 3. Where the note stands (part F)

**The statement, in plain words.** Give every edit a cost (elements written or added) and the attacker a budget $B$.

1. Every change in the signature gets a size; the signature *covers within budget* if an edit's changes, kind by
   kind, total at most the edit's cost. This is the instance's premise, as covering is.
2. Each additive sum gets two *rates*: the most one unit of budget can raise it, and lower it. The sum moves by at
   most rate times $B$. A direction of the paper is the record of which of the two rates is not zero.
3. The readout rule carries the box of sums to an interval per feature: the readout's values at two corners (the
   *corner rule*; it needs the readout monotone on the whole box, which the readout rule does not).
4. A score that is monotone in every feature it reads is smallest, within the budget, at one computed vector (the
   *worst corner*). A file is certified at budget $B$ if that one score is above the threshold: no solver.

Theorem 1 and Corollary 1 are the case of an unlimited budget. **Proved in the note:** the bound on additive sums,
the upper side of a max pool, the corner rule, the containment of Theorem 1, the worst corner. **Believed, not
written out:** the lower side of a pool (it needs the item table, the first use of Proposition 1's record inside
the theory) and the two repairs below.

**What broke on Algorithm 1 (F.4).** One budget shared across kinds of item is false (count kind by kind). The
corner rule on the values that occur only is unsound (size / records with a record removed). "The worst case is the
whole budget on one kind of change" is false in general (distinct tokens). The one systematic loss: the sums share
one budget and the box forgets it; two elementary repairs exist (bound the total movement in a support; for ratios
and shares, the extremes are reached by pure edits). Where one element can complete or relocate an item, the rate is
infinite and the theory returns the sign, which is the right answer for a header field.

**What is against it, said to the user in session 75.**
- It is elementary: intervals after signs is the textbook order of abstract interpretation. What would be ours is
  what was ours for signs, the chain from a budget on edits to a certificate.
- Closest work: Chen et al. (CCS 2021, `papers/chen2021learning.pdf`, checked) train with a "small neighborhood"
  property whose distance is chosen from domain knowledge. **Not checked, from memory only, to read before any
  claim:** Chen et al., *Cost-Aware Robust Tree Ensembles for Security Applications* (USENIX Security 2021), and
  Vos and Verwer's robust trees for per-feature ranges. Neither PDF is in `papers/`.
- The payoff on EMBER looks small at 1% false positives, by the pilot's price list in §5.4: of the 7.8 points the
  guarantee costs, 3.9 are the copied signature, 2.1 import addition, 1.4 header overwrites, each flipped by one
  write or a few dozen bytes, which no byte budget bounds; about 0.2 points are the two-sided features. At 0.1% the
  two-sided features are worth 5.2 points, and whether any of that is recoverable depends on why each is two-sided
  (not looked at).
- A' does not bear on the statement (F.2): it ran an exact solver over a detector not built for a certificate, at a
  budget above the file's own size on 26 of 50 files.

**New since the note, from the other track:** the price list has now run at scale on tigris, and decision 12
(PLAN.md) found 96 `body_strings:printable_*` features two-sided under a section rename in the training table. Both
bear on question 2; neither has been read for this track.

## 4. The four questions that wait for the user (F.7)

1. Is the statement of section 3 what the user meant by "bounds on size", or was something else in mind?
2. May Claude read the stored derived table (and, if available on this machine, the scale-up's price list) to class
   each two-sided sum as bounded by a budget or not? A read, no run and no training; the cheapest way to learn
   whether EMBER can show anything. Claude's advice: yes.
3. The premise per edit (simple, parallel to Theorem 1; boundary items get an infinite rate) or for a whole
   sequence with an allowance per kind for boundary items (tighter, one more constant per kind, the instance must
   argue about sequences)? Claude's advice: the simple form until an instance needs the other.
4. The two repairs for the shared budget: now, or when a feature needs them? Claude's advice: wait.

After the answers, the likely next steps, in order and only as far as the user says: the read of question 2 with
its result reported plainly (a kill is a result); the two papers known from memory; the lower side of a pool
written out; then a decision with the user on whether the statement belongs in §3, in the discussion as one
paragraph on what the sign table discards, or nowhere.

## 5. Where the rest of the theory stands

`manuscript/main.aux` has Definitions 1-10, Proposition 1 (*Exact side effects*), Theorem 1 (*Sound directions*),
Lemma 1 (*Closure*), Corollary 1 (*Robustness*), Table 1 (the readout forms), Equation 11 (the readout rule),
Table 7 (the sign table, Appendix C). Lemma 1 and the readout rule were added in session 74 and approved after a
brief look; **the user's close read of both is still pending**, so expect comments on wording.

## 6. How the manuscript is changed (keep to it)

1. The idea is worked out in `theory-analysis.md` (statement, proof, the check on Algorithm 1, proposed text).
2. On the user's go, the text goes into the manuscript **uncommitted**; the user sees it as rendered text with a
   list of the choices made, reviews, and approves the commit.
3. A statement that belongs to the framework gets its own environment in §3 with the proof in Appendix C. A
   paragraph in §3 that only points to the appendix was rejected ("splits the baby").
4. Prose with the project skill `paper-prose`; `make` and `make check` in `manuscript/`; small diffs.

## 7. Follow-ups that are not this session's work

Do them only if the user asks (PLAN.md, next step 8 (c)): the instance-level work for Lemma 1; `monotone_violations`
in `4-detectors/train` (the scale-up has already trained, so this is now a check on the trained models, to agree
with the main-line track); the tighter normalized-bin rule in `reach.py`; one overfull vertical box of 1 pt in
Appendix D.

## 8. Settled; do not reopen without a strong, specific reason

- Closed in sessions 71-73: converses of Corollary 1, bounds on the cost of robustness computed from data, feature
  engineering as theory, boosting rounds. `docs/archive/fable-cost-of-robustness.md` is not read by default.
- Every feature mapping meets Definition 5: a property of the framework, not a gap. The relational refinement of
  the sign table was declined as machinery without payoff on EMBER (the two repairs of F.4 are of that family:
  propose them only with evidence of need).
- The formalization is a contribution; harsh but fair about novelty; credit foundations without a borrowed-versus-new
  ledger. Elegant fixes only. Proofs carry the weight.
- The framework is format-free. No timing claims, no effort claims, no packing motivation, no sandbox execution, no
  extractor redesign for robustness. Cited work in its authors' terms, checked against the PDF in `papers/`.

## 9. Output and housekeeping

- Continue `theory-analysis.md` with part G onward; commit after each part. Do not push.
- The other track edits `docs/status.md`, `PLAN.md`, `docs/README.md` and `docs/resume-prompt.md` too. Keep this
  track's edits to its own paragraphs there, and rewrite **this** file, not `docs/resume-prompt.md`, at the end.
- Two sessions were numbered 74 (the head node on tigris, and the theory session); the theory track's are "74
  (theory)" and 75.
