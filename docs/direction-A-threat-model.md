# Direction A: the threat model and feature directions (2026-10-22)

Step 1 and 2 of `PLAN.md`'s revised next steps. The threat model fixes what the attacker may do to a malware file;
the direction table says, for every EMBER v3 feature, which way those edits can move it. Every row of Table A1
(`docs/direction-A-mock.md`) names the threat model it assumes.

## 1. The threat model

**In plain terms.** The attacker keeps the malware working and edits its file with the transformations the attack
toolkits use (the coverage table, `docs/feature-provenance-model.md`, Section 6). They choose all content (bytes,
section names and properties, imported names) freely, within a byte budget. Three nested threat models, from the
additions monotone defenses are designed for to everything the toolkits do except rewriting the file:

| Operation (Section 6 row) | Short | M_add | M_shift | M_full | Toolkits |
|---|---|---|---|---|---|
| append bytes at the end (1) | app | x | x | x | secml padding, GAMMA padding; OA; t0 |
| add a section, any name, properties, content (11) | sec | x | x | x | GAMMA sections; SA; t3 |
| add imports, any library and function names (12) | imp | x | x | x | GAMMA API; t1 |
| extend the DOS header: insert a gap before the PE header (13) | ext | | x | x | secml extend, format exploit |
| shift section content: insert a gap before the first section (14) | shf | | x | x | secml shift, GAMMA shift |
| overwrite section slack (2) | slk | | | x | secml slack, Kreuk, Suciu; SP, CP1; t4 |
| overwrite the DOS header and stub, bytes 2-59 and 64 to e_lfanew (3, 4) | dos | | | x | secml partial / full DOS |
| overwrite loader-ignored header fields (5) | hdr | | | x | secml header fields (Nisi et al.) |
| overwrite the checksum (6) | chk | | | x | BC; t9 |
| rename a section, any 8-byte name (7) | ren | | | x | SR, SR1; t2 |
| remove debug: zero the DEBUG directory entry (9) | rdb | | | x | RD; t6 |
| remove the signature: zero the SECURITY entry (10) | rsg | | | x | RC; t5 |

Every operation is applied with its declared side effects (an added section raises NumberOfSections and SizeOfImage
and writes a section-table entry into the header; an insertion raises the pointers it moves; adding imports moves the
import directory into a new section). **Outside all three:** code randomization (MAB-Malware's CR: in-place rewriting
of code; it would make every byte of the code section attacker-writable) and UPX packing/unpacking (a whole-file
rewrite). Attacks that use them are reported against the threat model, not counted as failures of it.

Gimenez et al.'s 8 secml-malware attacks fall inside M_full (padding, DOS header, header fields, extend/shift, GAMMA).
MAB-Malware and Labaca-Castro et al. are inside M_full except CR and UPX.

## 2. Directions (C4, global: over all files)

For each feature and each operation, the set of signs the operation can give the feature's change on some file; a
threat model's direction is the union over its operations: **fixed** (no operation moves it), **up**, **down**, or
**both**. A monotone detector can use fixed and up features as they are, down features negated, and must drop both.
`pefilewarnings` is outside the model (no items) and is counted as both.

**Provisional (a stand-in for the automatic derivation).** The per-group rules below were derived by hand from the
extractor's code and the declared deltas, and are encoded in `scripts/a_directions.py`; the paper's version must come
from the instrumented extractor (C4 over the item table). This table is for screening (go/no-go checks 2 and 3).

Global soundness is strict: a feature counts as one-directional only if no file and no choice of content can move it
the other way. Where the exception is a rare file layout (header slack that is not zero-filled), the table still says
both, and the note says so.

### Re-encodings (layer-2 sums instead of features)

Most features are two-sided because of the readout, not the items. Four re-encodings make them one-directional, each
derived from the model:
1. **Raw counts instead of normalized frequencies** (byte histogram, printable characters): removes the division by a
   total. From the feature store (frequency x total), but up-only only under pure appends, since the other operations
   write a few header bytes in place.
2. **Counts over section bodies and the overlay only** (excluding the header region and section slack, the only
   places M writes in place; strings broken at region boundaries; byte-entropy windows tiled per region). Up-only
   under all three threat models. Needs re-extraction: the regions come from the parse (layer 1).
3. **Signed buckets split into their positive and negative parts** (section hashes keyed by name): each part only
   grows when sections are added. Up-only under M_add and M_shift; renaming (M_full) moves a section's contributions
   between buckets, so both. Needs re-extraction.
4. **The duplicate-library quirk fixed** (imports accumulated per library instead of overwritten): up-only. Needs
   re-extraction.

## 3. Results (run 76, `artifacts/experiments/a_directions/`)

Usable by a sound monotone detector = fixed + up (+ down, negated). Of 2,568 features:

| | M_add | M_shift | M_full |
|---|---|---|---|
| features as they are | 557 (22%) | 557 (22%) | 483 (19%) |
| re-encoded as layer-2 sums | 2,465 (96%) | 2,465 (96%) | 2,191 (85%) |

Per group (fixed / up / down / both):

| Group (size) | M_add, features | M_add, re-encoded | M_full, features | M_full, re-encoded |
|---|---|---|---|---|
| general (7) | 5 / 1 / 0 / 1 | same | 3 / 1 / 0 / 3 | same |
| histogram (256) | 0 / 0 / 0 / 256 | 0 / 256 / 0 / 0 | 0 / 0 / 0 / 256 | 0 / 256 / 0 / 0 |
| byteentropy (256) | 0 / 0 / 0 / 256 | 0 / 256 / 0 / 0 | 0 / 0 / 0 / 256 | 0 / 256 / 0 / 0 |
| strings (177) | 0 / 0 / 0 / 177 | 0 / 171 / 0 / 6 | 0 / 0 / 0 / 177 | 0 / 171 / 0 / 6 |
| header (74) | 69 / 5 / 0 / 0 | same | 42 / 7 / 0 / 25 | same |
| section (224) | 13 / 7 / 0 / 204 | 13 / 207 / 0 / 4 | 3 / 6 / 0 / 215 | same |
| imports (1,282) | 0 / 257 / 0 / 1,025 | 0 / 1,282 / 0 / 0 | 0 / 257 / 0 / 1,025 | 0 / 1,282 / 0 / 0 |
| exports (129) | 129 / 0 / 0 / 0 | same | same | same |
| datadirectories (34) | 30 / 0 / 0 / 4 | same | 26 / 0 / 2 / 6 | same |
| richheader (33) | 33 / 0 / 0 / 0 | same | 0 / 0 / 0 / 33 | same |
| authenticode (8) | 8 / 0 / 0 / 0 | same | 0 / 0 / 7 / 1 | same |
| pefilewarnings (88) | 0 / 0 / 0 / 88 | same | same | same |

What this says:
- **Hypothesis held.** As they are, four fifths of the features are two-sided, almost all because of the readout
  (normalized histograms, string distributions, ratios, entropies) or signed hashing, not because the attacker can
  remove items. Read as layer-2 sums, 96% are one-directional under M_add and 85% under M_full. Under M_full the
  re-encodings cannot help the features the attacker overwrites outright (loader-ignored header fields, DOS fields,
  the Rich header) or renames (section buckets keyed by name).
- **The duplicate-library quirk alone makes 1,025 import features two-sided** (num_imports and all 1,024 function
  buckets). `ImportsInfo.raw_features` sets `imports[dll_name] = []` for each import descriptor, so a second
  descriptor for an already imported DLL (same spelling) erases the first one's functions from the features; the
  library buckets are unaffected (a set). Adding a descriptor such as `KERNEL32.dll: Sleep` would hide every earlier
  KERNEL32 import from the import hashes. This is an A2 failure the model flags, and a candidate for check 2's hole:
  no secml-malware attack produces it (GAMMA's import attack reuses the existing descriptor), so PV selection would
  keep all 1,024 buckets as up-only. **Verified on a test file** (LIEF 1.0, one extra `KERNEL32.dll: Sleep`
  descriptor): pefile reports both descriptors; num_imports falls from 116 to 3 and 109 function buckets decrease.
  **Handling (user, 2026-10-22: do not let results depend on implementation quirks):** the sound table must record
  it (that is what soundness means for this extractor), but no A1 result may rest on it: check 2's hole and the A1
  comparison are measured on the quirk-fixed variant (all rows, baselines included), and the quirk is at most a side
  remark about what automatic analysis finds. Check 3 trains both variants to show the sensitivity.
- **Three features are constant**: `min_entropy`, `min_size_ratio`, `min_vsize_ratio` are always 0, since the
  extractor appends 0 to each list before taking the minimum.
- **Strictness costs some features.** Byte, string and section counts are two-sided under M_add only because adding a
  section writes its table entry over the header slack in place; on files whose slack is zero-filled (most) they would
  be up-only. The re-encodings avoid the question by not counting the header region.

Consequences for the next checks:
- **Check 3 (accuracy cost)** can be run from the feature store only for the "features as they are" row (557
  features under M_add). Every re-encoding needs re-extraction: region-restricted counts and windows need the parse
  (layer 1), split buckets and the quirk fix need the raw section and import lists. That is a featurization job over
  the training set, to be scoped with the user.
- **Check 2 (PV's hole)**: the prime suspects are now concrete: the 1,025 import features (the quirk), the signed
  section buckets PV's random names never decreased, and the strings regexes ending in a word boundary.
