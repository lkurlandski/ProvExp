# Review of Sections 3-5 (2026-10-14, evening): narrative, writing, presentation, validity

Read on the manuscript at commit `831ec37` (source and rendered PDF, pp. 3-11). Goal (user): a top-tier (CCS) paper
whose narrative, writing, and presentation are extremely strong, on top of scientific validity. Items are ranked within
each group; IDs (S1, ...) are for discussion only.

## Outcome (applied 2026-10-14, user's decisions)

Applied: S1 (influence left to construction, one sentence after Definition 3), S2 (novelty sharpened: region-summing is
the special case, cited), S3 (no bands, no "weak"), S4-S6 (threat model, discovery rule, MalConv ROC-AUC 0.9913), N1
(Figure 3 faithfulness vs. cost replaces Table 1; Figure 4 resolution replaces Table 3; Figure 5 MalConv curves; audited
fields Table 3), N2 conservative (Figures 1-2 kept, terms and captions fixed, round-trip marks removed), N3 partly (4.2
summary sentence; 4.3/5.1 paragraph heads), N5 (4.3 tightened, B9 cut), N6 (comparison trimmed), N9 (conventions
Table 1), N11 (setting split). Also fixed: the surrogate adds 5 fields, not 9; "import table" is the import address
table; 1.67 -> 1.71 in abstract/intro (interventional TreeSHAP, as the body). Not applied (user): N4 (no reorder of
5.1), N10 (Definitions 1-2 stay), S7 (consistent as is), strict writing rules (W-a..W-e) and results-first.

## Verdict in one paragraph

The science in Sections 3-5 is now in good shape: every headline claim has a measured result against a realistic
alternative. The **presentation is the weakest part of the paper**. Sections 4 and 5 are about 7 pages of continuous
prose in which nearly every sentence carries two to four numbers and a p-value; there is not a single figure of
results; the two figures that exist (Figures 1-2) spend two full-width figure slots on ideas a sentence carries, and
Figure 2 still draws the cut round-trip claim. The strongest results (the byte-level faithfulness win, the oracle, the
pushforward on MalConv, the audit's fields and its mitigation) are present but not *seen*: a reviewer skimming first
sentences, tables, and figures would miss most of them. Fixing this is mostly restructuring and moving numbers into
figures and tables, not new experiments.

## A. Scientific validity (fix regardless of presentation)

- **S1. The Influence axiom contradicts the instrumentation conventions.** Definition 3 says P_ij > 0 *iff* z_i
  influences x_j. Section 3.4's conventions exclude indirect influence ("a denominator that normalizes or a pointer
  that says where to read does not count"). A pointer field certainly *influences* the features it points to, so the
  instrumented P violates the axiom as written. Fix: define the relation P encodes ("is computed from", i.e., the
  feature's value is read, counted, or hashed from the element) and state the axiom in those terms; mention that
  influence through control (pointers, normalizers) is deliberately excluded. One reviewer with a formal bent will
  find this.
- **S2. "To our knowledge, the pushforward has not been used before" is exposed.** Summing element attributions into
  regions that contain them is common (superpixels/segments in vision; parser-based PE regions in Coull & Gardner and
  Bose et al., which we cite elsewhere): that is the incidence ("naive") pushforward. What is new is splitting shared
  elements among the features that read them (D-dagger) for features computed by a program, and using it to give a
  raw-byte model a feature vocabulary. Rephrase the claim to that, and cite the region-summing practice right there.
- **S3. The R bands label our own method "weak".** 5.1 introduces faithful/partial/weakened bands (0.8/0.5) and then
  reports the pushforward of window explanations at R = 0.31-0.40, "which is weak". The bands are ours and arbitrary;
  the evidence that matters is the trend with resolution and, now, the MalConv test. Drop the bands (or move them to
  the appendix) and let the comparison carry the meaning.
- **S4. 5.3's threat model says the attacker "needs ... only queries"** but the loader-safe attack issues no queries
  (it applies a fixed recipe). Drift between threat model and evaluation; say the attacker needs no access to MalConv
  beyond knowing which fields it relies on (which our audit, or a similar one, would reveal), or drop the clause.
- **S5. Ranking and candidate rules in 5.3 are underspecified.** "Features are ranked by how many files carry
  MalConv's evidence on them" vs. "20 features with the most malware evidence"; "few enough bytes to locate" (the 256-
  byte cap is not stated). State the rule once, precisely.
- **S6. MalConv's own accuracy is never given** (the GBDT's ROC-AUC is). Add it in the setting.
- **S7. Definition 2's clause "b_i = 0 for every element that no feature reads"** does not make sense for a raw-byte
  detector, where sigma is the identity. Drop it or restrict it to transferred explanations.

## B. Narrative and structure

- **N1. No figure of results.** Top-tier evaluation sections lead with a figure per key claim. Candidates, in order of
  value:
  1. *Faithfulness vs. cost* (replaces Table 1): extractions per file (log x) vs. gain; occlusion as a curve over 64-
     4,096 windows that plateaus, the field oracle as a point, the pullback as a curve over resolutions ending at the
     byte-level point far above the plateau at cost 1. The paper's first headline in one picture.
  2. *Faithfulness vs. resolution, both directions* (Table 3 + the pullback rows of Table 1): one panel per direction,
     showing that both transfers gain with resolution. Gives the "parallel structure" a visual.
  3. *Pushforward on MalConv*: deletion curves (evidence removed vs. budget) for pushforward, surrogate, IG over
     windows, random features; zero and random fill as two panels or line styles.
  4. Optional: the audit's fields as a small table (field, loader class, per-field effect, confirmed by
     pushforward/surrogate), replacing the long inline list in 5.3.
- **N2. Figures 1-2 should become one example-driven figure.** Figure 1 ("Explanatory Targets") is full-width for a
  distinction one sentence makes; it uses "saliency" and "explanation alg." (terms the text never uses), example
  dimensions R^10/R^30, and a grammatical slip ("yield"). Figure 2 ("Explanation Transformation") draws "concrete" vs.
  "transferred" explanations with approximate-equality marks, i.e., the round-trip claim that was cut. Replace both with
  one figure (full width, at the start of Section 3) that shows a *real* PE example: a strip of bytes (DOS header,
  CheckSum field, a .text slice, an import name) -> P (a few columns: CheckSum, byte histogram bin, section entropy, a
  hashed import bucket, plus the null element with an absence feature) -> features; pullback arrow one way, pushforward
  the other; shared bytes split among features. This makes the method, the null element, and why instrumenting a
  *program* is non-trivial (W1) visible in 30 seconds.
- **N3. Lead each subsection with its finding, consistently.** 4.1 and 5.1 have an "In short, ..." sentence; 4.2,
  4.3, 5.2, 5.3 bury their findings mid-paragraph. Give every subsection a first paragraph that states the result in
  one or two sentences, then the setup, then the evidence.
- **N4. 5.1 buries its strongest result.** The MalConv test (the pushforward on the model the audit uses, 2x the
  surrogate) is the last paragraph, after the GBDT test the section itself calls weak and an analysis it calls partly
  circular. Restructure 5.1: (i) what faithfulness means for a model that never computes the features, and the MalConv
  test; (ii) the GBDT test against TreeSHAP and the resolution trend as the explanation of why window-level sources
  push forward less well.
- **N5. 4.3 is overloaded** (about 1.7 columns plus a table): threat model, realistic alternative, setup, agreement,
  cross-deletion, shared reliance, triage, decisions, the negative evasion result, resolution. Cut or move:
  the B9 negative result to one clause (or the appendix); the agreement numbers (rho, overlaps) to a single sentence;
  the MalConv-setup details to the experimental setting.
- **N6. 5.3 ends on a detour.** The feature-by-feature comparison of the two detectors (Spearman 0.10, 2,214
  aggregates) after the mitigation dilutes the audit. Keep its one finding ("different header fields; only the checksum
  is shared") in the closing synthesis and move the rest to the appendix or cut it.
- **N7. The closing synthesis paragraph of 5.3** ("The two applications use the transfers in opposite directions ...")
  is good but sits inside the audit subsection. Promote it to a short unnumbered wrap-up at the end of Section 5, or
  open the discussion with it.
- **N8. Section 3 has no worked example.** Readers never see what P looks like for a PE file. The example figure (N2)
  solves this; refer to it from each definition.
- **N9. The instrumentation conventions are a dense paragraph.** A small table (feature family -> what counts as an
  element's contribution -> exact or convention: header fields, byte histogram, entropy windows, strings, hashed
  imports, section features, absence features -> null) would show the engineering judgment the novelty case rests on
  (W1) and be easy to check.
- **N10. Definitions 1-2 formalize something trivial** (also in the earlier review). Merge into one sentence each in
  the Preliminaries prose; keep Definitions 3-5 (P, pullback, pushforward), which carry the method.
- **N11. The experimental setting is one long paragraph** mixing data, models, the explanation set, the pilot scale,
  and the deletion operator. Split it: data and models (with MalConv's accuracy, S6), then the operator and its
  safeguards (now including the off-distribution sentence).

## C. Writing

- **W-a. Number density.** Most sentences in 4.1, 4.3, 5.1, 5.3 carry 2-4 numbers, p-values, and parenthetical
  ranges. Rule for the rewrite: one headline number per claim in the text, with its reference point; p-values and
  secondary numbers go to tables/figures or a single parenthesis per paragraph.
- **W-b. Paragraph length.** Several paragraphs exceed 25 lines in two-column format (4.1 results, 4.3 shared
  reliance, 5.1 MalConv, 5.3 evasion). Split at each new claim; each paragraph opens with its point.
- **W-c. Terminology drift.** Fix one term each and use it everywhere:
  attribution (not saliency, not evidence-as-noun when meaning attribution); transfer (not transformation);
  problem-space explanation / byte-level explanation (pick when to use which); window (not region, except the oracle's
  parsed regions); deletion (not ablation in the text); locatable vs. nameable vs. attributable features (three
  different notions; define once); the explanation set vs. the pilot subset.
- **W-d. Sentence shape.** Long sentences chained with semicolons and em-dashes (e.g., the oracle sentence in 4.1, the
  cost sentence "So the 135-fold saving in extractions is the whole story for TreeSHAP"). Break them; prefer plain
  subject-verb-object.
- **W-e. Hedges and self-undercutting phrases.** "which is weak", "partly circular", "plausibly because", "we leave
  to future work" inside results. Keep honest limits, but state them once, plainly, where they matter.

## D. Presentation mechanics

- **P1. Captions are long and fully bold** (acmart default), so a 7-line caption is a heavy block (Tables 1, 3, 4).
  Shorten to a title sentence plus the takeaway; move definitions into the text.
- **P2. Float placement.** Tables land a page away from their discussion (Table 2 before 4.3's triage text, Table 3 on
  the page after 5.1). Revisit after the restructure; place floats at the top of the page where they are discussed.
- **P3. Table 1 mixes method families without grouping labels**; the field oracle sits among occlusion rows. If it
  stays a table (rather than the figure in N1), add group headers (direct, oracle, pullback) and bold the best per
  group.
- **P4. Table 4's blue row** reads as a result at a glance; keep it visibly marked (it is) and make sure the caption's
  first words are not the placeholder note.
- **P5. Remaining TODO comment** in the experimental setting (scale-up) is invisible in the PDF; fine for now.

## E. What is already strong (keep)

- The three-question parallel structure (faithful? known answer? what can a defender now do?) for both directions.
- The oracle result and its explanation (resolution within a field, not knowledge of the read set).
- The trigger testbed's "spectrum" framing (struct vs. content trigger).
- The off-distribution paragraph in the setting, and the honest "by construction" sentence in the mitigation.
- The closing synthesis of Section 4 ("resolution is what makes the comparison work").

## Suggested order of work

1. Validity fixes S1-S7 (small, text only).
2. Decide the figure plan (N1, N2) with the user; build the figures (matplotlib/pgfplots from existing artifacts).
3. Restructure: N3-N7, N10-N11 (section by section: 3, 4.1, 4.3, 5.1, 5.3).
4. Line-level rewrite with the rules W-a to W-e, one subsection at a time, with the user reading each.
5. Presentation pass (P1-P3) once the floats settle.
