# Resume: R18, read run 144 and take the user's decisions

**Closed in session 63 (2026-11-14):** run 144 read and audited, the three decisions taken (docs/evidence/r18-trial-competitor.md, Log). R18 has nothing open before the scale-up; this prompt is kept for the record.

Written in session 60 (2026-11-13, R18 track), updated in session 62 (2026-11-14), for the next R18 session. Self-contained: everything needed is below or
in the files it names. Two other tracks run in parallel: R7 (`docs/resume-prompt.md`) and the rebuttal
(`docs/resume-prompt-rebuttal.md`). Commit only the files you changed (`git add <paths>`, never `git add -A`).

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1). From those come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. §5 is three findings: what hand analysis
misses (5.2), what defenses learned from observed attacks miss (5.3), what robustness costs (5.4). Check
`manuscript/main.aux` before naming a section, table or theorem number, and give the title alongside.

**Read first:** `CLAUDE.md`, `docs/status.md` (skim), then **`docs/evidence/r18-trial-competitor.md`** (all of session
60's work: the mock, the trial table, the detectors, the smoke attack and its audit, the adversarial-training
recommendation) and the header of `run/144_trial_competitor.sh` (hypothesis, resources). The R18 entry of
`docs/reviews/2026-11-12-body/rebuttal/triage.md` has the open action lines.

## Where R18 stands

The review's point: §5 never builds the competitor a practitioner who knows the twelve operations would use, a
systematic trial over them. Session 60 built it in its strongest fair form with our own byte-level writers (catalogue
edits, a stronger probe of every in-place region, donor imports from benign training files), plus a variant that adds
the toolkit's LIEF-written outputs.

- Trial table vs derived (modeled features): no soundness conflict; 66 lowerable features trial never lowered (62
  string-pattern counts; the IAT entry, which the `imp` declaration lets an import adder move); 86 raise-only features
  it never moved (84 import buckets).
- Detectors, TPR at 1% / 0.1% FPR: derived `-loose` 83.4 / 65.1; trial 87.6 / 71.3; trial-toolkit 53.1 / 36.5.
- Smoke (real-scored beam, 100 candidates, 12 pilot malware): trial evaded 5/11, each by one signature-cloning edit,
  carried by `strings:regex_https://` (the certificate's URLs raise a count trial never moved, so left free);
  derived 0/2, score never falls; trial-toolkit 0/3 but its score fell. The hypothesis of session 58 (no new hole)
  failed.

## Done in session 62 (while run 144 ran; evidence note, section "While run 144 ran")

- The six non-string disagreements traced: parse_error, num_zero_size and SizeOfUninitializedData are trial's blind
  spots (derived right); the two import/IAT *addresses* are declared too broadly (`imp` `BOTH`, they can only rise),
  but run 145 shows freeing them as monotone gains nothing (83.2 / 66.3 vs 83.4 / 65.1), so trial's four-point edge
  rests on really lowerable features. Narrowing the declaration is an R7 proposal that changes no number.
- `docs/evidence/r18-a1_adaptive-save_rows.patch`: the `--save_rows` option adversarial training needs, tested on a
  copy, not applied (R7-owned). Training malware needs no code (`--pilot_files` with a training list, `--db .../tr`).
- `scripts/trial_audit.py`: the audit, tested (reproduces the smoke evasion exactly).
- Run 144 started 2026-11-14 10:05 with NUM_WORKERS=24; 51/103 adaptive tasks after 12 min.

## What waits

1. **Run 144** (the user runs it; ~3 h at 16 workers): the real-scored beam (2,000 candidates) and MAB-Malware against
   trial, trial-toolkit and the derived detector. Read it against the hypothesis in its header: trial evaded on 40-60%,
   nearly all by `ent`; derived 0 with its score never falling; trial-toolkit evaded on a few files; MAB-Malware (no
   signature cloning) few or none. Audit every evasion before any reading:
   `PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/trial_audit.py` (all evaded rows; `--defense` to filter; a `!!`
   line means the replay differs from the run). MAB-Malware's evasions are not covered by it: audit them from
   `$OUT/mab` the same way (feature rows before and after, `pred_contrib`): name the feature
   carrying it and whether trial marked it. Any evasion of the derived detector on a file in the population is a
   soundness bug, not a result.
2. **The user's decisions** (ask; do not decide):
   - the reading: proposed, §5's lead and §5.3 gain the trial row as measured evidence that trial answers only for the
     edits and contents it tries (and, from the toolkit variant, that trial through published tools cannot separate the
     operations from the tools' side effects); text after the scale-up (no manuscript edits now);
   - the trial row (trial and derived detectors, same protocol) in the scale-up;
   - iterated adversarial training at the scale-up: recommended in (two rounds, adaptive beam over the twelve
     operations on training malware, `ent` held out of the loop and MAB-Malware as the held-out attack; ~13-15 h at
     pilot scale, days at scale). It needs `--save_rows` in `scripts/a1_adaptive.py` (R7-owned): the patch is
     `docs/evidence/r18-a1_adaptive-save_rows.patch`; ask the user whether to apply it.
3. **Record** the decisions: R18's Decision cell and action lines in `triage.md`; the scale-up items in PLAN.md's next
   step 3 (session 60's paragraph there is a proposal); a line in `docs/status.md`'s log; the evidence note's log.

## Open details (small; raise only if they matter for the reading)

- The six non-strings disagreements (iat_size, iat_virtual_address, import_virtual_address, authenticode:parse_error,
  num_zero_size, SizeOfUninitializedData) were not traced through the derivation; `directions.csv`'s columns are the
  strict variant, not the `-pre` one the detector uses.
- The parser warning "Suspicious flags set for section" (13.9% of the trial detector's gain) is likely one no operation
  removes, so the derived table over-approximates it by the warnings rule (R12); freeing the warnings costs the derived
  detector nothing measurable (83.0 / 66.2).
- The catalogue edits behind the trial table are on test files (the 2,000-file explanation set and the pilot), as is
  the derivation's vocabulary; the donors are training files.

## Constraints

- **No manuscript edits** in these sessions. The R7 track owns §4.3.1, §4.4, §5.1's setup, §5.4, Table 5 and
  `catalogue.py`, `a_directions.py`, `a1_adaptive.py`, `catalogue_checks.py`: read them, do not edit them.
- Pilot scale, one seed. Jobs over ~10 minutes (from the slowest case) go to the user as `run/` scripts (check `ls run/`
  for the next free number right before writing one; `NUM_WORKERS="${NUM_WORKERS:-16}"`, one argument per line, an
  `echo` naming each step's log).
- §5 is findings, not a defense paper; no timing or effort claims; hypothesis before every run, failed checks reported
  as such. Explain plainly.
