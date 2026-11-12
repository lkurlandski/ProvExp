# Resume: a holistic review of §5 *Evaluation*, weighing how much its contributions matter; then the plan

Written at the end of session 41b (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024
extractor is the instance; the framework is format-free. The paper is written straight into `manuscript/*.tex` (ACM
`sigconf`, CCS format; `make` and `make check` in `manuscript/`). §5 *Evaluation* is `manuscript/_f_evaluation.tex`:
5.1 *Setup*, 5.2 *What Hand Analysis Misses*, 5.3 *What Observed Attacks Miss*, 5.4 *What Robustness Costs*; Appendix
D *The EMBER Instance* is `_j2_ember.tex`. Check `manuscript/main.aux` before naming a section, table or definition
number, and give the title alongside (`docs/README.md` has the numbering).

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 10: §5 is three findings about adversarial
examples, not a validation section and not a defense paper; agreed, do not reopen; and "Next steps"). The `paper-prose`
skill governs any prose you write; the user's raw reactions are at the end of `docs/writing-spec.md` (sessions 35-41
are the ones on §4-5).

## Where things stand

§2-4 are in good shape (§4 reviewed twice with the `humanistic-paper-review` skill). §5 is fully drafted, with no blue
(synthetic) values. In session 41b it was reviewed with the same skill one subsection per pass (25 findings in all);
the user approved every finding they did not drop, and all are applied (commits ce4ba21, f8baea5, 1053bf7, e8b0335).
What changed: each subsection's lead now ends by answering its question (a stopgap; see step 3 below); 5.1 names "the
side effects and directions we compute" and introduces the unconstrained detector; 5.2 counts eight errors of our
hand table, with the certificate table apart, and gives Gimenez et al.'s expert set and Severi et al.'s hashed
features their own paragraphs; 5.3 names ERDALT and PV in its lead and says the derived table marks 142 features as
ones an edit *may* lower (20 shown by our edits); 5.4's lead states the cost (3.9 points at 1% FPR and 9.7 at 0.1%, on
the sums) and its 0.1% breakdown keeps only what clears retraining noise; Table 2's attack names ("GAMMA imports",
"header fields") and "population" throughout, no "pilot". The user has approved changes but not read §5 end to end.

## The task, in order

1. **A holistic review of all of §5** (user, 2026-11-12), with `anthropic-skills:humanistic-paper-review`, on the
   section as a whole rather than per subsection, and **with more weight on how important a human reader will consider
   the contributions**: does each of the three findings matter to a security reader, are its stakes visible (what was
   believed before, what breaks, who should change what), does the section as a whole make R care, and does it deliver
   what §2 and the contributions promise. Pass 1's section-level checks (P1, P2, P5, P6) and T3 "so what" carry the
   most weight; sentence-level patterns only when clearly ugly; say plainly what is in good shape. Read the source and
   the rendered PDF (`pdftotext manuscript/main.pdf -`). **Do not edit before the user responds.** Practitioners'
   likely objections to keep in view without fixing now: the cost at 0.1% FPR (about ten points), the structural-only
   threat model (no packing, no code-level edits), pilot scale (10% subsamples, one seed, 50 malware).
2. When the user responds: answer their questions first, plainly; apply what they approve, in small passes (approved
   ones first); `make`, `make check`, read the rendered text; show old and new text per finding; log their reactions
   raw at the end of `docs/writing-spec.md` (never as rules); commit.
3. Then the rest of the plan (PLAN.md, next step 2, each to be considered with the user, one at a time):
   (0) **§5's questions and answers given visual emphasis**: the user wants "serious structural modifications ... with
   regard to how the research questions are presented, i.e., 'asked', and how the findings are presented, i.e.,
   'answered' ... more visual emphasize to the questions and answers." Nothing is designed yet: first propose two or
   three concrete looks as rendered snippets (check accepted CCS-style papers in `papers/` for precedent) and let the
   user choose before drafting. (a) Remake the tables (Tables 3 and 4 above all; the user dislikes them), before
   (b) shortening §4 and §5 together (§4 ~1,500 words against ~1,000; §4.3 first). (c) Align §2's closing sentence
   and contribution 4 with §5's three findings.
4. After that (PLAN.md): the 4 MB-truncation brainstorm (decision 8 (iv)); then decide with the user whether the paper
   is ready for the next full simulated review (update `docs/reviews/review-prompt.md` first); the scale-up (seeds 0-2,
   full splits, more malware) once the write-up is finished. The ERDALT check is done (session 41; PLAN.md step 3).

## How the user wants reviews handled

- Keep the review's finding numbers throughout the conversation; never renumber them in a reply.
- Apply in small passes: first the findings the user understands and approves; explain the others plainly, one at a
  time, when asked. The user approves or rejects each proposed change; they do not necessarily read the section end
  to end during the review.
- Trimming is welcome, but moving very small snippets to the appendix does more harm than good.
- A finding that touches what a claim rests on (proven, checked, or measured) needs care: verify in the code and the
  run outputs (run headers in `run/`, `artifacts/`, the `%` comments beside each paragraph) before wording it.
- A lead may mention a concept in passing without defining it; it should give a rough idea of what the section does
  and why (user, session 41b, on the adaptive attack). PE constructs (e.g., the Rich header) need no definition; the
  reader can look them up.

## Open items found in session 41b (outside the prose)

- 5.1 *Checking results* says the computed features match the extracted ones on "73,063 edits"; that is run 107's
  direction check, while the exactness counts are Appendix D's table (62,604 in its upper block, run 118's 34,965
  declared edits). Fix with the scale-up's numbers unless the user wants it now.
- 5.2 says our hand table was written "before the derivation existed", from "the operation's declared effects". If a
  reviewer could ask whether the declared effects came with the derivation, check the history before rewording.

## Constraints and settled points

- §5.3: no audit table for now; no random-seed or protocol-hygiene details in the paper; the learned-region paragraph
  stays cut; rename gets one sentence, no new run. Points a careful reader may stop at (have answers ready, do not
  change pre-emptively): PV judged on 9 files (counts, not rates); "PV pays for the same gap a second time"; 928 of
  1,070 without a comparison (the seed comparison is out by the user's decision); ERDALT is "our implementation of
  their design" (it follows their paper where their released code breaks the guarantee; Appendix D); the toolkit
  evasions of the GAMMA attacks are partly outside the threat model (5.4 *Beyond the guarantee*).
- §5.4 (do not re-raise): the sums row's adaptive cell stays 0% with its footnote; the full-training-set cells keep
  theirs; never scale a cell down to the pilot protocol; one toolkit column counting any of the eight attacks; no
  comparison of the adaptive attack's 51% with the toolkit's rate; no derivation-cost or timing paragraph.
- Tables 3 and 4 will be remade: do not spend findings on their layout; note only what a table fails to tell.
- Explain plainly, no jargon. Claims say "on EMBER"; the detectors' accuracy cost is a measurement, never "small"; no
  "pilot" in the paper; no timing of Proposition 1 against extraction; no effort claims. Exact numbers matter less than
  structure and argument while drafting. Keep the session focused: short notes, a recommendation rather than a menu.
- Commit to `main` in logical pieces; do not push. At the end of the session, re-read and update `docs/status.md`,
  write the next resume prompt (archive this one under `docs/archive/` and index it in `docs/README.md`).
