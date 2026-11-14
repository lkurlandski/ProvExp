# Upstream issues to report (for the user)

To submit by hand on GitHub; drafted 2026-10-22. Repository: https://github.com/FutureComputing4AI/EMBER2024
(thrember, EMBER feature version 3). Check the current `features.py` in its `src/` directory first: the lines below
are from the copy in `tests/reference/thrember_features.py`.

## 1. Imports: a repeated DLL overwrites the earlier descriptor's functions (TODO: issue + pull request)

**Issue title:** `ImportsInfo.raw_features` drops imports when a DLL has more than one import descriptor

**Issue text (draft):**

> `ImportsInfo.raw_features` sets `imports[dll_name] = []` for every import descriptor. When a PE file has two
> descriptors for the same DLL name (allowed by the format, and produced by some linkers and packers), the second one
> replaces the functions of the first, so they are missing from `num_imports` and the function hashes. For example,
> adding one descriptor `KERNEL32.dll: Sleep` to a file that already imports 114 functions from `KERNEL32.dll` lowers
> `num_imports` from 116 to 3.
>
> The original EMBER (`elastic/ember`, `ImportsInfo.raw_features`) handled this explicitly:
> `if lib.name not in imports: imports[lib.name] = []  # libraries can be duplicated in listing, extend instead of overwrite`.
> The pefile re-implementation seems to have lost the check. Besides losing information, it lets an attacker hide
> imports from a model by adding one small descriptor.

**Pull request (one line, mirrors EMBER v2):**

```diff
         for entry in pe.DIRECTORY_ENTRY_IMPORT:
             dll_name = entry.dll.decode()
-            imports[dll_name] = []
+            if dll_name not in imports:
+                imports[dll_name] = []  # a DLL can have several descriptors: extend instead of overwrite
```

Mention in the PR that feature vectors already released for EMBER2024 were computed with the old behavior, so the
change affects only files with repeated descriptors (rare) and may warrant a feature-version note.

Our copy: fixed as a pure addition, `ImportsInfoMerged` and `merge_import_descriptors` in
`src/provexp/featuresets/ember2024/features.py` (tests in `tests/test_ember2024.py`, `TestImportsInfoMerged`).

## 2. Optional: three section features are constant (check before filing)

`SectionInfo.process_raw_features` appends `0` to the lists of entropies, size ratios and vsize ratios before taking
the minimum, so `min_entropy`, `min_size_ratio`, `min_vsize_ratio` are always 0 (entropies and ratios are
nonnegative). Probably intended as a default for files without sections; `min(...) if sections else 0` would keep that
and make the features informative. Lower priority than 1; confirm on the released vectors (the column should be all
zeros) before filing.

## 3. Optional: other constant features (from `docs/design.md`, Section 5.2)

`exports:num_exports` is `len(exports_hashed)`, so always 128 (or 0 without exports); `datadirectories` skips the last
directory, so `reserved_size` and `reserved_virtual_address` are always 0. Could go into the same issue as 2.

## 4. secml-malware: the shift attacks destroy files whose first section has raw offset 0 (found 2026-10-26)

Repository: https://github.com/pralab/secml_malware (vendored, patched copy in `third_party/secml_malware/`).
`shift_section_by` / `shift_section_by_using_lief` (`secml_malware/utils/pe_operations.py`) insert the gap at
`liefpe.sections[0].offset`. On files whose first section has `PointerToRawData = 0` (a VMProtect-style layout with
an uninitialized `.text`; 2 of our 50 pilot malware, e.g. `48d9cc0c...`), that is offset 0: the gap goes in front of
the MZ header and the result no longer parses as a PE. The GAMMA shift and content-shift attacks then report an
"evasion" that is a broken file. A fix would insert at the smallest nonzero raw offset of a section with
`SizeOfRawData > 0` (or at `SizeOfHeaders`). Our harness (`scripts/a1_evaluate.py`) now counts such outputs as invalid,
not evaded.

## 5. pefile: a malformed debug directory crashes the parse, and thrember then treats the file as not a PE (found 2026-10-27)

Repository: https://github.com/erocarrera/pefile (version 2024.8.26). In `PE.parse_debug_directory`, a debug entry of
type 20 (`IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS`) whose data lies outside the file makes `__unpack_data__` return
`None`, and the next line reads `dbg_type.ExDllCharacteristics`: an `AttributeError`, not a `PEFormatError`, so it
escapes `parse_data_directories`. thrember's `PEFeatureExtractor.raw_features` catches `AttributeError` and sets
`pe = None`, so the file gets `is_pe = 0` and every header, section, import, export, directory, Rich, and signature
feature becomes zero. Found by check G5 (`scripts/item_checks.py locating`, run 91): on pilot file `cf877553...`,
flipping one byte of the debug directory's `Size` (offset 477, XOR 0xFF) makes pefile read garbage entries and crash.
A fix: `if dbg_type is not None:` before `set_flags` (the other debug types already guard against `None`). An
attacker-chosen edit can trigger it: appending bytes to a file whose debug directory lies past its end (3 of the 100
pilot files, mostly files cut at the dataset's 4 MB cap) makes the appended bytes the debug entries, so a type-20 entry
pointing outside the file zeroes every PE feature. **Patched here (2026-10-27, user)**, together with a second bug of the same kind (`parse_dynamic_relocations` reads
`.Version` from a dynamic relocation table header it could not read, `pefile.py:4102`), by one general rule rather than
per-bug fixes: a directory parser that raises anything other than `PEFormatError` loses only its own directory, with a
warning (`features.py`, "Correctness: a crash in one directory's parser loses only that directory"; installed in pefile
at import; `tests/test_ember2024.py::TestDirectoryGuard`). Of the 1,235 files the store held as not a PE, 394 (of
2,879,653) were such crashes, almost all benign files truncated at 4 MB: 76 debug, 304 dynamic relocations, 14 in two
rarer paths (`contains_rva`, `get_data`); all parse with the guard (run 94 rewrites their rows). Also
worth reporting to thrember: `raw_features` catches `AttributeError` around `pefile.PE(...)`, so any pefile bug of
this kind silently turns a file into a non-PE.

## 6. Gimenez et al.'s expert features: two assign-instead-of-accumulate quirks and a constant DOS-stub flag (found 2026-10-29)

In `static_features_extraction.py:get_features` (github.com/PFGimenez/certifiably-robust-malware-detectors-by-design),
the per-library function counts are *assigned* per import descriptor (`features[lib.name.lower()] = len(lib.entries)`),
so a second descriptor for a watched library (an edit in their own threat model: adding imports) replaces that
library's count, e.g. kernel32.dll from 120 down to 1; likewise a second section named `.text`, `.data`, `.rsrc`, or
`.rdata` replaces that name's size and entropy x size with its own. Both lower features their monotone models constrain
to increase, so the certified robustness does not hold against these additions. A fix: accumulate (`+=`) in both
places. Separately, `binary.dos_stub == default_dos_stub` compares a list with what current LIEF returns, a
memoryview, so the comparison is always unequal and `modified_dos_stub` is constant 1 (`bytes(binary.dos_stub) ==
bytes(default_dos_stub)` fixes it; which LIEF version they used is not stated). **Patched here** by accumulating
(`provexp.featuresets.ember2024.expert`, `accumulate=True`; the quirks are witnessed in
`tests/test_ember2024_expert.py::TestQuirks`).

## 7. secml-malware (design note, optional): GAMMA section injection adds every donor section in every candidate (found 2026-11-04)

`CGammaSectionsEvasionProblem.apply_feasible_manipulations` (`secml_malware/attack/blackbox/c_gamma_sections_evasion.py`)
loops over all k donor sections and calls `add_section` for each, with `content[:int(t[i] * len(content))]`, even when
that slice is empty. A weight of 0 therefore does not mean "do not inject": every candidate gains exactly k sections
(30 or 75), the near-zero ones empty and randomly named, and the optimizer can never try "inject one section" or
"inject nothing". Against our EMBER 2024 GBDT the empty sections alone raise the score (0.98 -> 0.998 on a pilot file;
`section:num_zero_size` and the section count jump), which is why the attack evades nothing at any budget. maltorch's
`GAMMASectionInjectionManipulation` does the same, and the GAMMA paper describes the attack space as parametric in k,
so this is a design choice rather than a bug; a suggestion upstream: skip donors whose slice is empty (or below a
minimum), so the attack can choose how many sections to add. Not patched here: the toolkit is used as published.

## 8. Gimenez et al.'s ERDALT code: the output layer is not constrained, so the network is not monotone (found 2026-11-04)

Repository: https://github.com/PFGimenez/certifiably-robust-malware-detectors-by-design, `train_model.py`. The paper's
Proposition 3 needs the layers above the linear post-processing to be monotone. `monotonic()` projects the negative
weights of `layer2` and `layer3` to small positive values (`exp(w - 5)`), with ELU activations, but leaves `fc4` (the
output layer) unconstrained, so a negative output weight makes the score decrease in some post-processed feature. Our
port (`src/provexp/models/erdalt.py`) follows the paper and applies the same projection to the output layer. A note
to the authors, not a bug report against their results: their robustness numbers are empirical either way.

Other differences between their code and our port, none of which the paper specifies (checked 2026-11-12): their
code selects the epoch on the test split (ours: validation); batches of 16 (ours: 256, for compute); the l2 term
samples up to 152 batches of 16 perturbation vectors per step (ours: all of them); the saved epoch is the last one
whose test ROC-AUC beats the minimum of recent saves with < 5 violations (ours: the best validation ROC-AUC among
epochs with < 5 violations). The < 5 rule itself (theirs, kept) tolerates a few negative entries of L(delta), which
Proposition 3 assumes away; our selected epoch has 2 among 3,183 vectors. Standardization matches (inputs centered and
scaled; perturbation vectors scaled only).


## 9. pefile (design note, optional): data-directory entries the loader ignores decide where the overlay starts (found 2026-11-13)

`PE.get_overlay_data_start_offset` (pefile 2024.8.26; the same rule since at least 2016.3.28, the certificate entry
skipped since 2017.11.5) starts the overlay after the furthest extent, within the file, of the optional header, the
sections, and every data directory except the certificate's. The loader maps only the sections and does not read some of
those entries (debug, the reserved architecture entry), so an 8-byte write to such an entry, which the program never
notices, moves where the overlay starts: pointing the debug extent to one byte before the end of the file leaves a
one-byte overlay. thrember's overlay features (`section:overlay_*`, the `max_*` pools) inherit the rule. LIEF starts the
overlay where the furthest section's raw data ends (none if that lies at or past the end of the file) and ignores the
directories; on 54 pilot files with the debug extent pointed into the overlay, pefile's start moved on all 54 and
LIEF's on none. This is a deliberate design, not a bug: PR #670 (merged 2026-11-13) says "Directory data appended past
the section data is deliberately not treated as overlay". A note for thrember rather than pefile: an overlay feature
meant as "bytes the loader does not map" is better served by the sections-only rule.

Our copy: LIEF's rule installed in pefile at import (`features.overlay_data_start_offset`, the original kept as
`PEFILE_OVERLAY_START`; tests in `tests/test_ember2024.py`, `TestOverlayRule`). On the files of the population the two
rules agree; they differ on 67 of the 1,670 test files below 4 MB and ~3.7% of training files, mostly incomplete
ones. Record: `docs/evidence/r7-overlay-rule.md`.

## 10. pefile: defensive parser caps are not modeled by our instance (design note, found 2026-11-14)

pefile caps the structures it parses: `MAX_IMPORT_SYMBOLS` 0x2000 (8,192, shared across import descriptors),
`MAX_SECTIONS` 0x800, `MAX_SYMBOL_EXPORT_COUNT` 0x2000, `MAX_RESOURCE_ENTRIES` 0x8000, `MAX_STRING_LENGTH` 0x100000.
Our `imp`/`sec` operations declare a change (new import/section items) that an addition crossing a cap does not fully
realize, because pefile stops parsing at the cap. This is an exactness gap for the declared delta, not a soundness hole:
our additions append after the existing parsed content, so a monotone-up feature (e.g. `num_imports`) still rises and
never falls (verified session 62, `docs/evidence/r7-overlay-rule.md` §10; 0 model-read features fell over three pilot
files pushed past the 8,192-import cap). Not a bug in pefile (the caps guard against malformed files); listed so the
extractor audit records it as a deviation. A deliberate extractor could model the cap in the signature (declare the
rise as "to at most the cap").
