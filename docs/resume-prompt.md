# Resume: R7 continued (if run 138 is done), or the next limitation from the review

Written at the end of session 48 (2026-11-12). Self-contained: everything needed to start is below or in the files it
names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware with the EMBER 2024 extractor is the instance. The paper is written
straight into `manuscript/*.tex`; check `manuscript/main.aux` before naming a number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` (decision 11; next steps 2-3), and
`docs/evidence/r7-population-escape.md` (the R7 record). The review itself: `docs/reviews/2026-11-12-body/meta-review.md`
(sections 1, 6 and 7 first; the four reviews only when an item needs them).

## Where things stand

- The full simulated review ran (A Weak accept, B Weak reject, C Weak reject, D Weak accept; risk register R1-R21).
  Session 48 checked the deciding verdicts and discussed **R7 only**: the guarantee covers the population, and the
  router sent every other file to the unconstrained detector, which the attacks evade about half the time.
- **Run 137 (escape audit):** one field write the loader ignores (certificate or debug entry past the end of the file,
  SizeOfImage raised by one alignment step) takes 150 of 150 population files out of the population.
- **Decision 11 (user):** no router; one monotone detector scores every file. The guarantee is proven on the
  population and measured outside it. Option 5 (widen the population for one clause) only if an escape breaks the
  monotone detectors.
- **Run 138** (`run/138_escape_pilot.sh`, ~5-6 h, launched by the user after session 48) tests it. The 50 pilot
  malware are escaped by the certificate write (step 1) and by the SizeOfImage write (step 2), then attacked by the
  beam search over all twelve operations with every candidate extracted (`a1_adaptive.py --score real`), against the
  unconstrained detector (the routed system's result) and both monotone detectors. Hypothesis in the script header and
  in the R7 record, §7. The paper is unchanged until the run is read.

## The task

**First, check run 138.** Look at `artifacts/logs/escape_pilot.log` and
`artifacts/experiments/escape_pilot/{cert_entry,image_size}/adaptive.json`.

**A. If run 138 is complete (both steps), continue R7.**
1. Read it against the hypothesis (monotone detectors evaded on 0-3 of about 40 escaped files each, largest score drop
   small; unconstrained about 40-50%). Report held or failed plainly, per detector and per escape, the count beside
   its denominator. Record the result in the run script's header and in the R7 record (§7 and the log).
2. If a monotone detector is evaded, find which side effect did it (the written files can be rebuilt from the `ops`
   column; compare the extraction before and after) and weigh option 5 for that clause, one recommendation.
3. If they hold, plan what decision 11 changes in the paper: §4.4's last paragraph (no routing), §5.4's *Where the
   guarantee holds* (the escape result; "such files ... stand out" removed; the population share as n/N), any mention
   of routing in §5.1 and Appendix D. Draft in small blocks with the user (`paper-prose` skill), or record the plan and
   leave the prose for after the scale-up if the user prefers. Then list what the scale-up needs for R7: the toolkit
   attacks on escaped files (their harness needs `--escape` support), the end-to-end "still detected out of all
   attacked" share per attack column, the population share of attacked malware with its denominator.
4. Then move on to B.

**B. If run 138 is not complete (or once A is done), choose the next limitation(s).** Triage the rest of the register
(meta-review §6), following memory `review-comments-workflow`: plain words, the reviewers' IDs (`B-W4`, ...) and the
R-numbers kept, one recommendation per item, small passes, approved items first. Start with what the register ranks
highest after R7: R1 (attacks below published strength; MAB-Malware; the adaptive attack never used header fields,
which `--score real` now fixes), R2 (premises tested, not proven: one paragraph of trusted parts with their checks; a
multi-byte probe of the locating record), R18 (learned baselines given less information: decision 6's revisit,
which the checklist asked for), R6 (§3's classical parts named; cheap). The batch of cheap writing fixes (meta-review
§8; Claude's list in session 48: §3's classical/new paragraph and the monoid hypothesis, §6's incremental-parsing
contrast and the certified defenses, the five uncited bib entries, the 100-query attribution to Gimenez et al.'s
released code, Appendix D's minima) can be offered for approval as one pass.

**A question to settle with the user in either case: scale first or widen first?** Should the existing experiments
run at larger scale first (more files, seeds 0-2, full splits: what R11 and R20 ask for), or should the set of
experiments widen first (the review's new ones: MAB-Malware, the escape attack, equal-information learned defenses, a
trial table, the adaptive search scoring by extraction), then scale everything once? Weigh it and give one
recommendation. Considerations: most reviewer verdicts turn on breadth (B, C and D's conditions are new experiments);
scaling twice costs compute twice and risks two protocols (R11); CLAUDE.md says research at pilot scale and scale only
when the user decides; but small denominators (PV on 9 files, the expert set on 8) are themselves a review risk (R20).
Record the answer in PLAN.md, next step 3.

## Constraints and settled points

- Explain plainly, no jargon; a recommendation rather than a menu. State a hypothesis before any run; report a failed
  check as such.
- No deadline talk; do not reopen settled decisions (`docs/reviews/process/checklist.md`, "Settled"; PLAN.md); ask
  before reframing what a claim or statistic is for.
- Never propose running modified samples in a sandbox, or obtaining the files over 4 MB. Loader behaviour is argued
  from documentation.
- Jobs over ~10 minutes go to the user as `run/` scripts (NUM_WORKERS, default 16).
- At the end of the session: update `docs/status.md`, PLAN.md and the R7 record; write the next resume prompt (archive
  this one under `docs/archive/` and index it in `docs/README.md`).
