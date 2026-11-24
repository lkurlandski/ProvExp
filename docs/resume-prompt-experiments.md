# Resume: after the maintenance, see ERDALT and the attacks through on tigris, then read the new round with the user

Written at the end of session 112 (experiments track, 2026-11-24, tigris head node; a writing session also numbered
112 ran in parallel). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading first. **The next session
starts after the clusters' maintenance** (the user, 2026-11-24: both clusters were cycling down for maintenance). Work
on tigris only: the two-cluster race was dropped (user, session 112). Background, when needed:
`docs/scaleup-protocol.md` (items (1)-(23)), `docs/experiments-to-reconsider.md` (the register of aspects we may
change), `SETUP.md`, `pipeline/4-detectors/learned/run.sh`. Other tracks: `docs/resume-prompt-writing.md`,
`docs/resume-prompt-theory.md`, `docs/resume-prompt.md`.

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3) replaces every number. Detectors: unconstrained,
monotone-features, monotone-sums (the two guaranteed ones), additions-only, adversarial-training, pv, trial,
iterated-2, and ERDALT (Gimenez et al.'s learned defense, a monotone neural network trained on a GPU; nine models: the
full one, `erdalt`, and eight leave-one-out folds `erdalt-loo-<attack>`). Attacks: Gimenez et al.'s eight
secml-malware attacks (the "toolkit"), our adaptive search, MAB-Malware (three settings: ours, expert, zainab).
Operations (`src/provexp/featuresets/ember2024/directions.py`, `OPS`), fourteen: additions `app sec imp`; insertions
`ext shf hgr`; overwrites `slk dos hdr chk ren rdb rsg ent`. The validity rule (`src/provexp/attacks/validity.py`): an
output counts only if pefile and LIEF both read it, neither lost a section (by virtual address), DLL or imported
function the original had, and it is at most 4,000,000 bytes.

## 2. Where things stood (end of session 112, 13:30, before the maintenance)

**The full rerun** (submitted 2026-11-23, `logs/submit-20261123-141442.txt`): everything up to ERDALT finished cleanly
(session 110). Left, all on tigris, chained by ordinary SLURM dependencies (no holds):
- **ERDALT, nine models**, one per array task, each on one GH200 (2 cores, 128 GB, 9 h limit; ~10 min loading and
  ~5.1-5.7 min per epoch, 68 epochs, ~6.5 h):
  - 1260392_0 trains `erdalt` (started 10:22 on gh-a-043; epoch 26 at 12:57; expected done ~17:00).
  - 1264791_1 trains `erdalt-loo-gamma_sections` (started 10:40 on gh-a-112; epoch 25 at 12:57; ~17:00).
  - 1264791_[2-8] (the other seven folds, task i trains the i-th model of `erdalt`, then the folds in the order of
    `ATTACKS` in `learned/run.sh`) were pending on priority, with no start estimate. SLURM split them into separate
    records (job ids 1264917-1264922 and 1264791 itself for _8) when their `Requeue` was set to 0 (below); they are
    still tasks of array 1264791.
- **toolkit (1260395, 29 tasks), adaptive (1260396, 81 tasks), MAB `zainab` (1260397)**: `Dependency=afterok:
  1260392_0:1264791` (all nine ERDALT tasks must succeed). Submitted with `--kill-on-invalid-dep=yes`: if an ERDALT
  task fails, they are cancelled.
- **`6-results` (1260399)**: `afterok` on the three.

**The ERDALT claims (a trap to know about).** All nine tasks were submitted with `CLAIMS=artifacts/scaleup/4-detectors/
erdalt-claims` (session 111's race). A task trains its model only if it creates `<claims>/<model>` (atomic `mkdir`);
if the directory exists, it *skips the model and exits 0*. Session 112 moved the old claims directory (with the
release and cancel lists, now unused) to `artifacts/scaleup/diag/s112/erdalt-claims-s111`, so the two running tasks
hold no claim, and a pending task creates a fresh claim when it starts. Hence:
- the two running tasks (1260392_0, 1264791_1) keep `Requeue=1`: if the maintenance killed and requeued them, they
  start their model again from scratch (no claim to block them);
- the seven pending tasks have `Requeue=0` (set in session 112): if one is killed after it started, it ends FAILED or
  NODE_FAIL instead of being requeued into a skip, and the three attack jobs (then `6-results`) are cancelled.
**Before resubmitting any ERDALT model, remove its claim** (`rm -r artifacts/scaleup/4-detectors/erdalt-claims/
<model>`), or the new task skips it.

**sporc**: nothing of ours runs there. The race's sporc array (22176620) was cancelled before it started. The A100
trial (22176526) measured ERDALT on an A100 40 GB: 22.8 GB of GPU memory, ~96 GB RSS, ~12 min loading, ~15 min per
epoch (2.6x a GH200), ~17.2 h per model; recorded in `pipeline/systems/sporc.sh` (request 23 h there). The H100 is
~1.6x an A100 on fp32 matmul.

**One environment per architecture** (session 111): `env-aarch64/`, `env-x86_64/` (built by
`pipeline/setup/build_env.sh`), `env/` a dispatcher (`pipeline/setup/make_dispatcher.sh`). Kept for a rollback:
`env-aarch64-old/` (the former `env/`) and an interim fallback in `pipeline/common.sh` (the branch taken when `env/` is
not the dispatcher and its Python cannot run). The ERDALT jobs are the first real jobs through the dispatcher on tigris.

## 3. What the next session does (stop and report at each step)

**Step 1. Check once** (do not watch the queue): `squeue -M tigris -u $USER -r`; `sacct -M tigris -u $USER -S
2026-11-24 -X --format=JobID%16,JobName%20,State,Elapsed,Timelimit,AllocCPUS,TotalCPU,ReqMem,MaxRSS,NodeList,Restarts`
(MaxRSS and TotalCPU are on the `.batch` steps: drop `-X` for them); `ls artifacts/scaleup/4-detectors/erdalt-claims/`
and `cat` the `owner` files; for each of the nine models, whether `artifacts/scaleup/4-detectors/<model>/
vl_predictions.parquet` exists; the tail of `artifacts/scaleup/4-detectors/logs/train-<model>.log` for any model still
training; the job logs `logs/learned-erdalt_<array>_<task>.out`. Report plainly which models are done, where each is
training, and whether the maintenance killed, requeued (`Restarts`) or failed anything.

**Step 2. Repair what the maintenance broke, if anything** (tell the user before any `scancel` or resubmission):
- A model that is missing although its task ended COMPLETED: the task skipped it on a claim (look for "claimed by ...;
  skipping." in its job log). The attacks may then have started or be about to start without it: tell the user at once.
- A FAILED, NODE_FAIL or TIMEOUT ERDALT task: read its logs, fix any real cause at its source, remove its claim, and
  resubmit that one model with the array's command (`pipeline/submit.sh`, the `L1=` line: `sbatch --export=ALL,
  PART=erdalt --array=<i> --constraint=gh --gpus-per-node=1 --output=./logs/%x_%A_%a.out --cpus-per-task=2 --mem=128G
  --time=0-09:00:00 --job-name=learned-erdalt pipeline/4-detectors/learned/run.sh`, without `CLAIMS`). If the attack
  jobs were cancelled by `--kill-on-invalid-dep`, resubmit 5-attacks toolkit, adaptive, MAB `zainab` and `6-results`
  with the commands in `pipeline/submit.sh` (those lines; the earlier stages are done), depending `afterok` on the
  surviving and resubmitted ERDALT jobs. Do not resubmit what finished.
- Jobs that were simply pending through the maintenance need nothing.

**Step 3. Clean up the environment switch** once real jobs have run cleanly through the dispatcher on tigris (ERDALT,
then a toolkit or adaptive task): `rm -rf env-aarch64-old`; remove the interim fallback in `pipeline/common.sh` (keep
the `ENV_DIR` knob: `source "${ENV_DIR:-env}/bin/activate"`); ruff, strict mypy on `src tests pipeline`; commit. Also
move `artifacts/scaleup/diag/s111/` (race smoke tests, the A100 trial) and `diag/s112/erdalt-claims-s111` out of the
way or delete them (ask). Right-size from sacct the steps that finished (CLAUDE.md, the resources rule; memory
`right-size-while-fresh`): the ERDALT header (2 cores, 128 GB, 9 h) against the nine tasks' MaxRSS and elapsed time.

**Step 4. When `6-results` is done, read the new round with the user** (as planned in session 105), result by result,
plainly: the detection table, each attack's still-detected share per detector
(`artifacts/scaleup/6-results/tables/still_detected.csv`), the toolkit per attack and per escape, the leave-one-out
folds, the adaptive search (how often `hgr` was used: `header_growth`), MAB's three settings, the validity rejections
by cause (list the "pefile only" ones: extractor quirks to weigh with the user), the bytes added (median; the 4 MB
rule; register entry 1.6: would the over-size outputs have evaded?), coverage and ERDALT's hole (and the GPU each model
trained on: all GH200s on tigris; the node from sacct; the paper's appendix states it). Hypothesis: the guaranteed
detectors 0 in their population; gamma_api still the strongest toolkit attack but weaker than under LIEF and not
applicable to ~114 test malware; gamma_sections not applicable to ~25% of the test malware and weaker than at the old
budget (the material: 0.7% against 1.5%); the byte-level attacks unchanged. Right-size each newly finished step from
sacct. Then, with the user's approval: PV's sample-size experiment (protocol item (17)); the numbers into the
manuscript (writing track).

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On a head node: light work only; tests, builds and diagnostics through `sbatch`. Diagnostic Python in a file under
  `artifacts/scaleup/diag/` (the next session's: `diag/s113/`), never from stdin; worker pools under
  `if __name__ == "__main__":`; diagnostics need `FILE_STORE=artifacts/scaleup/2-features/files/files.sqlite` and
  `PYTHONHASHSEED=0`. Read files by name from the file store, never from the SimpleDB. Jobs longer than ~10 minutes go
  through `sbatch` after asking. Kill by PID, never `pkill -f`. Never edit a run script while `bash` runs it (a
  `sbatch` job runs SLURM's copy, but it sources `pipeline/common.sh` from disk: edits there reach every pending job).
- `sbatch --test-only` start estimates are unreliable; use `squeue --start` of a submitted job and `sprio`.
- Do not watch the queue: check once, report, hand back. Tell the user before every `scancel` of a real job.
- Never submit production work to sporc's `debug` partition (user). For now, no two-cluster work (user, session 112).
- A plan (and the user's approval) before an experiment; a hypothesis before running; report failed checks as such;
  fix failures at their source. The user decides protocol questions; Claude recommends, plainly.
- The user wants meaning, not raw numbers: say whether a result supports the research direction and what it changes.
- Methodology changes go on the next-round list (`docs/scaleup-protocol.md`, end) and the register
  (`docs/experiments-to-reconsider.md`), not into a rerun of their own.
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push. Another session may be
  working in the same checkout: check `git status` before committing, and never stage its files.
- At the end: `docs/status.md`, PLAN.md, `docs/scaleup-protocol.md` (a new item for any decision), and this prompt
  rewritten self-contained (archive this one under `docs/archive/` and list it in `docs/README.md`).

## 5. Noted for later

- The register `docs/experiments-to-reconsider.md` holds every methodology candidate (GAMMA's applicability, dropping
  the ineffective toolkit attacks, the adaptive search without cloning, MAB against the official model, the
  hand-table and shifts detectors, the validity and loader questions, seeds, PV's sample size, ...).
- `learned/run.sh`'s race knobs (`ORDER`, `CLAIMS`, `ERDALT_SCRIPT`) stay; `pipeline/submit.sh` submits ERDALT on
  tigris without them. If claims are ever used again, `claim()` should let a requeued task re-take its own claim (same
  array job and task id) instead of skipping its model.
- `scaleup_tables.py`'s not-applicable rows join a job's `room_check.parquet` names with every defense row of the
  attack, although a defense attacks only the files it detects; check this when `6-results` is read (register 4.3).
- The 2-minute audits (population, item-checks, deviations) report MaxRSS equal to their 200 GB request; most likely
  page cache. Left as is.
- `pipeline/5-attacks/toolkit/pv_attacks.py` is pilot-era with no applicability gate; gate or retire it if ever run.
- `pipeline/setup/identity_check.sh` compares with the pilot-final baseline, which sessions 102-105 break; re-baseline
  after the rerun if it is to stay useful.
- Open with the user: move `docs/erdalt-diagnosis-plan.md` under `docs/evidence/`.
- ERDALT's logits reach +-8,007 on validation (temperature 266.9); a sentence if calibrated probabilities are reported.
- Per-item loops that may still run serially: `toolkit.py` and `mab.py` (extraction before the pool), `6-results`
  scripts, `expert_adaptive.py`. Steps that still read the SimpleDB by name: `1-audit/deviations`,
  `population_clauses.py`, `escape_audit.py`, `trial_table.py`. `coverage.py` accepts an unused `--db`.
  `third_party/README.md` lacks 50f3e97's patches. `adaptive.add_section`/`add_imports` (LIEF writers) look unused.
- Disposable: `artifacts/scaleup/diag/s111/` (race smoke tests, the A100 trial), `diag/s112/erdalt-claims-s111`;
  `diag/s105/smoke/`, `diag/s105/malconv-weights/` (keep while the MalConv control may be cited), and the older ones
  listed in `docs/archive/resume-prompt-experiments-2026-11-23-s104.md`.
- Session 110's commits 557f0b5 and 022dceb say "session 106" in their messages; the experiments session was 110.
