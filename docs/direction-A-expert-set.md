# Direction A: the expert-set row (Gimenez et al.'s 40 features), for the user to check (2026-10-27)

Source: Gimenez, Sivaprasad & Fritz, "Certifiably robust malware detectors by design" (arXiv 2508.10038,
`papers/gimenez2025-certifiably-robust.pdf`, Section 3 and Table 1). The paper describes the set in one paragraph and
does not list it; the list below is from their code, `static_features_extraction.py:get_features` in
github.com/PFGimenez/certifiably-robust-malware-detectors-by-design (read 2026-10-27). Their monotone models
constrain **all 40 features to be increasing** (`monotonic_cst=[1]*n`); the paper reports AUC 76.2% for the monotone
GBT on these features (92.3% unconstrained), 100% robustness against their 8 attacks.

## The finding that changes the plan

The 40 features are **not EMBER features**. They come from their own LIEF-based extractor, and only about 5 of them
have a thrember v3 counterpart; the rest (per-library function counts, keyword counts over imported names,
entropy x size of sections with a given name) are hashed or absent in thrember. A mapping onto thrember names would
therefore be a different, much weaker set, and not their baseline. **Proposal:** re-implement their extractor (about
40 lines; on pefile, our parser, so that the row shares the parse with every other row), featurize the 10% store with
it, and train the monotone GBDT with all 40 constrained increasing, as they do.

## The 40 features, their thrember counterpart, and their direction under our threat models

Directions are reasoned by hand from their code against `docs/direction-A-threat-model.md` S1 (they are what C4
would compute if their extractor were instrumented). "Up" = the expert's claim holds; anything else is a hole in a
row that constrains every feature to be increasing.

| # | Feature (their name) | What it is | thrember v3 counterpart | M_add | M_full |
|---|---|---|---|---|---|
| 1-15 | `kernel32.dll` ... `urlmon.dll` (15 libraries) | number of functions imported from that library | none (hashed into `imports:*`) | **down via quirk** | **down via quirk** |
| 16 | `nb_imports` | number of imported libraries | `imports:num_libraries` | up | up |
| 17 | `nb_imported_functions` | number of imported functions | `imports:num_imports` | up | up |
| 18-26 | `Get_`, `Set_`, `File_`, `Console_`, `Thread_`, `Process_`, `Delete_`, `Write_`, `System_imported_functions` | imported function names containing the keyword | none | up | up |
| 27 | `modified_dos_stub` | DOS stub differs from one fixed stub (incl. one specific Rich header) | none | up | **both** (overwrite the stub back) |
| 28 | `has_resources` | a resource directory exists | `datadirectories:` resource size > 0 (approx.) | fixed | fixed |
| 29 | `no_sig` | no Authenticode signature | `authenticode:` (approx.) | fixed | up (remove signature) |
| 30 | `unknown_sections` | sections not named `.text`/`.data`/`.rsrc`/`.rdata` | none | up | **both** (rename into a known name) |
| 31 | `info_unknown_sections` | sum of entropy x raw size over those sections | none | up | **both** (rename; slack overwrite changes entropy) |
| 32-35 | `.text_info` ... `.rdata_info` | entropy x raw size of the section with that name | none | **down via quirk** | **both** |
| 36-39 | `.text-size` ... `.rdata-size` | raw size of the section with that name | none | **down via quirk** | **both** (rename away) |
| 40 | `nb_sections` | number of sections | `section:num_sections` | up | up |

The two quirks, both the same kind as thrember's duplicate-DLL overwrite (`docs/upstream-issues.md` item 1): their
code assigns, rather than accumulates, per name. Adding a second import descriptor for `kernel32.dll` with one
function *replaces* that library's count with 1; adding a section named `.text` with a few bytes *replaces*
`.text_info` and `.text-size` with the new section's small values. Both are edits in M_add. (Read from the code;
the import case assumes LIEF lists duplicate descriptors separately, to be confirmed on one file before relying on it.)

## What the row would show, and two decisions

Per the rule that no result may rest on an extractor quirk, the row must run on a patched variant (accumulate per
library and per section name; a pure addition, noted upstream). On that variant the expert set is sound under M_add
(as its authors argue) but **not under M_full**: 12 of its 40 features (rows 27, 30-39) can be lowered by renaming a
section, overwriting slack, or rewriting the DOS stub, all of which our M_full and their own secml-malware attacks
contain (the DOS-header attacks). Our adaptive search already has rename, slack, and DOS-stub edits.

Predicted row (M_full, 10% store, seed 0): AUC ~0.80, TPR@1%FPR ~30% (their 76.2% AUC was on a different dataset;
40 features lose most of the signal), toolkit evasion 0-5%, adaptive evasion > 0 through rename/stub edits. The
argument it supports: an expert set is far less accurate than the derived one (0.993 / 88.6%), and even an expert
analysis of 40 features misses holes that a derivation from the extractor exposes.

**Decided (user, 2026-10-29), both as recommended:** (1) re-implement their 40 features on pefile, with the two
quirks patched (accumulate per library and per section name) as a pure addition noted upstream; (2) report the row
under both M_add and M_full.

**Built (2026-10-29):** `provexp.featuresets.ember2024.expert` (`ExpertFeatureExtractor`; `accumulate=False` keeps
their behavior). Checked against their own code (run through LIEF, with assign) on the 45 test files: every feature
equal except where the parsers disagree (pefile fails on one file, misses a resource directory on one and nine imports
on another; LIEF names one ordinal import on two). Three readings fixed by their code rather than the paper:
`nb_imported_functions` and the keyword counts are over LIEF's `imported_functions` (imports by name, repeats included,
ordinals left out); a section's entropy is over its raw data up to the virtual size (LIEF's `content`); and their
`modified_dos_stub` compares a LIEF memoryview with a list, so under current LIEF it is constant 1 (we compare bytes, as
intended; `docs/upstream-issues.md` item 6, with the two quirks). The quirks are witnessed on test files with our own
byte-level edits (a second `.text` section lowers `.text-size`; a second kernel32.dll descriptor sets its count to 1),
and the patched variant never falls under either addition (`tests/test_ember2024_expert.py`). `run/106_expert_set.sh`
(user): featurize the 10% store, train the monotone and an unconstrained model, the toolkit columns. The adaptive
search does not cover this row: the C1 engine reads only the instrumented extractor.

**Decisions as first posed:**
1. Re-implement their 40 features (recommended), or approximate them with the ~5 thrember counterparts?
2. Report the row under M_add (where it is sound once patched), M_full (where it is not), or both? Recommended: both,
   since the A1 rows are M_full and the M_add row shows the set at its best.

Cost: re-implementation and tests ~half a day; featurizing the 10% store with a 40-feature pefile extractor is
probably 10-20 min on 16 workers (a `run/` script for the user; estimate to be smoke-tested); training ~2 min.

## Result (run 106, read 2026-10-30)

As the mock predicted for accuracy. Monotone (all 40 increasing): AUC 0.844, TPR 29.1% at 1% FPR and 14.8% at 0.1%
(the model saturates: validation AUC flat at ~0.855 from round 10, no split with positive gain left). Unconstrained on
the same 40 features: AUC 0.978, 75.1% and 56.1%. For comparison, the derived C4 sums row under M_full: 0.9935, 89.6%,
74.8%.

Toolkit columns (pilot, unrouted): at its own 1% FPR threshold the monotone model detects only 8 of the 50 pilot
malware, and no attack evades it on them (0/8 under M_add, i.e. padding, GAMMA sections, GAMMA API; 0/8 under M_full,
all eight attacks). The unconstrained model detects 40 and is evaded on 24/40 by the M_add attacks (GAMMA API 24, GAMMA
sections 3) and 25/40 by all eight (one format_exploit run). The M_full holes reasoned above (rename, slack, DOS stub)
are not exercised by the toolkit's attacks, and the adaptive search cannot run on this extractor (the C1 engine reads
only the instrumented one), so for now they rest on the reading of the code and the patched-variant witnesses, not on a
measured evasion.

## Instrumented (item 11, 2026-11-03): the engine derives the holes

`ExpertFeatures` is now instrumented into the item layer (`src/provexp/featuresets/ember2024/expert.py`: `items()` and
`readouts`), reusing only `Identity` and `Opaque` -- no change to `items.py`/`reach.py`. **G1 is bit-exact** on the 45
local test files (`evaluate(items, readouts) == feature_vector`, 0 mismatches). The two quirks are modeled as
non-locality: `accumulate=False` makes a watched library's count (and a named section's info/size) depend on the other
descriptors/sections, so the item is `local=False`; the C4 derivation then reads those entries as two-sided. The
instrumentation surfaces the import quirk quantitatively -- on a file with two `kernel32.dll` descriptors the sound sum
is 92 where the assign extractor reports 1 (the last descriptor's count).

**The C4 derivation gives 11 M_full holes, not 12** (corrects the "12 of 40" prose above, which listed only 11 rows).
Deriving M_full directions over the corpus (reusing `catalogue.regions` + `reach.region_changes` for the in-place ops,
`Change` lists for the structural ones) yields exactly rows 27 and 30-39: `modified_dos_stub` lowered by the DOS-stub
overwrite (`dos`), and `unknown_sections`, `info_unknown_sections`, and the eight `.text/.data/.rsrc/.rdata` info/size
features all lowered by **rename** (`ren`). Two corrections the derivation forces:
- **Slack overwrite does not change the `info` features** (contradicts the "slack overwrite changes entropy" claim in
  the rows above). The expert entropy is over the mapped content (`get_data(min(SizeOfRawData, VirtualSize))`), which
  excludes the slack bytes; the info holes come from renaming only, not slack.
- **`no_sig` is up under M_full, not a hole.** Modeled tightly (a marker item present iff the parsed file is unsigned;
  removing the signature *adds* it, and no M_full operation adds a signature), `no_sig` derives as up -- sound and
  tight. Left as a generic structural flag it would read two-sided, the 12th (spurious) hole.

So the go/no-go ("derived holes match the reasoned 12 of 40") passes at **11 of 40** (the reasoned set was 11 rows; the
"12" was a prose miscount). Still to do: a recognizer for the C1 engine, the adaptive cell against the run-106 monotone
model (rename + DOS-stub edits), per-hole witnesses by our own byte edits, and productionizing the derivation.
