# Resume: the scale-up's experiments (read session 102's reruns; GAMMA through our own writers; validity by sets)

Written at the end of session 102 (2026-11-20, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs
reading first, plus `docs/evidence/gamma-lief-relayout.md` (sessions 101-102's record and plan; section 5 is session
102) before item 1. The session may run on the cluster's interactive partition (small tests and diagnostics directly
in the allocation) or on the head node (light work only; tests and diagnostics through `sbatch`). Other tracks:
`docs/resume-prompt-writing.md`, `docs/resume-prompt-theory.md`, `docs/resume-prompt.md` (general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`, items
(1)-(19)) replaces every number. Detectors: unconstrained, monotone-features, monotone-sums (the two guaranteed ones),
additions-only, adversarial-training, pv, trial, iterated-2 (learned from attack outputs or trial edits), and ERDALT
(Gimenez et al.'s learned defense). Attacks: Gimenez et al.'s eight secml-malware attacks (the "toolkit"), our adaptive
search, MAB-Malware. Every output counts only under one validity rule (`src/provexp/attacks/validity.py`).

The threat models' operations (`src/provexp/featuresets/ember2024/directions.py`, `OPS`), fourteen since session 102:
additions `app sec imp` (M_add); insertions `ext shf hgr` (M_shift adds them); overwrites `slk dos hdr chk ren rdb rsg
ent` (M_full adds them). The population (where the guarantee holds) is `catalogue.precondition`: nothing located past
the end of the file, and `plain_layout`'s five layout clauses.

## 2. Where things stand

**Every detector but ERDALT has been retrained and attacked on the current material** (session 85's chain, all
COMPLETED 2026-11-18); **none of it has been read with the user.** Claude's quick tally (session 94), evaded / detected
of 1,000 test malware at 1% FPR:

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

The unconstrained toolkit column is almost all gamma_api. ERDALT: settled (validation 0.978, test 0.981; criterion not
met; record `docs/erdalt-diagnosis-plan.md`); its eight leave-one-out folds run as job **1239350** (~6.7 h each; tasks
1-4 running at the end of session 102, 5-8 pending) on the current material; the rerun on new material replaces them.

**Session 101:** the guaranteed detectors' four toolkit evasions are outside the threat model through LIEF's rebuild
(no soundness failure); the validity rule compares *counts*, missing losses hidden by additions in ~1-2% of GAMMA
outputs. **Decided (user):** GAMMA's edits written by our byte-level writers; the validity rule compares sets; reruns
acceptable (prototyping); the current round's numbers go into the manuscript meanwhile.

**Session 102 (evidence section 5), all on `main` unless noted:**
- **`hgr`, header growth, the fourteenth operation** (user: an operation, not a variant of `shf`):
  `catalogue.write_header_growth` / `predict_header_growth` insert a FileAlignment-multiple gap at SizeOfHeaders and
  raise it, so new section headers fit (`new_section_slot`). Declared: the insertion plus SizeOfHeaders up (no body
  change). The debug entries' file offsets stay stale (user; raising them would write body bytes). Exact on both
  extractors; on 40 files the table is unchanged but for the new column. Room for GAMMA's 30 headers: 808 of 1,000 test
  malware (97 already, 711 after growth); the other 192 have data after the section table (85), section data in the
  headers (52), a first RVA too low for 30 (42), a directory in the gap (8), other (3).
- **A fifth layout clause:** the section table ends within SizeOfHeaders (`catalogue.section_table_end`; user). It
  closes the population table's only violations in the 2026-11-18 catalogue check (`pass: False`, unrecorded until
  session 102: `ext` and `shf` writing body bytes on two files whose table runs into the body).
- **The file store holds all 20,000 training files** (user: the SimpleDB is fast to iterate, slow by name; files read
  by name repeatedly belong in the store). **Not yet on `main`:** the derivation reading from the store by default
  (commit b7b104a on branch `hgr`, worktree `../ProvExp-hgr`); fast-forward `main` to it once job 1243542 has finished
  (its four Python runs each read `directions.py` when they start).
- **Running at the end of session 102** (`logs/submit-*-s102-hgr.txt`): `directions` **1243542** (the strict and loose
  tables and the evaluation-set check, from the SimpleDB; ~55 min), `catalogue-checks` **1243543** (afterok; ~1.5 h),
  `file-store` **1243547** (~15 min). Before-images for comparison: `artifacts/scaleup/diag/before-s102/`
  (`3-directions/{strict,loose,check}`, `1-audit/{report,chains}.json`, `edits.parquet`).

## 3. What this session does (stop and report at each result)

Code changes go in the worktree `../ProvExp-hgr` (branch `hgr`; `PYTHONPATH=<worktree>/src`; its `artifacts` links
to `/shared/rc/admalware/provexp`, its `tests/data` to the main checkout's; run tools as `../ProvExp/env/bin/...`) and
are fast-forwarded to `main` once verified. **ERDALT's folds import `src/provexp` when they start** (check `squeue -u
$USER` once): until tasks 5-8 have started, do not merge changes to what they import (`provexp.attacks.toolkit`,
`models.erdalt`, `models.mlp`, `featuresets.ember2024.features`, `reach`, `items`, `provenance`, `boxmatrix`,
`metrics`, `data.tabular`, `data.paths`); `catalogue`, `directions`, `edits`, `validity`, `population` are not imported.

1. **Read session 102's reruns** (`sacct -j 1243542,1243543,1243547`). (a) The tables: `compare_tables.py --table
   artifacts/scaleup/3-directions/loose --check artifacts/scaleup/diag/before-s102/3-directions/loose` (and strict;
   it compares the operations both have). Hypothesis: no threat-model direction and no detector input file changes
   (then the guaranteed detectors need no retraining); the fifth clause can only make the population table stricter.
   The population size from `3-directions/logs/directions-loose.log`/`g3.json` (`precondition_files`) against the old
   run's. (b) The catalogue check (`artifacts/scaleup/1-audit/catalogue/report.json`): expected `pass: True`,
   `closed: True`, `hgr` exact; any violation is a finding to trace, not to discard. (c) The store
   (`2-features/files/files.json`: 22,200 stored). Then fast-forward `main` to the worktree's b7b104a (the derivation
   reads the store) if 1243542 has finished. Right-size the three headers from sacct.
2. **GAMMA written by our writers.** In `src/provexp/attacks/toolkit.py`, subclass or wrap secml-malware's
   `CGammaSectionsEvasionProblem.apply_feasible_manipulations` and `CGammaAPIEvasionProblem`'s (vendored in
   `third_party/secml_malware/`; do not edit upstream code) so the chosen edit is written by `catalogue.write_section`
   (sections after the overlay, `before_overlay=False`, as the adaptive search does), growing the headers with
   `catalogue.write_header_growth` when the slots run out, and by one multi-library `write_imports` (a pure addition:
   today it takes one library; GAMMA adds functions to DLLs the file already imports, which gives them a second
   descriptor, handled by `merge_import_descriptors`). The search is unchanged. **Decide with the user** what happens
   when GAMMA picks more sections than fit even after growth (192 of 1,000 test malware cannot take 30): write the
   ones that fit, or the file is not applicable. Keep a structural check as an assertion (no data directory moved but
   those the declared edit writes, section bodies and overlay kept, nothing lost). Smoke test: speed (up to 30 writes
   per query) and the four session-101 files (`artifacts/scaleup/diag/gamma_evasion.py` re-runs them).
   `LIEF_ATTACKS`/`lief_check` then no longer gate GAMMA; decide what replaces it. `toolkit.py` is imported by ERDALT:
   merge only after tasks 5-8 have started. `pipeline/6-results/toolkit_split.py` and `coverage.py` map attacks to
   operations: GAMMA becomes `sec`/`imp` plus `hgr` where growth was used.
3. **The validity rule by sets.** `output_invalid` compares sets per parser: sections as a multiset of names, DLLs by
   lowercase name, functions by (lowercase DLL, name or ordinal) (the comparison in
   `artifacts/scaleup/diag/validity_sets.py`, `parsed`/`compare`). Keep the reason strings' "pefile only" prefix.
   Tests. Not imported by ERDALT: may go to `main` once verified.
4. **The reruns** (the user's call on what and when; work out processes, threads, cores and memory first): the
   toolkit (every part), the material (`pipeline/5-attacks/toolkit/pv_attacks.py`,
   `pipeline/4-detectors/adversarial-training/attack_training.py`), the learned defenses (pv, ERDALT, adversarial-
   training, iterated-2) and their attacks; the adaptive search may use `hgr` (its operation lists are in
   `src/provexp/attacks/adaptive.py:50`, `INSERT`, and `:719`; 283 test malware have no free header slot today);
   MAB-Malware's validity under the new rule; the guaranteed detectors only if item 1 shows a direction change. Then
   `6-results`.
5. **Meanwhile, with the user:** read every current result (the table above with the toolkit's `escape` and `loo`
   parts, the adaptive search's escapes and `expert`, MAB `expert` and `zainab` against Zainab et al.'s 83%, the
   validity counts and the "pefile only" rejections by cause); PV's setup against Gimenez et al.'s (theirs 1,033
   vectors, ours 78,715; PV's sample-size experiment, `docs/scaleup-protocol.md` item (17), approved and deferred).
6. **When ERDALT's folds are done** (`sacct --name=learned-erdalt -S 2026-11-20`): R19's asks
   (`docs/reviews/2026-11-12-body/meta-review.md`) and ERDALT's attacks (as in
   `logs/submit-20261117-181439-no-erdalt.txt`); its toolkit run waits for item 2 if the rerun is near.
7. **Right-size from sacct** every finished step (`sacct -u $USER -S 2026-11-18 --format=JobID%16,JobName%20,State,
   Elapsed,Timelimit,AllocCPUS,TotalCPU,MaxRSS,ReqMem`), finished steps' headers too.

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On an interactive node: use only the allocation; worker pools under `if __name__ == "__main__":`, diagnostic Python
  in a file under `artifacts/scaleup/diag/`, never from stdin; diagnostics need `FILE_STORE=artifacts/scaleup/2-
  features/files/files.sqlite` and `PYTHONHASHSEED=0`. **Read files by name from the file store, never from the
  SimpleDB** (slow by name; on this cluster the SimpleDB is `/shared/rc/admalware/datasets/EMBER-2024/data`, not
  CLAUDE.md's path). Artifacts live under `/shared/rc/admalware/provexp` (the main checkout's `artifacts` link), not
  `/scratch`. Jobs longer than ~10 minutes or larger than the allocation go through `sbatch` after asking. Kill by
  PID, never `pkill -f`.
- **Do not watch the queue.** Check once, report, hand back. Read every new job's log within ~2 minutes of its start.
- Before submitting or changing a step, work out the processes, threads, cores and memory it uses; say plainly what was
  not checked.
- A plan (and the user's approval) before an experiment; a hypothesis before running; report failed checks as such;
  fix failures at their source. The user decides protocol questions; Claude recommends, explaining plainly.
- Changes to the thrember-derived `features.py` are pure additions; `tests/reference/` is never edited.
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push. In the worktree, `git
  add` only named paths (its `tests/data` link is excluded via `.git/info/exclude`, but check `git status`).
- At the end: `docs/status.md`, PLAN.md, and this prompt rewritten self-contained.

## 5. Noted for later

- The writing track: the operations table gains `hgr` (a shift); §4.4's population gains the fifth clause; GAMMA
  becomes additions plus, on files without header room, a shift (noted in `docs/status.md`, "Waiting on the user").
- Not counted: how many training and test files the fifth clause excludes (item 1 gives it).
- Not checked: whether Windows loads a file whose section table runs past SizeOfHeaders (the clause does not depend
  on it).
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
  `diag/derive-store-smoke/`.
