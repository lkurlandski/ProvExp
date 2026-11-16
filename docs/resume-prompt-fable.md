# Resume prompt: the cost of robustness, step 2 (written 2026-11-16, session 72)

Paste into a fresh session. Read `docs/evidence/fable-cost-of-robustness.md` first: §2.1-2.3 (the two orders,
Proposition B, signature slack and sign slack, Proposition E), §7 (the discussion with the user and the candidate
theorem), §8 and §8.1 (step 1's results). Then §3.3 (*Sound Directions*) of the manuscript with Definitions 7-9,
Theorem 1 and Corollary 1 (numbers from `manuscript/main.aux`).

## Where things stand

- **Step 1 is done.** Experiments 1-3 ran at pilot scale (§8); §5.4's *Where the cost lies* is rewritten (Opus
  session, committed in 9b5825c; the user has seen it).
- **Boosting rounds: every detector stays at 500 (user, session 72). Do not reopen it.** The round comparisons of §8
  and §8.1 were made on the pilot's 10% training subsample and say nothing about the full training set; the user's
  experience there is that rounds past 500 add very little. Raising the cap is an end-stage option of the user's,
  for all detectors together. Open, the user's call: the last sentence of *Where the cost lies* still reports the
  3,000-round aside beside 500-round numbers; I recommended cutting it and got no answer.
- **Lesson from session 72:** before measuring anything on the pilot stores, say in the first sentence whether the
  question depends on the amount of training data (rounds, capacity, learner comparisons do). If it does, the pilot
  cannot answer it; say so and do not report numbers as if it could. Report facts and their limits before
  recommendations, and never compare models trained under different settings.

## Step 2: what it is

Today: a score that is monotone with respect to the table is unevadable (Corollary 1). The candidate result is the
converse as a theorem: **under a condition that can be checked on the signature, every unevadable detector on these
sums is monotone with respect to the table.** Theorem 1 says the table is sound; this would say that, for detectors,
it loses nothing, so the cost of robustness is the price of the threat model for this extractor and not of our
construction. The user hoped for a second result on the order of Theorem 1; my estimate in session 71 was about even
odds that a bounded session yields one.

What is missing (§7):

- Proposition B assumes "the table is complete", which restates the conclusion. Needed: a condition on the signature.
  My guess has two parts: every change in the signature is realizable by an edit on every population input where it
  applies (no signature slack), and every one-sided sum can be moved on its own up to identities that hold on the
  population (no sign slack).
- Bundling: the condition holds for the import block, but an added import also brings bytes and strings into other
  sums. A block-by-block statement looks provable; a clean statement over the whole EMBER table may not exist.
- Novelty is unchecked.

## Order of work

1. **Literature check first** (CLAUDE.md: read the closest work on the same task before building). Is a converse
   stated anywhere: that a detector robust to a set of transformations must be monotone in the order they induce?
   Start with Gimenez et al. (sufficiency only, checked in the PDF), Incer et al. 2018, Chen et al. 2021, the papers
   citing them, and the monotone-classification and abstract-interpretation (completeness of an abstraction)
   literatures. Check claims against PDFs in `papers/`; mark anything from memory as such. This part is search and
   reading and can be done in an Opus session.
2. **A short math note for the user's review** (in the findings file or a new file under `docs/evidence/`): the
   condition, the statement, the proof, the import block as the worked case, and what bundling does to it. Plain
   version first, then the mathematics.
3. **Stop rule (proposed in session 71):** if the statement needs more than one new definition, or bundling cannot
   be handled in a remark, it stays the two-sentence remark it is now. Report that outcome as it is.
4. Nothing goes into the manuscript before the user has read the note and agreed.

## Constraints

- No extractor changes, no anchored sums, no verified signatures (rejected, §7). No new experiments are planned for
  step 2; if a check on data seems needed, propose it with its hypothesis first, and see the lesson above.
- The framework stays format-free: the condition must be stated on items, sums, changes and the signature, never on
  PE specifics; the import block is an example, in the instance sections.
- Be harsh about novelty, and do not present elementary order theory as ours.
- Update `docs/status.md` at the end of the session.
