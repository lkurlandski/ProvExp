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

**Decisions for the user:**
1. Re-implement their 40 features (recommended), or approximate them with the ~5 thrember counterparts?
2. Report the row under M_add (where it is sound once patched), M_full (where it is not), or both? Recommended: both,
   since the A1 rows are M_full and the M_add row shows the set at its best.

Cost: re-implementation and tests ~half a day; featurizing the 10% store with a 40-feature pefile extractor is
probably 10-20 min on 16 workers (a `run/` script for the user; estimate to be smoke-tested); training ~2 min.
