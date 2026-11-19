# Resume prompt (writing track): cut §3 by ~20%, then §4 with Appendix D

Written 2026-11-19 (end of session 96). Nothing here depends on the scale-up on tigris. Read `CLAUDE.md` and this
prompt. Then read all of §3 (`manuscript/_d_framework.tex`, ~4,210 words) and its appendices: Appendix A *Symbol
Table* (`_i_symbols.tex`), Appendix B *Types, Monoids, and Folds* (`_i2_types.tex`) and Appendix C *Proofs for the
Framework* (`_j_proofs.tex`, ~1,335 words). Read `docs/review-cuts.md`. Open `manuscript/_c_background.tex` (§2) and
`_g_related_work.tex` (§6) only where a cut touches them. Run on Opus. Use no subagents unless the user asks.

## Where the writing stands

- **§6 Related Work is done for now** (session 84). Change it only where a §3 cut moves credit there (see below), and
  ask first.
- **§3 has four subsections**, each reviewed with its appendix material (sessions 92-95), then reviewed whole in
  session 96:
  - §3.1 *Sum-then-Readout Extractors*. Since session 96 it opens by defining "extractor" (the code that computes a
    feature mapping), and Definition 3 defines an item's *contribution* and the sums it *touches* (non-neutral
    contribution). The user rejected one finding in session 92: the sentence after Definition 1 on why the item map
    drops positions stays as it is; do not raise it again.
  - §3.2 *Edits and Their Side Effects*.
  - §3.3 *Sound Directions*: Definition 7 (threat model, population, directions, sound table; "closed" is no longer
    here), Definition 8 (*item changes* and signatures: "item change" is the operation on one item, plain "change" is
    how much a value moves), Definition 9 (directions of sums), Table 1, Definition 10 (*Readout rule and derived
    table*, equation (11)), Theorem 1 (now only: the derived table is sound for one edit), abstract interpretation.
  - §3.4 *Sequences and Robust Detectors* (title chosen "for now", session 96): closure defined in the lead,
    Proposition 2 (*Sequences of edits*, for any sound table on a closed population), closure checked directly (as §4.4
    does) or proven by Lemma 1, monotone detectors, Corollary 1, closing paragraph.
  - Appendix C has three subsections, one per body subsection: C.1 *Edits and Their Side Effects*, C.2 *Sound
    Directions*, C.3 *Sequences and Robust Detectors*.
- **Appendix B stays** as a stand-alone crash course on §3's background; light repetition of its definitions in §3 is
  fine (user, session 96). Do not propose trimming it.
- **The split that worked** (sessions 93 and 95): the body keeps the statements, the conditions a reviewer would test,
  and the reason each result holds in a few plain sentences, with a pointer to Appendix C. The appendix keeps the
  derivations, with each step stated and definitions named instead of cited by equation number. No examples in the
  appendix by default.
- **The paper-prose skill is not used** (user, session 92). Draft fixes without it and do not ask about it.
- What the user said about earlier drafts is in `docs/writing-spec.md` (top entries; session 96's is the newest). Read
  it as evidence of taste, not as rules.

## How to work

- The user approves small changes that improve clarity and consistency directly; run larger changes to the language,
  structure, or claims by them first, explained plainly with the options and a recommendation (session 96).
- Use ranked findings or plan items with exact quotes, and get a verdict on each before applying anything. Apply the
  approved small fixes in one go, then run `make` and `make check` in `manuscript/`, read the rendered text
  (pdftotext), commit, and report what changed with word counts (`texcount -brief`) before and after.
- For a large rewrite, or if the user asks, go one fix at a time with the old and new text.
- When a fix rewrites prose, rewrite the passage so that it flows at its new length.
- Take numbers and cross-references from the compiled PDF (`manuscript/main.aux`), with the title alongside.

## The task, in order

1. **Cut §3 by about 20%** (user, session 95): from ~4,210 words to ~3,450, about the mock's budget of 3,500. First
   present a plan per subsection: where the words go and what each cut costs the reader. Moving material to the
   appendix counts, but only where the split rule above allows it. Get approval, then apply. For §6 (session 84), a
   30% cut planned paragraph by paragraph worked, with every change approved. Fold in the logged candidates in
   `docs/review-cuts.md`:
   - Appendix C *Patterns under extension* (nothing refers to it) and *Computing part (ii)* (all of it is in the
     body). These are appendix words and do not count toward §3's budget, but decide them in the same pass.
   - §3.2, the paragraph "The proposition gives the side effects of an edit exactly": two repeats (~50 words). When
     cutting it, its "a sum to which an item of the delta contributes" becomes "a sum that an item of the delta
     touches" (the session-96 term fix left this paragraph alone).
   - The three analogy passages: Gray et al.'s distributive/algebraic classes (§3.1 readout paragraph, ~120 words),
     incremental view maintenance (end of §3.2), abstract interpretation (end of §3.3). The user: cutting all three
     is an option, since §6 may be adjusted (its *Incremental computation* paragraph cites §3.2 and §3.3 for them),
     but "shortening all three might be a better approach". Present both with their costs.
   - Session 96's patterns: trim "not X but Y" and "thus/therefore" sentences only where they do not help, cautiously
     (several remaining ones sit in the paragraphs above).
2. Then **§4 Instantiating the Framework** (`_e_instances.tex`, ~1,830 words) with Appendix D *The EMBER Instance*
   (`_j2_ember.tex`), using the same method: review each subsection, split and polish its appendix material, then a
   final pass over both together. §4.4 *Population* now carries the closure argument that §3.4 points to ("Closure is
   checked rather than proven"); keep the two consistent. After that comes **§5 Evaluation** (`_f_evaluation.tex`,
   ~4,100 words; the numbers are pilot values, so do not sync them; the user has not read §5 end to end).

§2 comes in a later session. Its closing sentence and contribution 4 of `docs/paper-mock.md` wait for the user's
discussion of the motivation (the prepared note is the *C.6 note* in `docs/status.md`'s session-80 entry). Not in this
round: the abstract, introduction, discussion, ethics, open science.

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`) is the closest work; the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare against their method experimentally is the
  user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB) may be reconsidered later. Do nothing about it now.
- §3.4's title, *Sequences and Robust Detectors*, was taken "for now".

## At the end

Add a short session-log entry to `docs/status.md` and commit the docs. Archive this prompt under `docs/archive/`, then
write the next resume prompt into this file.
