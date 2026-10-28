# Design: deriving side effects and directions from the instrumented extractor (2026-10-27)

This is the foundation of direction A's novelty claim and of A'. Today the directions (C4) are hand-written rules per
feature group (`scripts/a_directions.py`, about 130 lines of rules), and the side-effect predictors (C1) are
hand-coded per edit type (`scripts/a_c1_table0.py`, used by `scripts/a1_adaptive.py`). Both were validated against
re-extraction, so direction A's results stand, but the paper says the derivation is automatic. This document designs
the code that makes it so. It implements the model in `docs/feature-provenance-model.md` (Sections 2-4: three layers,
edits as item operations, C1-C4, assumptions A1-A4) and the threat models in `docs/direction-A-threat-model.md`. It
adds nothing to the model. Nothing here is built or run yet.

## In plain terms

The extractor works in three steps. First it finds the file's pieces (sections, imports, strings, header fields,
bytes, entropy windows). Then it adds up what each piece contributes (counts, sizes, hash buckets). Finally it applies
a formula per feature (divide by the file size, take an entropy, take a maximum). Today the instrumentation records
only *which bytes* feed each feature: `Contributions.add_item` takes an item's byte ranges and one feature column,
spreads one unit over those bytes, and forgets the item. The plan is to record the middle step as well: every piece,
which bytes make it up, which bytes decide where it is, and the numbers it adds to which running totals. Each feature
also gets its final formula, written as data instead of code.

An attacker's edit can then be described once, in terms of pieces: "add a section", "add bytes at the end",
"overwrite bytes in this region". That replaces reasoning about 2,568 features x 12 operations by hand. Everything
else follows by arithmetic:

- **Side effects (C1):** new totals = old totals + what the added pieces contribute - what the removed pieces
  contributed; then apply each feature's formula to the new totals.
- **Directions (C4):** which signs the edit's contributions can have, pushed through each feature's formula.

Two kinds of thing stay hand-written: how each feature group's pieces and formulas are recorded (one annotation per
loop of the extractor, in the same places the provenance instrumentation already sits), and the edit catalogue, which
*is* the threat model. Neither one says what an attacker can do to a feature, and each is checked by a machine. The
recorded totals passed through the declared formulas must reproduce the extractor's output **exactly** on every file,
and the catalogue's predictions must match re-extraction (Table A0). Today's hand rules have no such check, so a wrong
rule goes unnoticed. The section on anticipated disagreements below lists four places where reading the code
suggests they are wrong.

## Where we start

The thrember extractor is already split almost along the model's layers. `raw_features` builds a dictionary that is
mostly layer-2 sums (byte counts, string counts, the list of sections with their sizes). `process_raw_features` is
mostly the readout (normalize, hash, take max/min). Both C1 predictors in `a_c1_table0.py` work at this level: they
edit the raw dictionary and call `process_raw_features`. The split is not clean in five places, and each of them
matters to the design:

| Where the raw dictionary is not a sum | Why it matters | Fix in the item layer |
|---|---|---|
| entropies are computed in `raw_features` (file, overlay, sections, strings) | an entropy is a readout, not a sum | item contributes its byte counts; entropy is a readout |
| `size_ratio = SizeOfRawData / len(bytez)` | contribution depends on the file length (A2) | item contributes SizeOfRawData; division in the readout (model doc, A2) |
| `imports[dll_name] = []` per descriptor | a later item erases earlier ones (A2, the quirk) | flagged in `ImportsInfo`; `ImportsInfoMerged` is local |
| entry section chosen by a rule over AddressOfEntryPoint and all sections | a selection, not a sum | a selection readout with declared locating elements |
| overlay start chosen by pefile from all section and directory extents | the overlay item's existence and extent depend on many fields | overlay item with those fields as locating elements |

C4 needs the readout as data, because it reasons about the formula's shape (ratio, entropy, max) and not only its
value. So the design defines the readout explicitly rather than reusing `process_raw_features`, and the exactness
check proves that the two agree.

## Components

### 1. The item table (layers 1-2), recorded by the extractor

Each feature type gains an `items(bytez, pe)` method next to `provenance`, as a pure addition to `features.py`; the
original lines and the existing `provenance` methods stay as they are. It returns the items of that group. An item
has:

- a **kind** (`byte`, `window`, `string`, `section`, `overlay`, `field`, `import`, `library`, `export`, `rich_pair`,
  `certificate_table`, `entry`);
- its **member ranges** (the bytes its content is read from, as today) and its **locating ranges** (the bytes that
  decide whether it exists and where; A1, mostly new);
- the **attributes** its contribution is computed from (a section's name, SizeOfRawData, VirtualSize, byte counts,
  characteristics; a string's text);
- its **contribution**, written in a small vocabulary whose sign behavior is known, so that C4 can read signs off it
  without running anything.

| Contribution term | Meaning | Sign when the item is added | EMBER uses |
|---|---|---|---|
| `count(s)` | +1 to sum s | + | numstrings, num_sections, num_w, ... |
| `add(s, a)` | the value of attribute a (declared nonnegative) | + or 0 | printables, SizeOfRawData into max pools |
| `bins(S, vec)` | a vector of nonnegative counts into sum family S | + or 0 per bin | byte histogram, window counts in row Hbin, printable distribution |
| `hashed(S, key, a, signed)` | a or 1 into bucket h(key), times the hash's sign if `signed` | + if unsigned; sign of h(key) if signed | section size/vsize/entropy/characteristics, entry name, rich pairs (signed); imports (unsigned) |
| `keyed(S, key)` | +1 to the per-key count of `key` (distinct-count readout) | + | unique libraries |
| `slot(s, a)` | the value of a field read from exactly one item | any (modify only) | header fields, data directories, DOS fields |
| `opaque(group, a)` | an attribute computed by a parser we do not open | any; declared default when absent | authenticode (signify) |

Sums aggregate by addition, except the max pools (section entropy, size, vsize ratio), which the item table answers
directly, since removal needs the runner-up (model doc, C1 step 2). The generic types (Item, ItemTable, the
vocabulary, the projection to a BoxMatrix) know nothing about PE files and live in `src/provexp/items.py`, beside
`provenance.py`. `PEFeatureExtractor` gains `item_table(bytez)`, which parses once and concatenates the groups.

### 2. The readout table (layer 3), as data

Each feature gets a readout spec: a type and the sums or items it reads. Each group's `readouts` property (a pure
addition) lists them, generated per group by a few lines (256 histogram bins share one rule).

| Readout | Formula | EMBER features | Global C4 rule (all files) |
|---|---|---|---|
| identity | s | counts, hashed buckets, header and directory fields, raw sums | signs of Δs |
| ratio | a / b (b = 0 -> declared default) | avlength, overlay_size_ratio | fixed if neither moves; if only a moves: sign of Δa; if only b moves: opposite sign; both move: both (per-file ratio test exact) |
| normalized vector | v_i / Σv | histogram, byteentropy, printable distribution | both if Σv moves, else sign of Δv_i (an in-place write: one bin up, others down) |
| entropy | H(v) | general entropy, string entropy; overlay and section entropies as item attributes | both if v moves (per-file cross-entropy test exact) |
| max over items | max of attribute a (optionally / a total) | max_entropy, max_size_ratio, max_vsize_ratio | added items: up; removed or modified items: both |
| min with zero | min(a over items ∪ {0}), a ≥ 0 | min_entropy, min_size_ratio, min_vsize_ratio | fixed (constant 0) |
| distinct count | number of keys with count > 0, per bucket | num_libraries, library_hash_* | keys added: up |
| field transform | bit test or category lookup of one field | characteristics_*, dll_characteristics_*, machine, subsystem | fixed if the field is fixed, else both |
| selection | attribute of the item a declared rule selects | entry_name_hash_* | fixed if no locating or member byte moves, else both |
| opaque with default | parser output, default when the item is absent | authenticode | removal: sign of (default - value) over the declared value range; other changes: both |
| outside the model | (no items) | pefilewarnings (88), is_pe | both, except is_pe, which the catalogue declares fixed (loader-safe edits keep a PE) |

That is ten readout types plus the residual, which matches the model's list (Section 4a, Setting). The readouts live
with the feature types in `features.py`; their evaluators and the C4 rules live in `src/provexp/items.py`, since
neither one depends on PE.

### 3. The edit catalogue (the threat model as item operations)

`src/provexp/featuresets/ember2024/catalogue.py` declares the twelve operations of `docs/direction-A-threat-model.md`
Section 1. Each operation is a function from the item table of z and a parameter value to an item delta (T+, T-, T~,
T→) plus the field changes it forces (an added section raises NumberOfSections and SizeOfImage and writes a table
entry into the header region). Each operation also declares its **parameter domain**: "any 8-byte name", "any content
up to B bytes", "any value for these fields", "zero this directory entry". C1 takes one parameter value. C4 takes the
domain. The catalogue is PE-specific and stays with the experiment code, as the threat model does; the model stays
generic.

Operations that write bytes in place (`slk`, `dos`, `hdr`, `chk`) are not given item deltas by hand. They declare
only the byte region and the content domain, and the engine derives the delta through layer 1 (component 4). The
declared structural operations (`sec`, `imp`, `ext`, `shf`, `rdb`, `rsg`, and the table-entry part of `ren`) state
their deltas, as the model allows (Section 3, "declared").

### 4. The C1 engine (side effects of one concrete edit)

`src/provexp/reach.py`, generic. Given z's item table and one edit:

1. **Byte writes** (in place): find the items whose member or locating ranges meet the written region S, using an
   interval index over the table. If S meets a locating range, the edit is structural. If the catalogue declares the
   delta, use it; otherwise flag the edit and the affected items (model, Section 3). If not, re-run each affected
   kind's recognizer on S widened by its declared margin (A3), on the edited bytes only, and diff the result with the
   old items to get T-, T+, and T~.
2. **Declared operations:** take T+, T-, T~, and T→ from the catalogue. Moved items keep their contributions, except
   position-defined kinds (windows, fields read through a file offset), which are re-recognized over the shifted
   range.
3. Update the sums, answer max pools from the table, and apply the readouts.

The engine never extracts z'. It reads at most the edited region plus margins, as the hand predictors do now, but
from a cached item table rather than by re-running `raw_features` on z per prediction (which `_raw_copy` does today).

### 5. The C4 engine (directions under a threat model)

Also in `reach.py`. For each operation, it collects the sign envelope of every sum over the operation's parameter
domain: added items contribute their vocabulary signs, removed items the negated signs, and modified items the union
of both. For signed hashing with an attacker-chosen key, the reachable (bucket, sign) pairs are computed by
enumerating the key domain, as `bucket_names` in `a1_adaptive.py` already does for three-letter names (it hits all 100
pairs). For in-place writes, the envelope comes from the kinds the region can touch and the content domain. The
readout rules above then turn sum envelopes into feature signs, per operation. The union over a threat model's
operations gives fixed / up / down / both. Flagged items (undeclared structural, A2 failures) give "both" on every
feature they reach, which keeps the table sound.

The output has the same shape as run 76's `directions.csv` (per-operation signs, the direction under each threat
model, and the re-encoded directions), so the comparison in G3 is a join and the downstream files
(`*.neutralize.txt`, `*.monotone.tsv`) come out unchanged in format.

**The re-encodings come for free.** With layer 2 explicit, `sums.py`'s groups are identity readouts over sums, with
items restricted to the body regions (an item filter) and signed buckets read as their positive and negative parts.
The C4 engine gives their directions with no further rules, and the exactness check (G1) applies to them as well.

## What stays declared by hand, and how each declaration is checked

None of these declarations says "feature j moves up under operation o". That is the line between the old approach
and the new one.

| Declaration | Size | Mechanical check |
|---|---|---|
| item emitters (which items, members, contributions) | one `items` method per group, 12 groups | **G1**: readouts over the recorded sums reproduce `feature_vector` exactly; **G2**: projecting items onto bytes reproduces today's provenance |
| readout per feature | ~10 types, about 30 group-level rules | G1 (same check) |
| value ranges (attribute is nonnegative, a default value) | a few per kind | asserted on every recorded item; most follow from the field's unsigned type or the formula (entropy ≥ 0) |
| locating ranges (A1) | per kind | **G5**: single-byte flips across the header region; any byte that changes the parse but is not recorded as locating is a failure |
| recognizer margins (A3) | strings, windows, fields | **G6**: random local writes, engine vs re-extraction |
| catalogue (operation -> item delta, parameter domain) | 12 operations | **G4**: Table A0 rows, engine vs re-extraction, including adversarial parameter choices (G7) |
| hash image of attacker-chosen keys | per signed family | computed by enumeration, not declared |
| features outside the model | 88 pefilewarnings | none: declared "both" and reported as a residual |

One limit should be stated plainly. G1 checks the emitters on the files we have; it cannot catch a locality failure
(A2) that natural files never trigger. The duplicate-DLL quirk is the example: almost no file has two descriptors for
one DLL, so the plain `ImportsInfo` emitters would pass G1 while being wrong for an attacker who adds one. G7 is
there for this: the catalogue test includes adversarial parameter choices (a repeated DLL name, an empty or
colliding section name, printable bytes next to an existing string). For the EMBER instance, the derivation is
therefore validated, not proved. The paper should say "computed from the instrumented extractor and validated
against re-extraction", which is what A0 already supports.

## Validation and go/no-go checks

| Check | What is compared | Pass |
|---|---|---|
| G1 exactness | readouts(item table of z) vs `feature_vector(z)`, all 2,480 modeled features, plus the four re-encoded groups vs `SumsFeatureExtractor` | bit-exact (float32) on every pilot file; any mismatch is a bug, with no tolerance |
| G2 projection | items spread over their members vs today's `provenance` BoxMatrix | equal up to float rounding |
| G3 directions | automatic C4 table vs run 76's `directions.csv` (and run 80's `a_directions_sums`) | every disagreeing cell explained (below) |
| G4 C1 | engine vs re-extraction on the run 79 pairs, and engine vs the hand predictors | reproduces Table A0; bit-equal to the hand predictors on every pair |
| G5 locating (A1) | byte flips in the header region of 20 pilot files: parse change vs recorded locating ranges | no unrecorded locating byte |
| G6 margins (A3) | random in-place writes, engine vs re-extraction | exact |
| G7 catalogue (A2) | the nine operations A0 does not yet cover, plus adversarial parameters, engine vs re-extraction | exact, or a flagged A2/A4 case named in advance |

**G1 and G2.** Hypothesis: both pass after a debugging round. Mismatches should come from mirroring details that
`provenance` already handles (clipping on truncated files, zero-size sections, pefile's handling of name offsets);
none should be conceptual. If a group cannot be made exact, it is placed outside the model with pefilewarnings and
the claim shrinks by its size. That is the no-go for the group, not for the design.

**G3 against run 76.** The comparison runs at two levels: the 30,816 per-operation sign cells (2,568 features x 12
operations), and the direction per threat model, for the features and for their re-encodings. Each disagreement goes
into one of three classes:

1. *The hand rule was wrong* (the automatic table is stricter). This needs a witness: a concrete file and edit,
   re-extracted, that moves the feature the way the hand rule ruled out.
2. *The automatic table is conservative* (a flagged item or a coarse readout rule says both where the truth is
   one-sided). This must be argued, and tightened if it costs a feature a detector uses.
3. *The catalogue declares something different* from what the hand rule assumed (e.g., which header fields an added
   section updates). This is resolved by the catalogue's A0 row (G7), not by either table.

Hypothesis: the threat-model columns agree on more than 99% of features. Many per-operation cells will differ, in the
harmless direction: the hand rules use `every("+-")` as a shorthand, while the engine will find, for example, that
zeroing a directory entry (`rdb`, `rsg`) can only raise the normalized zero-byte bin and lower the others. The
threat-model unions absorb these. The class-1 cases are the ones that matter, because each one is a hole in a C4
row's guarantee.

**Anticipated disagreements (from reading the code; each to be confirmed with a witness):**

| Feature(s) | Run 76 | Expected from the engine | Why | Witness to build |
|---|---|---|---|---|
| `section:overlay_size`; the `body_*` sums | up under every threat model (constrained +1 in the M_full models) | both | pefile's overlay start ignores any section or directory extent that runs past the end of the file. Appending can bring such an extent inside the file, so the overlay start jumps later and the overlay (and the body region `sums.py` takes from it) can shrink. These are the 11 overrun files Table A0 flagged under A2 | the A0 overrun files; a test file with a directory past EOF |
| overlay features under `rdb` | not moved | moved (M_full) | the DEBUG directory's extent counts toward the overlay start, so zeroing the entry can move it | a file whose debug data is the furthest extent |
| `richheader:*` under `ext` (M_shift) | fixed | both | pefile searches for "Rich" in [0x80, optional-header offset), a range that contains the gap `ext` inserts; on a file without a Rich header, the attacker's gap content creates one | a file without a Rich header plus `ext` |
| `section:entry_name_hash_*` under `sec` (M_add) | fixed | both | when AddressOfEntryPoint lies in no section, the entry is the first executable section; an added executable section can become it, or can contain the entry point | a file whose entry point lies outside every section |

**First row confirmed (2026-10-27).** `pefile.get_overlay_data_start_offset` skips any extent whose end lies past
the file. Of the 100 pilot files, 11 have a section past EOF; on the 5 whose overrun is under 8 MB, appending enough
bytes to cover it lowered `overlay_size` on 4, all malware (e.g. 31,482 -> 4,096). Gain share in the M_full C4
models: `overlay_size` 0.9% (features), 0.25% (sums). Witness: `scripts/a_overlay_witness.py` (run 88).

**The `body_*` sums are not affected (checked 2026-10-27).** On all 100 pilot files, appending enough bytes to bring
every skipped section and directory extent inside the file (190 appends; guard byte plus random payload) lowered no
`body_*` count, while `overlay_size` dropped on 8 files. The reason is in `sums.body_regions`: it clips an overrunning
section at the end of the file and starts the overlay region only after every section's clipped data, so appending
extends that section's region instead of shrinking the overlay's. The one case left open in principle is a data
directory past EOF while no section is; the pilot has none (all 11 overrun files overrun through a section). Of the
11, 7 are files truncated at the dataset's 4,000,000-byte cap, so the overrun is mostly a truncation artifact.
Decided (user, 2026-10-27): treat pefile's rule as the extractor's real behavior (no patch); `overlay_size`
becomes two-sided under appending, the only feature whose direction changes (`overlay_size_ratio`, `overlay_entropy`,
and `max_entropy` are two-sided already). The hand rule in `scripts/a_directions.py` changes with the next retraining of the C4
models, so that code and artifacts stay in step.

The first row is the important one. `overlay_size` is constrained monotone in the C4 detectors of Table A1, and the
body sums are most of the C4-on-sums row. If it is confirmed, the strict table moves them to "both" (or the decision
in Open decision 2 applies), the affected C4 models are retrained, and Table A1's C4 rows are re-run. Table A1's
adaptive search could not have found this hole: its append predictor assumes no overrun (`has_overrun_section`
excluded those files from A0's exact count). That is exactly the kind of failure automatic derivation exists to
catch, and if it is confirmed, it belongs in the paper as a finding, stated briefly.

**G4 against Table A0** (`docs/direction-A-threat-model.md` Section 6, run 79). The engine must reproduce append:
exact on the 89 A2-applicable files, with the 11 overrun files flagged **by the engine itself** (the append region
meets the overlay item's locating extents) rather than by the hand-written `has_overrun_section`. It must reproduce
dos_overwrite: exact on 100/100. For add_section, the declared delta must equal run 79's predictor feature by feature
on all 100 files, with the same A4 residual against the LIEF output. Bit-equality with the hand predictors on every
pair is the stronger half of G4: it carries runs 82-87 (which used the hand predictors) over to the engine with no
re-run. Run 79 took about 2 minutes, so G4 is a short job to run directly.

## Hard cases

**Strings and regex boundaries.** A string item is a maximal run of 5+ printable bytes. Its margin extends to the
nearest non-printable byte on each side, so an in-place write or an insertion can split one string into two or merge
two into one, and C1 handles that by local re-recognition. Each string's contribution includes 76 regex indicators,
which C1 recomputes on the re-recognized strings. C4 needs more: when a string is modified by extension (appending to
a file that ends in printable bytes), can an indicator go from 1 to 0? A regex search keeps every match under
extension unless the pattern inspects context past the match: `\b`, `\B`, `$`, `\Z`, or lookahead on the right;
`^`, `\A`, or lookbehind on the left. The engine decides this from the parsed pattern (Python's `re` parser), so it
is derived from the extractor and not declared. The test is syntactic and therefore sound but possibly conservative.
Run 76 used `pattern.endswith("\\b")`, which should agree on EMBER's 76 patterns; G3 will show it. The body-region
re-encoding breaks strings at region boundaries (the joining zero byte), which the engine models as one recognizer
run per region.

**Byte-entropy windows.** Windows are position-defined items: 2,048 bytes at multiples of 1,024 from offset 0, each
contributing its 16 nibble counts to the row of its own entropy bin. The row depends nonlinearly on the content, so a
modified window can move counts between rows; added windows only add nonnegative counts to some row. Three things
need care: an append adds windows that span old and new bytes (margin = window - step); a move (`ext`, `shf`)
re-tiles every window after the insertion point unless the shift is a multiple of 1,024, so C1 re-recognizes them
all (as costly as that part of an extraction, but still no full extraction); and a file under 2,048 bytes is one
whole-file window that every edit modifies. Region-tiled windows (`body_byteentropy`) count only full windows from
each region's start, so extending a region adds windows and moves no existing one. The engine should find that
without being told.

**Max and min readouts.** Max pools are answered from the item table (adding: max(old, new); removing or lowering the
maximum: the runner-up). `max_size_ratio` divides by the file length, so the item contributes SizeOfRawData and the
readout divides (the A2 fix the model names). The overlay sits in the same pools as the sections, and its entropy and
size are attributes of an item whose content grows under append. That is why `max_entropy` comes out "both" under
`app` (appending can lower the overlay's entropy), which agrees with run 76. The three min features come out "fixed"
from the readout type and the nonnegativity of their attributes; nothing special-cases them. Sections with
overlapping raw data are separate items with overlapping members, so one write can modify several of them; the
interval index handles that.

**Signed hashing.** sklearn's FeatureHasher gives each key a bucket and a sign (murmurhash3). A section's size, vsize,
and entropy go to h(name) with that sign, and its characteristics go to h("name:prop"). Rich pairs and the entry
name are also signed; imports and libraries are unsigned. With an attacker-chosen name, the reachable (bucket, sign)
set is computed by enumeration, which for 8-byte names covers every pair; so `sec` is "both" on every signed bucket
and "up" on every split part. Rename is a modify: the item leaves h(old) and enters h(new), so both parts of both
buckets can move, which matches run 76's M_full re-encoded "both" for those buckets. A restricted catalogue (names
from a list, as a toolkit uses) gets the exact image of that list, and the engine handles it the same way.

**pefile warnings, and other features with no items.** pefilewarnings (88 features) are raised from all over pefile's
parser, which does not say which bytes caused them. They stay outside the model: "both" under every operation,
excluded from G1 and G4, and reported as a residual (they changed on 6 of 100 files under append and 1 under the DOS
overwrite in run 79). `is_pe` has no items either; the catalogue declares it fixed, which is the loader-safety
premise, and the A0-style tests check it by re-parsing (the A1 harness already counts non-PE outputs as invalid).

**Also hard, briefly.** *The import quirk:* in plain `ImportsInfo`, a function item's contribution depends on later
descriptors for the same DLL name, so its emitter marks those items non-local and the `imp` operation flags them when
the chosen DLL name already exists. Experiments use `ImportsInfoMerged`, where the items are local. *The Rich
header:* XOR-keyed pairs found by searching for markers, so the whole search range is locating (and that is where the
`ext` disagreement above comes from). *The entry section:* a selection, located by AddressOfEntryPoint and every
section's range and characteristics. *Truncated files* (the 4 MB cut): extents past the file end are the A2 cases
above, and the engine flags them through the overlay's locating ranges.

## Build order and effort

Estimates are focused working days, including tests in the style of `tests/` (sections mirrored, real-file tests
skipped when the data is absent).

| Step | What | Where | Effort | Check reached |
|---|---|---|---|---|
| 1 | Item, ItemTable, contribution vocabulary, readout types and evaluators, projection to BoxMatrix | `src/provexp/items.py` | 1-1.5 d | unit tests |
| 2 | emitters and readouts for the simple groups: general, histogram, header, datadirectories, exports, imports (both classes), richheader, authenticode | `features.py` (additions) | 1.5-2 d | G1, G2 for these groups |
| 3 | the hard groups: strings, byteentropy, section (max pools, overlay, entry selection, signed hashes) | `features.py` (additions) | 2-3 d | G1, G2 complete |
| 4 | locating ranges (A1) for every kind; the byte-flip check | `features.py`; `scripts/item_checks.py` + `run/` script | 1-2 d | G5 |
| 5 | C1 engine: interval index, local re-recognition with margins, declared deltas, moves | `src/provexp/reach.py` | 2-3 d | G4 (A0 reproduced), G6 |
| 6 | catalogue: 12 operations with parameter domains and adversarial instances; A0 rows for the nine operations not yet covered | `featuresets/ember2024/catalogue.py`; `scripts/a_c1_table0.py` extended | 2-3 d | G7 |
| 7 | C4 engine: sign envelopes, hash images, readout rules, unions; the disagreement report with witnesses | `reach.py`; `scripts/a_directions.py` gains `--derive` | 2 d | G3 |
| 8 | re-encodings as item filters and identity readouts, checked against `SumsFeatureExtractor` | `reach.py` / `sums.py` | 1 d | G1 (sums), G3 (sums) |
| 9 | switch the scripts to the engines; keep the hand rules and predictors as test oracles. If G3 moved a direction: retrain the affected C4 models and re-run Table A1's C4 rows (user-run `run/` scripts) | `scripts/` | 1 d + runs | Table A1 consistent |

Total: about 14-19 working days, plus the user-run retraining if step 7 confirms a class-1 disagreement. Steps 1-3
are useful on their own (A' needs the item table to realize feature-space targets). Step 7 does not depend on step 5
and can run in parallel with steps 5-6.

Runtime for the checks, from the slowest case: an item-table pass should cost about as much as one extraction
(~0.25 s per pilot file), so G1/G2 on the 100 pilot files take under a minute. G5's byte flips (~1,024 header bytes x
20 files, parse only) are about 20,000 pefile parses, a few minutes with 16 workers; that is a `run/` script, smoke-
tested on one file first. G4 and G7 at pilot scale are run-79-sized (minutes).

## Build status (2026-10-27, third session)

Steps 1-5 are built; the effort table above was far too high (they took one session). Results:

| Check | Result | Run |
|---|---|---|
| G1 exactness | bit-exact on 100 pilot and 2,000 files, both import variants; no debugging round | 90 |
| G2 projection | equal to `provenance` on 100 pilot files (max relative difference 0.0) | 90 |
| G5 locating | first round: 1,385 failures at 55 (file, byte) pairs from three pefile rules (the section table is a chain; any non-PEFormatError in a directory parse ends the parse, e.g. a bogus debug size; SizeOfImage bounds relocations). After the fix: 0 failures on 18,944 flips of 20 pilot and 18,944 of 20 fresh files | 91 |
| G4 C1 | Table A0 reproduced: append flagged by the engine on exactly the 11 overrun files, bit-exact on the other 89; dos_overwrite bit-exact on 100; add_section bit-equal to the hand predictor on 100; bit-equal to the hand predictors on all 289 predicted pairs | 92 |
| G6 margins | first round: 1 failure in 1,561 (the dynamic relocation table the load configuration points to). After the fix: 1,560/1,560 pilot and 1,463/1,463 fresh writes bit-exact | 93 |

Decisions made while building (all within the design): locating ranges of every parsed item include the bytes the
parse succeeds through (`pe_locating`: header fields, the declared section table, every directory entry, the data of
the ten directories pefile parses), so pefile's crash on a malformed debug directory is recorded rather than patched
(`docs/upstream-issues.md` item 5; the user may revisit). The section group's `file` item carries the overlay's
locating ranges when there is no overlay. Recognizers are per feature type (`FeatureType.recognize`); opaque and
import/export items have none yet, so writes to them are flagged. In-place predictions re-count the whole-file byte
run (cheap to make local if A' needs it). Steps 6-9 remain; step 7 does not depend on 6.

**Fourth session (2026-10-27): structures past the end of the file.** The overlay row of the anticipated
disagreements is one case of a wider one: pefile skips any directory, section, or signature table that a header
points to past the end of the file, and appending turns the appended bytes into it. 12 of 100 pilot files have such
a structure. Witnessed for the signature table (`num_certs` 0 -> 1 on a truncated pilot file; `docs/status.md`),
which the hand rules let only fall; exports, relocation flags, and the entry name hash are exposed the same way (to
witness in G3). Decided (user): strict directions plus one precondition row (no locating range past the end of the
file; fallback detector otherwise). Also: pefile's directory parsers crashed on unreadable structures and the
extractor then treated the file as not a PE; one guard now makes a crash lose only that directory (`features.py`;
run 94 rewrote the 394 stored files affected). This makes per-structure locating ranges sound, which step 7 needs:
today every parsed item is located through every directory's data (`pe_locating`), so the strict C4 table would
otherwise call even header fields two-sided under append.

**2026-10-28: per-structure locating ranges and the C4 engine (step 7).** `pe_locating` is split into
`header_locating`, `section_locating`, `entries_locating`, and `directory_locating`; G5 also flips directory data now
(run 95). Round 1 found signify reading SizeOfOptionalHeader and the import parse reading names and both thunk arrays
through their terminators (one rule: every byte the import parse reads locates every import and library); then 0
failures on 58,666 flips. G1/G2, G4, G6 unchanged (run 96; G6 flags 209 writes instead of 440). The C4 engine is in
`reach.py` (Vocabulary from recorded items, Change: add/remove/modify/rewrite/grow/flag, envelope, one rule per readout
type, regex extension test, hash images); the catalogue (`catalogue.py`) derives the in-place operations from the
bytes they write on each corpus file (restricted to loader-ignored bytes) and declares the structural ones
(provisional until step 6), plus the precondition check. Results (run 97, pilot and 2,000 files, identical): the
precondition variant equals the hand rules per threat model except entry_name_hash under sec and the Rich header under
ext (both anticipated) and security_size (hand over-approximates); the strict variant keeps 44 features under M_add
and 9 under M_full (6 constant), so strict soundness over every possible file leaves no usable detector. Also found:
three `hdr` fields lie in pefile's Rich search range. Witness: the signature (run 98, two files, num_certs 0 -> 1).
Open: the remaining witnesses, the sums re-encodings (step 8), and what the detector does with files that fail the
precondition (16% of the 2,000-file set; 73 benign, 245 malware) -- the user's decision.

## Open decisions for the user

**Settled (user, 2026-10-27), all as recommended:** (1) add `items` now and keep `provenance` until G2 passes, then
make it a projection of `items` (the old code is in git); (2) strict only, no precondition row: pefile's overlay rule
is the extractor's real behavior, `overlay_size` becomes two-sided under appending, the `body_*` sums are unaffected
(run 88); (3) re-run Table A1's C4 rows at pilot scale once step 7 changes a direction (the toolkit part is a `run/`
script for the user); (4) G1 on the pilot and on the 2,000-file set; (5) the sound syntactic regex test. The
questions as first posed:

1. **Mirrors in `features.py`.** Each group would carry three mirrors of the same loop: `raw_features` (thrember's),
   `provenance`, and `items`. Proposal: add `items` now; once G2 passes, make `provenance` a projection of `items`,
   which removes one mirror. `provenance` is our addition, not thrember's, so this respects the pure-additions rule,
   but it changes code the old direction's results came from. Keep both, or collapse after G2?
2. **Strictness for rare layouts.** The settled rule is strict global soundness (the threat-model doc, Section 2). If
   the overrun case is confirmed, strictness moves `overlay_size` and the body sums to "both" and costs the C4-on-sums
   row some accuracy. The alternative is a per-file precondition the detector checks at inference time ("every
   extent lies within the file"; files that fail it go to a fallback detector), reported as a separate row. Strict
   only, or strict plus the precondition row?
3. **If G3 changes directions, re-run Table A1's C4 rows at pilot scale right away**, or batch that with the scale-up?
4. **G1 scale.** The 100 pilot files (the pilot-scale rule), or also the 2,000-file set, since exactness is cheap
   (~2,000 x 0.25 s, about a minute with 16 workers)? Exactness on more files is the cheapest evidence the
   instrumentation is right.
5. **The regex test.** A sound syntactic test (proposed) may call a regex two-sided when it is not. Accept that, or
   require an exact decision for the patterns where the syntactic test says "both"?
