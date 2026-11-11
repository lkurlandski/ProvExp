# ProvExp

Dissertation research (restarted 2026-10-22): for the feature extractors security classifiers use
(*sum-then-readout extractors*: find the pieces of the input, add up what each contributes, compute each feature by a
formula over a few totals), the feature-space consequences of an attacker's edits are computed from the instrumented
extractor: exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no
edit in the threat model can evade. PE malware with EMBER is the primary instance; the framework is format-free. The
previous direction (explanation provenance) was abandoned on 2026-10-22 (`docs/graveyard.md`). Deadlines and
conference cycles are not a planning constraint (user).

## Read first

- **Every session:** `docs/status.md` (current state, what waits on the user; **update it at the end of every
  session**) and `PLAN.md` (thesis, decisions, next steps). The session's starting point: `docs/resume-prompt.md`.
- **Everything else only when the task needs it.** `docs/README.md` indexes every document, active, evidence, and
  archived, with when to open it. Do not read archived material by default; search it when a reason or a record is
  needed. The manuscript (`manuscript/*.tex`) is the authority on the paper's content.
- `docs/paper-mock.md` decides what goes into the paper; check new work against it.
- **Paper numbers (sections, definitions, tables) come from the compiled PDF**, never from a document: check
  `manuscript/main.aux` before naming one, and give the title alongside (table in `docs/README.md`).
- Writing paper prose: the project skill `.claude/skills/paper-prose/` (the user's accepted text as reference, their
  taste described as judgement, the fixed constraints; rewritten 2026-11-09 after its accumulated rules did harm, so
  never grow it into a rule list) and the raw reaction log `docs/writing-spec.md`.
- Be harsh about our own novelty: read the closest work on the same *task* before building (user, 2026-10-22).
- **State a hypothesis before running an experiment** (what you expect and why), and report a failed check as such.
  Keep it short and proportionate: a sentence or two, not an elaborate pre-registered reading for every outcome
  (user, 2026-10-09).
- The manuscript is written straight into `.tex` (`manuscript/`), drafted from the paper mock to its word budget; no
  markdown drafts of paper text. Write continuous prose rather than stacks of labeled paragraphs (user, 2026-10-14);
  no internal IDs in the paper. Old manuscript and simulated reviews of the old direction: git history and
  `docs/reviews/explanation-provenance/`.

## Code

- `src/provexp/`: `items.py` (the item layer: items, terms, readouts as data), `reach.py` (the side-effect and
  direction engines; "C1" and "C4" in old names), `featuresets/ember2024/` (`features.py`: thrember + instrumentation;
  `catalogue.py`: the edit catalogue and the population check; `sums.py`: the re-encoding over sums; `expert.py`:
  Gimenez et al.'s 40 features), `data/` (SimpleDB, feature store, TLSH), `models/` (GBDT, MLP, MalConv, ERDALT),
  `metrics.py`. From the old direction: `boxmatrix.py`, `provenance.py`, `explain/`, `ablation.py`. Design notes:
  `docs/design.md`.
- `scripts/`: inventory in `scripts/README.md`, grouped by what the paper uses. Dropped experiments are under
  `scripts/archive/`.
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
- Binaries: SimpleDB at `/shared/datasets/EMBER-2024/data/{tr,vl,ts}`, truncated to 4,000,000 bytes; scripts read
  the location from `EMBER2024_DATA` (`src/provexp/data/paths.py`; set it on machines where the dataset lives
  elsewhere). Copying the artifacts to another server: `run/sync_artifacts.sh`.
- Run featurization with `PYTHONHASHSEED=0` (thrember's warning features depend on the hash seed).

## Working rules

- **Work at pilot scale** (decided 2026-10-08): do most of the research on the ~100-file pilot subset and one seed;
  scale up (2,000 files, seeds 0–2) only for final numbers, and only when the user decides.
- **Do not run long or resource-intensive jobs** (featurization, training, large sweeps, the full test suite while
  the user's jobs run) without asking. Run yourself only jobs estimated at **~10 minutes or less**, estimating from
  the slowest case (user, 2026-10-26); otherwise smoke-test on a small slice and give the user a `run/` script.
- **Resources in `run/` scripts:** default to at most 16 workers or threads (the user cut runs 38-40 down to these,
  2026-10-12); GPUs are whatever `CUDA_VISIBLE_DEVICES` makes visible (unset: all), one process per visible GPU
  when separate processes train in parallel, never a custom `GPUS` variable (2026-11-11); the user may raise them, so
  never enforce the cap in Python (2026-10-26). Every new script reads the worker count from the environment, `NUM_WORKERS="${NUM_WORKERS:-16}"`, and passes `"$NUM_WORKERS"` to the
  Python flag (`--workers`, `--num_workers`, ...), so the user can run `NUM_WORKERS=32 run/NNN_x.sh` (2026-11-03).
  Never edit a `run/` script while it runs (bash reads it as it goes); sync its comments afterwards.
- **Explain plainly.** Lead with the plain-language version of an argument (what is computed, what it is compared
  with, why it matters); define terms and avoid dense shorthand. The user could not follow a jargon-heavy explanation
  (2026-10-12).
- Light checks: `OMP_NUM_THREADS=2 nice -n 10 env/bin/pytest -q -p no:xdist tests/test_<module>.py`.
  Full suite: `env/bin/pytest -n 16 tests` (~4 min).
- Before committing: `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts` (strict) must pass.
- **Compile the manuscript with `make` in `manuscript/`** (user-space TeX Live in `~/texlive`, latexmk + pdflatex).
  One file per section (`_a_abstract.tex` ... `_h_discussion.tex`, appendices `_j_proofs.tex` ...), in the mock's
  outline order; each stub's comment states its content and word budget. Count words with `texcount` per file.
  `main.tex` is the complete document (ACM `acmart` `sigconf`, the CCS format; do not change fonts, margins, or spacing) and
  `\input`s the section fragments. After editing, run `make` and `make check` (undefined refs/citations, overfull boxes).
- **Early drafting stage (user, 2026-10-14):** (1) exceeding the page limit does not matter yet; do not cut or compress
  text to fit. A section may run 50-75% over its mock word budget while drafting (user, 2026-11-03). (2) Exact numbers in the prose are of little concern, since experiments will be re-run and more data
  added; focus on structure, argument, and prose, not on syncing every number. Write the body first; the introduction
  and conclusion come last, once we can assess what the body shows.
- **Deferred runs (user, 2026-10-21):** when a run is designed and scripted but deferred, put its predicted values in
  the manuscript in blue (`\synthetic{...}`), write the prose as if the run had finished, and add a `% SYNTHETIC`
  comment naming the run that replaces them. Replace them when the run is read.
- Commit to `main` in logical pieces. Do not push unless asked.
- Changes to the thrember-derived `features.py` are pure additions; the original lines stay untouched.
- **No result may rest on an implementation quirk of the extractor** (user, 2026-10-22). Patch the quirk as a pure
  addition (e.g., `merge_import_descriptors` for the duplicate-DLL import overwrite), run every row on the patched
  variant, and note it in `docs/upstream-issues.md`.

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

- In the EMBER code, elements are bytes and feature sets record raw contributions (`Contributions.add_item` already
  spreads each item over its bytes; the item layer of the new model is implicit there). `Provenance` normalizes
  lazily.
- Features with no contributions go to the null element (`empty="null"`, the default; `uniform`/`ignore` also exist).
- All explainers attribute the malware log-odds (GBDT raw score; logit₁ − logit₀ for neural networks).
- **The domain is adversarial examples in practical security tasks** (user, 2026-11-02; settled, do not reopen). The
  core framework is as agnostic as Pierazzi et al.'s: it depends only on elements, items, sums, and readouts, never on
  what they mean, and should apply to as many kinds of malware and security domains as possible (executables, apps,
  documents, traffic, ...). PE malware detection is the user's expertise and the primary inspiration, guidance, and
  experimental instance; other domains are breadth. PE specifics are allowed where they serve an experiment, never in
  the framework; format minutiae turn reviewers off.
- **Coverage, localizability, and the null element's share are not contributions** (old direction; still applies to
  explanation-style analyses).
- **Each application must cross the feature-problem gap in a way only feature provenance makes cheap**, against the
  realistic alternative a practitioner would use. Using provenance in both directions is a plus, not a requirement
  (relaxed 2026-10-22). Before any code for an application: the screening criteria, a mock of its paper table with the
  model component behind each column, and a falsifiable go/no-go check. A hand-built, format-specific mapping that
  takes tremendous manual effort is not a realistic alternative.
- **The GBDT is the first classifier we experiment with** (decided 2026-10-08). The framework stays general-purpose
  (P does not depend on the classifier). The MLP is set aside *temporarily*; do not describe it as dropped.
- **Experiments may use domain knowledge selectively** where it protects their integrity (decided 2026-10-07): e.g., a
  PE-aware perturbation operator or loader-safe edit rules. Keep it inside the experiment, say why it is needed, and
  never let it into the model.
