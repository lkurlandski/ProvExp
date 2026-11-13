# R7: leaving the population (the routing bypass)

Started in session 48 (2026-11-12), from the simulated review of 2026-11-12 (`docs/reviews/2026-11-12-body/`). This
document holds the analysis, the options weighed, the decision, and the runs. Update its log as the work goes on. R7 is
the top risk of that review's register (meta-review, §6).

## 1. The problem in plain words

The guarantee (Corollary 1, *Monotone detectors*) holds only for files in the *population*: complete PE files with a
plain layout (§4.4, *Population*). Until now a deployed monotone detector sent every other file to the unconstrained
detector, which has no guarantee and which our attacks evade about half the time (run 127: 25 of 49). An attacker who
can move a file out of the population therefore gets the weak detector instead of the robust one. Three of the four
reviewers (B, C, D) made this their "one change". A raised it too, and so did the meta-reviewer, which found in the
code that one 4-byte field write is enough.

## 2. Why the limitation exists

- **The direction table is computed once, from how each operation changes the items.** That is valid only if every
  file reacts to an operation as declared. Two kinds of files do not:
  - **Incomplete files** (something the parser locates lies past the end of the file). An append can fill that range,
    so the parser finds a structure that was not there before, a side effect the append's declaration does not state.
    Example: a certificate entry that says "the signature is at byte 2,000,000" in a 50 KB file.
  - **Unusual layouts** (`catalogue.plain_layout`). Examples: SizeOfImage larger than the sections need, where adding
    a section and recomputing SizeOfImage *lowers* it; a section's raw data inside the headers; the overlay starting
    at a data directory's extent.
- **The population** (`catalogue.precondition`) is the set of files where neither happens, so the table is provably
  right there.
- **Theorem 1 also needs the population to be closed**: no operation of the threat model takes a file out of it (checked
  on 56,902 edits). Closure says nothing about edits *outside* the threat model.
- **The fallback.** A table that holds on every file (the "strict table") marks 2,559 of 2,568 features lowerable, so
  a monotone detector built from it has almost nothing to use (session 46). The design therefore routed files outside
  the population to the unconstrained detector, the best detector without a guarantee. The text justified this by
  "such files are rare among benign software, and so stand out" (§5.4, *Where the guarantee holds*). That argument
  fails at the operating point: 1.5% of benign test files lie outside the population, above the 1% FPR budget.

## 3. What the review found

- **Reviewers.** B-W3, C-W1, D-W2 and A-W4 (questions B-Q2, C-Q1, D-Q1, A-Q3): the routed system is never evaluated end
  to end. A malware author can start outside the population or step out of it. Flagging every outside file costs
  1.5% FPR, more than the whole budget. The 89% placeholder needs a denominator (D-W2).
- **Meta-reviewer (verified in code).** `precondition` rejects a file if any data directory extends past the end of
  the file, the certificate entry included (`catalogue.py:453-457`). The certificate table is never mapped by the
  loader, so one field write that the loader ignores takes any file out.
- **Severity.** The meta-review rates it fatal if a loader-safe one-field write leaves the population and the paper
  does nothing; otherwise major.

## 4. The escape audit (run 137, session 48)

`scripts/escape_audit.py`, `run/137_escape_audit.sh`. Method: 150 population files below 4 MB (93 benign, 57 malware)
from the 2,000 test files. One field write per file, then the population check again. Byte edits only; nothing is
executed (settled: no sandbox execution). Whether Windows still loads each written file is argued from Microsoft's
PE format documentation (learn.microsoft.com/en-us/windows/win32/debug/pe-format).

| Write (at most 8 bytes) | Files that left | Check it trips | Does the loader accept it? (documentation) |
|---|---|---|---|
| Certificate entry extended or placed past the end of the file | 150/150 | item and directory past the end | Almost certainly: "These certificates are not loaded into memory as part of the image … the first field … is a file pointer instead." |
| SizeOfImage raised by one SectionAlignment | 150/150 | image too large | Very likely: the stated rule is only "must be a multiple of SectionAlignment" (still met); the loader reserves more address space |
| Debug entry extended or placed past the end | 150/150 | item and directory past the end | Likely: certificate and debug data sit at the end of the file "because the loader does not map these into memory" |
| Reserved architecture entry (index 7) pointed past the end | 150/150 | item and directory past the end | Probably, but the specification says it "must be 0" (the weakest of the five) |
| Architecture entry pointed at the overlay | 22/22 (the files with an overlay) | overlay at a directory | As the previous row |
| Control: the last section's raw size past the end | 150/150 | section and item past the end | Probably not (the loader reads section data) |

Real data shows the same state: 6 test files below 4 MB are outside the population only because of a dangling
certificate entry (run 136).

**Conclusion.** The escape is cheap and has several routes across at least three clauses (directories past the end,
image too large, overlay at a directory). Patching clause by clause would be whack-a-mole with PE special cases.

## 5. The options weighed (session 48)

Likelihoods are Claude's estimates. "Closes" means how far the option closes the hole; "Reviewers" means how likely
it is to satisfy B, C and D.

| # | Option | Strengths | Weaknesses | Closes | Reviewers |
|---|---|---|---|---|---|
| 1 | **Drop the router: the monotone detector scores every file** (proven on the population, measured outside) | Removes a component instead of adding one; leaving the population no longer hands over a weak detector, only the few out-of-table side effects; reviewer A proposes it; the detector's 1% FPR threshold already covers every benign test file, so the system's FPR is the detector's | No proof outside the population; the one toolkit evasion of each monotone detector so far was on an incomplete file (with the router, though); slightly lower detection on outside files | medium-high | medium; high if the escape attack measured end to end rarely evades |
| 2 | Flag every outside file as malware | Cleanest story; being outside is a malware signal (about 11% of malware, 1.5% of benign) | 1.5% benign outside is above the 1% budget on its own, far above 0.1% | high | low |
| 3 | Keep the unconstrained fallback at a stricter threshold, system FPR held at 1% | Small change; uses the signal | The fallback is still evaded by the same attacks | low | low |
| 4 | Canonicalize before extracting (e.g., read a certificate entry past the end as absent) | Closes specific escapes exactly; keeps the proof | One rule and argument per triggerable clause (PE special cases); the features are no longer stock EMBER on those files; does not cover files built incomplete in a way that cannot be undone | medium | medium ("and the next clause?") |
| 5 | Widen the population for the triggerable clauses (e.g., certificate features made two-sided under append) | Keeps a proven guarantee for those files | Narrow clauses only (all incomplete files give the strict table); re-derivation, more machinery | high for the clauses covered | high for those |
| 6 | Report the end-to-end number and state the limitation | Honest; needed in any case | Alone, the bypass stays | none | low alone |

## 6. Decision (session 48, agreed by the user)

1. The escape audit first (done, run 137: §4).
2. **Option 1 plus option 6 as the default:** no router; one monotone detector scores every file. The guarantee is
   proven on the population and measured outside it, with an escape attack evaluated end to end.
3. Option 5 only if the audit finds one or two cheap escapes that the monotone detector handles poorly in a pilot.

Why: the audit found several routes, which rules out patching clause by clause (4, 5 as the main fix). Option 1 is the
simplest design (the user's preference for less machinery: memory `constrain-experiment-complexity`), and it removes
the free downgrade. Its claim, if run 138 holds: *proven on the population, measured outside it, and leaving the
population gains the attacker little.*

Not yet written into the paper; it waits for run 138. When it is: §4.4's last paragraph (no routing; files outside are
scored by the same detector, without the proof), §5.4's *Where the guarantee holds* (drop "stand out"; the escape
result; the population share as n/N), and the detectors' description in §5.1 if it mentions routing.

## 7. The pilot (run 138)

`run/138_escape_pilot.sh` (to be run by the user; about 5-6 h with 16 workers). `scripts/a1_adaptive.py` gained
`--score real` (every candidate written by our own edits and extracted with the sums extractor; nothing declined, so
the header-field overwrites are used too, which also answers part of R1) and `--escape` (a write from
`escape_audit.WRITES` applied first; only files it takes out are attacked).

- **Setup.** The 50 pilot malware, escaped by the certificate entry (step 1) and by SizeOfImage (step 2). The beam
  search over all twelve operations, up to 2,000 candidates per file, 1% FPR thresholds. Detectors: Table 5's
  unconstrained detector (`seed-0-s10-ref`, where the router would send the file, so its result is the routed
  system's), and the monotone detectors on the features and on the sums (`seed-0-s10-mfull-{feat,sums}-pre-v2`).
- **Hypothesis (fixed before the run).** The monotone detectors are evaded on few escaped files (0-3 of about 40 each;
  their largest score drop small), because leaving the population opens only the side effects the table does not
  cover. The unconstrained detector is evaded on about 40-50%.
- **Smoke (session 48).** 3 files, certificate escape, 300 candidates: unconstrained 1 of 2 evaded; both monotone 0
  of 2, largest drop exactly 0. About 0.6 s per candidate.
- **Reading the result** (decided after the run, per memory `interpret-after-run`). Reference points: the hypothesis
  above; the unconstrained row is the routed system under escape. If the monotone rows evade on several files, look at
  which out-of-table side effect did it (the certificate range filled by an append; SizeOfImage lowered by adding a
  section) and weigh option 5 for that clause.
- **Left for the scale-up.** The toolkit attacks on escaped files (their harness needs its own escape support);
  the end-to-end share "still detected out of all attacked" per attack column; the population share of attacked
  malware with its denominator (the blue 89%).

## 8. Log

- 2026-11-12 (session 48): R7 explained to the user, options weighed, decision agreed (§5-6). Run 137 (escape audit)
  run and read (§4). `a1_adaptive.py` extended (`--score real`, `--escape`), smoke-tested; run 138 scripted for the
  user.
- 2026-11-12 (session 49): no change to R7; run 138 still running at the end of the session. The parallel line R1
  (MAB-Malware, run 139; PLAN.md decision 12) touches 5.4's *The price*, *The width* and *Beyond the guarantee*, not
  *Where the guarantee holds*.
- 2026-11-12 (session 51): run 138 still on step 2 (step 1's summary as in the resume prompt: monotone 1/41 and 1/43
  with drops of about 3 logits; not yet read). Evidence from run 139 for decision 11 (no router): MAB-Malware never
  lowered either monotone full-model detector's score on any file, including the 12 (features) and 11 (sums) detected
  files outside the population, in ~2,400 actions each, among them its removals of the debug and certificate entries
  (which also zero the data the entry pointed to). It shows that unrouted files outside the population are not evaded
  by these actions; it does not cover the deliberate escapes of run 138.
