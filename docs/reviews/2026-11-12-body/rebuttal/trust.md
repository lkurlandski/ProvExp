# trust: R2

## The deciding questions

**1. Would a multi-byte marker probe (MZ, `PE\0\0`, Rich/DanS, magic values) find a write that changes which items
the parser finds without touching a recorded locating position?** I did not run the probe: reading the code already
answers the question, so the probe would not decide anything. pefile checks multi-byte content in only a few places:
- the DOS and NT signatures (`pefile.py:3079-3111`);
- the search for the "Rich" marker (`pefile.py:3380`);
- a section named `PAGE` (`pefile.py:3656`), which only adds a parser warning, a group we drop;
- the CodeView markers `RSDS`/`NB10` in the debug data (`pefile.py:4449`, `:4503`), which feed no feature.

The checks that matter are already recorded: `e_magic`, `e_lfanew`, `Signature` and the optional header's `Magic`
(`features.py:263-268`), and the whole Rich search range, which locates every Rich pair and also locates the empty
case, so a forged block is flagged (`features.py:2373`, `:2380`). signify's certificate parse is a single opaque item
whose members are the whole certificate table (`features.py:2509-2531`). A write inside that table therefore changes
the item's own bytes; it cannot change where an item is found without the record noticing. My hypothesis for the probe
is zero hits.

The reading did find one small gap, which the probe as posed would miss. When pefile finds "Rich", it reads a 4-byte
key just past the marker (`pefile.py:3390`, `:3402`). If the marker ends exactly where the optional header starts,
that key is the optional header's first four bytes: `Magic` plus the two linker-version bytes, which `hdr` writes
(`catalogue.py:211`). Our record stops at the optional header. Hitting the gap needs a file whose COFF header spells
"Rich" (SizeOfOptionalHeader 0x6952). The fix is to extend the recorded range by four bytes, a pure addition to our
`items` code. As far as I can tell the gap could affect a single-edit prediction, never the direction table: on such
a file `hdr` also writes fields that lie inside the recorded range, so it already flags the Rich kind. I have not
checked this on data.

**2. How many test files have a (kind, sum) pair, or an item kind at an overwritten position, that the 2,000-file
vocabulary lacks?** The stored outputs cannot answer this: the derivation keeps only the merged vocabulary
(`scripts/a_directions.py:389-420`), so a count needs one pass that builds the item tables of the test files. The
question also decides less than the triage expected:
- **The attacked files are the sample.** The vocabulary is collected from the same file list the attacks use
  (`a_directions.py:554`; `a1_adaptive.py:1092`, `mab_attack.py:458`, `catalogue_checks.py:524`). Every attacked
  original therefore contributes its own items and overwrite changes, so no §5 number rests on the sample premise.
- **Edited files used as starting points** for further edits pass the direction check (run 142, the copies with a
  section added far, near or inside the file: 0 violations).
- **The premise matters only for files the sample has never seen**, i.e. in deployment.
- **C-Q5's check at inference would inspect the wrong file.** It sees the edited file, which says nothing certain
  about the original the guarantee concerns, and under decision 11 nothing is routed anyway.

**3. Is every in-place write of the catalogue either declined or off every locating position?** No:
- the slack and checksum overwrites never write a locating position;
- the DOS-stub overwrite and the header-field overwrite (`hdr`) do write locating positions on nearly every file:
  both lie in the Rich search range (`catalogue.py:285`, and the COFF fields come before the optional header);
- in those cases the derivation flags the Rich kind as able to change freely (`reach.py:879-881`); it does not
  decline.

So closure does not follow from the locating record, and meta-review §5 item 8 reaches the right conclusion for the
wrong reason. It does follow from what the population check reads. That check (`catalogue.py:426-483`) reads
SizeOfImage, SectionAlignment, SizeOfHeaders, `e_lfanew`, the section table's addresses and sizes,
SizeOfOptionalHeader, the data-directory entries, the file's length, and whether any recorded locating range lies
past the end. The four overwrites write none of these fields (`catalogue.py:208-213`, `:269-287`), keep the file's
length, and can move only the Rich kind's locating range, which lies inside the headers. The check therefore returns
the same answer before and after every overwrite. Closure needs testing only for the declared operations, including
`ent`, `rdb` and `rsg`, which write the two entries the widened check exempts (`catalogue.py:473-478`).

## R2: "sound" rests on tested premises
**Opinion:** change the argument or description (one paragraph naming what the EMBER guarantee trusts and why, the
EMBER claims conditioned on it; plus the four-byte fix to the Rich range in the code)

All four reviewers raise this (A-W1, B-W1, C-W2, D-W1; questions A-Q1, B-Q3, C-Q5, D-Q3). On EMBER, every premise of
Theorem 1 is established by checks, not proofs:
- the instrumentation equals the extractor;
- the declared changes are right;
- the sample vocabulary is complete;
- the locating record is complete (it needed a correction round);
- the population is closed.

So "no edit in the threat model can evade" is, in the reviewers' view, an empirical claim. B puts it most sharply:
the contrast with trial reduces to a hand instrumentation tested by trial against a hand table tested by trial.

Two things hold. The paper never gathers the trusted parts in one place. And the EMBER claims drop the condition, for
example the evaluation's lead (`_f_evaluation.tex:18`); §3's statements (`_d_framework.tex:15`, `:297`) are
conditional theorems and are fine. Half of the criticism, though, restates our own disclosures as a flaw: §4.3.2
already says the overwrite signature "rests on the sample rather than on a proof", §4.4 (Population) that "Closure is
checked rather than proven", and Appendix D (The EMBER Instance) reports the first round of single-byte probing.

The strongest rebuttal is that what we check differs in kind from trial:
- **Trial covers only the edits it tries.** A trial table needs an edit that moves each of 2,568 features under each
  of 12 operations, and a cell where no edit moved the feature says nothing.
- **Our checks test a small set of rules for each kind of item:** contribution functions bit for bit on every file,
  each declaration by re-extraction, the record by comparing parses. A rule that passes covers every edit of its kind
  on every file in the population, and a wrong rule is one fix, made once per extractor.

The three questions above add three facts the paragraph can state:
- for every attacked file, the sample premise holds by construction;
- closure for the overwrites follows from what the population check reads;
- the record covers pefile's marker checks, including the whole Rich range.

**What to dismiss.**
- *A's request for sound read sets by dynamic taint* reopens decision 2 (checked, not proven, is acceptable; the proof
  carries the weight). Taint gives the bytes one run of the parser reads, misses dependencies through control flow,
  and would not prove anything either.
- *A's locality hypothesis in §3* is R17's fix, which the user rejected in session 53.
- *Lines of code, and error counts before correction compared with the hand table:* no effort or fix-round claims.
- *D's malformed corpora:* such files mostly fall outside the population, where the paper already says the guarantee
  is measured, not proven.

**Calibration.** I would propose this paragraph without any reviewer. The paper's central contrast is computation
against trial, and a security reader will ask what the computation trusts. The objection does not attack a claim we do
not make, but half of it restates our own disclosures.

**The smallest change.** One paragraph of about 120 words at the end of §4.4 (Population). It lists the trusted parts,
each with how it is checked and with R13's counts (item kinds, declarations, recorded rules), and states the three
facts above. Then "cannot be evaded" in §5's lead becomes "on the population, given the checks of §4". The four-byte
fix goes into the record before the scale-up's recount; I expect no direction to change. The multi-byte probe is not
needed: reading the code answers A-Q1 and D-Q3 more strongly than a probe would, and the probe would miss the one gap
the reading found.

Cost: a paragraph and a one-line code change. Without it, all four reviewers' shared point stands unanswered, and so
does B's "trial against trial" reading of the paper's main contrast.
