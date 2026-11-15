# Resume: the audit pass's decisions, then the extractor fix and the deviations table

Written at the end of session 65 (2026-11-14). The user was away for most of that session and asked for everything that
needed no decision to be done. This prompt is self-contained: what the project is, where things stand, the rules that
apply, and what this session does, step by step. Files are named for detail, but only `CLAUDE.md` (loaded
automatically) needs reading first.

## 1. The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find the
pieces of the input (items), add up what each contributes (sums), compute each feature by a formula over a few totals
(readouts). From the instrumented extractor we compute what an attacker's edits do to the features: exactly for one
edit (Proposition 1), as sound directions for a whole threat model (Theorem 1: for each feature, whether some edit
can raise it, lower it, or neither), and from those, monotone detectors no edit in the threat model can evade
(Corollary 1). PE malware on EMBER2024 is the instance. The paper (`manuscript/*.tex`, ACM CCS format) is drafted on
pilot-scale results (100 pilot files, one seed). The next big step is the **scale-up** (PLAN.md step 3) on the
user's SLURM clusters, which replaces every number in the paper.

## 2. Where things stand

- **Session 64** reorganized the code for the scale-up: library code in `src/provexp/`, the experiments in `pipeline/`
  (numbered stages, one step per folder, a `run.sh` with a SLURM header next to a thin Python command line),
  checked byte-identical to the old code (`pipeline/setup/identity_check.sh`).
- **Session 65 did the extractor audit pass** (record: `docs/evidence/extractor-audit.md`). The audit is the only part
  of the scale-up that can change the feature store, so it has to be settled before the scale-up's featurization. The
  pass read all of thrember's extractor (EMBER v3's, which ours is) and the pefile rules its features rest on, against
  three principles: (1) structures are located as the loader locates them; (2) features describe the file, not the
  parser's diagnostics; (3) known aggregation bugs are fixed. Each candidate was counted on the 2,000 test files
  (`artifacts/explanation_set/ts.parquet`, which include the 100 pilot files; 1,674 are in the population, i.e. the
  complete files with a plain layout the guarantee covers).
- **Also done in session 65, without needing a decision** (commits 4458d06, 1b12cbc, 8e8f8ca and a docs commit):
  - `run.sh` for every audit step in `pipeline/1-audit/` (item-checks, catalogue-checks, population, escapes,
    hand-table, and a new `deviations` step), smoke-tested end to end on six pilot files: every check passes. The
    file list is a required knob, `FILES`, because it is still undecided (step 3 below).
  - The two additions agreed in session 64: a chained-edit mode of the catalogue checks
    (`catalogue_checks.py --chained`: three added sections then an append, each predicted from the previous step's
    predicted item table, never re-extracted; the run.sh runs it as a second pass), and Table 3's witness counts
    (`hand-table/witness_counts.py`: for each error of the hand-written table, the files where a real edit shows it,
    in the population and outside it; it reproduces Table 3's 650, 151 and 37 from the pilot-era outputs).
  - `1-audit/deviations` (module `provexp.featuresets.ember2024.deviations`): per file, which of our deviations from
    EMBER v3 and which parser heuristics apply; the counts for the deviations table.
  - A crash fixed: the escape audit aborted on a pilot file because pefile's `PE.write()` rewrote ~40 bytes no write
    had touched. The writes now patch their one field directly; on run 137's 150 files all 900 writes are
    byte-identical to before.
  - Drafts of two upstream issues (`docs/upstream-issues.md` items 11-12).

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- Every result the paper reports comes from the scale-up (one protocol, the same files); pilot runs are for tests and
  explorations only. This rule decides by itself; do not ask the user about it per item.
- Explain plainly: what is computed, what it is compared with, why it matters; no internal labels without saying what
  they are; when citing an earlier decision, restate the decision itself.
- State a hypothesis (a sentence or two) before running anything; report a failed check as such.
- Run yourself only jobs of about 10 minutes or less, estimated from the slowest case; otherwise smoke-test and hand
  the user a `run.sh`. Normal priority, no `nice`. (Session 65's estimate for its first measurement was wrong: the
  machine was loaded and a regex of mine was quadratic. Estimate from the slowest file.)
- No result may rest on an implementation quirk of the extractor; changes to the thrember-derived `features.py` are
  pure additions (a subclass and an installer, like `ImportsInfoMerged` / `merge_import_descriptors`). The parser is
  not the gold standard.
- Paper text: straight into `.tex`, in small blocks the user reviews, with the `paper-prose` skill; table numbers from
  `manuscript/main.aux`. Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass);
  do not push.

## 4. This session

**Step 1: the user decides the five candidates** (`docs/evidence/extractor-audit.md` §2; open with the plain summary
below, then go one at a time, and record each decision in that file and PLAN.md step 2c):

1. *The directory off-by-one* (principle 3). thrember skips the last data directory it reads, meaning to skip the
   16th, always-empty "reserved" one. A file that declares fewer than 16 directories loses a real one: 11 .NET
   programs with 15 directories lose their CLR header (the COM descriptor), 2 files with 3 lose their resources. 13
   files, 11 in the population. **Recommended: fix** (skip the reserved entry by name), the same kind of bug as the
   import overwrite we already fix.
2. *The entry section on files whose sections are not aligned* (principle 1). pefile rounds a section's address down
   to the alignment, finds no section holding the entry point, and thrember falls back to the first executable
   section. 3 files, all in the population, each with a tiny injected entry section (e.g. `ba37125a...`: pefile gives
   `UPX0`, the section's own extent gives `Entry1`). **Recommended: keep and list it** (no clean loader rule to
   adopt; the loader probably rejects such files, unverified). Alternatives: LIEF's view (the section's own extent),
   or a population clause excluding them.
3. *Alignment bits read as several flags* (principle 2). 59 files (45 in the population). **Recommended: keep**: a
   fixed function of one field of the file, so it still describes the file.
4. *pefile's early stops in imports and exports.* Export names lost on 10 files (4 in the population); on 1 file in
   the population pefile read 1,143 of 1,738 imports. **Recommended: list with the parser caps, no change.**
5. *Typos in thrember's string patterns.* `email_addr` repeats `mac_addr`'s pattern; `registry_key` misspells
   `HKEY_`/`HKLM` (93 files contain them). **Recommended: keep v3's definitions and report upstream**; alternative:
   fix `registry_key` alone (v2 had it right).

**Step 2: the deviations table.** Propose the table of §3 of the record (adjusted to the decisions) to the user, then
write it into Appendix D (`manuscript/_j2_ember.tex`) in small blocks with the `paper-prose` skill, with one short
paragraph: our extractor is EMBER v3's with the changes listed, each for one of three reasons. Counts in the table come
from `1-audit/deviations` at the scale-up; until then, blue (`\synthetic{}`) with a `% SYNTHETIC` comment naming the
step. §4's prose (`_e_instances.tex`, around "We drop the warnings" and the overlay rule) may point to the table.

**Step 3: the audit's file list** (`FILES` in every `pipeline/1-audit/*/run.sh`). One protocol, the same files: most
naturally the scale-up's evaluation files, so decide it together with the malware count (the first remaining protocol
item, PLAN.md step 3, with leave-one-out's cost). The pilot checks used the 100 pilot files and the 2,000 test files.
Cost at 2,000 files: catalogue checks ~36 min (plus ~5 min for the chains), item checks ~1-1.5 h (57 min at 24 workers), the
rest minutes. The overlay and signature witnesses run in one process.

**Step 4: if the user approves a change to `features.py`** (1, or 2/5's alternatives): implement it as a pure
addition with its instrumentation and tests, regenerate `pipeline/setup/reference/` (`make_fixtures.py`,
`check_reference.py`), fix the stale `scripts/item_checks.py` path in the `features.py` comment in the same change (the
file's hash changes anyway), and run the identity check expecting differences in exactly the changed features. Then
`check.sh` and the full test suite (`env/bin/pytest -n 16 tests`, ~4 min).

**Then**, one at a time with the user: the remaining protocol items (PLAN.md step 3), then a session on a cluster head
node (`SETUP.md`, `check.sh`, the "TO CONFIRM" values; sporc first).

## 5. Noted for later (not this session unless it becomes necessary)

- Duplicate code to merge, under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- Featurization as a SLURM job array needs a step that creates the feature store before the tasks write into it.
- The registry has only the `pilot` model set; the scale-up adds `scaleup` (`artifacts/scaleup/4-detectors/<name>`).
- Witness counts vs Table 3: on pilot-era outputs the counts give overlay/append 8 (Table 3: 4/100) and section
  entropy/header 5 (4/2,000), both outside the population; the scale-up's counts replace them anyway.
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.

## 6. At the end of the session

Update `docs/status.md` (current state, waiting on the user, a session-log entry; archive the oldest entries past about
ten) and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one as
`docs/archive/resume-prompt-2026-11-14-s66.md` (or the session's date), with its line in `docs/README.md`.
