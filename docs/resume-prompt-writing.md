# Resume prompt (writing track): review the rebuilt §5 *Evaluation* and Appendix E

Written 2026-11-23 (end of session 108; replaces session 107's prompt, archived as
`docs/archive/resume-prompt-writing-2026-11-23-s107.md`). Self-contained: read `CLAUDE.md` (loaded automatically) and
this prompt. Run on Opus. Use no subagents unless the user asks.

## 1. The project in brief

ProvExp is the user's dissertation research. Its subject is *sum-then-readout* feature extractors, the kind security
classifiers use: they find the pieces of the input (items), add up what each contributes (sums), and compute each
feature by a formula over a few totals (readouts). From the instrumented extractor the paper computes what an
attacker's edits do to the features: exactly for one edit (Proposition 1), as sound directions for a whole threat
model (Theorem 1, the *derived table*: for each feature, whether edits can raise it, lower it, both, or neither), and
from those, monotone detectors no edit in the threat model can evade (Corollary 1). PE malware with EMBER 2024 is the
instance. The paper is `manuscript/*.tex` (ACM CCS format; `make` and `make check` in `manuscript/`); §3 is the
framework, §4 instantiates it on EMBER, §5 evaluates. Every number is a pilot value until the scale-up's rerun (jobs
1260382-1260399, submitted 2026-11-23 on tigris) is read in the experiments track
(`docs/resume-prompt-experiments.md`); scale-up outputs live only on tigris. Blue `\synthetic{}` values are
predictions, each with a `% SYNTHETIC` comment naming the run that replaces it.

## 2. What session 108 did

The user asked for §5 to be brought up to date and then for a ground-up rethink of it, like §4's in session 106. The
plan, every decision and what was weighed: **`docs/evaluation-note.md`** (read it first; sections 1, 3 and 6);
standing record: `docs/decisions.md`, decision 13. In short:

- **What §5 evaluates.** A defender learns what an attacker's edits do to the features from one of three sources:
  reading the extractor (a hand analysis), observed attacks, or trial (applying edits and re-extracting). Each yields a
  detector. §5 compares them with the derived table by what the detectors built on them withstand. A source fails in
  one of two ways: *unsound* (it misses a direction, so the detector can be evaded) or *over-cautious* (it constrains
  features no edit moves, so detection is lost for nothing). The derived detector is sound, so its cost against the
  unconstrained detector is the price of soundness itself. This refines decision 10 (three findings, not a validation
  section, not a defense paper), which stands.
- **§3.4 merged into §3.3** (§3 now only measures edits): Proposition 2 (*Sequences of edits*) and Lemma 3 (*Closure*)
  close §3.3 *Sound Directions*; the definition "monotone with respect to D" and **Corollary 1 (*Robustness*) moved
  into §5's lead**, the yardstick for every source. Appendix C mirrors: C.3 *Robust Detectors* holds the corollary's
  proof.
- **§5 now** (4,647 words by texcount; check numbers in `manuscript/main.aux`):
  - *Lead*: the three sources; Gimenez et al.'s result and the definition; Corollary 1; why one wrong direction
    reopens evasion; one sentence per finding.
  - 5.1 *Setup*: *Files and detectors* (files held in full, below 4 MB; one training set of ~1.76M files; thresholds
    on the validation split; the evaluation set of 1,000 + 1,000 test files), *Attacks* (the validity rule: at most
    4 MB, pefile and LIEF both read it; toolkit at the GAMMA paper's budget; the adaptive attack extracts every
    candidate, up to 5,000; MAB-Malware), *Checking results*.
  - 5.2 *What Hand Analysis Misses*: unchanged except the expert set's paragraph, which now holds both of its
    failures (lowerable under *full*; 29.1% against 92.2% detection under *additions*, moved from 5.4).
  - 5.3 *What Observed Edits Miss*: Table 4, the comparison table (every detector, grouped: unconstrained; read by
    hand; learned from observed edits; derived from the extractor; replaces the old Tables 4 and 5), then the defenses
    learned from attacks (the material: 10,000 training malware), what the attacks reveal, PV (rename hole; the DLL
    flag), ERDALT (rescaled), adversarial training and iterated adversarial training (new, blue), leave-one-out, and
    *Learning by trial* (new, from pilot run 144: 87.6% against 83.4% detection, evaded on 26/44 through features no
    tried edit moved, mostly URL-like string counts; the toolkit-widened trial evaded on 13/20 through import
    buckets).
  - 5.4 *What Robustness Costs*: the price, where the guarantee holds (escapes), where the cost lies (now cites
    Table 11), the width of the threat model (the restored closing sentence), beyond the guarantee.
- **Appendix E mirrors §5**: E.1 *Setup* (toolkit, adaptive attack with header growth, MAB-Malware, Table 9 per
  attack, regrouped like Table 4), E.2 *What Observed Edits Miss* (PV's rule, ERDALT with each rescaling stated,
  adversarial and iterated training, the trial table, leave-one-out Table 10), E.3 *What Robustness Costs* (the
  per-operation price list, new Table 11; measured before the entry write). 976 words.
- **The rule for added defenses** (the user: more defenses will very likely be benchmarked, body or appendix
  undecided): a row in Table 4 and Table 9, a paragraph in E.2 on how it was built and ported; body prose only if it
  shows a failure the existing rows do not.
- Commits 4a11d53 (manuscript), 2209cae (note); docs in a third commit.

## 3. This session

1. **Read** §5 (`manuscript/_f_evaluation.tex`) and Appendix E (`_j3_attacks.tex`) in full, rendered as well
   (`pdftotext` or page images of `manuscript/main.pdf`), and the note's sections 1 and 6. Read §4
   (`_e_instances.tex`) and §3 only where §5 cites them.
2. **A humanistic review of §5 and Appendix E** (`anthropic-skills:humanistic-paper-review` skill): findings ranked
   most to least important, each with exact quotes, numbered, diagnosis only. Session 108 wrote most of 5.3 and 5.4's
   new prose and the lead in one pass, unreviewed: expect seams. Look in particular at: whether the lead and the
   subsection leads make clear what is evaluated (the user's main worry this session: "its not clear what we're
   evaluating"); whether the two failure modes are visible in the prose and in Table 4 (they are named in the note,
   barely in the text: the lead says "what that source misses"); the lead's length (it now holds a definition and a
   corollary); 5.3's length and order (eight run-in paragraphs; trial last); the comparison table's readability; the
   seam where 5.4 no longer restates the corollary.
3. Present the findings; get the user's verdicts; the user often approves all and asks for the fixes in one pass, by
   Claude's judgement. Show old/new text for each applied fix.
4. Later, not before the review is settled: a cut with `cut-to-length` (mock budget 3,200; drafting allowance 50-75%
   over, so up to ~5,600 is acceptable for now; the user rejected every ⚑ item in §4's cut).

## 4. Open items in §5 (raise when the work touches them)

- **Hand-table detector not in the scale-up**: §5.2 *What the error costs* (pilot: score lowered on 10 of 29 files,
  none crossing) has no scale-up step (`% SCALE-UP GAP` comment). The user decides: next round or keep the pilot result
  (memory: every paper number gets a scale-up step). On the next-round list as a candidate.
- **The *shifts* threat model** (§4.2, Table 2) is used nowhere in §5; deferred by the user until a *shifts* detector is
  implemented and run (next-round candidate). Do not fold it into *full* and do not change §4 for it.
- **The sample-read sentence** at the end of 5.1's *Checking results* ("the table derived from 100 of the files is also
  the same as the one derived from all 2,000") is false at scale (the 20,000 training files add 98 directions); the
  same in §4.3's last sentence. Rewrite both to the held-out check with the user, once the files behind the new moves
  are known (PLAN.md, open items). An `% OPEN` comment marks it.
- **Blue predictions**: iterated adversarial training's row and its sentence in 5.3 (no pilot run; predicted evaded
  through signature cloning, the operation held out of its rounds); trial's AUC, 0.1% detection and toolkit cells; the
  monotone rows' toolkit and MAB-Malware cells; "about 1.76 million"; "about 80,000" outputs; "no tree of any monotone
  detector violates them". ERDALT's row is the pilot's (AUC .883); the rescaled scale-up model reached .981.
- **Mixed pilot models** in Table 4: unconstrained, PV, ERDALT, the expert set and the monotone rows are 10% subsample
  models; adversarial training is the full-training-set model (comment beside the table). The scale-up trains every
  row on one training set; until then 5.3's "leaves its detection unchanged" compares adversarial training with a
  detector not in the table.
- **Terms**: §4.4's "complete" (headers point within the file) is not 5.1's "held in full" (below 4 MB); keep them apart.
  §4.4's 94% and 5.4's "all but 1.5% of the benign test files" count different populations (both recounted at scale).
- **Unused label** `sec:instances:sums` on a `\paragraph` in Appendix D.1; 5.4 now cites §4.1 (`sec:instances:record`)
  for the sums.
- **§2's closing sentence** ("§5 uses them to attack malware detectors and to build robust ones") no longer matches
  §5: the user leaves it to the end-to-end pass with the introduction. Do not change it now. Do not change one section
  on the strength of another section's stale content.
- The title stays *Evaluation* (decision 13: the lead and the subsection titles carry the question).

## 5. Also open (raise only when the work touches it)

- The rebuttal's number-free fixes R4, R5, R15, R21 (`docs/reviews/2026-11-12-body/rebuttal/triage.md`): ask whether
  to take them up.
- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`), the closest work; reading at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`; an experimental comparison is the user's call (a candidate
  added defense under the rule above).
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed; check.
- `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history (Closure is Lemma 3 now).
- Not in this round: abstract, introduction, discussion, ethics, open science.

## 6. How the user works (sessions 106-108)

- Early in a section's construction the user cannot answer lists of design questions: weigh the options and decide,
  record what was weighed, report the decisions (memory: decide early design questions). Still ask about claims,
  compute, and anything that reverses an earlier decision of the user's.
- Prose: diagnosis first with the user's verdicts; fixes in one pass when approved; exact old/new text; read the
  rendered PDF for slips afterwards. Explain plainly; no internal IDs in the paper.
- Proposals must show understanding of the section: the user rejected title options that named only part of what §5
  does.

## 7. At the end

After editing: `make` and `make check` in `manuscript/`; `texcount -1 -sum` per changed file; after moving floats,
check that every table appears in the PDF (`pdftotext main.pdf - | grep -o "^Table [0-9]*"`). Add a session entry to
`docs/status.md` (top of *Current state*), log the user's reactions raw in `docs/writing-spec.md`, update
`docs/evaluation-note.md` if a decision changes, and commit the manuscript and the docs in logical pieces. Archive this
prompt under `docs/archive/` (list it in `docs/README.md`), then write the next resume prompt into this file,
self-contained.
