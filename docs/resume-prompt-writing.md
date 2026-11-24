# Resume prompt (writing track): the user's read of §4 and §5, subsection by subsection

Written 2026-11-24 (end of session 109; replaces session 108's prompt, archived as
`docs/archive/resume-prompt-writing-2026-11-24-s108.md`). Self-contained: read `CLAUDE.md` (loaded automatically) and
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

## 2. Where the sections stand

- **§4 *Instantiating the Framework*** (`_e_instances.tex`, 1,792 words; Appendix D, `_j2_ember.tex`): reviewed and cut
  in session 107 (the user rejected the five ⚑ cut items).
- **§5 *Evaluation*** (`_f_evaluation.tex`, 4,406 words: lead 521, 5.1 746, 5.2 931, 5.3 1,318, 5.4 890; Appendix E,
  `_j3_attacks.tex`, 892): rebuilt in session 108 (`docs/evaluation-note.md`, decision 13), reviewed and cut in
  session 109. What it evaluates: a defender learns what edits do from reading the extractor, observed attacks, or
  trial; a detector built on each source is compared with one built from the derived table. A source fails by being
  unsound (it misses a direction: the detector is evaded) or over-cautious (it constrains features no edit moves:
  detection lost against the derived detector on the same features). The lead says both, and that the derived table
  predicts where each other detector is open. 5.1 *Setup*; 5.2 *What Hand Analysis Misses* (our hand table, the expert
  set, Severi et al.); 5.3 *What Observed Edits Miss* (Table 4, every detector grouped by source; the material, what
  the attacks reveal, *PV's hole*, *What PV pays in detection*, *ERDALT*, *Holding one attack out*, *Adversarial
  training* with iterated, *Trial*); 5.4 *What Robustness Costs* (the price, where the guarantee holds, the entry
  write's share, where the rest lies, the width of the threat model, beyond the guarantee).
- The two ⚑ cut items of session 109 were not applied (leave-one-out shortened to one sentence; trial's closing turn
  "Trial answers for the edits and contents it tries; the derived table answers for the threat model."). Do not
  propose them again unless the user raises them.

## 3. This session: the user reads §4, then §5, one subsection at a time

Decided at the end of session 109 (the user): "I'll begin reading starting with section 4. I'll provide feedback on a
subsection-by-subsection basis. You'll make adjustments and we'll move to the next subsection." No humanizer pass
(Claude recommended against it: the reviews found few of its patterns, and rule-driven rewriting has harmed the user's
register before).

Order: §4's lead, 4.1 *EMBER as a Sum-then-Readout Extractor*, 4.2 *Threat Model*, 4.3 *Signature*, 4.4 *Population*
(with Appendix D's matching part where the user asks), then §5's lead, 5.1-5.4 (and Appendix E's mirror). Per
subsection:

1. Wait for the user's feedback on the subsection; read it in the `.tex` and the rendered PDF
   (`manuscript/main.pdf`) before answering.
2. Answer questions first; keep the user's numbering of comments; diagnose before fixing (memory: review-comments
   workflow). For each fix show the exact old/new text.
3. Apply what the user approves (in one pass when they say so); `make`, `make check`, read the rendered text for
   slips; commit the subsection's changes on their own (e.g., "Manuscript: §4.2, the user's read"); then move to the
   next subsection.
4. Note in `docs/status.md` which subsections are done, so a session that ends mid-way resumes at the right place.

Do not change one section on the strength of another section's stale content (§2's closing sentence, the
introduction, and the discussion wait for the end-to-end pass). A fix in §4 that a §5 passage depends on: say so and
check the §5 passage when its turn comes.

## 4. Open items in §5 (raise when the work touches them)

- **"24 of the 28 malware"** (5.4 *Where the guarantee holds*) does not match Table 4's 39 and 40 detected, though 5.1's
  evaluation set holds only files of at most 4 MB (`% OPEN` comment); recount at the scale-up or explain the 28.
- **Hand-table detector not in the scale-up** (5.2 *What the error costs*, `% SCALE-UP GAP`): next round or keep the
  pilot result; the user decides.
- **The *shifts* threat model** is used nowhere in §5; deferred until a *shifts* detector is implemented and run. Do not
  change §4 for it.
- **The sample-read sentence** at the end of 5.1's *Checking the computation* and §4.3's last sentence are false at
  scale (the 20,000 training files add 98 directions): rewrite both to the held-out check with the user once the files
  behind the new moves are known (`% OPEN`).
- **Blue predictions**: iterated adversarial training (row and sentence), trial's AUC, 0.1% and toolkit cells, the
  monotone rows' toolkit and MAB-Malware cells, "about 1.76 million", "about 80,000", "no tree of any monotone detector
  violates them". ERDALT's row is the pilot's (AUC .883; the rescaled scale-up model reached .981).
- **Mixed pilot models**: Table 4's unconstrained, PV, ERDALT, expert set and monotone rows are 10% subsample models;
  adversarial training is the full-training-set model, and 5.3 now says its comparison uses full-training-set detectors
  without the entry write. The scale-up trains every row on one training set; then rewrite that comparison against the
  table's row.
- **"The entry write's share"**: the debug entry's 0.6 and "the certificate entry for the rest" are not strictly
  additive (`% NOTE`).
- **Terms**: §4.4's "complete" is not 5.1's "held in full"; §4's "signature" (the framework's) and code signing
  (Authenticode) share a word in §4.3; §5 now says "Authenticode signature" or "code signing" for the latter.
- **§2's closing sentence** ("§5 uses them to attack malware detectors and to build robust ones") is stale; left for the
  end-to-end pass with the introduction.

## 5. Also open (raise only when the work touches it)

- The rebuttal's number-free fixes R4, R5, R15, R21 (`docs/reviews/2026-11-12-body/rebuttal/triage.md`).
- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`), the closest work; an experimental comparison is the
  user's call (a candidate added defense: a row in Table 4 and Table 9, a paragraph in E.2).
- Giri et al.'s author names in `main.bib` (`giri2026towards`): check.
- `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history (Closure is Lemma 3 now).
- Not in this round: abstract, introduction, discussion, ethics, open science.

## 6. How the user works (sessions 106-109)

- Early in a section's construction the user cannot answer lists of design questions: weigh the options and decide,
  record what was weighed, report the decisions. Still ask about claims, compute, and anything that reverses an earlier
  decision of the user's.
- Prose: diagnosis first; fixes in one pass when approved; exact old/new text; read the rendered PDF afterwards.
  Explain plainly; no internal IDs in the paper. In cuts the user rejects ⚑ items (content removed) and accepts
  redundancy cuts.

## 7. At the end

After editing: `make` and `make check` in `manuscript/`; `texcount -1` per changed file; after moving floats, check that
every table appears in the PDF (`pdftotext main.pdf - | grep -o "^Table [0-9]*"`). Add a session entry to
`docs/status.md` (top of *Current state*), log the user's reactions raw in `docs/writing-spec.md`, and commit the
manuscript and the docs in logical pieces. Archive this prompt under `docs/archive/` (list it in `docs/README.md`), then
write the next resume prompt into this file, self-contained.
