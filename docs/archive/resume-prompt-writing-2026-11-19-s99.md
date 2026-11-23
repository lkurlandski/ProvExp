# Resume prompt (writing track): §4 *Instantiating the Framework* with Appendix D

Written 2026-11-19 (end of session 99). Nothing here depends on the scale-up on tigris. Read `CLAUDE.md` and this
prompt. Then read all of §4 (`manuscript/_e_instances.tex`, 1,833 words by `texcount -brief`) and Appendix D *The
EMBER Instance* (`manuscript/_j2_ember.tex`, 1,341 words). Read §3 (`_d_framework.tex`) only where §4 depends on a
definition or result. Run on Opus. Use no subagents unless the user asks.

## Where the writing stands

- **§3 is done for this round** (sessions 96-99): 3,312 words (lead 116, §3.1 1,029, §3.2 579, §3.3 1,064, §3.4 524).
  The target was 3,000-3,250; the user accepted the overshoot. Appendix C *Proofs for the Framework* holds proofs
  only (session 98): every definition and every condition a stated result needs is in the body, every lemma is stated
  in the body with its proof in the appendix. Table 7 and *Hashed keys* are switched off in an `\iffalse` block in
  `_j_proofs.tex`; leave them there.
- **§4's structure** (check numbers against `manuscript/main.aux` before naming them): §4.1 *EMBER and PE Files*,
  §4.2 *EMBER as a Sum-then-Readout Extractor*, §4.3 *Threat Model*, §4.4 *Population*. §4.4 carries the closure
  check that §3.4 points to ("Closure can be checked directly ... as Section 4.4 does"); keep them consistent.
- What the user said about drafts is in `docs/writing-spec.md` (session 99's entry is the newest); read it as
  evidence of taste, not as rules. The paper-prose skill is not used. A past over-compression of §6 was called "one of
  the worst things I have ever seen you write": a cut passage must still read smoothly and keep the right emphasis.

## The task

The user's order (end of session 99): **first the humanistic review of §4, then the `cut-to-length` skill.** The user
decides how the two skills are used together; do not propose combining them.

1. **Humanistic review of §4**: run the `humanistic-paper-review` skill on `_e_instances.tex` (diagnosis only, ranked
   findings with exact quotes). Present the findings and get the user's verdicts before changing any text.
2. **Then cut §4 with the project skill `cut-to-length`.** A word target for §4 is for the user to set (the mock's
   budget is in `docs/paper-mock.md`); ask.
3. **What Appendix D holds** is not settled. It is not a proofs appendix; the §3 principle adapted would keep in the
   body what a reader needs to follow §4's claims and §5's experiments and leave PE bookkeeping (field-level detail,
   quirk patches, how each EMBER feature group maps to items) to the appendix. Body sentences are never moved to the
   appendix to save words (session 97). Raise it with the user when the review or the cut touches it; do not settle
   it alone.

PE specifics are allowed in §4 where they serve the experiment, never in the framework; format minutiae turn
reviewers off (CLAUDE.md).

## Also pending (small, ask when convenient)

- §3.4's title, *Sequences and Robust Detectors*, was taken "for now".
- `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history and stay as written (Closure is Lemma 3 now).

## After this

**§5 Evaluation** (`_f_evaluation.tex`, ~4,100 words; pilot numbers, do not sync them; the user has not read §5 end to
end). §2 comes later; its closing sentence and contribution 4 of `docs/paper-mock.md` wait for the user's discussion
of the motivation (the *C.6 note* in `docs/status.md`'s session-80 entry). Not in this round: abstract, introduction,
discussion, ethics, open science.

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`) is the closest work; the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare experimentally is the user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget is decided (session 105, protocol item (22)): an output counts only if it is at most 4 MB, for
  every attack; the toolkit runs at the GAMMA paper's budget. The number-free sentences this needs, and the toolkit's
  framing (the byte-level attacks to an appendix), are listed in `docs/status.md`, "For the writing track".

## At the end

Add a short session-log entry to `docs/status.md` and commit the docs. Archive this prompt under `docs/archive/`, then
write the next resume prompt into this file.
