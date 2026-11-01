# Resume: ProvExp (after 2026-11-01): fresh planning and brainstorming session for direction A'

This session is for **planning, not building**. The user wants to think A' through from scratch before anything else
is run: its aim, what it claims, against what, and a go/no-go that actually tests that claim. Do not write code or start
experiments until the user agrees on a plan.

## Read first

`CLAUDE.md`; `docs/status.md`'s top block (2026-11-01, end of session); `PLAN.md` ("Next steps (2026-11-01, end of
session)"); `docs/direction-A-prime-mock.md` in full, especially "The pitch in plain terms", Table A'1, Table A'2, the
checks, **"Re-evaluation of the go/no-go (2026-11-01)"**, "Harsh notes on novelty", and decision 7;
`docs/literature-Aprime-2026-10-27.md` (closest work: Kantchelian et al., Chen et al. 2020 for PDF, Simonetto,
Sheatsley, Bostani's Level Up, Incer et al., HRAT); `docs/direction-A-summary.md` (where direction A stands: A' must
complement it); `docs/direction-A-prime-encoding.md`, skimming to "Built: the tightening round" (what the encoding can
and cannot do). Skim `docs/feature-provenance-model.md` (claims C1-C4) if needed to explain what provenance provides.

## Then, before asking anything, recap for the user in plain language

- The research in three sentences, and direction A in two.
- What A' set out to do: a detector's true worst case against realistic file edits, from an exact solver over the
  attacker's choices, with every feature written as a function of those choices (computed from the extractor through
  provenance); certificates when no edit evades.
- What happened: check 1b (certify >= 4 of 13 battery-surviving files on the undefended GBDT) failed: 0 certified,
  6 solver "evasions" that did not work as files, 7 undecided. A bounded tightening round (2026-11-01) tied section
  entropies to their bytes, modeled the overlapping byte-entropy windows exactly, and fixed the realizer (the
  histogram gap and most of the strings gap were realizer bugs, not looseness); a 480 s diagnostic left all 6 files
  undecided. A HiGHS presolve false "infeasible" was found and guarded (every infeasibility is now confirmed without
  presolve).
- The re-evaluation: the checks ran on the undefended EMBER model (failure expected), the threshold was ungrounded,
  undecided was counted as failure, and realizing solver evasions is not needed for certificates. So the no-go does
  not decide A'.
- `run/113`'s result (the tightening round's verdict at 1,800 s on the 6 files), if it has run: read
  `artifacts/experiments/ap_containment/report.json` (must contain every edit), `artifacts/experiments/ap_tightening/`
  (`report.json`, `solves.parquet`, `realized/realized.parquet`) and the logs `artifacts/logs/ap_tightening_*.log`;
  record it in `run/113`'s and `run/111`'s comments (only once the script has finished; never edit a running script).

## The planning session

Brainstorm with the user, openly and critically. Points to cover (not a script; follow the user's lead):

1. **The aim.** What question does A' answer that matters to the community, and for whom? The candidate on the
   table (not adopted): compare hardenings by what can be proved about them under realistic edits: certified %,
   evaded % by real attacks, undecided, with learned and budget-only constraints as the practitioner's alternatives.
   Also weigh alternatives the user or you raise (e.g., where certification is the wrong tool and something else
   provenance enables is better; whether A' should be about defenses, constraints, or evaluation methodology).
2. **Novelty, harshly.** Against Chen et al. 2020 (verified PDF classifiers with edit-derived regions), Kantchelian,
   Simonetto/Sheatsley/Bostani (constraints), Level Up (realizable adversarial training), Incer (monotone). What is
   only possible because the mapping is computed from the extractor? The user doubts the expert-set row (a
   little-cited paper) and Table A'2 as a standalone (Level Up, Chen et al.); a tighter learned baseline is welcome as
   a column.
3. **Which detectors.** Defenses built without our constraints: undefended, PV-seen, PV-all (exist), adversarially
   trained (toolkit), trained on realizable edits, monotone. Our own C4 detector certifies by construction (sanity
   only).
4. **Feasibility.** Tractability is the main risk: the program is ~225 K variables, ~230 K rows, ~43 K binaries on a
   4 MB file; most solves were undecided at 30 min. Options to discuss: smaller catalogues or budgets, per-file time
   budgets, decomposition, a better solver (only HiGHS via scipy is installed), certifying on hardened models that
   split on fewer reachable features. A cheap pre-check was proposed: the existing pipeline on the PV models for a few
   files (a `run/` script for the user; > 15 min).
5. **The go/no-go.** It must test the claim on informative cases, keep undecided separate, ground its thresholds, and
   validate each stage in isolation. A sketch is in the mock's re-evaluation section.
6. **The mock.** End with a revised mock of the main table (each column's model component, invented numbers marked),
   the screening criteria, and the go/no-go, written into `docs/direction-A-prime-mock.md` once the user agrees.

For every decision you put to the user: say what it is, give a concrete example, and say what each choice changes.
Never use doc-internal labels (C3, M_full, G7, A4) without saying what they are.

## State of the code

All committed; ruff and mypy pass; `tests/test_ap_encoding.py` and `tests/test_ap_realize.py` pass. Main pieces:
`scripts/ap_encoding.py` (the edit-choice encoding: append + up to 3 sections within the budget; per-section counts;
the block model of windows; Pinsker / dominant-share / least-share / Fano cuts; `Program.solve` confirms
infeasibility without presolve), `scripts/ap_realize.py` (writes a solver answer as a file), `scripts/ap_check1b.py`
(certification runs; `--names` filter), `scripts/ap_check2_realize.py` (writes, scores, and attributes solver
evasions), `scripts/ap_containment.py` (`run/111`). Saved solutions only load with the encoding they were solved with.

## Standing rules

Be harsh about novelty; never raise deadlines; bring any no-go to the user before dropping anything; no result may rest
on an extractor quirk; keep experiments' complexity down; **run only jobs of ~10 minutes or less yourself (anything
over ~15 minutes goes to the user as a `run/` script); estimate from the slowest case first**; default 16 workers,
never cap workers in Python; state a short hypothesis before each run; add a `run/` script for every experiment (next
number: 114) and record results in its comments; re-run `run/111` after any change to the encoding; commit in logical
pieces after ruff and mypy pass; never edit `tests/reference/`; do not run the full test suite while the user's jobs
run; answer methodology questions by reasoning, not by running data first.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- A' detectors: `artifacts/models/gbdt/seed-0-s10-{ref,pv-seen,pv-all}`; thresholds at 1% FPR from each model's
  `ts_predictions.parquet` (ref: raw 1.103). Battery evasions: unconstrained 27/47, PV-seen 15/22, PV-all 15/22. The
  expert-set monotone model (run 106) detects 8 of 50 pilot malware.
- Kill background jobs by PID, never with `pkill -f`/`pgrep -f` on a pattern that matches your own shell's command
  line (it happened again this session).
