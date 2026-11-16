# Resume prompt: the cost of robustness (rewritten 2026-11-16, session 73)

Steps 1 and 2 are both done. There is no open work on this question unless the user decides otherwise.

- **Step 1** (experiments 1-3, *Where the cost lies*): `docs/evidence/fable-cost-of-robustness.md` §8, §8.1. Every
  detector stays at 500 boosting rounds (user); do not reopen it.
- **Step 2** (the converse of Corollary 1 as a theorem): negative outcome, the findings file's §9. The converse is
  false in general: on Algorithm 1's extractor under "add a record", the score `size - records` cannot be evaded and
  is not monotone with respect to the table. The stop rule applied (two new definitions, bundling not a remark).
  Nothing went into the manuscript.

## Waiting on the user (after they read §9)

1. Whether to add the two-sentence "least sound table" remark (§9.5, Proposition I) to §5.4 or §3.3. It is the
   "region's tightness" that `docs/paper-mock.md` lists as dropped, so it needs an explicit yes. It would need one
   count from the catalogue check's existing outputs (which non-fixed signs of the sums table are witnessed by an
   edit); state the hypothesis of §9.5 before counting.
2. Whether §6 cites Wang et al. 2022 (*Robust Learning against Relational Adversaries*, `papers/wang2022robust.pdf`,
   not in `main.bib`) beside Gimenez et al.

## Keep in mind

- Gimenez et al.'s Proposition 2 *is* a converse (existential: a post-processing built from the classifier). The
  manuscript's §6 says so correctly; never write "sufficiency only" again.
- Lesson from session 72: before measuring on the pilot stores, say whether the question depends on the amount of
  training data; if it does, the pilot cannot answer it.
- No extractor changes, no anchored sums, no verified signatures, no relational rule (all declined, §7 and §3.1).
