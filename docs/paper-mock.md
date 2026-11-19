# Paper mock (rewritten 2026-11-09, after the holistic review; layout accepted provisionally by the user, to be judged
# once §4-5 are written)

At most two pages. It decides what the paper contains; what is not listed here stays out. Written against the
manuscript's new §3 and PLAN.md's "Decisions of 2026-11-09". "Measured" means a pilot-scale number exists; final
numbers need the scale-up (user's decision). The 2026-11-02 mock is in git history.

## Thesis

For sum-then-readout extractors (find the items of the input, fold their contributions into sums, compute each
feature by a readout over a few sums), the feature-space consequences of an attacker's edits are computed from the
instrumented extractor: exactly for one edit (Proposition 1), as a sound direction table for a whole threat model
(Theorem 1), and from that table, monotone detectors no edit in the threat model can evade (Corollary 1). Today this
knowledge comes from trial, from an analyst's reading of the extractor, or from observed attacks.

## Contributions

1. **The class and exact side effects.** Sum-then-readout extractors (items, sums in commutative monoids, readouts
   with a support), and Proposition 1: an edit's delta and the item table of the input give the features of the
   edited input exactly, before the edit is applied, re-evaluating only the readouts whose support a changed sum is in.
2. **Sound directions.** Signatures (the changes a threat model may make to each kind of item), the derived table
   (direction of each sum from the changes, of each feature from its readout's rule), Theorem 1 (sound over a
   population, and for sequences of edits when the population is closed), Lemma 1 (closure follows from the table
   when the population is bounded by features no edit can raise; session 74), and Corollary 1 (monotone detectors).
   The readout's direction comes from one rule, the sums it rises and falls with (session 74). Format-free, with
   proofs.
3. **Instantiation, on EMBER.** A template any instance follows (§4), filled in for EMBER 2024: 2,480 of 2,568
   features modeled and reproduced bit for bit, three repairs, a catalogue of twelve operations from the public
   toolkits, and every edit's predicted features checked against extracting them again (0 wrong).
4. **What the computation shows about adversarial examples (on EMBER; §5's three findings, decision 10).** Hand
   analysis misses the side effects that come from how the parser locates structures (eight errors in a careful hand
   table, each witnessed by a real edit; 11 lowerable features in a published expert set); defenses learned from
   observed attacks inherit the attacks' blind spots (PV, ERDALT, learned constraints, adversarial training all fall
   to a search aimed at what they trust); and with the directions known, robustness against the whole threat model
   costs a measured four to six points of detection, attributable per operation, with no evasion on files in the
   population. Not a state-of-the-art defense claim.

## Outline and word budget (body about 11,000 words while drafting; CCS format)

| Section | Content | Words |
|---|---|---|
| 1 Introduction | last | 1,000 |
| 2 Background and Motivation | as drafted, adjusted to the alignment option the user picks (below) | 950 |
| 3 Measuring Edits Across Feature Mappings | as drafted (sum-then-readout extractors; edits and side effects; sound directions; robust by construction, split from sound directions in session 94); finetuning only | 3,500 (now ~4,050) |
| 4 Instantiating the Framework | the template, EMBER in it (below); bookkeeping in an appendix | 1,000 |
| 5 Evaluation | three findings: what hand analysis misses, what observed attacks miss, what robustness costs (below) | 3,200 |
| 6 Related Work | as drafted; "margins" and old terms fixed | 1,000 (now ~1,280, accepted in session 84) |
| 7 Discussion | what does not fit (global analyses, learned features), cost of instrumenting (no effort claims), other domains; limitation: code-level transformations are outside the threat models (decision 9) | 500 |
| Appendix | symbols, types, proofs; the EMBER details §4 points to; other domains, one section each, if added | — |

## §4 Instantiating the Framework (about 1,000 words; restructured with the user 2026-11-09, session 27)

The body keeps what a reviewer judges (how strictly EMBER fits the class, the threat model against the literature,
the population); the bookkeeping goes to an appendix (user: "Most of this is engineering and book-keeping material
... Its boring"). No "instances at a glance" table until a second domain exists.

- **Lead (~50).** The four parts an instance supplies (items, contributions, readouts; the features that do not fit;
  a threat model with its signature; the population), in one or two sentences. No checks in the lead.
- **4.1 EMBER and PE files (~170), its own subsection.** The paper's first mention of PE files and malware detection:
  what a PE file is (headers, section table, sections, import table, overlay), why EMBER (the standard benchmark for
  static malware detection; 2024 version), its feature groups, instrumented without changing what it computes.
- **4.2 EMBER as a sum-then-readout extractor (~300), parts (a) and (b) merged.** Paragraph 1: the gist of the
  accepted block-1 text (two families of items, the sums, every row of Table 1 occurs), closed by the one-sentence
  bit-exact check. Paragraph 2, qualitative: how strictly EMBER fits and what to do with features that do not:
  rewritable without changing a value (section size over file size, the library set), or with no items at all (the
  88 parser warnings: drop them or keep them as both; a monotone detector cannot read "both", so they coincide;
  absent from EMBER 2017/2018, VERIFY; dropping them costs nothing, run 126). The import-overwrite bug is not
  mentioned. The overlay is taken as LIEF takes it (after the last section; pefile's rule lets entries the loader
  ignores move it; R7, `docs/evidence/r7-overlay-rule.md`): one sentence by the warnings, Appendix D's locating
  sentence follows. How the extractor is framed (EMBER2024's corpus with an extractor derived from EMBER-v3, its
  deviations stated once by principle) waits on PLAN.md step 2c. One sentence on the re-encodings over sums (here or where §5 introduces the sums detector).
- **4.3 Threat model (~400, with the catalogue table).** Literature first: the edits the PE problem-space attacks use
  (a literature pass before drafting), our catalogue as the functionality-preserving edits that do not rewrite code,
  exclusions named (code-level transformations, which are harder to execute without breaking functionality; packing).
  Code-level transformations are a stated limitation (PLAN.md, decision 9). Declared changes (operations stated in items, and append) checked by
  re-extraction; in-place writes collected from item tables. Writes onto locating positions: Proposition 1 declines;
  the directions allow any change of that kind unless declared (rename, remove debug, remove signature). Corpus-
  collected, so checked rather than proven (decision 2): the writes' changes and the kinds' vocabulary; one sentence,
  the check in §5.
- **4.4 Population (~150).** Complete files with a plain layout; almost every file outside it is incomplete (headers
  locate content past its end); membership checked at inference, routing, closure (0 of 56,902). The files we use are
  those of at most 4 MB, stated once in §5.1's Setup (PLAN.md decision 8 (iv), settled in session 46).
- **Appendix, the EMBER instance.** The item kinds; a table mapping each row of Table 1 to EMBER's features; the two
  rewrites; the re-encodings; how the locating positions are recorded (single-byte flip check).

## §5 Evaluation, three findings (3,200 words; restructured with the user 2026-11-10, session 30)

**Framing (PLAN.md, decision 10).** §5 is not organized by §3's results (that made it a validation section: the
implementation is correct, the proofs hold) and not as a defense paper. It tests the claim §2 makes about where
practitioners get their knowledge of what edits do: by trial (exact, but only for the edits tried), by an analyst's
reading of the extractor (as complete as that reading), or from observed attacks (only what those attacks did). Each
subsection is one finding about adversarial examples, stated with a number; the adaptive search and the monotone
detectors are the instruments that confirm each finding on real files. Claims say "on EMBER", not "malware in
general", until a second instance exists. The detectors' accuracy cost is reported as a measurement of what one kind
of robustness costs, never as "small" or "cheap" (user: 4 points is not small; they would like about 1% or less).
No state-of-the-art defense claim (three defense baselines; the user would want at least six for that).

**Plan, one line per paragraph.** Numbers are the pilot's, from the current draft; tables are named by content
(check `manuscript/main.aux` for their compiled numbers).

- **Lead (~120).** A practitioner learns what an attacker's edits do to the features by trial, by reading the
  extractor, or from observed attacks (§2). We compute it instead; each subsection tests what the computation shows
  about one of these sources, on EMBER.
- **5.1 Setup (~400).**
  1. Data, detectors, threshold, threat model, byte budget (as now).
  2. The attacks: the toolkit (seen / held-out), and the adaptive search as the instrument that confirms on real files
     what the directions flag (it scores candidates by Prop. 1 and aims section names at the buckets a detector trusts;
     every kept file re-extracted). No timing (memory `no-timing-claims`).
  3. Is our computation right? Two or three sentences: 0 wrong of the ~73,000 checked edits, it declines exactly the
     writes onto positions the parser reads; the 100- and 2,000-file direction tables are identical and no edit moves
     a feature in a direction the table excludes (decision 2's one sentence). **The side-effect table (today Table 3)
     and its two paragraphs move to Appendix D** (user, 2026-11-10).
- **5.2 What Hand Analysis Misses (~850).**
  1. The finding: the side effects an analyst misses come from how the parser locates structures, not from the content
     an edit writes. *If check C1 below succeeds:* open with how far one edit reaches (per operation, how many features
     one edit moves and how many it does not target; Pierazzi et al.'s side-effect features), with the easy-to-miss
     content effects (append lowers every section's size ratio, extends the last string).
  2. The hand-written direction table against the derived one (today Table 4, kept): eight disagreements, each a hand
     error witnessed by a real edit, from three parser facts (structures past the end, the Rich header's fixed search
     range, the entry section's fallback rule).
  3. What the error costs: the detector built on the hand table, attacked; one added section after the overlay lowers
     its score on 10 of 29 files; the derived detector provably does not move.
  4. A hand analysis that is not ours: the expert set (Gimenez et al.), 11 of its 40 features lowerable by renaming a
     section or rewriting the DOS stub, evaded on 2 of 8. *If check C3 finds published hand classifications of EMBER's
     features:* compare the derived table with them here (no runs).
- *Drafted in session 39 (7a2ceff, 9d0369f, 035d977); the draft supersedes the plan below: items 7 (learned region)
  and 8 (audit table) dropped by the user, the tables to be remade later; no seed or protocol-hygiene details; PV's
  published-style 14/22 out (PLAN.md, decision 10, session 39).*
- **5.3 What Observed Attacks Miss (~950), with the new audit table.** *Rewritten in session 34 after runs 133-134
  (claim agreed with the user; evidence and caveats in `docs/evidence/section-5.3-design.md` §10.4-10.5). Every defense
  learned from attacks is built from the same 3,183 outputs of the eight toolkit attacks, a seed per (attack, file),
  on 400 training malware; tested on the pilot malware with a seed per file. The old seed-0 rows are retired.*
  1. The finding: a defense learned from observed attacks inherits what the attacks did not do, and nothing in the
     observations says what that is. Coverage first: the same eight attacks lower 745 of the 1,070 lowerable features
     under the published protocol and 928 when varied over 400 training files; the derivation lists all 1,070 at once.
  2. The operation the attacks lack becomes the hole: PV rebuilt from the varied outputs is evaded on 4 of its 9
     files, each by one rename of the entry section (no toolkit attack renames), through the entry-section-name
     buckets the derived table marks lowerable before any attack runs; the toolkit itself evades it on none.
  3. Unmoved is not unmovable: observation cannot tell features the threat model can lower from features no edit can
     move, so PV trusts what it should not (PV from the published protocol: the search evades 14/22) or constrains
     what it need not (PV rebuilt: 26.2% at 1% FPR against the derived detector's 87.3% on the same features; the
     DLL flag, which no edit moves, is forced monotone).
  4. ERDALT constrains the vectors it saw, not the next ones: its own training attack, with imports from other donor
     goodware, evades it 24/29; the search 22/29.
  5. Adversarial training: the toolkit evades it 12/50 (undefended 25/49), the search 23/50.
  6. Leave-one-out (run 135, `\synthetic{}` until read): each defense built from seven attacks, attacked by the
     eighth; one sentence in the body (expected: PV's folds near 0, so held-out observed attacks give false
     confidence while rename gets through; ERDALT high on gamma_api and header_fields), per-fold table in the
     appendix.
  7. The learned region (exact tree solver), from the old plan: certifies a defense on its own attacks by
     construction; whether it keeps a sentence is decided when drafting.
  8. **Audit table (assembly only; user chose option (b)):** one row per defense, grouped by how its trust was set (by
     hand: the hand-table detector, the expert set; from attacks: PV, ERDALT, adversarial training; the derived
     detector for reference). Columns: how its trust was set, what the derivation flags, TPR at 1% FPR, toolkit
     (seed per file), leave-one-out held-out, adaptive. Risk: the "flags" column mixes units; settle when drafting.
- *Drafted in session 36 (8fd8c9c); the draft supersedes the plan below: the expert-set comparison moved second,
  TPR at 0.1% FPR added, one any-of-eight toolkit column, no cost paragraph (PLAN.md, decision 10, session 36).*
- **5.4 What Robustness Costs (~900), with the detector table (today Table 5) trimmed** to the undefended rows, the
  monotone rows, and the additions block (the baselines move to the audit table).
  1. The finding: with the directions known, robustness against every structural edit in the threat model costs about
     four points of detection (93.5% to 89.6% at 1% FPR on the sums; 87.2% on the features), with 0% evasion on files
     in the population; one clause that the adaptive search's largest score drop is exactly 0.
  2. Where the cost lies, per operation: import addition 2.1 points, the three header overwrites 1.4, the rest at most
     0.3; dropping the two-sided features costs 0.2; reading the sums recovers about two points.
  3. The width of the threat model: additions only gives 92.2%, and the header-field attacks then evade on 28%; the
     expert set under the same threat model detects 29.1%.
  4. Beyond the guarantee's hypotheses: GAMMA's rebuilding injections move features outside the table and still evade
     no monotone row on files in the population (0/56, 0/60; also at the literature's budget); 41 of 42 malware still
     detected after every toolkit attack, against 21 of 47 undefended.
  5. Scope: the population (89% of the attacked malware, predicted for the files of at most 4 MB; 1.5% of benign test
     files outside it, so leaving it stands out); deriving the table costs one pass per extractor (about 5 minutes), PV repeats its attack runs per attack.

**Checks before drafting 5.2 and 5.3** (new measurements on existing outputs, no new runs; state the hypothesis
before each, report a failure as such):

- **C1, side-effect breadth (for 5.2.1).** Do the correctness runs (runs 107 and 118, `catalogue_checks`) keep the
  per-edit feature deltas? If so, count per operation the features one edit moves and those outside the operation's
  target. Expect most operations to move features they do not target (size ratios, string counts, entropy). If the
  deltas are not stored, estimate a re-run and ask the user; 5.2 works without it.
- **C2, how much of the lowerable set observed attacks reach (for 5.3.1).** From the toolkit outputs already compared
  with the derived table (`scripts/a1_toolkit_split.py`, runs 78 and 105): of the features the derived table marks
  down or both, the share any toolkit output lowered, on files in the population. Expect a small minority (the PV
  hole's section-name buckets are untouched).
- **C3, published hand classifications of EMBER's features (for 5.2.4).** Check
  `docs/evidence/literature-adversarial-malware.md` and `papers/` for work that labels EMBER features as modifiable or
  not (possibly Rosenberg et al., 2020: verify before claiming; memory `portray-cited-work-accurately`). Compare with
  the derived table only if the classification is published per feature or per group.

**Extending §5 to other domains (agreed with the user, session 31).** The structure is domain-free: the three findings
follow §2's three sources of knowledge, and each is a measurement per instance, so a second domain adds a number to
each finding, rows to the tables, and an appendix section (decision 1), not a new structure. Drafting rules that keep
it so: (1) each finding states its claim in the framework's terms first, then EMBER's number ("on the EMBER instance");
PE mechanics (parser facts, section names, hash buckets) stay in the evidence sentences or Appendix D; (2) tables are
shaped so a second instance adds rows: the audit table and the detector table take an instance grouping later, and the
hand-table disagreement table (PE witnesses) moves to the instance's appendix, replaced by one summary row per
instance; no one-row tables now; (3) 5.2 gives published hand analyses (Severi et al., the expert set) as much weight
as our own hand table, since published ones are what the finding rests on in another domain (candidates there, to
verify when the user opens domains: additions-only assumptions on Android feature sets, hand-written properties for
PDF classifiers); (4) 5.1 keeps the shared protocol; each instance's data, toolkit, and budget move to its appendix
once there are two. *Risk, not structural:* the size of 5.2's finding depends on the extractor's complexity (a
presence-of-token extractor may leave a hand analysis little to miss), so findings are written as measurements ("how
far each falls short"), never as "always falls short".

**Revisions after the user's review of blocks 1-2 (session 31).** (a) The toolkit attacks are introduced in §4.3 (per
instance: the published attacks and their implementation, secml-malware), not in 5.1; 5.1 keeps only the shared
protocol (budgets, leave-one-out, the adaptive search in format-free terms). (b) **Leave-one-out for the defenses
learned from attacks** (PV, ERDALT): build from seven toolkit attacks, test on the eighth, for each of the eight; the
fixed split (chosen so the strongest attack was held out) looked like tuning the setup in our favor (user). The
adaptive cells use the models built from all eight attacks (PV exists, 14/22; ERDALT-8 must be trained). To run in
another session (coding and analysis); until then the held-out cells are `\synthetic` in block 3. *Scripted (session
32): `run/131_loo_defenses.sh`*; the held-out attack runs against each fold's model (same protocol as every cell), and
ERDALT's training malware covers all eight attacks (its step 0). Outputs: `artifacts/experiments/a_loo/summary.json`
(per-fold and mean held-out evasion, files evaded in any fold) and `a_loo/erdalt-all8-adaptive/adaptive.json`. Expected
(header of run 131): PV mostly 0 outside the gamma_api fold (smoke: 5/21) and maybe gamma_sections; ERDALT high on
the gamma_api and header_fields folds. (c) No "pilot
scale" and no "written to disk" bookkeeping in the prose; re-extraction is stated once in 5.1 with why. (d) 5.2 has an
opening question and run-in paragraph headings (Our hand table, Why it errs, What the error costs, Published hand
analyses).

**Results of the checks (session 31, 2026-11-10):**

- **C1: held.** `catalogue_checks/2000-exact/edits.parquet` keeps each edit's moved features (`moves`). On the 60,934
  applied edits in the population, EMBER's own features only (re-encodings `body_*`, `section_split` excluded): median
  263 features per edit; per operation from 10 (checksum) and 11 (debug removal) through 25 (header fields), 122
  (rename), 362 (append), 501-510 (gaps), to 539 (imports) and 548 (add a section), spread over 4-8 feature groups.
  Every operation moves the byte histogram and the general group; rename moves strings and entropy histograms; append
  moves the section group on every edit (size ratios).
- **C3: two published hand classifications, one comparable.** Severi et al. (USENIX Sec. 2021, `papers/severi2021explanation.pdf`,
  Sec. 6.1) discard all hashed EMBER features ("directly manipulating these features by tampering with the binary would
  be extremely difficult", by the hash's preimage resistance), keeping 35 directly editable non-hashed features, 17
  controlled by their utility. Derived table (features, population, `a_directions_derived_v2`): of EMBER 2024's 1,650
  hashed features, edits of the additions threat model can move 1,490 (lower 1,234); only the 128 export buckets and
  the 32 Rich-header pairs stay fixed (the latter movable under full). Caveat: Severi et al. used the 2018 feature set
  (same hashed groups, verify) and needed set values for a trigger, not only movement. Rosenberg et al. (IJCNN 2020)
  name a few "easily modifiable" features in the text; the full list is only in their repository (not comparable).

**Drafting order (blocks, `paper-prose`, `make` and `make check` after each):** (1) lead and 5.1, and Table 3 with a
short paragraph into Appendix D; (2) 5.2; (3) 5.3 with the audit table; (4) 5.4 with the trimmed detector table. Then
§2's closing sentence ("uses them to attack malware detectors and to build robust ones") and contribution 4 above,
re-read against the findings.

**Known weaknesses of this framing (from the session-30 analysis):** findings about adversarial examples rest on one
extractor (a second instance would strengthen 5.2 and 5.3 most; later, the user's call); 5.2's main evidence is our own
hand table (strawman risk; the expert set and C3 counter it); 5.4 measures the cost of one kind of robustness
(monotone over the derived directions), not robustness in general.

## §2 against §5: the four lines of work

§2 says four lines of work each need part of the reachable set. What §5 shows for each today (still accurate after
the 2026-11-10 restructuring, which moves the baselines to 5.3 and the monotone rows to 5.4):

| §2's line | What it needs | §5 shows it? |
|---|---|---|
| problem-space attacks | the point each candidate reaches | **Yes, partly**: the adaptive search scores by Prop. 1 (Table 5's adaptive column); its saving is not measured |
| feature-space attacks (constraints Ω) | constraints over features | **As constraints, not as an attack**: Table 4 and the learned-region check compare constraints; no feature-space attack runs on ours |
| problem-space defenses (adversarial training) | many points on many training objects | **No**: adversarial training is a baseline in Table 5, trained on toolkit outputs, not on points the framework produced |
| feature-space defenses (monotone, verified) | which way each feature can move | **Yes**: Table 5 (monotone); verified training only cited |

Options (both allowed by the user, decision 4):

- **A. Narrow §2 (no new runs).** Keep the four lines as the landscape, but say plainly that we evaluate three uses:
  the attack (scoring without extraction), the constraints themselves, and monotone detectors; adversarial training
  appears as the realistic alternative a defender would use, not as a use. (The per-candidate cost measurement was dropped, 2026-11-10.)
  Cost: §2 promises less; a reviewer may ask why adversarial training on computed points was not tried.
- **B. Show all four.** A plus two runs: (i) adversarial training on the adaptive search's outputs, produced through
  Prop. 1 (the problem-space defense made cheap); (ii) a feature-space attack (the exact tree solver already used for
  the learned region) inside the derived region on the unconstrained detector, against the evasions the problem-space
  search realizes. Cost: (i) is heavy (the adaptive search on hundreds of training malware; a 1,000-candidate budget
  would bring it down) and adds a row whose expected result (resists the toolkit, still falls to a fresh adaptive
  search, as the toolkit-trained row does) mostly repeats Table 5's point; (ii) is cheap but adds machinery.

**Decided (2026-11-09): A** (the per-candidate cost measurement dropped 2026-11-10); revisited at the next full review, which
also checks how much the literature values problem-space defenses (PLAN.md, decision 6). Reasons: The paper's strongest claims (Table 4, Table 5's
monotone rows) need no new runs, every line §2 keeps has a table behind it, and adversarial training already serves
as the defender's alternative. B(ii) is the one addition worth weighing if the review asks for the feature-space
side; B(i) costs most and argues least.

## Measured vs missing

- **Measured (pilot):** Tables 3-5 complete; closure; coverage across corpus sizes; price list; PV and ERDALT holes;
  expert set's 11 holes; the hand detector's soundness loss.
- **Missing, small (session 30):** checks C1-C3 above (two counts on existing outputs, one literature check); the
  audit table and the trimmed detector table (assembly only).
- **Missing, small:** the instances-at-a-glance
  table (assembly only); the sums row's adaptive cell (beam search cannot route to the sums detector yet; expected 0%).
- **Missing, user's decision:** the scale-up (seeds 0-2, full splits, more malware; the adaptive budget at 2,000
  files); a second toolkit for held-out attacks (MAB-Malware); other domains (later, appendix plus table rows).

## Dropped from the paper

Requirements R1-R5, footprints, margins, Theorems 2-3, the CTU-13 rows and Drebin as planned instances (any later
domain goes through the template), coupling, the region's tightness, a cost theorem, effort claims.
