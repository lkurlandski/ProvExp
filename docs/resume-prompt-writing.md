# Resume prompt (writing track): the humanistic review and polish of §3, §4 and §5

Written 2026-11-17 (end of session 84). The scale-up runs on tigris; nothing here depends on its numbers. Read
`CLAUDE.md` and this prompt; open the section under review (`manuscript/_d_framework.tex`, `_e_instances.tex`,
`_f_evaluation.tex`), `manuscript/_c_background.tex` (§2, which the reader is assumed to have read carefully) and
the appendices only as a finding needs them. Run on Opus. No subagents unless the user asks.

## Where the writing stands

- **§6 Related Work is done for now** (session 84): cut from 1,843 to 1,284 words, paragraph by paragraph, every change
  approved; the user: "a reasonably appropriate length". The plan, the user's guidance on related work and the source
  checks are in `docs/archive/related-work-plan-2026-11-17-s84.md`. Do not reopen §6 unless the user asks.
- **The paper-prose skill was not used in session 84** (the user's choice, after asking at the end of session 83
  whether it holds the writing back). Draft without it unless the user says otherwise; ask once at the start if a
  fix needs new prose.
- What the user said about session 84's drafts is in `docs/writing-spec.md` (top entry): a first draft that read
  "choppy and disconnected" was approved once its sentences led into each other; "whatever the edits mean" was
  "informal and unclear". Read it as evidence of taste, not as rules.

## The task: one subsection per pass, in this order

1. **§3 The framework** (`_d_framework.tex`, ~4,700 words; proofs in `_j_proofs.tex`): 3.1 *Sum-then-Readout
   Extractors*, 3.2 *Edits and Their Side Effects*, 3.3 *Sound Directions*. 3.3 holds Lemma 1 (*Closure*), the readout
   rule and Table 1, which the user has **not read closely yet** (added in session 74, approved after a brief look); the
   user reads §3.3 only after its pass. One thing noticed, not yet raised: after Lemma 1 the text says "The same holds
   for lower bounds on features that the table does not allow to fall", then gives an example (a count of unwanted
   items bounded above by 0) that is the lemma's own case, not a lower bound.
2. **§4 Instantiating the Framework** (`_e_instances.tex`, ~1,900 words): 4.1, 4.2, 4.3 (*Operations*, *Signature*;
   the attacker paragraph changed in session 80), 4.4 *Population*. Reviewed twice before (sessions 38, 40).
3. **§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words): 5.1 *Setup* (the query-budget sentence changed in session
   80), 5.2, 5.3, 5.4. Reviewed in sessions 41b and 42; the user has not read §5 end to end. Numbers are pilot values;
   do not sync them. §5.3 has a run-in paragraph *Adversarial training*; §6's is now *Hardening by retraining*, so
   they no longer clash.

§2 comes after these three, in a later session: its closing sentence and contribution 4 of `docs/paper-mock.md` wait
for the user's discussion of the motivation (the prepared note is in `docs/status.md`'s session-80 entry, *C.6
note*). Not in this round: the abstract, introduction, discussion, ethics, open science (not written), and the
appendices (read an appendix only where a finding in §3-§5 points into it).

## The method (as in session 82)

- Run `humanistic-paper-review` on **one subsection per pass**; report ranked findings with exact quotes; apply
  nothing until the user picks.
- Then **one fix at a time**: apply, `make` and `make check` in `manuscript/`, read the rendered text (pdftotext),
  show old and new text and what was checked in the source, wait for the verdict, commit only after approval. A
  rejected change is reverted; do not defend it. The user rejects some proposed changes (R4, part of R5 and others
  were rejected because the extractor is defined algebraically in §3.1).
- When a fix rewrites prose, rewrite the passage so it flows at its length, rather than deleting or patching sentence
  by sentence; sentences should lead into each other.
- "This passage does not earn its place" is not applied in these sections: add one line to `docs/review-cuts.md`
  (create it: place, first words, why it looks cuttable). That list is the input to the length pass after the
  abstract, introduction and discussion are written.
- Numbers and cross-references come from the compiled PDF (`manuscript/main.aux`), with the title alongside.
- Which model runs a pass is the user's choice (Sonnet did §6's first pass in session 82; the user judged it weak on
  structure, so §3 in particular is worth Opus).

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`), the closest work: the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare against their method experimentally is a
  larger decision for the user, not for this session.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB, ours, not Gimenez et al.'s) may be reconsidered later: do nothing now.

## At the end

Update `docs/status.md` (a short session-log entry: which passes ran, which findings were applied or rejected, the
commits) and commit the docs. Write the next resume prompt into this file (archive this one first under
`docs/archive/`).
