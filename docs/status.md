# Status

**2026-10-29, third session: run 102 read; the hypothesis holds.** G1 for sums exact on 2,000/2,000 files; the
precondition variant equals the hand rules per threat model on the re-encoded groups; the `*-pre*` training inputs are
byte-identical to run 99's, so no C4 model needs retraining. One per-cell disagreement the pilot lacked (also in run
97's 2,000-file cells, unexplained until now): the header overwrites (dos, hdr, chk, rdb, rsg) move section entropy
both ways, which the hand rules rule out. Cause: 4 of 2,000 files have a .bss section with PointerToRawData 0 and
SizeOfRawData > 0, so its raw data is the header; witnessed on all four by rewriting the DOS stub (entropy_hash_29 up
and down). No threat-model change (these operations are only in M_full, where section entropy is already two-sided).
Recorded in `run/102_step8_sums.sh`.

**Step 6 (G7) built and run on the pilot (`scripts/catalogue_checks.py`, `run/103_catalogue_checks.sh`; user chose the
direction check over exact prediction for all twelve operations).** In-place operations and append hold. Fixed, one
rule each: an absent Rich header is located by its search range (C1 missed a forged one); every lengthening operation
gets the strict past-end flags; a section placed before the overlay moves the certificate table (security_virtual_address
under M_add: fixed -> up, the only training-input change so far). **Open, for the user:** a section placed *after* the
overlay swallows it (pefile's overlay rule): overlay_size/overlay_entropy/max_entropy down and the old overlay bytes
leave the body regions (all body_* down), on all 31 pilot files with an overlay that pass the precondition. Options:
declare it as is (body sums lose their one-sidedness), declare it and count the bytes between and after sections as
body (re-featurize the sums store), or restrict sec/imp to placement before the overlay (narrows the threat model).

**2026-10-29, second session: step 8 built (sums re-encodings as items); pilot checks pass; run 102's 2,000-file
steps are for the user.** Commits ef8aa21..(this wrap-up).
- **What changed:** the four re-encoded groups (`sums.py`) record items: byte runs, full windows, and strings per body
  region (own kinds, located through the section table, SizeOfHeaders, and pefile's overlay rule; `body_layout`), and
  sections with a new `split` term (a value into the positive or negative part of its name's bucket). Their readouts
  are identities, so C4 derives their directions; `a_directions.py --derive` uses the sums extractor as the merged
  variant, and no direction is hand-written any more (the hand rules stay as G3's oracle).
- **Engine fixes found on the way (one rule each):** Max/Min readouts read only their own group's items (the split
  sections share the kind "section"); an in-place write keeps element counts (it no longer moves ratios over the file
  size: 17 over-approximated cells gone, no threat-model change); debug removal moves the overlay only where the debug
  directory decides its start (0 of 2,000 files: survey); the catalogue's slack excludes sections of virtual size 0,
  which the loader maps whole (5 of 2,000 files would otherwise have made every body count two-sided under M_full).
  `attack.region_parts` keeps the old slack convention for virtual size 0 (noted, not changed: results there are
  measured by re-extraction).
- **Pilot (run 102, steps 1-2):** G1 for sums exact on 100/100 files; G3 for sums: the precondition variant equals
  the hand rules on every (feature, operation) cell of the re-encoded groups (M_add/M_shift 1,083 up, 4 both; M_full
  683 up, 404 both); the strict variant differs only under append (sections and directories past the end), as for
  thrember's groups. Thrember's directions per threat model are unchanged from run 97. The training inputs equal run
  99's, so no C4 model needs retraining if the 2,000-file set agrees.
- **For the user:** `run/102_step8_sums.sh` steps 3-4 (G1 with sums and the derivation on the 2,000-file set; ~10-20 min
  together, each estimated at 5-10 min). Read `artifacts/experiments/item_checks/exact-sums-2000/report.json` and
  `artifacts/experiments/a_directions_derived_sums_2000/g3.json` ("sums"), and compare its `*-pre*` files with
  `a_directions_derived_sums/`.
- **Next:** read run 102; then step 6 (catalogue checks, G7), step 9, the expert-set row, the A' pilot.

**2026-10-29: runs 99-100 read (both hypotheses hold); every remaining witness built (run 101); next: step 8.**
Commits 2155aa8..(this wrap-up).
- **Run 99 (retraining from the derived directions):** test metrics within noise of runs 77/80 under M_add; under
  M_full slightly better (+1.2-1.4 points TPR at 1% FPR; security_size kept, constrained down).
- **Run 100 (Table A1 with routed C4 rows):** 38/50 pilot malware pass the precondition check. On those, every routed
  row is evaded by no seen attack, and the M_full rows by no held-out attack (0/28, 0/30); M_add's held-out evasions
  are header_fields, outside M_add. On the 12 failing files every routed row is evaded once (one file, header_fields,
  unconstrained branch), fewer than the unconstrained model alone (4/12; its other three are GAMMA API runs, likely
  because queries that pass the check are scored by the C4 model; not checked). Adaptive search: C4 rows 0/45,
  unconstrained 10/49, PV 22/22; the unconstrained model is 0/12 on the failing files, so a routed row would also be
  0/45 unless a query switches branch (not checked). Run 100 took 2.4 h (estimate 1-1.5 h).
- **Run 101 (`scripts/a_structure_witness.py`):** entry section 8/8 pilot files (an added executable section becomes
  the entry section); Rich header via the stub extension 39/39, via TimeDateStamp/PointerToSymbolTable 8/39 (pefile
  accepts any "Rich" marker and reads pairs from 0x90); relocations past the end 2 pilot / 151 of 2,000 (has_relocs
  0 -> 1); exports past the end 0 pilot / 37 of 2,000 (num_exports 0 -> 128 is the known constant-128 quirk,
  upstream-issues item 3). All covered by the derived directions: the entry and Rich cases are the precondition
  variant's differences from the hand rules; the past-the-end cases fail the precondition check.
- The witness script runs on a worker pool (16 by default, one read and parse per file, tqdm progress every 30 s): the
  2,000-file step took ~4.5 min instead of an estimated 60-80 min serially (the user asked for it).
- Recorded in `docs/direction-A-A1-design.md` ("Re-run with derived directions"), `docs/item-layer-design.md` (Build
  status, 2026-10-29), `docs/direction-A-summary.md` (update note), and the comments of runs 99-101.
- **Next (user, 2026-10-29): step 8** (sums re-encodings in the engine), then step 6 (catalogue checks), step 9, the
  expert-set row, the A' pilot. `PLAN.md`, "Next steps (2026-10-29)".

**2026-10-28: locating ranges split per structure (runs 95-96); step 7's C4 engine built (run 97); signature
witness (run 98); the user decided the precondition row and started runs 99-100 (retraining, Table A1 re-run with
routed C4 rows) at the end of the session; read them next.** Commits 8b34250..(this wrap-up).
- Split `pe_locating` into header / section / per-directory levels; G5 now also flips directory data. Round 1 found
  signify reading SizeOfOptionalHeader and the import parse reading names and both thunk arrays through their
  terminators (one rule: everything the import parse reads locates every import). G5 passes on pilot + fresh files
  (58,666 flips); G1/G2 exact, G4 identical to run 92, G6 1,791/1,791 exact (flagged 440 -> 209).
- C4 engine (`reach.py`) + catalogue changes (`catalogue.py`: in-place ops derived from per-file regions restricted to
  loader-ignored bytes, structural ops declared provisionally, `precondition`) + `a_directions.py --derive`.
- **Precondition variant = hand rules per threat model**, on the pilot and the 2,000-file set alike, except
  entry_name_hash (sec, anticipated), Rich (ext, anticipated), and security_size (hand over-approximates). Also
  found: three hdr fields lie in pefile's Rich search range (no threat-model change: dos already moves Rich).
- **Strict variant is degenerate:** M_add keeps 44 features, M_full 9 (6 constant), so the planned fallback of
  always-safe features is effectively empty. Pilot: 12/100 fail the precondition, all malware, 8 at the 4 MB cap.
  2,000 files: 318 fail (73 benign, 245 malware; 231 truncated).
- **Signature witness (run 98):** both pilot files with a table past the end: num_certs 0 -> 1, chain_max_depth 0 -> 4,
  signing_time_diff both ways (appends of 4.9 MB and 421 MB).
- **Decided (user, 2026-10-28):** files that fail the precondition go to the unconstrained detector (no guarantee for
  them; report coverage); the >4 MB files stay; the strict detector is one sentence, not a row of Table A1.
- **Built for the user:** routed detectors in `a1_evaluate.py` (`--route name=fallback`: the check on every attack
  query, each branch at its own 1% FPR threshold, results split by whether the original file passes);
  `a_directions.py --derive --extractor sums` (the derived directions in the 10% store's layout; re-encoded groups
  keep their hand rules until step 8). The derived files differ from runs 77/80's only in entry_name_hash (dropped
  under M_add) and security_size (down under M_full). **Running (started by the user, 2026-10-28):** `run/99_a1_train_derived.sh`
  (~20 min: six models) then `run/100_a1_toolkit_derived.sh` (~1-1.5 h; smoke-tested on 3 files). Read their logs
  and outputs next; record the results in the run scripts' comments.
- Noted, not acted on: the experiments' slack and DOS edits (`attack.region_parts`, `a1_adaptive.py`) do not exclude
  loader-read bytes (7 of 2,000 files have slack overlapping headers or relocations; 2 keep import names in the DOS
  stub); their results are measured by re-extraction, so nothing rests on it.
- Next: `PLAN.md`, "Next steps (2026-10-28)".

**2026-10-27, fourth session: step 7 not started; a wider hole in the hand direction rules found and witnessed, and
pefile's directory crashes fixed by one rule (run 94).** Commits 474e176..(this wrap-up).
- **Appending can complete structures that lie past the end of the file.** pefile reads directory data, sections, and
  the signature table through header pointers; where these point past EOF, the parse skips them, and appended bytes
  later become them. 12 of 100 pilot files have such a structure (imports 9, resources 6, debug 3, security 2, ...;
  mostly files cut at the dataset's 4 MB cap). **Witness (signature):** pilot malware `4294f2f053c2...` (4,000,000
  bytes, truncated) has its security entry at file offset 8,841,232 (size 11,216); appending zeros up to that offset
  plus a 10,160-byte certificate table copied from a signed pilot file gives `num_certs` 0 -> 1, `chain_max_depth`
  0 -> 2, and new signing times on re-extraction (signify parses, never verifies). The hand rules constrain
  authenticode to fall only (rsg); its features carry 13-16% of the gain of the M_full C4 models (4-5% M_add).
  Exports, relocation flags, the entry-section name hash (via sections pefile dropped), and `overlay_size` are
  exposed by the same mechanism; no witness for those yet. The witness was a scratch script; rebuild it in step 7's
  report next to `scripts/a_overlay_witness.py`.
- **Decided (user):** strict directions plus a precondition row: the detector checks at inference that no locating
  range lies past the end of the file; files that fail go to a fallback detector of always-safe features, reported
  next to the strict row. The user warned this approaches distracting complexity: keep the experiments' global
  complexity down; excluding files over 4 MB is an option to weigh later, not decided.
- **pefile directory crashes fixed by one rule** (user: patch, but no rabbit hole). pefile's directory parsers raise
  AttributeErrors on structures they could not read (a type-20 debug payload outside the file; a dynamic relocation
  table header outside the file; two rarer paths), and thrember then treats the file as not a PE (all PE features
  zero). Appending can trigger the first two. Rule: a directory parser that raises anything but PEFormatError loses
  only its own directory, with a warning (`features.py`, last section; installed in pefile at import). 394 of the
  2,879,653 stored files were such crashes (371 benign, mostly truncated); **run 94** rewrote them in both stores
  (full: 394; sums: 47; old values in `{store}/patches/`); none is a pilot file. `docs/upstream-issues.md` item 5.
- **Consequence for step 7:** with the rule, a crash no longer spreads from one directory to every item, so the
  parse-wide locating ranges (`pe_locating`: every item is located through all ten directories' data) can shrink to
  per-structure ones. Without that split, the strict C4 table would call header fields two-sided under append.
- Pending from before: the C4 retraining must run on the patched stores (they are now).

**2026-10-27, third session: derivation steps 1-5 built and checked; step 6 (the edit catalogue) not started.**
Commits 94c8d37..4d9d1ee. All checks passed, each after at most one fix round, with fresh-file confirmation:
- Step 1: `src/provexp/items.py` (items, terms, readouts as data, projection), `tests/test_items.py`.
- Steps 2-3: `items`/`readouts` for every group in `features.py` (pure additions). **G1** bit-exact on 100 pilot +
  2,000 files (both import variants); **G2** projection equals provenance on 100 (run 90).
- Step 4: locating ranges. **G5** (header byte flips): first round found three pefile rules (section-table chain, a
  debug-directory crash that makes the extractor treat the file as non-PE -- `docs/upstream-issues.md` item 5,
  SizeOfImage bounds relocations); after the fix 0 failures on 20 pilot + 20 fresh files (run 91).
- Step 5: `src/provexp/reach.py` (C1 engine), recognizers per group, `catalogue.py` (add_section only). **G4**:
  Table A0 reproduced, bit-equal to the hand predictors on all 289 predicted pairs, the 11 overrun files flagged by
  the engine itself (run 92). **G6** (random in-place writes): 1,560/1,560 and 1,463/1,463 bit-exact after adding the
  dynamic relocation table to locating (run 93).
- Not done: step 6 (catalogue for the other operations, parameter domains, G7). The session's response was stopped
  by the safety classifier while reading the toolkit's transformation code for the A0 rows; nothing was written for
  step 6. Next (recommended to the user): step 7 (the C4 engine and the disagreement report), then step 6 built
  from our own edit functions. Pick up at `docs/resume-prompt.md`.

**2026-10-27, second session (end): A' mock written, reviewed, and accepted; A' check 0 passed; the overlay gap
settled.** Next: derivation steps 1-6 of `docs/item-layer-design.md` in one stretch (item table, readouts as data,
exactness checks G1/G2, locating ranges, C1 engine, edit catalogue), then step 7, the expert-set row, and the A'
pilot. Details: `PLAN.md`, "Next steps (end of 2026-10-27, second session)". Pick up at `docs/resume-prompt.md`.

**2026-10-27 (first session, end): A' chosen and its literature read; the derivation designed; a soundness gap in
Table A1 confirmed.**

Session log (2026-10-27, second session):
- **A' mock written** (`docs/direction-A-prime-mock.md`; first draft by another session, then revised). Fixes: the
  C4 row's "certificate" was circular (now a sanity check); battery cells now use Table A1's measured numbers; the
  solver searches over edit choices, so every evasion is a concrete edit; Chen et al. (USENIX Sec 2020) added as the
  closest precedent; solver tractability is check 0; the baseline is constraints learned from the toolkit (predicted
  to give wrong certificates on PV), not Simonetto's constraints translated by hand; the expert-set detector is a row.
  Order: derivation steps 1-3, then 5 (C1 engine), then 7. Six open decisions at its end, for the user.
- **Overlay gap: `body_*` sums not affected** (100 pilot files, 190 appends: no body count drops; `overlay_size`
  drops on 8). 7 of 11 overrun files are cut at the 4 MB dataset cap. Decided (user): pefile's rule is real behavior;
  only `overlay_size` becomes two-sided (with the next C4 retraining). Witness: `scripts/a_overlay_witness.py`, run 88.
- **A' mock decisions accepted** (all six recommendations): lead with Table A'1; solver over edit choices; check 0
  (solver tractability, no provenance needed) first.
- **A' check 0: go** (run 89, `scripts/ap_check0_solver.py`; mock, check 0). Exact encoding; every solve decided in
  <= 34 s on the 500-tree model. Directions alone certify nothing on non-monotone detectors (all evadable in feature
  space), so A'1's region needs C3's magnitude bounds, which the edit-choice formulation gives; an L0 stand-in (K=1, 3)
  yields real proofs in 13-34 s. Next: derivation steps 1-6.
- **Design doc open decisions settled** (user accepted the recommendations): keep `provenance` until G2 passes, then
  make it a projection of `items`; overlay: strict, no precondition row, no pefile patch; re-run A1's C4 rows when
  the directions change (toolkit part is a 47-min `run/` script for the user); G1 also on the 2,000-file set; the
  sound syntactic regex test.
- **Order (agreed with the user):** A' check 0 (solver tractability), then derivation steps 1-6 in one stretch
  (4, locating ranges, feeds the C1 engine; 6, the edit catalogue, gives the solver its edit choices), then step 7,
  then the expert-set row, then the A' pilot.

Session log (2026-10-27, first session):
- **Second application: A'** (user agreed). Literature: `docs/literature-Aprime-2026-10-27.md`; nine foundational
  papers plus six for A' saved to `papers/` (untracked). Novelty is only the computed side effects/constraints;
  hash-bucket targeting is Rosenberg et al.'s.
- **Found: direction A's C4 directions and C1 predictors are hand-written**, not derived from the instrumentation.
  Design for the automatic version: `docs/item-layer-design.md` (written by another session from a task prompt,
  after the safety classifier stopped two attempts here; reviewed). User: pursue it; the doc's 14-19-day estimate is
  far too high.
- **Confirmed:** pefile skips extents past EOF when locating the overlay, so appending can lower
  `section:overlay_size` (4 of 5 testable pilot files with a section past EOF; witness script was in the session
  scratchpad, not committed; rebuild it in step 7's report). The M_full C4 rows constrain it up-only (0.9% / 0.25% of
  gain), so "never moved by any attack" does not hold on such files. The `body_*` sums (10.7% of the sums row's
  gain) still need a witness. Fix pending a user decision.
- **Expert set:** `docs/direction-A-expert-set.md`. Their 40 features come from their own LIEF extractor; user:
  re-implement; M_full is the priority, their add-only model for context.
- **Safety classifier:** stopped four responses this session (literature notes, the derivation design, the A' mock
  twice counting the last); the literature notes went through on a second attempt. The user had another session
  write the design doc from a task prompt.

---

**2026-10-26 (end of session): direction A complete at pilot scale; Tables A1 and A2 done.** Every go/no-go check and
falsifiable outcome passed (`docs/direction-A-summary.md`). Table A1 (`docs/direction-A-A1-design.md`, "Result"): the
four C4 rows are never moved by any attack (seen, held-out, adaptive; largest score change exactly 0.0), the M_full
rows keep 86.7-88.6% TPR at 1% FPR and still detect 40-41 of 50 pilot malware after every attack; PV (4 or all 8
attacks) holds against the toolkit but the C1-guided adaptive search evades it on 21-22 of 22, and it costs ~35 TPR
points. Table A2: the search needs 3-4.5 extractions per file vs ~100 per toolkit attack; provenance-chosen section
names double its success on PV-seen (random-name ablation, run 87). **Next (agreed with the user):** screen
the second application on paper, three candidates side by side -- A' (realizing feature-space attacks in the problem
space; `PLAN.md`, Directions), B, C -- and, in parallel, A's expert-set row (needs Gimenez et al.'s paper, arXiv
2508.10038) and cost column. Later, with the scale-up: adversarial-training row, second toolkit, leave-one-out PV,
scale. The framework/theory section waits for the applications. Pick up at `docs/resume-prompt.md`.
**User rules from this session:** run only jobs of ~10 min or less myself; never hard-code
worker caps in Python (16 is the run/ default only).

Session log (2026-10-26), newest first:

**Direction A summary (2026-10-26):** `docs/direction-A-summary.md` -- every check and falsifiable outcome passed at
pilot scale; missing: expert-set row, adversarial-training row, second toolkit, leave-one-out, scale, cost column.
Recommended next: the expert-set row (needs Gimenez et al.'s 40-feature list) and the cost column.

**Run 87 + Table A2 (2026-10-26):** Table A2 assembled (`docs/direction-A-A1-design.md`, "Result: Table A2"). The
random-name ablation (run 87) held the hypothesis only partly: provenance-chosen names take PV-seen evasion from 11/22 to
21/22 and PV-all from 15/22 to 22/22, but random names already evade PV often (its hole is broad), and on the
unconstrained model targeting adds nothing (15 vs 14/47; GAMMA API, which adds imports, beats both there at 24/47). The
toolkit attacks evade PV-all on 0/22 with ~100 extractions each; the C1-guided search needs a median of 3. User rule
(2026-10-26): only run jobs of ~10 min or less myself.

**Run 86 (2026-10-26, read): Table A1 complete at pilot scale** (`docs/direction-A-A1-design.md`, "Result").
Toolkit re-run with the fixed harness matched every prediction: seen 0% on every constrained row; held-out 18% PV-seen,
0% PV-all and both M_full C4 rows. With the adaptive column: pilot malware still detected after every attack, of 50:
C4 M_full sums 41, features 40; unconstrained 20; PV-seen 1; PV-all 0. Next: Table A2 (the adaptive attack's own table,
mostly in run 84/85's output).

**Run 85 (2026-10-26, read): PV built from all eight toolkit attacks (s10 PV-all; AUC 0.944, TPR@1%FPR 53.8%) is
evaded by the targeted adaptive search on 22/22 detected pilot malware (20/22 on re-extraction; median 4.6 KB, 24
queries).** Observing more attacks does not close PV's hole. Run 86 then re-ran the toolkit columns.

**Run 84 (2026-10-26, read): the adaptive column now separates decisively.** Step 1 of the plan (which edits reach
PV-seen's hole, weighted by its gain; hole = 44% of PV-seen's split gain) showed 72% of the hole is reachable by
add-section, already in the search; the Rich header (DOS stub) holds most of the rest (27%). The search was weak for
two reasons, now fixed in `scripts/a1_adaptive.py`: it materialized a freshly drawn random edit instead of the chosen
one (steps did not compose), and section names were random rather than chosen through the inverted section hash
(bucket, sign) at the defense's highest-gain buckets. Also: predicted props now match the materialized section, the
toolkit byte budget applies, and the real re-extracted score is reported beside the declared one. Result (declared /
real re-extraction): **PV-seen evaded 21/22 / 19/22**, unconstrained 14/47 / 9/47, **all four C4 rows 0/0 with
min_delta_logit exactly 0.0**. The Rich-header predictor is no longer needed for the separation.

**Runs 81-83 read (morning; superseded by runs 84-86):** After correcting a secml-malware bug (the shift
attacks insert at `sections[0].offset`, which is 0 on 2 pilot files, so they overwrite the MZ header; the harness now
counts non-PE outputs as invalid; `docs/upstream-issues.md` item 4), every prediction held except one. Seen evasion 0%
on every constrained row (17% unconstrained); held-out 18% PV-seen, **0% M_full C4 (features and sums)**, 35-40% M_add
(header_fields, outside M_add, as expected); adaptive **0 on every C4 row with min_delta_logit exactly 0.0** (run 83
added the s10 features-as-is rows). **Failed:** adaptive evasion of PV-seen is 0/22 (min -1.19 logits), and the search
is weak overall (2/47 on the unconstrained reference); it reaches only append + add-section, while PV's hole is mostly
Rich header + header fields. On the full-data models the same search evades full PV 4/22. **New, unplanned:** PV-seen
has TPR@1%FPR 56.2% vs 86.7-88.6% for the M_full C4 rows; files still detected after all toolkit attacks: 82% (C4
M_full sums) vs 36% (PV-seen) vs 42% (unconstrained). **User decisions (2026-10-26):** strengthen the adaptive search
first (C1 predictors for header-field and DOS-stub/Rich-header edits, then re-run the adaptive column); keep the
adaptive column as designed; no scaling for now (nowhere near seeds 0-2 / 2,000 files). **Next:** those predictors.



---

**2026-10-24 (end of session): Table A1 machinery built; runs 81/82 running.** All of Table A1's build order
(`docs/direction-A-A1-design.md`) is implemented and committed; the user is running `run/82` (`run/81` was running at
hand-off). The decisive result already showed in smoke tests: the **same** adaptive search drives the unconstrained
detector down ~1.4-2.8 logits yet moves the C4 detectors by exactly 0.0, in both the thrember and sums feature spaces
— the soundness guarantee, measured. **Pick up at `docs/resume-prompt.md`:** read
`artifacts/experiments/a1/{toolkit,adaptive,adaptive_sums}/*.json`, confirm the separation (seen ~0 everywhere;
held-out > 0 for PV-seen, 0 for M_full C4; adaptive 0 for every C4 row — a nonzero on a sound row is an A1-A4 bug,
debug via A0 — and > 0 for the unconstrained/PV-seen), then assemble Table A1. Scoped remainder: C1 predictors for the
DOS-stub/header-field/checksum/rename/remove operations (A0-sized; append + add-section already reach the
histogram/string/section-bucket parts of PV's hole, not yet the Rich-header/header-field parts). Session details
below.

---

**2026-10-24 (A1 decisions).** User decided (recorded at the end of `docs/direction-A-A1-design.md`): sums
re-encoding on a 10% subsample of all splits first (~1 h); the proposed seen/held-out split as a **quick check only**,
with **leave-one-out** (8 PV models) for the formal experiment later; baselines later; 50 pilot malware; budgets at
the doc's defaults (max(5%, 512 KB) bytes, 100 queries) unless overridden.
**Build step 1 ready:** `src/provexp/featuresets/ember2024/sums.py` (`SumsFeatureExtractor`: thrember with merged
imports + body_histogram, body_byteentropy, body_strings, section_split; 3,655 features; tests
`tests/test_ember2024_sums.py`, incl. append-never-lowers), `scripts/featurize.py --extractor sums --every 10`,
`scripts/a_directions.py --extractor sums` (outputs in `artifacts/experiments/a_directions_sums/`; the -control lists
reproduce run 77's quirk-fixed counts). **Waiting on the user:** run `run/80_a1_sums.sh` (~1-1.5 h featurization +
5 GBDTs). Side finding: 4.2% of a test shard's files repeat a DLL descriptor (the quirk affects them). Meanwhile: build
steps 2-4 (PV-seen, harness, adaptive attack).
**Steps 2-3 ready (2026-10-24):** `a_pv_hole.py --attacks ... --tag=-seen` (all-8 reproduces run 78 exactly; PV-seen
keeps 1,773 features, M_full hole 246 features); `scripts/a1_evaluate.py` (harness: 1% FPR thresholds from each
model's test predictions, detected-only, byte cap, re-extracted scores, seen/held-out/all groups split by truncation;
smoke-tested on 2 files); `run/81_a1_toolkit.sh` (PV-seen GBDT on the s10 store + 8 attacks x 6 defenses, ~1-2 h),
to run after run 80. Pilot note: at 1% FPR the full-split PV model detects few pilot malware (tau 0.81).
**Step 4 (adaptive attack) built for thrember-space defenses (2026-10-24):** `scripts/a1_adaptive.py`. Decision
(recorded in memory + design doc): the adaptive column scores by **C1-declared effect** (the attacker's reachable set
under M), not real LIEF re-extraction, so the C4 rows are 0 by construction and LIEF relayout (A4) is a separate
number. Edit primitives verified (in-place edits stay in M; LIEF structural edits relayout `.rsrc`, so they feed only
the A4-gap report). Greedy search over append + add-section (the two operations whose C1 predictors from
`a_c1_table0.py` are complete). **Smoke result: the same search drives the unconstrained detector down 2.77 logits
but moves the M_full C4 detector by exactly 0.0000** -- the soundness probe works. Wired into `run/81` step 4.
**Sums-space C1 predictors done (2026-10-24):** `predict_append_sums` / `predict_add_section_sums` in
`a_c1_table0.py` (refactored `predict_append`/`predict_add_section` to expose their raw dict; A0 regression holds).
Validated vs re-extraction on 36 clean pilot files: append matches all four body groups 34/36 exactly; add-section's
body histogram/strings match (section_split is A4 layout, as expected). **Up-only confirmed:** neither predictor
lowers any of the 1,979 M_full-sums kept features on any file, so the C4-sums rows are sound by construction. The
adaptive driver is now store-aware (`run/82` runs the sums adaptive column; smoke: ref driven -1.40 logits,
mfull-sums exactly 0.0). Run 81's operating-point worry is resolved: the s10 defenses detect 40-43/50 pilot malware
at 1% FPR.
**Still open (scoped, A0-sized, lower priority):** C1 predictors for the DOS-stub (Rich header), header-field,
checksum, rename, and remove operations (`predict_content_overwrite` models DOS members only). append + add-section
already reach the histogram/string/section-bucket parts of PV's hole; these would add the Rich-header and
header-field parts. The toolkit columns (run 81) exercise those attacks empirically meanwhile.

**2026-10-23 (A1 design drafted).** `docs/direction-A-A1-design.md`: the full plan for Table A1 (defenses as rows,
seen/held-out/adaptive attacks as columns), the one evasion protocol (1% FPR operating point, re-extraction ground
truth, shared budgets, pilot scale), the C1-guided adaptive attack (the decisive column; 0 by construction for the
C4 rows, an A1-A4 bug if not), the build order, falsifiable outcomes, and five open decisions for the user. Key
prerequisite: the re-encoding ("sums") feature extraction for the decisive C4-on-sums row is a multi-hour
featurization pass to scope with the user first; the features-as-is rows (run 77 models) and the adaptive attack can
proceed now. **Waiting on the user:** the five decisions in the design doc (re-encoding scale, seen/held-out split,
baselines now/later, malware set size, budgets).

**2026-10-23 (A0 complete): all three A0 rows done; C1 side-effect engine validated.** Added the declared-structural
row (add_section via LIEF) to `scripts/a_c1_table0.py`. Full pilot, three transformations:
- **append** (item-creating): 89/89 A2-applicable exact; 11 flagged A2 (section overrun).
- **dos_overwrite** (content): 100/100 exact.
- **add_section** (declared structural): C1 predicts the declared delta exactly -- COFF NumberOfSections +1 on all
  100, section counts on 93-100 -- while SizeOfImage (99/100) and the quantitative byte/size features are LIEF's
  layout (A4), as the model says; untouched groups (exports/richheader/imports) predicted ~100/100.
So C1 is exact on the two non-structural classes (56% of the coverage table) where A1-A4 hold, and on the
declared-structural class predicts the semantic delta while correctly localizing the rest to tool layout (A4).
Reading: `docs/direction-A-threat-model.md` S6. **Go/no-go checks 1, 2, 3 all pass; A0 is complete.** Next: A1 proper
(the monotone defenses from run 77 vs PV selection, on seen/held-out/adaptive attacks; the adaptive column uses C1).

**2026-10-23 (A0 extended): Table A0 now covers both non-structural classes, both exact.** Added a content-edit row
to `scripts/a_c1_table0.py` (now a two-transformation registry) and re-ran `run/79`. On the 100 pilot files:
**append** (item-creating) 89/89 A2-applicable exact (11 flagged A2 section-overrun); **dos_overwrite** (content,
in-place DOS-header fields [2,60)) **100/100 exact**. The content row exposed that EMBER's `header` group reads the
DOS-header fields (dos_e_cblp..e_oeminfo); the predictor recomputes them from the edited bytes. C1 is now validated
exact for content + item-creating (56% of the coverage table) wherever A1-A4 hold. Reading:
`docs/direction-A-threat-model.md` S6. **Remaining A0 rows:** declared-structural (add section/imports via the attack
toolkit; expect LIEF A4 side effects). Then A1 proper.

**2026-10-23 (later still): go/no-go 1 (Table A0) is a GO.** First C1 predictor + validation
(`scripts/a_c1_table0.py`, `run/79_a_check1.sh`): on the 100 pilot files, apply overlay append (guard byte + 4 KB
random), predict phi(z') from z alone (no re-extraction), compare to re-extraction feature by feature. **89/89
A2-applicable files predicted exactly** (all 2,480 modeled features, incl. every renormalized histogram/byteentropy
bin, string dist/entropy, section size-ratios + overlay + max/min); the 11 exceptions each have a section whose
declared raw size overruns the truncated file (an A2 locality failure the model flags), all 13 mismatches in the
`section` group. pefilewarnings (no items, outside the model) excluded. Reading in
`docs/direction-A-threat-model.md` S6. This validates C1's side-effect engine for the item-creating class.
**Next A0 rows:** a content edit (in-place DOS/header overwrite) and declared-structural (add section/imports via the
attack toolkit; expect LIEF A4 side effects). Then A1 proper (seen/held-out/adaptive), whose adaptive column check 2
set up. All three go/no-go checks (1, 2, 3) now pass.

**2026-10-23 (later): check 2 is a GO; attack toolkits vendored and patched.** secml + secml-malware now run in
`env/` (Python 3.14, NumPy 2, LIEF 1.0); vendored under `third_party/` (pristine commit `3cbef4f`, patches `dce1f60`).
No separate venv was needed; no fix was due to Python 3.14 itself. All eight of Gimenez et al.'s black-box attacks
run against our GBDT. **Check 2 (run 78):** of the 1,736 features PV selection keeps (its reproduction matches
Gimenez: AUC 0.945 vs their 0.938), C4 proves 213 decreasable under M_full; they carry **37.8% of the PV GBDT's
split gain** (threshold 5%) — signed section buckets (22%) and string regexes (13%), exactly the hypothesised holes;
85 were never touched by any attack. Decisive GO. Bonus: the C4-sound GBDT (run 77, AUC 0.993) beats PV (0.945) on
accuracy too. Code: `scripts/a_pv_attacks.py`, `scripts/a_pv_hole.py`, `run/78_a_check2.sh`; results
`artifacts/experiments/a_pv/` (deltas, hole.csv, report.json); reading in `docs/direction-A-threat-model.md` S5.
**Next:** go/no-go 1 (C1 item table + Table A0), then A1 proper (the adaptive column this check sets up).

**2026-10-23: run 77 read (check 3, as-is rows): passes, better than predicted.** Sound-as-is monotone GBDTs on the
full splits: test AUC 0.9957 / TPR@1%FPR 92.1% under M_add, 0.9930 / 87.4% under M_full, against 0.9976 / 95.6%
unconstrained (predicted ~0.97-0.98 and ~0.96). The quirk-fixed import features add nothing to accuracy. So the
re-encodings have little to recover under M_add (3.5 TPR points) and more under M_full (8.2); A1's weight shifts to
soundness (check 2) and M_full; lead with TPR at low FPR (AUC saturated). Details:
`docs/direction-A-threat-model.md`, Section 4.
- **No separate venv needed (user asked; verified).** secml + secml-malware run in `env/` (Python 3.14, NumPy 2.5,
  LIEF 1.0) after ~20 one-line patches (NumPy 2: copy semantics, removed aliases, one NEP 50 overflow; LIEF 1.0:
  builder API, parse(bytearray), add_import; one upstream None-default bug; eager imports of the old `ember` package).
  None were caused by Python 3.14. All 8 of Gimenez et al.'s attacks (from their repo) smoke-tested against our GBDT,
  re-extracted from disk. maltorch (user's fork) also runs with 2 LIEF patches but lacks 4 of the 8 (header fields,
  GAMMA API, GAMMA shift, format exploit) and uses nevergrad instead of the GA. Patches and smoke scripts:
  `artifacts/experiments/attack_env/`. **Waiting on the user:** OK to vendor patched secml/secml-malware under
  `third_party/` and add their dependencies (deap, moocore, python-magic, torchvision, Pillow, matplotlib) to `env/`.

**2026-10-22, end of day: summary and hand-off.** Today the project restarted as feature provenance for malware
classification and direction A took shape:
- **Model:** coverage of 34 real transformations on paper (94% exact or bounded once C1 admits declared structural
  edits and a "move" operation, both adopted); proof sketches for C1-C4 with assumptions A1-A4; C2 and C4 restated
  (adopted).
- **Direction A:** the mock (`docs/direction-A-mock.md`; A1 approved as the target result); Treant and Chen et al.
  CCS 2021 read (consumers of a hand-written specification); threat models and the provisional direction table
  (run 76: 22% usable as is, 96% re-encoded, under M_add).
- **Quirk policy (user):** no result rests on extractor quirks. The duplicate-DLL import overwrite is verified and
  patched (`ImportsInfoMerged`, `merge_import_descriptors`, tests in `TestImportsInfoMerged`); every A1 row will use the
  patched extractor. **For the user: file the upstream issue + PR** (`docs/upstream-issues.md`, drafted).
- **Running:** run/77 (check 3, as-is rows; the user launched it in tmux). Read it next session.
- **Waiting on the user:** OK for a separate Python 3.10 venv with a pinned secml-malware clone (it and secml need
  Python < 3.11); the scale of the re-encoding extraction (to be estimated first).
- LIEF 1.0 added to `requirements.txt`; `scripts/train_classic.py --monotone` added; lint and mypy clean.

**2026-10-22 (end, later): steps 1-2 of A done: threat model and provisional direction table (run 76).**
- `docs/direction-A-threat-model.md`: three nested threat models (M_add: append, add section, add imports; M_shift:
  + DOS extension, content shift; M_full: + slack, DOS header, header fields, checksum, rename, remove debug and
  signature). Outside all: code randomization, UPX.
- `scripts/a_directions.py` / `run/76_a_directions.sh` (hand-written per-group rules, a stand-in for C4): of 2,568
  features, a sound monotone detector can use 22% as they are under M_add (19% under M_full), **96% (85%) once
  re-encoded as layer-2 sums** (region-restricted counts, split signed buckets, the import quirk fixed). Hypothesis
  held: the readout, not the items, makes features two-sided.
- Found: EMBER's imports overwrite a DLL's functions when a second descriptor names the same DLL; this alone makes
  1,025 import features two-sided and is a prime suspect for check 2's hole (no secml attack produces it). To verify
  on a real file. Also: min_entropy, min_size_ratio, min_vsize_ratio are constant 0.
- The quirk is verified (116 -> 3 imports on a test file). The user does not want results to depend on such quirks:
  check 2 and A1 use the quirk-fixed variant; the sound table records it. LIEF 1.0 installed (`requirements.txt`).
- **run/77 ready (the user runs it, ~35 min):** check 3's as-is rows, five monotone/dropped GBDTs on the full splits
  (`scripts/train_classic.py --monotone`, new). Smoke-tested (20k and 200k samples; constraints verified in the model).
- secml-malware and secml need Python < 3.11 (our venv: 3.14, numpy 2.5): proposed a pinned clone in a separate
  Python 3.10 venv for the attacks; awaiting the user's decision.

**2026-10-22 (end): A1 approved as the target; Treant and Chen et al. CCS 2021 read; next steps set.**
- The user likes A1 (monotone detectors with C4 directions vs. PV selection); any no-go goes to the user first.
- Treant (hand-written per-feature rewriting rules; non-malware data) and Chen et al. CCS 2021 (hand-specified global
  properties for 7-25 features, from domain knowledge and a measurement study) consume a threat-model specification;
  neither derives one. No novelty threat; they sharpen the pitch (the specification is the bottleneck). Notes in the
  literature doc (fourth pass) and the mock.
- **Next (`PLAN.md`, revised next steps):** (1) fix the threat model M on paper; (2) provisional C4 directions for
  every EMBER feature + the sums re-encoding; (3) go/no-go 3 partial (monotone LightGBM training: user runs it);
  (4) go/no-go 2 (secml-malware attacks; new dependencies: ask); (5) item table + C1 predictor, go/no-go 1.

**2026-10-22 (later): coverage of real transformations on paper (step 1) done; refinements adopted.**
- `docs/feature-provenance-model.md` Section 6: secml-malware (from its source), Labaca-Castro et al.'s t0-t9, and
  MAB-Malware's 13 actions: 34 listed, 16 distinct. Strict classes: content 41%, item-creating 15%, structural 44%
  (declared 38%: remove debug/signature, add section/imports, DOS extend, content shift; undeclared 6%: UPX pack/unpack).
- Not "most structural", but close. **The user adopted two refinements:** C1 covers structural edits whose item
  delta the transformation declares, and "move" is a fourth item operation (DOS extend, content shift). With them,
  32/34 are exact or bounded. Model doc Sections 3-4 and `PLAN.md` updated.
- Caveats recorded: UPX is the strongest attack in Labaca-Castro et al. (uncovered); LIEF-rebuilding tools add
  undeclared side effects; the content rows are hand-mappable header fields, so A's value is in readout effects and
  hashing.
- **Proof sketches written** (model doc, Section 4a): C1 holds under four per-item-kind assumptions (A1 complete
  location, A2 local contributions, A3 local recognition with a margin, A4 faithful declarations), each testable by
  re-extraction; this is the prototype's first go/no-go check. C3: sound cone/box/polytope regions, with care at chunk
  boundaries (merged strings). **Waiting on the user:** C2 and C4 as stated are wrong in part (C2 conflates
  co-movement with inseparability; C4's sign test fails for ratios and entropies, whose direction depends on the
  file); proposed restatements are in 4a. Found on the way: a repeated DLL name in a second import descriptor erases
  the first's functions in EMBER's import features.
- C2/C4 restatements **adopted** by the user (Section 4 updated).
- **Step 3 done: `docs/direction-A-mock.md`** (invented numbers). Lead result: monotone detectors whose feature
  directions come from C4 are sound against attacks nobody ran, unlike Gimenez et al.'s PV selection (whose
  Proposition 3 assumes the perturbation set is known); reading layer-2 sums (raw counts, signed buckets split) instead
  of normalized features should recover accuracy (the re-encoding ERDALT learns). Go/no-go: (1) C1 matches
  re-extraction on >= 95% of pairs; (2) PV selection keeps features M can lower that carry >= 5% of the GBDT's gain;
  (3) the sums-based monotone GBDT within ~2 AUC of PV.
- **Waiting on the user:** review the mock. To read first: Treant (Calzavara et al.), Chen et al. CCS 2021 (verified
  global robustness properties).

**2026-10-22: the project restarts as "feature provenance in malware classification". Conceptual phase; no code.**
- **Why:** the user judged the explanation-provenance paper far below CCS (not novel; no compelling security utility)
  and agreed with the diagnosis (method first, applications after the fact; flat P is precise only where it is not
  needed). Old plan archived (`docs/archive/PLAN-explanation-provenance-2026-10-21.md`); graveyard entry added. The
  simulated review is in `REVIEW-2026-10-21.md` (untracked, left for the user).
- **New thesis and plan:** `PLAN.md`. Directions A (threat models to feature space; the core), B (auditing raw-byte
  detectors for backdoors/shortcuts), C (evasion diagnosis across heterogeneous ensemble members).
- **Literature read** (`docs/literature-2026-10-22.md`): Pierazzi, Labaca-Castro, Gimenez, Severi, Rosenberg,
  Sheatsley, Bostani, Chen (robust PDF), Incer (from `papers/incer.pdf`, provided by the user), Dyrmishi, Smutz &
  Stavrou, Jigsaw, PBP, RAMP, Perasso, PASA, Cheney. A's space is crowded, but every paper obtains "what can the
  attacker reach in feature space" by hand, from data, or by running transformations.
- **Model:** `docs/feature-provenance-model.md`, three layers (parse: membership/location; additive contributions;
  readout), edits in bytes translated to items (content / item-creating / structural), claims C1-C4, a worked example
  (adding a writable section in EMBER). Adopted as the working design after the "P + R" two-model idea was rejected.
- **Pending runs:** run/75 is on hold (old direction); do not run.
- **Next:** coverage of real transformations on paper; proof sketches for C1-C4; mock A's table (see `PLAN.md`).
- Memories updated: symmetry is nice to have (not required); PE specifics allowed but keep framing malware-generic; be
  harsh about novelty; never raise deadlines.

**2026-10-21 (later still): Table 2 gets a KernelSHAP row (predicted, blue); run/75 ready.**
- `scripts/cm_shared_edit.py --kernelshap`: the GBDT's KernelSHAP over 4,096 windows as a second window baseline,
  computed in a cached, resumable phase (1b) with Section 5.1's worker (`faithfulness.process_kernelshap`, fork pool;
  inside the spawned phase-2 workers it ran ~3x slower). Smoke test (3 files): run 72 reproduces exactly.
- **run/75** (not run; the user runs it later): 500 files, 16 workers, ~32 h. Hypothesis: rho ~0.25-0.35, between
  occlusion (0.21) and the pullback (0.48). If KernelSHAP reaches the pullback, 6.1's claim weakens: stop and decide.
- Manuscript (blue, as if run): Table 2's KernelSHAP row (rho 0.31, AUC 0.65), 6.1's prediction paragraph (CI of the
  difference 0.09-0.26; 32,770 queries vs. one extraction), the "realistic alternative" sentence, the intro's
  comparison. `docs/review-prompt.md` now tells the reviewer how to treat blue placeholders.

**2026-10-21 (later): front matter, background, discussion, conclusion brought up to date; end-to-end pass.**
- Abstract and introduction: the cost ratio was stale (1/135 -> "about a hundredth of its time", 5.1's 1/95); byte
  resolution now "more evidence than any direct explanation, from one extraction instead of tens of thousands"; 6.1 led
  by its decided claim (the pullback predicts the GBDT's drop under MalConv-guided edits, 0.48 vs. 0.21), triage
  second; the pushforward's surrogate result in the abstract; the mitigation bullet names whose fields are zeroed.
- Background (position, third point), discussion (KernelSHAP 0.68 -> 0.97 as evidence that transfer quality is source
  quality; a new paragraph on direct explanation at finer windows: ~131k extractions at 16k windows), conclusion
  (rewritten around the current results), ethics (the trigger is now one worked example; 6.1's transfer to the GBDT).
- Fixes: the method claimed Appendix C measures the data-flow convention's cost (it does not); 6.1's three questions
  were punctuated as two; small wording.
- Unchanged, for the user: the blue Android sentence (W7) and 6.2's retrained row; the TODO in 6.1 to use the best
  window explainer (now KernelSHAP@4096) in place of occlusion@4096 for Table 2 needs a run. `make check`: one 1.7pt
  overfull vbox on page 17 (column break in the appendices; will reflow).

**2026-10-21: run 74 read; Section 5 and Figures 3-4 updated.**
- **Run 74 (KernelSHAP over 4,096 windows, GBDT):** clean (100/100, no failures or invalid points), 8.1 h (not ~5 h).
  Hypothesis held: 7.17 log-odds (vs. KernelSHAP@1024 6.31, adaptive@4096 5.96, occlusion@4096 5.51), below the
  byte-level pullback (8.03). But the margin narrows: the pullback beats it on only **59/100 files (p = 0.005)**, though
  at every budget and with 1/32,770 of its queries. Pushed forward it reaches **0.97** of TreeSHAP's evidence (KernelSHAP
  0.68/0.75/0.83/0.97 at 64/256/1k/4k; the trend 0.79 at 4k). Run 66's numbers reproduce exactly; output
  `artifacts/experiments/e1/seed-0/zeros-typical-header-shared-ks4096/` supersedes run 66's as the figures' source.
- **Manuscript:** `scripts/paper_figures.py` reads run 74 by default (adds `kernelshap_k4096`). Figure 3 now shows
  KernelSHAP@4096 (32,770 extractions) in place of @1024; caption "well below" -> "below". 5.1: KernelSHAP keeps
  improving with finer windows (6.3 -> 7.2); pairwise counts updated; the opener drops "substantially" and says "from one
  query instead of tens of thousands". 5.2: KernelSHAP 0.68 -> 0.97. `make check` clean.
- **Reviewer risk to note:** with KernelSHAP still rising at 4,096 windows, a reviewer may ask whether 16k windows would
  match the pullback; the paper's answer is cost (131k queries per file), not faithfulness.

**2026-10-20 (end of afternoon session): 6.1 written; body filled except the deferred runs; run/74 running.**
- **Run 72 read (500 files):** hypothesis held. MalConv-guided edits of 3 loader-safe fields: Spearman 0.48 (pullback)
  vs. 0.21 (occlusion, 4,096 windows) vs. 0.03 (bytes); AUC 0.78 / 0.60 / 0.55 (drop > 1, 291/499); CI of the rho gap
  [0.17, 0.38]. Details in `docs/experiments/cm.md`.
- **Manuscript:** 6.1's attack paragraph and Table 2 written (run 68's stub/slack attack: MalConv evaded 81%, the GBDT
  rises, the pullback shows why; MalConv-guided field edits: GBDT drop 1.36, both > 1 on 43%; the prediction; one
  sentence for the asymmetric GBDT-guided mirror). Coherence: 6.1 opener, Section 6 close, intro's pullback bullet,
  discussion. `make check` clean. Remaining blue: 6.2's retrained row and sentence; the discussion's Android sentence.
- **Pool bug fixed** (commit 534edc3): two benign ImageBase values above 2^63 overflowed into a junk entry; a file that
  drew it skipped one field. **Run 73** reran 49, 59, 72: every estimate and p-value unchanged; the `*fixpools*`
  outputs are the current ones.
- **Extraction ~2x faster** (commit 52db0f4): `features.byte_counter` replaces `Counter` for thrember's and pefile's byte
  counts by name (pefile monkeypatched at import; no original line changed; identical features; `docs/design.md`,
  "Speed"). It affects no other code (`collections.Counter` untouched).
- **Run 74 running** (user, started 2026-10-20 ~16:00): KernelSHAP over 4,096 windows on the GBDT, reusing run 66,
  ~5 h. Log `artifacts/logs/pb1-shared-ks4096-seed0.log`; output `artifacts/experiments/e1/seed-0/
  zeros-typical-header-shared-ks4096/`. Hypothesis: beats KernelSHAP@1024 (6.31) and adaptive@4096 (5.96), stays below
  the byte-level pullback (8.03).
- **Decisions (user, 2026-10-20):** MalConv retraining, the scale-up, and more seeds stay deferred. The three remaining
  review items were evaluated and dropped: a stronger attacker on the zeroed MalConv (outcome near-certain; belongs with
  retraining), a named-feature TreeSHAP baseline for Table 2 (it presumes a hand-built field-to-feature map, which is not
  a realistic alternative; the GBDT-score covariate is optional, only if a reviewer asks), and a 0.1% FPR column (noisy
  at 5,000 benign files; at most one sentence later). Sentence-level rewordings (the 6.2 "attack surface" sentence,
  "for any extractor") ignored for now.
- **Next:** read run 74 and update Figures 3-4 and Section 5; a fresh critical review of the current draft
  (`REVIEW.md` predates the reorganization and most results); the W7 decision (Android vs. scoped claims; the blue
  Android sentence must go or be filled); then abstract, introduction, conclusion.

**2026-10-20 (end of morning session): Section 5, 6.2, and Appendix C filled; 6.1's claim decided, waiting on
run/72 (500 files, the user is running it).**
- **6.1 decided (user, 2026-10-20).** Claim: before any attack, the GBDT's pullback on the fields an attacker who
  explains only MalConv edits predicts how much the GBDT's score drops; windows and byte counts do not. Defender
  framing kept (optionally worded as the defender red-teaming the pair); the GBDT-guided mirror is one sentence
  (transfer is asymmetric: GBDT-guided edits drop MalConv 0.59 vs. MalConv-guided edits dropping the GBDT 1.31; the
  mirror's predictor, MalConv's IG, needs no P). Run 68 becomes the "wrong region" contrast (DOS stub and slack: the GBDT
  puts ~0.1% of its evidence there and rises). Run 71's five-way "who chooses the fields" table stays in
  `docs/experiments/cm.md`, not in the paper (MalConv-only selection does as well as the pullback, 37% vs. 32%).
- **Run 71 (100 files):** prediction under MalConv-guided edits: Spearman 0.47 (pullback) vs. 0.25 (occlusion, 4,096
  windows) vs. -0.04 (bytes); AUC 0.78 / 0.64 / 0.52 (drop > 1, 56 positives). The pullback leads in all five arms but
  the CI of the gap for the MalConv-only arm starts at 0.00, hence **run/72** (500 files, ~25 min; log
  `artifacts/logs/cm-shared-edit-500-seed0.log`; output `artifacts/experiments/cm_shared_edit_500/seed-0/`). The script
  now prints the prediction table itself.
- **run/66 (5.1/5.2, GBDT):** clean. Adaptive KernelSHAP beats occlusion only at 4,096 queries (5.96 vs 5.51, 70/100);
  below it at 64/256 queries (3.42 vs 4.79; 4.46 vs 5.07), about even at 1,024 (5.37 vs 5.47). KernelSHAP over 1,024 windows is the strongest
  direct method (6.31 at 8,194 queries) and beats the pullback summed into the same windows; the byte-level pullback
  (8.03, one extraction) beats it on 72/100 and adaptive@4096 on 81/100. Pushforward relative to TreeSHAP's pullback:
  KernelSHAP 0.68/0.75/0.83 (64/256/1k), adaptive 0.61/0.65/0.70/0.76, occlusion flat ~0.65, trend 0.64/0.63/0.70/0.79,
  bytes 1.00. Hypothesis half held (below the pullback: yes; adaptive beats occlusion at equal queries: only at 4,096).
- **run/67 (5.2, MalConv):** clean; hypothesis held. Gradient-free sources beat the surrogate (occlusion@1k 4.23,
  71/100; KernelSHAP@1k 4.69, 83/100; vs 3.28); IG pushforward on top (6.25).
- **run/68 (6.1 attack transfer): NO-GO** (superseded by the decision above). MalConv evaded 81%; the GBDT never crosses its threshold and *rises* on
  78% of files (median +1.06 log-odds); only 5/100 drop by >1 log-odds. Pullback on E ranks the signed change best
  (Spearman 0.34, p = 5e-4, vs occlusion 0.18, |C| -0.18), but the bootstrap CI of the difference with occlusion spans 0
  ([-0.09, 0.41]).
- **run/69 (6.2 unfiltered audit): done, hypothesis failed (neutral-to-favorable for the paper).** Two script fixes
  (IG symlink; `--direction malware`, which the first rerun lacked: discovery wrote only the benign direction, kept in
  `audit-discover-unfiltered-benign-seed0.log`). Unfiltered candidates add hashed section entropies, byte-entropy bins,
  the DOS-stub message; none confirmed. MalConv: 8 of the 9 Table 3 fields confirmed again (IAT drops out of the top
  20); surrogate: the same 9 as before. No section/import/string reliance. The run's preset gate reads "no-go" (b: 4 of 8
  confirmed shared with the surrogate, exactly half), only because IAT left the top 20. Manuscript: 6.2 keeps the
  filtered protocol (Table 3 and the evasion/mitigation rest on it) and states the unfiltered run as a robustness
  sentence; the blue sentence is gone.
- **Run 70 (Appendix C):** exact, max difference 8.5e-14 over 2,000 files; filled.
- **Manuscript (commit b2aea56):** Figures 3-5 regenerated under byte deletion (`scripts/paper_figures.py`, new
  `pf_gbdt.dat`; Figure 3 adds KernelSHAP@1k and adaptive@4096); every `\synthetic` in Section 5 and Appendix C
  replaced. Wording changed where results changed direction: "as faithful as direct explanation at the same resolution"
  narrowed to "as faithful as occlusion" (KernelSHAP beats both at matched windows); adaptive pays off only with a large
  budget; the TreeSHAP trend is no longer called a bound (KernelSHAP exceeds it). The introduction (line 42) already says
  "as faithful as occlusion". Remaining blue: 6.1 (Table and paragraph), 6.2 (audit sentence; retrained row, deferred),
  the discussion's Android sentence (deferred).

**2026-10-19: manuscript reorganized** (user). Sections 5-6 were one per operator (Pulling Back / Pushing Forward);
now **5 Evaluating the Transfers** (`_e_evaluation.tex`: 5.1 pullback faithfulness and cost, 5.2 pushforward
faithfulness, 5.3 the planted trigger, both directions in one subsection) and **6 Security Applications**
(`_f_applications.tex`: shared setting, 6.1 comparing two detectors file by file, 6.2 auditing MalConv, 6.3 the two
together). Reasons: the paper is a method plus two security applications; the pushforward's "trigger" never tested the
pushforward (W6); the applications already cross operators; the field-level baselines (REVIEW risks 1-2) have a natural
home. Labels `sec:XML:PullbackTrigger`/`PushforwardTrigger` merged into `sec:XML:Trigger`; new `sec:XML:Evaluation`,
`Applications`, `Together`. Text otherwise unchanged except seams (section openers/closers, duplicated motivation
trimmed, intro's "three questions" and contribution pointers). `REVIEW.md`'s file:line references point to the old
files (`_e_pullback.tex`, `_f_pushforward.tex`).

**Experiment code written (2026-10-19), not yet run at scale.** WP0-WP5, WP7 (implementation plan): adaptive
KernelSHAP (shap PartitionExplainer) and a sparse window pushforward in the library; faithfulness.py extended for the
shared-protocol 5.1/5.2 (KernelSHAP at every budget, adaptive KernelSHAP, feature rankings scored by byte deletion);
pf_malconv.py for MalConv's window sources; featuresets/ember2024/attack.py (loader-safe DOS/stub/slack attack) and
cm_transfer.py for 6.1 attack transfer; cm_disagreement_select.py --both_detect; audit unfiltered via existing scripts.
All smoke-tested on GPU 3, lint + strict mypy clean, new unit tests pass. **Run scripts run/66-69 ready for the user**
(GPU 3, <=16 workers); run/66 ~8 h, run/67 ~2-3 h, run/68 gate ~15 min, run/69 ~12 min. Committed up to this point.

**Low-hanging fruit done (2026-10-19; commits 94708bb, ca5dbdb, 80aa47e):** Influence axiom as "computed from",
classifier renamed f, overclaims trimmed, identifiability result kept as a Section 3 illustration; theory coverage
(67% additive / 9% data-flow / 23% null of TreeSHAP's attribution; run 64) and instrumentation cost (0.19 vs 0.05 s
median, 2.7 vs 0.4 s at 4 MB; run 65; "adds little" corrected); related work checked against sources. **Adjudication
pre-check: likely no-go** (scores alone AUC 0.91, + triage 0.90 on 50 pilot files); WP6 on hold, the 6.1 placeholder
paragraph stays until the user decides. Run numbers in the implementation plan now start at 66. Next: decision on Part
B, then WP0.

**Manuscript carries the new methodology (fd814be)** with blue placeholders for every new result. **REVIEW
reassessed** (`docs/review-reassessment-2026-10-19.md`): every WP answers a named review risk; low-hanging fruit listed
(axiom and notation fix, overclaims, additive-share and worst-case numbers, adjudication pre-check on pilot files,
stronger attacker on the mitigated MalConv, related work, Part A covariates); open decision: keep the identifiability
result as an illustration in Section 3.

**Implementation plan (2026-10-19):** `docs/implementation-plan-2026-10-19.md`, WP0-WP8 (adaptive KernelSHAP and
query accounting; 5.1/5.2 reruns in one faithfulness run; 5.2 on MalConv; the 6.1 attack with a feasibility gate;
adjudication; the unfiltered audit; figures). Part B rewording approved by the user. Next: WP0.

**Specs finalized, round 3 (2026-10-19, commit dcf7928):** 6.1 = option 3 (white-box MalConv attack on the DOS
header, DOS stub, and section slack; does the GBDT's pullback on that region predict its confidence drop?) + option 2
reworded as adjudication of GBDT-only disagreements (scores vs. scores + triage shares), pending the user's OK. Next:
implementation plan for the reruns (5.1, 5.2) and 6.1.

**Specs round 2 (2026-10-19, user feedback; commit 228e5d5):** cut from the manuscript: the black-box P (3.3.1, 5.1,
intro, discussion, open science), 5.3 the planted trigger (archived; struct trigger kept as a worked example in a new
appendix), the naive translation. Decided for the reruns: one byte-deletion measurement and one cost unit (detector
queries + seconds) for 5.1 and 5.2; budgets 64/256/1,024/4,096 for every window method; adaptive KernelSHAP =
shap's PartitionExplainer; 5.2 mirrors 5.1; log-odds in Section 5, probabilities in Section 6. Open: which 6.1
option(s) (attack transfer with white-box GAMMA preferred; design first, no code yet). See `docs/experiments/specs.md`.

**Phase 1 drafted (2026-10-19):** `docs/experiments/specs.md` (one spec per experiment, comparison class under rule
(a), mocks). Surfaced: adaptive occlusion is the missing in-class baseline for 5.1; the naive translation on MalConv for
5.2; run 57 argues against full joint evasion in 6.1; the unfiltered audit is required under (a). Next: the user
reviews the specs, then Phase 2 (baseline rule) and the 6.1 brainstorm.

**Phase 0 done (2026-10-19):** field-occlusion oracle removed from 5.1 and Figure 3 (5.1 now compares format-agnostic
methods only; run 56 stays in `docs/experiments/pb1.md`); 6.3 deleted (the feature-by-feature comparison of the two
detectors is dropped, a two-sentence close ends 6.2). 16 pages, clean build.

**Next: `docs/plan-2026-10-19.md`** (research plan from REVIEW.md + the user's comments): Phase 0 cleanups
(remove the field oracle from 5.1, delete 6.3; awaiting a yes), Phase 1 per-experiment claim specs, Phase 2 one
baseline rule for the paper (brainstorm), Phase 3 rebuild Section 6 (shared setting; find/confirm/realize/act for both
applications), then theory consistency, the Android decision, and the final round.

Last updated: 2026-10-16 (end of session). **Section 3 now carries real theory (answer to W1, thin novelty).** Today:
- **Brainstorm** of directions for W1 (in chat; outcome in `docs/theory.md`). Kept: (A) a Shapley-grounded construction
  of P and (B) the pushforward as an inverse problem. Dropped: a "theory of resolution" and axiomatic uniqueness.
  Parked as possible case studies: bounds on what control of a byte set can do; naming a raw-byte model's units.
- **Coarsening out of Section 3** (user: weak, distracting). Granularity/P^G moved to a new **Section 4, "Experimental
  Setup"** (`manuscript/_d_setup.tex`: EMBER instrumentation and Table 1, data/models/explainers, deletion operator,
  windows of bytes), an experimental device only; the experiments that use it are unchanged.
- **P stays nonnegative** (user), with a short "Why provenance is nonnegative" paragraph in 3.3.
- **Run 61, go/no-go for the iterated pushforward** (`scripts/pf_inverse.py`, `run/61_pf_inverse.sh`, user ran it):
  recovering TreeSHAP from its pullback, R rises 0.80 -> 0.86 at bytes (93/100 files, p = 7e-17) and 0.36 -> 0.44 at
  256 windows (84/100), for all three explainers. Below the "toward 1" hypothesis: the limit matches the byte
  explanation exactly (residual ~1e-9) but misses 37% of the feature explanation, i.e., non-identifiable features.
  **A qualified go:** the theory explains the gap; the algorithmic gain is reliable but modest.
- **Section 3 rewritten** (`_c_method.tex`): 3.3 items, Definition Shapley Provenance, Proposition Additive Features
  (instrumentation = Shapley provenance for features additive over their items: fields, counts, histograms over a
  fixed denominator, one-sign hashed counts), the data-flow convention for entropies/averages/ratios/min-max, why
  nonnegative, 3.3.1 the black-box estimate; 3.4 Proposition Exact Pullback (linear model -> exact problem-space
  Shapley values; G-DeepSHAP's linear-chain result for a program), Definition and Proposition Exact Pushforward
  (iteration converges, conserves, recovers everything the bytes determine; one step exact without shared elements).
  Key modeling choice: the game holds each feature's context fixed (parse, denominators). Build clean, 16 pages.

- **Later the same day:** Section 3 feedback applied (Shapley 1953 cited; new background subsection 2.3 "Shapley
  Values"; definitions and propositions numbered separately; the exact pullback's baseline stated; paragraph splits).
  **Run 62** (identifiability ceiling, twins oracle): R at bytes 0.80 / 0.86 / 0.95 (one step / exact / twins oracle),
  at 256 windows 0.36 / 0.44 / 0.86: what the exact pushforward misses lies mostly in features with identical
  provenance. **Run 63** (MalConv): exact = one step (median area 6.25 both), both 1.9x the surrogate.
  **Decided (user):** the experiments keep the one-step pushforward, nothing reruns; Section 3 keeps Definition 7 and
  Proposition 3 as theory (what any pushforward can recover); Section 6.1 reports the exact form and the twins result
  in two sentences (GBDT and MalConv). Details: `docs/theory.md`, "The ceiling and MalConv".

- **Front and back matter updated** for the theory: abstract (now 232 words: Shapley-grounded P, exact pullback, the
  pushforward as the pullback's inverse, the mitigation), introduction (a new paragraph on the theory; contributions),
  "Our Position", a discussion paragraph "Beyond the exact cases", and the conclusion. Light-touch: the structure and
  results of these sections are unchanged.

- **Section 4 restructured** (`_d_setup.tex`): 4.1 Provenance for EMBER (items per feature group, null element),
  4.2 Data, Detectors, and Explainers (the explainer settings moved here from 5.1), 4.3 Measuring Faithfulness by
  Deletion (operator + evidence-removed protocol + ties, moved from 5.1), 4.4 Windows of Bytes. 17 pages; one 2 pt
  overfull vbox on the last page (float reflow, harmless).

- **Pre-submission review (2026-10-16, read-only):** `REVIEW.md` in the repo root (simulated CCS review, claim audit,
  threat models, risk register, action plan, draft abstract/contributions/threat models). Top risks: no per-field
  IG baseline for the audit/MalConv test (the oracle's parser map already exists), byte vs. field resolution
  unablated (W4), triage without a security outcome; synthetic blue results must go before submission.

**Current goal:** the user reads the revised front/back matter and Section 4; then reassess W7 (Android); the scale-up
last.

**Waiting on the user:** the black-box P's final place (now 3.3.1, maybe an appendix later); whether to keep the GBDT
window-pushforward test (a lab study need not be realistic).

**Appendix C drafted (2026-10-19):** "Checking the Exact Pullback" (`manuscript/_j3_exact_pullback.tex`), the
exactness check for Proposition 2 (review W2), with synthetic predicted numbers; Proposition 2 now points to it. The
script `scripts/exact_pullback_check.py` is still to write (light CPU, no pipeline; `docs/plan-2026-10-19.md` Phase 4
item 3). Synthetic numbers to replace: median l1 2e-3, data-flow agreement 0.74.

## Overnight runs launched 2026-10-19 (results expected 2026-10-20 a.m.)

The user is running, in one tmux chain (GPU 3, 16 workers): `run/66_pb1_shared.sh` (5.1/5.2 GBDT, ~8 h) ;
`run/67_pf_malconv_shared.sh` (5.2 MalConv window sources, ~2-3 h) ; `run/68_cm_transfer.sh` (6.1 attack transfer +
its feasibility read, ~15-20 min) ; `run/69_audit_unfiltered.sh` (6.2 unfiltered audit, ~12 min). Outputs:

- `artifacts/experiments/e1/seed-0/zeros-typical-header-shared/` and `artifacts/reports/pb1_tables-shared.md` (66)
- `artifacts/experiments/pf_malconv/seed-0-shared/` (67; table at the end of its log)
- `artifacts/experiments/cm_transfer/seed-0/{files,report}.parquet|json` (68)
- `artifacts/experiments/audit_discover_unfiltered/`, `audit_scramble_unfiltered/` (69)
- Logs in `artifacts/logs/`.

## Next (this thread) — WP8, after the overnight runs

1. **Read the results** (see the resume prompt). First checks: 66's pushforward table (does adaptive KernelSHAP stay
   below the byte-level pullback? does the pushforward of window sources rise with resolution?); 68's summary
   (`gbdt_drop_over_1.0`, `malconv_evaded`, per-predictor Spearman/AUC) — **the go/no-go for 6.1 attack transfer**; 69's
   confirmed features by group (any section/import/string features, not only header fields?).
2. **If 68 is a go:** keep attack transfer as 6.1's security outcome; replace the blue Table 4 and prose with the real
   numbers. **If no-go** (GBDT does not move): fall back to option 1 (controlled shared-reliance changes; specs.md).
3. **WP8:** regenerate Figures 3-5 and the 6.1/6.2 tables from the real data (`scripts/paper_figures.py` and the table
   scripts); replace the blue placeholders in Sections 5-6; `make` and `make check`. Figure 4 still shows old-protocol
   data and must be regenerated under byte deletion.
4. **Deferred, user decides:** KernelSHAP/adaptive at 4,096 windows and the scale-up (500 files); retraining MalConv
   (Table 5's blue row) and the stronger attacker on the mitigated model (rerun run/68's attack with the audited
   fields zeroed); W7 (Android second extractor); the front/back matter rewrite from the final results.

Earlier plan (superseded by tonight's runs): front/back matter feedback; refine Section 4; W7 then scale-up.

---

Previous session (2026-10-14):

**The self-review's main criticisms are answered with measured results, and
Sections 3-5 are revised for presentation.** Today, in order:
- **Run 56, field-occlusion oracle** (W2/W4): gain 0.91 at 124 extractions/file; the byte-level pullback beats it 88/100.
- **Run 57, B9** (triage vs. attack-caused disagreements): negative (design flaw: ~600 changed bytes in a ~19K-byte
  readout). Abandoned and cut from the paper (user: present what works).
- **Run 58, M1** (W5): pushed forward on MalConv, the pushforward removes 1.9x the surrogate's evidence (99/100 files),
  1.46x IG over windows, 2.7x random features. **Run 60**: same with random fill (2.0x, 99/99), closing W4.
- **Run 59, M3 test-time mitigation** (W6): zeroing the audited fields cuts the strongest loader-safe attack 16.8% ->
  8.2% (pushforward's 8 fields) / 2.9% (both methods' 12) at 2.0 / 3.5 pts of detection. Framed as a trade-off: the
  point is that the pushforward identifies actionable issues (user). Retraining half stays blue.
- **W6 writing:** comparison threat model (stand-ins), audit vs. surrogate backed by M1 ("use both").
- **Sections 3-5 revised** (`docs/review-sections-3-5-2026-10-14.md`, "Outcome"): three pgfplots result figures,
  conventions and audited-fields tables, validity fixes, sharper novelty, no self-deprecating labels.

**Current goal:** the user reads Sections 3-5 (pp. 3-11 of `manuscript/main.pdf`); then the same treatment for the
intro, abstract, discussion, and conclusion; then reassess W7 (a second extractor, Android) once the PE/EMBER
contributions are solid. The scale-up (2,000 files / 3 seeds, then 10K on the cluster) comes last.

## Where we are

| | state |
|---|---|
| **Manuscript** | `manuscript/` (CCS `acmart` `sigconf`, anonymous; `make`, `make check`: clean). Order: 1 Introduction (`_b`) / 2 Background and Related Work (`_b2`) / 3 Transferring Explanations with Provenance (`_c`; Figures 1-2 conceptual, Table 1 EMBER provenance conventions) / 4 Pulling Back to the Bytes (`_e`; setting; 4.1 with Figure 3 faithfulness vs. cost; 4.2 trigger; 4.3 comparison with Table 2 triage) / 5 Pushing Forward to the Features (`_f`; 5.1 on the GBDT with Figure 4 and on MalConv with Figure 5; 5.2 trigger; 5.3 audit with Table 3 audited fields and Table 4 mitigation) / 6 Discussion / 7 Conclusion; appendices. 14 pages. Figures are pgfplots (palette in `main.tex`; MalConv curve data from `scripts/paper_figures.py` -> `manuscript/assets/data/`). **Blue placeholders left:** the retrained-MalConv row of Table 4 and its sentence (5.3), the Android paragraph (discussion). **Not yet revised:** abstract, intro, discussion, conclusion (only number fixes). Numbers are pilot-scale. |
| **Pullback (PB1, PB2, CM)** | Pilot done (100 files; 50 per trigger; 25 per triage cell). 500-file seed-0 runs prepared: `run/51` (PB1 full baselines, GBDT + MLP), `run/52` (operator variants), `run/54` (CM: cross-deletion, shared, triage at 100/cell, window triage), `run/55` (triggers, 250 files each). |
| **Pushforward (PF1, PF2, AU)** | PF1/PF2 pilot done. **On MalConv (runs 58, 60, `docs/experiments/pf1.md`):** 1.9-2.0x the surrogate under both fills. **AU (runs 47-49, 59; `docs/experiments/audit.md`):** realizable evasion 12.4% vs. 6.0% null, surrogate 10.4%, union 18.4%; test-time mitigation 16.8 -> 2.9% strongest attack for 3.5 pts detection. Retraining MalConv (mitigation's second half) deferred to the cluster round. |
| **CP / theory** | Cut from the paper, archived (`manuscript/archive/`). |
| **The MLP** | **Cut from the manuscript body (2026-10-14)**; returns in future work. The code and runs keep it; the body carries only load-bearing results. |
| **Speed** | String features 2.1x faster, bit-identical. Deferred ideas (`docs/design.md`, "Deferred optimizations"): reuse the extractor's parse in `verify` (~15%); numpy byte counts for the entropies and vectorized byte-entropy windows (~30% together, needs copying thrember code or patching pefile; user: not now). |

## Next

1. **User reads Sections 3-5** and gives feedback; apply it.
2. **Front and back matter:** abstract, introduction, discussion, conclusion get the Sections 3-5 treatment (narrative,
   presentation, consistency with the revised body; results stay in the evaluation). Today's new results (MalConv
   faithfulness, mitigation, fields table) are only partly reflected there.
3. **Reassess W7** (generality): the Android second extractor (`docs/revision-plan.md`, item 12) is the largest
   remaining weakness and several sessions of work; decide scope once 1-2 are done (user: PE/EMBER first).
4. **Later:** MalConv retraining (Table 4's blue row); the scale-up (2,000 files / 3 seeds, then 10K on the cluster),
   which also enlarges the triage cells (W10); deferred optimizations before it; CCS Cycle A vs. B (user, open).

## Decisions

2026-10-14 (whole day):
- **B9 abandoned and cut** (user): negative results that do not support the method are not reported; restrictions are
  stated where they matter. Writing guidance saved as memory `paper-writing-style` (natural prose, no rigid rules, never
  call our method weak, Definitions 1-2 stay, no results-first reordering, be ambitious about the pushforward's novelty).
- **Mitigation framed as a trade-off** (user): the audit's value is identifying actionable issues, not a perfect defense.
- **Figures:** result figures added; Figures 1-2 kept with fixes (conservative, user's guidance).

2026-10-13 (night, end of session):
- **The user runs `run/50`-`55` on the code as-is** (no verify/parse change tonight). Two optimization ideas are noted
  for later in `docs/design.md`, "Deferred optimizations" (user asked).

2026-10-13 (night, seed-0 scale-up prepared):
- **Scale-up = 500 files, seed 0, full fidelity, GBDT + MLP** (user). Selection
  `artifacts/explanation_set/ts-scaleup500-seed0.parquet` (250/label, a superset of the 100 pilot files; written by
  `faithfulness.py --include ... --select_only`). Scripts `run/50`-`55`, all smoke-tested; the user runs them in tmux
  (16 CPUs, GPUs 2 and 3). Order: 50 (KernelSHAP, `explain.py --fill_missing` keeps the pilot rows) -> 51 (pullback
  faithfulness, ~12 h) -> 53 (pushforward) and 54 (comparison); 52 (operator variants) and 55 (triggers) need only 50 /
  nothing. ~20-24 h in all, run one after another.
- **String features 2.1x faster overall, bit-identical** (`features.py`, added at the end: one `finditer` per regex
  over the joined strings instead of 590k `re.search` calls; verified on 400 files and in `tests/test_ember2024.py`).
  The user rejected replacing pefile's / the entropy `Counter`s ("too much code to review"): only the string change and
  numpy for its per-character loop stay. The runner's cost model is now ~2x pessimistic.

2026-10-13 (evening, experiments: 1a/1b of the experiment plan):
- **Plan (user):** now 1a (realizability of AU's evasion) and 1b (significance on fresh, detected held-out malware);
  then a seed-0 scale-up to 2,000 files. Mitigation (1c) is a manuscript TODO, no code yet; real-attack transfer (1d)
  not now (maybe never). A later round (3 seeds, 10K files) runs on a cluster.
- **Run 47 done** (`docs/experiments/audit.md`, "Held-out evasion and realizability"). Run 46's rates were inflated
  (non-detected files counted; random draws that broke the parse dropped; evaluated on the confirmation files). On 902
  fresh detected malware: pushforward 19.7% vs. random 12.3% (+7.5 pts, p = 3e-14), surrogate 19.0%, union 30.6%.
  **Realizable (loader-safe) pushforward: 12.4%, not above random free fields (10.9%, p = 0.17);** realizable union
  18.4% (p = 2e-16). The manuscript's AU numbers are now wrong (22.5/16.5/24.6/35.1) and must be updated; how to frame
  realizability is for the user to decide. Proposed follow-ups (cheap): decompose the realizable loss (IAT exclusion
  vs. benign values in constrained fields) and a null that excludes the recipe's own fields.
- **Run 48 done:** realism costs the pushforward recipe 19.7 -> 12.4% (IAT/skips 3.4 pts, abnormal values 3.9 pts);
  against a null of loader-ignored fields that no method confirmed (4.4%), the realizable recipe is +8.0 pts
  (p = 3e-13). Run 47's "failure" came mostly from a null drawn half from the confirmed fields. Open: a broader null
  (all loader-ignored header fields), and whether to validate the loader classification by execution. User wants
  realistic perturbations only (CCS standard), so the paper's AU headline becomes the realizable numbers.
- **Run 49 done (broad null):** realizable pushforward 12.4% vs. 6.0% for as many other loader-ignored fields outside
  the DOS region (+6.4 pts, p = 3e-12) and 3.8% for all loader-ignored fields; realizable union 18.4%; realizable
  surrogate 10.4%. User: lead with the pushforward; no sandbox validation needed ("we don't break the files"). Manuscript
  AU numbers still to update (lower priority). Next: the seed-0 scale-up to 2,000 files (run/ scripts for the user).

2026-10-13 (evening, writing session, background/related work):
- Section 2 is now "Background and Related Work" (user): an overview of learning-based detection, post-hoc
  explanation, explaining malware detectors, transferring attributions, and an "Our Position" subsection with the
  three novelties (P for program extractors; the pushforward; detectors over different representations in one space
  -> triage and audit). The old standalone Related Work is archived (`archive/g_related_work_old.tex`).
- Notation (problem/feature space, Definitions 1-2, Figures 1-2) moved to Section 3.1 "Preliminaries". Figure 3 is
  input before 3.4 so the three figures do not stack on one page. Body ends on p. 11.

2026-10-13 (evening, writing session, polish pass 1; user's 7 criticisms):
- Intro rewritten in paper voice: research questions dropped, three compact contributions (method, pullback,
  pushforward). Figures 1-3 kept (user rejected a replacement overview figure); only their whitespace was tightened (Figure 2 panels fit their content; Figure 3 gaps and padding reduced; Figure 1 boxes slightly smaller).
- Section 2 is now Background (detectors: EMBER, GBDT, MalConv; explainers: SHAP, KernelSHAP, TreeSHAP, IG,
  occlusion; two spaces; faithfulness). Related Work moved to Section 3. The "Setting" subsection is gone: a short
  threat model opens each application (5.3 CM, 6.3 AU).
- Section 4 "Transferring Explanations with Provenance": theory first (P, pullback, pushforward), then constructing P
  (instrumentation, occlusion, granularity = coarsening as a paragraph, EMBER instance). Coarsening is kept because
  PF1 pushes window explanations through P over windows and PB1/CM's window controls use it.
- Experimental Setup dissolved: data/models open Section 5; explainer configs and the deletion operator in 5.1; the
  trigger in 5.2; EMBER instrumentation in 4.3. Desiderata and sigma-consistency archived. Bib: +lundberg2020local,
  +ke2017lightgbm.
- Short titles: 5 "Pulling Back to the Bytes", 6 "Pushing Forward to the Features". Body ends on p. 11 (limit 12).

2026-10-13 (evening, writing session, restructure):
- **Organized by operator** (user agreed): 1 Intro, 2 Background and Setting (spaces + a short Setting; the threat
  model is minor, user), 3 Explanation Provenance (P, **constructing P: instrumentation vs. occlusion**, transfers,
  coarsening), 4 Experimental Setup, 5 Pulling Explanations Back to the Bytes (faithfulness and cost incl.
  instrumented vs. black-box P; planted trigger; comparing two detectors), 6 Pushing Explanations Forward into
  Features (faithfulness; ground truth for feature explainers; auditing MalConv), 7 Related Work, 8 Discussion,
  9 Conclusion. PB2/PF2 stay in the body (user: high value as laboratory experiments).
- CM and AU made parallel (Motivation / What the operator adds / Design / three findings).
- Threats to Validity and per-application limitations folded into a light Discussion (user: no self-criticism);
  design caveats moved into the designs. Claims lists and the experiments/status table archived.
- Appendices B/C (soundness, completeness, independence), E, and the symbol table archived (user: not measured, no
  practical impact); conservation kept as one sentence per transfer.
- Body ends at the bottom of p. 12 (references start p. 13). Next: section-level writing.

2026-10-13 (evening, writing session, later):
- **CP and the theory cut from the paper (user).** Sections 3.4 (statistics of P), 3.5 (round trips, bounds,
  perfect-reconstruction theorems), and 4.2 (CP) moved to `manuscript/archive/` (not deleted). Kept: the coarsened-
  provenance definition (short, in 3.3) and the Bayes reading of D+ in the pushforward. The instrumented-vs-black-box
  comparison is replaced by PB1's black-box pullback (1.02-1.04 of occlusion at 256 windows). C2 dropped (C1-C3 now);
  claim 3 is "faithful up to its source's resolution" (no overlap); paper claims renumbered 1-4. The resolution table
  lost its overlap row.
- **"Framework" -> "method"** (user: not much of a framework left). Section 3 is now "Explanation Provenance". Body
  ends on p. 13 (from 15).
- **Evaluation split** into Section 4 "Evaluating the Transfers" (intrinsic) and Section 5 "Comparing and Auditing
  Detectors" (extrinsic), each with opening and closing transitions.

2026-10-13 (evening, writing session):
- **Missing sections drafted** in paper voice. New section 2, "System and Threat Model": the defender (owns detectors,
  instruments the extractor once, white-box explainers), the two tasks (triage, audit), the adversary the audit
  anticipates (malware author changing bytes; scrambling measures reliance, not a demonstrated attack), out of scope
  (attacks on explanations/extractor/training data; the planted trigger is a ground truth, not a threat; dynamic
  features). "Summary" renamed "Conclusion".
- **Abstract reports AU's 22.5% next to the 16.5% random-field baseline** (Claude's call for honesty; the margin is
  modest and a reviewer would find it). Abstract is ~270 words (trim later if needed).
- **Cut candidates (not applied; for the user):** the claims list + experiments/status table in `_d` (~0.5 p); the
  research questions in `_b` (~0.15 p); PB2/PF2 and the trigger setup to the appendix (~0.9 p); CP's instrumented-vs-
  black-box paragraph to the appendix (~0.25 p); parts of `_c` (perfect-reconstruction theorems, desiderata, one of the
  three framework figures) to the appendix (~1 p).

2026-10-13:
- **Venue switched to ACM CCS 2027, Cycle A** (user; prefers the ACM template to USENIX's). CfP not out; by CCS 2026,
  abstract ~Jan 7 and paper ~Jan 14, 2027 (about 12 days earlier than USENIX's Jan 26). Cycle A rejects cannot go to
  Cycle B. `manuscript/main.tex` is now a complete document on `acmart` `sigconf` (anonymous; body <= 12 pp; Open
  Science and Ethics appendices after the bibliography); built with `make` in `manuscript/`.
- **3-C revised (the audit) worked and is written up.** The working framing scrambles the bytes P names for the
  features MalConv's detection rests on (not forging benign content, which does not transfer; see `docs/graveyard.md`).
  Mitigation deferred (SSViT GPU work); the surrogate column is kept but we do not fit the narrative to it (user).
- **Manuscript updated** to add 3-C, reframe CM as the pullback's local use, rewrite claim 3 for the pushforward
  application, and remove Appendix F (promoted into 3-C's global comparison).
- **Repository cleanup:** 3-B and the rule-based 3-C (YARA) are archived (`scripts/archive/`, `run/archive/`); their
  full plan docs are summarized in `docs/graveyard.md` and removed from the tree (kept in history).
- **CLAUDE.md relaxed:** the "do not propose X" research prohibitions became "generally unproductive, raise with a
  reason" (`docs/graveyard.md`, "Directions the user has generally found unproductive").
- **Docs reorganized:** experiment docs merged/moved to `docs/experiments/`; "3-A/3-C" vocabulary retired (CM/AU
  canonical); `design_provexp.md` -> `design.md`.
- **Introduction rewritten** with two framing choices (user): (i) **framework + symmetry first** (applications are
  evidence); (ii) **claim the fuller vision** in the contributions -> this makes AU's mitigation, CM's real-attack
  transfer, and the scale-up load-bearing before submission.
- **LaTeX toolchain = user-space TeX Live + latexmk + pdflatex** (not tectonic, not conda). Installed in `~/texlive`; `manuscript/main.tex` is a complete document
  (preamble included) built with `make`.

2026-10-12 (latest):
- **The pushforward needs an extrinsic application**; the symmetry is the novelty (user). CM alone is not enough.
- **3-C revised adopted:** auditing MalConv for shortcuts through the pushforward (`docs/experiments/audit.md`). Go/no-go
  requires a confirmed shortcut (confirmation is cheap); discovery on the 2,000-file explanation set; MalConv
  mitigation out of scope.
- **Hand-built domain-specific aggregation (a PE parser) is not a realistic alternative**: tremendous manual effort for
  one format (user). The realistic alternative is the surrogate.
- The surrogate is trained on the test split outside the explanation set (only MalConv's test predictions exist); to
  be stated in the paper.

2026-10-12 (later):
- **3-C on hold** after failing the sniff test: as built it rests on the pullback and Pᵀ, not the pushforward. Next
  step is a mock-up of a pushforward-native task, or 3-C as an application of P (user decides).
- **Screening criterion 6: mock the result first** (`PLAN.md`, section 3).
- Packing is not a motivation or case study (user). Rule semantics do not matter to the method (a rule is a byte set
  from an outside detector) but matter to the story's realism (user and Claude agree); YARA-Forge only later, for
  realism. capa deferred.
- Long installs and setup steps go in `README.md`; the user runs them.

2026-10-12:
- **3-B dropped** as the pullback application; **CM is the pullback's application** (user). 3-C stays the
  pushforward's.
- **Screening criteria** for extrinsic applications (`PLAN.md`, section 3): needs what only P gives; a practical task;
  the realistic alternative named; a go/no-go check first; extra skepticism for ideas already ruled out.
- **Hand-mappable findings are acceptable** when P automates the mapping (CM's shared bytes are named header fields;
  "the whole point of computers is to automate things", user). State the caveat once.
- **CM scope:** problem-space only (shared reliance; disagreement triage, option 1: blind / oppose / agree); the
  feature-space comparison goes to the appendix until it has a use beyond being interesting; byte n-grams set aside.
  Real-attack transfer noted for the future. In the paper: "shared reliance", not "attack surface".
- **Stay on track:** analyses must serve the current task; no rabbit holes (user).

2026-10-09 (second review, after run 21):
- **Paper structure:** framework / intrinsic evaluation (lab-style: PB1, PF1, CP's theory) / extrinsic applications
  (A = CM, B = byte-level discovery of what a detector keys on via the pullback, C = a pushforward application, to
  be found). Adding EMBER v2 as a second feature set is not worth it (too similar to v3).
- **Trigger experiments (PB2, PF2) demoted**, kept for now, possibly removed later.
- **Round-trip matrices M, N stay** as theory; ambiguity and overlap undecided; **coverage, localizability, and the
  null element's share are not contributions** (explanation-specific; a pipeline limitation, not a finding).
- **Theory:** an axiomatic (Shapley-style) uniqueness result noted in `PLAN.md` as a possible strengthening, not now.
- **Hypotheses before experiments, briefly** (not elaborate pre-registered readings; `CLAUDE.md`).

2026-10-09:
- **Claim 3, option A:** the pushforward is faithful up to its source's resolution, a limit set by P's overlap; PF2
  carries "useful". TreeSHAP's window round trip counts only through its trend across resolutions.
- **PF1 design** (`docs/experiments/pf1.md`): two references, the attributable-only check, the naive incidence sum, the
  criterion fixed in advance (above random and naive; R bands 0.8 / 0.5). No pushforward of triggered files.
- **PF2 reads r = ψ(1_T) as a support, not a target** (mass and top-k in supp(r)).
- **PF1's per-file reading dropped** (overlap at a fixed window count is mostly file size).
- **Rankings break ties by a seeded permutation**, never by position or index.
- **No scaling** until the pilot results and the claims are settled; manuscript polish is low priority.

2026-10-08:
- Evaluation structure and IDs (CP, PB1–2, PF1–2, CM; App-L, App-R). Pilot scale for most of the research.
- CP: ambiguity = entropy with effective support, overlap = 1 − M_jj, round-trip bounds, coarsening proposition.
- PB1: level 3 primary (level 2 robustness); main claim window-level parity, byte-level advantage secondary.
- The GBDT first; the MLP set aside temporarily.
- Trigger testbed: both triggers, dirty-label trigger → benign at 1%, long files overwritten, backdoor-fired filter.

2026-10-07:
- Framework domain-agnostic; experiments may use domain knowledge selectively (CLAUDE.md). No PE-structure analyses.
- Ambiguity and overlap *characterize P*; they were never meant to predict faithfulness.
- Localizability ℓ removed from the framework (an evaluation metric only); coverage κ kept. Ambiguity and overlap
  exclude unattributable features under the null policy.
- GBDT treats categorical features as numeric (shap misencodes LightGBM categorical splits).
- PB1 operator: level 2 = protect layout fields plus per-file breakers, zero the rest; level 3 = header fields take
  typical values; every ablated file verified. Insertion dropped. K = 256 windows.
- KernelSHAP: 32,768 samples, a 16-sample balanced background, `l1_reg=False`.

## Known issues and anomalies

- Interventional TreeSHAP violates local accuracy on 2 of 2,000 files (max 0.11; suspected shap deep-tree bug; trees
  reach depth 37); PB1 excludes those files.
- 2 of 2,000 census files differ from the feature store in 2 `pefilewarnings` features (thrember's hash-seed bug).
- `pefilewarnings` features have no provenance (pefile does not say which bytes caused a warning); the top one carries
  about 5% of the GBDT's attribution.
- Occlusion cannot see zero or protected header bytes and creates fill artifacts (new entropy windows, pefile
  warnings); most of its windows at fine resolution change nothing (score exactly 0).
- One test file differs from the released features in all byte-entropy features (max diff 1.7e-4); not explained.

## Notes

- Untruncated files match the released EMBER features except `strings:entropy` (float32 round-off) and a rare,
  hash-seed-dependent pefile-warning choice (thrember bug). 13–16% of files are truncated.
- TLSH dedup at threshold 30 removed only ~6% of the first 32,765 test files; `data/tlsh.py` dedup is exact.
- The released JSONL lists some samples twice; `build_metadata.py` drops duplicates.
- Model test ROC-AUC (seed 0/1/2): GBDT 0.99759/0.99764/0.99763; MLP 0.99586/0.99551/0.99595.
- The machine: 2 sockets x 16 cores, hyperthreaded (64 logical CPUs), about 500 GB of memory.
