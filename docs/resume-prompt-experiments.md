# Resume: the scale-up's experiments (GAMMA's evasions of the guaranteed detectors first, then PV's setup and the results)

Written at the end of session 100 (2026-11-20, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs
reading first. **This session runs on the cluster's interactive partition** (the user's choice): small tests and
diagnostics run directly in the allocation, not through `sbatch`. Other tracks: `docs/resume-prompt-writing.md`,
`docs/resume-prompt-theory.md`, `docs/resume-prompt.md` (general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`, items
(1)-(17)) replaces every number. Detectors: unconstrained, monotone-features, monotone-sums (the two guaranteed ones),
additions-only, adversarial-training, pv, trial, iterated-2 (learned from attack outputs or trial edits), and ERDALT
(Gimenez et al.'s learned defense). Attacks: Gimenez et al.'s eight secml-malware attacks (the "toolkit"), our adaptive
search, MAB-Malware. Every output counts only under one validity rule (pefile and LIEF both read it, neither loses a
section or an import; `src/provexp/attacks/validity.py`).

## 2. Where things stand

**Every detector but ERDALT has been retrained and attacked on the new material** (session 85's chain,
`logs/submit-20261118-s85.txt`, all COMPLETED 2026-11-18). **None of it has been read with the user.** Claude's quick
tally (session 94), evaded / detected of 1,000 test malware at 1% FPR:

| detector | toolkit (main) | adaptive (none) | MAB-Malware ours |
|---|---|---|---|
| unconstrained | 598 / 953 | 932 / 953 | 68 / 953 |
| monotone-features | **3** / 803 | 0 / 803 | 0 / 803 |
| monotone-sums | **1** / 802 | 0 / 802 | 0 / 802 |
| additions-only | 129 / 917 | 901 / 917 | 6 / 917 |
| adversarial-training | 46 / 959 | 934 / 959 | 15 / 959 |
| pv | 0 / 234 | 51 / 234 | 10 / 234 |
| trial | 187 / 876 | 623 / 876 | 192 / 876 |
| iterated-2 | 36 / 958 | 922 / 958 | 50 / 958 |

PV keeps 1,359 features (78,715 vectors), validation AUC 0.924, test 0.930. Unread: the toolkit's `escape` and `loo`
parts, the adaptive search's escapes and `expert`, MAB `expert` and `zainab` (against Zainab et al.'s 83%), every
validity count.

**ERDALT is settled** (session 100; record `docs/erdalt-diagnosis-plan.md`, last section). Retrained with every setting
rescaled to its authors' setup: validation AUC 0.978, test 0.981, but its criterion was not met (kept epoch 64: 35,594
violated entries against the rescaled limit of 381, i.e. 0.018% of 202M entries; still falling slowly). The user kept
these settings and released the eight leave-one-out folds (job **1239350**, tasks 1-8, ~6.7 h each on one GPU; task 1
started 2026-11-20). Appendix D states each rescaling and the measured trade-off (their literal penalty weight: 769
violations at 0.914).

**The guaranteed detectors' toolkit evasions, located in session 100** (`artifacts/scaleup/5-attacks/toolkit/main/
<detector>/results.parquet`, `evaded` true). All four come from the two GAMMA attacks, which rebuild the file through
LIEF; all four pass the validity rule:

| detector | attack | file (sha256) | p clean -> adv (tau) | bytes added | precondition |
|---|---|---|---|---|---|
| monotone-features | gamma_sections | `714d2a7d4f7dc0201091e513d96bd3fcb23fa8ee121627d15d937edee0796673` | 0.904 -> 0.789 (0.806) | 466,944 | yes |
| monotone-features | gamma_api | `34089080d7936df5e3c6b88688a674611eeb6aac9ea73797922f9e79d5fb6a65` | 0.951 -> 0.790 (0.806) | 40,960 | yes |
| monotone-features | gamma_api | `eb61a5bdcdea1285362dada9a618ab33bd174216a5b30d96fd383798daacdc50` | 0.964 -> 0.791 (0.806) | 50,688 | **no** (outside the guarantee) |
| monotone-sums | gamma_sections | `714d2a7d...` (same file) | 0.916 -> 0.785 (0.811) | 520,192 | yes |

So two files are open: `714d...` (gamma_sections, both detectors) and `3408...` (gamma_api, monotone-features).
Hypothesis (Claude's, unchecked): LIEF's rebuild changes more than the declared edit (rewritten headers, a moved or
dropped overlay, relaid sections), and one of those changes lowers a feature the derived table does not let an edit in
the threat model lower; the outputs then lie outside the threat model, not a soundness failure. **The user's view
(session 100):** rebuilding with LIEF can have unexpected consequences, which is why the adaptive search materializes
its edits with our own byte-level writers; the toolkit may need the same.

## 3. What this session does

0. **The allocation.** `scontrol show job $SLURM_JOB_ID` (cores, memory, GPUs, time limit); work only within it and set
   `NUM_WORKERS` to its cores. `squeue -u $USER` once: ERDALT's folds (1239350) should be running or queued; do not
   watch them.
1. **Reproduce the two open evasions and find what lowered the score** (a soundness failure would be the most serious
   finding of the scale-up, so check it on the file itself before anything else).
   - The attacked files were deleted after scoring (`pipeline/5-attacks/toolkit/toolkit.py`, the `finally:
     out_path.unlink(...)`). Add a pure-addition option (e.g. `--keep_outputs DIR`, default off) or a diagnostic
     script under `artifacts/scaleup/diag/gamma-evasion/` that calls the same functions. The per-file seed is
     `file_seed(0, attack, name)` (sha256 of `attack:name`, `src/provexp/attacks/toolkit.py:239`), so a run on a
     files list holding only these files reproduces the run; use the same donors (`2-features/files/tr-donors-1.parquet`)
     and the same detector models. `run.sh`'s `FILES` knob takes a files parquet (filter `2-features/files/ts.parquet`
     to the three names; include `eb61...` as a control). First check that p_adv matches the table above; if it does
     not, the reproduction is not faithful and nothing below holds.
   - For each output: re-extract (the sums store's extractor), list every feature that fell against the clean file,
     and for each such feature say whether the derived table allows an edit in the threat model to lower it. Run
     `lief_preserves(original, adv, op)` (`src/provexp/attacks/adaptive.py:201`: original section bodies, overlay, DOS
     header and stub, section names all kept) and check the output against the precondition
     (`provexp.detectors.precondition_holds`), and whether the rebuild alone (LIEF parse and write, no edit) already
     lowers the score.
   - Hypothesis to state before running: the falling features trace to LIEF's relayout (e.g. the overlay), not to the
     declared section or import addition.
   - Outcomes: (i) outside the threat model through LIEF's rebuild: then decide with the user how GAMMA's edits are
     materialized; (ii) a soundness failure (the declared edit alone lowers a feature the table says it cannot): stop
     and trace it in the derived table and `reach.py` before anything else.
2. **If (i): how the toolkit materializes GAMMA's edits (decide with the user; Claude recommends).** The adaptive
   search writes sections and imports with our byte-level writers (`catalogue.write_section`, `catalogue.write_imports`
   in `src/provexp/featuresets/ember2024/catalogue.py`; see the `# NOTE` in `adaptive.py`'s `_section`), and keeps a
   LIEF edit only when `lief_preserves` holds. Options: replace LIEF's rebuild in GAMMA by those writers (GAMMA's search
   unchanged, only how its chosen edit is written); or keep GAMMA as published and classify each output by whether it
   stays inside the threat model (counted apart, like `evaded_outside_population`). Weigh: fidelity to Gimenez et al.'s
   attacks against a clean claim for the guarantee; that the same GAMMA outputs are in **the defenses' material**
   (the vectors PV, ERDALT, adversarial-training and iterated-2 learn from), so a change reaches the learned detectors
   too, and the reruns it needs (toolkit, perhaps the material and every learned detector: hours to a day, the user's
   call). Code changes go in a `git worktree` first (`PYTHONPATH=<worktree>/src`): **ERDALT's running folds import
   `src/provexp` when they start**, and tasks 2-8 have not all started; do not touch `models/erdalt.py`,
   `train_erdalt.py`, or what they import until they have.
3. **PV's setup against Gimenez et al.'s** (the porting rule; CLAUDE.md "ported for its effect"). Theirs: 1,033
   vectors, PV then a random forest (0.952 AUC), monotone GBT (0.867) or GBT (0.938); `feature_selection.py` at
   0b6f222. Ours: 78,715 vectors, a monotone GBDT; PV keeps 1,359 of 2,568 features and detects 234 / 1,000 at 1% FPR.
   PV's rule (drop any feature any vector lowers) has no constant to rescale, but its result depends on the vector
   count, as ERDALT's criterion did, which is now scaled. Decide whether that asymmetry needs anything beyond PV's
   sample-size experiment (approved and deferred, `docs/scaleup-protocol.md` item (17): kept features and TPR against
   the training malware observed, E[K(n)] = sum_j (1 - p_j)^n).
4. **Read every result with the user:** the table above with the toolkit's `escape` and `loo` parts, the adaptive
   search's escapes and `expert`, MAB `expert` and `zainab` (against 83%; the superseded run's 52% is in
   `superseded-s85/5-attacks/mab-malware/zainab/`); the validity counts (per material shard `Validity:` / `DOS header:`
   lines, `report.json`'s `invalid` and `invalid_pefile_only`, `invalid.parquet`; the toolkit's and adaptive search's
   `invalid`, `not_applicable`, `lost`). Expected: "pefile only" rejections ~0.2%; list them by cause (extractor quirks
   to patch, CLAUDE.md). Report a failed expectation as such. If item 2 changes the toolkit, read the toolkit's
   numbers only after its rerun.
5. **Right-size from sacct** every finished step (`sacct -u $USER -S 2026-11-18 --format=JobID%16,JobName%20,State,
   Elapsed,Timelimit,AllocCPUS,TotalCPU,MaxRSS,ReqMem`), finished steps' headers too. Already done for `erdalt`:
   ~1 of 2 cores used, 96 GB of 128 GB, 6.7 h of 9 h (header kept).
6. **When ERDALT's folds are done** (`sacct --name=learned-erdalt -S 2026-11-20`; each should print the rescaled
   criterion, ~330-370): R19's asks (`docs/reviews/2026-11-12-body/meta-review.md`: the share of training and test
   vectors with L delta < 0; a donor-overlap control); then ERDALT's attacks, submitted with plain
   `sbatch --export=ALL,...` as in `logs/submit-20261117-181439-no-erdalt.txt`: `toolkit` with `DETECTORS=erdalt
   PARTS="main loo donors" LOO=erdalt` (`--array=0-9`); `adaptive` with `TAG=erdalt DETECTORS=erdalt ESCAPES=none
   EXPERT=0` (20 tasks, writes `none/shard-<k>-erdalt/`); MAB-Malware with `TAG=erdalt DETECTORS=erdalt SETTINGS=ours
   --array=0 --cpus-per-task=1` (writes `ours-erdalt/`). If item 2 changes how GAMMA is written, ERDALT's toolkit run
   waits for that change. Then `6-results` (`sbatch pipeline/6-results/run.sh`; it stops if a detector's outputs
   appear twice).
7. **Later, approved:** PV's sample-size experiment (item (17)); decision 12's follow-up (PLAN.md, open items: the
   training files behind the derived table's new moves).

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On the interactive node: use only the allocation (cores, memory, GPUs); every worker pool under
  `if __name__ == "__main__":`, diagnostic Python in a file (under `artifacts/scaleup/diag/`), never from stdin. Jobs
  longer than ~10 minutes, or larger than the allocation, still go through `sbatch` after asking. Kill by PID, never
  `pkill -f`.
- **Do not watch the queue.** Check once, report, hand back. Read every new job's log within ~2 minutes of its start
  and its startup line (`Threads per process: ...`).
- The user is out of patience with avoidable cluster failures: before submitting or changing a step, work out the
  processes, threads, cores and memory it uses; say plainly what was not checked.
- A code change is live for every job that starts Python after it is saved: risky changes go in a `git worktree`,
  verified, then fast-forwarded (ERDALT's folds, above).
- A method from another paper is ported for its effect, not its letter: tabulate their setup against ours and rescale
  what the differences touch, before the first run and before diagnosing a weak result.
- Explain plainly; a hypothesis before running anything; report failed checks as such; fix failures at their source;
  discard failures only when rare (~10 in 1,000). The user decides protocol questions; Claude recommends. Commit to
  `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push.
- At the end: `docs/status.md`, PLAN.md, and this prompt rewritten self-contained.

## 5. Noted for later

- Open with the user: move `docs/erdalt-diagnosis-plan.md` under `docs/evidence/`.
- ERDALT's logits reach +-8,007 on validation (temperature 266.9); harmless at a 1%-FPR threshold, worth a sentence if
  calibrated probabilities are ever reported.
- Toolkit task 9 (the debug-entry escape) used 41% of its 36 cores with every attack 2-3x slower in an earlier run;
  cause not found. If it recurs, `sstat` it while it runs.
- Per-item loops that may still run serially in a main process: `toolkit.py` and `mab.py` (feature extraction before
  the pool), `6-results` scripts, `expert_adaptive.py`. `mab.py` runs all detectors in one pool: one detector's crash
  loses every other detector's finished run.
- `third_party/README.md` lists MAB-Malware's patches but not 50f3e97's (shell commands checked, donor names).
- `coverage.py` still accepts an unused `--db`. Other audit steps (population, item checks, escapes, deviations) may
  still read the SimpleDB; move them to the file store before their next run.
- Not checked in the ERDALT diagnosis: that the std scale on a 24,000-file sample of ours behaves like theirs; which
  vectors and features carry the remaining violations (35,594 in the retrain).
- `artifacts/scaleup/diag/erdalt/smoke-s93/` holds session 94's 2-epoch smoke model (disposable).
