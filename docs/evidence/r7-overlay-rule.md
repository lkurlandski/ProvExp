# R7: pefile's overlay rule, and the decision to use LIEF's (session 55, R7 track, 2026-11-13)

Record of how the overlay rule came up, what was weighed, what was decided, and what stays open. Context: R7 and the
widened population, `docs/evidence/r7-population-escape.md` §7; PLAN.md decision 11 and step 2b.

## 1. How it came up

Step 2b (i) checks that the widened population (the certificate and debug entries' data may lie past the end; `ent`
in M_full) is closed under the threat model and that the computed changes are right (`catalogue_checks.py --loose`,
run 141). Every operation, `ent` included, was applied to the pilot files and to escaped copies of each: both entries
far past the end (`far`), one byte past it (`near`), and the debug extent ending inside the overlay (`inside`).

- **A bug of session 53, fixed:** the loose precondition exempted only the certificate table's items, not the overlay
  and file items located through the debug extent, so a debug entry past the end still failed it. Fixed by exempting
  all of `LOOSE_PAST_END_KINDS`; run 140's table, masks and population (89) were unchanged.
- **Closure failed** (as predicted): pefile starts the overlay after the furthest extent, within the file, of the
  sections *and of every data directory but the certificate's*. An append to a `near` copy brings the debug extent
  back inside and moves the overlay's start; so does `ent` pointing the debug extent into the overlay. The file then
  fails `plain_layout`'s overlay clause.
- **A trial fix failed:** evaluating the overlay clause without the debug entry closed the population (0 of 13,234
  edits left it) but broke soundness on the files it let in: a section added at pefile's (moved) overlay start split an
  unclaimed run and lowered `body_strings`; `rdb` grew the overlay outside its column; Proposition 1's declarations
  raised or erred. Reverted.
- Run 137 had already shown the same mechanism outside the threat model: the architecture entry pointed into the
  overlay (`overlay_entry`) took 22 of 22 files out.

## 2. The questions the user asked, and the evidence

**How does LIEF compute the overlay?** After the furthest section's raw data (`PointerToRawData + SizeOfRawData`);
none when that lies at or past the end of the file; data directories play no part. Checked on files, not from
documentation: on the 100 pilot files, where both find an overlay (46) the start is identical; they disagree on 11
incomplete files (a section past the end: LIEF finds none, pefile counts what lies inside). On 54 copies with the debug
extent pointed into the overlay, pefile's start moved on all 54, LIEF's overlay on none. On the population the two
rules agree by construction (complete files, and the overlay clause excludes directory-set starts). The attack
toolkits place sections at LIEF's overlay; the SANS ISC overlay script uses the last section's end; our own body
regions (`sums.py`) already ignore the directories.

**Would a change move EMBER (thrember) vectors?** Header-only scans of the 2,000 test files and 16 random training
shards (13,925 files below 4 MB):

| Rule | Test files changed | Training files changed |
|---|---|---|
| skip the debug (and architecture) entry | 0 complete (2 truncated) | 15 (0.1%), all incomplete |
| skip every directory | 63 (12 complete) | 228 (1.6%) |
| LIEF's rule exactly | 67 of the 1,670 below 4 MB (4%), none in the population | 511 (3.7%), mostly incomplete |

No complete test file has its overlay set by the debug or architecture entry; the complete ones set by a directory use
import, resource, relocation, load-config or CLR entries.

**Bug or quirk?** Neither: a deliberate design. The directory rule is in pefile since at least 2016.3.28 (the
certificate entry skipped since 2017.11.5; checked in the release sources); PR #670, merged the day of this analysis,
says "Directory data appended past the section data is deliberately not treated as overlay". What is weak about it for
us: it trusts entries the loader ignores, and for the debug entry it measures the debug directory's own table of
records, not the debug data they point to.

**EMBER v2 vs v3.** EMBER v2's extractor (LIEF; elastic/ember `features.py`) has no overlay features at all; it has the
data-directory features (15 x size and address) and `has_signature`/`has_debug` bits. Joyce et al. list data
directories among v3's new categories (inaccurate: v2 has them) and moved from LIEF to pefile for maintenance ("outdated
dependencies"; pefile "well-supported and robust"), not for parsing semantics. pefile's overlay rule came along
incidentally.

## 3. The mechanisms behind R7's escapes

| Mechanism | Examples | With LIEF | With EMBER v2 |
|---|---|---|---|
| 1. a directory entry moves the overlay's start | debug into the overlay; an append after a near escape; architecture `overlay_entry` | gone | gone (no overlay features) |
| 2. data located through an entry lies past the end | certificate, debug, architecture past the end | gone for entries whose data no feature reads; stays for the certificate | same |
| 3. a field the loader ignores is a feature | `debug_size`, `security_size`, SizeOfImage | stays (feature design) | stays |
| 4. signature cloning | the certificate entry pointed at an appended certificate (run 140's cost) | stays (unverified signature) | stays (`has_signature`) |

Only mechanism 1 is a parser matter. Mechanisms 3 and 4 are what the features measure; `ent` covers them at the cost
run 140 measured.

## 4. Options, and the first recommendation's mistake

Claude's first recommendation (session 55) was to keep pefile's rule and model it on our side: an exemption in the
overlay clause, a placement rule for added sections, an `rdb` case, declines in Proposition 1. It treated pefile's
behaviour, the stock extractor and the 2026-10-27 decision (keep pefile's past-the-end handling) as constraints. The
user: pefile is not the gold standard for what an overlay is; the framework and findings should not be tied to one
parser's implementation details; parsing, feature design and sample selection may change where worthwhile; the options
were not weighed equally. Reweighed:

| Option | Removes | Cost | Verdict |
|---|---|---|---|
| (a) LIEF's overlay rule in our extractor (pure addition) | mechanism 1; the overlay clause, `rdb`'s per-file case and the loose overlay flags become vacuous | ~4% of rows outside the population change; a sentence in the paper | **chosen now** |
| (b) the whole extractor on LIEF | as (a) | re-instrument the item layer and rerun every check; LIEF's own behaviour and version drift | **to weigh carefully** (§6) |
| (c) EMBER v2 features | mechanism 1 | 3 and 4 remain; older; loses v3 groups behind Table 3 (Rich header rows); re-instrumentation | no |
| (d) keep pefile's rule, model it | nothing | ties population and catalogue to pefile; escapes through other entries stay | no |
| (e) pefile's rule minus the debug entry | the debug case only | ad hoc; the architecture and other entries stay | no |

**The test of (a)** (scratch: pefile's method replaced at interpreter start; 50 pilot files with their `far`, `near`,
`inside` copies; 15 min): closed (0 of 6,812 edits on passing files leave), sound (0 violations), exact (1,767 exact,
1,618 declined, 0 wrong). The loose table re-derived with the rule: every M_full mask (and control) byte-identical to
run 140's; three cells of the strict `ren` column change. The declines are almost all on the `far`/`near` copies
(locating ranges past the end): Proposition 1 abstains on escaped files, and the directions cover them.

## 5. Decision (user, 2026-11-13)

Option (a) now, as a quick patch to keep the research moving: `features.overlay_data_start_offset` installed in pefile
at import (like the directory guard), pefile's original kept as `PEFILE_OVERLAY_START`; `overlay_extents_locating`
kept as a sound superset (to tighten with the redesign); tests `TestOverlayRule` and the rewritten
`TestPlainLayout::test_overlay_past_last_raw_data`. Run 140's table refreshed (masks unchanged; the `-loose` models
stand). Run 142: the full-pilot check (user). Stores: the affected rows (outside the population) are re-featurized with
the scale-up; pilot numbers are redone there anyway. `docs/upstream-issues.md` item 9.

Paper, when R7's text is written (step 2b (iv)): Appendix D's "The overlay starts where the last section or data
directory ends, so the extent of every section and directory locates it" becomes "... where the last section ends, so
the extent of every section locates it"; one sentence by "We drop the warnings" on the deviation and why; §4's "Bytes
after the last section form the overlay" becomes literally true.

## 6. The larger question: an extractor designed, not patched

The user's view (2026-11-13): we use EMBER-2024 files below 4 MB, drop the parse-warning features, patch thrember's
quirks, and now change pefile's behaviour; each is reasonable, but together we can no longer claim to "use" EMBER-2024
as is, and the work has felt like battling the parser and the extractor. Approach it directly rather than reactively,
perhaps as an extractor "inspired by" EMBER v2 and v3 with deviations that remove specific problems; consider moving to
LIEF (native, faster, 1.0 with a stable API promised, though 1.0.0 brought many bugs per its maintainers) once a 1.x
release fixes them.

Claude's view, recorded for the decision:

- **What we still use.** The EMBER2024 *corpus* (binaries, labels, splits; files below 4 MB), not the released
  *extractor*. Precise wording: "the EMBER2024 corpus, with an extractor derived from EMBER-v3".
- **The nuance.** Part of the paper's credibility is that it analyses an extractor someone else designed; "inspired by"
  invites "did you design the features to suit your guarantees?". Stay as close to v3 as possible and justify every
  deviation by a principle stated once; a deviations table in Appendix D and the unconstrained detector's accuracy
  matching v3's answer the reviewer.
- **Proactive principles** (each current deviation falls under one): (1) structures are located as the loader locates
  them (the overlay is the unmapped tail); (2) features describe the file, not the parser's diagnostics (warnings
  dropped); (3) known aggregation bugs are fixed (the import merge). Audit the extractor against them in one pass
  instead of finding issues one at a time. The 4 MB restriction is sample selection, apart.
- **(b), LIEF, weighed.** For: native speed, a stable 1.x API, the toolkits' parser, the common overlay definition.
  Against, and the larger cost: the framework needs every byte the parser reads to locate a structure; pefile is Python,
  so the record was read off its code and verified by G5; LIEF reads in C++, so the record would be rebuilt from its
  source or by byte-flip probing. Parsing is likely a modest share of our runtime (features, item tables, prediction are
  Python): measure before counting on speed. Any parser has heuristics; a principle such as (1) is what decides when we
  override and when we model.
- **Timing.** The cheapest moment for any extractor change is before the scale-up's featurization; after it, everything
  reruns. Decide on (b) or a redesign before launching the scale-up. A short spike would inform it: parse the pilot
  with LIEF, compare structures with pefile, time both, list which locating positions LIEF exposes.

## 7. Run 142, and what stays open

- **Run 142 read (session 56).** On all 100 pilot files with LIEF's rule: closed (0 of 13,326 edits on files in the
  population leave it; the 89 originals in it and all 89 `far`, 89 `near` and 46 `inside` copies), sound (0
  violations), and exact after one fix: 3,583 exact, 3,217 declined, 0 wrong. Before the fix 16 declared edits raised
  an error instead of declining, all on one file's `far`/`near` copies inserting a section or imports before the
  overlay: its certificate table lies inside `.rsrc`, and the escape stretches it past the end, across the overlay's
  start, where the insertion lands. The catalogue declared the table moved; the engine now declines an insertion that
  splits an item's members (e0fa5b8; re-run on that file: only those 16 rows change). Details in the script's header.
- Mechanism 2 for entries no feature reads: the population requires every directory within the file; requiring it
  only of directories whose data a feature reads would close the architecture (and reserved) past-the-end exits. A
  separate, checkable refinement.
- Mechanism 4: only features that verify the signature would remove signature cloning; that needs chain trust (a
  self-signed signature verifies too), so it depends on the environment and the date. Not proposed now.
- The escape search at the scale-up should score, end to end, writes to other entries the loader may ignore
  (architecture, delay-import, reserved).
- The extractor question (§6), before the scale-up.

Sources: pefile PR #670 (github.com/erocarrera/pefile/pull/670), issue #378, PR #254 (open); elastic/ember
`ember/features.py`; SANS ISC diary 31268; Joyce et al. 2025 (EMBER2024), §3.2 and the implementation paragraph.

## 8. The LIEF spike (session 62, 2026-11-14)

Scratch script (not kept): the 100 pilot files parsed by pefile (with LIEF's overlay rule installed) and by LIEF 1.0.0,
structures compared after normalizing presentation (LIEF lists Rich entries in reverse; pefile names well-known
ordinals through `ordlookup`; NUL padding in section names). Hypothesis: sections and directories agree on all files,
imports and exports on >95%; LIEF parses >=10x faster; pefile's parse is <30% of our per-file time. Held.

- **Structures:** identical on 99 of 100 files (sections, data directories, imports, exports, overlay size, Rich pairs,
  entry point). The one difference: `85a9da0f439b...` has 14,707 imports in 21 libraries; pefile keeps 280 in 8,
  because it stops at `MAX_IMPORT_SYMBOLS` (8,192) and skips every later descriptor. Signatures: 30 files have a
  certificate entry; LIEF parses a signature on 25, pefile/signify on the same 25 (the other 5 lie past the end or do
  not parse in either). LIEF 1.0.0 logs "Failed to parse X509 cert" on some signed files.
- **Timing (per file, mean / median):** pefile parse 29 / 5 ms; LIEF parse 0.8 / 0.4 ms; our feature vector (incl.
  pefile's parse) 104 / 21 ms; our item table 148 / 31 ms. Parsing is ~12% of features plus item table (~25% if the
  item table parses again); the rest is our Python.
- **pefile's defensive caps** (none modelled by the instance): imports 8,192 symbols (shared with delay imports),
  sections 2,048, export symbols 8,192, resource entries 32,768 and depth 32, strings 1 MB. Our `imp` and `sec` keep the
  existing descriptors and sections first, so crossing a cap truncates only added content: no feature falls (no
  soundness hole found), but the declared change is then wrong (exactness). An audit item.
- **Reading:** a parser switch buys little speed and agrees on structure where it matters, at the cost of rebuilding
  the locating record (pefile.Structure offsets throughout `features.py`) and losing the bit-exact match with the
  released EMBER2024 vectors. The caps are the kind of parser behaviour a deliberate audit (§6) would catch.

## 9. The escape audit against the widened population (session 62, 2026-11-14)

Triage R7 question 2 (`rebuttal/triage.md`): run 137 audited loader-ignored writes against the *strict* population;
does the *loose* widening (`ent` = security + debug entries exempt) open a new in-population escape? Scratch script
(not kept; `passes_precondition(..., loose=True)` only, no extraction, no execution): 100 pilot files, 89 in the loose
population, nine other data-directory entries (export, exception, architecture, global-ptr, tls, load-config,
bound-import, delay-import, com), each pointed past the end, pointed at `SizeOfImage`, and zeroed.

- **Every "past the end" write takes all 89 out of the loose population; "at image" takes 70 of 89 out** (the rest map
  into a section, so they do not trip `directory_past_end`). Same as run 137 for the strict population: the loose
  precondition still rejects these writes through `directory_past_end` / `vrange_beyond_image` / `image_too_large`.
- **Only the `zero` writes stay in-population** (0 of 89 left). But zeroing a directory entry is either a no-op (the
  entry is already 0) or removes a structure the loader uses (tls callbacks, load-config, imports), so it is not a
  loader-ignored, functionality-preserving write. The genuinely loader-ignored entries are certificate (4) and debug
  (6), already in `LOOSE_ENTRIES`, and architecture (7, reserved on x86/x64), whose feature (`copyright_*`) a nonzero
  write only *raises* from 0.

**Reading:** the widening introduced no new free bypass. Loader-ignored entry writes leave the loose population exactly
as they left the strict one; with no router, such a file is scored by the same monotone detector, which run 143
measured holds under the three escapes (cert, debug, image_size). The scale-up's active escape search (§7, and
PLAN.md step 3) should still *score* end-to-end the writes that leave the population through other entries, since
"measured outside the population" is the claim there, not "proven". Note the ~12% of entry writes that point an entry
into the image and stay in-population: outside the threat model, not a soundness counterexample, but a cheap scoring
item for the scale-up.
