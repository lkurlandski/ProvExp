# §4 working note: what an instance supplies (2026-11-09, session 27)

Working note for drafting §4 Instantiating the Framework in blocks (PLAN.md, decision 8 and next step 3). Archive it
once §4 is accepted.

## What §3 takes as given, and which part of §4 supplies it

| §3 needs | Where §3 uses it | §4 part | Proven or checked |
|---|---|---|---|
| items, contributions, readouts with $\varphi = \rho\circ\sigma\circ\pi$ | Definitions 1-5 | (a) | checked: the readouts of the recorded sums reproduce the extractor on 2,000 files (one sentence) |
| the features that are not of this form, and what to do with them | the remark after Definition 5 ("a sum-then-readout extractor on the remaining features") | (b) | a choice, argued qualitatively |
| a threat model $\mathcal{M}$ and a signature $\Delta$ that covers it over $Z$ | Definitions 7-8, Theorem 1's hypothesis | (c) | declared changes: checked by re-extraction; collected parts: checked on the corpus (decision 2) |
| a population $Z$, closed under $\mathcal{M}$ | Definition 7, Theorem 1's second part, Corollary 1 | (d) | membership decided per file at inference; closure checked |

## Structure (revised with the user after block 1, session 27)

Lead (four parts, no checks) · 4.1 EMBER and PE files · 4.2 EMBER as a sum-then-readout extractor ((a) + (b)) ·
4.3 Threat model · 4.4 Population · appendix: the EMBER instance. Budgets in `docs/paper-mock.md`, §4. The table
above still says which of §3's assumptions each part supplies; the "checks" column is for us, not for the lead.

## The points each part must make

**(a)** The kinds (scanned: bytes, entropy windows, strings, Rich header; parsed: sections, overlay, header fields,
imports, libraries, exports, certificate table, entry section). The sums: additive counts and totals, one per key of
each hashed vocabulary, and max/min pools (section entropy, size ratio). The readouts: which rows of Table 1 occur
(identity; monotone: exports present, pools with a floor, an item's value with a default; distinct count: libraries;
ratio: average string length, section size over file size; normalized bin: the histograms; any other: entropies,
lookups, flag tests). Two of thrember's features are written as sums by a brief clause (section size over file size:
a ratio of two sums; the library set: a count per library, read by a distinct count). Bit-exact check in one or two
sentences. A detector may read the sums themselves: re-encodings as identity readouts, kept short.

**(b)** How strictly an extractor fits Definition 5, and the options for the features that do not: leave them out
(the remark after Definition 5), or keep them as able to move both ways, which is always sound; a monotone detector
cannot read a feature marked both (Corollary 1), so for a detector the two options coincide. EMBER: 88 parser-warning
flags with no items; absent from EMBER 2017/2018 (VERIFY in Joyce et al.); dropping them costs nothing (run 126).
No mention of the import-overwrite bug.

**(c)** Literature first: the edits the PE problem-space attacks use (a separate pass), our catalogue as the
functionality-preserving, non-code-rewriting ones, exclusions named. Two sources of changes: declared (operations
stated in items, and append), checked by re-extraction; collected from item tables (the in-place writes). Writes onto
positions the parser reads to locate items: Proposition 1 declines; the directions allow any change of that kind
unless the catalogue declares it (rename, remove debug, remove signature). Corpus-collected and therefore checked, not
proven (decision 2): the writes' changes and the kinds' vocabulary (which sums a kind can touch, which counts every
item of a kind carries).

**(d)** The plain-layout population, the membership check, routing, closure (0 of 60,934). The 4 MB truncation stays
as is for now (decision 8 (iv)).
