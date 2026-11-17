# Resume prompt (writing track): first a holistic assessment of §6 Related Work and a plan to cut it by 30-40% (Opus), then the humanistic review of the other sections

Written 2026-11-17 (end of session 82, after the first pass on §6). The scale-up runs on tigris; nothing here depends
on its numbers. Read `CLAUDE.md` and this prompt. Open `docs/status.md`'s *Current state*, `docs/paper-mock.md` (the
§6 row and the paper's argument) and `docs/evidence/r6-prior-work.md` only as the task below needs them.

**Run this session on Opus** (the user, session 82: Sonnet's reading of the section was not good enough for a
structural judgement). No subagents unless the user asks.

## First order of business: assess §6 as a whole, then plan its cut

The user's words (session 82): the Related Work section "is past the point of simply being a little too long. It's now
so long that it isn't even useful." The earlier permission to run long while drafting (CLAUDE.md, early drafting stage)
no longer holds **for §6**. The user wants, in this order: (1) confidence that §6 covers the right ideas in the right
way, judged on structure, organization and content; (2) a plan to cut its length by **30% to 40%**. Other sections stay
under the old rule: their cuts go to `docs/review-cuts.md`, for a later length pass.

**State of §6** (`manuscript/_g_related_work.tex`, `texcount` 1,843 words; the mock's budget is 1,000, "now ~1,470" in
`docs/paper-mock.md`, so 30-40% off the present text is about 1,100-1,300 words). Words per paragraph: *Problem-space
attacks* 160; *Constraints over features* 424; *Robust and monotone detectors* 765; *Certified defenses* 180;
*Incremental computation and provenance* 294. Sentence-level problems (a quote-checked humanistic pass on the first two
paragraphs) were already found and fixed; do not redo that. The cut is about what the section is for.

**The five edits of pass 1 are committed** (`d9fc35d`, approved by the user): (1) Kantchelian et al.'s sentence moved up
beside the other methods that take constraints as input, "All three take the constraints as input"; (2) "In each case,
nothing checks the constraints against the extractor" replaced by "None of these derives the constraints from the
extractor itself"; (3) a paragraph break at "All three take the constraints as input"; (4) *Problem-space attacks* now
names Pierazzi et al.'s condition (feature mappings neither differentiable nor invertible, quote-checked) and ends on
what our work computes, not "replaces this trial and error"; (5) "realizable" (§2's own term) in place of "realistic"
where the paper's notion is meant, and "problem-space examples" for what Dyrmishi et al. and Lucas et al. mean. The cut
may rewrite them; keep what they fixed (the condition, the term, the narrower claim).

**How to assess** (diagnose; propose; the user decides):

- Start from what the paper needs §6 to do for a reader of a security venue: place the contribution against the closest
  work, once. Read §2's closing paragraphs and the mock's row, because §2 already states the gap and the two sections
  may say the same thing twice. Search `_d_framework.tex` for where abstract interpretation is cited (the comment at
  the top of §6 says it is cited in both).
- For each paragraph, write down its job in one sentence and the one claim about *our* difference it carries. Ask of
  each cited work whether the section loses anything if it goes, and whether a group of works can share one sentence.
  Paragraphs 2 and 3 are the long ones; *Robust and monotone detectors* holds three separate things (adversarial
  training, monotone and robust-by-construction detectors, and Chen et al.'s verified classifiers) and may read better
  as two paragraphs of half the length. Check the order of the paragraphs, and whether *Certified defenses* and
  *Incremental computation and provenance* belong in §6, in an appendix, in §3 where the idea is used, or nowhere.
- Where does the closest work, Tsingenopoulos et al. (below), belong: one sentence inside *Robust and monotone
  detectors*, or a place of its own at the start of that paragraph?
- Is anything missing that a reviewer would expect (a closest work not cited; a line of work that attacks our claim)?
  Be harsh about our own novelty (CLAUDE.md). Papers cited from `papers/` only.
- The humanistic-review skill's section-level tests (P1 to P5: contribution restatement, topic-sentence skim) fit
  here; the sentence-level ones do not.

**Deliverable of the assessment** (to the user, in the terminal, before any edit): (a) the section's argument in
a few sentences and whether the present order serves it; (b) per paragraph: keep, merge, split, move or drop, with the
reason; (c) a cut plan that adds up to 30-40%: each cut named by place and first words, with the words it saves and
what the reader loses (nothing, or one named thing); (d) anything missing; (e) the decisions that are the user's (the
Tsingenopoulos wording and whether to compare against their method; Gibert et al.). Then **wait**. After the user
approves a plan, apply it **one paragraph at a time** (show old and new, `make` and `make check` in `manuscript/`, wait
for the verdict, lines wrapped at 120, `paper-prose` skill for any new sentence; commit a paragraph only after
approval). A rejected change is reverted, not defended. Findings from simulated or skill reviews are not instructions
(memory: distrust simulated reviews): quote the claim before calling it a flaw.

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
- **Not in `papers/`, so their claims in §6 cannot be quote-checked:** Šrndić and Laskov's PDFrate evasion
  (`srndic2014practical`, "worked this way"), Chernikova and Oprea's FENCE (`chernikova2022fence`, "updating dependent
  features after each step"), Sheatsley et al. (`sheatsley2021robustness`, "learn constraints from data around a few
  features chosen by hand"). Ask the user for the PDFs, or mark `% TODO cite`. Not yet quote-checked in the pass on
  §6's first two paragraphs: Simonetto et al., Dyrmishi et al., Bostani et al. (they are in `papers/`; Pierazzi et al.
  and Kantchelian et al. were checked).
- **Gibert et al.'s certified detectors** (AISec 2023, IEEE Access 2024, as listed by Giri et al.) are not in
  `papers/`; ask the user for them if the user wants them in §6's certified-defenses paragraph (`% TODO cite`).
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB, ours, not Gimenez et al.'s) may be reconsidered later: do nothing now.

## At the end

Update `docs/status.md` (a short session-log entry: which passes ran, which findings were applied or rejected, the
commits) and commit the docs. Write the next resume prompt into this file.
