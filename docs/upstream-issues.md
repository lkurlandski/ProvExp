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
