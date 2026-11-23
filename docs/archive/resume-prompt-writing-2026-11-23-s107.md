# Resume prompt (writing track): bring §5 *Evaluation* up to date

Written 2026-11-23 (end of session 107; replaces session 106's prompt, archived as
`docs/archive/resume-prompt-writing-2026-11-23-s106.md`). Read `CLAUDE.md` and this prompt. Then read §5
(`manuscript/_f_evaluation.tex`, ~4,000 words; the user has not read it end to end) and Appendix E *Attacks and
Defenses* (`_j3_attacks.tex`). Read §4 (`_e_instances.tex`) for the terms §5 uses, and §3 (`_d_framework.tex`) only
where §5 cites a definition or result. Check numbers in `manuscript/main.aux` after `make`, and give titles with them.
Run on Opus. Use no subagents unless the user asks.

## Where things stand

- **§4 *Instantiating the Framework* is done for this round** (sessions 106-107): restructured as the bridge from §3
  to §5, reviewed twice, cut to 1,792 words (user's range: 1,500 fine, 1,700 acceptable; the user rejected the cut's five
  ⚑ items, those that change what a reader is told, so do not propose them again). Its subsections: 4.1 *EMBER
  as a Sum-then-Readout Extractor* (items, sums, the item table, reading the sums directly, the 88 warnings dropped,
  2,480 features exact, the overlay rule), 4.2 *Threat Model* (fourteen operations, the entry write and header growth,
  three nested models *additions* / *shifts* / *full*, Table 2), 4.3 *Signature* (declared changes, the part read from
  a sample, declined edits, what is proven and what is checked), 4.4 *Population* (complete files with a plain layout;
  the debug data and the signature exempt; closure checked). Appendix D mirrors it (D.1-D.3).
- **The user said §5 is "quite out of date"** and is to be updated in this session. Session 106 already wrote the
  decided methodology of sessions 102-105 into §5 (header growth, the 4 MB scope, the GAMMA paper's budget, the
  byte-level toolkit attacks to Appendix E). What else "out of date" covers was not said: **start by asking the user**
  what the update includes, with your reading of what is stale as options. Candidates:
  1. The new round's numbers. The scale-up's full rerun was submitted on tigris on 2026-11-23 (jobs 1260382-1260399);
     whether it has been read is in `docs/status.md` and `docs/resume-prompt-experiments.md`. Scale-up outputs live
     only on tigris (memory: scale-up sessions on tigris). Blue `\synthetic{}` values and `% SYNTHETIC` comments mark
     what the runs replace.
  2. The refactor the user is considering: §3.4's robust detectors (the monotone detectors, Corollary 1) moved into
     §5, and §3.3 and §3.4 merged, so that §3 is only about measuring edits. §4 does not depend on §3.4's detectors;
     keep it that way.
  3. Terms and cross-references that §4 changed (below).
- Then, once the content is current: a humanistic review of §5 (`humanistic-paper-review` skill; findings ranked, with
  exact quotes, numbered; the user's verdicts before changing text), and later a cut.

## Open items carried from §4's review (session 107), all touching §5

- **The stray fragment at the end of §5.4's additions paragraph** (`_f_evaluation.tex`, around line 480): the sentence
  "A defender chooses the threat model, and with it which edits the detector withstands and what that costs in
  detection." begins at the end of a `% MEASURED` comment line, so only "model, and with it ..." renders. Restore the
  sentence (move its start out of the comment) or delete it; ask.
- **The *shifts* threat model** is defined in §4.2 and Table 2 but used nowhere else in the paper. The user kept it
  because §5 is out of date; if the updated §5 still does not use it, ask whether to fold the insertions into *full*.
- **Cross-references from §5 into Appendix D are coarse**: §5.1's checks cite "Appendix D" for what is Table 9 (in D.2
  *Signature*), and §5.4 cites "Appendix D" for the re-encodings over sums (the last paragraph of D.1). §4.1 now
  introduces reading the sums; §5.4 can point there too. The label `sec:instances:sums` sits on a `\paragraph` in D.1
  and is unused. Also: §4.1 says a detector "reads the sums directly", while D.1's re-encodings include splitting the
  signed section-name buckets; keep the naming consistent if §5 describes the sums detector.
- **"Complete"**: §4.4 now says incomplete files are ones "our copy holds in full" but whose headers point past their
  end; §5.1 says "only the files it holds in full". Keep the two senses apart in §5's wording.
- **Population figures**: §4.4's 94% (population before the entry write) and §5.4's "all but 1.5% of the benign test
  files" (the widened population) count different populations; the scale-up recounts both (PROTOCOL comment in §4.4).

## Also open (raise when the work touches it)

- §3.4's title, *Sequences and Robust Detectors*, was taken "for now" (may change with the refactor).
- The rebuttal's number-free fixes R4, R5, R15, R21 (`docs/reviews/2026-11-12-body/rebuttal/triage.md`): ask the user
  whether to take them up.
- The appendices: the user agreed to Appendix D/E's split "for now" and wants to talk about them more later.
- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`) is the closest work; the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare experimentally is the user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history and stay as written (Closure is Lemma 3 now).
- Not in this round: abstract, introduction, discussion, ethics, open science.

## How the user works on prose (from sessions 106-107)

Diagnosis first, with the user's verdicts; the user often approves all findings and asks for the fixes in one pass,
by Claude's judgement (ask which way). Cuts with `cut-to-length`: exact old/new text, measured savings, least to most
disruptive, ⚑ on what changes what a reader is told (in session 107 the user rejected every ⚑ item); then read the rendered PDF for slips (session 107 found three).
Never change one section on the strength of another section's stale content.

## At the end

After editing: `make` and `make check` in `manuscript/`; `texcount` per changed file. After moving floats, check that
every table appears in the PDF (a float placed last in an appendix was silently lost in session 106). Add a short
session-log entry to `docs/status.md`, log the user's reactions raw in `docs/writing-spec.md`, and commit the
manuscript and the docs in logical pieces. Archive this prompt under `docs/archive/`, list it in `docs/README.md`, then
write the next resume prompt into this file, self-contained.
