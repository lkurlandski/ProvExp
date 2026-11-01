# Resume: ProvExp (after 2026-11-01, end of session): decide whether A' can be salvaged

This session is a **decision, not a build**. After several days on direction A', the user doubts it can give a result
a security reviewer would find practically useful. Decide with the user whether A' is salvaged (in what form, with
what claim), folded into direction A as a section, or dropped to `docs/graveyard.md`. Do not write code or start
experiments until the user has decided. Be candid: if the honest answer is "drop it", say so and say why; if a salvage
is credible, say exactly what a reviewer would gain from it and what it would cost.

## Read first

`CLAUDE.md`; `docs/status.md`'s top block; `PLAN.md` ("Next steps (2026-11-01, end of session: decide whether A' is
salvaged)" and "Directions"); **`docs/direction-A-prime-plan.md` in full, especially Sections 1-5 (the adopted plan:
brackets, the go/no-go G0-G3), 9-11 (what the runs showed) and 12 (the evidence summary)**; `docs/direction-A-summary.md`
(direction A, which stands at pilot scale: A' must add something A does not); the "Harsh notes on novelty" and
"Re-evaluation of the go/no-go" sections of `docs/direction-A-prime-mock.md`; `docs/literature-Aprime-2026-10-27.md`
(Chen et al. 2020 for PDF, Kantchelian, Simonetto / Sheatsley / Bostani, Level Up). Skim `docs/feature-provenance-model.md`
for claims C1-C4 if needed to explain what provenance provides.

## Then, before asking anything, recap for the user in plain language

- The research in three sentences; direction A in two (sound monotone detectors from computed directions; every check
  passed at pilot scale; PV falls to our adaptive search on 21-22 of 22 files).
- What A' tried: prove a detector's worst case under realistic file edits (append, added sections) with an exact
  solver whose every feature is computed from the attacker's choices through provenance; report a bracket per file
  (floor: proven lower bound on the reachable score; ceiling: the best real attack).
- What it showed (plan Section 12): sound throughout (containment 1,105 of 1,105; no certificate on an evaded file);
  certifies only where the edits barely touch the detector (append on PV, in seconds, and partly circular because PV
  was built from padding and section attacks) or at tiny budgets (4 KB: 2 of 13 on the undefended model); fails
  wherever the detector relies on movable features at realistic budgets (64 KB and up; added sections), because the
  relaxation is both large (one block per KB of byte-entropy windows) and far too loose (LP floor -10.8 at 64 KB vs a
  threshold of 1.10). Many files cannot take an added section at all. The adversarially trained rows (G2) were never
  built; as things stand they would very likely stay open too.
- The user's decision 6, accepted: A' stands on its own only if it rests on what A does not use (how far features move
  and how they move together under combined edits, claims C2-C3) and shows a result directions alone cannot.

## The decision session

Points to cover (follow the user's lead):

1. **Is there a reviewer-relevant claim left?** Weigh honestly, each against the realistic alternative a practitioner
   would use and against the screening criteria in `CLAUDE.md` (the gap only provenance makes cheap; a realistic
   competitor; a falsifiable check):
   - (a) a certified budget per file (largest append or section proven not to evade, tractable to ~16-32 KB) beside the
     attack ceiling; weakness: real attackers are not limited to a few KB, so a reviewer may call it irrelevant;
   - (b) fold into A: PV's append certificates and the contrast with learned constraints (they certify nothing, or
     only circularly) as a section of the A paper;
   - (c) a new formulation for large budgets: the relaxation, not the solver, is what fails, so this is high risk;
   - any other use of the same machinery the user or you raise (e.g., using the computed region for something that
     needs no certificate). Do not reopen the realizer / "solver evasions as files" line (check 2), already dropped.
2. **Cost of each** in sessions and in the user's compute, and what the thesis loses or gains. No deadline talk.
3. **If dropped:** write the graveyard entry (what was tried, why it failed, what survives: the encoding's soundness,
   `scripts/ap_bracket.py`, the learned-constraints contrast), and pick the next work: A's remaining gaps
   (`docs/direction-A-summary.md`: adversarial-training baseline, second toolkit, leave-one-out PV, scale) or screening
   B / C (`PLAN.md`, "Directions").
4. Record the decision in `docs/direction-A-prime-plan.md`, `PLAN.md`, `docs/status.md`, and (if dropped)
   `docs/graveyard.md`; update `CLAUDE.md`'s pointers.

For every decision you put to the user: say what it is, give a concrete example, and say what each choice changes.
Never use doc-internal labels (C3, M_full, G2) without saying what they are.

## State of the code

All committed; ruff, mypy, and the A' tests pass (`tests/test_ap_encoding.py`, `tests/test_ap_bracket.py`,
`tests/test_ap_realize.py`). Main pieces: `scripts/ap_encoding.py` (the edit-choice encoding; `Program.solve` now calls
HiGHS directly through `highspy`, added to `requirements.txt`, so a timeout keeps the dual bound; every infeasibility is
confirmed without presolve; `certify(..., minimize=True)` returns a proven floor), `scripts/ap_bracket.py` (the
bracket per detector, edit family, and file; `--budget_frac 0 --budget_min B` for a fixed budget; `--max_sections`).
Results: `artifacts/experiments/ap_bracket/` (`precheck` from `run/114`; `ref_append_{4096,65536,524288}` and
`pv_sections_k1` from `run/115`). The full containment run (`run/111`) has not been re-run since the switch to
`highspy` (a 48-edit smoke held); re-run it before any further result rests on the solver.

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk; keep experiments' complexity down; run only jobs of ~10 minutes or less yourself (anything
over ~15 minutes goes to the user as a `run/` script); estimate from the slowest case first; default 16 workers, never
cap workers in Python; state a short hypothesis before each run; add a `run/` script for every experiment (next
number: 116) and record results in its comments; commit in logical pieces after ruff and mypy pass; never edit
`tests/reference/`; answer methodology questions by reasoning, not by running data first.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}`; thresholds at 1% FPR (ref raw 1.103). The
  battery (toolkit-v2 + toolkit_v2 + the adaptive search) evades ref 27/47, PV-seen 15/22, PV-all 15/22.
- Kill background jobs by PID, never with `pkill -f`/`pgrep -f` on a pattern that matches your own shell's command line.
