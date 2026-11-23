# Resume: the scale-up's experiments (check the rerun, then read its results with the user)

Written at the end of session 105 (2026-11-23, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs
reading first. Background, when needed: `docs/scaleup-protocol.md` (items (1)-(22); (22) is this session's),
`docs/evidence/gamma-lief-relayout.md` (sessions 101-104). The session may run on the cluster's interactive partition
(small tests and diagnostics in the allocation) or on the head node (light work only; tests and diagnostics through
`sbatch`). Other tracks: `docs/resume-prompt-writing.md`, `docs/resume-prompt-theory.md`, `docs/resume-prompt.md`
(general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3) replaces every number. Detectors: unconstrained,
monotone-features, monotone-sums (the two guaranteed ones), additions-only, adversarial-training, pv, trial,
iterated-2, and ERDALT (Gimenez et al.'s learned defense). Attacks: Gimenez et al.'s eight secml-malware attacks (the
"toolkit"), our adaptive search, MAB-Malware (three settings: ours, expert, zainab).

Operations (`src/provexp/featuresets/ember2024/directions.py`, `OPS`), fourteen: additions `app sec imp` (M_add);
insertions `ext shf hgr` (M_shift; `hgr` grows the headers so new section headers fit); overwrites `slk dos hdr chk ren
rdb rsg ent` (M_full). The validity rule (`src/provexp/attacks/validity.py`): an output counts only if pefile and LIEF
both read it and neither lost a section (by virtual address), DLL or imported function the original had.

## 2. What session 105 did

1. **Read the old round with the user** (session 85's chain), looking only for red flags before a rerun:
   - *Toolkit:* GAMMA API carries almost all of its evasions. Explained: it switches on ~1,006 of the 1,024 hashed
     import-function features (2-5 logits), also through our writers (`artifacts/scaleup/diag/s105/gamma_api_why.py`).
     The five byte-level attacks barely move our GBDT; checked rather than explained away: their edits reach the
     features and the scored file is the edited one (`diag/s105/toolkit_reach.py`), and against secml-malware's
     pretrained MalConv the same code and budget evade 16, 14, 9, 6, 5 of 20 (`diag/s105/malconv_control.py`). Not a
     bug: they were built for byte-level models.
   - *Adaptive search:* 888 of its 932 evasions of the unconstrained detector clone a signature (`ent`); expected
     (decisions.md, around line 208).
   - *MAB-Malware at Zainab et al.'s setting:* 52% against their 83.4%. Accepted (user): their detector (the official
     EMBER2024 model) and malware (VirusShare/Dike/MalwareBazaar files all eight of their models detect, Cuckoo
     executability) differ; code randomization is not the cause (they too ran seven actions; Song et al. attribute
     0.28% of EMBER evasions to code sequences). Both papers are in `papers/`.
   - *Validity rejections:* small and mostly LIEF-era GAMMA; *ERDALT's folds:* as settled (AUC 0.978-0.984, criterion
     unmet).
2. **Decided (user; protocol item (22)):** every toolkit attack and the training material at the GAMMA paper's budget
   (`literature`: 51 iterations, 75 donors); the byte cap max(5%, 512 KiB) replaced by one rule for every attack and
   the material: **an output counts only if it is at most 4,000,000 bytes** (`provexp.detectors.byte_room`; the study
   concerns PE files up to 4 MB); the weak toolkit attacks stay in this round, in an appendix, and are dropped before
   the final submission (which reruns everything); `hgr` added to the adaptive search (section and import candidates
   grow the headers first where no slot is free, as GAMMA does; `header_growth` per result) and to the iterated
   detector's search. Later methodology changes go on the **next-round list** at the end of
   `docs/scaleup-protocol.md`, applied together in a later full rerun, never one by one (user).
3. **The rerun was smoke-tested end to end** (`diag/s105/smoke/`: toolkit, material and merge, MAB, adaptive with
   `hgr`, and `scaleup_tables.py` on their outputs), the full suite passed (2,058), and the old round was moved to
   `artifacts/scaleup/superseded-s105/` (README inside). **The user submitted the chain** on 2026-11-23:
   `SKIP="3-directions/derived 3-directions/gate 1-audit/catalogue-checks" bash pipeline/submit.sh`, jobs
   1260382-1260399 (`logs/submit-20261123-141442.txt`). The gate was skipped under PLAN.md decision 12 (the training
   table covers every evaluation cell plus 265). The first four jobs (population, item-checks, trial, train) started
   cleanly.

## 3. What this session does (stop and report at each result)

1. **Check the chain once** (`squeue -u $USER`; `sacct -u $USER -S 2026-11-23 -X
   --format=JobID%16,JobName%20,State,Elapsed,Timelimit,AllocCPUS,TotalCPU,ReqMem`). For a failed job read its log
   (`logs/<name>_<id>.out`, then the step's own log the first lines name), find the cause, fix it at its source, and
   tell the user before resubmitting (`bash pipeline/submit.sh` with SKIP for the finished steps; every step skips
   finished work). Read the first log of any job that started since the last check. Do not watch the queue.
   Expected order and length: audits and trial (minutes; hand-table ~2 h), train (~10 min), material (10 shards, est.
   2-6 h each, limit 8 h), learned (GBDTs ~20 min; ERDALT 9 models ~6-7 h each on GPUs), iterated (~3 h), toolkit
   (29 tasks, est. up to ~8 h, limit 12 h), adaptive (81 tasks, ~1 h each, limit 4 h), MAB (~3 h), results.
2. **Right-size from sacct** each finished step (Elapsed, TotalCPU, MaxRSS against the request) and edit its header.
   The new limits (toolkit 12 h / 72 GB, material 8 h / 80 GB, adaptive 4 h) are estimates from a few smoke files.
3. **When `6-results` is done, read the new round with the user**, result by result, plainly: the detection table,
   each attack's still-detected share per detector (`artifacts/scaleup/6-results/tables/still_detected.csv`), the
   toolkit per attack and per escape, the leave-one-out folds, the adaptive search (how often `hgr` was used:
   `header_growth`), MAB's three settings, the validity rejections by cause (list the "pefile only" ones: extractor
   quirks to weigh with the user), the bytes added (median; the 4 MB rule), coverage and ERDALT's hole. Hypothesis
   before reading: the guaranteed detectors 0 in their population; gamma_api still the strongest toolkit attack but
   weaker than under LIEF and not applicable to 114 test malware; GAMMA sections somewhat stronger at the larger
   budget; the byte-level attacks unchanged.
4. **Then, with the user's approval:** PV's sample-size experiment (protocol item (17), approved and deferred until
   after the reruns); the numbers into the manuscript (writing track).

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On an interactive node: use only the allocation; worker pools under `if __name__ == "__main__":`, diagnostic Python
  in a file under `artifacts/scaleup/diag/` (this session's: `diag/s105/`), never from stdin; diagnostics need
  `FILE_STORE=artifacts/scaleup/2-features/files/files.sqlite` and `PYTHONHASHSEED=0`. Read files by name from the
  file store, never from the SimpleDB. Artifacts live under `/shared/rc/admalware/provexp` (the main checkout's
  `artifacts` link). Jobs longer than ~10 minutes or larger than the allocation go through `sbatch` after asking. Kill
  by PID, never `pkill -f`.
- Do not watch the queue: check once, report, hand back.
- A plan (and the user's approval) before an experiment; a hypothesis before running; report failed checks as such;
  fix failures at their source. The user decides protocol questions; Claude recommends, plainly.
- **The user wants meaning, not raw numbers:** say whether a result supports the research direction and what it
  changes; go slowly after a break (user, session 105).
- Methodology changes go on the next-round list, not into a rerun of their own (user, session 105).
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push.
- At the end: `docs/status.md`, PLAN.md, `docs/scaleup-protocol.md` (a new item for any decision), and this prompt
  rewritten self-contained (archive this one under `docs/archive/` and list it in `docs/README.md`).

## 5. Noted for later

- The next-round list (`docs/scaleup-protocol.md`, end): drop the ineffective toolkit attacks (criterion to state);
  optional, the adaptive search without signature cloning; optional, MAB-Malware against the official EMBER2024 model.
- `scaleup_tables.py`'s not-applicable rows join a job's `room_check.parquet` names with every defense row of the
  attack, although a defense attacks only the files it detects; check this when `6-results` is read.
- The byte-level attacks stop early once their search stagnates, so the literature budget barely changes them (smoke:
  same run time as before); worth one sentence where the paper states the budget.
- An operation that reaches files with no header room (e.g. growing the last section) is the only way to recover the
  114 files for gamma_api; noted, not planned (user, session 103).
- `pipeline/5-attacks/toolkit/pv_attacks.py` is pilot-era with no applicability gate; gate or retire it if ever run.
- Not checked: whether Windows loads a file whose section table runs past SizeOfHeaders; whether Windows loads GAMMA's
  consecutive empty sections at one RVA.
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
