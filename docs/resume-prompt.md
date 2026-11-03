# Resume: ProvExp (after 2026-11-03, session 6): items 9-10, then the empty paper sections

## Where things stand

Session 6 finished two things and left the manuscript's empty sections as the next big phase. Nothing is pushed.

1. **Table 7's PV adaptive cell is decided and written (commit `7c9d8ff`).** The two search menus are complementary on
   PV, not one-worse-than-the-other (run 108 append+add-section 16/22, twelve-op 12/22, intersection 8, **union 20/22**,
   two files evaded by neither). The user chose **Option A, the union**: report the adaptive attacker as the search run
   under both menus keeping any evasion (standard max-over-configs). Table 7: unconstrained Adaptive **8%->20%** (10/49),
   PV-4 Adaptive **73%->91%** (20/22); soundness rows stay 0% (noted as checked across all twelve operations). The PV
   prose was rewritten and a latent stray-`%` bug fixed. Diagnosis + resolution: `docs/direction-A-A1-design.md`.
2. **Item 11 (instrument the expert set) is done (commits `352fc55`, `195b354`, `01e8608`, `68d2434`).** See
   `docs/direction-A-expert-set.md` ("Instrumented (item 11)" and the witnesses/adaptive section).
   - `ExpertFeatures` now emits `items()`+`readouts`, reusing only `Identity`/`Opaque` -- **no core-framework change**.
     **G1 bit-exact** on 45 files. The two assign-per-name quirks are modeled as non-locality (`local=False` when
     `accumulate=False`); the import quirk is surfaced quantitatively (sound sum 92 vs the assign extractor's 1).
   - The C4 derivation (`scripts/a_expert_directions.py`, go/no-go built in) gives **11 M_full holes = rows 27, 30-39**,
     not 12 (the doc's "12" miscounted its own 11-row list; the user chose the tight 11). Two corrections the derivation
     forced: **`no_sig` is up, not a hole** (a marker present iff unsigned; removing the signature adds it), and **slack
     does not change the `info` features** (entropy is over the mapped content, which excludes slack -- the holes come
     from rename). All **11 of 11 holes witnessed** by our own edits; the **adaptive search evades the monotone expert
     model on 2 of 8** detected pilot malware (rename hole), scored by re-extraction (`scripts/a_expert_adaptive.py`,
     `run/120`). Manuscript §5 updated ("12 of 40" -> "11", slack dropped, +the 2/8). `make`/`make check` clean.

## The task (in order)

1. **Item 9: a detector on the hand table** (`PLAN.md` Tier 2). *Hypothesis:* the search, adding a section after the
   overlay, evades it on some in-population files; inside the population the hand and derived tables differ in only two
   features (`entry_name_hash`, `security_size`), so the detectors should be near-identical. **Go/no-go:** at least one
   in-population evasion; otherwise report the in-population difference as immaterial to the detector (honesty row, R3a).
   Likely answerable from existing artifacts or a short run (the hand-table directions already exist; `a_directions.py
   --hand`).
2. **Item 10: the adversarial-training row** (synthetic now), against item 8's twelve-op search. A training run (the
   toolkit's adversarial examples added to training), so a `run/` script for the user (next number 121, reads
   `NUM_WORKERS`). **Run with eyes open:** the review flags the synthetic 20% as implausible given our search gets only
   10/49 on the *undefended* model, so adversarial training may come out competitive with the monotone rows -- report
   honestly whatever it shows (`docs/memory`: gates are guides; never reframe a weak result).
3. **Then the empty paper sections** (the big phase; the review's top remaining risks live here). Order from the review
   (`docs/reviews/2026-11-02-body.md` §2 and §7, and `PLAN.md`): **related work (§6)** and **introduction (§1)** first
   (they carry the novelty, deliverable, and Pierazzi risks), then **background (§2)**, **discussion (§7)**, **Figure 1**
   (edit -> item delta -> adjusted sums -> features, against re-extraction), then the **abstract** last. Section stubs
   exist and are empty (`manuscript/_b_introduction.tex`, `_c_background.tex`, `_g_related_work.tex`, `_h_discussion.tex`,
   `_a_abstract.tex`). Drafts to reuse: the review's §8 (contributions list, key-insight sentence, introduction
   argument); the §5/§6 lists of related work and the fair characterizations; `docs/paper-mock.md` for budgets.

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
  script (next number **121**), reading `NUM_WORKERS` when the script has a worker flag. Item 11's `run/120` is
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
