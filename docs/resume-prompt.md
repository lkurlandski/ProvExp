# Resume: after §5's review, the structural work on §4-5 (questions and answers, tables, shortening)

Written at the end of session 41b (2026-11-12, parallel to session 41's ERDALT check). Self-contained: everything
needed to start is below or in the files it names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find
the pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1). From those directions come monotone detectors that no
edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. The paper
is written straight into `manuscript/*.tex` (ACM `sigconf`; `make` and `make check` in `manuscript/`). Check
`manuscript/main.aux` before naming a section, table or definition number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 10: §5 is three findings about adversarial
examples, not a validation section and not a defense paper; "Next steps"). The `paper-prose` skill governs any prose;
the user's raw reactions are at the end of `docs/writing-spec.md` (sessions 35-41 are the ones on §4-5).

## Where things stand

§2-4 are in good shape (§4 reviewed twice). §5 (`manuscript/_f_evaluation.tex`) was reviewed with the
`humanistic-paper-review` skill in session 41b, one subsection per pass; the user approved every finding they did not
drop, and all are applied (ce4ba21, f8baea5, 1053bf7, e8b0335). Each subsection's lead now ends by answering its
question, as a stopgap. The user has not read §5 end to end; they approved changes, not the whole text.

## The task: PLAN.md next step 2, to be considered with the user (in this order, one at a time)

0. **§5's questions and answers given visual emphasis.** The user (2026-11-12): "serious structural modifications ...
   with regard to how the research questions are presented, i.e., 'asked', and how the findings are presented, i.e.,
   'answered' ... more visual emphasize to the questions and answers." Nothing is designed yet. Start by proposing,
   briefly, two or three concrete ways it could look on the page (e.g., each subsection opens with its question set
   off, and closes or opens with a boxed or bold-run-in answer), shown as rendered snippets, and let the user choose.
   Check the closest accepted CCS papers in `papers/` for how they do it, if any. Do not draft before they choose.
1. **Remake the tables** (Tables 3 and 4 above all; the user dislikes them). Do this before shortening.
2. **Shorten §4 and §5 together** (§4 ~1,500 words against ~1,000; §4.3 first). Trimming is welcome; moving small
   snippets to the appendix does more harm than good.
3. **Align §2's closing sentence and contribution 4** with §5's three findings.

Then (PLAN.md): the 4 MB-truncation brainstorm; then decide with the user whether the paper is ready for the next
full simulated review; the scale-up once the write-up is finished.

## Open items found in the review (outside the prose)

- 5.1 *Checking results* says the computed features match the extracted ones on "73,063 edits"; that is run 107's
  direction check, while the exactness counts are Appendix D's table (62,604 in its upper block, run 118's 34,965
  declared edits). Fix with the scale-up's numbers unless the user wants it now.
- 5.2 says our hand table was written "before the derivation existed" and from "the operation's declared effects".
  If a reviewer could ask whether the declared effects came with the derivation, check the history before rewording.

## Constraints and settled points

- How the user wants reviews and changes handled: keep finding numbers; small passes, the approved ones first; show
  old and new text; a finding that touches what a claim rests on is verified in the code and run outputs first.
- §5.3: no audit table for now; no seed or protocol-hygiene details; the learned-region paragraph stays cut.
- §5.4: the sums row's adaptive cell stays 0% with its footnote; the full-training-set cells keep theirs; never scale
  a cell down to the pilot protocol; one toolkit column counting any of the eight attacks; no comparison of the
  adaptive attack's 51% with the toolkit's rate; no derivation-cost or timing paragraph.
- Claims say "on EMBER"; the detectors' cost is a measurement, never "small"; no "pilot" in the paper; no effort
  claims. Exact numbers matter less than structure and argument while drafting.
- Commit to `main` in logical pieces; do not push. At the end of the session, update `docs/status.md`, write the next
  resume prompt, archive this one under `docs/archive/` and index it in `docs/README.md`.
