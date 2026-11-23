# Resume: the scale-up's experiments (read the current results; plan and run the reruns)

Written at the end of session 104 (2026-11-23, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs
reading first. Background, when needed: `docs/evidence/gamma-lief-relayout.md` (sessions 101-104; section 6 is GAMMA
through our writers, section 7 the validity rule by sets), `docs/scaleup-protocol.md` (items (1)-(21)). The session
may run on the cluster's interactive partition (small tests and diagnostics directly in the allocation) or on the head
node (light work only; tests and diagnostics through `sbatch`). Other tracks: `docs/resume-prompt-writing.md`,
`docs/resume-prompt-theory.md`, `docs/resume-prompt.md` (general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3) replaces every number. Detectors: unconstrained,
monotone-features, monotone-sums (the two guaranteed ones), additions-only, adversarial-training, pv, trial,
iterated-2 (learned from attack outputs or trial edits), and ERDALT (Gimenez et al.'s learned defense). Attacks:
Gimenez et al.'s eight secml-malware attacks (the "toolkit"; GAMMA sections and GAMMA API among them), our adaptive
search, MAB-Malware.

The threat models' operations (`src/provexp/featuresets/ember2024/directions.py`, `OPS`), fourteen: additions `app sec
imp` (M_add); insertions `ext shf hgr` (M_shift adds them; `hgr` grows the headers so new section headers fit);
overwrites `slk dos hdr chk ren rdb rsg ent` (M_full adds them). The population (where the guarantee holds) is
`catalogue.precondition`: nothing located past the end of the file, and `plain_layout`'s five layout clauses (the
fifth: the section table ends within SizeOfHeaders). Training population: 18,450 of 19,983 PE files.

**The validity rule** (`src/provexp/attacks/validity.py`; by sets since session 104): an output counts only if pefile
and LIEF both read it and neither lost anything the original had: a section (identified by its virtual address, as a
multiset; renames, shifts, growth and slack writes pass), an imported DLL (lowercase name) or an imported function
((lowercase DLL, name or `#ordinal`)). Reasons start "both", "pefile only" (logged as extractor quirks) or "lief only".

**GAMMA through our writers** (session 103, on `main` since session 104): GAMMA's search is unchanged, each query's
sections or imports are written by our byte-level writers (no LIEF rebuild); headers are grown by the smallest gap
only when they lack room (`header_growth` per row; such outputs lie in M_shift); where no growth makes room the attack
is not applicable (`room_check.parquet`: 192 of 1,000 test malware for gamma_sections, 114 for gamma_api). The import
attack is weaker without LIEF's rebuild on some files.

## 2. Where things stand

Nothing runs (`squeue` empty at the end of session 104 but for the interactive job). ERDALT's eight leave-one-out folds
(job 1239350) finished on 2026-11-21, unread.

**The current round of results (session 85's chain, finished 2026-11-18) is unread with the user.** It predates GAMMA
through our writers, the fifth clause's change to M_full and the validity rule by sets, so the reruns replace it;
meanwhile its numbers go into the manuscript (user). Claude's quick tally, evaded / detected of 1,000 test malware at
1% FPR:

| detector | toolkit (main) | adaptive (none) | MAB-Malware ours |
|---|---|---|---|
| unconstrained | 598 / 953 | 932 / 953 | 68 / 953 |
| monotone-features | 3 / 803 | 0 / 803 | 0 / 803 |
| monotone-sums | 1 / 802 | 0 / 802 | 0 / 802 |
| additions-only | 129 / 917 | 901 / 917 | 6 / 917 |
| adversarial-training | 46 / 959 | 934 / 959 | 15 / 959 |
| pv | 0 / 234 | 51 / 234 | 10 / 234 |
| trial | 187 / 876 | 623 / 876 | 192 / 876 |
| iterated-2 | 36 / 958 | 922 / 958 | 50 / 958 |

The unconstrained toolkit column is almost all gamma_api (598; 52 of them on the 114 files where gamma_api is now not
applicable); gamma_sections evades 1 file over five detectors. The guaranteed detectors' four toolkit evasions were
LIEF's rebuild moving structures outside the threat model (session 101); under our writers three are not applicable
and the fourth no longer evades.

What the changes did to the verdicts (session 104): the set rule changes none of the 1,217 kept outputs (MAB-Malware's
evasive and minimal, GAMMA smoke); on session 101's LIEF-era sample it rejects 2 of 150 gamma_api outputs more.

**ERDALT:** settled (validation 0.978, test 0.981; its criterion not met; `docs/erdalt-diagnosis-plan.md`). Its folds
are done; its attacks (as in `logs/submit-20261117-181439-no-erdalt.txt`) are not yet run.

## 3. What this session does (stop and report at each result)

1. **Read with the user** every current result: the table above, the toolkit's `escape` and `loo` parts, the adaptive
   search's escapes and `expert`, MAB `expert` and `zainab` against Zainab et al.'s 83%, the validity counts and the
   "pefile only" rejections by cause, ERDALT's folds (`artifacts/scaleup/4-detectors/erdalt-loo-*`); PV's setup
   against Gimenez et al.'s (theirs 1,033 vectors, ours 78,715; PV's sample-size experiment,
   `docs/scaleup-protocol.md` item (17), approved and deferred until after the reruns). Explain plainly; the user
   decides what each result means for the paper.
2. **Plan the reruns with the user** (their call on what and when), then submit. Work out processes, threads, cores
   and memory for each step before submitting (`pipeline/submit.sh`, the steps' `run.sh`); read every new job's log
   within ~2 minutes of its start. What needs rerunning:
   - the guaranteed detectors **monotone-features and monotone-sums** (`pipeline/4-detectors/train`; decided, M_full
     changed: they read `M_full-pre.*`, `train/run.sh:77`) and **the price list** (`4-detectors/price-list`), then
     their attacks;
   - the **toolkit**, every part (`5-attacks/toolkit/run.sh`: main, escape, loo, donors-0), with GAMMA through our
     writers and the set rule;
   - the **material** (`4-detectors/adversarial-training/attack_training.py`, the toolkit run on training malware) and
     the **learned defenses** built from it (pv, adversarial-training, iterated-2, ERDALT) and their attacks;
   - **MAB-Malware** under the set rule: it keeps only its evasive and minimal outputs, so re-judging them suffices
     for evasion counts (nothing changes, session 104), but its rejection counts by cause need a rerun (the user's
     call whether that matters);
   - optionally the **adaptive search with `hgr`** (its operation lists: `src/provexp/attacks/adaptive.py:50`,
     `INSERT`, and `:719`; 283 test malware have no free header slot today);
   - **ERDALT's attacks**; R19's asks (`docs/reviews/2026-11-12-body/meta-review.md`) now that the folds are done;
   - then `6-results`.
3. **Right-size from sacct** every finished step, finished steps' headers too (`sacct -u $USER -S 2026-11-18
   --format=JobID%16,JobName%20,State,Elapsed,Timelimit,AllocCPUS,TotalCPU,MaxRSS,ReqMem`); ERDALT's folds took
   ~5.9 h each.

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On an interactive node: use only the allocation; worker pools under `if __name__ == "__main__":`, diagnostic Python
  in a file under `artifacts/scaleup/diag/` (session 104's are in `diag/s104/`), never from stdin; diagnostics need
  `FILE_STORE=artifacts/scaleup/2-features/files/files.sqlite` and `PYTHONHASHSEED=0`. **Read files by name from the
  file store, never from the SimpleDB** (slow by name; on this cluster the SimpleDB is
  `/shared/rc/admalware/datasets/EMBER-2024/data`, not CLAUDE.md's path). Artifacts live under
  `/shared/rc/admalware/provexp` (the main checkout's `artifacts` link), not `/scratch`. Jobs longer than ~10 minutes
  or larger than the allocation go through `sbatch` after asking. Kill by PID, never `pkill -f`.
- **Do not watch the queue.** Check once, report, hand back. Read every new job's log within ~2 minutes of its start.
- Before submitting or changing a step, work out the processes, threads, cores and memory it uses; say plainly what was
  not checked.
- A plan (and the user's approval) before an experiment; a hypothesis before running; report failed checks as such;
  fix failures at their source. The user decides protocol questions; Claude recommends, explaining plainly: when a
  decision is the user's, lay out the options, how each affects later work, and a recommendation.
- Changes to the thrember-derived `features.py` are pure additions; `tests/reference/` is never edited.
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push.
- At the end: `docs/status.md`, PLAN.md, `docs/scaleup-protocol.md` (a new item for any decision), and this prompt
  rewritten self-contained (archive this one under `docs/archive/` and list it in `docs/README.md`).

## 5. Noted for later

- The writing track (`docs/status.md`, "Waiting on the user"): the operations table gains `hgr` (a shift); §4.4's
  population gains the fifth clause; GAMMA becomes additions plus, on files without header room, a shift, and is not
  applicable where no growth makes room (192 / 114 of 1,000 test malware); the import attack weaker without LIEF's
  rebuild (a sentence once the rerun is read); the validity rule's description in the paper becomes "lost none of the
  sections, DLLs and functions it had" (sets; sections by address) if it currently says counts.
- An operation that reaches files with no header room (e.g. growing the last section to hold the new content) is the
  only way to recover the 114 files for gamma_api; noted, not planned (user, session 103).
- `pipeline/5-attacks/toolkit/pv_attacks.py` is a pilot-era script with no applicability gate; under our writers a
  file without room raises `NotApplicable` there and is counted as a failed run. Gate it or retire it if it is ever
  run again.
- `scaleup_tables.py`'s not-applicable rows pair each name of a job's check files with every defense of the job (as
  the LIEF check did), although a defense attacks only the files it detects; check this when `6-results` is read.
- Not checked: whether Windows loads a file whose section table runs past SizeOfHeaders (the clause does not depend
  on it); whether Windows loads GAMMA's consecutive empty sections at one RVA (LIEF wrote the same).
- `pipeline/setup/identity_check.sh` compares with the pilot-final baseline, which sessions 102-104's intended changes
  (`hgr`, the fifth clause, the set rule) already break; re-baseline it after the reruns if it is to stay useful.
- Open with the user: move `docs/erdalt-diagnosis-plan.md` under `docs/evidence/`.
- ERDALT's logits reach +-8,007 on validation (temperature 266.9); worth a sentence if calibrated probabilities are
  ever reported.
- Toolkit task 9 (the debug-entry escape) once used 41% of its 36 cores with every attack 2-3x slower; if it recurs,
  `sstat` it while it runs.
- Per-item loops that may still run serially in a main process: `toolkit.py` and `mab.py` (feature extraction before
  the pool), `6-results` scripts, `expert_adaptive.py`. `mab.py` runs all detectors in one pool.
- Other steps that still read the SimpleDB by name (`--db`): `1-audit/deviations`, `population_clauses.py`,
  `escape_audit.py`, `trial_table.py` (the pilot's files); move them to the store when next touched.
- `third_party/README.md` lists MAB-Malware's patches but not 50f3e97's.
- `coverage.py` still accepts an unused `--db`.
- `adaptive.add_section`/`add_imports` (the LIEF writers) look unused by the search now; remove if so.
- Disposable: `artifacts/scaleup/diag/erdalt/smoke-s93/`, `diag/validity-sets-smoke/`, `diag/hgr-derive-smoke/`,
  `diag/derive-store-smoke/`, `diag/s103/gamma-smoke/`, `diag/s103/toolkit-smoke/`, `diag/s104/section-va*/`.
