# Resume: ProvExp (after 2026-10-27) — A' chosen; write its mock; build the automatic derivation

Read `CLAUDE.md`, then `docs/status.md`'s top block, `PLAN.md` ("Directions", A', and "Next steps (end of
2026-10-27)"), `docs/direction-A-summary.md`, `docs/literature-Aprime-2026-10-27.md`, and `docs/item-layer-design.md`.
**Start by recapping for the user in plain language** where things stand and what is next, before asking anything.
Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may
rest on an extractor quirk. Run only jobs of ~10 minutes or less yourself (estimate from the slowest case first);
anything longer goes to the user as a `run/` script (default 16 workers; never cap workers in Python).

## Where things stand

- **Direction A** is complete at pilot scale (`docs/direction-A-summary.md`), with two corrections found on
  2026-10-27:
  1. Its C4 directions are hand-written per-group rules (`scripts/a_directions.py`) and its C1 predictors are
     hand-coded per edit (`scripts/a_c1_table0.py`, `scripts/a1_adaptive.py`). The paper's claim that they are derived
     from the extractor needs the design in `docs/item-layer-design.md` built.
  2. **A confirmed soundness gap:** pefile skips extents past EOF when locating the overlay, so appending can lower
     `section:overlay_size` (4 of 5 testable pilot files with a section past EOF). The M_full C4 rows constrain it
     up-only, so "never moved by any attack" does not hold on such files. The `body_*` sums (10.7% of the sums row's
     gain) may be affected too; not yet witnessed.
- **Second application: A'** (from feature-space targets to real file edits; B and C set aside). The literature is
  read (`docs/literature-Aprime-2026-10-27.md`). Harsh read:
  - the only new part is side effects and constraints computed from the extractor;
  - hash-bucket targeting is prior work (Rosenberg et al.);
  - the strongest uses are probably evaluative or defensive: exact realizable worst-case evaluation of a detector, or
    realizable examples for adversarial training as in Bostani et al.'s Level Up.
- **Expert-set row:** designed in `docs/direction-A-expert-set.md`. The user decided to re-implement Gimenez et al.'s
  40 features (their own LIEF extractor, not EMBER); our M_full is the priority, their add-only threat model is for
  context.
- **Cost column:** deferred until the derivation is automatic.

## Do next

1. **The A' mock** (`docs/direction-A-prime-mock.md`). Not yet written: the safety classifier stopped the draft
   twice on 2026-10-27. If it is still missing, the user may have another session write it from the task prompt below;
   then review it against the literature notes and direction A's results, and bring it to the user. No A' code before
   the user has seen it.
2. **The open decisions at the end of `docs/item-layer-design.md`.** My recommendations from 2026-10-27:
   - keep `provenance` until G2 passes, then make it a projection of `items`;
   - for the overlay gap, be strict and also report a precondition row;
   - ask whether pefile's overlay rule is a quirk to patch or real behavior (leaning: real, it is pefile's
     definition);
   - re-run A1's C4 rows at pilot scale now (the toolkit part is a 47-min `run/` script);
   - run G1 on the 2,000-file set too;
   - accept the sound syntactic regex test.
3. **Build the derivation, steps 1-3** (item table, readouts as data; checks G1/G2). Both A and A' need them. The mock
   decides whether the C1 engine (step 5) or the C4 engine (step 7) follows. The doc's effort estimate is in human
   days and far too high (user).
4. **The expert-set row:**
   - re-implement the 40 features on pefile, and confirm the per-name overwrite reading on one file;
   - patch the quirks as pure additions and note them upstream;
   - featurize the 10% store (a `run/` script if over 10 min);
   - train the monotone GBDT and run the A1 protocol under M_full and M_add.

## Task prompt for the A' mock (for another session, if needed)

```
You are working in the ProvExp repository (/home/lk3591/Documents/code/ProvExp), a dissertation project on feature
provenance for robust malware detection. Read CLAUDE.md first and follow its conventions, especially "Explain
plainly", "Be harsh about our own novelty", and the screening criteria under "Framework conventions".

Task: write docs/direction-A-prime-mock.md, the on-paper screening mock for direction A' (PLAN.md, Directions, A').
Model it closely on docs/direction-A-mock.md, which is the template the user was happy with: the pitch in plain
terms; one or more mock paper tables with invented numbers clearly marked as invented; for every column, the model
component (docs/feature-provenance-model.md, C1-C4) that produces it; the realistic baselines and why; falsifiable
go/no-go checks to run before building; and harsh notes on novelty.

Read before writing:
  - PLAN.md (Thesis; Directions, especially A'), docs/direction-A-summary.md, and docs/direction-A-A1-design.md
    ("Result: Table A2": the existing C1-guided search is half of A');
  - docs/literature-Aprime-2026-10-27.md (closest work and the harsh read; note that hash-bucket targeting is prior
    work and must not be claimed);
  - docs/item-layer-design.md (the automatic derivation A' depends on; treat it as a planned component, and say which
    of its build steps A' needs first);
  - docs/feature-provenance-model.md Sections 2-4 and docs/direction-A-threat-model.md Section 1 (threat models).

The mock must state, in plain language, which security task A' serves and against which realistic alternative a
practitioner would use, and why only feature provenance makes it cheap. It should weigh the uses the literature notes
name (realizable worst-case evaluation of a detector; realizable examples for adversarial training) and recommend
one as the main table. Keep the comparison consistent with direction A's protocol (pilot scale, M_full, 1% FPR).
End with open decisions for the user. Do not write code, run experiments, or commit; produce only the document.
```

## Notes

- `papers/` now holds the foundational PDFs (Gimenez, Pierazzi extended, Severi, Rosenberg, Labaca-Castro, Demetrio,
  RAMP, Perasso, Smutz & Stavrou, EvadeDroid, Kantchelian, PAD, Level Up, Dyrmishi, Simonetto). It is untracked, as are
  `REVIEW*.md` and `make-manuscript.sh`; leave them uncommitted.
- Gimenez et al.'s code (the 40-feature extractor) is at
  github.com/PFGimenez/certifiably-robust-malware-detectors-by-design, `static_features_extraction.py:get_features`.
- Still unread for A': HRAT (Zhao et al., CCS 2021; paywalled, ask the user), Šrndić & Laskov (S&P 2014), verifiable
  boosted tree ensembles (arXiv 2402.14988).
- The user still owes the upstream reports in `docs/upstream-issues.md` (thrember item 1; secml-malware item 4).
- Everything uses the quirk-fixed (merged-imports) extractor; the sums extractor includes it.
