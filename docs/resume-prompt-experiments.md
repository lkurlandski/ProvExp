# Resume: the scale-up's experiments, all of them (ERDALT's retrain, the three open questions, then the results)

Written at the end of session 94 (2026-11-19, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs
reading first. Since session 94 this one prompt covers every experiment; the ERDALT track
(`docs/resume-prompt-erdalt.md`, record `docs/erdalt-diagnosis-plan.md`) is folded in here and is archived once its
retrain is verified (§3, step 1). Other tracks: `docs/resume-prompt-writing.md`, `docs/resume-prompt-theory.md`,
`docs/resume-prompt.md` (general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`, items
(1)-(17)) replaces every number. Detectors: unconstrained, monotone-features, monotone-sums, additions-only (ours,
from the derived table, or plain), adversarial-training, pv, trial, iterated-2 (learned from attack outputs or trial
edits), and ERDALT (Gimenez et al.'s learned defense). Attacks: Gimenez et al.'s eight secml-malware attacks (the
"toolkit"), our adaptive search, MAB-Malware. Every output counts only under one validity rule (pefile and LIEF both
read it, neither loses a section or an import; `src/provexp/attacks/validity.py`).

## 2. Where things stand

**Every detector except ERDALT has been retrained and attacked on the new material** (session 85's chain,
`logs/submit-20261118-s85.txt`, all COMPLETED 2026-11-18: catalogue checks, trial, material, learned GBDTs,
`iterated`, toolkit 19 tasks, adaptive 81, MAB-Malware `ours`, `expert`, `zainab`). **None of it has been read with
the user.** Headline counts at 1% FPR, evaded / detected of 1,000 test malware (Claude's quick tally, session 94):

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

PV keeps 1,359 features (`4-detectors/pv-selection/report.json`; 78,715 vectors), validation AUC 0.924, test 0.930,
and detects 234 / 1,000 at 1% FPR (pilot ~26%). Unread: the toolkit's `escape` and `loo` parts, the adaptive search's
escapes and `expert`, MAB `expert` and `zainab` (against Zainab et al.'s 83%), every validity count.

**ERDALT's retrain was submitted by the user at the end of session 94**: `erdalt` (array task 0) running, the eight
leave-one-out folds (tasks 1-8) submitted held. Find the IDs with `sacct --name=learned-erdalt -S 2026-11-19`.
The road there (`docs/erdalt-diagnosis-plan.md`, sessions 88-94): ported literally, ERDALT collapsed at scale
(validation AUC 0.84 -> 0.73, its criterion never met). The cause was the port, not the method: their setup is far
smaller (24,000 training files at batch 16, ~465,000 steps; 1,033 vectors; std input scale) than ours (1.76M files at
batch 256; 78,715 vectors). Chiefly the input scale: their std, fitted on 24,000 files, lets a few of our heavy-tailed
files dominate the monotone network; a per-feature scale max(std, 0.9999 quantile of |x - mean|) keeps the AUC
(round 1 robust: 0.938 at 7.5k violations). Round 2 (session 94, quantile scale throughout): the whole schedule in 20
epochs with their literal weight reaches 0.914 at 769 violations (a plateau from epoch 9); with their penalty mass per
step 0.951 at 40k (138k steps, a third of theirs); L frozen at PV's mask 0.82 and still rising after 15 epochs; with
their 1,033 vectors 0.971, but 8.8M of the 202M entries over all 78,715 vectors violated (~4.4%): the blind-spot
evidence. **The retrain's settings** (`pipeline/4-detectors/learned/run.sh`, b9edda9; header states each against their
setup, for Appendix D): quantile scale; w2 x 1,033 / the model's vectors (`--reference_vectors 1033`); criterion
< 5 x our vectors / 1,033 (`--scale_criterion`: < 381 for `erdalt`); 68 epochs = their steps, weights per step; LR
patience 20 -> 4 epochs (their 20 epochs are ~30,000 steps). Expected: validation AUC ~0.93-0.95; whether the
criterion is met is uncertain (less than even odds). ~10 min loading + ~5.7 min per epoch, ~6.7 h per model;
2 cores, 128G, 9 h.

## 3. What the next session does

1. **ERDALT's first epochs, then the hold.** `squeue -u $USER`; read the job's startup line
   (`logs/learned-erdalt_<job>_0.out`: one thread per process, 2 cores) and
   `artifacts/scaleup/4-detectors/logs/train-erdalt.log`. It should print "Their 1033 vectors against our 78715:
   w2 x 0.0131229, criterion < 381 violations". Going well: validation AUC ~0.92 or above and not falling as
   violations fall (round 2's robust-pscale: 0.911 at epoch 0, 0.94-0.95 from epoch 2; its violations 88k at epoch 1,
   40k at 20 on a faster schedule, so expect more at matched epochs here). If so, the user releases the folds
   (`scontrol release <held job ID>`); if not, diagnose before releasing (`scancel <held job ID>` drops them).
   When `erdalt` ends: did it meet the criterion, at what AUC (selected epoch, `erdalt.json`)? Then archive the ERDALT
   track: `docs/resume-prompt-erdalt.md` -> `docs/archive/resume-prompt-erdalt-<date>-s<N>.md`, line in
   `docs/README.md`; `docs/erdalt-diagnosis-plan.md` stays as evidence (move it under `docs/evidence/` if the user
   agrees), and Appendix D states each rescaling.
2. **Three open questions, decided with the user (Claude recommends):**
   - **(a) The guaranteed detectors were evaded by the toolkit:** monotone-features 3 / 803, monotone-sums 1 / 802
     (`5-attacks/toolkit/main/<detector>/table.json`, per attack; the adaptive search and MAB found 0). Find which
     attack and files, and whether each output lies outside the threat model (e.g. an edit the derived table does not
     cover, `evaded_outside_population`), is a validity escape, or is a soundness failure. A soundness failure would
     be the most serious finding of the scale-up: check it on the file itself before anything else.
   - **(b) PV's setup against Gimenez et al.'s** (the same porting rule that fixed ERDALT; CLAUDE.md "ported for its
     effect"). Theirs: 1,033 vectors, PV then a random forest (0.952 AUC), monotone GBT (0.867) or GBT (0.938);
     `feature_selection.py` at 0b6f222. Ours: 78,715 vectors, a monotone GBDT; PV keeps 1,359 of 2,568 features and
     detects 234 / 1,000 at 1% FPR. PV's rule (drop any feature any vector lowers) has no constant to rescale, but its
     result depends on the vector count, as ERDALT's criterion did, which is now scaled: decide whether that
     asymmetry needs anything beyond PV's sample-size experiment (approved and deferred, `docs/scaleup-protocol.md`
     item (17): kept features and TPR against the training malware observed, E[K(n)] = sum_j (1 - p_j)^n), which
     measures exactly this.
   - **(c) Read every result with the user:** the table above with the toolkit's `escape` and `loo` parts, the
     adaptive search's escapes and `expert`, MAB `expert` and `zainab` (against 83%; the superseded run's 52% is in
     `superseded-s85/5-attacks/mab-malware/zainab/`); the validity counts (per material shard `Validity:` /
     `DOS header:` lines, `report.json`'s `invalid` and `invalid_pefile_only`, `invalid.parquet`; the toolkit's and
     adaptive search's `invalid`, `not_applicable`, `lost`). Expected: "pefile only" rejections ~0.2%; list them by
     cause (extractor quirks to patch, CLAUDE.md). Report a failed expectation as such.
3. **Right-size from sacct** every finished step (`sacct -u $USER -S 2026-11-18 --format=JobID%16,JobName%20,State,
   Elapsed,Timelimit,AllocCPUS,TotalCPU,MaxRSS,ReqMem`), the headers of finished steps too (standing instruction).
4. **When the nine ERDALT models are done:** R19's asks (`docs/reviews/2026-11-12-body/meta-review.md`: the share of
   training and test vectors with L delta < 0; a donor-overlap control); then ERDALT's attacks, submitted with plain
   `sbatch --export=ALL,...` as in `logs/submit-20261117-181439-no-erdalt.txt`: `toolkit` with `DETECTORS=erdalt
   PARTS="main loo donors" LOO=erdalt` (`--array=0-9`); `adaptive` with `TAG=erdalt DETECTORS=erdalt ESCAPES=none
   EXPERT=0` (20 tasks, writes `none/shard-<k>-erdalt/`); MAB-Malware with `TAG=erdalt DETECTORS=erdalt
   SETTINGS=ours --array=0 --cpus-per-task=1` (writes `ours-erdalt/`). Then `6-results`
   (`sbatch pipeline/6-results/run.sh`; it stops if a detector's outputs appear twice).
5. **Later, approved:** PV's sample-size experiment (item (17)); decision 12's follow-up (PLAN.md, open items: the
   training files behind the derived table's new moves).

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- **Do not watch the queue.** Check once, report, hand back. Read every new job's log within ~2 minutes of its start
  and its startup line (`Threads per process: ...`). Diagnostic Python goes in a file, every worker pool under
  `if __name__ == "__main__":`.
- The user is out of patience with avoidable cluster failures: before submitting or changing a step, work out the
  processes, threads, cores and memory it uses; say plainly what was not checked.
- Head node: at most two CPUs, nothing heavier than a minute or two; everything else through `sbatch` (diagnostics
  under `artifacts/scaleup/diag/`). In an interactive job use only its allocation. Kill by PID, never `pkill -f`.
- A code change is live for every job that starts Python after it is saved: risky changes go in a `git worktree`
  (`PYTHONPATH=<worktree>/src`), verified, then fast-forwarded. **ERDALT's held folds import `src/provexp` when
  released**: do not change `models/erdalt.py` or `train_erdalt.py` until they have started.
- A method from another paper is ported for its effect, not its letter: tabulate their setup against ours and
  rescale what the differences touch, before the first run and before diagnosing a weak result.
- Explain plainly; a hypothesis before running anything; report failed checks as such; fix failures at their source;
  discard failures only when rare (~10 in 1,000). The user decides protocol questions; Claude recommends. Commit to
  `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push.
- At the end: `docs/status.md`, PLAN.md, and this prompt rewritten self-contained.

## 5. Noted for later

- Toolkit task 9 (the debug-entry escape) used 41% of its 36 cores with every attack 2-3x slower in an earlier run;
  cause not found. If it recurs, `sstat` it while it runs.
- Per-item loops that may still run serially in a main process: `toolkit.py` and `mab.py` (feature extraction before
  the pool), `6-results` scripts, `expert_adaptive.py`. `mab.py` runs all detectors in one pool: one detector's crash
  loses every other detector's finished run.
- `third_party/README.md` lists MAB-Malware's patches but not 50f3e97's (shell commands checked, donor names).
- `coverage.py` still accepts an unused `--db`. Other audit steps (population, item checks, escapes, deviations) may
  still read the SimpleDB; move them to the file store before their next run.
- Not checked in the ERDALT diagnosis: that the std scale on a 24,000-file sample of ours behaves like theirs (a cheap
  check that the difference is the data size, not only the tails); which vectors and features carry the last few
  hundred violations under the heavy penalty.
- `artifacts/scaleup/diag/erdalt/smoke-s93/` holds session 94's 2-epoch smoke model (disposable).
