# Resume: §4 Instantiating the Framework, block by block in the new structure

Read `docs/status.md` and `PLAN.md` (especially decision 8, (i)-(v)). Then `docs/paper-mock.md`, §4 (the agreed
structure and budgets) and `docs/instances-note.md` (what each part must say). Open other documents only as the task
needs them (index: `docs/README.md`). Use the `paper-prose` skill; read the user's reaction to block 1 at the end of
`docs/writing-spec.md` before writing.

**Numbers.** Check `manuscript/main.aux` before naming any section, definition, or table number, and give its title
alongside ("Table 1, Direction rules of the readout forms"). Show concrete old/new text, never a figurative name for
an edit.

## How we work (as in Sound Directions round 4, which the user found very effective)

One block of a few paragraphs at a time, written into `manuscript/_e_instances.tex`, then `make` and `make check`,
then shown to the user as rendered text (pdftotext) with what changed. Apply the user's comments before the next
block, and log their reactions raw in `docs/writing-spec.md`. Commit after each accepted block. The body is about
1,000 words (may run 50-75% over while drafting); report the length honestly.

## State of `_e_instances.tex`

Block 1 of the old structure is in place (lead, the EMBER paragraph, §4.1 Items, Sums, and Readouts, the paragraph
on reading the sums). The user's verdict: §4.1's content and style are "quite good", but it is bookkeeping and too
bulky for the body; the lead is verbose and must not spotlight checks; the EMBER paragraph needs ~30% more and its own
subsection. Below it: the old locating-positions paragraph and the old repairs, commented out (material for 4.3 and
the appendix), then the old catalogue subsection and Table 2 (still rendered; §5 cites the table).

## Block 1 (redraft): the lead, 4.1 EMBER and PE files, 4.2's first paragraph

1. **Lead (~50 words):** the four parts an instance supplies, in one or two sentences, in §3's terms; another domain
   supplies the same four. No checks, no tour of the subsections.
2. **4.1 EMBER and PE files (~170), its own subsection.** The paper's first mention of PE files and malware detection.
   What a PE file is (headers, section table, sections, import table, the overlay after the last section); EMBER
   (`anderson2018ember`, `joyce2025ember`) as the standard benchmark for static malware detection, its feature groups;
   instrumented without changing what it computes (each feature group gains a method returning its items from the
   same parse). Check §2 (`_c_background.tex`) for what it already says, so as not to repeat it.
3. **4.2 EMBER as a sum-then-readout extractor, paragraph 1 (~150):** the gist of the accepted §4.1 text: two
   families of items (scanned, parsed), additive sums with one per hashed bucket, a few pools, and every row of Table 1
   occurs (details in the appendix). End with the one-sentence bit-exact check (2,000 files, 2,480 features), the
   only place the code check appears in §4.
4. **Appendix stub, "The EMBER instance"** (new file after the proofs appendix, `\input` in `main.tex`): move the
   accepted §4.1 sentences there nearly as they are (the user liked them): the kinds, the readout forms with EMBER's
   examples (a small table, Table 1 row -> EMBER features, from `docs/evidence/code-audit-sound-directions.md`,
   "Readout rule per EMBER feature"), the two rewrites, and the re-encodings over sums. Keep the label
   `sec:instances:sums` resolving (§5 cites it) or update §5's reference.

## Then, one block each

- **Block 2, 4.2 paragraph 2:** how strictly EMBER fits and what to do with features that do not (rewritable without
  changing a value; no items at all: the 88 parser warnings, drop them or keep them as both, which coincide for a
  monotone detector; absent from EMBER 2017/2018, verify in Joyce et al.; dropping them costs nothing, run 126: +0.1
  points TPR at 1% FPR). Never mention the import-overwrite bug. One sentence on the re-encodings if not placed in 4.2.
- **Block 3, 4.3 Threat model, literature first.** First a modern literature review of adversarial malware
  (user, 2026-11-09: "a more modern, up-to-date literature review ... with an emphasis on works published in reputable
  venues. The papers you've listed are basically all workshop papers"). Scope: problem-space attacks on, and defenses
  of, malware detectors, emphasis on Windows PE, roughly 2019 onwards; Android and other formats where they set the
  standard for threat models (Pierazzi et al.). Venues: IEEE S&P, ACM CCS, USENIX Security, NDSS, EuroS&P, AsiaCCS,
  ACSAC, RAID, and journals (TOPS, TDSC, TIFS, Computers & Security); preprints and workshops only when heavily used
  (as the toolkits), and marked as such. Record per work: venue and year, the edits it applies (problem-space
  operations), what it attacks or defends, and whether it keeps functionality (and how it checks). Output: an
  evidence record in `docs/evidence/` with the edits-by-work table, verified against the papers (PDFs in `papers/`;
  ask the user to add what is missing, or read the publisher/arXiv version and mark it), and `main.bib` entries from
  real records. Show the user the table and what it implies for the catalogue (which edits the literature uses that
  ours lacks, which of ours it does not use, what we exclude and why) before any prose. The current §4 cites
  `demetrio2021adversarial` (TOPS), `song2022mab` (AsiaCCS), `kreuk2018deceiving` (arXiv), `suciu2019exploring` (SPW);
  already in `papers/`: Demetrio et al. 2021, Lucas et al. 2023 (USENIX Sec.), Dyrmishi et al. 2023 (S&P), Pierazzi
  et al. 2020 (S&P), Rosenberg et al., Labaca-Castro et al., Gimenez et al. 2025 (IFIP SEC), Bostani and Moonsamy, Li
  et al. (PAD). The review may run as its own session if it is large. Then audit findings 4-6
  (`docs/evidence/code-audit-sound-directions.md`): corpus-collected vocabulary and write signatures (checked, not
  proven; one sentence), writes onto locating positions (Proposition 1 declines; directions allow any change unless
  declared: rename, remove debug, remove signature), append declared.
- **Block 4, 4.4 Population:** plain layouts, membership at inference, routing, closure (0 of 60,934); the 4 MB
  truncation as is (decision 8 (iv)).

After §4: §5 Evaluation in blocks (PLAN.md, next step 3), then the next full simulated review with the truncation
brainstorm just before or after it (PLAN.md, step 4).
