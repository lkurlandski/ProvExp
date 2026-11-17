# Resume prompt: the detailed humanistic review of the manuscript, one piece at a time (Sonnet)

Written 2026-11-17 (end of session 82). The scale-up runs on tigris; nothing here depends on its numbers. Read
`CLAUDE.md` and this prompt. Open `docs/status.md`'s *Current state* only if something below needs it.

## Budget (the user, session 82)

The user was at 92% of the week's usage on 2026-11-17, so **work cheaply**: Sonnet at the default effort; read only the
subsection under review (plus the definitions it uses, by search, not whole files); no subagents; do not open
`docs/status.md`, `PLAN.md`, or the evidence notes unless a finding needs one fact. If the user says to stop, finish
the piece in hand, commit what they approved, update `docs/status.md`, and stop. If budget is left after a reset, §3 is
the pass worth an Opus run (decided by the user).

## How to work

- **The skill:** run `humanistic-paper-review` (it diagnoses with exact quotes and ranked findings; it does not
  rewrite) on **one subsection per pass**, as in session 41b. Report that pass's findings to the user, ranked, with
  the quote for each. Do not apply anything yet.
- **One fix at a time.** The user picks a finding; apply that one fix to the `.tex` (wrap lines at 120; use the
  `paper-prose` skill when writing), run `make` and `make check` in `manuscript/`, show the old and the new text and
  what you checked in the source, and **wait for the verdict** before the next. Commit a piece only after approval.
  The user rejects some proposed changes (R4, part of R5 and others were rejected because the extractor is defined
  algebraically in §3.1): do not defend a rejected change; revert it (`git checkout -- <file>`) and move on.
  Findings from simulated or skill reviews are not instructions (memory: distrust simulated reviews): before calling
  something a flaw, quote the claim and check it against the text.
- **Length is a separate, later pass.** Do not shorten anything now. When a finding is "this passage does not earn
  its place", do not apply it; add one line to `docs/review-cuts.md` (create it: the place, the first words of the
  passage, why it looks cuttable) and move on. That list is the input to the length pass after the abstract,
  introduction and discussion are written.
- **Numbers and cross-references** come from the compiled PDF (`manuscript/main.aux`), with the title alongside.
- **Related work text** stays short and is about the cited work and the difference from ours. Cite from `papers/`
  only (quote the PDF); never write a claim about a paper from memory; a paper that is not there: say so and leave
  `% TODO cite`. Use the S&P version of Pierazzi et al., not the TOPS one.

## Order (the user's)

1. **§6 Related Work** (`_g_related_work.tex`, ~1,900 words), a pass per paragraph group: *Problem-space attacks* and
   *Constraints over features* (the Kantchelian sentence is new); *Robust and monotone detectors* (the Lucas 2023
   sentence was rewritten, and the Lucas 2024 and Tsingenopoulos sentences are new); *Certified defenses* (new in
   session 80); *Incremental computation and provenance*.
2. **§3 The framework** (`_d_framework.tex`, ~4,700 words; proofs in `_j_proofs.tex`): 3.1 *Sum-then-Readout
   Extractors*, 3.2 *Edits and Their Side Effects*, 3.3 *Sound Directions*. 3.3 holds Lemma 1 (*Closure*), the
   readout rule and Table 1, which the user has **not read closely yet** (added in session 74, approved after a brief
   look); the user reads §3.3 only after its pass. One thing noticed, not yet raised: after Lemma 1 the text says "The
   same holds for lower bounds on features that the table does not allow to fall", then gives an example (a count of
   unwanted items bounded above by 0) that is the lemma's own case, not a lower bound.
3. **§4 Instantiating the Framework** (`_e_instances.tex`, ~1,900 words): 4.1, 4.2, 4.3 (*Operations*, *Signature*;
   the attacker paragraph changed in session 80), 4.4 *Population*. Reviewed twice before (sessions 38, 40).
4. **§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words): 5.1 *Setup* (the query-budget sentence changed in session
   80), 5.2, 5.3, 5.4. Reviewed in session 41b and 42; the user has not read §5 end to end. Numbers are pilot values;
   do not sync them.
5. **§2 Background and Motivation** (`_c_background.tex`, ~1,000 words), last, because its closing sentence and
   contribution 4 of `docs/paper-mock.md` wait for the user's discussion of the motivation. **Do not edit those two.**
   The prepared note is in `docs/status.md`'s session-80 entry (*C.6 note*). The sentence session 80 added to §2
   (Pierazzi et al.'s closed-form reason) is in this pass.

Not in this round: the abstract, introduction, discussion, ethics, open science (not written), and the appendices
(read an appendix only where a finding in §3 or §5 points into it).

## Open, ask the user first

- **Tsingenopoulos et al. (arXiv 2402.19027, `papers/tsingenopoulos2024train.pdf`), the closest work.** Read closely in
  session 82. In §6 one sentence (*Robust and monotone detectors*) says they harden a detector of dynamic-analysis
  reports with examples that an RL agent builds from a set of problem-space transformations the authors define, and
  claim a probabilistic guarantee. **Proposed, not applied (ask):** say instead that they define robustness as the
  probability the strongest such adversary fails, estimated by training a new agent on held-out reports. What the
  reading found: (a) Theorem 4.1 (p-robustness) is the definition (the optimal adversary's expected success is 1-p);
  no bound is computed, and the level is estimated by retraining an RL agent on held-out reports ("given sufficient
  horizon to converge"), so it is only as strong as that attack; (b) the capability set C is hand-written (Table 1:
  add and replace allowed, removal not, replacing APIs not) and dependencies among the 13 report categories are
  propagated by a hand-written sweep (Appendix A: rename an entry everywhere), checked by hand on "a handful" of
  traces: the side-effect computation our framework derives from the extractor; (c) the edits are applied to the
  JSON report, not to binaries (7 years against 45 hours; the binary level is a proof of concept on a modified
  `capemon`), so do not describe their examples as binaries; (d) they state our premise, "attackers must generate
  realistic adversarial binaries, defenders... merely have to generate feature spaces that correspond to realistic
  transformations", by hand and for one model; (e) their model reads the whole report: no sum-then-readout extractor;
  (f) results: attack success 73.8% to 0.0% on the binary task at budgets of 1K and 2K entry modifications, 26,200
  samples of three families, against gradient-based adversarial training near 72%. A reviewer may ask why a defender
  cannot write the realistic edits by hand; the answer is what we compute instead of write. Their method (a
  hand-written edit model and an RL attacker, then retraining) is the realistic competitor for the defender's task;
  whether to compare against it is a larger decision for the user, not for this session.
- **Gibert et al.'s certified detectors** (AISec 2023, IEEE Access 2024, as listed by Giri et al.) are not in
  `papers/`; ask the user for them if the user wants them in §6's certified-defenses paragraph (`% TODO cite`).
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB, ours, not Gimenez et al.'s) may be reconsidered later: do nothing now.

## At the end

Update `docs/status.md` (a short session-log entry: which passes ran, which findings were applied or rejected, the
commits) and commit the docs. Write the next resume prompt into this file.
