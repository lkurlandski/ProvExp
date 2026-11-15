# Resume: the scale-up's protocol, starting with the malware count and the audit's file list

Written at the end of session 66 (2026-11-15). This prompt is self-contained: what the project is, where things stand,
the rules that apply, and what this session does. Files are named for detail, but only `CLAUDE.md` (loaded
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
  (numbered stages, one step per folder, a `run.sh` with a SLURM header next to a thin Python command line).
- **Sessions 65-66: the extractor audit is finished** (`docs/evidence/extractor-audit.md`). Its only possible effect
  on the feature store, two fixes, is now in the code, so the scale-up's featurization can use the extractor as it is:
  - Fixed (user's decisions, session 66), as pure additions in `features.py`: thrember's directory loop skipped the
    last directory a file declares instead of the reserved 16th one (`DataDirectoriesReserved`), and three string
    patterns were typos (`registry_key` searched `KHEY_`, `email_addr` repeated the MAC-address pattern, `.click(` was
    unescaped; `StringExtractorFixed`, v3's feature names kept). `fix_quirks(extractor)` installs both together with
    the merged import descriptors; it replaced `merge_import_descriptors(...)` everywhere the patched extractor is
    built, and `SumsFeatureExtractor` uses it. Plain `PEFeatureExtractor()` still computes EMBER v3's released vectors.
  - Kept and listed: the entry section on files whose sections are not aligned, alignment bits read as several flags,
    pefile's limits on imports and exports.
  - Appendix D now opens with *Changes to EMBER* and Table 8 (each change with its reason and the files it affects);
    the counts are on the 2,000 test files, blue (`\synthetic{}`) until `pipeline/1-audit/deviations` runs at the
    scale-up.
  - The identity check (`pipeline/setup/identity_check.sh`) now differs from run 146's outputs in exactly the fixed
    features (noted in `pipeline/setup/README.md`); the reference fixtures were regenerated.
- **What every `1-audit` step still waits for: its file list** (`FILES`, a required knob of each
  `pipeline/1-audit/*/run.sh`). That is this session's first decision, together with the malware count.

## 3. Rules that apply (from the user; also in CLAUDE.md and the memory)

- Every result the paper reports comes from the scale-up (one protocol, the same files); pilot runs are for tests and
  explorations only. This rule decides by itself; do not ask the user about it per item.
- One seed (0) until the methodology is final; spend compute on more samples (decided in session 63).
- Explain plainly: what is computed, what it is compared with, why it matters; no internal labels without saying what
  they are; when citing an earlier decision, restate the decision itself.
- State a hypothesis (a sentence or two) before running anything; report a failed check as such.
- Run yourself only jobs of about 10 minutes or less, estimated from the slowest case; otherwise smoke-test and hand
  the user a `run.sh`. Normal priority, no `nice`.
- Sizing: the user has shared SLURM clusters (hundreds of nodes like this server); this scale-up need not be the last
  or largest, so size it for days to a few weeks, not months.
- Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline` must pass); do not push.

## 4. This session: the protocol items, one at a time with the user

Each item is agreed before any code, and the steps it touches get the scale-up's arguments in their `run.sh` as it is
decided. Lay out each item plainly (what it decides, the options with their cost, a recommendation), then ask.

1. **The malware count and the audit's file list.** How many malware (and benign files) the scale-up evaluates on,
   from the files our copy holds in full (below 4 MB). Constraints on record (PLAN.md step 3): enough malware that PV
   and the expert set are not judged on 8-9 files (the pilot's weakness); the adaptive attack at 5,000
   extraction-scored candidates for every detector and escape costs ~3,000 CPU-h on 2,000 files (options on record:
   the 1,000-candidate checkpoint, a fixed subset, a cap on the monotone rows); leave-one-out (Table 10) runs at scale
   and its cost joins this budget. The audit's `FILES` are most naturally the same evaluation files (one protocol, the
   same files). Audit cost at 2,000 files: catalogue checks ~36 min plus ~5 min for chains, item checks ~1-1.5 h, the
   rest minutes. Estimate each cost from the pilot's per-file timings before proposing a number.
2. **Then, in order**, the rest of PLAN.md step 3 (each its own decision): one training set and one attack protocol
   for every detector (the pilot's adversarial-training detector read the plain, unpatched `ember2024` store; at the
   scale-up every detector reads the patched store); the trial row in Table 5; iterated adversarial training (two
   rounds of the beam, `ent` held out); MAB-Malware at our setting and at Zainab et al.'s; the escape attacks at scale;
   the reporting duties (the share of all attacked malware still detected; R12, R15, R3); the recounts behind the
   R7 blue values and PROTOCOL notes.
3. **Then** a session on a cluster head node (`SETUP.md`, `check.sh`, the "TO CONFIRM" values; sporc first).

## 5. Noted for later (not this session unless it becomes necessary)

- Duplicate code to merge, under the identity check: the section and import writers in
  `featuresets/ember2024/edits.py` and `attacks/adaptive.py`; the operation tuples in `attacks/adaptive.py` and
  `featuresets/ember2024/directions.py`.
- Featurization as a SLURM job array needs a step that creates the feature store before the tasks write into it.
- The registry has only the `pilot` model set; the scale-up adds `scaleup` (`artifacts/scaleup/4-detectors/<name>`).
- EMBER v2's handling of the directories and the entry section is stated from memory in the audit record; verify
  against `elastic/ember`'s `features.py` before the paper cites v2 for either.
- `import_stopped` (pefile's stop after repeated import errors) fires on 26 of the 2,000 test files; on most of them
  pefile still reads what LIEF reads. Table 8 counts files where a limit applies, not files that lose imports.

## 6. At the end of the session

Update `docs/status.md` (current state, waiting on the user, a session-log entry; archive the oldest entries past about
ten) and PLAN.md; write the next resume prompt, self-contained like this one, and archive this one as
`docs/archive/resume-prompt-<date>-s67.md`, with its line in `docs/README.md`.
