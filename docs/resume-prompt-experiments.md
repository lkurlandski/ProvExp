# Resume: the scale-up's experiments (GAMMA through our own writers, the validity rule by sets; then the results)

Written at the end of session 101 (2026-11-20, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs
reading first, plus `docs/evidence/gamma-lief-relayout.md` (session 101's record and plan, short) before item 1. The
session may run on the cluster's interactive partition (small tests and diagnostics directly in the allocation) or
on the head node (light work only; tests and diagnostics through `sbatch`). Other tracks:
`docs/resume-prompt-writing.md`, `docs/resume-prompt-theory.md`, `docs/resume-prompt.md` (general work and the index).

## 1. The project in brief

ProvExp studies *sum-then-readout* feature extractors (find the items, add up each one's contributions, compute each
feature from a few totals). From the instrumented extractor we compute what an attacker's edits do to the features:
exactly for one edit, as sound directions for a whole threat model, and from those, monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper (`manuscript/*.tex`, ACM CCS format) is
drafted on pilot-scale numbers, and the scale-up (PLAN.md step 3; full record `docs/scaleup-protocol.md`, items
(1)-(18)) replaces every number. Detectors: unconstrained, monotone-features, monotone-sums (the two guaranteed ones),
additions-only, adversarial-training, pv, trial, iterated-2 (learned from attack outputs or trial edits), and ERDALT
(Gimenez et al.'s learned defense). Attacks: Gimenez et al.'s eight secml-malware attacks (the "toolkit"), our adaptive
search, MAB-Malware. Every output counts only under one validity rule (`src/provexp/attacks/validity.py`).

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

The unconstrained toolkit column is almost all gamma_api (598 of 598). ERDALT: settled (validation 0.978, test 0.981;
criterion not met; record `docs/erdalt-diagnosis-plan.md`); its eight leave-one-out folds run as job **1239350**
(~6.7 h each; task 1 started 2026-11-20) on the current material, and finish as they are: they give the current
round's leave-one-out table; the rerun on new material replaces them.

**Session 101 (`docs/evidence/gamma-lief-relayout.md`):** the guaranteed detectors' four toolkit evasions are outside
the threat model through LIEF's rebuild (relocated resource directory; WS2_32's ordinal imports destroyed; directories
rewritten); the declared edits alone raise the score; no soundness failure. The validity rule compares *counts* of
sections, DLLs and functions, so a loss hidden by additions passes: measured on 480 re-created outputs, 2/150 gamma_api,
1/150 gamma_sections, 0 elsewhere. LIEF moves the resource directory in ~60% of GAMMA outputs; `lief_preserves`
(`src/provexp/attacks/adaptive.py:201`) ignores data directories. Header room: 97 of 1,000 test malware fit GAMMA's 30
section headers in place (`catalogue.new_section_slot`), 992 after growing the headers up to the first section's RVA.

**Decided by the user (session 101):** (1) GAMMA's edits are written by our byte-level writers (the attack does not
depend on the parsing library; fidelity to Gimenez et al.'s LIEF rebuild is low priority); (2) the validity rule
compares sets; (3) reruns are acceptable (prototyping stage); (4) the current round's numbers go into the manuscript
while the reruns run (validity holds to ~1-2% on GAMMA rows).

## 3. What this session does (stop and report at each result)

Code changes go in a `git worktree` first (`PYTHONPATH=<worktree>/src`) and are fast-forwarded once verified:
**ERDALT's folds import `src/provexp` when they start** and tasks 2-8 may not all have started (`squeue -u $USER`
once); do not change what `models/erdalt.py` and `train_erdalt.py` import until they have.

1. **The header-growth variant of `shf`.** `catalogue.write_gap(at_pe_header=False)` inserts a FileAlignment-multiple
   gap before the first section's data and raises PointerToRawData and the certificate offset, but not SizeOfHeaders,
   so it makes no header room. Add a variant that also raises `SizeOfHeaders` (allowed only while SizeOfHeaders + gap
   <= the first section's RVA, SectionAlignment >= page), so `new_section_slot` finds room. While there, also raise the
   debug entries' `PointerToRawData` (a file offset; a pre-existing gap of `write_gap`). It is a shift (in M_shift and
   M_full, not M_add). Needed: its declared changes in the catalogue (how structural ops enter the derivation:
   `pipeline/3-directions/derived/directions.py`, `declared_changes`), its exact single-edit predictor and tests (as
   `shf`'s), a hand rule for the G3 oracle, and the table re-derived (`3-directions/derived`). Hypothesis: no direction
   changes (SizeOfHeaders is already up and `shf` is in M_full), so the guaranteed detectors need no retraining; check
   with `compare_tables.py` against `artifacts/scaleup/3-directions/loose/`. Rerun the closure check. Decide with the
   user whether it is a variant of `shf` (the paper's table stays at thirteen operations) or a fourteenth operation.
2. **GAMMA written by our writers.** In `src/provexp/attacks/toolkit.py`, subclass or wrap secml-malware's
   `CGammaSectionsEvasionProblem.apply_feasible_manipulations` and `CGammaAPIEvasionProblem`'s (vendored in
   `third_party/secml_malware/`; do not edit upstream code) so the chosen edit is written by `catalogue.write_section`
   (growing the headers when needed; sections after the overlay, `before_overlay=False`, as the adaptive search does)
   and by one multi-library `write_imports` (a pure addition: today it takes one library; GAMMA adds functions to DLLs
   the file already imports, which gives them a second descriptor, handled by `merge_import_descriptors`). The search
   is unchanged. Keep a structural check as an assertion (no data directory moved other than those the declared edit
   writes, section bodies and overlay kept, nothing lost). Smoke test: speed (up to 30 writes per query) and the four
   session-101 files (`artifacts/scaleup/diag/gamma_evasion.py` re-runs them). `LIEF_ATTACKS`/`lief_check` then no
   longer gate GAMMA; decide what replaces it (files our writer cannot take: not applicable).
3. **The validity rule by sets.** `output_invalid` compares sets per parser: sections as a multiset of names, DLLs by
   lowercase name, functions by (lowercase DLL, name or ordinal) (the comparison in
   `artifacts/scaleup/diag/validity_sets.py`, `parsed`/`compare`). Keep the reason strings' "pefile only" prefix.
   Tests.
4. **The reruns** (the user's call on what and when; work out processes, threads, cores and memory first): the
   toolkit (every part), the material (`pipeline/5-attacks/toolkit/pv_attacks.py`,
   `pipeline/4-detectors/adversarial-training/attack_training.py`), the learned defenses (pv, ERDALT, adversarial-
   training, iterated-2) and their attacks; the adaptive search may use the header growth (283 test malware have no
   free header slot today); MAB-Malware's validity under the new rule. Then `6-results`.
5. **Meanwhile, with the user:** read every current result (the table above with the toolkit's `escape` and `loo`
   parts, the adaptive search's escapes and `expert`, MAB `expert` and `zainab` against Zainab et al.'s 83%, the
   validity counts and the "pefile only" rejections by cause); PV's setup against Gimenez et al.'s (theirs 1,033
   vectors, ours 78,715; PV's rule has no constant but its result depends on the vector count; PV's sample-size
   experiment, `docs/scaleup-protocol.md` item (17), approved and deferred).
6. **When ERDALT's folds are done** (`sacct --name=learned-erdalt -S 2026-11-20`): R19's asks
   (`docs/reviews/2026-11-12-body/meta-review.md`) and ERDALT's attacks (as in
   `logs/submit-20261117-181439-no-erdalt.txt`); its toolkit run waits for item 2 if the rerun is near.
7. **Right-size from sacct** every finished step (`sacct -u $USER -S 2026-11-18 --format=JobID%16,JobName%20,State,
   Elapsed,Timelimit,AllocCPUS,TotalCPU,MaxRSS,ReqMem`), finished steps' headers too.

## 4. Rules that apply (from the user; also in CLAUDE.md and the memory)

- On an interactive node: use only the allocation; worker pools under `if __name__ == "__main__":`, diagnostic Python
  in a file under `artifacts/scaleup/diag/`, never from stdin; diagnostics need `FILE_STORE=artifacts/scaleup/2-
  features/files/files.sqlite` and `PYTHONHASHSEED=0`. Jobs longer than ~10 minutes or larger than the allocation go
  through `sbatch` after asking. Kill by PID, never `pkill -f`.
- **Do not watch the queue.** Check once, report, hand back. Read every new job's log within ~2 minutes of its start.
- Before submitting or changing a step, work out the processes, threads, cores and memory it uses; say plainly what was
  not checked.
- A plan (and the user's approval) before an experiment; a hypothesis before running; report failed checks as such;
  fix failures at their source. The user decides protocol questions; Claude recommends.
- Changes to the thrember-derived `features.py` are pure additions; `tests/reference/` is never edited.
- Commit to `main` in logical pieces (ruff, strict mypy on `src tests pipeline`); do not push.
- At the end: `docs/status.md`, PLAN.md, and this prompt rewritten self-contained.

## 5. Noted for later

- Open with the user: move `docs/erdalt-diagnosis-plan.md` under `docs/evidence/`.
- ERDALT's logits reach +-8,007 on validation (temperature 266.9); worth a sentence if calibrated probabilities are
  ever reported.
- Toolkit task 9 (the debug-entry escape) once used 41% of its 36 cores with every attack 2-3x slower; if it recurs,
  `sstat` it while it runs.
- Per-item loops that may still run serially in a main process: `toolkit.py` and `mab.py` (feature extraction before
  the pool), `6-results` scripts, `expert_adaptive.py`. `mab.py` runs all detectors in one pool.
- `third_party/README.md` lists MAB-Malware's patches but not 50f3e97's.
- `coverage.py` still accepts an unused `--db`; other audit steps may still read the SimpleDB.
- `adaptive.add_section`/`add_imports` (the LIEF writers) look unused by the search now; remove if so.
- `artifacts/scaleup/diag/erdalt/smoke-s93/` and `diag/validity-sets-smoke/` are disposable.
