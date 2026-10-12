# ProvExp

Dissertation research: **explanation provenance** for malware detectors. A provenance matrix P (bytes × features,
plus a null element) transfers explanations between the feature-space (EMBER v3 features) and the problem-space
(the bytes of a PE file): pullback b = Pa, pushforward a = PᵀD†b. Target: USENIX Security 2027, second cycle
(late January 2027), as a single security paper with modest theory.

## Read first

- `docs/status.md`: current state, what is waiting on the user, and what to do next. **Update it at the end of
  every session.**
- `PLAN.md`: claims, experiments by ID (CP, PB1–2, PF1–2, CM; appendix App-L, App-R), timeline, gates, open
  questions.
- Experiment docs, named by ID: `docs/cp_plan.md`, `docs/cp_census.md` (CP: characterizing P); `docs/pb1_plan.md`,
  `docs/pb1_pilot.md`, `docs/pb1_baselines.md` (PB1: pullback faithfulness and cost; the baselines doc fixes the
  reading of each outcome in advance); `docs/trigger_plan.md` (the planted-trigger testbed: PB2 and PF2, design and
  results); `docs/pf1_plan.md` (PF1: the pushforward's faithfulness and the resolution trend); `docs/cm_plan.md`
  (3-A: comparing detectors through the pullback, the pullback's application); `docs/appendix.md` (App-L, App-R);
  `docs/shortcuts_plan.md` (3-B: real shortcuts via the pullback; dropped, kept for its post-mortem).
- `docs/design_provexp.md`: package design, decisions, provenance conventions, thrember quirks.
  `docs/related_work.md`: literature and gaps. `docs/archive/`: superseded documents (the Phase 2 plan and census,
  old IDs E1–E4, A1–A3; artifact paths such as `artifacts/experiments/e1/` (PB1) still use them).
- **State a hypothesis before running an experiment** (what you expect and why), and report a failed check as such.
  Keep it short and proportionate: a sentence or two, not an elaborate pre-registered reading for every outcome
  (user, 2026-10-09).
- `manuscript/_c_framework.tex`: the framework's definitions; `_d_applications.tex`: the evaluation. Keep code and
  manuscript consistent.

## Layout

- `src/provexp/`: `boxmatrix.py` (sparse boxes), `provenance.py` (P, transfers, statistics, round trips),
  `featuresets/ember2024/features.py` (thrember + provenance), `data/` (SimpleDB, feature store, TLSH),
  `models/` (GBDT, MLP, MalConv), `explain/` (feature- and problem-space explainers), `ablation.py` (generic
  ablation, budgets, black-box provenance, coarsening), `featuresets/ember2024/ablation.py` (PE-aware protection and
  verification, experiment code), `metrics.py`.
- `scripts/`: data (featurize, check_features, build_metadata, select_explanation_set, train_classic, make_fixtures);
  explanations and census (explain, provenance_census, pullback_agreement, pilot_tables); CP (cp_tables,
  cp_coarsening, cp_blackbox); PB1 (discover_protected_fields, header_typical_values, faithfulness, pb1_tables);
  the trigger (trigger_select, trigger_poison, trigger_validate, trigger_explain, trigger_tables); PF1 (pf1,
  pf1_resolution).
- **Rankings break ties by a seeded permutation, never by position or index** (`ablation.element_order` /
  `window_order` with `tiebreak`, `pf1.feature_order`), and treat scores within 1e-9 (relative) as tied: equal scores
  are common (features or bytes with identical provenance; occlusion windows that change nothing).
- `run/`: the commands that produced `artifacts/`, one numbered script per step, with the runtimes they took. **Add a
  script here whenever a new experiment is run**, and keep its arguments in sync with what was actually run. In
  these scripts: (1) `echo` a short line before each step saying what runs and, above all, **the log file** a long
  step writes to; (2) put one argument (or one short group) per line with `\` continuations, so that long commands
  are readable and easy to edit.
- `tests/`: `reference/` is a verbatim copy of thrember's `features.py`. **Never edit it.**

## Environment

- venv in `env/` (uv, Python 3.14): `VIRTUAL_ENV=$PWD/env uv pip install -r requirements.txt -r requirements-dev.txt`
  then `uv pip install -e .`. Never use the miniconda installation.
- `tmp/` holds the user's scratch files (gitignored). Do not mention, list, or ask about them.
- Gitignored, never commit: `tests/data/` (real malware), `checkpoints/` (MalConv), `index/` (split files from SSViT),
  `artifacts` (symlink to `/scratch/lk3591/provexp`: feature store, models, reports, logs).
- Binaries: SimpleDB at `/shared/datasets/EMBER-2024/data/{tr,vl,ts}`, truncated to 4,000,000 bytes.
- Run featurization with `PYTHONHASHSEED=0` (thrember's warning features depend on the hash seed).

## Working rules

- **Work at pilot scale** (decided 2026-10-08): do most of the research on the ~100-file pilot subset and one seed;
  scale up (2,000 files, seeds 0–2) only for final numbers, and only when the user decides.
- **Do not run long or resource-intensive jobs** (featurization, training, large sweeps, the full test suite while
  the user's jobs run) without asking. Smoke-test on a small slice, then give the user the exact command.
- Light checks: `OMP_NUM_THREADS=2 nice -n 10 env/bin/pytest -q -p no:xdist tests/test_<module>.py`.
  Full suite: `env/bin/pytest -n 16 tests` (~4 min).
- Before committing: `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts` (strict) must pass.
- **Do not try to compile the manuscript.** There is no LaTeX toolchain here, and `manuscript/` holds fragments of a
  larger document (no preamble). After editing it, check that braces and environments balance and that every `\ref`
  has a `\label` in `manuscript/`; the user builds it.
- Commit to `main` in logical pieces. Do not push unless asked.
- Changes to the thrember-derived `features.py` are pure additions; the original lines stay untouched.

## Code style

Follow `/home/lk3591/Documents/code/SSViT/exeformer/exeformer.py` (ignore that it bundles everything in one file):

- A module docstring on its own lines; `from __future__ import annotations`; one import per line, grouped
  stdlib / third-party / local; `__all__` near the top.
- `####...` section banners (80 characters), mirrored in the tests.
- Full type hints with `Optional[...]`; Google-style `Args:` / `Returns:` docstrings, one-liners for small helpers.
- Validate inputs and raise `ValueError` / `RuntimeError` with f-strings.
- `# NOTE:` comments for deliberate compromises; `# NOTE (Axiom 3):` marks the null-element/empty-feature tension.
- 120-character lines, double quotes, `pytest` classes `TestX` with `parametrize`, skip when data is absent.

## Framework conventions

- Elements are bytes. Feature sets record raw contributions; `Provenance` normalizes lazily.
- Features with no contributions go to the null element (`empty="null"`, the default; `uniform`/`ignore` also exist).
- All explainers attribute the malware log-odds (GBDT raw score; logit₁ − logit₀ for neural networks).
- **The framework and the core contributions are domain-agnostic.** The framework applies to any classifier with a
  complex feature extractor and depends only on the relationships between elements and features (P), never on what an
  element or a feature *means*. `provexp` (outside `featuresets/`), the provenance statistics, the census, and the
  core analyses work with elements, features, feature subsets, and P only. Do not propose analyses, modules, or
  stratifications built on PE-format structure (headers, sections, overlay, packers, PE-specific "attacker-controllable
  regions" such as the DOS header); the user has rejected this direction several times. Questions about what control
  of an *arbitrary* byte set allows, posed domain-agnostically in terms of P, are welcome (user, 2026-10-09).
- **Coverage, localizability, and the null element's share are not contributions** (user, 2026-10-09). Do not propose
  promoting them, building analyses on them, or reporting "reliance on absence" as a finding. (i) They measure a
  particular explanation of a particular file by a particular explainer, not the provenance; (ii) a large share of
  attribution on unattributable features reflects a limitation of the provenance extraction pipeline (features whose
  bytes it cannot name), not a broad, novel finding about detectors. App-L stays only as a stated limitation.
- **The GBDT is the first classifier we experiment with** (decided 2026-10-08). The framework stays general-purpose
  (P does not depend on the classifier). The MLP is set aside *temporarily* and returns once the GBDT methodology is
  established (`PLAN.md`, "Model scope"); do not describe it as dropped.
- **Experiments may use domain knowledge selectively** where it protects their integrity (decided 2026-10-07): e.g., a
  PE-aware perturbation operator for the faithfulness evaluation (PB1) or a PE-aware trigger for the planted ground
  truth (PB2, PF2). Keep it inside the experiment, say why it is needed, and never let it into the framework. The
  extrinsic applications (3-A, 3-B, 3-C) may lean into domain-specific ideas where appropriate (user, 2026-10-09).
