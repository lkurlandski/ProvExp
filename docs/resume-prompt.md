# Resume: remake §5's tables, starting from what the user dislikes

Written at the end of session 42 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with the EMBER 2024
extractor is the instance; the framework is format-free. The paper is written straight into `manuscript/*.tex` (ACM
`sigconf`, CCS format; `make` and `make check` in `manuscript/`). §5 *Evaluation* (`manuscript/_f_evaluation.tex`) is
three findings about adversarial examples (PLAN.md decision 10; agreed, do not reopen): 5.1 *Setup*, 5.2 *What Hand
Analysis Misses*, 5.3 *What Observed Attacks Miss*, 5.4 *What Robustness Costs*. Appendix D *The EMBER Instance* is
`_j2_ember.tex`. Check `manuscript/main.aux` before naming a section, table or definition number, and give the title
alongside (`docs/README.md` has the numbering).

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 10, and "Next steps" step 2, whose item (a) records
the first table attempt and the facts it surfaced). The user's raw reactions are at the end of `docs/writing-spec.md`
(sessions 35-42 concern §4-5; session 42's table brief and verdict are the last entry).

## Where things stand

- §2-4 are in good shape. §5 is fully drafted, reviewed per subsection (session 41b) and as a whole (session 42). In
  session 42, the holistic review's findings 1-4 were applied (68f6385): what Gimenez et al. report (no toolkit attack
  evades their expert-set detector or PV; detection and robustness a "trade-off regarding features set") now precedes
  our results; the §5 lead names what breaks; 5.4's comparison names both alternatives (learned from attacks, chosen
  by hand); 5.2's cost paragraph ends on why a broken guarantee matters. The uncited "usually tested against an attack
  it did not learn from" was fixed (49d879d). Two notes for later are in PLAN.md step 2: no table shows 5.3's result
  (finding 6), and §2 promises an attack contribution §5 does not deliver (finding 7: a known weakness, not fixable now).
- **The tables come first** (user, session 42), before the question-and-answer emphasis, the shortening of §4-5, and
  §2's alignment.
- **The first table attempt failed.** The user's brief: tables "data-dense" rather than "linguistically-dense"
  (exceptions allowed when they give a better result), designed to (i) communicate the findings, (ii) be aesthetically
  pleasing, (iii) extend to other domains, the least important. Claude's mock-ups,
  `docs/archive/table-mockups-2026-11-12/mock.pdf` (source `mock.tex`), were judged "pretty bad, quite possibly as bad
  if not worse than what we already had", with no specifics. What they were: Table 3 redone with Cause and Files
  columns and row groups; a new 5.3 table of the learned defenses (AUC, TPR at two FPRs, detected, evaded by toolkit /
  held-out / adaptive, "weight on lowerable"); Table 4 in one column with short labels; a per-operation cost table
  (features dropped and constrained, TPR, with each operation left out); alternatively one detectors table grouped by
  where the directions come from. The user also dislikes the current Tables 3 and 4 ("incredibly disgusting",
  session 39).

## The task: the tables, restarted

1. **Find out what is wrong before designing anything.** Do not propose another full set. Open the session by asking
   the user, briefly and concretely, what makes the current Tables 3 and 4 and the mock-ups bad, with the PDFs at hand
   (`manuscript/main.pdf`, the mock above), and which tables they find good, in `papers/` or elsewhere. Their own papers
   are the strongest evidence of their taste: `papers/kurlandski2027dont.pdf` (tables on pp. 6-10, 12, 15-16: compact
   numeric grids, metrics by model, ± intervals, arrows for significance, very little text) and
   `papers/kurlandski2022impact.pdf`. Accepted security papers with comparable tables: `papers/lucas2024training.pdf`
   (CCS 2024, Table 2, p. 7), `papers/ling2024wolf.pdf` (USENIX 2024, pp. 10-11), `papers/dyrmishi2023empirical.pdf`
   (multi-domain tables). Render pages with `pdftoppm -r 70 -png -f N -l N file.pdf out` and view them.
   Things in the mock-ups that may have hurt, as hypotheses to check with the user, not conclusions: phrases in cells
   (the Cause column), six-line captions, many footnotes, two training protocols and two threat models in one table,
   long row labels, 10-11 columns. Also ask whether some content would be better as a figure than a table (main.tex
   already defines a plotting palette, `paper` pgfplots style); the per-operation cost and the learned defenses'
   evasion rates are candidates.
2. **Then one table at a time, small:** what the table must tell (one sentence), then one or two rendered alternatives
   in the paper's class (copy the mock's preamble), viewed by Claude as images before the user sees them. The user
   picks; only then into the manuscript, with the prose that cites the table adjusted. Start with whichever table the
   user cares about most (likely Table 4, the detectors, or the missing 5.3 table).
3. When done: `make`, `make check`, read the rendered text; log the user's reactions raw in `docs/writing-spec.md`;
   commit in logical pieces (main, no push).

## Data at hand (all pilot scale: 10% subsamples, one seed, 50 malware attacked; percentages over detected malware)

- **Table 4 today** (`tab:eval:detectors`, 5.4; AUC / TPR at 1% / at 0.1% FPR / detected / toolkit / adaptive):
  unconstrained 0.996 / 93.5 / 84.4 / 47 / 55% / —; unconstrained, full training set 0.998 / 95.6 / 87.0 / 49 / 55% /
  51%; monotone on derived directions, features 0.992 / 87.2 / 70.9 / 40 / 3%† / 0%§; same, sums 0.994 / 89.6 / 74.7 /
  42 / 2%† / 0%*; additions: expert set 0.844 / 29.1 / 14.8 / 8 / 0% / —; derived, sums 0.995 / 92.2 / 79.8 / 43 / 28%‡
  / —. Footnotes: † one evasion, a file outside the population; ‡ the header fields attack, outside the additions
  threat model; § adaptive cell on the full-training-set model; * a simpler search that appends and adds sections
  (settled, do not re-raise).
- **5.3's defenses, in prose only today** (built from run 133's 3,183 toolkit outputs on 400 training malware; AUC /
  TPR 1% / 0.1% computed in session 42 like Table 4's): PV 0.844 / 26.3% / 10.3%, detects 9, toolkit 0/9, adaptive 4/9
  (one rename each), leave-one-out 0 in all eight folds, 124 lowerable features with 38.8% of its split gain; ERDALT
  0.883 / 62.7% / 42.2%, detects 29, GAMMA imports 24/29 (the other seven attacks 0), adaptive 22/29, leave-one-out
  25/29 when GAMMA imports is held out and 0-2 otherwise (Table 9, `tab:ember:loo`), 90.5% of its layer's weight on
  lowerable features; adversarial training (full training set) 0.998 / 95.6% / 87.3%, toolkit 12/50, adaptive 23/50,
  against the unconstrained full-set detector's 25/49 and 25/49 (run 133's seed-per-file protocol).
- **Table 3 today** (`tab:eval:directions`, 5.2): the hand table's eight errors (feature, operation, hand → derived, in
  population, witness prose). Causes: structures past the end of the file (3 errors), the Rich header's fixed search
  range (2), the entry section's fallback rule (1), the overlay starting where the last section ends (1), a section
  holding the headers (1). Witness counts: 650/2,000; 8/100; 39/100; 8/100 (in population); 4/100; 2/100; 151 and
  37/2,000; 4/2,000 (outside). Plus one cautious disagreement: the certificate table's size (hand both, derived down).
- **Where the cost lies** (5.4 prose; `artifacts/experiments/a_price_list/table.json`): TPR at 1% / 0.1% with one
  operation left out (features dropped / constrained): full 89.6 / 74.7 (1,464 / 1,988); append 89.3 / 71.7; imports
  91.7 / 78.8 (1,460 / 706); gap before the PE header 89.6 / 77.1; DOS header 89.4 / 75.7; header fields 90.8 / 77.0;
  checksum 90.3 / 76.1; the three overwrites 91.0 / 79.2; rename 89.7 / 76.0 (1,163 / 2,289); remove debug 90.0 /
  75.2; remove certificate 90.0 / 75.0; add a section, first-section gap and slack change no direction; two-sided
  dropped, nothing constrained 93.3 / 79.2; unconstrained 93.5 / 84.4.
- Model directories: `/scratch/lk3591/provexp/models/{gbdt,erdalt}/` (`seed-0-s10-pv-best`, `erdalt/seed-0-s10-best`,
  `gbdt/seed-0-advtrain-seedperfile`, `seed-0-s10-mfull-{feat,sums}-pre-v2`, `seed-0-s10-expert-mono`), each with
  `ts_predictions.parquet` (read with polars in `env/bin/python`; TPR by `np.interp` on sklearn's ROC, as
  `scripts/a_price_list.py`). Adaptive results: `artifacts/experiments/a_varied/adaptive-*/adaptive.json`,
  `a1/adaptive-beam/*/adaptive.json`, `a1/hand-table/adaptive.json`.

## Open items found in session 42 (fix when the affected text is touched)

- 5.2's *Why it errs* says the errors come from "three facts about how the parser finds structures"; two of the eight
  come from others (the overlay starts where the last section ends; a section whose raw data starts at offset 0 holds
  the headers). The prose needs a matching fix; the Rich header and past-the-end facts stay.
- Table 4's toolkit cells come from the older fixed-seed runs (`a1/toolkit-v2`), 5.3's from run 133's seed per file;
  the full-set unconstrained detector reads 27/49 (55%) in Table 4 and 25/49 in 5.3. Nothing in the paper (user: no
  protocol hygiene); one protocol at the scale-up. A redesigned table that puts both together must pick one.
- `make check` reports a 2 pt overfull page box among the appendix floats since 68f6385 (harmless; layout will move).
- From session 41b: 5.1 says the computed features match on "73,063 edits" (run 107's direction check; the exactness
  counts are Appendix D's, 62,604 + run 118's 34,965); fix at scale-up unless the user wants it now. 5.2 says our hand
  table was written "before the derivation existed"; check the history before rewording if a reviewer could ask.

## After the tables (PLAN.md step 2, then 4-6; each considered with the user)

(0) §5's questions and answers given visual emphasis (the user: "serious structural modifications ... more visual
emphasize to the questions and answers"; first propose two or three looks as rendered snippets; Ling et al. box an
"Answer to RQ" paragraph, `papers/ling2024wolf.pdf` p. 11); (b) shorten §4 and §5 together (§4 ~1,500 words against
~1,000; §4.3 first); (c) §2's closing sentence and contribution 4 against §5's three findings (the attack promise is a
known weakness). Then the 4 MB-truncation brainstorm; then decide whether the paper is ready for the next full
simulated review (update `docs/reviews/review-prompt.md` first); the scale-up once the write-up is finished.

## Constraints and settled points

- Explain plainly, no jargon; short notes, a recommendation rather than a menu; keep the session focused.
- Claims say "on EMBER"; the detectors' cost is a measurement, never "small"; no state-of-the-art defense claim and no
  defense-paper framing (decision 10); no "pilot" in the paper; no timing of Proposition 1 against extraction; no
  effort claims; no random-seed or protocol-hygiene details in the paper.
- §5.4 (do not re-raise): the sums row's adaptive cell stays 0% with its footnote; the full-training-set cells keep
  theirs; never scale a cell down to the 10% protocol; one toolkit column counting any of the eight attacks; no
  comparison of the adaptive attack's 51% with the toolkit's rate.
- §5.3: points a careful reader may stop at (have answers ready, do not change pre-emptively): PV judged on 9 files;
  "PV pays for the same gap a second time"; 928 of 1,070 without a comparison; ERDALT is "our implementation of their
  design" (it follows their paper where their code breaks the guarantee); the toolkit evasions of the GAMMA attacks
  are partly outside the threat model.
- Reviews and feedback: keep finding numbers; small passes, approved items first; show old and new text per item;
  trimming is welcome, but moving very small snippets to the appendix does more harm than good; log reactions raw,
  never as rules (the `paper-prose` skill governs prose).
- At the end of the session: update `docs/status.md` and PLAN.md, write the next resume prompt (archive this one under
  `docs/archive/` and index it in `docs/README.md`).
