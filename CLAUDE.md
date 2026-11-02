# ProvExp

Dissertation research: **feature provenance in malware classification** (restarted 2026-10-22). Instrumenting a
feature extractor records which problem-space elements (bytes, characters, tokens, ...) produce which features,
through which items; this bridges the feature-problem space gap: what an attacker's edits can reach in feature space
(side effects, coupling, reachable directions and regions), computed instead of found by hand, from data, or by running
transformations. Model: `docs/feature-provenance-model.md`. The previous direction (explanation provenance: pullback
b = Pa and pushforward a = PᵀD†b of explanations) was abandoned on 2026-10-22 (`docs/graveyard.md`); its code, data,
and manuscript remain as source material. Deadlines and conference cycles are not a planning constraint (user).

## Read first

- `docs/status.md`: current state, what is waiting on the user, and what to do next. **Update it at the end of
  every session.** `docs/resume-prompt.md`: where to pick up next.
- `PLAN.md`: thesis, the model, directions A (core), B, C, next steps, settled decisions.
- `docs/formalization.md`: the formal model (current work; three running domains: EMBER, Drebin, CICFlowMeter) and
  `docs/feedback.md`, the user's review log for it (one item per point; apply in one pass when a round ends).
- `docs/feature-provenance-model.md` (the three-layer model, claims C1-C4 with proof sketches and assumptions A1-A4,
  worked example, coverage of real transformations) and `docs/literature-2026-10-22.md` (related work for the new
  direction). Be harsh about our own novelty: read the closest work on the same *task* before building (user,
  2026-10-22).
- Direction A: `docs/direction-A-summary.md` (where A stands at pilot scale: checks, mock vs measured, gaps; read
  this first), `docs/direction-A-mock.md` (the target tables, baselines, go/no-go checks),
  `docs/direction-A-threat-model.md` (threat models M_add / M_shift / M_full, the direction table and re-encodings,
  Table A0 in S6), and `docs/direction-A-A1-design.md` (Table A1/A2 design, decisions, and results).
  `docs/upstream-issues.md`: thrember (and secml-malware) bugs for the user to report upstream.
- Direction A' (realizable worst-case evaluation with an exact solver) was **dropped on 2026-11-02**
  (`docs/graveyard.md`; record: `docs/direction-A-prime-plan.md`, Section 13); two pieces fold into A. Its documents
  (`docs/direction-A-prime-plan.md`, `docs/direction-A-prime-mock.md`, `docs/literature-Aprime-2026-10-27.md`) and code
  (`scripts/ap_*`) remain as source material. The automatic derivation A rests on: `docs/item-layer-design.md`. The
  expert-set row: `docs/direction-A-expert-set.md`.
- `docs/graveyard.md`: ideas and directions that did not pan out and why.
- Old direction, for reference only: `docs/archive/PLAN-explanation-provenance-2026-10-21.md`, `docs/experiments/`
  (cp, pb1, pf1, trigger, cm, audit), `docs/theory.md`, `docs/appendix.md`, `docs/related_work.md`,
  `docs/review-prompt.md`, the manuscript under `manuscript/`, `REVIEW-2026-10-21.md`. Some artifact paths use
  retired IDs (e.g. `artifacts/experiments/e1/` is PB1). `docs/design.md` (package design, provenance conventions,
  thrember quirks) and `docs/style_guide.md` still apply.
- **State a hypothesis before running an experiment** (what you expect and why), and report a failed check as such.
  Keep it short and proportionate: a sentence or two, not an elaborate pre-registered reading for every outcome
  (user, 2026-10-09).
- The manuscript is being rewritten (user, 2026-11-02): the framework section goes straight into `.tex`
  (`manuscript/`), drafted from a paper mock to a word budget (about 2,500 words); no new markdown drafts of paper
  text. `docs/formalization.md` is frozen as the reference and appendix source. Other sections stay untouched until
  their turn. Write continuous prose rather than stacks of labeled paragraphs (user, 2026-10-14); no internal IDs in
  the paper.
- `src/provexp/`: `boxmatrix.py` (sparse boxes), `provenance.py` (P, transfers, statistics, round trips), `items.py`
  (the item layer: items, terms, readouts as data, projection), `reach.py` (the C1 and C4 engines),
  `featuresets/ember2024/catalogue.py` (the edit catalogue: add_section, the operations as C4 changes, the
  precondition check with its plain-layout clauses), `featuresets/ember2024/expert.py` (Gimenez et al.'s 40 features,
  quirks patched: the expert-set row),
  `featuresets/ember2024/features.py` (thrember + provenance), `data/` (SimpleDB, feature store, TLSH),
  `models/` (GBDT, MLP, MalConv), `explain/` (feature- and problem-space explainers), `ablation.py` (generic
  ablation, budgets, black-box provenance, coarsening), `featuresets/ember2024/ablation.py` (PE-aware protection and
  verification, experiment code), `metrics.py`.
- `scripts/`: data (featurize, check_features, build_metadata, select_explanation_set, train_classic, make_fixtures);
  explanations and census (explain, provenance_census, pullback_agreement, pilot_tables); CP (cp_tables,
  cp_coarsening, cp_blackbox); PB1 (discover_protected_fields, header_typical_values, faithfulness, pb1_tables);
  the trigger (trigger_select, trigger_poison, trigger_validate, trigger_explain, trigger_tables); PF1 (pf1,
  pf1_resolution, pf_malconv); 3-A (cm_check, cm_shared, cm_triage, cm_tables); 3-C audit (audit_*, incl. audit_mitigate;
  cm_global); the manuscript's figure data (paper_figures -> `manuscript/assets/data/`); shared
  discovery/transplant machinery (shortcuts, shortcuts_transplant). Direction A: a_directions (C4 directions per
  threat model; derived from the item tables by default, `--hand` for the hand rules), a_c1_table0 (hand C1 predictors, the engine's oracle, and Table A0), a_pv_attacks / a_pv_hole (secml-malware attacks, PV
  selection and its hole), a1_evaluate (toolkit columns), a1_adaptive (C1-guided adaptive search), a_overlay_witness
  (the overlay gap), a_signature_witness (the signature table past the end), a_structure_witness (the other class-1 witnesses: entry section, Rich header, exports and relocations past the end), item_checks (derivation checks G1/G2, G5, G6), catalogue_checks (G7: every operation applied by our own byte-level edits, checked
  against the derived directions). Direction A' (dropped; kept as source material): ap_check0_solver (Kantchelian's exact GBDT encoding, HiGHS via scipy), ap_check1_learned (learned
  regions), ap_encoding (the edit-choice encoding: append + up to 3 added sections), ap_containment (it must contain
  every real edit; run 111), ap_check1b (certification; run 112), ap_realize (a solver answer written as a file), ap_bracket (the adopted plan's
  bracket per detector and edit family: solver floor, real-attack ceiling; run 114). The sums
  re-encoding is `src/provexp/featuresets/ember2024/sums.py`. Dropped experiments are under `scripts/archive/`.
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
  the user's jobs run) without asking. Run yourself only jobs estimated at **~10 minutes or less**, estimating from
  the slowest case (user, 2026-10-26); otherwise smoke-test on a small slice and give the user a `run/` script.
- **Resources in `run/` scripts:** default to at most 16 workers or threads and 2 GPUs (the user cut runs 38-40 down
  to these, 2026-10-12); the user may raise them, so never enforce the cap in Python (2026-10-26).
  Never edit a `run/` script while it runs (bash reads it as it goes); sync its comments afterwards.
- **Explain plainly.** Lead with the plain-language version of an argument (what is computed, what it is compared
  with, why it matters); define terms and avoid dense shorthand. The user could not follow a jargon-heavy explanation
  (2026-10-12).
- Light checks: `OMP_NUM_THREADS=2 nice -n 10 env/bin/pytest -q -p no:xdist tests/test_<module>.py`.
  Full suite: `env/bin/pytest -n 16 tests` (~4 min).
- Before committing: `env/bin/ruff check src tests scripts` and `env/bin/mypy src tests scripts` (strict) must pass.
- **Compile the manuscript with `make` in `manuscript/`** (user-space TeX Live in `~/texlive`, latexmk + pdflatex).
  `main.tex` is the complete document (ACM `acmart` `sigconf`, the CCS format; do not change fonts, margins, or spacing) and
  `\input`s the section fragments. After editing, run `make` and `make check` (undefined refs/citations, overfull boxes).
- **Early drafting stage (user, 2026-10-14):** (1) exceeding the page limit does not matter yet; do not cut or compress
  text to fit. (2) Exact numbers in the prose are of little concern, since experiments will be re-run and more data
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
