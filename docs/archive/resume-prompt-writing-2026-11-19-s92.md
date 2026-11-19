# Resume prompt (writing track): the humanistic review and polish of §3, §4 and §5

Written 2026-11-19 (end of session 92). The scale-up runs on tigris; nothing here depends on its numbers. Read
`CLAUDE.md` and this prompt; open the section under review (`manuscript/_d_framework.tex`, `_e_instances.tex`,
`_f_evaluation.tex`), `manuscript/_c_background.tex` (§2, which the reader is assumed to have read carefully) and
the appendices only as a finding needs them. Run on Opus. No subagents unless the user asks.

## Where the writing stands

- **§6 Related Work is done for now** (session 84; plan and source checks in
  `docs/archive/related-work-plan-2026-11-17-s84.md`). Do not reopen it unless the user asks.
- **§3.1 *Sum-then-Readout Extractors* is reviewed and polished** (session 92, commit 0185d58; the findings and
  verdicts are in `docs/status.md`'s session-92 entry). The user rejected one finding: the sentence after Definition 1
  on why the item map drops positions stays as it is; do not raise it again.
- **Deferred to a holistic review of all of §3, after §3.3's pass:** recurring sentence patterns and the term ledger.
  Known items so far: "element" means an input's unit, a neutral element, an element of $\mathcal{S}$, and a loop kind
  in Algorithm 1; "extractor" is used in Definition 1 before Definition 5 defines it. Collect further items from the
  §3.2 and §3.3 passes into that review rather than reporting them as findings.
- **The paper-prose skill is not used** (the user, session 92: "I don't think it's really helpful after all"). Draft
  fixes without it and do not ask.
- What the user said about earlier drafts is in `docs/writing-spec.md` (top entries): read it as evidence of taste,
  not as rules.

## The task: one subsection per pass, in this order

1. **§3.2 *Edits and Their Side Effects*** (`_d_framework.tex`, from `\subsection{Edits and Their Side Effects}`).
   Session 92 added one sentence there (after "the same holds for a minimum": a sum in any other monoid without
   subtraction is recomputed the same way); it belongs to the pass.
2. **§3.3 *Sound Directions***: Lemma 1 (*Closure*), the readout rule and Table 1, which the user has **not read
   closely yet**; the user reads §3.3 only after its pass. One thing noticed, not yet raised: after Lemma 1 the text
   says "The same holds for lower bounds on features that the table does not allow to fall", then gives an example (a
   count of unwanted items bounded above by 0) that is the lemma's own case, not a lower bound. Table 1's caption and
   the readout paragraph refer to the readout forms listed in §3.1, whose paragraph was rewritten in session 92 (the
   distinct count is now said to read a whole family of sums and not to be algebraic); check they still agree.
3. Then the holistic review of §3 (patterns and terms, above).
4. **§4 Instantiating the Framework** (`_e_instances.tex`, ~1,900 words): 4.1-4.4. Reviewed twice before (sessions
   38, 40).
5. **§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words): 5.1-5.4. Numbers are pilot values; do not sync them. The user
   has not read §5 end to end.

§2 comes after these, in a later session: its closing sentence and contribution 4 of `docs/paper-mock.md` wait for the
user's discussion of the motivation (the prepared note is in `docs/status.md`'s session-80 entry, *C.6 note*). Not in
this round: the abstract, introduction, discussion, ethics, open science, and the appendices (read an appendix only
where a finding points into it).

## The method (as in session 92)

- Run `humanistic-paper-review` on **one subsection per pass**; report ranked findings with exact quotes; apply
  nothing until the user gives a verdict per finding.
- In session 92 the user approved the small findings together and asked for them to be applied in one go rather than
  one at a time. If the approved fixes are small, do that: apply them all, `make` and `make check` in `manuscript/`,
  read the rendered text (pdftotext), commit, and report what changed. For a large rewrite, or if the user asks, go
  back to one fix at a time with old and new text and a verdict before committing.
- When a fix rewrites prose, rewrite the passage so it flows at its length; sentences should lead into each other.
- "This passage does not earn its place" is not applied in these sections: add one line to `docs/review-cuts.md`
  (create it when the first one comes up: place, first words, why it looks cuttable).
- Numbers and cross-references come from the compiled PDF (`manuscript/main.aux`), with the title alongside.

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`), the closest work: the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare against their method experimentally is the
  user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB) may be reconsidered later: do nothing now.

## At the end

Update `docs/status.md` (a short session-log entry) and commit the docs. Write the next resume prompt into this file
(archive this one first under `docs/archive/`).
