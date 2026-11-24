# Resume: run ERDALT on sporc as well, then check the rerun and read its results with the user

Written at the end of session 110 (2026-11-24, experiments track, tigris head node). Self-contained: only `CLAUDE.md`
(loaded automatically) needs reading first. **This session runs on the sporcsubmit head node (sporc, x86_64)**, the
other RIT cluster; it shares the file system with tigris (aarch64), and `squeue`/`sacct`/`scancel`/`sbatch` reach either
cluster with `-M sporc` or `-M tigris`. Background, when needed: `docs/scaleup-protocol.md` (items (1)-(22)),
`docs/experiments-to-reconsider.md` (the register of aspects we may change, with reasons), `SETUP.md`,
`pipeline/systems/{tigris,sporc}.sh`. Other tracks: `docs/resume-prompt-writing.md`, `docs/resume-prompt-theory.md`,
`docs/resume-prompt.md` (general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3) replaces every number. Detectors: unconstrained,
monotone-features, monotone-sums (the two guaranteed ones), additions-only, adversarial-training, pv, trial,
iterated-2, and ERDALT (Gimenez et al.'s learned defense, a monotone neural network trained on a GPU). Attacks:
Gimenez et al.'s eight secml-malware attacks (the "toolkit"), our adaptive search, MAB-Malware (three settings: ours,
expert, zainab). Operations (`src/provexp/featuresets/ember2024/directions.py`, `OPS`), fourteen: additions `app sec
imp`; insertions `ext shf hgr`; overwrites `slk dos hdr chk ren rdb rsg ent`. The validity rule
(`src/provexp/attacks/validity.py`): an output counts only if pefile and LIEF both read it and neither lost a section
(by virtual address), DLL or imported function the original had; since session 105 also only if it is at most
4,000,000 bytes.

## 2. Where things stand (end of session 110)

**The full rerun (submitted by the user 2026-11-23, jobs 1260382-1260399 on tigris, `logs/submit-20261123-141442.txt`).**
Finished cleanly, outputs present, no errors (the material's "leaked semaphore" warnings are loky's shutdown, harmless):
the audits, trial, train, train-trial, the material (10 shards, 2.2-2.6 h each; 73,502 kept of 76,049 runs: 2,001 over
4 MB, all GAMMA; 268 invalid, 21 "pefile only"), the GBDT defenses (`learned`, 1260391), iterated (3.7 h), the price
list, MAB-Malware's `ours` (unconstrained: 455 of 867 evaded) and `expert` (137 of 161) settings (1260398_1-2).
**Pending:** ERDALT's nine GPU models (array 1260392_[0-8], tigris `gh` nodes, "Priority"; SLURM estimated a start on
2026-11-25 ~15:00, then ~6.7 h per model on a GH200). Waiting on it with `afterok:1260392_*`: toolkit (1260395, 29
tasks), adaptive (1260396, 81 tasks), MAB `zainab` (1260397); `6-results` (1260399) waits on those three.

**Session 110 also:** right-sized material (4 h, 96 GB: it peaked at 79 GB of 80), iterated (6 h, 192 GB), trial
(64 GB), the single MAB settings (4 h, 24 GB) (commit 557f0b5); started the register
`docs/experiments-to-reconsider.md` (combed from every document; add to it as things come up); the user accepted for
this round that GAMMA's section attack is not applicable to ~25% of files at the literature budget (75 donor section
headers do not fit: 2,457 of 10,000 training malware; register entry 1.1). Its evasions in the material: 51 of 7,533
(0.7%, against 1.5% at the old budget).

**Why sporc (decided, user, session 110).** On sporc, SLURM's `--test-only` estimated a start for one ERDALT-sized job
(1 GPU, 2 cores, 128 GB, 14 h) at 2026-11-24 ~11:40 in `tier3` (an A100 node, or the H100 node spr-a-02) and ~15:50 in
`sporc-gpu`, against tigris's ~15:00 the next day; an A100 is slower than a GH200 (guess: 10-13 h per model), so the
expected gain is half a day to a day. ERDALT keeps the whole training set on the GPU (1.76M x 2,568 float32 ~ 18 GB,
plus validation and the vectors; estimate 25-30 GB; `src/provexp/models/erdalt.py` around line 266), which should fit
an A100's 40 GB.

## 3. What this session does (stop and report at each step)

**Step 0 (done by the user before this session).** Claude Code runs on both clusters: `~/.local/bin/claude` is a plain
launcher (`~/.local/lib/claude-launcher.sh`) that runs the newest version installed for the machine's architecture under
`~/.local/sw/<arch>/share/claude/versions` (session 110). If `claude` fails on either head node, fix that first.

**Step 1. Check the chain once** (from sporc: `squeue -M tigris -u $USER`; `sacct -M tigris -u $USER -S 2026-11-23 -X
--format=JobID%16,JobName%20,State,Elapsed,Timelimit,AllocCPUS,TotalCPU,ReqMem`). If ERDALT's tasks have started on
tigris, tell the user: the sporc plan shrinks to the tasks still pending (or is dropped). Do not watch the queue.

**Step 2. One environment per architecture, selected automatically** (the user's design, as in
`~/Documents/code/SSViT`): `env-aarch64/` and `env-x86_64/` are the real virtual environments, and `env/bin/activate`
is a small dispatcher that sources `env-$(uname -m)/bin/activate` (copy `~/Documents/code/SSViT/env/bin/activate`; it
prints how to create the environment when it is missing). `~/.bashrc` already makes uv's Python and caches
per-architecture (`SWROOT=$HOME/.local/sw/$MYARCH`, `UV_PYTHON_INSTALL_DIR`, `UV_CACHE_DIR`, `XDG_CACHE_HOME`), so uv
builds each environment with that machine's interpreter. Constraints:
- **Never leave tigris without a working `env/`.** Every pending tigris job (ERDALT, toolkit, adaptive, MAB,
  results) runs `source env/bin/activate` (`pipeline/common.sh:26`) when it starts, possibly in the middle of this
  session. Virtual environments are not relocatable (absolute paths in `pyvenv.cfg`, the scripts' shebangs and
  `activate`), so do **not** `mv env env-aarch64`. Build `env-aarch64` fresh with a job on tigris and `env-x86_64`
  with a job on sporc (`pipeline/setup/build_env.sh` with the target directory as a knob, e.g. `ENV_DIR`, default
  `env-$(uname -m)`; it already detects the system and loads the spack gcc), test both, and only then switch `env/` to
  the dispatcher in one quick step at a moment when no tigris job is starting (none is running now), keeping the old
  `env/` as `env-aarch64-old/` for a rollback until both clusters have been verified on real jobs.
- **Everything that names `env/bin/...` directly** must keep working: `pipeline/setup/build_env.sh:33`
  (`env/bin/python`), `pipeline/setup/identity_check.sh:35`, `.claude/skills/delegate/SKILL.md:62`, and CLAUDE.md's
  checks (`env/bin/pytest`, `env/bin/ruff`, `env/bin/mypy`). Either the dispatcher also provides those as small
  shims that exec `env-$(uname -m)/bin/<tool>`, or the documents switch to `source env/bin/activate` then the bare tool
  name; pick the simpler one and update CLAUDE.md's Environment line and SETUP.md §2-3. Add `env-*/` to `.gitignore`.
- `pipeline/systems/sporc.sh` holds guesses marked "TO CONFIRM" (cores per node, the spack gcc module `gcc/lhqcen5`,
  the walltime): confirm them on sporcsubmit. Partitions seen in session 110: `sporc-gpu`, `tier3`, `sporc`,
  `scavenger` (max time 20 days, account `admalware`); A100 nodes (skl-a-*, 2 or 4 A100 40 GB, 36 cores, ~380 GB)
  carry the feature `cuda11`, the one H100 node (spr-a-02, 4 x H100 80 GB) `cuda12`. The `run.sh` headers target
  tigris (`--partition=tigris --constraint=gg|gh`): on sporc override them at submission (partition, `--gres=gpu:...:1`
  in place of `--constraint` and `--gpus-per-node`).

**Step 3. Test thoroughly before anything is cancelled** (the user: we must not break tigris, and the code must run
on sporc). Hypothesis: everything passes, the open question is the A100 nodes' CUDA driver.
- tigris (`sbatch -M tigris`, short jobs on `gg`): imports, `pipeline/setup/check.sh`, the full test suite
  (`pytest -n 16 tests`, ~4 min; 2,058 passed in session 105) through the dispatcher, and a tiny `run.sh` smoke through
  `common.sh` (e.g. `4-detectors/learned` with `PART=erdalt`, `LIMIT`, `EPOCHS=1` on a `gh` node, written under a
  scratch `OUT_ROOT`; never into `artifacts/scaleup`).
- sporc: the same, plus a GPU probe (`nvidia-smi`, the driver's CUDA version, `torch.cuda.is_available()`, a small
  matmul) on an A100 node and on the H100 node. Our torch is built for CUDA 12.9 (`requirements-lock.txt`); if the
  A100 nodes' driver is too old for it, only the H100 node (4 GPUs) is usable: report and decide with the user.
  `pipeline/setup/check.sh` also says whether featurization is bit-identical to the reference on x86 (only ERDALT runs
  there now, but record it).
- One real ERDALT model on sporc for one or two epochs (scratch `OUT_ROOT`, the real store): GPU memory (estimate
  25-30 GB) and time per epoch (GH200: ~5.7 min per epoch, ~10 min loading, 68 epochs). Report the projected time per
  model and the finish time against tigris's estimate; the user decides whether to go ahead.

**Step 4. ERDALT on both clusters, the first to start wins** (decided, user: resubmit on sporc in **reverse order**,
task 8 first, so the two clusters take the nine models from opposite ends; the mechanism is to be worked out with the
user before any submission or `scancel`). What it must guarantee:
1. Each model trains exactly once: when a model's task starts on one cluster, its twin on the other must not train
   it (cancelled, or exits at once).
2. The tigris jobs that need ERDALT (toolkit 1260395, adaptive 1260396, MAB 1260397) start only once all nine models
   exist, whichever cluster trained them. SLURM cannot make a tigris job wait for a sporc job, and their
   `afterok:1260392_*` is never satisfied once a tigris twin is cancelled (cancelled is not "ok").
3. A failure is seen, not silently skipped: if a winning task dies, nothing downstream starts on a missing model.

A candidate design to weigh with the user (Claude's, session 110; not decided): (a) a claim per model on the shared
file system, taken atomically at the start of the task (`mkdir $OUT_ROOT/4-detectors/erdalt-claims/<name>`, writing
the cluster and job id inside); the loser exits 0 at once; the winner `scancel -M <other cluster>`s its pending twin
(the twin's job id from a small map written at submission). (b) A gate job on tigris (one core, CPU, long time limit)
that waits for the nine finished models (the predictions file `learned/run.sh` writes; "a model whose predictions exist
is skipped") and fails if a claimed task ended in any state but COMPLETED (`sacct -M`); then re-point the three
dependents to it (`scontrol -M tigris update JobId=<id> Dependency=afterok:<gate>`, allowed on pending jobs; for the
arrays, the job id applies to every task). (c) The reverse order as a knob in `learned/run.sh` (e.g. `ORDER=reverse`
mapping array task i to model 8-i), since SLURM's order among array tasks is not guaranteed. Simpler alternative: hold
the three dependents (`scontrol hold`), and release them by hand once the nine models exist (someone must remember to
check). Whatever is chosen: smoke-test it with a scratch `OUT_ROOT` and dummy jobs on both clusters before touching
1260392, and tell the user before every `scancel`.

**Step 5. When `6-results` is done, read the new round with the user** (as planned in session 105), result by result,
plainly: the detection table, each attack's still-detected share per detector
(`artifacts/scaleup/6-results/tables/still_detected.csv`), the toolkit per attack and per escape, the leave-one-out
folds, the adaptive search (how often `hgr` was used: `header_growth`), MAB's three settings, the validity rejections
by cause (list the "pefile only" ones: extractor quirks to weigh with the user), the bytes added (median; the 4 MB
rule; register entry 1.6: would the over-size outputs have evaded?), coverage and ERDALT's hole (and the GPU it trained
on). Hypothesis: the guaranteed detectors 0 in their population; gamma_api still the strongest toolkit attack but
weaker than under LIEF and not applicable to ~114 test malware; gamma_sections not applicable to ~25% of the test
malware and weaker than at the old budget (the material: 0.7% against 1.5%); the byte-level attacks unchanged. Right-
size each newly finished step from sacct (Elapsed, TotalCPU, MaxRSS against the request) and edit its header.
Then, with the user's approval: PV's sample-size experiment (protocol item (17)); the numbers into the manuscript
(writing track).

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On a head node (tigris or sporcsubmit): light work only; tests, builds and diagnostics through `sbatch`. Diagnostic
  Python in a file under `artifacts/scaleup/diag/` (this session's: `diag/s111/`), never from stdin; worker pools under
  `if __name__ == "__main__":`; diagnostics need `FILE_STORE=artifacts/scaleup/2-features/files/files.sqlite` and
  `PYTHONHASHSEED=0`. Read files by name from the file store, never from the SimpleDB. Artifacts live under
  `/shared/rc/admalware/provexp` (the checkout's `artifacts` link). Jobs longer than ~10 minutes go through `sbatch`
  after asking. Kill by PID, never `pkill -f`. Never edit a run script while `bash` runs it.
- Do not watch the queue: check once, report, hand back.
- A plan (and the user's approval) before an experiment; a hypothesis before running; report failed checks as such;
  fix failures at their source. The user decides protocol questions; Claude recommends, plainly.
- The user wants meaning, not raw numbers: say whether a result supports the research direction and what it changes.
- Methodology changes go on the next-round list (`docs/scaleup-protocol.md`, end) and the register
  (`docs/experiments-to-reconsider.md`), not into a rerun of their own.
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push.
- At the end: `docs/status.md`, PLAN.md, `SETUP.md` (the two environments; sporc's confirmed values),
  `docs/scaleup-protocol.md` (a new item for any decision), and this prompt rewritten self-contained (archive this one
  under `docs/archive/` and list it in `docs/README.md`).

## 5. Noted for later

- The register `docs/experiments-to-reconsider.md` holds every methodology candidate (GAMMA's applicability, dropping
  the ineffective toolkit attacks, the adaptive search without cloning, MAB against the official model, the
  hand-table and shifts detectors, the validity and loader questions, seeds, PV's sample size, ...).
- `scaleup_tables.py`'s not-applicable rows join a job's `room_check.parquet` names with every defense row of the
  attack, although a defense attacks only the files it detects; check this when `6-results` is read (register 4.3).
- The 2-minute audits (population, item-checks, deviations) report MaxRSS equal to their 200 GB request; most likely
  page cache from reading the dataset, not use. Left as is; look again if memory on the gg nodes gets tight.
- `pipeline/5-attacks/toolkit/pv_attacks.py` is pilot-era with no applicability gate; gate or retire it if ever run.
- `pipeline/setup/identity_check.sh` compares with the pilot-final baseline, which sessions 102-105 break; re-baseline
  after the rerun if it is to stay useful.
- Open with the user: move `docs/erdalt-diagnosis-plan.md` under `docs/evidence/`.
- ERDALT's logits reach +-8,007 on validation (temperature 266.9); a sentence if calibrated probabilities are reported.
- Per-item loops that may still run serially: `toolkit.py` and `mab.py` (extraction before the pool), `6-results`
  scripts, `expert_adaptive.py`. Steps that still read the SimpleDB by name: `1-audit/deviations`,
  `population_clauses.py`, `escape_audit.py`, `trial_table.py`. `coverage.py` accepts an unused `--db`.
  `third_party/README.md` lacks 50f3e97's patches. `adaptive.add_section`/`add_imports` (LIEF writers) look unused.
- Disposable: `artifacts/scaleup/diag/s105/smoke/` (its 4-detectors links point into `superseded-s105/`),
  `diag/s105/malconv-weights/` (keep while the MalConv control may be cited), and the older ones listed in session
  104's prompt (`docs/archive/resume-prompt-experiments-2026-11-23-s104.md`).
- Session 110's commits 557f0b5 and 022dceb say "session 106" in their messages; the experiments session was 110
  (sessions 106-109 were the writing track). The documents are corrected.
