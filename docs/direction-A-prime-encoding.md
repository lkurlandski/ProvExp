# Direction A', step 4: the edit-choice encoding (design note, 2026-10-30)

Status: **reviewed by the user (2026-10-30); built in `scripts/ap_encoding.py`, tested by `scripts/ap_containment.py`.**
Decisions below ("Decisions"). Implements `docs/feature-provenance-model.md`, Section 4a, C3
(reachable sums and features under add-only edits), for the two edits with exact C1 predictors: append and add-section.
Feeds check 1b and check 2 (`docs/direction-A-prime-mock.md`).

## What this is for, in plain terms

Check 1b asks whether we can *prove*, for a detected file, that no combination of appends and added sections within
the byte budget brings the detector's score below its threshold. The exact solver (Kantchelian's encoding,
`scripts/ap_check0_solver.py`) already proves such statements over a region of feature vectors. Check 0 and check 1
showed that the region decides everything: per-feature boxes (a budget only, or limits learned from attacks) let each
feature move on its own, so the solver combines changes no real edit makes and finds an "evasion" on every file.

The encoding replaces the box with the edit itself. The solver's variables are the attacker's choices (how many bytes
of each value to append, how many sections to add, each one's size, name bucket, characteristics, and content). Every
feature the edit moves is written as a function of those choices, computed from the item table. One choice moves many
features together in fixed proportions (appending zeros raises the size and the zero-byte share and lowers every
other share at once), which is the coupling the boxes lose. If the solver then finds no evading choice, no edit in the
catalogue evades: a certificate. If it finds one, the answer is a list of edits that we write as a file and re-extract
(check 2).

**Soundness is the requirement; tightness is the hope.** Wherever a feature is not an exact linear function of the
choices, the encoding may only *widen* (allow more feature values than the edits produce), never narrow. A widened
encoding can still certify; it cannot certify wrongly.

## Facts from the pilot that shape the design (10% detectors, 50 detected pilot malware)

- What the unconstrained model splits on (31,500 split nodes): byte histogram 27%, strings 21% (96 of the 177 string
  features are the printable-character distribution), byte-entropy histogram 19%, section 8%, imports 7%, header 7%.
  The PV models split mostly on section (39-48%), Rich header, strings, imports, exports.
- The histograms are ratios (count / total). A split "count / total ≤ t" is the same as "count ≤ t · total" because
  the total is positive: **linear and exact**. So the groups the unconstrained model leans on most need no
  approximation at all. Only entropies are truly nonlinear.
- File sizes: quartiles 4 KB / 83 KB / 458 KB / 3.9 MB (the 4 MB cap); the byte budget max(5% of the size, 512 KB)
  exceeds the file's own size on 26 of 50 files. On those, an attacker can more than double the file, so the
  histograms can be pushed close to anything: **certificates are unlikely there whatever the encoding does.**
- 38 of 50 pass the precondition check; 10 have no free slot for a section header (append only); free slots are
  otherwise 3-5+. Alignments: (FileAlignment, SectionAlignment) = (512, 4096) on 39, (4096, 4096) on 8, (512, 8192) on 3.

## The catalogue being encoded (the threat model of the certificate)

The edits, exactly as `scripts/catalogue_checks.py` writes them (our own byte-level edits, never LIEF):
1. **Add up to K sections** (`add_section(..., before_overlay=False)`): each gets a header in the next free slot of
   the section table, its content at the end of the file padded to FileAlignment, NumberOfSections + 1, SizeOfImage
   recomputed, SizeOfCode (code sections) or SizeOfInitializedData (others) raised by the padded size.
2. **Then append** any bytes at the end of the file (they become the overlay).

All added bytes count against the budget B = max(5% of the file's size, 512 KB) (Table A1's protocol). The order is
fixed (sections first, then the append): appending first and then adding a section turns the appended bytes into a gap
between sections instead of an overlay. NOTE: this is a restriction of the catalogue, stated with the certificate; one
extra binary would cover the other order if it matters.

K is a tractability cap (proposed: 3, or the file's free slots if fewer). The certificate then reads "no combination of
at most K added sections and one append within the budget evades".

## The solver's variables

Per file (all integers unless stated):
- `a[v]`, v = 0..255: appended bytes of value v. `A = Σ a[v]`.
- per section slot i = 1..K:
  - `on[i]` (binary; slots fill in order, `on[i+1] ≤ on[i]`);
  - `c[i]`: content length; `m[i]`: raw size in units of FileAlignment, with `FA·m[i] − FA < c[i] ≤ FA·m[i]` (exact
    padding; the raw size `r[i] = FA·m[i]` is what pefile reports as SizeOfRawData, and the padding is zero bytes);
  - `pages[i]`: virtual pages, with `SA·pages[i] − SA < r[i] ≤ SA·pages[i]` (exact, gives each next section's address
    and SizeOfImage);
  - name: one-hot over the 100 (bucket, sign) pairs of the 50-bucket signed name hash, plus "empty name";
  - characteristics: binaries for a menu of loader-safe flags (CNT_CODE, CNT_INITIALIZED_DATA, MEM_READ, MEM_WRITE,
    MEM_EXECUTE, MEM_DISCARDABLE); per chosen flag, a one-hot over the 100 (bucket, sign) pairs its "name:flag" string
    hashes to (see the name relaxation below);
  - `e[i]` (continuous, [0, 8]): the section's entropy, bounded below.
- pooled content counts `s[v]` (all added sections' content bytes of value v; `Σ s[v] = Σ c[i]`).
- strings brought by the new content: number `ns`, printable characters `np`, per printable character `pd[ch]`, per
  regex `rg[j]`.
- byte-entropy windows: new windows per entropy row `w[row]` and their counts per (row, nibble) `we[row, col]`.
- Budget: `gap + Σ r[i] + A ≤ B`, where `gap` is the zero padding from the old end to the first section's aligned
  offset (a constant given `on[1]`).

Products of a binary and a bounded integer (a size counted into the bucket the name chose) are linearized exactly
(standard big-M with the variable's bounds).

## Features that are exact linear functions of the choices

Each is the file's old sum (from its item table) plus what the added items contribute (the C1 delta, now a function of
the choices). A tree split "x ≤ t" on such a feature is linked to its binary by two big-M rows; the split is then
exact, as in check 0.

| Feature (group) | New value |
|---|---|
| general:size, section file size N' | N + gap·on[1] + Σ r[i] + A |
| byte histogram counts (before normalizing) | old + a + s + zeros(padding, gap) + header bytes (below) |
| section counts (num_sections, num_zero_size, num_empty_name, num_rx, num_w) | old + Σ on[i] · [condition on flags/size/name] |
| size / vsize / entropy name-hash buckets | old + Σ_i sign · {r[i], c[i], e[i]} · [name of i hits the bucket] |
| characteristics-hash buckets | old + Σ_i Σ_flag sign · [flag chosen and its key hits the bucket] |
| header: NumberOfSections, SizeOfImage, SizeOfCode, SizeOfInitializedData | old + Σ on[i]; SA·(base pages + Σ pages[i]); old + Σ r[i]·[code] / [not code] |
| strings: numstrings, printables, regex counts | old + ns, old + np, old + rg[j] (each string counts once per regex it matches) |
| byte-entropy counts (before normalizing) | old windows kept + Σ we (+ the rewritten header windows, below) |
| overlay size | A if any section is added, else old overlay + A |

## Ratios: exact, by clearing the denominator

Every ratio in the list has a positive, linear denominator, so its split is linear: "num / den ≤ t" becomes
"num − t·den ≤ 0".
- **Normalized histograms** (byte histogram, byte-entropy histogram, printable distribution): count over total.
- **avlength** (printables / numstrings), **overlay_size_ratio** (overlay / N').
- **max_size_ratio** (largest section or overlay size over N'): "≤ t" means every candidate ≤ t·N' (one row each);
  "> t" means some candidate exceeds it (one binary per candidate).
- **max_vsize_ratio** (SizeOfRawData / VirtualSize per section, maximum over sections): the new section's r[i] / c[i]
  ≥ 1, handled the same way. (The min_* section features are constant zero in thrember: their lists include a 0.)

This is where the mediant and mixture bounds of C3 step 3 would have been used; clearing the denominator makes them
unnecessary inside a MILP. NOTE: the model's C3 text describes a sound *box*; the solver can use the exact polytope
instead, which is tighter. (The model doc should say so once this is built.)

## Entropies: sound linear bounds from concavity

Entropy H(p) = −Σ p_v log2 p_v is concave in the distribution p. Five features read an entropy: the file's
(general:entropy), the strings' (over the printable distribution), the overlay's, each new section's (e[i]; it enters
the entropy-hash buckets and max_entropy), and max_entropy itself.

- **"H > t" side (the tree's right branch):** concavity gives H(p) ≤ H(p₀) + ∇H(p₀)·(p − p₀) for any p₀ (a tangent
  plane lies above a concave function). So "H > t" implies "tangent(p) > t" for every tangent: a linear row after
  clearing the denominator. Use a few tangents (at the current distribution and at the corners of the reachable
  region): sound, tighter with more.
- **"H ≤ t" side (left branch; usually the evasion direction, since malware is high-entropy):** each term −p_v log2 p_v
  is concave in p_v, so on an interval [l_v, u_v] it lies above its chord. Summing chords gives a linear *lower*
  bound of H; "H ≤ t" implies "Σ chords ≤ t". The intervals [l_v, u_v] come from the budget (p_v' between the old count
  over N + B and the old count plus B over N + B). Narrow intervals (budget small against the file) make the chord
  bound tight; wide ones (the 26 files where the budget exceeds the file size) make it loose. If needed, split each
  interval into pieces with one binary each (piecewise chords).
- **Section entropy e[i]** uses the same two bounds on the section's own counts. To keep the variable count down, the
  first build pools all added sections' content (`s`) and bounds each e[i] only by [0, min(8, log2 r[i])], since a
  section's raw data is its content plus zero padding. NOTE: a loosening, sound; tightened (per-section counts with
  the cuts above) only if check 2 shows evasions failing on section entropy.
- **max_entropy** = max(old max, e[i] for added sections, overlay entropy): binaries per candidate, as max_size_ratio.

## The layout bytes an added section brings (modeled, not left out)

Run 109 showed three declared evasions on PV failing because the declared add-section ignored the bytes written into
the header. The byte-level edit writes, per section: the 40-byte table entry (8 name bytes, four 4-byte size and
address fields, 12 zero bytes, 4 characteristics bytes) into a slot that held 40 zeros; and it rewrites
NumberOfSections (2 bytes), SizeOfImage (4), SizeOfCode or SizeOfInitializedData (4). Encoding:
- **Byte histogram:** remove the old values of those bytes (known: zeros and the old fields) and add up to
  40·K + 10 bytes of free values (`hb[v] ≥ 0`, sum fixed by K). Sound: the exact values (the name's bytes, the sizes'
  little-endian bytes) are one assignment of the free ones. Loose by at most a few dozen bytes per file.
- **Byte-entropy histogram:** the one or two 2,048-byte windows that cover the written header bytes are removed from the
  old counts (known) and re-added with free counts: each window contributes 2,048 counts in a single entropy row, the
  row free.
- **Strings:** a run of printable bytes in the table entry (a name followed by printable size bytes) can form, extend,
  or end a string. The strings overlapping the written range widened to the nearest non-printable byte are removed
  (known from the item table) and replaced by free strings bounded by that range's length (C3 step 2's boundary
  generators).
- **SizeOfImage, NumberOfSections, SizeOfCode / SizeOfInitializedData:** exact (table above).

## Appended and added content: the windows and strings it brings

- **Byte-entropy windows** (2,048 bytes at multiples of 1,024): the number of new windows is fixed by the new length
  (integer rows, exact). Their counts are free except: each window's 2,048 counts sit in one entropy row; the nibble
  totals over the new windows are within the boundary slack (2,048 per end) of twice the added content's nibble counts
  (each byte lies in two windows). The old file's last window, which a lengthening can complete, is in the slack.
- **Strings** (runs of 5 or more printable bytes): `pd[ch] ≤ (added bytes of value ch)`; `np = Σ pd`; `5·ns ≤ np`;
  `ns ≤ (added bytes + 1) / 6` (each string needs a terminator); `rg[j] ≤ ns`. A string straddling the old end of the
  file (the old file ends in printable bytes) or a section boundary is one boundary generator each (one merge).
- **Overlay entropy:** the entropy of the appended bytes (plus the old overlay if no section is added), with the
  bounds above.

## Features held fixed, and why (assumptions of the certificate)

- **Groups append and add-section never reach** under the precondition check (no structure located past the end):
  imports, exports, data directories, Rich header, Authenticode (the certificate table stays in place since content is
  added after it, not before), the remaining header fields, the first four bytes. Held at the file's values; G7 (run
  107) checked these directions on all 73,063 edits.
- **pefile's 88 warning flags** (the model reads them, no readout models them): held at the file's values, as in the
  adaptive search (it held on every run-108 evasion). Checked again by the containment test.
- **The entry section's name hash:** an added section does not contain the entry point, and under the precondition
  check the entry section is the one that does. Held fixed; checked by the containment test.
- **Files the encoding does not cover:** files failing the precondition check (12 of 50; no certificate, reported as
  such) and files with SectionAlignment below the page size (none in the detected pilot). Files with no free header slot
  get append only (K = 0).

## The name relaxation (how buckets become a file)

The section name decides, at once, the bucket and sign of its size, vsize, and entropy hashes, and the bucket and sign
of each "name:flag" characteristics string. The encoding lets the solver choose the name's own (bucket, sign) and,
separately, each flag string's (bucket, sign). Sound (every real name gives one such tuple); possibly loose (not every
tuple has a name). Realizing an answer: search 8-byte names for one that hits the chosen tuple (with two or three flags,
about 10⁶ hashes, a second or so); if none is found in a fixed number of tries, the evasion counts as not realized
(check 2), and the encoding is not wrong, only loose there.

## How a solver answer becomes a file

From the solution: K' added sections, each with its name (from the search above), flags, content length c[i], and a
content with the chosen byte counts; then the append with counts a. The contents' byte *order* is free, except that
the strings and windows the solver assumed must exist: lay printable bytes out as ns strings separated by zero bytes,
and the rest in runs that hit the chosen window rows (a greedy layout; failures show up in check 2). Write with
`catalogue_checks.add_section` and plain concatenation, re-extract with `SumsFeatureExtractor`, score.

## The test (before check 1b): the encoding must contain the real file

For every pilot file that passes the precondition check (38 detected malware and, cheaply, the pilot goodware too),
draw a dozen random edit choices (0-3 sections with random names, flags, and content of random size and byte mix from
zeros, random bytes, printable text, and goodware sections; appends likewise), write each with the byte-level edits,
and re-extract. Then:
1. **Exact features:** every feature the table above calls exact equals the re-extracted value (to float32 rounding).
2. **Containment:** with the solver's choice variables fixed to the drawn choice and every split binary fixed to the
   re-extracted vector's side of each split, the program is feasible on each detector. This is exactly the statement
   the certificate needs: the real file's path through every tree is one the encoding allows.
3. **Held-fixed features** (warnings, entry name, the untouched groups) are unchanged.

Any failure is a bug or an assumption to list, as with G1-G7. Hypothesis: the exact features and containment hold on
all drawn edits; the likeliest failures are strings at the boundaries (a printable name next to printable size bytes)
and the pefile warnings (an added section can trigger one, e.g. on its alignment).

## Check 1b, stated before running

On the unconstrained 10% model, among the detected files the battery does not evade (20 of 47), the computed region
must certify at least 20% (4 files). Hypothesis: it certifies a minority, concentrated on the large files where the
5% budget is small against the file (the histograms barely move and the chord bounds are tight); on the 26 small files
where 512 KB exceeds the file size it certifies almost nothing, because the attacker can then set the histograms nearly
freely. If the go/no-go is met only on large files, that is the reading to report, not a reason to change the budget.

## Size and runtime

Per (file, detector): ~19,000 binaries for the splits (as in check 0) plus about 3K·100 + 256·2 + 300 integers and
continuous variables for the choices, and two big-M rows per split on a moved feature. Check 0 decided every solve
within 34 s on a larger region; the choice block adds variables but cuts the region, which usually speeds proofs.
Estimate before any run: the containment test (~40 files × 12 edits, extraction ~1-2 s each, one feasibility solve each)
under 10 minutes on 16 workers; check 1b (20 files × 1 detector, 30-minute limit) possibly over, so it goes to a `run/`
script after a smoke test on 2-3 files.

## Decisions (user, 2026-10-30; both configurable)

1. **Byte budget: Table A1's protocol, max(5% of the file's size, 512 KB)** (`--budget_frac 0.05 --budget_min 524288`).
   Why: every column of Table A'1 (the battery, the budget-only and learned regions, ours) must face the same attacker,
   and the battery's numbers (runs 105, 109) were measured under this budget; one protocol, budgets, and cost measure
   across experiments. Consequence, stated before the run: on the 26 of 50 detected pilot files where 512 KB exceeds the
   file's size, the attacker can more than double the file and steer the histograms almost freely, so certificates
   there are unlikely; check 1b is reported split by file size, and a 5%-only budget is a sensitivity row at most,
   never a replacement. Alternative considered: 5% only (more certificates, but not comparable with the battery).
2. **At most K = 3 added sections** (`--max_sections 3`; fewer when the header has fewer free slots). Why: the
   battery's evasions used at most a few added sections, so K = 3 covers the attacks we compare against, and each slot
   adds ~1,000 variables (name and flag hashes) to the program. The certificate is stated as "no combination of at most
   3 added sections and one append within the budget evades". Alternative considered: every free slot (usually 5 or
   more): a broader certificate, at the cost of slower solves; to revisit if check 1b's solves are fast.
3. **Defaults kept without asking (recorded):** the edit order is fixed (sections, then the append), and the name
   relaxation chooses the name's own hash bucket and its flag strings' buckets independently (sound; realized by a name
   search).

## Built: findings (2026-10-30, third session)

What changed from the design above while building, and why:
- **pefile's warnings are not all fixed.** The containment test found two that the catalogue reaches: "Byte 0x..
  makes up ..." (a byte value above 50% (zero) or 15% (other) of the file: a share test, linear after clearing the
  size) and "Suspicious flags set for section" (an added section both writable and executable; a driver's PAGE
  section is exempt, left free). Both are modeled, with the warning count. The other 85 stay held (checked).
- **Byte histograms are not exact** in the strict sense: the header bytes a section writes are free bytes. Exact are
  sizes, counts, buckets, header fields, the warnings; the containment test checks these on every edit.
- **Entropy lower bound:** the chords alone are vacuous when the budget exceeds the file (each share's range is nearly
  [0, 1]). Added the mixture floor: H' T' >= H T minus a correction for overwritten counts (applied only when a section
  is added or a string dropped), from concavity; exact at zero edit.
- **Whole-number features** (counts, sizes, fields, flags) split as value <= floor(t) or >= floor(t) + 1; shares split
  below one count's share need at least one count. Both remove tolerance slack the solver exploited.
- **Strings:** the old trailing string can only merge into a longer string, and only when bytes are added.
- **Solver numerics** (see `Program.solve`): coefficients HiGHS would drop are folded into widened bounds (an unsound
  exclusion of the real file was seen before this); columns scaled by their bounds; rows by their non-switch
  coefficients; feasibility tolerances 1e-9. With "no edit" fixed, the minimum is 4.05 against the real 4.20 (the rest
  is the entropy relaxations); it was 2.66 before the whole-number rule.
- **Check 1b smoke** (above in `docs/direction-A-prime-mock.md`): 0/13 certified at 300 s. The solver's "evasions"
  do not realize; attribution on one file: byte-entropy windows (true looseness: a new window's entropy row is not
  tied to its bytes) and strings (mostly realization: regex-matching strings the solver counts were not written).

Still open: per-row entropy cuts for the new windows (row r needs aggregate nibble entropy >= r/4, by concavity; Gibbs
cuts at distributions concentrated on each nibble); a piecewise lower bound for the overlay and section entropies
(section entropies are free in [0, 8] today); the realizer.

## Code plan (after review)

- `scripts/ap_encoding.py`: build the choice block from a file's item table and a `catalogue_checks` description of the
  edit menu; attach it to `ap_check0_solver.solve` (a new `region` kind that adds rows instead of a box);
  `realize(solution) -> bytes`.
- `scripts/ap_containment.py`: the test above; `run/111_ap_containment.sh`.
- `scripts/ap_check1b.py` (or a flag of `ap_check0_solver.py`): the certification run; `run/112_ap_check1b.sh`.
- Tests: `tests/test_ap_encoding.py` on fixtures (exact features, one containment case).
