# Resume prompt (writing track): §3.3 with its appendix material, then the rest of §3, §4 and §5

Written 2026-11-19 (end of session 93). The scale-up runs on tigris; nothing here depends on its numbers. Read
`CLAUDE.md` and this prompt; open the section under review (`manuscript/_d_framework.tex`, `_e_instances.tex`,
`_f_evaluation.tex`), the appendix that holds its proofs (`manuscript/_j_proofs.tex`, Appendix C *Proofs for the
Framework*), the symbol table (`_i_symbols.tex`, Appendix A) and `manuscript/_c_background.tex` (§2, which the reader
is assumed to have read carefully) only as the work needs them. Run on Opus. No subagents unless the user asks.

## Where the writing stands

- **§6 Related Work is done for now** (session 84). Do not reopen it unless the user asks.
- **§3.1 *Sum-then-Readout Extractors* is reviewed** (session 92, commit 0185d58). The user rejected one finding: the
  sentence after Definition 1 on why the item map drops positions stays as it is; do not raise it again. Its appendix
  material (Appendix B *Types, Monoids, and Folds*) has **not** had the new treatment below; raise it at the holistic
  review of §3 (step 3) and let the user decide whether it gets one.
- **§3.2 *Edits and Their Side Effects* and its appendix material are done** (session 93, commits 2eec34b, 0c0da24):
  a review pass, then the split with Appendix C. The body now states Proposition 1, says what each part means and why
  it holds in plain words, why the result is exact (tied back to §2's "cannot be computed in advance"), and what it
  costs; Appendix C holds the proof and a short paragraph *Computing part (ii)* (why the item table is needed). The user
  had the {5, 3} / {5, 5} pool example removed from the appendix. Proposition 1 (ii) now covers every non-additive sum
  ("every other sum"). Do not reopen §3.2 except through the holistic review.
- **Deferred to the holistic review of all of §3, after §3.3:** recurring sentence patterns and the term ledger.
  Collected so far: "element" means an input's unit, a neutral element, an element of $\mathcal{S}$, and a loop kind in
  Algorithm 1; "extractor" is used in Definition 1 before Definition 5 defines it; edit vs transformation ("An edit
  applies a transformation", "the side effects of $T$"); sums vs totals ("the old total", "rule for totals");
  "contributes to" meaning "contributes a non-neutral value", never defined; "delta of a pair of inputs" (Definition 6)
  vs "the delta of one edit"; the entries of $I^-$ are "items" in the body but "pairs" in the appendix proof. Add
  further items from §3.3 here rather than reporting them as findings.
- **The paper-prose skill is not used** (the user, session 92). Draft fixes without it and do not ask.
- What the user said about earlier drafts is in `docs/writing-spec.md` (top entries): evidence of taste, not rules.

## The method: each subsection together with its appendix material (user, session 93)

The user wants a subsection's proofs polished in the same pass as the subsection, since the content is tightly
related. For each subsection, three steps:

1. **Review the subsection**: `humanistic-paper-review`, ranked findings with exact quotes, a verdict per finding
   before applying anything.
2. **Split and polish the appendix material**: propose how the content divides between body and appendix, with the
   proposed text of both, and review the appendix material (correctness of notation, steps asserted rather than
   derived, bare equation numbers used as arguments, terms). The split that worked for §3.2: the body keeps the
   statements, the conditions a reviewer would test, and the reason each result holds in a few plain sentences, with a
   pointer to Appendix C; the appendix keeps the derivations, each step stated, definitions named rather than equation
   numbers. Examples in the appendix are not wanted by default (the user removed the one in §3.2's).
3. **A final pass over the subsection and its appendix material together**: no overlap, no gaps, terms consistent.

In session 93 steps 1 and 2 were presented and approved separately, and the user approved the small fixes together;
apply them in one go: `make` and `make check` in `manuscript/`, read the rendered text (pdftotext), commit, report what
changed and the word counts (`texcount -brief`) of the section and the appendix before and after. For a large rewrite,
or if the user asks, go back to one fix at a time with old and new text.

Further: when a fix rewrites prose, rewrite the passage so it flows at its length. "This passage does not earn its
place" is not applied: add a line to `docs/review-cuts.md` (create it on first use). Numbers and cross-references come
from the compiled PDF (`manuscript/main.aux`), with the title alongside.

## The task, in order

1. **§3.3 *Sound Directions*** (`_d_framework.tex`, from `\subsection{Sound Directions}`) with its appendix material
   in Appendix C: the paragraphs *Directions*, the sign table (`tab:fw:signs`), *Directions of sums*, *Hashed keys*,
   *Patterns under extension*, *The readout rule*, and the proofs of Theorem 1, Lemma 1 (*Closure*) and Corollary 1;
   and §3.3's rows of the symbol table. The user has **not read §3.3 closely yet** and reads it only after its pass.
   Known overlap: the paragraph after Definition 9 (*Directions of sums*) argues the additive, max-pool and min-pool
   cases and the product counterexample, which Appendix C's *Directions of sums* repeats; the readout-rule paragraphs
   likely overlap Appendix C's *readout rule*. Expected split: the cases move to the appendix; the totally-ordered
   condition and the product counterexample stay in the body (they make the condition believable). The user asked
   whether the split shortens §3; for §3.2 it was neutral (4,389 to 4,390 words), for §3.3 a real saving is likely;
   report the counts. Two things noticed earlier, not yet raised: after Lemma 1, "The same holds for lower bounds on
   features that the table does not allow to fall" is followed by an example (a count of unwanted items bounded above
   by 0) that is the lemma's own case, not a lower bound; and Table 1's caption and the readout paragraph refer to the
   readout forms of §3.1, whose paragraph was rewritten in session 92 (the distinct count reads a whole family of sums
   and is not algebraic); check that they agree. §3 is at ~4,390 words against the mock's 3,500.
2. Then the **holistic review of §3** (patterns and the term ledger above; whether Appendix B gets the new treatment).
3. **§4 Instantiating the Framework** (`_e_instances.tex`, ~1,900 words): 4.1-4.4, with Appendix D *The EMBER
   Instance* (`_j2_ember.tex`) where it holds §4's material.
4. **§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words): 5.1-5.4. Numbers are pilot values; do not sync them. The user
   has not read §5 end to end.

§2 comes after these, in a later session: its closing sentence and contribution 4 of `docs/paper-mock.md` wait for the
user's discussion of the motivation (the prepared note is in `docs/status.md`'s session-80 entry, *C.6 note*). Not in
this round: the abstract, introduction, discussion, ethics, open science.

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`), the closest work: the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare against their method experimentally is the
  user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB) may be reconsidered later: do nothing now.

## At the end

Update `docs/status.md` (a short session-log entry) and commit the docs. Write the next resume prompt into this file
(archive this one first under `docs/archive/`).
