# Resume: the scale-up's experiments (merge GAMMA through our writers; validity by sets; the reruns)

Written at the end of session 103 (2026-11-20, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs
reading first. Background for items 1-2, when needed: `docs/evidence/gamma-lief-relayout.md` (sessions 101-103; section
6 is session 103). The session may run on the cluster's interactive partition (small tests and diagnostics directly
in the allocation) or on the head node (light work only; tests and diagnostics through `sbatch`). Other tracks:
`docs/resume-prompt-writing.md`, `docs/resume-prompt-theory.md`, `docs/resume-prompt.md` (general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`, items
(1)-(20)) replaces every number. Detectors: unconstrained, monotone-features, monotone-sums (the two guaranteed ones),
additions-only, adversarial-training, pv, trial, iterated-2 (learned from attack outputs or trial edits), and ERDALT
(Gimenez et al.'s learned defense). Attacks: Gimenez et al.'s eight secml-malware attacks (the "toolkit"; GAMMA
sections and GAMMA API among them), our adaptive search, MAB-Malware. Every output counts only under one validity
rule (`src/provexp/attacks/validity.py`): pefile and LIEF both read it and neither lost a section or import.

The threat models' operations (`src/provexp/featuresets/ember2024/directions.py`, `OPS`), fourteen: additions `app sec
imp` (M_add); insertions `ext shf hgr` (M_shift adds them; `hgr` grows the headers so new section headers fit);
overwrites `slk dos hdr chk ren rdb rsg ent` (M_full adds them). The population (where the guarantee holds) is
`catalogue.precondition`: nothing located past the end of the file, and `plain_layout`'s five layout clauses (the
fifth since session 102: the section table ends within SizeOfHeaders). Training population: 18,450 of 19,983 PE files.

## 2. Where things stand

**The current round of results (session 85's chain, finished 2026-11-18) is unread with the user.** It predates
everything below, so the reruns (item 4) replace it; meanwhile its numbers go into the manuscript (user). Claude's
quick tally, evaded / detected of 1,000 test malware at 1% FPR:

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

The unconstrained toolkit column is almost all gamma_api (598); gamma_sections evades 1 file over five detectors (most
of its outputs exceed the byte budget, `max(5% of the size, 512 KiB)`, as under LIEF: 590 of 950). The guaranteed
detectors' four toolkit evasions were LIEF's rebuild moving structures outside the threat model (session 101).

**ERDALT:** settled (validation 0.978, test 0.981; its criterion not met; `docs/erdalt-diagnosis-plan.md`). Its eight
leave-one-out folds run as job **1239350**: tasks 1-4 completed (~5.9 h each); at the end of session 103 **tasks 5-8
were pending** (Priority).

**Session 103 (all recorded in `docs/evidence/gamma-lief-relayout.md`, section 6):**
- *Session 102's reruns read.* The catalogue check passes (`pass`, `closed`, `exact`; `hgr` exact; the `ext`/`shf`
  violations 32/24 -> 0; `exact_all_files: False` and `ext`'s 20 wrong declarations are pre-existing, outside the
  population). M_add's and M_shift's detector inputs are byte-identical to before; **M_full changed**: 352 body
  features (256 `body_byteentropy`, 96 `body_strings` printable distribution) go from "both" (dropped) to "up" (kept,
  monotone), because the fifth clause drops the 24 training files on which `ren` wrote body bytes. **Decided (user):
  monotone-features, monotone-sums and the price list are retrained in the reruns** (they read `M_full-pre.*`,
  `pipeline/4-detectors/train/run.sh:77`; the current ones stay sound, only stricter than needed). The file store holds
  22,000 distinct files (all 20,000 training, 2,000 test; the 200 donors are training files). The derivation reads the
  store by default (on `main`). Right-sized: `directions` 280G, `file-store` 64G.
- *GAMMA through our writers, option A (user).* GAMMA's search is unchanged; each query's edit is written by our
  writers: `gamma_sections` adds one section per donor on every query (30 at the low budget, 75 at the literature one;
  a zero gene gives an empty section; characteristics 0, as LIEF writes them; after the overlay), `gamma_api` one
  import section holding every chosen library (`catalogue.write_import_libraries`; a function the library already has
  is not added again; ordinals skipped). A file whose headers lack room grows them first by the smallest gap
  (`catalogue.grow_headers_for`, 512-1,536 bytes; such outputs lie in M_shift; `header_growth` per row); **where no
  growth makes room the attack is not applicable** (`room_check.parquet`, counted as `not_applicable`): 192 of 1,000
  test malware for gamma_sections, 114 for gamma_api (52 of gamma_api's 598 unconstrained evasions were on those).
  `toolkit.structure_kept` asserts every output kept the start file's structure. The room check replaces LIEF's round
  trip (`lief_check`) as GAMMA's gate in `pipeline/5-attacks/toolkit/toolkit.py` and
  `pipeline/4-detectors/adversarial-training/attack_training.py`; `6-results/scaleup_tables.py` counts it;
  `toolkit_split.py` maps GAMMA to `sec`/`imp` plus `hgr`. Checks: the room count matches an independent count on all
  1,000 test malware; tests (`tests/test_toolkit_gamma.py`, catalogue tests; full suite 2,013 passed); smoke
  (`artifacts/scaleup/diag/s103/gamma_smoke.py`, and the toolkit step on 24 malware in `diag/s103/toolkit-smoke/`):
  10-50 s per run as under LIEF, every output valid, every in-population original's output in the population.
  Session 101's four evasions are gone (three not applicable, one no longer evades: 0.964). **The import attack is
  weaker without LIEF's rebuild** on some files (p_adv 0.68 vs 0.04, 0.79 vs 0.09, 0.51 vs 0.20; 13/20 vs 15/20
  evaded in the step smoke): expect the unconstrained toolkit number to fall by more than the 52.
- *Where the code is.* The catalogue part (`write_import_libraries`, `section_slots`, `grow_headers_for`) is on
  `main`. **Two commits wait on branch `hgr`** (worktree `../ProvExp-hgr`): "Toolkit: GAMMA's sections and imports
  written by our writers ..." and "Pipeline: GAMMA's room check (room_check.parquet) replaces LIEF's round trip ...".
  They change `provexp.attacks.toolkit`, which ERDALT's folds import when they start.

## 3. What this session does (stop and report at each result)

Code changes go in the worktree `../ProvExp-hgr` (branch `hgr`; run with `PYTHONPATH=$PWD/src` there, since the venv's
editable install points at the main checkout; its `artifacts` links to `/shared/rc/admalware/provexp`, its
`tests/data` to the main checkout's; tools as `../ProvExp/env/bin/...`) and are fast-forwarded to `main` once
verified. **ERDALT's folds import `src/provexp` when they start:** until tasks 5-8 of 1239350 have started, do not merge
changes to what they import (`provexp.attacks.toolkit`, `models.erdalt`, `models.mlp`,
`featuresets.ember2024.features`, `reach`, `items`, `provenance`, `boxmatrix`, `metrics`, `data.tabular`,
`data.paths`); `catalogue`, `directions`, `edits`, `validity`, `population` are not imported.

1. **Merge GAMMA through our writers.** `squeue -u $USER` once (and `sacct --name=learned-erdalt -S 2026-11-20` for the
   finished tasks). If tasks 5-8 are running or done: in the worktree, `git rebase main`, then in the main checkout
   `git merge --ff-only hgr`; ruff and strict mypy on `src tests pipeline` first. If still pending, keep the commits on
   `hgr` and do item 2 there meanwhile (item 2 touches only `validity`, which may go to `main` at once).
2. **The validity rule by sets** (decided by the user in session 101; the count comparison misses a lost DLL hidden by
   added ones: ~1-2% of GAMMA outputs under LIEF). Today `validity.Structure` holds six counts and `output_invalid`
   flags a count that fell. Make it compare sets per parser: DLLs by lowercase name; functions by (lowercase DLL, name
   or ordinal); keep the reason strings' "both" / "pefile only" / "lief only" prefix (the "pefile only" rejections are
   logged as extractor quirks). Session 101's reference comparison: `artifacts/scaleup/diag/validity_sets.py`
   (`parsed`, `compare`). **Decide with the user how sections are identified before coding:** session 101 planned a
   multiset of names, but the adaptive search (`ren`) and MAB-Malware rename sections, so a name multiset would reject
   every rename as a lost section. Options to put to the user: keep sections as a count (renames pass; a lost section
   hidden by an added one is missed, which GAMMA cannot cause now that it only adds); identify a section by its raw
   range (PointerToRawData, SizeOfRawData) shifted by any insertion; or names except for the operations that rename.
   Recommend after looking at what each attack can do to the section table. `Structure` is computed in the main
   process and sent to workers (`toolkit.py`, `attack_training.py`, `adaptive.py`, `mab.py`, `trial_probe.py`,
   `catalogue_checks.py` all import the module): keep it a small picklable value. Tests in `tests/test_validity.py`
   (a loss hidden by an addition must now be caught). Then measure on the smoke outputs and on a sample of the current
   round's outputs how many verdicts change (hypothesis: only GAMMA's LIEF-era outputs, ~1-2%). Not imported by ERDALT:
   to `main` once verified.
3. **Read with the user** (meanwhile, or when they ask): every current result (the table above, the toolkit's
   `escape` and `loo` parts, the adaptive search's escapes and `expert`, MAB `expert` and `zainab` against Zainab et
   al.'s 83%, the validity counts and the "pefile only" rejections by cause); PV's setup against Gimenez et al.'s
   (theirs 1,033 vectors, ours 78,715; PV's sample-size experiment, `docs/scaleup-protocol.md` item (17), approved and
   deferred until after the reruns).
4. **The reruns** (the user's call on what and when; plan them with the user first, and work out processes, threads,
   cores and memory for each step before submitting; the submission scripts are `pipeline/submit.sh` and the steps'
   `run.sh`). What needs rerunning:
   - the guaranteed detectors **monotone-features and monotone-sums** (`4-detectors/train`; decided, M_full changed)
     and **the price list** (`4-detectors/price-list`), then their attacks;
   - the **toolkit**, every part (`5-attacks/toolkit/run.sh`: main, escape, loo, donors-0), with GAMMA through our
     writers;
   - the **material** (`4-detectors/adversarial-training/attack_training.py`, the toolkit run on training malware) and
     the **learned defenses** built from it (pv, adversarial-training, iterated-2, ERDALT) and their attacks;
   - **MAB-Malware**'s validity under the new rule (re-judging its outputs may suffice if they are kept; check);
   - optionally the **adaptive search with `hgr`** (its operation lists: `src/provexp/attacks/adaptive.py:50`,
     `INSERT`, and `:719`; 283 test malware have no free header slot today);
   - then `6-results`.
   ERDALT's attacks (as in `logs/submit-20261117-181439-no-erdalt.txt`) wait for its folds and, if the rerun is near,
   for item 1. R19's asks (`docs/reviews/2026-11-12-body/meta-review.md`) when the folds are done.
5. **Right-size from sacct** every finished step (`sacct -u $USER -S 2026-11-18 --format=JobID%16,JobName%20,State,
   Elapsed,Timelimit,AllocCPUS,TotalCPU,MaxRSS,ReqMem`), finished steps' headers too.

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On an interactive node: use only the allocation; worker pools under `if __name__ == "__main__":`, diagnostic Python
  in a file under `artifacts/scaleup/diag/` (session 103's are in `diag/s103/`), never from stdin; diagnostics need
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
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push. In the worktree, `git
  add` only named paths (its `tests/data` link is excluded via `.git/info/exclude`, but check `git status`).
- At the end: `docs/status.md`, PLAN.md, `docs/scaleup-protocol.md` (a new item for any decision), and this prompt
  rewritten self-contained (archive this one under `docs/archive/` and list it in `docs/README.md`).

## 5. Noted for later

- The writing track (`docs/status.md`, "Waiting on the user"): the operations table gains `hgr` (a shift); §4.4's
  population gains the fifth clause; GAMMA becomes additions plus, on files without header room, a shift, and is not
  applicable where no growth makes room (192 / 114 of 1,000 test malware); the import attack weaker without LIEF's
  rebuild (a sentence once the rerun is read).
- An operation that reaches files with no header room (e.g. growing the last section to hold the new content) is the
  only way to recover the 114 files for gamma_api; noted, not planned (user, session 103).
- `pipeline/5-attacks/toolkit/pv_attacks.py` is a pilot-era script with no applicability gate; under our writers a
  file without room raises `NotApplicable` there and is counted as a failed run. Gate it or retire it if it is ever
  run again.
- `scaleup_tables.py`'s not-applicable rows pair each name of a job's check files with every defense of the job (as
  the LIEF check did), although a defense attacks only the files it detects; check this when `6-results` is read.
- Not checked: whether Windows loads a file whose section table runs past SizeOfHeaders (the clause does not depend
  on it); whether Windows loads GAMMA's consecutive empty sections at one RVA (LIEF wrote the same).
- `pipeline/setup/identity_check.sh` compares with the pilot-final baseline, which sessions 102-103's intended changes
  (`hgr`, the fifth clause) already break; re-baseline it after the reruns if it is to stay useful.
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
  `diag/derive-store-smoke/`, `diag/s103/gamma-smoke/`, `diag/s103/toolkit-smoke/`.
