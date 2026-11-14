# Resume: the extractor audit pass, the scale-up's first work

Written at the end of session 64 (2026-11-14), the refactoring session. Self-contained: what the project is, where the
code and the paper stand, the rules that apply, and what this session does, step by step. Files are named for detail,
but nothing below requires reading them first except `CLAUDE.md` (loaded automatically).

## 1. The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input (items), add up what each contributes (sums), compute each feature by a formula over a few totals
(readouts). From the instrumented extractor we compute what an attacker's edits do to the features:

- **exactly for one edit** (Proposition 1, "side effects");
- **as sound directions for a whole threat model** (Theorem 1): for each feature, whether any edit in the threat model
  can raise it, lower it, or neither;
- and from those, **monotone detectors** no edit in the threat model can evade (Corollary 1): a GBDT constrained to be
  non-decreasing in every feature an attacker can only raise, and blind to features an attacker can lower.

PE malware on EMBER2024 is the instance. The paper (`manuscript/*.tex`, ACM CCS format) has the framework (§2-3), the
EMBER instance (§4), the evaluation as three findings (§5), and Appendix D (the instance's details). Its body is drafted
on **pilot-scale** results (100 pilot files, 50 malware and 50 goodware; one seed). The next big step is the
**scale-up** (PLAN.md step 3) on the user's SLURM clusters, which replaces every number in the paper.

## 2. What session 64 did: the code reorganized for the scale-up

Four commits (b223fcd, 185212e, 3a6fba2, 1076878):

- **Dead code removed:** the old explanation direction's 49 scripts and modules, the dropped A' encoding (`ap_*`),
  their tests. Tag `pilot-final` is the last commit with everything. `run/` (steps 1-146) is now a historical record:
  its scripts call the old `scripts/`, re-runnable at that tag.
- **Library code in `src/provexp/`**, so no script imports another: `attacks/{toolkit,adaptive,mab}.py`,
  `detectors.py`, `parallel.py`, `data/files.py`, `featuresets/ember2024/{edits,escapes,population,directions,hand}.py`,
  next to the existing `items.py` (the item layer), `reach.py` (the side-effect and direction engines),
  `featuresets/ember2024/{features,catalogue,sums,expert}.py`. `provexp.registry` holds plain names for the detectors
  (`unconstrained`, `monotone-features`, `monotone-sums`, `additions-only`, `adversarial-training`, `pv`, `erdalt`,
  `expert-set`, `trial`; model set `pilot` only so far) and attacks.
- **`pipeline/`**: stages `setup/`, `1-audit/`, `2-features/`, `3-directions/`, `4-detectors/`, `5-attacks/`,
  `6-results/`, one step per subfolder: a thin command-line Python file next to a `run.sh` whose `#SBATCH` header makes
  it `sbatch`-able on the clusters and `bash`-able here, always from the repository root. `pipeline/common.sh` detects
  the system (`pipeline/systems/{local,sporc,tigris}.sh`; cluster values marked "TO CONFIRM"), sets `NUM_WORKERS` (16
  here), `OUT_ROOT` (default `artifacts/scaleup`), `PYTHONHASHSEED=0`. `run.sh` exists so far for
  `2-features/featurize`, `3-directions/derived`, `1-audit/catalogue-checks`, `5-attacks/adaptive`,
  `5-attacks/mab-malware`; every other step gets its `run.sh` when its protocol item is decided, in the same pattern
  (knobs as environment variables with the scale-up's defaults; `echo` each step and its log; one argument per line).
- **`pipeline/README.md`** maps every result of the paper (tables and sections) to the step that produces it at scale.
- **`SETUP.md`**, `pipeline/setup/build_env.sh` (env from `requirements-lock.txt`), `pipeline/setup/check.sh`
  (dataset found; featurization bit-identical on 32 test files to `pipeline/setup/reference/`; the tests).
- **Checked:** `pipeline/setup/identity_check.sh` runs five computations on a pilot slice (featurization with the three
  extractors, the strict and loose direction tables, a catalogue check, two extraction-scored adaptive searches,
  MAB-Malware) and compares them with the old code's outputs (run 146): all 61 output files identical except timing
  fields and the commit the feature manifests record. Tests: 1,572 passed. **After any future code move, this check
  must report no difference** (~15-30 min).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- **Every result the paper reports comes from the scale-up** (session 64): one protocol, the same files. Pilot runs are
  for tests and explorations only. If an item is in the manuscript it gets a scale-up step; if not, it stays at pilot
  scale. This rule decides by itself: do not ask the user about it per item.
- Explain plainly: what is computed, what it is compared with, why it matters; no internal labels without saying what
  they are; when citing an earlier decision, restate the decision itself, not "your decision in session N".
- State a hypothesis (a sentence or two) before running anything; report a failed check as such.
- Run yourself only jobs of about 10 minutes or less, estimated from the slowest case; otherwise smoke-test on a small
  slice and hand the user a `run.sh`. Normal priority, no `nice`.
- No result may rest on an implementation quirk of the extractor; patches to the thrember-derived `features.py` are
  pure additions. The parser is not the gold standard: what a structure is must not hang on one parser's implementation.
- Paper text: straight into `.tex`, in small blocks the user reviews, with the `paper-prose` skill; table numbers from
  `manuscript/main.aux`. Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass);
  do not push.

## 4. This session: the extractor audit pass

**Why first.** It is the only part of the scale-up that can change the feature store (PLAN.md step 2c and step 3 (a)),
so it must be finished before any scale-up featurization; afterwards, every change reruns everything.

**Background.** In session 62 the user decided to stay on pefile (the parser behind thrember, EMBER v3's extractor)
rather than move to LIEF: on the 100 pilot files both parsers find the same structures on 99 (the one difference is
pefile's cap of 8,192 imports), and parsing is only ~12-25% of our per-file time. Our extractor already deviates from
EMBER v3 as released in a few places, each found reactively. The audit pass replaces that with one deliberate pass and
a **deviations table in Appendix D**, each deviation justified by one of three principles (recorded in
`docs/evidence/r7-overlay-rule.md` §6):

1. **Structures are located as the loader locates them** (e.g., the overlay is the file's unmapped tail).
2. **Features describe the file, not the parser's diagnostics** (pefile's warnings are dropped).
3. **Known aggregation bugs are fixed** (e.g., the import merge: thrember lets a repeated DLL's descriptor overwrite the
   earlier one's functions).

The 4 MB restriction (files our copy of EMBER2024 holds in full, below 4,000,000 bytes) is sample selection, listed
apart. Why the table matters: part of the paper's credibility is that it analyses an extractor someone else designed;
"inspired by" invites "did you design the features to suit your guarantees?". Staying close to v3 and justifying every
deviation once answers it, together with the unconstrained detector's accuracy matching v3's.

**Known entries** (sources in parentheses):

- LIEF's overlay rule installed in pefile at import: the overlay starts after the last section's raw data, not where
  data-directory extents end (principle 1; `docs/evidence/r7-overlay-rule.md`, `docs/upstream-issues.md` item 9).
- pefile's warnings dropped from the model (principle 2).
- thrember's quirks patched: the duplicate-DLL import overwrite (principle 3; `docs/upstream-issues.md` item 1), and a
  guard so that a crash in one directory's parser (e.g., a malformed debug directory) loses only that directory instead
  of turning the whole file into a non-PE (item 5).
- pefile's defensive parser caps (e.g., 8,192 imports): an exactness gap near a cap, not a soundness hole; not modeled
  (`docs/upstream-issues.md` item 10, `r7-overlay-rule.md` §10).
- Features constant on every file (`docs/upstream-issues.md` items 2-3).
- Files above 4 MB excluded (sample selection).

**Steps:**

1. **The pass itself.** Go through `src/provexp/featuresets/ember2024/features.py` (2,922 lines; thrember's original
   lines untouched, our instrumentation and patches added) group by group, against the three principles: where does a
   feature depend on the parser's heuristics rather than the file, or on an aggregation bug? Compare with EMBER v2 and v3
   and with how the loader reads the structure where it matters. List candidates with a concrete example each and what
   changing them would change; the user decides each one. Then propose the deviations table to the user before writing
   it into Appendix D (small blocks, `paper-prose` skill).
2. **The audit steps at scale**, each with its `run.sh` in `pipeline/1-audit/` (pattern of
   `pipeline/1-audit/catalogue-checks/run.sh`). Pilot timings, for estimates (16 workers):

   | Step | What it checks | Pilot runs and time | Paper |
   |---|---|---|---|
   | `item-checks/` | the item layer reads out every feature bit for bit; single-byte flips; random writes | runs 90-96, 118 (57 min on 2,000 files at 24 workers) | Table 9, §5.1 |
   | `catalogue-checks/` | every operation by our own byte edits: sound (directions), closed (population), exact | runs 107, 117 (36 min, 2,000 files), 142 (~30 min, 100 files, loose) | §4.4, §5.1, Table 9 |
   | `population/` | which population clause each file fails | run 136 (~3 min) | §4.4, §5.4 |
   | `escapes/` | which single field writes outside the threat model take a file out of the population | run 137 (~1 min) | §5.4 |
   | `hand-table/` | the hand-written side-effect rules against re-extraction; files showing each error | runs 88, 92, 98, 101 (2-14 min, 100 files) | §5.2, Table 3 |

   Two additions decided in session 64: the hand table at scale **with a count of the files that show each of its
   errors** (the witnesses become counts), and **a chained-edit mode of the catalogue checks** (up to three added
   sections, then an append, with the item table carried forward one edit at a time): Appendix D says such combined
   edits are exact, and that rested on the A' code removed in session 64 (run 111).
   **The file set needs a decision with the user**: the pilot checks ran on the 100 pilot files
   (`artifacts/experiments/e1/seed-0/zeros/files.parquet`) and on 2,000 test files (`artifacts/explanation_set/ts.parquet`,
   runs 117-118); the scale-up's files are part of the protocol (one protocol, the same files everywhere).
3. **Then**, one at a time with the user: the remaining protocol items (PLAN.md step 3; the malware count first, with
   leave-one-out's cost joining it), then a session on a cluster head node (`SETUP.md`, `check.sh`, the "TO CONFIRM"
   values; sporc first, tigris only after `check.sh` is bit-identical there).

## 5. Noted for later (not this session unless it becomes necessary)

- Duplicate code to merge, under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- Featurization as a SLURM job array needs a step that creates the feature store before the tasks write into it.
- `features.py` has one stale path in a comment (`scripts/item_checks.py`), kept so the file's hash matches the stored
  feature stores' manifests; fix it with the scale-up's featurization.
- The registry has only the `pilot` model set; the scale-up adds `scaleup` (`artifacts/scaleup/4-detectors/<name>`).

## 6. At the end of the session

Update `docs/status.md` (current state, waiting on the user, a session-log entry; archive the oldest entries past about
ten) and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one as
`docs/archive/resume-prompt-2026-11-14-s65.md` (or the session's date), with its line in `docs/README.md`.
