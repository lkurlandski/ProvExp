# The extractor audit pass (session 65, 2026-11-14)

The scale-up's first step (PLAN.md, step 2c): one deliberate pass over our extractor
(`src/provexp/featuresets/ember2024/features.py`: thrember's lines, our instrumentation and patches), group by group,
against the three principles of `docs/evidence/r7-overlay-rule.md` §6:

1. **Structures are located as the loader locates them.**
2. **Features describe the file, not the parser's diagnostics.**
3. **Known aggregation bugs are fixed.**

The goal is a deviations table for Appendix D. Each deviation from EMBER v3 as released is justified by one of the
principles, and the parser heuristics we leave alone are listed too. Then a reviewer asking "did you design the
features to suit your guarantees?" finds every difference stated once, with its reason.

**How it was done.** I read thrember's whole `features.py` (`tests/reference/thrember_features.py`) and checked each
pefile rule the features depend on in pefile's source (2024.8.26). Each candidate was then counted on the 2,000 test
files (`artifacts/explanation_set/ts.parquet`, which include the 100 pilot files). The counts come from
`pipeline/1-audit/deviations/` (module `provexp.featuresets.ember2024.deviations`), split by whether the file is in the
population (run 136's `in_population`; 1,674 of the 2,000). Output:
`artifacts/experiments/deviations/2000/` (`files.parquet`, `report.json`, and `imports_pefile_vs_lief.txt` for 2.4;
about 3 minutes to re-create; `pipeline/1-audit/deviations/run.sh` runs it at scale).
Hypothesis beforehand: each candidate fires on at most a few percent of files, mostly incomplete ones. That held for
everything except the alignment bits and the registry typo (both ~3-5%, mostly in the population) and the import
merge, which is already a deviation.

## 1. The deviations we already have (no decision needed; for the table)

| Deviation | Principle | Files (in population / outside) | Source |
|---|---|---|---|
| The overlay starts after the furthest section's raw data (LIEF's rule), not after the furthest data-directory extent | 1 | 0 / 270 | `r7-overlay-rule.md`; `upstream-issues.md` 9 |
| pefile's 88 warning flags dropped | 2 | every file | §4 prose; run 126 |
| A crash in one directory's parser loses only that directory (else thrember makes the file a non-PE) | 2 | 0 / 0 here; 394 of 2,879,653 in the corpus | `upstream-issues.md` 5 |
| A DLL with several import descriptors: their functions merged, not overwritten | 3 | 61 / 16 | `upstream-issues.md` 1 |
| Files of 4,000,000 bytes or more excluded (sample selection, listed apart) | — | 330 of the 2,000 are truncated | decision 8 (iv) |

## 2. New candidates, each for the user to decide

Each entry gives what happens, a concrete file, the counts, how EMBER v2 handled it where I know, what a change would
change, and my recommendation.

### 2.1 Data directories: thrember drops the last directory it reads, not the reserved one (principle 3) — **recommend: fix**

thrember's `DataDirectories.process_raw_features` loops `for i in range(1, len(raw_obj) - 1)`, meant to skip the
16th, always-empty `RESERVED` entry. But it skips whichever entry comes last. When a file declares fewer than 16
directories (`NumberOfRvaAndSizes`), the entry dropped is a real one.
- Example: `033056f8...` (a .NET program in the population) declares 15 directories, so its COM descriptor, the CLR
  header that marks a .NET program, is dropped: `datadirectories:com_descriptor_size` and `_virtual_address` read 0.
  Two files with 3 directories lose their resource directory.
- Counts: 13 files with fewer than 16 directories, all with a non-empty dropped entry: **11 in the population**, 2
  outside. 11 of the 13 are .NET files that lose the COM descriptor.
- EMBER v2 (from memory of `elastic/ember`'s `features.py`; to verify before citing) filled its 15 named slots by
  position and did not drop a real entry. The off-by-one came with the v3 port, like the import overwrite.
- A fix: skip the entry named `RESERVED` instead of the last one, a pure addition in the style of
  `ImportsInfoMerged`. It changes two features on ~0.6% of files. Nothing in the guarantees depends on it. The item
  layer already records each directory entry as a field, so instrumenting the fix is small.
- Why fix rather than note it: it is the same kind of bug as the import overwrite, which we already fix under
  principle 3, and it loses a structure the file plainly has.

### 2.2 The entry section on files whose sections are not aligned (principle 1) — **recommend: keep thrember's rule, note it**

thrember takes the entry section to be the last section for which pefile's `contains_rva(entry point)` is true, and
if there is none, the first executable section. pefile's `contains_rva` first rounds the section's address down to
`SectionAlignment`. On files whose sections start at addresses that are not multiples of the alignment, this finds
no section, and the fallback picks another one.
- Example: `ba37125a...` (in the population). Its entry point 0x16400 is the start of a 6-byte section `Entry1` at VA
  0x16400, with SectionAlignment 0x1000. pefile finds no section, so thrember picks `UPX0`, the first executable one.
  Taking the section's own extent [VA, VA + VirtualSize) gives `Entry1`, as LIEF's `section_from_rva` would (and
  hence presumably EMBER v2). `8ea41a92...` (`CodeSec` vs `DataSec`) and `9b951384...` (`.text` vs `NewSect`) have
  the same shape: a tiny section injected at a 0x200-aligned address.
- Counts: **3 in the population**, 0 outside. pefile's other quirk here, which depends on the file's length (a
  section whose raw data runs past the end is measured by its virtual size instead), affects 0 files in the population
  and 2 outside.
- What the loader does: I believe the Windows loader rejects images whose section addresses are not aligned to
  SectionAlignment when the alignment is at least a page, but I have not verified it, and we never run files. If it
  does, these 3 files are not runnable and the question does not arise for an attacker.
- Options: (a) keep thrember's rule and list it as a parser rule left as it is (recommended: 3 files, no clean loader
  answer to adopt); (b) take the section's own virtual extent (LIEF's view; changes the 10 entry-name features on
  those files); (c) add "section addresses aligned" to the population's plain-layout clauses (moves 3 files out).
- Note: Table 3's entry-section row (an added section becoming the entry section through the fallback) does not depend
  on this. It is the fallback rule, which all options keep.

### 2.3 Section alignment bits decoded as several flags (principle 2) — **recommend: keep**

pefile turns a section's `Characteristics` into named flags by testing each flag's value against the field
(`value & field`). The alignment field (bits 20-23) is a number, not a set of flags, so one alignment value turns on
several `IMAGE_SCN_ALIGN_*` names. thrember hashes every name into `section:characteristics_hash_*`.
- Counts: **45 in the population**, 14 outside (3%), mostly files whose sections carry an object-file alignment value.
- Why keep: the decoding is a fixed function of one field of the file, so the feature still describes the file
  (redundantly), and the item layer already locates it in that field. Changing it would move v3's features on 3% of
  files and buy nothing for the guarantees.

### 2.4 pefile's early stops in imports and exports (principle 2) — **recommend: list with the parser caps, no change**

Besides its caps (8,192 imports; `docs/upstream-issues.md` 10), pefile gives up on import and export tables it judges
corrupt. It stops reading export names at the first name with a character outside printable ASCII. It drops a DLL's
table on repeated or far-spread thunks. It stops reading descriptors after five errors. And it reads a DLL name
outside its character set as `*invalid*`.
- Counts: export names lost on **4 files in the population**, 6 outside; the import cap 1 / 1; an `*invalid*` DLL
  name 2 / 0. On the 22 files in the population with a damaged-import warning, pefile's import list matched LIEF's on
  17. 2 differed by the same number of entries both ways (2 and 12; probably how ordinal imports are named, not
  checked), 1 is the cap (`85a9da0f...`: 280 of 14,707 imports read), and on 1
  (`f3ea1e67...`) pefile stopped after repeated errors and read 1,143 of LIEF's 1,738.
- Why no change: like the caps, these are exactness gaps on rare, odd files, not soundness holes in what the
  derivation assumes (pefile's choice is a fixed function of the bytes, which the locating ranges cover; the item layer
  already marks exports as not local). Replacing them means re-implementing pefile's import and export parsing, which
  session 62 decided against.

### 2.5 Typos in thrember's string patterns (not a principle; feature definitions) — **recommend: keep as v3, report upstream**

- `email_addr` uses the same pattern as `mac_addr`, so the two features are always equal.
- `registry_key` searches for `KHEY_|KHLM|HKCU`, a misspelling of `HKEY_|HKLM`. Of the 2,000 files, 93 contain
  `HKEY_` or `HKLM` (79 in the population). v2's registry feature counted `HKEY_` correctly.
- `.click(` is the pattern `.click` (the dot matches any character), and the key `onlick` is misspelt (its pattern,
  `onclick`, is right).
- Why keep: these are v3's definitions of what a feature counts, not the parser's view of the file or an aggregation
  bug. Fixing them would be redesigning EMBER's features. They do not touch any guarantee: the string items are the
  same either way.
- Alternative: fix `registry_key` alone, since v2 had it right. It changes one feature on ~5% of files.

### 2.6 Smaller items — **recommend: keep, mention only if the table has room**

- `authenticode:signing_time_diff` is taken from the last countersigned signature, not the latest one;
  `self_signed` skips the last certificate of each chain. Both are thrember's definitions.
- pefile stops reading the section table at an all-zero header: 0 / 2 files.
- The constant features already noted (`docs/upstream-issues.md` 2-3): `min_entropy`, `min_size_ratio`,
  `min_vsize_ratio` (always 0), `num_exports` (always 0 or 128), the reserved directory's two features (always 0;
  still 0 after the fix of 2.1). Kept, constant.

## 3. The proposed deviations table (for Appendix D, after the user decides 2.1-2.5)

One table, two parts. Counts at the scale-up from `1-audit/deviations` (the numbers below are the 2,000 test files').
It assumes the recommendations above; it changes if the user decides otherwise.

| | Change from EMBER v3 | Why (principle) | Files |
|---|---|---|---|
| *Changed* | The overlay starts after the last section's raw data | 1: the loader maps only sections; a directory entry it ignores must not move the overlay | 270, none in the population |
| | Parser warnings dropped | 2: they report the parser's diagnostics, and no bytes are recorded for them | all |
| | A crashing directory parser loses only its directory | 2: a parser bug must not turn a file into a non-PE | 394 of 2.9 M |
| | Repeated import descriptors merged | 3: EMBER v2 merged them; v3 lets the last overwrite the rest | 77 (61) |
| | Data directories: the reserved entry skipped, not the last one read | 3: v3 drops a real directory when fewer than 16 are declared | 13 (11) |
| *Kept* | pefile's caps and early stops (imports, exports) | exactness gaps on rare files, not soundness holes | ~12 |
| | The entry section's rule on misaligned sections | no clean loader rule to adopt; 3 files | 3 (3) |
| | Alignment bits read as flags; constant features; string-pattern typos | v3's definitions; a fixed function of the file | — |
| *Selection* | Files of 4 MB or more excluded | our copy of EMBER2024 holds only their first 4 MB | — |

Prose around it: one paragraph, saying that our extractor is EMBER v3's with the changes listed, each made for one of
three reasons, and that the unconstrained detector's accuracy matches v3's (the scale-up's number).

## 4. What a "fix" of 2.1 (or 2.2 (b), 2.5) costs

Any change to `features.py` changes the feature store, so it has to land before the scale-up's featurization. It
means: a pure addition (a subclass and an installer like `merge_import_descriptors`), the instrumentation mirrored,
`tests/` extended, `pipeline/setup/reference/` regenerated, and the identity check's comparison with run 146's
outputs then expected to differ in exactly the changed features. The stale `scripts/item_checks.py` comment in
`features.py` can be fixed in the same change, since the file's hash changes anyway.

## 5. Also found and fixed in this session

`escape_audit.py` aborted on pilot file `0485edc2...`. pefile's `PE.write()` repacks every parsed structure and
rewrote ~40 bytes no write had touched, which the audit's one-field check rejects (4458d06). The writes now patch
their field directly. On run 137's 150 files all 900 writes are byte-identical to `pe.write()`'s, so run 137's
result stands. (Rerunning run 137 today differs in the `overlay_entry` write, from LIEF's overlay rule adopted after
it, not from this fix.)
