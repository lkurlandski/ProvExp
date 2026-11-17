# Resume prompt (writing track): cut §6 Related Work by 30-40%, paragraph by paragraph, following the approved plan; then the humanistic review of the other sections

Written 2026-11-17 (end of session 83). The scale-up runs on tigris; nothing here depends on its numbers. Read
`CLAUDE.md`, this prompt, and **`docs/related-work-plan.md`** (the assessment and the plan the user approved, the
user's guidance on it, the source checks already done, and what went wrong in session 83). Open
`manuscript/_g_related_work.tex`, `manuscript/_c_background.tex` (§2, which the reader is assumed to have read
carefully) and the cited PDFs in `papers/` as the work needs them. Run on Opus. No subagents unless the user asks.

## First order of business: apply the §6 plan, one paragraph at a time

The user approved the plan in session 83. Session 83 then failed to apply it: a 160-word paragraph that read well was
gutted (rejected outright), and the next paragraph lost 11 words net against a planned 140 (rejected as pointless).
All of session 83's manuscript edits were discarded; §6 is as committed in `d9fc35d` (1,843 words). The target is
1,100-1,300 words.

**What the user wants from each paragraph:** the cut the plan names, delivered in full, in prose that reads as well
as the original. Rewrite the paragraph at its target length, so the argument still flows; do not delete sentences one
by one, and do not nibble. Contrast with our work only where necessary, never as a closing restatement in every
paragraph; no repetition of §2 (assume the reader read it); little detail about individual papers (their
contribution and how the works relate, not their numbers or architectures), except the critical works we build on.

**Order and targets** (per-paragraph detail in the plan, section (c)):
1. *Problem-space attacks*: **unchanged** (user: it "read smoothly, and it emphasized the correct ideas at an
   appropriate level"). Ask once whether to drop the inaccurate Šrndić and Laskov clause (plan, source checks).
2. *Constraints over features*: 424 to about 300, with Labaca-Castro et al. added and Sheatsley et al. corrected.
3. *Robust and monotone detectors*: split into *Adversarial training* (with Tsingenopoulos et al.: two sentences,
   wording in the plan, (e)1) and *Monotone and verified detectors* (with Chen et al. 2021), together about 430
   instead of 765.
4. *Certified defenses*: about 165, Calzavara et al. moved in, Gibert et al. 2023 beside DRSM.
5. *Incremental computation and provenance*: about 110.
Keep a running total after each paragraph and report it against the target; if a paragraph falls short, say so and
say where the words will come from instead.

**Per paragraph:** read the cited PDFs for every claim you write (quote-check; new bib entries from a real record);
write the paragraph; `make` and `make check` in `manuscript/`; read the rendered text (pdftotext); show the user old
and new text with the word count before and after; wait for the verdict; commit only after approval. A rejected
change is reverted. When the user rejects a draft, try again better (ask what failed if it is not clear); do not give
up on the paragraph.

**The paper-prose skill** (`.claude/skills/paper-prose/`): the user asked at the end of session 83 whether it is
holding the writing back. Session 84 starts from the user's answer on that (see `docs/status.md`, session 83).

## Then: the humanistic review of the other sections, one subsection per pass (as in session 82)

The method is unchanged: run `humanistic-paper-review` on **one subsection per pass**, report ranked findings with
exact quotes, apply nothing until the user picks; then **one fix at a time** (apply, `make`, `make check`, show old and
new text and what was checked in the source, wait for the verdict). The user rejects some proposed changes (R4, part of
R5 and others were rejected because the extractor is defined algebraically in §3.1): do not defend a rejected change;
revert it. "This passage does not earn its place" is not applied in these sections: add one line to
`docs/review-cuts.md` (create it: place, first words, why it looks cuttable); that list is the input to the length
pass after the abstract, introduction and discussion are written. Numbers and cross-references come from the compiled
PDF (`manuscript/main.aux`), with the title alongside. Which model runs these passes is the user's choice (Sonnet did
§6's first pass; the user judged it weak on structure, so §3 in particular is worth Opus).

1. **§3 The framework** (`_d_framework.tex`, ~4,700 words; proofs in `_j_proofs.tex`): 3.1 *Sum-then-Readout
   Extractors*, 3.2 *Edits and Their Side Effects*, 3.3 *Sound Directions*. 3.3 holds Lemma 1 (*Closure*), the
   readout rule and Table 1, which the user has **not read closely yet** (added in session 74, approved after a brief
   look); the user reads §3.3 only after its pass. One thing noticed, not yet raised: after Lemma 1 the text says "The
   same holds for lower bounds on features that the table does not allow to fall", then gives an example (a count of
   unwanted items bounded above by 0) that is the lemma's own case, not a lower bound.
2. **§4 Instantiating the Framework** (`_e_instances.tex`, ~1,900 words): 4.1, 4.2, 4.3 (*Operations*, *Signature*;
   the attacker paragraph changed in session 80), 4.4 *Population*. Reviewed twice before (sessions 38, 40).
3. **§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words): 5.1 *Setup* (the query-budget sentence changed in session
   80), 5.2, 5.3, 5.4. Reviewed in session 41b and 42; the user has not read §5 end to end. Numbers are pilot values;
   do not sync them.
4. **§2 Background and Motivation** (`_c_background.tex`, ~1,000 words), last, because its closing sentence and
   contribution 4 of `docs/paper-mock.md` wait for the user's discussion of the motivation. **Do not edit those two.**
   The prepared note is in `docs/status.md`'s session-80 entry (*C.6 note*). The sentence session 80 added to §2
   (Pierazzi et al.'s closed-form reason) is in this pass.

Not in this round: the abstract, introduction, discussion, ethics, open science (not written), and the appendices
(read an appendix only where a finding in §3 or §5 points into it).

## Rules for related-work text

Short, and about the cited work and the difference from ours. Cite from `papers/` only (quote the PDF); never write a
claim about a paper from memory; a paper that is not there: say so and leave `% TODO cite`. Use the S&P version of
Pierazzi et al., not the TOPS one.

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`), the closest work: the session-82 reading is at the end of
  `docs/related-work-plan.md`. Whether to compare against their method experimentally is a
  larger decision for the user, not for this session.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB, ours, not Gimenez et al.'s) may be reconsidered later: do nothing now.

## At the end

Update `docs/status.md` (a short session-log entry: which passes ran, which findings were applied or rejected, the
commits) and commit the docs. Write the next resume prompt into this file.
