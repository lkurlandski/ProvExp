# Resume prompt (writing track): §4 *Instantiating the Framework*, then the methodology changes of sessions 102-105

Written 2026-11-23 (end of session 105; replaces session 99's prompt, which is archived as
`docs/archive/resume-prompt-writing-2026-11-19-s99.md`). Read `CLAUDE.md` and this prompt. Then read all of §4
(`manuscript/_e_instances.tex`) and Appendix D *The EMBER Instance* (`manuscript/_j2_ember.tex`). Read §3
(`_d_framework.tex`) only where §4 depends on a definition or result, and §5 (`_f_evaluation.tex`) only at the
passages part 2 names. Run on Opus. Use no subagents unless the user asks.

**The scale-up's full rerun is running on tigris** (submitted 2026-11-23, jobs 1260382-1260399; about a day). Nothing
here waits for it: this track changes structure, argument and prose, not numbers. Exact numbers in the prose are of
little concern (CLAUDE.md): leave the pilot values and the old round's values where they are; the experiments track
replaces them when the new round is read (`docs/resume-prompt-experiments.md`).

## Where the writing stands

- **§3 is done for this round** (sessions 96-99): 3,312 words (target 3,000-3,250; the user accepted the overshoot).
  Appendix C *Proofs for the Framework* holds proofs only: every definition and condition a stated result needs is in
  the body, every lemma is stated in the body with its proof in the appendix. Table 7 and *Hashed keys* are switched
  off in an `\iffalse` block in `_j_proofs.tex`; leave them there.
- **§4's structure**: *EMBER and PE Files*, *EMBER as a Sum-then-Readout Extractor*, *Threat Model*, *Population*.
  The last carries the closure check §3.4 points to ("Closure can be checked directly ... as Section 4.4 does"); keep
  them consistent. Paper numbers (sections, tables) come from the compiled PDF: run `make` in `manuscript/` first,
  then check `manuscript/main.aux` before naming one, and give the title alongside.
- What the user said about drafts is in `docs/writing-spec.md` (session 99's entry is the newest); read it as
  evidence of taste, not as rules. The paper-prose skill is not used. A past over-compression of §6 was called "one of
  the worst things I have ever seen you write": a cut or changed passage must still read smoothly and keep the right
  emphasis.

## The task, in order

### 1. Humanistic review of §4 (the user's order, session 99)

Run the `humanistic-paper-review` skill on `_e_instances.tex` (diagnosis only, ranked findings with exact quotes).
Present the findings and get the user's verdicts before changing any text. Fix one finding at a time.

### 2. The methodology changes of sessions 102-105 into §4, §5 and Appendix D

These are decided (`docs/scaleup-protocol.md`, items (18)-(22)) and number-free. Propose each change as exact old/new
text with where it goes and get the user's verdict before applying it. Do it after the review's fixes to the same
passages, so that one edit does not undo another; where a review finding and a change touch the same sentence, say so
and let the user order them.

- **A fourteenth operation, header growth** (`hgr`, a shift; session 102). §4's threat model says "thirteen
  operations in all" (`_e_instances.tex`, around line 75) and the operations table (`tab:instances:catalogue`) lists
  thirteen: header growth inserts a gap at the end of the headers so that new section headers fit, and so belongs with
  the insertions. Check every count of operations in §4, §5 and Appendix D.
- **A fifth layout clause in the population** (session 102): the section table ends within the headers. §4's
  *Population* defines a plain layout (around line 159); add the clause in the same register as the others, without
  PE minutiae beyond what the reader needs.
- **GAMMA through our writers** (session 103): GAMMA's search is unchanged, but its sections and imports are written
  by our own byte-level writers, not by the LIEF library's rebuild; on a file whose headers lack room, the headers are
  grown first (so the output lies in the shift threat model), and where no growth makes room the attack is not
  applicable. **This changes the substance of §5's *Beyond the guarantee* paragraph** (`_f_evaluation.tex`, around
  lines 491-505), which is built on GAMMA "going through a library that rebuilds the file's layout, which no operation
  does": that is no longer true of our runs. Do not rewrite it alone: lay out the options with the user (e.g. keep
  MAB-Malware's own way of writing as the only off-model case; mention the LIEF rebuild as what the published tool
  does and why we replaced it; or wait for the new round's numbers) and let the user decide.
- **The validity rule by sets** (session 104): an output counts only if pefile and LIEF both read it and neither lost
  a section, imported DLL or imported function the original had. If the paper describes the rule by counts, change it
  to "lost none of the sections, DLLs and functions it had".
- **The attack budget and the size rule** (session 105, item (22)): §5's *Attacks* paragraph (around lines 53-57)
  says an attack may add "at most 5% of the file or 512 KB, whichever is larger" and that the toolkit runs "with 100
  queries per file, the low budget". Both change: every attack's output counts only if it is at most 4 MB, the files
  the study concerns (state it as the scope of the study, not as a budget we chose); the toolkit runs at the GAMMA
  paper's budget (about 500 queries, 75 donors; Demetrio et al., `demetrio2021functionality`). §4's threat model says
  content is "chosen by the attacker within a byte budget" (around line 77); reword consistently. Also check Appendix
  D (around lines 200-203).
- **The toolkit's framing** (session 105): the byte-level toolkit attacks (DOS extension, content shift, padding,
  format exploit, header fields) were designed for byte-level models such as MalConv and barely move a feature-based
  GBDT; we checked this with a positive control (against secml-malware's pretrained MalConv the same code and budget
  evade 5-16 of 20 files; record: `docs/scaleup-protocol.md` item (22)). In this round they move to an appendix and
  GAMMA's import attack carries the toolkit in §5; they are dropped before the final submission. One sentence in §5
  where the toolkit is introduced, the per-attack detail in the appendix. The adaptive search and MAB-Malware carry the
  case that the attacker is capable.
- **Not to claim:** that we reproduce Zainab et al.'s 83% for MAB-Malware (their detector and malware differ; the gap
  is accepted, item (22) and the experiments prompt). If Appendix D compares the two rates, word it as a comparison
  of different setups.

### 3. Then cut §4 with the project skill `cut-to-length`

A word target for §4 is for the user to set (the mock's budget is in `docs/paper-mock.md`, about 1,000 words; §4 runs
well over it); ask. Cut after part 2, so the cut works on the final content.

### Open, raise when the work touches it

- **What Appendix D holds** is not settled. The §3 principle adapted would keep in the body what a reader needs to
  follow §4's claims and §5's experiments and leave PE bookkeeping (field-level detail, quirk patches, how each EMBER
  feature group maps to items) to the appendix. Body sentences are never moved to the appendix to save words (session
  97). Do not settle it alone.
- PE specifics are allowed in §4 where they serve the experiment, never in the framework; format minutiae turn
  reviewers off (CLAUDE.md).

## After this

**§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words; the user has not read it end to end): a humanistic review and
polish as for §3 and §4, once the new round's numbers are in (the experiments track). §2 comes later; its closing
sentence and contribution 4 of `docs/paper-mock.md` wait for the user's discussion of the motivation (the *C.6 note*
in `docs/status.md`'s session-80 entry). The rebuttal's number-free fixes R4, R5, R15, R21
(`docs/reviews/2026-11-12-body/rebuttal/triage.md`) are scheduled while the scale-up runs (PLAN.md, next steps); ask
the user whether to take them up after part 2. Not in this round: abstract, introduction, discussion, ethics, open
science.

## Also pending (small, ask when convenient)

- §3.4's title, *Sequences and Robust Detectors*, was taken "for now".
- `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history and stay as written (Closure is Lemma 3 now).
- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`) is the closest work; the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare experimentally is the user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- `make check` reports one overfull vertical box (1 pt, the last pages of Appendix D); fix it at the next edit there.

## At the end

After editing: `make` and `make check` in `manuscript/`; `texcount` per changed file. Add a short session-log entry
to `docs/status.md` (and strike the items of "For the writing track" that are done) and commit the manuscript and the
docs in logical pieces. Archive this prompt under `docs/archive/`, list it in `docs/README.md`, then write the next
resume prompt into this file, self-contained.
