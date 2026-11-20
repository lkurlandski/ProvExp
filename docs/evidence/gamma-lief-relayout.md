# GAMMA through LIEF: the guaranteed detectors' toolkit evasions, the validity rule's count gap, header room

Session 101 (2026-11-20, tigris interactive node). Scripts and outputs: `artifacts/scaleup/diag/` (`gamma_evasion.py`,
`gamma_evasion_why.py`, `gamma_evasion_split.py`, `gamma_evasion_ws2.py`, `validity_sets.py`, `validity_sets_read.py`,
`header_room.py`, `header_room_grown.py`; outputs in `gamma-evasion/`, `validity-sets/`). Every toolkit output is
reproducible exactly from `file_seed(0, attack, name)`, donor set 1 and the detector's model (p_clean, p_adv and bytes
added matched the records on all 4 + 480 re-created runs).

## 1. The four evasions of the guaranteed detectors: outside the threat model through LIEF's rebuild

Each feature change of an output is either allowed by the detector's derived table (an up feature that rose) or against
it (an up feature that fell, or a fixed feature that moved; fixed features stay free in the model,
`3-directions/derived/directions.py`). Scoring the clean vector with only one group of changes applied:

| case | allowed only | against only | what moved against the table |
|---|---|---|---|
| `714d2a7d` gamma_sections, monotone-features | 0.991 | 0.208 | LIEF relocated `.rsrc` to the end: resource directory RVA 110,592 -> 577,536, size 5,054 -> 8,192 |
| `714d2a7d` gamma_sections, monotone-sums | 0.993 | 0.243 | the same |
| `34089080` gamma_api, monotone-features | 0.964 | 0.723 | LIEF's import rebuild destroyed WS2_32.dll's 10 ordinal imports (pefile no longer lists it, LIEF reads 3 garbled entries): `imports:library_hash_51` 1 -> 0 |
| `eb61a5bd` gamma_api (fails the precondition) | 0.993 | 0.479 | TLS, base relocation, load config and resource directories rewritten; LIEF's rebuild alone (no edit) scores 0.608 < tau |

The declared edits only raise the score: no soundness failure. `lief_preserves` passed `714d2a7d` (it checks section
bodies, names and the DOS stub, not data directories). Our byte-level writers could not write the declared edit on
`714d2a7d` (30 sections, no room for the headers) nor on `eb61a5bd`; on `34089080` they could (p 0.992, detected).

## 2. The validity rule compares counts

`provexp.attacks.validity.output_invalid` compares the numbers of sections, DLLs and functions, so an attack that adds
DLLs or sections hides a loss (`34089080`: 16 DLLs added, WS2_32 lost, counted valid). Measured on 480 re-created
toolkit outputs (main/unconstrained; a seeded random sample: 150 each of gamma_api and gamma_sections, 30 of each other
attack), comparing sets (sections by name as a multiset, DLLs by lowercase name, functions by (DLL, name or ordinal)),
per parser:

| attack | n | missed losses | among recorded evasions |
|---|---|---|---|
| gamma_api | 150 | 2 (both imports) | 2 of 96 |
| gamma_sections | 150 | 1 (a section name, pefile) | none evaded |
| the other six | 30 each | 0 | 0 (1 evaded) |

The other six attacks add no DLLs or sections, so a loss lowers a count and the rule already catches it. The adaptive
search writes every edit with our writers (no LIEF). MAB-Malware's own pefile-based writers are not measured.

LIEF's relayout in the same sample (data directories other than SECURITY whose (RVA, size) changed): gamma_sections moves
RESOURCE in 88/150, DEBUG 12, LOAD_CONFIG 7, BASERELOC 2; gamma_api moves IMPORT in 150/150 (declared), RESOURCE 92,
DEBUG 7, LOAD_CONFIG 5, TLS 1, BASERELOC 1. `lief_preserves` fails on 111 and 118 of the 150.

**Reading (Claude, session 101):** the current round's validity holds to ~1-2% on the GAMMA rows and exactly elsewhere;
its numbers can go into the manuscript. They are numbers of a LIEF-written GAMMA: most outputs relay out content the
declared edit does not touch, which counts against the guaranteed detectors only as the four evasions above (outside
the threat model) and will shift the other detectors' numbers in an unknown direction once GAMMA is written by our
writers.

## 3. Header room for our writers

`catalogue.new_section_slot` adds a section header only where the headers already have free room. Test malware
(1,000): free slots 0 in 283, >= 1 in 717, >= 30 (GAMMA's section count) in 97, median 6. Growing the headers up to the
first section's RVA (the loader's limit; SectionAlignment >= page): >= 30 slots in 992, 0 in 5, low-alignment 3, median 86.

## 4. Decided (user, session 101)

- **GAMMA is written by our byte-level writers** (the attack is independent of the parsing library; fidelity to Gimenez
  et al.'s LIEF rebuild is low priority; reruns are acceptable while prototyping). Plan:
  1. a header-growth variant of `shf` (the gap before the first section's data, also raising `SizeOfHeaders`, up to the
     first section's RVA): declared changes in the catalogue, its exact single-edit predictor and tests, a hand rule for
     G3, the table re-derived (expected: no direction changes, since `SizeOfHeaders` is already up and `shf` is in
     M_full; then the guaranteed detectors need no retraining), the closure check rerun. It is a shift, not an
     addition: GAMMA becomes additions on files with room and additions plus a shift on the others (the paper's
     operations table and the additions-only detector's coverage of GAMMA change accordingly);
  2. GAMMA wrapped so its chosen edit is written by `catalogue.write_section` (with growth when needed) and one
     multi-library `write_imports` (a pure addition); the search unchanged; a structural check (nothing undeclared
     moved, nothing lost) kept as an assertion; a smoke test of speed (up to 30 writes per query);
  3. the reruns: toolkit (every part), the material (`pv_attacks.py`, `attack_training.py`), the learned defenses and
     their attacks; the adaptive search may use the growth too.
- **The validity rule compares sets** (fix to `provexp.attacks.validity`; reruns as needed). Meanwhile the current
  round's numbers go into the manuscript.
- ERDALT's running folds (job 1239350, current material) finish; the rerun replaces them.

Pre-existing, found on the way: `catalogue.write_gap` raises the certificate table's offset but not the debug entries'
`PointerToRawData` (a file offset); harmless to loading, to fix with the growth variant.

## 5. Session 102: header growth, a fifth layout clause, the file store

Session 102 (2026-11-20, tigris interactive node; scripts in `artifacts/scaleup/diag/`: `hgr_room.py`,
`hgr_room_ts.py`, `hgr_room_why.py`, `catalogue_violations.py`, `insertion_body.py`, `table_past_headers.py`; smoke
outputs in `diag/hgr-derive-smoke/`, `diag/derive-store-smoke/`; the tables and catalogue report before the reruns in
`diag/before-s102/`).

**Decided (user):** header growth is a **fourteenth operation, `hgr`**, not a variant of `shf` (its gap lies in the
headers, as `ext`'s does; `shf`'s is body). The debug entries' `PointerToRawData` stays stale: it lies in a section's
data, so raising it would write body bytes under every insertion (the body sums would turn "both" under M_shift and
M_full); the loader never reads it, and no feature reads pefile's debug payload.

**`hgr`** (`catalogue.write_header_growth`, `predict_header_growth`; commit dec4fb1): a FileAlignment-multiple gap
inserted at SizeOfHeaders, which rises by the gap; PointerToRawData and the certificate offset past it rise
(`_raise_pointers`, shared with `write_gap`, whose bytes are unchanged). Refused when the image is low-alignment or has
no sections, a section's data starts in the headers, the section table runs past them, the grown headers would reach
the first section's RVA, or a data directory lies between the headers' end and the first RVA. Declared: the insertion
plus SizeOfHeaders up (no body change). In M_shift and M_full. Exact on all test fixtures for both extractors; hand
rules (size, SizeOfHeaders, security offset), expert table (no change), catalogue-check instances (zeros, random,
printable). On 40 training files the loose table derived with and without `hgr` is identical in every shared cell, every
threat-model direction and every detector input file; G3 shows only "stricter" cells.

**Header room for GAMMA's 30 sections** (test malware, 1,000): 97 fit already, 711 more after `hgr` (808 in all, not
session 101's 992, which ignored data after the table). The other 192: data right after the section table 85 (6 bound
imports), a section's data inside the headers 52, the first RVA too low for 30 headers 42, a directory in the gap
region 8, no sections or low alignment 3.

**A pre-existing soundness gap, closed by a precondition clause.** The catalogue check of 2026-11-18 (job 1141844)
reported `pass: False`, unrecorded until now: `ext` (32 edits, 232 feature moves) and `shf` (24, 115) violated the
population table, all on two files (`689c564a...`, `cfd2a0b8...`; originals and escaped copies) with hundreds of
sections, whose section table runs past SizeOfHeaders (0x400) into the run before the first section's data, which the
sums extractor counts as body; the insertions' PointerToRawData updates write those body bytes. *Decided (user):* a
fifth `plain_layout` clause, "the section table ends within SizeOfHeaders" (`catalogue.section_table_end`; mirrored as
`table_past_headers` in `population.clauses`; commit 9c0e970). Closure is expected to hold (no operation moves the
table past SizeOfHeaders); the rerun checks it. Not checked: whether Windows loads such files (the clause does not
depend on it). The count over the training and test sets stalled (random reads from the SimpleDB); the derivation's log
reports the population.

**The file store holds every training file** (user: the SimpleDB is for sequential passes; files read by name
repeatedly belong in the store). `2-features/file-store/run.sh` now stores all of `tr.parquet` (`TRAINING=all`, the
default; commit 079862f); the derivation reads from the store by default (`--db` reads a SimpleDB; identical outputs on
20 files; the commit "Directions: read the files from the file store by default" on branch `hgr`, merged into `main`
only after job 1243542 has finished).

**Submitted** (`logs/submit-*-s102-hgr.txt`): `directions` 1243542 (240G), `catalogue-checks` 1243543 (afterok; 80G,
2 h), `file-store` 1243547 (48G). Both started jobs' logs read: healthy.
