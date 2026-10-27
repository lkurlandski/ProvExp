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
