# Resume prompt (writing track): the user's read of §4 and §5, continued at 4.2

Written 2026-11-24 (end of session 111; replaces session 109's prompt, archived as
`docs/archive/resume-prompt-writing-2026-11-24-s109.md`). Self-contained: read `CLAUDE.md` (loaded automatically) and
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

- **§4 *Instantiating the Framework*** (`_e_instances.tex`, 1,778 words; Appendix D, `_j2_ember.tex`). The user's read
  is done for the lead and 4.1 (session 111). The lead's PE background names headers, sections, the headers' *data
  directory* (locating the imports, the debug data, and the Authenticode signature), and the overlay. 4.1 is now titled
  *Extractor* (D.1 too), and introduces pefile as EMBER's parser before the overlay rule change. Remaining: 4.2
  *Threat Model*, 4.3 *Signature*, 4.4 *Population*.
- **§5 *Evaluation*** (`_f_evaluation.tex`, 4,406 words: lead 521, 5.1 746, 5.2 931, 5.3 1,318, 5.4 890; Appendix E,
  `_j3_attacks.tex`, 892): rebuilt in session 108 (`docs/evaluation-note.md`, decision 13), reviewed and cut in
  session 109. What it evaluates: a defender learns what edits do from reading the extractor, observed attacks, or
  trial; a detector built on each source is compared with one built from the derived table. A source fails by being
  unsound (it misses a direction: the detector is evaded) or over-cautious (it constrains features no edit moves:
  detection lost against the derived detector on the same features). 5.1 *Setup*; 5.2 *What Hand Analysis Misses*;
  5.3 *What Observed Edits Miss* (Table 4); 5.4 *What Robustness Costs*.
- The two ⚑ cut items of session 109 were not applied (leave-one-out shortened to one sentence; trial's closing turn).
  Do not propose them again unless the user raises them.

## 3. This session: continue the user's read at 4.2

The user reads one subsection at a time and gives feedback; Claude adjusts; then the next. Order: 4.2 *Threat Model*
(with Table 3), 4.3 *Signature*, 4.4 *Population* (with Appendix D's matching part where the user asks), then §5's
lead, 5.1-5.4 (and Appendix E's mirror). Per subsection:

1. Wait for the user's feedback; read the subsection in the `.tex` and the rendered PDF (`manuscript/main.pdf`) before
   answering.
2. Answer questions first; keep the user's numbering; diagnose before fixing. For each fix show the exact old/new text.
3. Apply what the user approves; `make`, `make check`, read the rendered text; commit the subsection on its own (e.g.,
   "Manuscript: §4.2, the user's read"); note in `docs/status.md` which subsections are done.

**Above all, apply each comment proportionally** (memory `feedback-proportionally`). Session 111 overcorrected three
times and the user said so plainly ("You overcorrected like crazy this session"):

- Told "table" alone is ambiguous, Claude renamed standard PE terms ("header entry", "debug entry"). Wrong: keep the
  standard names (section table, data directory, debug directory entry, certificate table entry); only a *bare*
  "table" meaning a PE structure needs a fix.
- Told colons were overused as transitions, Claude put in "for instance" twice. Then, told there were too many, it
  removed both, although one was fine.

The user's aim is varied rhetoric and sentence structure ("That makes it interesting and fun to read"), not the
absence of any one device. Judge each instance on its own merits and say why it is wrong before changing it; leave good
uses alone (the user praised the colon in "We also change one rule ...: it starts the overlay where ...").

Pending from session 111, for their turn:
- "for instance" already appears in 4.3 ("adding a section, for instance,") and 4.4 ("Appending to an incomplete file,
  for instance,"). Mention them only if the user's comments touch them.
- "section table" (4.3, 4.4, 5.2) is the standard name and stays.

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
  adversarial training is the full-training-set model, and 5.3 says its comparison uses full-training-set detectors
  without the entry write. The scale-up trains every row on one training set; then rewrite that comparison against the
  table's row.
- **"The entry write's share"**: the debug entry's 0.6 and "the certificate entry for the rest" are not strictly
  additive (`% NOTE`).
- **Terms**: §4.4's "complete" is not 5.1's "held in full"; §4's "signature" (the framework's) and code signing
  (Authenticode) share a word in §4.3; §5 says "Authenticode signature" or "code signing" for the latter.
- **§2's closing sentence** ("§5 uses them to attack malware detectors and to build robust ones") is stale; left for the
  end-to-end pass with the introduction.

## 5. Also open (raise only when the work touches it)

- The rebuttal's number-free fixes R4, R5, R15, R21 (`docs/reviews/2026-11-12-body/rebuttal/triage.md`).
- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`), the closest work; an experimental comparison is the
  user's call (a candidate added defense: a row in Table 4 and Table 9, a paragraph in E.2).
- Giri et al.'s author names in `main.bib` (`giri2026towards`): check.
- `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history (Closure is Lemma 3 now).
- Not in this round: abstract, introduction, discussion, ethics, open science.

## 6. How the user works (sessions 106-111)

- Early in a section's construction the user cannot answer lists of design questions: weigh the options and decide,
  record what was weighed, report the decisions. Still ask about claims, compute, and anything that reverses an earlier
  decision of the user's.
- Prose: diagnosis first; exact old/new text; read the rendered PDF afterwards. Explain plainly; no internal IDs in the
  paper. In cuts the user rejects ⚑ items (content removed) and accepts redundancy cuts.
- In this read the user's comments are about flow and naming. Change only the instances a comment fits; when unsure
  whether an instance is meant, ask or propose it separately rather than sweeping.

## 7. At the end

After editing: `make` and `make check` in `manuscript/`; `texcount -1` per changed file; after moving floats, check that
every table appears in the PDF (`pdftotext main.pdf - | grep -o "^Table [0-9]*"`). Add a session entry to
`docs/status.md` (top of *Current state*), log the user's reactions raw in `docs/writing-spec.md`, and commit the
manuscript and the docs in logical pieces. Archive this prompt under `docs/archive/` (list it in `docs/README.md`), then
write the next resume prompt into this file, self-contained.
