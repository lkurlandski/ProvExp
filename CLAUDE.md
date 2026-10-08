# ProvExp

Dissertation research: **explanation provenance** for malware detectors. A provenance matrix P (bytes × features,
plus a null element) transfers explanations between the feature-space (EMBER v3 features) and the problem-space
(the bytes of a PE file): pullback b = Pa, pushforward a = PᵀD†b. Target: USENIX Security 2027, second cycle
(late January 2027), as a single security paper with modest theory.

## Read first

- `docs/status.md`: current state, what is waiting on the user, and what to do next. **Update it at the end of
  every session.**
- `PLAN.md`: claims, experiments (E1–E4, appendix A1–A3), timeline, gates, open questions.
- `docs/plan_e1.md` and `docs/e1_pilot.md`: the current experiment (faithfulness and cost) and its results.
  `docs/e1_baselines.md`: the running baselines pilot, with the reading of each outcome decided in advance.
- `docs/plan_e2.md` and `docs/e2_census.md`: E2 (characterizing P): the revised statistics and the census.
  `docs/pilot.md`: the census.
- `docs/design_provexp.md`: package design, decisions, provenance conventions, thrember quirks.
  `docs/related_work.md`: literature and gaps. `docs/plan_phase2.md`: Phase 2 (complete).
- `manuscript/_c_framework.tex`: the framework's definitions. Keep code and manuscript consistent.

## Layout

- `src/provexp/`: `boxmatrix.py` (sparse boxes), `provenance.py` (P, transfers, statistics, round trips),
  `featuresets/ember2024/features.py` (thrember + provenance), `data/` (SimpleDB, feature store, TLSH),
  `models/` (GBDT, MLP, MalConv), `explain/` (feature- and problem-space explainers), `ablation.py` (generic
  ablation, budgets, black-box provenance, coarsening), `featuresets/ember2024/ablation.py` (PE-aware protection and
  verification, experiment code), `metrics.py`.
- `scripts/`: data (featurize, check_features, build_metadata, select_explanation_set, train_classic, make_fixtures);
  explanations and census (explain, provenance_census, pullback_agreement, pilot_tables); E1
  (discover_protected_fields, header_typical_values, faithfulness, e1_tables).
- `tests/`: `reference/` is a verbatim copy of thrember's `features.py`. **Never edit it.**

## Environment

- venv in `env/` (uv, Python 3.14): `VIRTUAL_ENV=$PWD/env uv pip install -r requirements.txt -r requirements-dev.txt`
  then `uv pip install -e .`. Never use the miniconda installation.
- Gitignored, never commit: `tests/data/` (real malware), `checkpoints/` (MalConv), `index/` (split files from SSViT),
  `artifacts` (symlink to `/scratch/lk3591/provexp`: feature store, models, reports, logs).
- Binaries: SimpleDB at `/shared/datasets/EMBER-2024/data/{tr,vl,ts}`, truncated to 4,000,000 bytes.
- Run featurization with `PYTHONHASHSEED=0` (thrember's warning features depend on the hash seed).

## Working rules

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
  stratifications built on PE-format structure (headers, sections, overlay, packers, "attacker-controllable
  regions"); the user has rejected this direction several times.
- **The GBDT is the first classifier we experiment with** (decided 2026-10-08). The framework stays general-purpose
  (P does not depend on the classifier). The MLP is set aside *temporarily* and returns once the GBDT methodology is
  established (`PLAN.md`, "Model scope"); do not describe it as dropped.
- **Experiments may use domain knowledge selectively** where it protects their integrity (decided 2026-10-07): e.g., a
  PE-aware perturbation operator for the faithfulness evaluation (E1) or a PE-aware trigger for the planted ground
  truth (E3). Keep it inside the experiment, say why it is needed, and never let it into the framework.
