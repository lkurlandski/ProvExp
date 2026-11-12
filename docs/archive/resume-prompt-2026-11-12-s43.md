# Resume: does §5 need more tables? A check-in with the user

Written at the end of session 43 (2026-11-12). Self-contained: everything needed to start is below or in the files it
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

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 10; "Next steps" step 2, item (a)). The user's raw
reactions are at the end of `docs/writing-spec.md` (session 43's entry is about the tables).

## Where things stand

- §2-4 are in good shape; §5 is fully drafted and reviewed (per subsection in session 41b, as a whole in session 42).
- **Tables 3 and 4 were remade in session 43** (7788592, 52e07cc), after asking the user what they disliked (footnote
  symbols, captions that argue the finding, phrase row labels, two threat models or training sets mixed in one table,
  prose in cells; "these are the ugliest tables I have ever seen in my life"). Their models: their own ExeFormer tables
  (`papers/kurlandski2027dont.pdf`, p. 7) and Lucas et al.'s Table 2 (`papers/lucas2024training.pdf`, p. 7). What the
  accepted versions do: one column; data only, no sentences in cells; short row labels; arrows in headers for which
  direction is better; bold for the best value; a rule between the baseline and our detectors; counts such as 26/47
  instead of percentages plus a "detected" column; group labels (*In the population*) instead of a yes/no column; a
  one-line caption that names the table, with the finding in the text; no footnotes (their content in the text).
  - Table 4 (`tab:eval:detectors`, 5.4): two halves in one float, the full threat model (unconstrained, monotone on
    the features, monotone on the sums: AUC, TPR at 1% and 0.1% FPR, evaded by any toolkit attack) and additions only
    (the expert set, monotone on the sums; evaded split inside/outside the threat model: 0/8, 0/8; 0/43, 12/43). The
    adaptive results are now sentences in *The price* (25 of 49 on the full-training-set unconstrained detector; no
    score drop on the monotone ones). The user: "not perfect, but its good enough that I can actually look at it, read
    it, understand it". They want the two halves more consistent (the same detectors in both), which may need runs:
    a scale-up item, not now.
  - Table 3 (`tab:eval:directions`, 5.2): feature / operation / hand / derived / files, grouped by population, eight
    rows. *Why it errs* names the five parser facts behind the errors. The user hesitated between this and a numbered
    list by cause and asked Claude to decide; Claude chose the table (the finding at a glance, PE detail contained in
    a float, its columns fit other extractors and domains).
- `manuscript/tmp-tables.tex` (untracked, compiles to `tmp-tables.pdf`) is the comparison file the user asked for:
  the current version of a table on page 1, the proposed one on page 2. It now holds Table 3's comparison; overwrite
  it for the next table.
- A LaTeX trap found in session 43: when Table 3 became a one-column float, LaTeX silently dropped Table 9 (the
  leave-one-out table) at the end of the document, leaving two blank pages; declaring it earlier in Appendix D fixed
  it. After changing floats, check that `make check` reports no undefined references and that the page count did not
  jump.

## The task: a check-in on more tables

At the end of session 43 Claude suggested a next table, and the user answered: "you're asking now whether or not we
should add more tables to the evaluation? I think we should check-in and think about this question in a new session."
So this is a conversation, not a design session. Do not mock up or propose a layout until the user has decided that a
table should exist.

1. Open with the question itself, briefly and plainly: what each subsection shows a reader today, and where a table
   could carry a finding the prose carries now. The facts:
   - 5.2 has Table 3 (our hand table's errors); Gimenez et al.'s expert set (11 of 40 features lowerable, 2/8 evaded
     adaptively) and Severi et al.'s hashed features are prose.
   - 5.3 has no table. Its finding (published defenses that withstand their own attacks fall to edits the attacks did
     not make) is in prose only. Session 42's holistic review (finding 6) noted that a skimmer sees our hand table's
     errors and the cost, but not this result; the user then said it "needs more thought". Its leave-one-out folds are
     Table 9 in Appendix D.
   - 5.4 has Table 4; *Where the cost lies* is a paragraph of per-operation numbers.
   Considerations worth naming: the paper is over the page limit already but that does not matter yet (CLAUDE.md);
   §4 and §5 are to be shortened together (PLAN.md step 2 (b)); a table can replace prose rather than add to it; the
   question-and-answer emphasis (step 2 (0)) may change what each subsection needs.
2. Give an honest view if it helps the user think, but keep it short and let the user decide. If a table is wanted,
   then one table at a time as in session 43: what it must tell in one sentence, one or two rendered alternatives in
   `tmp-tables.tex` (old on page 1 if there is one, new on page 2), viewed by Claude as images first; into the
   manuscript only after the user picks, with the citing prose adjusted; `make`, `make check`; commit.
3. Log the user's reactions raw in `docs/writing-spec.md`.

## Data at hand, if a table is wanted (pilot scale: 10% subsamples, one seed, 50 malware attacked)

- **5.3's defenses** (built from run 133's 3,183 toolkit outputs on 400 training malware; AUC / TPR at 1% / 0.1% FPR
  from each model's `ts_predictions.parquet`, as Table 4's): PV 0.844 / 26.3% / 10.3%, detects 9, toolkit 0/9,
  adaptive 4/9 (one rename each), leave-one-out 0 in all eight folds, 124 lowerable features carrying 38.8% of its
  split gain; ERDALT 0.883 / 62.7% / 42.2%, detects 29, GAMMA imports 24/29 (the other seven attacks 0), adaptive 22/29,
  leave-one-out 25/29 when GAMMA imports is held out and 0-2 otherwise, 90.5% of its layer's weight on lowerable
  features; adversarial training (full training set) 0.998 / 95.6% / 87.3%, toolkit 12/50, adaptive 23/50, against the
  unconstrained full-set detector's 25/49 and 25/49 (run 133's seed-per-file protocol). Toolkit and adaptive results:
  `artifacts/experiments/a_varied/` (`toolkit-*`, `adaptive-*`).
- **Per operation left out** (`artifacts/experiments/a_price_list/table.json`; TPR at 1% / 0.1%, features dropped /
  constrained): full 89.6 / 74.7 (1,464 / 1,988); append 89.3 / 71.7; imports 91.7 / 78.8 (1,460 / 706); gap before the
  PE header 89.6 / 77.1; DOS header 89.4 / 75.7; header fields 90.8 / 77.0; checksum 90.3 / 76.1; the three overwrites
  91.0 / 79.2; rename 89.7 / 76.0 (1,163 / 2,289); remove debug 90.0 / 75.2; remove certificate 90.0 / 75.0; add a
  section, first-section gap and slack change no direction; two-sided dropped, nothing constrained 93.3 / 79.2;
  unconstrained 93.5 / 84.4.
- **Toolkit per attack** for Table 4's detectors: `artifacts/experiments/a1/toolkit-v2/table.json` (`per_attack`).

## After this (PLAN.md step 2, then 4-6; each considered with the user)

(0) §5's questions and answers given visual emphasis (first propose two or three looks as rendered snippets; Ling et
al. box an "Answer to RQ" paragraph, `papers/ling2024wolf.pdf` p. 11); (b) shorten §4 and §5 together (§4 ~1,500 words
against ~1,000; §4.3 first); (c) §2's closing sentence and contribution 4 against §5's three findings (the attack
promise is a known weakness). Then the 4 MB-truncation brainstorm; then decide whether the paper is ready for the next
full simulated review (update `docs/reviews/review-prompt.md` first); the scale-up once the write-up is finished
(including Table 4's consistency between its halves).

## Open items (fix when the affected text is touched)

- 5.1 says the computed features match on "73,063 edits" (run 107's direction check; the exactness counts are
  Appendix D's, 62,604 + run 118's 34,965); fix at scale-up unless the user wants it now.
- 5.2 says our hand table was written "before the derivation existed"; check the history before rewording if a
  reviewer could ask.
- The toolkit cells of Table 4 come from the older fixed-seed runs (`a1/toolkit-v2`), 5.3's from run 133's seed per
  file; nothing in the paper (no protocol hygiene); one protocol at the scale-up.

## Constraints and settled points

- Explain plainly, no jargon; short notes, a recommendation rather than a menu; keep the session focused.
- Claims say "on EMBER"; the detectors' cost is a measurement, never "small"; no state-of-the-art defense claim and no
  defense-paper framing (decision 10); no "pilot" in the paper; no timing of Proposition 1 against extraction; no
  effort claims; no random-seed or protocol-hygiene details in the paper.
- §5.4 (do not re-raise): the sums detector's adaptive result is a simpler search that appends and adds sections, now
  said in the text; the full-training-set results keep their values; never scale a result down to the 10% protocol;
  one toolkit evasion count over any of the eight attacks; no comparison of the adaptive attack's rate with the
  toolkit's.
- §5.3: points a careful reader may stop at (have answers ready, do not change pre-emptively): PV judged on 9 files;
  "PV pays for the same gap a second time"; 928 of 1,070 without a comparison; ERDALT is "our implementation of their
  design" (it follows their paper where their code breaks the guarantee); the toolkit evasions of the GAMMA attacks
  are partly outside the threat model.
- Reviews and feedback: keep finding numbers; small passes, approved items first; show old and new text per item;
  log reactions raw, never as rules (the `paper-prose` skill governs prose).
- At the end of the session: update `docs/status.md` and PLAN.md, write the next resume prompt (archive this one under
  `docs/archive/` and index it in `docs/README.md`).
