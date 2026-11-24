# Resume: see ERDALT through on two clusters, then read the new round with the user

Written at the end of session 111 (experiments track, 2026-11-24, an interactive job on sporc; a writing session also
numbered 111 ran in parallel). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading first. The next
session can run on either cluster's head node or in an interactive job: tigris (aarch64) and sporc (x86_64) share the
home directory, the checkout and `/shared/rc/admalware/provexp` (the `artifacts` link), and `squeue`/`sacct`/
`scontrol`/`scancel`/`sbatch` reach either with `-M tigris` or `-M sporc`. Background, when needed:
`docs/scaleup-protocol.md` (items (1)-(23)), `docs/experiments-to-reconsider.md` (the register of aspects we may
change), `SETUP.md` (§2-3: the two environments and both clusters), `pipeline/4-detectors/learned/run.sh` (the race
knobs). Other tracks: `docs/resume-prompt-writing.md`, `docs/resume-prompt-theory.md`, `docs/resume-prompt.md`.

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

## 2. Where things stand (end of session 111, 10:40)

**The full rerun** (submitted 2026-11-23, `logs/submit-20261123-141442.txt`, which also records session 111's changes):
everything up to ERDALT finished cleanly (session 110). Still to run: ERDALT's nine models, then toolkit (1260395, 29
tasks), adaptive (1260396, 81 tasks), MAB `zainab` (1260397), then `6-results` (1260399, `afterok` on those three).

**ERDALT is raced on both clusters** (protocol item (23); mechanism in `learned/run.sh`, commit f46e8bd):
- tigris **1260392_0** trains `erdalt` (all eight attacks); started 10:22 on gh-a-043 with the *old* script (no claim
  code; its claim was written by hand); epoch 0 at 10:39 (validation ROC 0.945); ~6.7 h, so done ~17:00.
- tigris **1264791_[1-8]**: models 1-8 in forward order (gh, 1 GPU, 2 cores, 128 GB, 9 h). It took the cancelled
  1260392_[1-8]'s place in the queue (rank 225 of 295, verified with a real dummy job before cancelling: the age term
  was 0.06% of the priority and no job lay in between). SLURM plans to hand these GPUs out slowly (a dummy job behind
  them was estimated for 2026-11-25 ~15:00).
- sporc **22176620_[0-7]**: `ORDER=reverse`, models 8 down to 1, `--partition=tier3,sporc-gpu --gres=gpu:1` (A100 40 GB
  or the H100 80 GB node), 2 cores, 128 GB, **20 h limit (a placeholder: lower it after the trial, step 2)**. Estimated
  start 2026-11-26 ~06:30: our fairshare on sporc is low (533k against 1.2-1.3M for the users ahead).
- `artifacts/scaleup/4-detectors/erdalt-claims/`: one directory per claimed model, `owner` inside (cluster, job, order,
  host, time); `release` (tigris 1260395, 1260396, 1260397) and `cancel` (tigris 1264791, sporc 22176620).
- The three dependents are **held** (`JobHeldUser`) with their dependency on 1260392 cleared (necessary: `submit.sh`
  submits with `--kill-on-invalid-dep=yes`, so cancelling 1260392's tasks would otherwise have killed them).
  `6-results` still waits on them.
- How it ends: a task takes a model's claim (atomic `mkdir`) or skips it, naming the owner. When a task ends and all
  nine `4-detectors/<model>/vl_predictions.parquet` exist, it runs `scontrol -M tigris release` on the three and
  `scancel -M <cluster> --state=PENDING` on both arrays. A failed model makes its task exit 1 (FAILED in sacct),
  releases nothing, and keeps its claim.

**One environment per architecture** (commit 6b51345): `env-aarch64/`, `env-x86_64/` (built by
`pipeline/setup/build_env.sh`), `env/` a dispatcher (`pipeline/setup/make_dispatcher.sh`: `env/bin/activate` and
per-command shims). `pipeline/systems/arch.sh` re-points the per-architecture paths of `~/.bashrc` (uv, caches,
`~/.local/sw/<arch>`) in a job submitted from the other cluster. Both pass `pipeline/setup/check.sh` (featurization
bit-identical on both architectures; 2,058 tests). 1260392_0 is the first real job through the dispatcher on tigris.
Kept for a rollback: `env-aarch64-old/` (the former `env/`); an interim fallback in `pipeline/common.sh` (the branch
taken when `env/` is not the dispatcher and its Python cannot run).

## 3. What the next session does (stop and report at each step)

**Step 1. Check once** (do not watch the queue): `squeue -M tigris,sporc -u $USER`; `sacct -M tigris -u $USER -S
2026-11-24 -X --format=JobID%16,JobName%20,State,Elapsed,Timelimit,AllocCPUS,TotalCPU,ReqMem,MaxRSS,NodeList` and the
same with `-M sporc`; `ls artifacts/scaleup/4-detectors/erdalt-claims/*/owner` and `cat` them; for each model, whether
`4-detectors/<model>/vl_predictions.parquet` exists; the tail of each running model's
`4-detectors/logs/train-<model>.log`. Report plainly: which models are done, where each is training, any FAILED task.

**Step 2. The A100 trial (sporc 22176526, `logs/erdalt-trial_22176526.out`)**, if not read yet: the GPU probe on an A100
node (expect torch to see it: the H100 node and an A100 on clx-a-01 run driver 610, CUDA 13.3), then one real ERDALT
model for 2 epochs under the scratch `OUT_ROOT=artifacts/scaleup/diag/s111/erdalt-trial` (log
`.../4-detectors/logs/train-erdalt.log`; a GPU memory line every minute in the job log). Hypothesis: it fits in 40 GB
(estimate 25-30 GB) at roughly 1.5-2x the GH200's 5.7 min per epoch. Report the GPU memory, loading time and time per
epoch; project a model (68 epochs + loading); then **lower the sporc array's limit** to that projection plus ~30%
(`scontrol -M sporc update JobId=22176620 TimeLimit=...`; allowed on pending tasks; a shorter limit backfills more
easily). If the model does not fit an A100, tell the user before changing anything (the H100 node alone:
`--gres=gpu:h100:1`, which means cancelling and resubmitting 22176620). The trial runs in `debug`, which was for this
test only: **never submit production work to sporc's `debug` partition** (user).

**Step 3. When all nine models exist**: check that the three dependents were released (no longer `JobHeldUser`) and
both arrays' leftovers cancelled. The one case the mechanism does not cover: if 1260392_0 (old script) happens to be
the last model to finish, nobody releases; then, after checking the nine `vl_predictions.parquet`,
`scontrol -M tigris release 1260395 1260396 1260397`. **If a model failed**: read its log, fix the cause at its
source, `rm -r artifacts/scaleup/4-detectors/erdalt-claims/<model>`, and resubmit that one task with the same
command as its array (tigris: `--array=<i>`, `ORDER=forward`; sporc: `--array=<8-i>`, `ORDER=reverse`; the
`--export` and resource flags of §2), after telling the user. Note which GPU each model trained on (the owner files):
the paper's appendix states it.

**Step 4. Clean up the environment switch** once real jobs have run cleanly on both clusters (ERDALT on tigris and,
when one starts, on sporc; the toolkit or adaptive jobs on tigris): `rm -rf env-aarch64-old`; remove the interim
fallback in `pipeline/common.sh` (keep the `ENV_DIR` knob: `source "${ENV_DIR:-env}/bin/activate"`); ruff, strict mypy;
commit. Also right-size from sacct the steps that finished (CLAUDE.md, the resources rule; memory `right-size-while-fresh`).

**Step 5. When `6-results` is done, read the new round with the user** (as planned in session 105), result by result,
plainly: the detection table, each attack's still-detected share per detector
(`artifacts/scaleup/6-results/tables/still_detected.csv`), the toolkit per attack and per escape, the leave-one-out
folds, the adaptive search (how often `hgr` was used: `header_growth`), MAB's three settings, the validity rejections
by cause (list the "pefile only" ones: extractor quirks to weigh with the user), the bytes added (median; the 4 MB
rule; register entry 1.6: would the over-size outputs have evaded?), coverage and ERDALT's hole (and the GPUs it
trained on). Hypothesis: the guaranteed detectors 0 in their population; gamma_api still the strongest toolkit attack
but weaker than under LIEF and not applicable to ~114 test malware; gamma_sections not applicable to ~25% of the test
malware and weaker than at the old budget (the material: 0.7% against 1.5%); the byte-level attacks unchanged. Right-
size each newly finished step from sacct. Then, with the user's approval: PV's sample-size experiment (protocol item
(17)); the numbers into the manuscript (writing track).

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On a head node: light work only; tests, builds and diagnostics through `sbatch`. In an interactive job, light tests
  are fine. Diagnostic Python in a file under `artifacts/scaleup/diag/` (the next session's: `diag/s112/`), never from
  stdin; worker pools under `if __name__ == "__main__":`; diagnostics need
  `FILE_STORE=artifacts/scaleup/2-features/files/files.sqlite` and `PYTHONHASHSEED=0`. Read files by name from the
  file store, never from the SimpleDB. Jobs longer than ~10 minutes go through `sbatch` after asking. Kill by PID,
  never `pkill -f`. Never edit a run script while `bash` runs it (a `sbatch` job runs SLURM's copy, but it sources
  `pipeline/common.sh` from disk: edits there reach every pending job).
- `sbatch --test-only` start estimates are unreliable on both clusters (it predicted days for jobs that started within
  a minute, and "18:00 today" for a sporc GPU job SLURM then placed two days out). Use the real scheduler's estimate
  (`squeue --start`) of a submitted job, and `sprio` for queue position.
- Do not watch the queue: check once, report, hand back. Tell the user before every `scancel` of a real job.
- A plan (and the user's approval) before an experiment; a hypothesis before running; report failed checks as such;
  fix failures at their source. The user decides protocol questions; Claude recommends, plainly.
- The user wants meaning, not raw numbers: say whether a result supports the research direction and what it changes.
- Methodology changes go on the next-round list (`docs/scaleup-protocol.md`, end) and the register
  (`docs/experiments-to-reconsider.md`), not into a rerun of their own.
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push.
- At the end: `docs/status.md`, PLAN.md, `docs/scaleup-protocol.md` (a new item for any decision), and this prompt
  rewritten self-contained (archive this one under `docs/archive/` and list it in `docs/README.md`).

## 5. Noted for later

- The register `docs/experiments-to-reconsider.md` holds every methodology candidate (GAMMA's applicability, dropping
  the ineffective toolkit attacks, the adaptive search without cloning, MAB against the official model, the
  hand-table and shifts detectors, the validity and loader questions, seeds, PV's sample size, ...).
- `learned/run.sh`'s race knobs (`ORDER`, `CLAIMS`, `ERDALT_SCRIPT`) stay for future rounds; `pipeline/submit.sh` does
  not use them yet (it submits ERDALT on tigris only). If the next full rerun races again, add it there.
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
- Disposable: `artifacts/scaleup/diag/s111/race-local/`, `race-slurm/` (smoke tests), `erdalt-trial/` once read;
  `diag/s105/smoke/`, `diag/s105/malconv-weights/` (keep while the MalConv control may be cited), and the older ones
  listed in `docs/archive/resume-prompt-experiments-2026-11-23-s104.md`.
- Session 110's commits 557f0b5 and 022dceb say "session 106" in their messages; the experiments session was 110.
