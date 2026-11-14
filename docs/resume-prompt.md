# Resume: the extractor audit pass (the scale-up's first work)

Written at the end of session 64 (2026-11-14). Self-contained: everything needed is below or in the files it names.

## The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input, add up what each contributes, compute each feature by a formula over a few totals. From the
instrumented extractor we compute what an attacker's edits do to the features: exactly for one edit (Proposition 1),
and as sound directions for a whole threat model (Theorem 1), from which come monotone detectors that no edit in the
threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. All pre-scale-up research is done; the
code was reorganized for the scale-up in session 64.

**Read first:** `CLAUDE.md`, `docs/status.md`, `PLAN.md` step 2c (the audit pass) and step 3 (d)-(f), then
`pipeline/README.md` (the stages, and which step produces each result of the paper).

## Where the code stands (session 64)

- `pipeline/<stage>/<step>/`: a thin command line next to a `run.sh` with a SLURM header (`sbatch` on the clusters,
  `bash` here, from the repository root); outputs under `artifacts/scaleup/<stage>/`; `pipeline/common.sh` sets the
  system, `NUM_WORKERS`, `OUT_ROOT`. Library code in `src/provexp/`; no script imports another. Detector names in
  `src/provexp/registry.py` (model set `pilot` only so far).
- `run.sh` exists for `2-features/featurize`, `3-directions/derived`, `1-audit/catalogue-checks`, `5-attacks/adaptive`,
  `5-attacks/mab-malware`. Every other step gets its `run.sh` when its protocol item is decided, following the same
  pattern (knobs as environment variables with the scale-up's defaults; echo each step and its log).
- After any code move, `pipeline/setup/identity_check.sh` must report no difference (~15-30 min).
- `run/` (steps 1-146) is the pilot's record; its scripts are at tag `pilot-final`.

## The rule for this and every later session (user, session 64)

Every number, table and example the paper reports comes from the scale-up: one protocol, the same files. Pilot runs are
for tests and explorations only. If an item is in the manuscript, it gets a scale-up step; if not, it stays at pilot
scale. Do not ask the user about this per item.

## This session: the audit pass

The only stage that can change the feature store, so it comes before any scale-up featurization (PLAN.md 2c, 3 (a)).

1. **The deviations table (Appendix D).** A deliberate pass over the extractor against the three principles of §6:
   every place where our extractor differs from EMBER v3 as released, why, and what it changes. Known entries: LIEF's
   overlay rule; the warnings dropped; thrember's quirks patched (`docs/upstream-issues.md`); files above 4 MB
   excluded; pefile's parser caps (an exactness gap near 8,192 imports, not a soundness hole;
   `docs/evidence/r7-overlay-rule.md` §10); the always-constant features. Look for further ones; propose the table to
   the user before writing it into the paper (small blocks; the `paper-prose` skill).
2. **The audit steps at scale**, each with its `run.sh` in `pipeline/1-audit/`: item checks, catalogue checks,
   population clauses, escapes, and (decided in session 64) the hand table with a count of the files that show each of
   its errors, and a new mode of the catalogue checks that chains edits (up to three added sections, then an append)
   with the item table carried forward: Appendix D's "combined edits are exact" rested on the removed A' code (run
   111). The file set: decide with the user (the pilot's checks ran on the 100 pilot files and on 2,000 test files,
   runs 117-118); estimate runtimes from the slowest case and hand long runs to the user.
3. Then, one at a time with the user, the remaining protocol items (malware count first; leave-one-out's cost joins
   it), then a session on the cluster's head node.

## Noted for later (not this session unless needed)

- Duplicate code to merge under the identity check: the two section/import writers (`featuresets/ember2024/edits.py`
  and `attacks/adaptive.py`), the operation tuples in `attacks/adaptive.py` and `featuresets/ember2024/directions.py`.
- Featurization as a SLURM job array needs a step that creates the store before the array's tasks write into it.
- `features.py` has one stale path in a comment (`scripts/item_checks.py`); kept so the file's hash matches the stored
  feature stores' manifests.
- The cluster values in `pipeline/systems/{sporc,tigris}.sh` are marked "TO CONFIRM" (cores per node, output storage,
  walltime, Python 3.14 through uv, libmagic, torch's aarch64 wheels on tigris).

At the end of the session: update `docs/status.md` and PLAN.md; write the next resume prompt (archive this one).
