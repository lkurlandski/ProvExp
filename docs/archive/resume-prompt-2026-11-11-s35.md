# Resume: §5.4 *What Robustness Costs*, in small blocks, while §5.3 waits on run 133 in another session

**The project, in two sentences.** ProvExp is dissertation research on *sum-then-readout* feature extractors (find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals): the
feature-space effects of an attacker's edits are computed from the instrumented extractor (exactly for one edit,
Proposition 1; as sound directions for a whole threat model, Theorem 1), and from those, monotone detectors no edit
in the threat model can evade (Corollary 1). PE malware with EMBER 2024 is the instance; the paper is written straight
into `manuscript/*.tex` (ACM `sigconf`), §5 *Evaluation* is in `manuscript/_f_evaluation.tex`.

**Read first:** `CLAUDE.md` (rules), `docs/status.md`, and `PLAN.md` (decision 10 above all: §5 is three findings
about adversarial examples, *What Hand Analysis Misses* (5.2), *What Observed Attacks Miss* (5.3), *What Robustness
Costs* (5.4); not a validation section and not a defense paper; this structure is agreed, do not reopen it). Then the
paper mock's plan for 5.4 (`docs/paper-mock.md`, §5, the item "5.4 What Robustness Costs", five numbered paragraphs),
and §5 as it now stands in the compiled PDF (`manuscript/main.pdf`): the lead, 5.1 and 5.2 were revised with the user
in session 35 and are the reference for tone and vocabulary.

## Another session owns §5.3 and run 133: do not touch them

Session 34 may still be open to read **run 133** (`run/133_varied_observation.sh`, ~7 h, launched by the user): it
rebuilds the defenses learned from attacks (PV, ERDALT, adversarial training) from varied attack runs on training
malware, because session 34 found that PV's hole, and its 14/22 adaptive evasion, rest mostly on the attack harness
resetting the RNG to seed 0 before every run. The plan for §5.3 is `docs/section-5.3-design.md`. In this session:

- Do not edit §5.3's text (`\subsection{What Observed Attacks Miss}`), `docs/section-5.3-design.md`, `run/133_*`, or
  anything under `artifacts/experiments/a_varied/`, `artifacts/experiments/a_pv/best/`,
  `artifacts/experiments/a1/advtrain/generated-seedperfile/`; do not start jobs that compete with run 133 for CPU or
  GPU without asking. Check `git log` first: session 34 may have committed changes to §5.3, the plan, or the status.
- `docs/status.md` and `PLAN.md` are shared: re-read them right before editing, change only your own lines.
- §5.4's draft still contains the PV, ERDALT, adversarial-training and cost paragraphs, and Table 4 still has their
  rows. They belong to 5.3's audit table, which session 34 settles. Leave them where they are, or mark them with a
  comment, without rewriting them.

## The task: block 4, §5.4 *What Robustness Costs*

The subsection is labelled `sec:eval:detectors`; its title in the draft is still "Detectors the Threat Model Cannot
Evade". Its table is `tab:eval:detectors`, compiled as **Table 4** ("Detectors under the full threat model");
check `manuscript/main.aux` before naming any number, and give the title alongside.

The mock's plan, in brief (verify each number against its `% MEASURED` comment or artifact before using it):
1. The finding: with the directions known, robustness against every structural edit in the threat model costs about
   four points of detection (93.5% to 89.6% TPR at 1% FPR on the sums; 87.2% on the features), with 0% evasion on
   files in the population; the adaptive attack's largest score drop is exactly 0.
2. Where the cost lies, per operation: import addition 2.1 points, the three header overwrites 1.4, the rest at most
   0.3; dropping the two-sided features 0.2; reading the sums recovers about two points.
3. The threat model's width: additions only gives 92.2%, and header-field attacks then evade on 28%; the expert set
   under the same threat model detects 29.1%.
4. Beyond the guarantee: GAMMA's rebuilding injections move features outside the table and still evade no monotone
   row on files in the population (0/56, 0/60; also at the literature's budget); 41 of 42 malware still detected
   after every toolkit attack, against 21 of 47 undefended.
5. Scope: the population (38 of 50 pilot malware; 1.5% of untruncated benign files outside it).
The table is trimmed to the undefended rows, the monotone rows and the additions block; the baselines move to 5.3.

**How to work (memory `draft-in-small-blocks`; the `paper-prose` skill for all prose):**
1. Read the current §5.4 text, Table 4 and its `% MEASURED` comments, and the mock's plan. Check every number against
   its source and list any mismatch.
2. Write a short note for the user first: what each paragraph establishes and why the reader needs it there, the
   trimmed table (rows, columns, footnotes), and the open points below with one recommendation each. Wait for
   approval.
3. Draft a few paragraphs at a time; after each block `make` and `make check` in `manuscript/`, read the rendered
   text with `pdftotext` as the user will, show it, and apply the user's comments before the next block. Log the
   user's raw reactions in `docs/writing-spec.md`.

## Open points to raise in the note (do not decide them alone)

- **The sums row's adaptive cell** (0%, footnote $^\ast$: a greedy search with 200 candidates, because the beam cannot
  score the sums detector yet). The `% MEASURED` comment calls it a "greedy union of runs 108/119", which conflicts
  with memory `report-attacks-separately` (one attack per cell, never a union). Expected 0% by construction either
  way; options: report one run, mark the cell as guaranteed by Corollary 1, or route the beam (PLAN.md step 5).
- **Footnote $^\S$:** the monotone rows' adaptive cells use models trained on the full training set while their other
  cells use the 10% subsample. One protocol per table (memory `consistency-and-simplicity`); say so to the user.
- **The toolkit columns:** "Seen" and "Held-out" exist for the learned defenses. With those rows gone, the trimmed
  table needs one toolkit column (all eight attacks, each reported separately or as the share of files any of them
  evades; ask, given `report-attacks-separately`). Caption: call the attack "the adaptive attack" as 5.1 now does.
- **Toolkit evasions outside the threat model:** 14 of the toolkit's 27 evasions on the undefended detector come only
  through GAMMA's LIEF relayouts, which lie outside the threat model; the six in-catalogue toolkit attacks evade 13/49
  (run 127's header). This is the substance of paragraph 4 (beyond the guarantee) and must be stated accurately; do not
  use "51% against 53%" as evidence that the adaptive attack is no stronger than the toolkit.
- **How tight the derived table is:** our own edits (catalogue_checks, 2,000 test files, re-extracted) lower 915 of
  the 1,070 features the table marks lowerable under the full threat model (`artifacts/experiments/a_coverage/
  report.json`); the 155 never lowered are 78 parser warnings and 67 strings. It suggests the four points are not
  mostly the table's looseness. Propose it for paragraph 2 only with the user's agreement (memory
  `dont-reframe-research-claims`).
- **Scope paragraph:** the mock's "deriving the table costs one pass per extractor (about 5 minutes), PV repeats its
  attack runs per attack" compares with PV, which is 5.3's and changes with run 133, and it is a cost claim (memories
  `no-timing-claims`, `no-effort-claims`). Ask whether it stays.

## What session 35 settled in 5.1 (use the same terms in 5.4)

- 5.1 has three run-in paragraphs: *Detectors* (10% subsamples of EMBER 2024's splits, one seed, 100 test files, half
  malware, thresholds at 1% FPR), *Attacks*, *Checking results*.
- An attack evades when it drives a detected malware sample below the threshold, adding at most 5% of the file or
  512 KB. The **toolkit attacks** (eight, §4.3) are black-box: each applies one kind of edit, tuned by a genetic
  algorithm that sees only the score, 100 queries per file, as in Gimenez et al. The **adaptive attack** is ours,
  "a white-box adaptive attack, in the spirit of Tramèr et al." (`tramer2020adaptive`): it reads the detector's trees,
  combines any operations of the full threat model, computes candidates' features by Proposition 1, up to 5,000
  candidates per file; its beam-search mechanics are in Appendix D ("The adaptive attack").
- Every evasion is decided by writing the file and extracting it again; the computation only guides the search.

**What the user's reactions in session 35 say about drafting 5.4** (full log: `docs/writing-spec.md`): give each
design choice its purpose, then its facts, plainly ("just state the number"); a definition must separate what it
defines from everything else; mechanics a reader does not need go to an appendix; run-in headings in §5's
subsections; no jargon. The first rewrite of 5.1's Attacks paragraph drew a very harsh reaction for failing these.

## Also waiting (not this session's task unless the user brings it)

- The user's remaining comments on 5.1 (*Checking results*) and on 5.2, current version 9b7d0ba.
- After 5.3 is settled: §2's closing sentence and contribution 4 against the findings; shortening §4 and §5 together
  (§4.3 first); PLAN.md step 4 (the next full simulated review).
- The scale-up (seeds 0-2, full splits): the user wants it first once the write-up is finished (PLAN.md step 5).

## Constraints (from CLAUDE.md, the memory, and the user)

Claims say "on EMBER"; no timing of Proposition 1 against extraction; the detectors' accuracy cost is a measurement,
never "small" (memory `findings-not-defense-paper`); report each attack separately, never a union; ask before
changing what a claim or statistic is for; check `manuscript/main.aux` before naming a table, section or definition
number, and give its title alongside (definitions are referenced as `Definition~\ref{...}`: `\Cref` prints "??" for
them); exact numbers matter less than structure and argument at this stage; explain plainly. Jobs over ~10 minutes go
to the user as numbered `run/` scripts (check the highest number first: 133 is taken). Before committing:
`env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts` when code changed. Commit to `main` in
logical pieces; do not push. At the end, update `docs/status.md` (re-read it first) and write the next resume prompt.
