# Resume prompt: manuscript review fixes, one piece at a time (Sonnet)

Written 2026-11-17 (end of session 80). The scale-up runs on tigris; nothing here depends on its numbers. Read
`CLAUDE.md` and `docs/status.md`'s *Current state* and the session-80 entry. Nothing else is needed.

## How to work (the user's instruction, session 80)

- **One piece at a time.** Apply one fix to the `.tex` (not several), run `make` and `make check` in `manuscript/`,
  show the user the old and the new text (and what you checked in the source), and **wait for their verdict** before
  starting the next. Commit a piece only after the user approves it.
- **The user rejects some proposed changes.** The register entries come from simulated reviews and are not
  instructions; the user judged R4's and part of R5's fix "stupid" and was right (the extractor is defined
  algebraically in §3.1). Do not defend a rejected change; revert it (`git checkout -- <file>`) and move on.
- Keep related-work text short and about the cited work and the difference from ours; the reader knows our method.
- Cite from `papers/` only (quote the PDF); never write a claim about a paper from memory. A paper that is not there:
  say so and leave `% TODO cite`. Use the S&P version of Pierazzi et al.; do not cite the TOPS version.
- Use the `paper-prose` skill when writing; wrap `.tex` lines at 120.

## What is done (committed)

A.1, A.3, B.1 (see the status entry); C.2 §2's closing reason (R5); C.3 the attacker named (R15); C.4(a) the query
budget attributed to Gimenez et al.'s released script; C.4(b) the certified-defenses paragraph in §6. Rejected by the
user, not to be redone: C.1 (R4) and C.2's §6 part.

## What is left, in order

**C.4(c) R21: cite where they fit**, one citation at a time, each with the sentence it supports checked against the
PDF: Kantchelian et al. (`kantchelian2016evasion.pdf`; finds the nearest evading instance of a tree ensemble under
constraints, a model analysis that takes the feature-space attacker as given, like Calzavara et al., already cited in
§6), Lucas et al. 2024 (`lucas2024training.pdf`; training robust raw-binary detectors without adversarial examples, at a
fraction of the cost; fits where §6 cites Lucas et al. 2023 on adversarial training), Tsingenopoulos et al.
(`tsingenopoulos2024train.pdf`; reinforcement-learning adversarial examples in the problem space for a detector of
dynamic-analysis reports). `main.bib` has Kantchelian and Lucas 2024; Tsingenopoulos needs an entry (arXiv 2402.19027,
from the PDF's front matter). Zainab et al. and Calzavara et al. are already cited. Skip Cortellazzi et al. (it is the
TOPS version of Pierazzi et al.). Gibert et al.'s certified-detector papers are not in `papers/`: ask the user for them
if the user wants them in §6's certified-defenses paragraph (`% TODO cite` there).

**C.5 The review passes.** After C.4(c), run the `humanistic-paper-review` skill on the passages changed this session
(§2's new sentence, §4.3's attacker paragraph, §5.1's query sentence, §6's certified-defenses paragraph) and, separately,
on §3.3's Lemma 1 (*Closure*), the readout rule and Table 1 (`_d_framework.tex`; proofs in `_j_proofs.tex`). Report the
findings to the user and apply them one at a time like the rest. One thing noticed already, not yet raised: after
Lemma 1 the text says "The same holds for lower bounds on features that the table does not allow to fall", then gives
an example (a count of unwanted items bounded above by 0) that is the lemma's own case, not a lower bound; the user has
not seen this. The user reads §3.3 only after this pass.

**C.6 Not now.** §2's closing sentence and contribution 4 of `docs/paper-mock.md` wait for the user's discussion of the
motivation. The prepared note is in the status entry. Do not edit either.

**Also open, small.** (1) The byte budget (5% of the file or 512 KB, ours, not Gimenez et al.'s) may be reconsidered
later: the user said so; do nothing now. (2) Check Giri et al.'s author names in `main.bib` (`giri2026towards`).

## At the end

Update `docs/status.md` (a short session-log entry) and commit the docs.
