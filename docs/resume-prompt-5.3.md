# Resume: finish run 135 in §5.3 *What Observed Attacks Miss*, then the user's review of §5.3

Written at the end of session 39 (2026-11-11), which drafted §5.3 in parallel with session 38 (the §4 review).
Self-contained: everything needed to start is below or in the files it names. (`docs/resume-prompt.md` belongs to the
parallel track, a second review of §4 and then the holistic review of §5; leave it alone.)

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions (which way each feature can move) for a whole threat model (Theorem 1). From those directions
come monotone detectors that no edit in the threat model can evade (Corollary 1). PE malware with EMBER 2024 is the
instance. The paper is written straight into `manuscript/*.tex` (ACM `sigconf`; `make` and `make check` in
`manuscript/`). §5 *Evaluation* (`manuscript/_f_evaluation.tex`) is three findings about adversarial examples (PLAN.md
decision 10; agreed, do not reopen): 5.2 *What Hand Analysis Misses*, **5.3 *What Observed Attacks Miss***
(`sec:eval:observed`), 5.4 *What Robustness Costs* (`sec:eval:detectors`, Table 4). Appendix D *The EMBER Instance*
is `manuscript/_j2_ember.tex`. Check `manuscript/main.aux` before naming a section, table or definition number, and
give its title alongside (at the end of session 39: Table 4 = detectors, Table 9 = leave-one-out in Appendix D).

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 10, the notes of sessions 34 continued, 36 and
39). §5.3 as it stands in `manuscript/_f_evaluation.tex` (read it in the PDF with `pdftotext`, as the user will).
Use the `paper-prose` skill for any prose; the user's raw reactions are in `docs/writing-spec.md`. Background only if
needed: `docs/section-5.3-design.md` (how the design came about; §10.4 holds run 133's results table).

## What session 39 did

Drafted §5.3 in three blocks (commits 7a2ceff, 9d0369f, 035d977), about 970 words against a budget of ~950. **The
user has not read any of it**; they will review it in the next session. Decisions the user made during the session:

1. The learned-region paragraph (exact tree solver on the old outputs) is cut.
2. No audit table for now. The user considers Tables 3 and 4 "incredibly disgusting"; all tables will be remade
   together later, so 5.3 reports its defenses in prose. Do not propose the audit table again unless the tables are
   being redesigned.
3. Rename gets one sentence (adding it to the attacks would close PV's hole, but the defender learns which operation
   to add only after an attacker used it); no new run.
4. **No random-seed or protocol-hygiene details in the paper** ("do the obviously correct thing in our experiments and
   leave it at that"). So the seed-reset comparison (847 vs 928 lowered features) and the published-style PV's 14/22
   are out of the paper.

The agreed finding: a defense learned from observed attacks inherits what the attacks did not do, and nothing in the
observations says what that is. §5.3's seven run-in paragraphs, with numbers and sources (also in `%` comments beside
each paragraph):

- **Opening:** the protocol. PV, ERDALT and adversarial training are all built from the same 3,183 outputs of the
  eight toolkit attacks on 400 training malware (benign training files as donors; run 133's
  `artifacts/experiments/a1/advtrain/generated-seedperfile`), then attacked as in 5.1 on the test malware each detects.
- **What the attacks reveal:** on the 314 training files in the population the outputs lower 928 of the 1,070
  features the derived table says the full threat model can lower; our own edits lower 20 of the other 142, among
  them the entry section's name buckets (rename; no toolkit attack renames, MAB-Malware does)
  (`a_varied/coverage/report.json`).
- **The operation the attacks lack:** PV detects 9 of 50 test malware; the toolkit evades it on none, the adaptive
  attack on 4 of 9, each with one rename of the entry section within the first 50 candidates; its hole is 124
  features, 38.8% of its split gain, the largest an entry-section-name bucket at 12.8%.
- **What the attacks did not move:** PV detects 26.2% at 1% FPR against 87.2% for the derived detector on the same
  features (Table 4); the DLL flag (24% of the unconstrained detector's gain) cannot be moved by any edit, PV forces it
  monotone; leaving the 455 never-moved features free gives 50.9% (run 134, PV-free) but is unsound.
- **What ERDALT learns:** our port detects 62.7% at 1% FPR, 29 test malware; seven toolkit attacks evade it on none,
  GAMMA's import injection (one of its training attacks, but now with test-set donors) on 24; the adaptive attack 22;
  90% of its layer's weight lies on features an edit can lower. The score-floor caveat (every evasion ends at p =
  0.49966 against tau = 0.49968) is only in a comment.
- **Adversarial training:** detection unchanged (95.6%); toolkit 12/50 (before: 25/49); adaptive 23/50 (before 25/49).
- **Holding one attack out:** run 135, below. Per-fold table `tab:ember:loo` in Appendix D (attack names as in
  Table 2).

Also done: the old PV/ERDALT/adversarial-training paragraphs and table-row comments were removed from 5.4 (it ends
with *Beyond the guarantee*); §6's ERDALT sentence now points to `sec:eval:observed`. Small fact found: the TPR of the
derived detector on the features is 87.21% by ROC interpolation (`scripts/a_price_list.py`'s method, with `polars`;
`pandas` cannot read the parquet files in this env), and PV-best 26.3% by the same method; the run 133/134 headers'
87.3% and 26.2% came from another computation. The prose uses 87.2% and 26.2%; settle one method when the tables
are remade.

## Step 0: run 135

**Run 135** (`run/135_loo_varied.sh`, launched by the user 2026-11-11 16:33): for each of the eight toolkit attacks,
PV and ERDALT are built from run 133's outputs of the other seven, then attacked by the eighth on the test malware they
detect. Outputs: `artifacts/experiments/a_loo_varied/` (`pv/<attack>/table.json`, `erdalt/<attack>/table.json`,
`summary.json`); logs `artifacts/logs/*vloo*.log`. Check that it has finished (`summary.json` exists, no
`a1_evaluate`/ERDALT process running) before editing its header: never edit a running `run/` script.

- **PV folds, already read:** 0 evaded in all eight (detected: gamma_sections 19, gamma_api 9, gamma_shift 9,
  content_shift 9, dos_extend 9, header_fields 9, padding 9, format_exploit 8). The header predicted 0-2 per fold,
  gamma_api perhaps 1-2 (it is 0): held. The detected counts differ from the header's guess of ~9-10 on one fold
  (gamma_sections, 19).
- **ERDALT folds:** were still running at the end of session 39. Header's predictions (now in blue in the paper):
  high on the gamma_api fold (~25 of ~29) and header_fields (~10 of ~29), near 0 on the rest.

Then: (1) say plainly which hypotheses held and which failed; (2) record the results and runtimes in run 135's
header (a "Results" block, as runs 133-134 have), in `docs/section-5.3-design.md` (§10.4 and its log) and in
`docs/status.md`; (3) replace every `\synthetic{...}` in 5.3's *Holding one attack out* and in Table 9's ERDALT
columns, and delete the `% SYNTHETIC: run 135` comments. If the ERDALT numbers differ from the prediction, the
paragraph's sentences about ERDALT ("in two of the eight folds", "the test shows that ERDALT fails, but not on which
features") must be rewritten to what the run shows, without changing the finding (memory
`dont-reframe-research-claims`): if the held-out attacks rarely evade ERDALT, that is the PV case again (the test
vouches for a defense its own training attack with other donors evades, 24/29). Show the user the changed text.
`make`, `make check`, commit.

## Step 1: the user's review of §5.3

The user reviews the text tomorrow. Ask first whether 5.3's review is its own pass or joins the parallel holistic
review of §5 (`docs/resume-prompt.md`), so the two tracks do not edit the same paragraphs. Follow memory
`review-comments-workflow`: answer the user's questions first, plainly; then a numbered plan, one recommendation per
comment; small passes; report per item; log the user's raw reactions in `docs/writing-spec.md` (never as rules).

Points a careful reader may stop at, to have answers ready (do not pre-emptively change them):
- PV is judged on 9 files (it detects little); the counts are given, not rates. The scale-up adds files later.
- "PV pays for the same gap a second time, in detection" ties two paragraphs; it may read as staged.
- *What the attacks reveal* states 928 of 1,070 without a comparison (the seed comparison is out by decision 4), so
  its point rests on "the other 142 look the same as features no edit can lower".
- ERDALT is "our port of their code"; the paper does not claim their published numbers fail.
- The toolkit evasions of the GAMMA injections are partly outside the threat model; 5.4 *Beyond the guarantee*
  explains this, and 5.3 does not repeat it.

## Constraints

Claims say "on EMBER"; §5 is findings, not a defense paper, and the detectors' accuracy cost is a measurement, never
"small" (memory `findings-not-defense-paper`); say what each evasion rate covers (memory
`attack-strength-vs-literature`); never a union across searches (memory `report-attacks-separately`); no timing or
effort claims; explain plainly; portray Gimenez et al. accurately (`papers/gimenez2025certifiably.pdf`). Jobs over
~10 minutes go to the user as numbered `run/` scripts (136 is next). Commit to `main` in logical pieces; do not push.
The parallel session may edit `docs/status.md` and `PLAN.md`: re-read them right before editing and change only your
own lines. At the end: update `docs/status.md`, archive this prompt under `docs/archive/` and index it in
`docs/README.md`.
