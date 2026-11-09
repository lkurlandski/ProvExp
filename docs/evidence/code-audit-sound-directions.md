# Code audit: does the code compute the derived table of Definitions 9-10? (2026-11-09)

Read-only audit of `src/provexp/reach.py`, `items.py`, and `featuresets/ember2024/{catalogue,sums,features}.py` against
`manuscript/_d_framework.tex` (Definitions 7-10, Table 2) and `_j_proofs.tex` (Table 3). Nothing was changed.

**Verdict.** On EMBER, the code gives the table Definitions 9-10 define, except for two per-operation cells that the code
leaves two-sided where the paper's ratio rule gives one side. No threat model's direction changes, so no number of
Tables 6-7 changes. Check: the pilot derivation (100 files, sums extractor) was run twice into the scratchpad, once with the
code as it is and once with Table 2's ratio and normalized-bin rules patched in. The two runs differ in exactly two cells
(`overlay_size_ratio` under add-section and add-imports, precondition variant: code both, paper down); the `M_*` columns and every
monotone/neutralize file are byte-identical. The paper and the code differ more in how they reach the table, and
several of those differences need a sentence in §4.

## Findings

1. **Ratio rule coarser than Table 2** (`reach.py:426-430`, also used by `Max`/`Min` with `divide_by`, 916 and 923).
   The code returns both whenever the numerator and the denominator both move, where Table 2 has $d_a \cup (-d_b)$.
   Effect: the two cells above. *Change the code* to the paper's rule, which is a one-liner and is proven in the appendix.
   EMBER's denominators reach 0 only when their numerators are 0 too, so the $b > 0$ condition costs nothing.
2. **Normalized-bin rule finer than Table 2** (`reach.py:903-910`). When exactly one bin of the family moves, the code
   gives that bin its own direction, where "as the ratio" gives $d \cup -d$ = both. The rule is correct (a single
   changing bin's share moves with it), but the paper does not prove it, and it never fires on EMBER (the patched run
   gives the same result). *Change the code* to the paper's rule, for one rule set.
3. **Pools have no single rule in the code; same table.** Pools are item-attribute readouts (`Max`/`Min`,
   `reach.py:914-923`): an added item raises a max and a removed one lowers it (the reverse for a min), and attribute
   changes come from `KindDelta`. That is Definition 9 with neutral elements $-\infty$/$+\infty$. Their `floor`
   (`items.py:618-683`) makes the readout a nondecreasing function of the pool, which Table 2 does not list.
   *Paper:* generalize Table 2's presence row to "a nondecreasing function of one sum: $d_k$". That row then covers
   presence, `Positive` with a scale, a pool with a floor, and `Opaque` (6). A pool divided by a sum is a ratio.
4. **Some of the contribution functions' properties come from the corpus, not from their form.** Definition 9 says the
   direction depends only on the contribution functions. The code reads, from the term vocabulary collected over the
   corpus (`Vocabulary`, `reach.py:490-607`):
   - which entries each kind can touch (`KindProfile.terms`);
   - which counts every item of a kind carries (`_unconditional`, 760-763), which is Table 3's "fixed, same key";
   - the sign of an added slot value (757);
   - the `Min` floor shortcut (920);
   - hashed signedness (569-572, conservative when undecided).

   The signs of count, add, hashed, and split terms are guaranteed by `Term`'s validation (`items.py:155-160`), so in
   practice only the supports and the unconditional counts rest on data. Theorem 1's corpus-checked hypothesis
   (decision 2) therefore covers the vocabulary as well as the write operations' signatures, and it does so for every
   operation, the declared ones included. The existing check already covers both (the 100- and 2,000-file tables are
   identical). *Paper:* §4's sentence for decision 2 names both. No code change.
5. **A write onto a locating position is flagged in the directions, not declined.** Proposition 1 declines such a write
   (`predict`, `reach.py:226-230`). The directions instead give it the change `flag`: any addition, removal, or
   replacement of items of that kind (`region_changes`, 861-863). Three in-place writes declare their change instead
   (`REGION_OPS`, `catalogue.py:216-231`):
   - `ren` keeps the sections;
   - `rdb` grows or adds the overlay and rewrites the file;
   - `rsg` removes the certificate table.

   Decision 1(c)'s "declines to predict a write that lands on one" fits Proposition 1 only. *Paper:* §4's template (c)
   states both behaviours and the three declarations.
6. **Append's signature is declared, not collected.** The remark after Definition 7 (`_d_framework.tex:343-345`) gives
   "appending any content" as the example of an operation whose changes come from the item tables. In the code, `app`
   is declared by hand, like `sec`, `imp`, `ext`, and `shf` (`declared_changes`, `catalogue.py:325-401`). G7 checks
   these declarations by re-extraction. The strict variant's past-end flags are checked against the corpus
   (`past_end_kinds_undeclared` = [] on 2,000 files, run 107). Only the seven in-place writes (`slk dos hdr chk ren rdb
   rsg`) are collected from item tables: per file in `file_region_changes` (`catalogue.py:299-313`), then unioned over the
   population's files (`scripts/a_directions.py:398-404`). *Paper:* change the example to an in-place write, for
   instance overwriting slack or header fields, and list append among the declared operations in §4. Deriving append's
   signature from `open_end` items and past-end locating ranges would be new machinery for no change in the table.
7. **A threat model's table is the union of its operations' tables** (`scripts/a_directions.py:135-145`), where
   Definition 10 uses one signature for the whole model. Under the paper's rules, which all distribute over unions, the
   two agree exactly. Under the code's rules (1, 2), the union of operation tables is equal or finer, and it is sound
   either way. Once 1 and 2 are fixed, the two agree by construction. Optional for §4/§5: a threat model's table is the
   union of its operations' tables.
8. **Replacements are kept apart, as Definition 7 requires** (`Change`, `reach.py:668-704`). The kinds of change:
   - add, remove;
   - modify: a replacement restricted to some families or attributes;
   - rewrite: a replacement of the same length;
   - grow: a replacement by an extension (regex entries up only if `extension_monotone`, as in the appendix);
   - flag: add ∪ remove ∪ replace any.

   Unconditional counts stay fixed under modify and rewrite (802-804, 828-829). No mismatch.

## Readout rule per EMBER feature (item 3 of the task)

| Rule (Table 2) | Code readout | EMBER features |
|---|---|---|
| identity | `Identity`, `Selection` | general size, start; strings numstrings, printables, regex; section counts, hashed size/vsize/entropy/characteristics, entry-name hash (`Selection`: the entry section is a repair, §4(b)), overlay size and flag; imports num_imports, functions; exports hash; header fields and DOS fields; data directories; Rich header; all four sums groups; expert identities |
| presence | `Positive` | exports present (scale 128) |
| distinct count | `DistinctCount` (total and per bucket) | imports libraries |
| ratio | `Ratio`, `Max`/`Min` with `divide_by` | strings avlength; overlay size ratio; max/min section size over file size |
| normalized bin | `Normalized` | byte histogram, byte-entropy histogram, printable distribution |
| any other | `Entropy`, `Lookup`, `BitTest` | general entropy, strings entropy; machine, subsystem; characteristics flags |
| not in Table 2: pool | `Max`/`Min` (finding 3) | max/min section entropy, max/min vsize ratio |
| not in Table 2: one item's value or its default | `Opaque`, with declared ranges | is_pe; has_relocs, has_dynamic_relocs; the authenticode features; expert DOS-stub and resource flags |
| outside the class | `Outside`: both always | pefile warnings (no items) |

`Opaque` matches Table 3's "a value in [l, u]" row if the item is taken to contribute value − default to an additive
slot. The code uses only declared ranges here, never the corpus fallback.

## Follow-up (same day): findings 1-2 fixed

Fixed with the user's approval: `ratio_signs` is now $d_a \cup (-d_b)$, and `Normalized` uses the ratio rule with the
family's total, both as Table 2 states them. `tests/test_reach.py` was updated and gained a ratio test. Re-derived
into the scratchpad with the new code: the pilot tables behind Table 7's detectors (`a_directions_derived_v2`,
`a_directions_derived_sums_v2`) and the 2,000-file table of runs 117-118 (`a_directions_derived_sums_2000_v3`). Each
differs from the stored one only in `directions_sums.csv`, in the two cells above. Every threat-model column and every
monotone/neutralize file is byte-identical, so the detectors' constraints and Tables 6-7 are unchanged. G7 on the pilot
against the tightened table passes (0 violations; 476 add-section and 424 add-imports edits). The stored artifacts
were left as they are: they differ only in those two cells, and the scale-up re-derives everything.
