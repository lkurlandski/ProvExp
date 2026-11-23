# Resume prompt (writing track): a fresh review of §4 *Instantiating the Framework*, then the cut

Written 2026-11-23 (end of session 106; replaces session 105's prompt, archived as
`docs/archive/resume-prompt-writing-2026-11-23-s105.md`). Read `CLAUDE.md` and this prompt. Then read all of §4
(`manuscript/_e_instances.tex`) and Appendix D *The EMBER Instance* (`manuscript/_j2_ember.tex`). Read §3
(`_d_framework.tex`) only where §4 depends on a definition or result, and §5 (`_f_evaluation.tex`) only where §4
points to it or where it uses §4's terms. Run on Opus. Use no subagents unless the user asks.

The scale-up's full rerun is running on tigris (jobs 1260382-1260399, submitted 2026-11-23). Nothing here waits for
it: exact numbers in the prose are of little concern (CLAUDE.md); leave the old round's values where they are.

## Where §4 stands (session 106)

Session 106 reviewed §4, wrote the decided methodology of sessions 102-105 into it, and then **restructured it with
the user** as the bridge from §3 (theory) to §5 (experiments). What §4 is for, agreed with the user: a reader reaching
§5 needs (1) the features: EMBER is a real, standard extractor that fits the framework except for the 88 warning
flags, which we drop; (2) the edits, by the names §5 uses (rename, add a section, import addition, append, the header
overwrites, the entry write; the additions and full threat models), and why they are there; (3) what is proven and
what is checked (declared changes, overwrites read from sample files, declined edits, closure checked); (4) where the
guarantee holds (the population: complete files with a plain layout).

The structure now (check numbers in `manuscript/main.aux` after `make`, and give titles with them):

- **Lead**: what an instance supplies (the extractor, a decision about features that do not fit, a threat model, a
  signature that covers it, the population), then the PE paragraph (what a PE file is; EMBER, its 2,568 features).
- **4.1 EMBER as a Sum-then-Readout Extractor**: items, sums, readouts; reading the sums directly (the sums detector
  of §5.4); the warnings dropped; the exact check (2,480 features); the overlay rule (kept in the body, user).
- **4.2 Threat Model**: the literature's operations; our union plus the entry write (signature copying, Kim et al.) and
  header growth, fourteen operations; the 4 MB scope; the three nested threat models; packing and code-level
  transformations excluded; Table 2 (the operations).
- **4.3 Signature**: two sources (declared, item tables of a sample), what rests on the sample, positions the parser
  reads (declined edits); the checks are in §5.1.
- **4.4 Population**: complete files with a plain layout, why, why Lemma 3 does not give closure, the closure check,
  the shares of files.
- **Appendix D** mirrors §4 (user): D.1 *EMBER as a Sum-then-Readout Extractor* (changes to EMBER, items, readouts,
  re-encodings), D.2 *Signature* (declared changes per operation, positions that locate items, the side-effect
  table), D.3 *Population* (the debug and signature exception, the five layout clauses). The threat model has no
  appendix counterpart. **Appendix E** *Attacks and Defenses* (`_j3_attacks.tex`, new) holds the toolkit, the
  adaptive attack, MAB-Malware, ERDALT, the per-attack and leave-one-out tables. The user agreed to the split "for
  now" and wants to talk about the appendices more later.
- The toolkit attacks are introduced in §5.1, no longer in §4 (they move to an appendix this round and are dropped
  before the final submission).

Length: §4 is 1,840 words by `texcount -1 -sum` (about 130 of them Table 2's cells, so about 1,710 of prose). The
user's range: **1,500 is fine, 1,700 acceptable, 2,000 too long**; be flexible, and allow about a hundred words over
per subsection while drafting.

**A refactor the user is considering**: moving §3.4's robust detectors (the monotone detectors, Corollary 1) into §5
and merging §3.3 and §3.4, so that §3 is only about measuring edits. Checked in session 106: §4 does not depend on
§3.4's detectors (it cites Proposition 2 and Lemma 3, which stay in §3). Keep it that way: no new reference from §4
to §3.4's detectors.

## The task, in order

### 1. A fresh humanistic review of §4 (the user's order, session 106)

Run the `humanistic-paper-review` skill on `_e_instances.tex` (diagnosis only, ranked findings with exact quotes).
Read it as the bridge described above: does each subsection deliver what §5 needs, in the order a reader needs it?
Include how Appendix D pairs with §4 (same titles; is D self-contained?) as a short part of the review. Present the
findings, keep their numbers in every reply, and get the user's verdicts before changing text. In session 106 the
user, once every finding was approved, asked for all fixes in one pass; ask which way they want it.

### 2. Then cut §4 with the project skill `cut-to-length`

Target as above (aim near 1,500; 1,700 is acceptable). Cut after the review's fixes, so the cut works on the final
content. Exact old/new text per item, measured savings, the user's verdict before applying. Body sentences are never
moved to the appendix to save words; the bookkeeping that belonged in Appendix D was moved in session 106's
restructuring, as whole groups. A past over-compression of §6 was called "one of the worst things I have ever seen
you write": a cut passage must still read smoothly and keep the right emphasis.

## Open, raise when the work touches it

- A stray fragment ends §5.4's *The width of the threat model*: "model, and with it which edits the detector
  withstands and what that costs in detection." (left from an earlier cut; not fixed in session 106). Offer to fix.
- §3.4's title, *Sequences and Robust Detectors*, was taken "for now" (and may change with the refactor above).
- `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history and stay as written (Closure is Lemma 3 now).
- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`) is the closest work; the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare experimentally is the user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.

## After this

**§5 Evaluation** (`_f_evaluation.tex`, ~4,000 words; the user has not read it end to end): a humanistic review and
polish once the new round's numbers are in (the experiments track), possibly after the §3/§5 refactor above. The
rebuttal's number-free fixes R4, R5, R15, R21 (`docs/reviews/2026-11-12-body/rebuttal/triage.md`): ask the user
whether to take them up. Not in this round: abstract, introduction, discussion, ethics, open science.

## At the end

After editing: `make` and `make check` in `manuscript/`; `texcount` per changed file. A float placed last in an
appendix was silently lost in session 106 (only an undefined reference showed it): after moving floats, check that
every table appears in the PDF. Add a short session-log entry to `docs/status.md` and commit the manuscript and the
docs in logical pieces. Archive this prompt under `docs/archive/`, list it in `docs/README.md`, then write the next
resume prompt into this file, self-contained.
