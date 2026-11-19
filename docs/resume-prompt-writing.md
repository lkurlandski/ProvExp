# Resume prompt (writing track): the holistic review of §3, then reorganize Appendix C, then cut §3 by ~20%

Written 2026-11-19 (end of session 95). Nothing here depends on the scale-up on tigris. Read `CLAUDE.md` and this
prompt. Then read all of §3 (`manuscript/_d_framework.tex`, ~4,320 words) and its appendices: Appendix A *Symbol
Table* (`_i_symbols.tex`), Appendix B *Types, Monoids, and Folds* (`_i2_types.tex`, ~390 words) and Appendix C *Proofs
for the Framework* (`_j_proofs.tex`, ~1,385 words). Open `manuscript/_c_background.tex` (§2, which the reader is
assumed to have read carefully) only where the work needs it. Run on Opus. Use no subagents unless the user asks.

## Where the writing stands

- **§6 Related Work is done for now** (session 84). Do not reopen it unless the user asks.
- **§3 now has four subsections**, each reviewed together with its appendix material:
  - §3.1 *Sum-then-Readout Extractors* (session 92, 0185d58). The user rejected one finding: the sentence after
    Definition 1 on why the item map drops positions stays as it is, so do not raise it again.
  - §3.2 *Edits and Their Side Effects* (session 93, 2eec34b, 0c0da24).
  - §3.3 *Sound Directions* and §3.4 *Robust by Construction*, split in session 95 (0587b86). §3.3 holds the
    signatures, the directions of sums, the readout rule, Theorem 1, and the abstract-interpretation paragraph. §3.4
    holds closure and Lemma 1, monotone detectors and Corollary 1, plus a closing paragraph (the guarantee needs no
    attack and covers every sequence of edits; §5.4 measures its cost). The user has not read §3.3 and §3.4 closely
    yet.
- **The split that worked** (sessions 93 and 95): the body keeps the statements, the conditions a reviewer would test,
  and the reason each result holds in a few plain sentences, with a pointer to Appendix C. The appendix keeps the
  derivations, with each step stated and definitions named instead of cited by equation number. The user does not
  want examples in the appendix by default.
- **The paper-prose skill is not used** (user, session 92). Draft fixes without it and do not ask about it.
- What the user said about earlier drafts is in `docs/writing-spec.md` (top entries). Read it as evidence of taste,
  not as rules.

## How to work

- Use ranked findings with exact quotes, and get a verdict on each before applying anything. The user usually approves
  the small fixes together; apply them in one go. Then run `make` and `make check` in `manuscript/`, read the rendered
  text (pdftotext), commit, and report what changed with word counts (`texcount -brief`) before and after.
- For a large rewrite, or if the user asks, go back to one fix at a time with the old and new text.
- When a fix rewrites prose, rewrite the passage so that it flows at its new length.
- Do not apply a "this passage does not earn its place" finding. Add a line to `docs/review-cuts.md` instead; one
  entry is there already (Appendix C, *Patterns under extension*, which nothing refers to).
- Take numbers and cross-references from the compiled PDF (`manuscript/main.aux`), with the title alongside.

## The task, in order

1. **The holistic review of all of §3 with Appendices A-C.** Read §3 as one piece. Look for:
   - recurring sentence patterns across the subsections;
   - overlap or gaps between subsections, and between the body and the appendices;
   - whether the four subsections hand off to each other (the §3 roadmap paragraph was updated for §3.4 only in
     passing).

   Use `humanistic-paper-review`. Report the term ledger as its own block. These items were collected in sessions
   92-95:
   - "element" means an input's unit, a neutral element, a member of $\mathcal{S}$, and a loop kind in Algorithm 1.
   - "extractor" is used in Definition 1 before Definition 5 defines it.
   - Edit vs transformation: "An edit applies a transformation", "the side effects of $T$", and Definition 7's "a set
     of transformations …, the single edits the attacker may apply".
   - Sums vs totals: "the old total", "rule for totals".
   - "contributes to" means "contributes a non-neutral value" but is never defined.
   - "delta of a pair of inputs" (Definition 6) vs "the delta of one edit".
   - The entries of $I^-$ are "items" in the body but "pairs" in the appendix proof.
   - "change" means both an item change $c \to c'$ (Definition 8) and the change of a feature's value (Definition 7,
     Theorem 1).
   - Three verb pairs for related ideas: a change "raises/lowers" a sum, a readout "rises with/falls with" sums, and
     directions are "up/down".
   - "monotone" names a Table 1 row (a nondecreasing $g$), "monotone with respect to $D$" (the detector), and Gimenez et
     al.'s notion.

   Also decide with the user whether Appendix B gets the same treatment as Appendix C. It has not been reviewed
   against §3.1.
2. **Reorganize Appendix C** (user, session 95). It is now a flat run of `\paragraph`s in this order: the proof of
   Proposition 1, *Computing part (ii)*, *Directions*, Table 7 (the sign table), *Directions of sums*, *Hashed keys*,
   *Patterns under extension*, *The readout rule*, then the proofs of Theorem 1, Lemma 1 and Corollary 1. Propose a
   structure before moving anything, for example one block per body subsection (§3.2, §3.3, §3.4) in the body's order,
   with the supporting lemmas before the proofs that use them. Show the outline and get approval first.
3. **Cut §3 by about 20%** (user, session 95): from ~4,320 words to ~3,450, which is about the mock's budget of 3,500.
   First present a plan per subsection: where the words go and what each cut costs the reader. Moving material to the
   appendix counts, but only where the split rule above allows it. Then apply the cuts after approval. The holistic
   review will already have found some of the cuts; fold them in rather than counting twice. For §6 (session 84), a
   30% cut planned paragraph by paragraph worked, with every change approved.
4. Then **§4 Instantiating the Framework** (`_e_instances.tex`, ~1,900 words) with Appendix D *The EMBER Instance*
   (`_j2_ember.tex`), using the same method: review each subsection, split and polish its appendix material, then a
   final pass over both together. After that comes **§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words; the numbers
   are pilot values, so do not sync them; the user has not read §5 end to end).

§2 comes in a later session. Its closing sentence and contribution 4 of `docs/paper-mock.md` wait for the user's
discussion of the motivation (the prepared note is the *C.6 note* in `docs/status.md`'s session-80 entry). Not in this
round: the abstract, introduction, discussion, ethics, open science.

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`) is the closest work; the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare against their method experimentally is the
  user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB) may be reconsidered later. Do nothing about it now.

## At the end

Add a short session-log entry to `docs/status.md` and commit the docs. Archive this prompt under `docs/archive/`, then
write the next resume prompt into this file.
