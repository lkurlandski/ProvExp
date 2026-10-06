# ProvExp

Dissertation research: **explanation provenance** for malware detectors. A provenance matrix P (bytes × features,
plus a null element) transfers explanations between the feature-space (EMBER v3 features) and the problem-space
(the bytes of a PE file): pullback b = Pa, pushforward a = PᵀD†b. Target: USENIX Security 2027, second cycle
(late January 2027), as a single security paper with modest theory.

## Read first

- `docs/status.md`: current state, what is waiting on the user, and what to do next. **Update it at the end of
  every session.**
- `PLAN.md`: goals, novelty strategy, phases, evaluations.
- `docs/design_provexp.md`: package design, decisions, provenance conventions, thrember quirks.
- `docs/plan_phase2.md`: the current phase. `docs/related_work.md`: literature and gaps.
- `manuscript/_c_framework.tex`: the framework's definitions. Keep code and manuscript consistent.

## Layout

- `src/provexp/`: `boxmatrix.py` (sparse boxes), `provenance.py` (P, transfers, statistics, numba kernel),
  `featuresets/ember2024/features.py` (thrember + provenance), `data/` (SimpleDB, feature store, TLSH),
  `models/` (GBDT, MLP, MalConv), `explain/` (feature- and problem-space explainers), `metrics.py`.
- `scripts/`: featurize, check_features, build_metadata, select_explanation_set, train_classic, make_fixtures.
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
