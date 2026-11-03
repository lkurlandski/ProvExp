# Resume: ProvExp (after 2026-11-03, session 7): read run/122, then a holistic stock-take vs the review

## Where things stand

Session 7 finished items 9 and 10 (the last tier-2 experiment items). All of tier 2 is now done; the manuscript's
empty sections are the one big remaining phase. Nothing is pushed.

1. **Item 9 (a detector on the hand table) is done (`run/121`, commit `29fc3a7`; `docs/direction-A-A1-design.md`,
   "Item 9").** The hand M_full detector (`seed-0-a-mfull-mono-qf`) is the derived model's counterpart -- same store,
   samples, and monotone/neutralize counts; they differ by exactly **two in-population features** (overlay_size,
   security_size), so no retrain. Re-ran the twelve-op search against it: **go/no-go (>=1 in-population evasion) NOT
   met, 0 evasions** (same as the derived model's 0). **But the difference is material to SOUNDNESS** (user's framing,
   "soundness, not outcome"): the search lowers the hand detector's score on 10 of 29 in-population files, always by a
   single add-section after the overlay (overlay_size hole), by up to **-1.57 logits in-population**, re-extracting
   exactly, where the derived detector is provably 0.0; no drop crosses the threshold (the detected malware sit far
   above it). Prose in `_f_evaluation.tex`; no Table 7 row (rate 0 for both). This is now a **§1/§6 data point**: the
   derivation catches a real unsoundness in the hand table that the hand table's own detector cannot see.
2. **Item 10 (the adversarial-training row) is scripted and handed to the user (`run/122`, commit `7e76952`).** A
   hand-off overnight job (~8-9 h), **built and smoke-tested, not run**: `train_classic.py --augment` (pure addition),
   `scripts/a_advtrain.py` (toolkit adversarial examples on **training** malware, 4 "seen" attacks x ADV_MALWARE=400),
   `run/122_adv_training.sh` (generate -> retrain unconstrained GBDT -> AUC/TPR + toolkit seen/held-out + adaptive as
   the union of both menus; reads `NUM_WORKERS`). The Table 7 row stays `\synthetic` until the user runs it and a
   session reads the output. Report honestly (expected ~20% adaptive, competitive with the unconstrained row, not the
   sound 0%).
3. **Item 11 (instrument the expert set) was done in session 6** (`docs/direction-A-expert-set.md`): the derivation
   finds Gimenez et al.'s quirks and **11 M_full holes**, all witnessed, and the search evades their "certifiably
   robust" set on **2/8** detected pilot malware. A strong independent-hand-baseline **§1/§6 data point**.

## The task: a holistic stock-take against the review, then decide next items (user, 2026-11-03)

Tiers 1-2 of the response to the 2026-11-02 review are complete. **This session is a planning/stock-take, not
drafting.** The user's agenda, in order:

0. **Read `run/122` first** (the adversarial-training row; running at `NUM_WORKERS=24` since 2026-11-03, ~8-9 h -- check
   it has finished, in `artifacts/experiments/a1/advtrain/` and `artifacts/logs/a_advtrain_*`/`a1_eval_advtrain.log`/
   `a1_adaptive_advtrain.log`). State a hypothesis before reading (expected: "seen" toolkit column near 0, held-out
   little changed, adaptive ~20% -- competitive with the unconstrained row, worse than the sound 0%). **Replace Table
   7's `\synthetic` adv-training row** (`manuscript/_f_evaluation.tex`, the `% SYNTHETIC` comment names it) with the
   measured AUC / TPR@1% / detected / seen / held-out / adaptive-union; report honestly whatever it shows (gates are
   guides; never reframe a weak result). `make`/`make check` after.

1. **A holistic analysis of what tiers 1-2 accomplished against the most recent critical review**
   (`docs/reviews/2026-11-02-body.md`). Go risk by risk (R1-R16; triaged into `PLAN.md`'s three-tier plan) and give each
   its *current* status: addressed (with what evidence/commit), partly addressed, still open, or rejected-with-reason.
   Lead with the top-weight risks (R1 tautology/adaptive search, R2 P1/P2, R3 hand table, R4 one instance, R5 Pierazzi).
   The new evidence to fold in: items 7-11 (exactness on 2,000 files; twelve-op adaptive search; hand-table soundness,
   item 9; adv-training, `run/122`; the expert set, item 11) and the tier-1 fixes already in `.tex`.

2. **From that analysis, determine the next items with the user.** The empty paper sections are the leading candidate
   (they carry the novelty/deliverable/Pierazzi risks and are the last big gap), but confirm against the review rather
   than assume -- e.g. whether a second instance (R4) or any remaining experiment should come first. Then settle the
   **open user decision**: the introduction's lead and the deliverable framing (deferred since 2026-11-02).

## If/when the empty sections are the chosen next step (reference)

Order from the review (`docs/reviews/2026-11-02-body.md` §2 and §7, and `PLAN.md`): **related work (§6)** and
**introduction (§1)** first (novelty, deliverable, Pierazzi risks), then **background (§2)**, **discussion (§7)**,
**Figure 1** (edit -> item delta -> adjusted sums -> features, against re-extraction), then the **abstract** last.
Section stubs exist and are empty (`manuscript/_b_introduction.tex`, `_c_background.tex`, `_g_related_work.tex`,
`_h_discussion.tex`, `_a_abstract.tex`). Drafts to reuse: the review's §8 (contributions list, key-insight sentence,
introduction argument); the §5/§6 lists of related work and the fair characterizations; `docs/paper-mock.md` for
budgets. Related work (§6) needs no framing call and has two strong independent-hand-baseline points now (items 9, 11).

## Key context for the empty sections (from the review)

- **R5 (Pierazzi).** Do not imply we compute what Pierazzi et al. call infeasible. Their side-effect features come from
  the *consolidation* a transformation needs to satisfy Gamma, which here is declared per operation (R5); we compute the
  extractor's response to a declared edit. Separate the two in §2. Cite the TOPS 2025 version too.
- **R6 (novelty).** One paragraph naming what is classical (the IVM delta rule, MIN/MAX, the sign domain, Gimenez et
  al.'s Proposition 1) and what is new (the item model with locating positions and margins, the term/readout
  vocabularies, per-input signatures). Theorem 1 is now Proposition 1; Theorem 2 is the main theorem.
- **Missing related work a reviewer will raise** (§5 table): Chen et al. USENIX Sec 2020 (PDF, hand-derived feature
  consequences -- the closest prior by-hand derivation), Srndic & Laskov S&P 2014, Simonetto et al., Dyrmishi et al.,
  Bostani et al., Chen et al. CCS 2021, Demontis et al. Fair lines are in the review's §6.
- **C's "what is the deliverable?"** Answer in §1: a detector sound for a stated edit catalogue at near-standard
  accuracy, derived automatically and re-derivable when the catalogue changes.
- The expert-set result is now a strong §6/§1 data point (the independent hand baseline the meta-review asked for):
  instrumenting Gimenez et al.'s own extractor, the derivation finds their quirks and 11 M_full holes, and our search
  evades their "certifiably robust" set on 2/8.

## Deferred / not re-audited (carry forward)

- **Table 5's population-scoping** (session 4's user decision: in-population Wrong=0, with 45 out-of-population wrong in
  the caption/prose). Not re-audited; recorded user decision, leave unless revisited.
- **Routing to Table 7's sums rows** (`--route <c4>=ref`): `a1_adaptive.py` has no routing and the engine predicts only
  in thrember space, so bring back a concrete plan before touching the sums-row adaptive cells.
- **A G1 unit test for the expert instrumentation** would be nice-to-have (G1 is verified by scratch + `run/120`'s
  derivation go/no-go, but not a committed unit test).

## Working notes

- **Runs:** only jobs under ~10 min yourself (estimate from the slowest case); otherwise smoke-test and write a `run/`
  script (next number **123**; `run/121` is item 9, `run/122` is item 10's hand-off job, pending the user),
  reading `NUM_WORKERS` when the script has a worker flag. Item 11's `run/120` is
  single-process, so it pins OMP and notes NUM_WORKERS does not apply -- same for any single-process successor.
- **Safety-classifier false positives / `/delegate`.** The main session's classifier can false-positive on
  fine-grained per-sample analysis of our own detectors/search logs and stop the response mid-stream. Workaround:
  isolate the unit, write a measurement-framed prompt, run it on a fresh subagent on a simpler model (Agent tool,
  `subagent_type: general-purpose`, `model: sonnet`/`haiku`), relay the conclusion. The `/delegate` skill captures this
  (mandatory Step-0 legitimacy gate).
- **Do not change the writers' output** (`catalogue.write_*`): G7 (runs 107, 117, 118) and Table 5's edit counts depend
  on the same seeded edits. The expert adaptive uses its own loader-safe writers (`a_expert_adaptive.py`) and
  `a1_adaptive.rename_section`.
- Three test modules fail to collect for a pre-existing reason (`tests/test_shortcuts_*`); not caused by recent work.
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. the expert set's two quirks, item 6).
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
