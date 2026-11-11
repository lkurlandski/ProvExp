# Resume: §5.1-5.2 feedback, then §5.4 — while §5.3 waits on run 133 in another session

**The project, in two sentences.** ProvExp is dissertation research on *sum-then-readout* feature extractors (find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals): the
feature-space effects of an attacker's edits are computed from the instrumented extractor (exactly for one edit,
Proposition 1; as sound directions for a whole threat model, Theorem 1), and from those, monotone detectors no edit
in the threat model can evade (Corollary 1). PE malware with EMBER 2024 is the instance; the paper is written straight
into `manuscript/*.tex` (ACM `sigconf`), §5 *Evaluation* is in `manuscript/_f_evaluation.tex`.

**Read first:** `CLAUDE.md` (rules), `docs/status.md`, and `PLAN.md` (decision 10 above all: §5 is three findings
about adversarial examples, *What Hand Analysis Misses* (5.2), *What Observed Attacks Miss* (5.3), *What Robustness
Costs* (5.4); not a validation section and not a defense paper; this structure is agreed, do not reopen it). The paper
mock's §5 (`docs/paper-mock.md`) has the paragraph-by-paragraph plan for 5.1, 5.2 and 5.4.

## Another session owns §5.3 and run 133: do not touch them

Session 34 is kept open by the user to read **run 133** (`run/133_varied_observation.sh`, ~7 h, launched by the user):
it rebuilds the defenses learned from attacks (PV, ERDALT, adversarial training) from varied attack runs on training
malware, because session 34 found that PV's hole, and its 14/22 adaptive evasion, rest mostly on the attack harness
resetting the RNG to seed 0 before every run (GAMMA's section names are identical on every file). The plan for §5.3
is `docs/section-5.3-design.md`. In this session:

- Do not edit §5.3's text, `docs/section-5.3-design.md`, `run/133_*`, or anything under `artifacts/experiments/a_varied/`,
  `artifacts/experiments/a_pv/best/`, `artifacts/experiments/a1/advtrain/generated-seedperfile/`; do not start jobs
  that compete with run 133 for CPU or GPU without asking.
- `docs/status.md` and `PLAN.md` are shared with session 34: re-read them right before editing, and change only your
  own lines (your session's log entry, the 5.1-5.2 and 5.4 state).
- §5.4's draft still contains the old PV, ERDALT, adversarial-training and cost paragraphs; they belong to 5.3 and wait
  for run 133. Leave them where they are (or mark them, without rewriting them, if they are in the way).

## The tasks, in order

1. **The user's second round of feedback on 5.1-5.2** (revised version, commit 0069f56). Follow memory
   `review-comments-workflow`: answer the user's questions first in plain words, verify claims about cited work in
   `papers/`, give a numbered plan (one item per comment, one recommendation each, risks flagged), wait for approval,
   implement, `make` and `make check` in `manuscript/`, read the rendered PDF, report per item. Log the user's raw
   reactions in `docs/writing-spec.md`. Use the `paper-prose` skill for any prose. Also open: the `% VERIFY` in 5.2
   (Severi et al. used EMBER 1.0: check that its hashed groups match EMBER 2024's section, imports, exports and
   entry-name groups; `papers/severi2021explanation.pdf`, Anderson and Roth's EMBER paper, thrember's code in
   `tests/reference/features.py`, which must never be edited).
2. **Block 4: §5.4 *What Robustness Costs*** (the subsection is labelled `sec:eval:detectors`; its title in the draft
   is still "Detectors the Threat Model Cannot Evade"), from the mock's 5.4 plan: the finding (robustness against every
   structural edit costs about four points of detection, 93.5% to 89.6% at 1% FPR on the sums, 87.2% on the features,
   with 0% evasion on files in the population; the adaptive search's largest score drop is exactly 0), where the cost
   lies per operation (import addition 2.1 points, the three header overwrites 1.4), the threat model's width
   (additions only 92.2%; header-field attacks then evade on 28%; the expert set 29.1%), beyond the guarantee (GAMMA's
   rebuilding injections evade no monotone row on files in the population: 0/56, 0/60), and the scope (population).
   The detector table is trimmed to the undefended rows, the monotone rows and the additions block; the baselines
   (PV, ERDALT, adversarial training) move to 5.3's audit table, which session 34 settles. Write in small blocks with
   the user's review after each (memory `draft-in-small-blocks`); `make` and `make check` after each.
3. Then, only if 5.3 is settled by then: §2's closing sentence and contribution 4 against the findings; shortening §4
   and §5 together (§4.3 first); PLAN.md step 4 (the next full simulated review).

## Facts from session 34 that touch 5.1, 5.2 and 5.4

- PLAN.md decision 10(c) compares the adaptive search on the undefended detector with the toolkit (51% against 53%)
  as "about as often". Run 127's header shows 14 of the toolkit's 27 evasions come only through GAMMA's LIEF
  relayouts, outside the threat model; the six in-catalogue toolkit attacks evade 13/49. Do not use the 51%/53%
  comparison in prose as evidence that the search is no stronger than the toolkit.
- Our own edits (catalogue_checks, 2,000 test files, re-extracted) lower 915 of the 1,070 features the derived table
  marks lowerable under the full threat model (`artifacts/experiments/a_coverage/report.json`): the table is fairly
  tight, which may help 5.4 (the cost is not mostly looseness). The 155 never lowered: 78 parser warnings, 67 strings.
- The draft's sentence "We run the attacks on the training malware" (in the PV paragraph) is false: PV was built from
  attacks on the pilot test malware. It belongs to 5.3; leave it to session 34.

## Constraints (from CLAUDE.md, the memory, and the user)

Claims say "on EMBER"; no timing of Proposition 1 against extraction (memory `no-timing-claims`); the detectors'
accuracy cost is a measurement, never "small" (memory `findings-not-defense-paper`); report each attack separately,
never a union (memory `report-attacks-separately`); ask before changing what a claim or statistic is for (memory
`dont-reframe-research-claims`); check `manuscript/main.aux` before naming a table, section or definition number, and
give its title alongside; exact numbers in the prose matter less than structure and argument at this stage; explain
plainly (memory `explain-plainly`). Jobs over ~10 minutes go to the user as `run/` scripts (the user launches them);
a new experiment gets a numbered `run/` script (check the highest number first: 133 is taken). Before committing:
`env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts`. Commit to `main` in logical pieces; do not
push. At the end, update `docs/status.md` (re-read it first; session 34 may have changed it) and write the next resume
prompt.
