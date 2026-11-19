# Writing: the reaction log

What the user said about real drafts, newest first, as close to their words as possible. This is the record the
`paper-prose` skill is built from; it is evidence, not a list of rules. Read the entries for the passage at hand and
the ones before it. (Until 2026-11-09 this file also held "tendencies" for style: habits to ration, techniques,
organization, layout. They are archived in `docs/archive/paper-prose-2026-11-09/writing-spec-tendencies.md`, with the
old skill and reader model.)

Each entry: what was shown, the verdict, the specifics, and, where it helps, what it seemed to imply at the time.
The "implied" notes are earlier readings, not instructions; several of them were later shown to be too broad.

## Reaction log

- **2026-11-19, §3 cut by trimming explanation (session 99).** First plan (22 items, −593 words) called "an
  excellent first-pass analysis"; asked for each cut to be assessed for (i) mathematical correctness and strength,
  (ii) the reader's comprehension and appreciation (doctorate-level security, privacy, ML researchers), (iii) flow, in
  that order, with improvements that keep most of each cut, listed least to most disruptive. Approved every revised
  item: "It's okay that we didn't quite hit 3250." Implied: a cut that drops a scope statement, a soundness caveat, or
  a back-referenced term is worth a few words to keep.
- **2026-11-19, body/appendix split of §3 (session 98).** Chose "Appendix C holds proofs only" (definitions and
  conditions of stated results in the body, commentary cut). On turning Table 7 into a stated lemma: "The table was
  meant to be illustrative and I feel like this takes the mathy-stuff too far" (cut it, kept in an `\iffalse` block).
  On the lemma behind Theorem 1: "I would rather keep the Lemma in the main body and leave its proof in the Appendix";
  then asked the same for the readout rule, and to fold a one-use helper lemma into the proof that used it. Kept the
  sentence bridging Gimenez et al. to direction tables once Claude gave its value; cut the recap sentence. Next round:
  "we'll let the math do more of the talking", trimming explanations and analysis rather than easy cuts.
- **2026-11-19, §3 cut (session 97).** Plan per subsection with exact replacement text; most items approved,
  two small cuts denied (the free-monoid sentence after equation (6), "They do not form a vector"). Analogies:
  "Shorten" for all three. Lemma 1: shorten in place, not move. Second round proposed moving a counterexample to the
  appendix: "We can't just cut sentences from the main section and place them in the appendix. That's confusing and
  creates more problems than it solves." On Appendix C: "I thought this would be all proofs, but it looks like there
  are some random other paragraphs"; "Why are there definitions in the appendix?" Decided to revisit the body/appendix
  split in a new session.
- **2026-11-19, §3 holistic review (session 96).** Approved most findings outright; asked to discuss the ones that
  change structure or claims before applying (closure claim vs §4, splitting one edit from sequences, the analogy
  paragraphs). "I approve all small/minor suggestions that improve clarity and consistency. Larger and more significant
  changes to the language should be run by me." Appendix B: "I envision this appendix being a stand-alone crash-course
  on the background material of section 3. It's okay if section 3 lightly repeats the definitions from this appendix."
  Analogy paragraphs (Gray et al., view maintenance, abstract interpretation): cutting all three is an option since §6
  may adjust, "shortening all three might be a better approach"; decide in the cutting session. On "not X but Y" and
  "thus" sentences: remove those that do not help, cautiously, not as a requirement.
- **2026-11-17, §6 cut (session 84), drafted without the paper-prose skill.** Šrndić and Laskov rewording, approved.
  *Constraints over features* at 321 words (plan ~300): approved; "it's okay that we weren't able to cut quite as
  aggressively". First split of *Robust and monotone detectors*: "the prose comes off as a little choppy and
  disconnected. Try to smooth it out without increasing the length too much"; the second version (sentences that lead
  into each other: "Realizable examples are costly to generate" before Lucas et al., the three Chen et al. papers
  together, "Rather than resist the edits it was trained on" as the opening) approved. *Certified defenses*: "whatever
  the edits mean" is "a little informal and unclear"; replaced by "by the size of its edits rather than by their
  kind", approved. *Incremental computation* at 118 words, approved. "We don't need to exactly hit our original
  target. We just need to make significant progress to it."
- **2026-11-08, §3.2 round 2 verdict.** "Quite satisfied." Hand edits only, for spacing and terseness: the lead
  shortened to "give $z'$ exactly (before the edit is applied) and thus the side effects of the transformation", "In
  other words" cut from Def 6, "the largest or smallest" instead of "the largest or, in a min pool, the smallest", and
  Prop 1's decompositions numbered. Implied: once the structure is right, the user trims wording by hand; prefer the
  shorter phrasing in leads and statements.
- **2026-11-07, §3.2 first read of the sprint-revised version (U1-U18 in `docs/archive/framework/sprint-framework-review.md`).** Def 6
  "quite good" (the user glossed $\uplus$ by hand). ¶1 "long and unfocussed", references other sections without
  reason, fails to introduce the subsection. The positions paragraph reads as "admitting to a significant limitation
  ... without any consolidation"; "an edit can have several deltas" obvious and its reason unconnected. The example
  from Algorithm 1 "largely fails": §3.1 needed one to picture the extractor, here "the math is somewhat
  self-explanatory"; the tokens caveat incomprehensible; no forward reference needed. Prop 1 abrupt; "In particular" a
  poor joint; (ii)'s "but not from the old value" unclear ("word salad?"). The explanation paragraph did three jobs;
  justify (i)-(iii) in order; the databases remark "really cool" but misplaced. The last two paragraphs "gobbledygook",
  "written without any real plan". Round 2 (2026-11-08) from a six-paragraph spine, plan approved; the {5, 3} example
  also dropped at the user's suggestion. Implied: lessons 32-33, lesson 20 limited.

- **2026-11-06, §2 review (written comments; plan approved, then implemented).** (1) Again: state Pierazzi et
  al.'s ideas as fact with a citation, not "Pierazzi et al. name/write ...", "Their account of ...". (2) Clarify what
  makes an attack feature- or problem-space (can a problem-space attack search in feature space?); answer: what it
  returns; keep it short. (3) The reachable set in its own paragraph, to mark it as our perspective (placed after side
  effects). (4) The side-effects paragraph ~20% too long ("good, but trim some fat"). (5) The motivation paragraph is
  the most important of §2: open with the unifying claim and **bold** each problem in the prose. (6) "Feels like we're
  missing something": the taxonomy is attacks/defenses x feature/problem space; naming needs our evaluation does not
  cover is fine, the closing makes the scope clear. (7) "Compute two descriptions" confusing; "the exact point one
  transformation reaches" sounds like plain extraction; the closing goes in its own paragraph, short and summative,
  saying the framework addresses the gap, with no terms §3 has not defined yet ("items"). Implied: a motivation
  section's key claim leads its paragraph; avoid vague nouns ("descriptions") for what we produce; never use a later
  section's terms in a summary.
- **2026-11-05, §3.2 second draft.** "Not making much progress"; asked Claude to reflect on its failures first.
  (1) The lead rambled and over-referenced other sections; it should say quickly what the subsection contains and its
  purpose in the framework; "parses" is needless domain specificity. (2) The paragraph after Def 6 still long-winded
  at the end; "what the hell is pi(1)" (an \eqref right after a symbol renders as an application). (3) A one-sentence
  definition ("contributes to") sitting alone looks strange: put it in the previous subsection if it is core, or
  inside the proposition, briefly. (4) "(5) applied to (7)" unintelligible: write "Definition 5 applied to ..."; the
  paragraph after Prop 1 was unreadable from notation and abbreviations. (5) No human interpretation of what the
  proposition gives, nor why the side effects are exact. (6) The last paragraph was LLM slop. Claude's reflection:
  it never read the rendered PDF, used equation numbers and section pointers in place of arguments, never said what
  the proposition means or why it is exact, and patched listed defects instead of rewriting. Implied: read the
  rendered text before showing; explain a result in words (what it says, why it holds, why exact) before or instead
  of a symbolic sketch; no \eqref as an argument.
- **2026-11-05, §3.2 first draft (item delta, Proposition 1, toy examples).** "Good", but "a little long-winded"
  and taking on "the long-winded hard-to-read characteristics of LLM writing". Specifics: (a) the paragraph after
  Definition 6 spelled out the patently obvious (a delta exists, the smallest one, others add the same items), while
  the one notable idea, that pi keeps contents and forgets positions, was "under-appreciated, under-emphasized, and
  under-discussed"; (b) Proposition 1 "extremely dense", complex notation, an index that seemed to mean two things
  (it did not, but the word "sum" did: our term and the summation sign in one formula); (c) "what is a pool?": defined
  only as two labels inside Definition 2's monoid list. Revised: the paragraph after Def 6 now develops why
  positions matter only through contents and through which items exist; Prop 1 restated from the kept items B with no
  summation signs or subscripts; "pools" defined in Def 2; ~1,100 -> ~880 words. Implied: spend a paragraph on the
  idea, not on facts any reader infers; prefer notation that names an object (B) over index-heavy formulas; a term
  used alone must be defined alone.
- **2026-11-05, §3.1 redraft (factorization, identity-free items, toy example in purple).** "A significant
  improvement." Preliminary notes before §3.2: number the equations; use parallel calligraphic spaces for the stages
  (Z -> V -> S -> X instead of a text label, M, and R^J), which also removes J from the first paragraph; tau for kinds
  "acceptable for now" (notation to improve later; change now only clear wins); no compound definition titles
  ("Contributions and the sum vector" -> "Contributions"); the "sum vector" is not a vector, so do not call it one.
  Implied: parallel objects get parallel notation; a name must be literally true; prefer simple definition titles.
- **2026-11-05, written review of the rewritten §2, §3 lead, §3.1, §3.2 (stopped at §3.3).** Verdict: §2 and §3.1
  are workable with revisions; §3.2 from Definition 6 to Lemma 1 is "unintelligible", "a completely unhinged rant";
  the user assumed §3.3-3.6 are no better and did not read them. Agreed: fix the second half's structure before any
  prose, and spend real effort on organization ("if we nail the organizational design, filling in the gaps becomes
  much simpler"). Word budgets are loose at this stage; the user simplifies by hand later.
  §2: tone "distant and passive" throughout. ¶1: add a sentence on how a feature-space attack's vector is turned into
  an object. ¶2: too much space on the problem-space constraints unless the framework uses them; more emphasis on the
  reachable set ("semi-novel idea of ours ... integral to our research"). ¶3: "A problem-space attack often starts
  from a feature-space target" confused the user (isn't that the feature-space attack?) and is not needed to reach
  side effects; too much credence to Pierazzi ("Pierazzi et al. write", "Their account of"): their paper is gospel,
  state its ideas as fact and cite; consolidation over-emphasized (just one source of side effects). ¶4: "really
  good"; make the three viewpoints stand out (on first read the user saw two); asked whether the three viewpoints map
  to our experiments; define "monotone".
  §3 general: too many symbols, and symbol types used inconsistently for similar constructs. Lead: "pretty good".
  §3.1 ¶1: fine but simplistic; consider tying it to a type theory; say that such features are extremely common and
  effective across domains; "an extractor doing stuff" is informal (though parts rely on it). ¶2 (elements): odd, no
  transition, too short; a definition? Def 1 (item): "wet clay", more vocabulary than needed; "identity" has no
  symbol; content could be written as $z$ restricted to the members. ¶3: identity "smells like a leaky abstraction",
  tied to pointers and executables, unbounded (identities of identities?); "same item iff same identity" seems
  wrong; the paragraph is informal and ungrounded. ¶4 (monoid lead-in): comes out of nowhere, delete. Def 2: write
  out both max and min pools; "much, much better" than Def 1, tight and intentional; "the identity element" was
  never introduced. ¶5: mention min pools; is this used later? ¶6 (terms): no idea what count/attribute/... mean or
  what contributions are for; consider separating the sum and contribution definitions (tightly coupled, discuss).
  Def 3 and Def 4: too thin, more detail. ¶7: readouts are not something we "need"; they are a class of mathematical
  object we identified, with commonly used feature functions as examples. ¶8: "residual" unexplained; the
  implementation remark is unwarranted. ¶9 (prevalence): good; cleaned-up tables may return here later.
  §3.2 ¶1: too abrupt an entry into the math; the written set is a convenience and should not be in the spotlight.
  Def 5 (item delta): "really good". ¶2: the forward reference is hand-wavy; must say that the standard way to get
  the delta is re-extraction, and why we would avoid it, which the section has not explained; "awful", "weird,
  LLM-passive voice", confusing. Def 6 (locating positions): the same thing as identity again; boring, overblown.
  ¶3-10: kinds appear abruptly after a definition about locating positions; incomprehensible; "honest tools" is "one
  of the stupidest sentences I have ever read" ("perhaps we should add a requirement about honest computers or honest
  physics"). Lemma 1: the claim is graspable, but not why it is true. ¶11: "LLM slop".
  Implied: (a) a definition that needs a paragraph of informal glossing to make sense ("identity", "locating
  positions decide whether an item exists") is not a definition; define by what the later results use, or drop it;
  (b) never stack concepts without examples or motivation, and introduce a concept before its subdivisions;
  (c) requirements must be about the mathematics, not anthropomorphic properties of software ("honest tools");
  (d) motivation comes before machinery: the reader must know why we want something (avoiding re-extraction)
  before the section works toward it; (e) state established ideas as fact with a citation instead of narrating
  what an author wrote; (f) active voice, a present author; (g) a whole subsection drafted without a reviewed spine
  failed: when the user cannot critique a spine, the spine is the problem.
- **2026-11-04, §3 spine (decisions D1-D5 and comments on P1-P10).** D1: Pierazzi's setup goes into a "Background and
  Motivation" section. D2: no domain examples in the framework while the theory is drafted ("keep the theory pure");
  keep the removed examples in LaTeX comments. D3: the term and readout tables are "simply disgusting"; out of the PDF,
  source backed up. D4: no figures yet; make the core framework beautiful first. D5: paper title "Bridging the Gap: A
  Closer Look at Adversarial Examples in the Problem Space"; section "Measuring Edits Across Feature Mappings" (or
  "... Changes in the Feature Space"); every section or subsection title fits on one line. General: the feedback is
  guidelines, not rules; follow Pierazzi's notation (calligraphic $\mathcal{Z}$, $\mathcal{X}$, bold vectors). P2:
  consider a symbol for the reachable set (a stylized R, or common notation) only if it improves the paper. P3: the
  consolidation account was overblown: side effects need not exist, consolidation is not always needed, and side
  effects arise without consolidation; it needs nuance. P4 is the most important paragraph of the preliminaries (the
  motivation and the shared gap). P5: plain language first or definitions first, either way balance the abstraction;
  connections to type theory welcome if not pretentious. P6: "an iteration of an extractor loop" is too informal;
  rather "a collection of elements analyzed jointly by the feature extractor". P8: separate the readout definition from
  the sum-then-readout definition. P9: weave the connections to formal theory through the subsection instead of
  appending them. P10: replace the domain table by a short paragraph on how common these extractors are, with examples
  across domains. On §3.3 (edits): P11 and P14 related, but P12 and P13 felt disconnected and unnecessary; the user
  could not critique the second half from the spine and asked for a whole-section draft instead. Implied: (a) a
  subsection needs a thesis it builds toward, like a definition or a result; (b) state cited mechanisms with their
  real scope (can, often, not always); (c) defer tables and figures until the prose is right.
- **2026-11-04, §3 (framework, drafted 2026-11-02 before the paper-prose procedure), written review of §3.1.**
  Verdict: "so awful that it's hard to provide good feedback"; the math is mostly correct, the presentation is not;
  rewrite the whole section from a new spine, keeping the content. Genre: a textbook style like Pierazzi et al. (S&P
  2020, TOPS 2025) is welcome; budgets are loose. Section and subsection titles ("Computing What Edits Do to
  Features", "The Problem") are boring and clumsy. §3 needs a short lead (the most important section of the paper).
  Typography looks wrong; add a symbol table to the appendix (done; the user will comment on notation against it).
  ¶1: "the objects an attacker edits" is a wrong definition of the problem space (attackers edit feature vectors too,
  in feature-space attacks); h introduced but not needed unless used later; Pierazzi's four constraints named without
  a gloss (gloss them briefly or drop them); the reachable set and "realizable evasion" undefined and unaesthetic.
  ¶2: "as is *usually* the case in malware detection" (hedge accurately); consolidation reads as a new idea worth its
  own paragraph yet is brushed off; the paragraph drifts into our experimental method ("no clue what the topic of this
  paragraph is"). ¶3: "opens the box" and the whole paragraph are LLM slop; EMBER features have no place in the
  framework's opening. Implied: (a) a framework paragraph has one topic, and methodology belongs elsewhere; (b) define
  borrowed concepts correctly and in the source's terms (Pierazzi's side-effect features are the features altered to
  satisfy the problem-space constraints, i.e., by consolidation); (c) every symbol must be used later; (d) no
  domain-specific instance in the general opening; (e) no figurative announcements of what the section does.
- **2026-11-04, §6 paragraphs 1-4, revised draft.** Accepted: "quite good", still sounds a little like AI in places,
  and the user will clean up and tweak parts by hand. It reached the bar: worth the user's handcrafted attention.
  The goal of drafting with Claude (user): rapidly prototype correct, coherent, fluid prose that the user then
  fine-tunes. Below that bar, fine-tuning takes longer than writing from scratch. Implied: correctness and coherence
  come first, and the remaining AI flavor is acceptable at this stage; the next unit can be larger.
- **2026-11-04, §6 paragraphs 1-4, first written review (all four).** ¶1: drop the extended version of Pierazzi et
  al. (a duplicate citation adds nothing); "the constraints have no closed form" was paraphrased without the reasoning
  that makes it support the claim (the user could not see how a closed form would help); restate our term
  "sum-then-readout"; the last two sentences can be shorter. ¶2: Simonetto et al. and Chernikova and Oprea were
  described accurately but with no visible reason for being there; the line of work was never described as a whole,
  so Dyrmishi et al. could not be placed in it; "The constraints themselves have to come from somewhere" switched
  subtopic without a signal; "require their users" (who is the user?); the closing contrast was long-winded and weak,
  and the good Sheatsley sentence was held back by the vague first half. ¶3: no transition into the paragraph; Incer
  and Gimenez squeezed into one sentence; Chen 2021 read as "a random paper that did this thing"; the key claim
  ("Each of these needs to know which features ... can move") is powerful but arrived without lead-up and without
  saying which works it covers (cite them); "Hidost" never introduced; too many of our own experimental results (an
  RW section is about ideas and claims); the closing statement of our contribution was "extremely weak", as if we
  did not respect our own paper ("The route from directions to robustness is theirs. We supply the directions").
  ¶4: drop "as Section 3 acknowledges"; the incremental-view-maintenance sentence had no role in the narrative; "are
  the ones our sums and pools obey" and "supplies the translation ... lifts single edits to a whole threat model"
  read as LLM-written; the database-versus-adversary contrast needed to be stronger. Implied: (a) say why each work
  matters to the paragraph's thread in the sentence that describes it; (b) describe a line of work's mechanism before
  its members; (c) introduce every named artifact; (d) related work positions ideas, not our numbers; (e) state our
  contribution with conviction and specifics; (f) don't paraphrase a cited reason you cannot explain; (g) abstract
  verb metaphors (supply, lift, translate, obey) are an LLM tell.
- **2026-11-03, §6 paragraphs 2-4 (constraints; detectors; incremental computation).** Drafted with the
  `paper-prose` skill in one pass, written into the `.tex`, **not yet read by the user** (flagged `% REVIEW`). The
  user is satisfied with the method (spine, one unit, self-review, log, skill update) and wants the skill to need
  less feedback over time.
- **2026-11-03, §6 paragraph 1, fourth draft.** Right content, but less clear than before: "falling back to
  LLM-rhetoric style". The tics: an announced count ("Learning by trial has two costs."), colon reveals, an emphatic
  "exactly this way", a cadenced triad ("applies ..., extracts ..., and sees what moved"), a metaphor ("inherits the
  same blind spots"), and mirrored "follow exactly ... follow soundly". Implied: when tightening an argument, Claude
  slides into rhetorical staging; state the point in plain sentences instead.
- **2026-11-03, §6 paragraph 1, third draft.** Good through the side-effect sentence and after the Pierazzi part.
  "Every component is left abstract ..." sounded naive and did not name the real limitation. Example attacks
  (Šrndić and Laskov, Demetrio et al.) need no lengthy description unless they made a further foundational
  contribution; spend the room on the limitation of such attacks and on what our work contributes. Implied: say the
  limitation concretely; examples get a citation, not a summary.
- **2026-11-03, §6 paragraph 1, expanded draft (rejected).** "Choppy, a series of statements rather than a paragraph
  with a purpose." Specifics: (a) harping on Pierazzi's black-box extractor was misplaced, since *everything* in their
  framework is abstract, which is what makes it a framework; (b) the jump from Pierazzi to Šrndić and Laskov was
  abrupt; (c) Šrndić and Laskov's bigger-picture contribution was unclear ("why this attack and not dozens of
  others?"); (d) semicolons used to chain list items. Implied: a paragraph has one purpose and its sentences build
  toward it; every cited work earns its place by its role in our story; the link to our work must be explicit;
  never position against a framework's abstraction as if it were a gap.
- **2026-11-03, the spec itself.** Rejected: hard bans and required techniques. Habits are rationed by frequency, not
  banned; techniques are used when they improve a passage; organization and layout are suggestions. Take risks; human
  writing has variance.
- **2026-11-03, §6 outline.** Accepted: four groups (problem-space attacks; constraints over features; robust and
  monotone detectors; incremental computation and provenance), closest work first. Cut: abstract interpretation (it
  belongs in the body where we use it). Run-in bold heads, no line break after the head.
- **2026-11-03, §6 sample paragraph (problem-space attacks).** Liked; wants more detail (up to +50%).
- **2026-11-03, length.** Sections may run 50-75% over budget while drafting (Section 5).
- **2026-11-04, §5 price-list paragraph.** "A fine start" but "a consistent mildly LLM-sounding style"; asked for a
  quick humanizing pass, then into the manuscript. Removed in the pass: the fronted causal opener ("Because the table is
  derived per operation, it also prices each one"), personified bookkeeping ("where the 3.9 points go", "Nearly all
  the price is in the constraints", "two operations account for most of it"), the summary hedge "beyond noise", and an
  advisory closer ("so a defender can weigh each operation's cost before deciding ..."). Put in instead: "we retrained
  ...", literal verbs ("removing it recovers 2.1 points"), and a factual last sentence.
- **2026-11-05, §3 as a whole (before reading §3.3-3.4).** Cut the toy example everywhere and every passage tying the
  framework to real feature sets (EMBER, Drebin, Hidost, CICFlowMeter; to be refactored into §4). No replacement
  plain-language examples ("not necessary", open to debate). Tables 1-2 "so unpleasant that it is hard to look at the
  PDF": redesigned (short math cells, no prose in cells, footnotes for conditions) and moved to the proofs appendix.
  And: "at times extremely hard to review your work because the writing is so unpleasant and challenging to get
  through"; good writing is a precondition for good feedback. Implied: the prose itself must be easy to read before
  the user reviews content; tables are never prose grids.
- **2026-11-06, §3.1 review (session 17).** Mostly questions, from confusion: what the contribution function maps to
  (because the sum space $\mathcal{S}$ was "the product" with no structure stated, and $\oplus$ was mentioned in
  passing); whether the big $\bigoplus$ is the small $\oplus$; what "agree on $K_j$" means; whether the three monoids are
  the only ones. On the Gray et al. paragraph: "a very simple idea that you made very difficult to understand" (why a
  total combines over parts and an average does not), and "how small must the support be" was rhetorical: the
  sentence "didn't make any sense", "gibberish". A proposed sentence on extending to other monoids was "choppy and
  robotic. Write this like a human would." Wanted: the loop language after Def 1 grounded by a short generic code
  listing ("tight and clean"), Remark 1 (granularity) gone as a tangent, the lead's §3.3 description as a bridge
  (items vs elements) and §3.4 in one sentence, "without extracting" corrected (readouts are re-evaluated). Approved
  phrasing pattern: ", a property that we exploit in Section X". Implied: a definition must state the structure of
  every object it introduces (what an element of $\mathcal{S}$ is, how $\oplus$ acts) before anything maps into it;
  an idea from a cited work gets its simplest concrete illustration, not a compressed paraphrase.
- **2026-11-06, §3.1 round 2 and verdict.** "This is fantastic", then six small points: appendices referenced in
  order (A, B, C); in Def 1 a symbol ($M$, $z[M]$) was introduced two sentences before its name, and "elements" was
  not emphasized; $\oplus$ needed one line saying what it is; the "as $\sum$ combines with $+$" analogy was unneeded;
  Def 4's colon and an equation stated with no comment on what it means; the readout paragraph should open with Gray
  et al.'s classes so the rest follows; "take a few forms" undersold the point (breadth: many features reduce to the
  shape). After the fixes: "§3.1 has improved enormously based on this round of feedback and editing." Implied:
  the question-first review procedure works; the remaining defects were introduce/name/gloss mechanics (lesson 31).
- **2026-11-08, Sound Directions (rounds 1-2 of the sprint).** Round 1 (from an 18-paragraph spine): "pretty bad",
  stopped before Def 9: abrupt lead with a defender's perspective; operation, $\theta$, "operation instance", and
  threat model unexplained or redundant; Incer et al. and monotone detectors unintroduced; "We ask ..." unnatural;
  "sort" a bizarre definition; the replacement paragraph and the footprint lead-in purposeless. Round 2: "We're having
  major problems. You keep writing entire paragraphs that don't mean anything and don't add anything. Its incredibly
  frustrating ... utterly meaningless rambling." On the round-2 lead: "too much LLM-speech"; drop "such as appending
  every possible content"; elaborate "deltas are not known in advance"; say what "sound" means; the last sentence
  "pure gobbledygook". On Def 7: not informative (what makes the transformations a group?); why both operation and
  threat model?; the last sentence repeats the preliminaries. Implied: every paragraph must pass a job test (the
  paragraph gate, `paper-prose`), definitions must be informative and non-redundant, the framework is neutral.

- **2026-11-09, Sound Directions round 3** (13 paragraphs from the gated plan, ~1,040 words): "still extremely
  problematic." The comments follow in a new session. Implied so far: the paragraph gate cut length and empty
  paragraphs but did not make the subsection readable; the cause is not yet known (prose, structure, or what the
  mathematics shows).
- **2026-11-09, Sound Directions round 3, the comments** (verbatim in `docs/archive/framework/sprint-framework-review.md`). Liked: the
  lead ("quite good", wants only two small clarifications), Def 7 ("an enormous improvement"), the paragraph on where
  signatures come from, the sums paragraph ("pretty well written"). Lost from the sign sets on: "what the fuck are $A$
  and $B$?" (undefined, clashing with Prop 1), "Don't know what you're talking about"; the derived table reusing $D$:
  "Are you even paying attention to what you're writing? I'm starting to worry that this entire framework is one
  massive AI hallucination." The rewrite and its restrictions: "Isn't a rewrite just a remove and an add together?",
  "way too confusing", "perhaps a leftover". The Omega sentence and the lead-in to Def 8: too brief, "a little more of
  an explanation", two or three sentences. The last paragraph: delete. Wants Table 7 (readout rules) in the body.
- **2026-11-09, Sound Directions round 4, the holistic read:** "Overall, this is very good. I only have one criticism
  ... at times, it feels like you try to do too much with a single sentence." About half a dozen uncomfortably long
  sentences (lead sentences 2 and 4, Def 7 sentence 1); "Definition 8, sentence 1 is a good example of a long sentence
  that isn't confusing. It has enough structure and transitioning language to cover several concepts nested under a
  single idea." Six sentences split (commit 528fdbb).
- **2026-11-09, §4 block 1** (opening, EMBER paragraph, §4.1 Items, Sums, and Readouts; ~720 words). Opening: "quite
  verbose", the four parts "more succinctly"; the checks: "misguided. The fact that we tested our code and it works
  doesn't deserve this much of a spotlight ... one or two sentences, maximum, mentioned in a sensible location (not in
  the section lead)." EMBER paragraph: "needs to be a little more detailed ... the first time that we're mentioning PE
  files or malware ... maybe 30% more"; "needs its own subsection. Otherwise, its just a hanging paragraph,
  documenting some of the most important information in the entire paper." §4.1: "quite good ... no complaints about
  its contents or writing style", but "concerned about the bulk and volume ... Most of this is engineering and
  book-keeping material ... Its boring and takes up nearly an entire column (about 5% of a manuscript)"; asks to
  reassess the emphasis per part and appendix helpers.
- **2026-11-10, §4 block 1 redraft** (lead, 4.1 EMBER and PE Files, 4.2 paragraph 1; appendix D). Lead's last sentence
  ("an instance from another domain supplies the same four") "a little confusing"; wants a separate sentence with a
  clearer message: a new instance also needs to supply these four aspects. 4.1: header description "can be less
  specific and a less detailed (~10-20% shorter)"; the point of the headers is to store critical metadata and describe
  the rest of the file (locations, sizes, executability); "The reader doesn't need to know that a particular structure
  called the DOS Header exists". EMBER paragraph "good. No complaints right now." 4.2: the first sentence "jumps too
  quickly into the sum-then-readout perspective of EMBER"; transition "gently and effectively" from the description of
  EMBER. "Just say, 'our tests confirm that the readouts' instead of 'on 2000 files, the readouts'." General: "sentence-
  structure in this block is a little repetitive. Consider reducing the number of ':'s."
- **2026-11-10, §4.1 merged.** Asked to merge the PE paragraph and the EMBER paragraph (~50-100 words shorter):
  "A lot of the ideas between the two of these are shared: EMBER essentially represents the salient metadata and
  statistical properties of PE file structures." The merged draft interleaved them sentence by sentence (a PE part,
  then EMBER's features from it): "some aspects of it are poorly designed. You're bouncing back and forth between
  discussing the EMBER feature and the PE format which is extremely confusing." Hand edits to the first two sentences
  ("The instance we consider is ...", "(we use the most recent version, EMBER-v3~\cite{joyce2025ember})"). Rewritten
  as the format first, then EMBER's features over those structures.
- **2026-11-10, §5 block 1** (lead, 5.1, 5.2 realigned with §3-4). "I didn't review this carefully, but it looks
  reasonable. I have a pretty big concern about the structure and organization of this section ... out of scope for
  the current section ... finish writing up this section, to bring it up to date with the rest of the manuscript. We can
  address my structural concerns after that ... I suspect we're going to have to rewrite this anyway." Implied: for
  now, realign §5's vocabulary and claims quickly; the structural rewrite comes after.
- **2026-11-10 (session 31), §5 rewrite blocks 1-2** (lead, 5.1, 5.2 "What Hand Analysis Misses"). Lead "pretty good";
  asked for refs to 5.1 and 5.4. Setup: "Don't state that the experiment is at 'pilot scale'. Just state the numbers";
  cut "Every attacked file is written to disk..." ("it basically suggests that our code is correct ... its assumed that
  we tested our code thoroughly"); attacks paragraph overlaps §4.3 ("especially awkward if or when we incorporate another
  domain"); "weird, to state that the toolkit attacks come from Gimenez. Shouldn't we cite the original authors";
  "I don't know what 'a population of 10 for 10 iterations' means"; the seen/held-out split needs cross-validation
  ("Otherwise, its going to look like we're manipulating the experimental setup to our favor"); "The description of
  the adaptive attack is very dramatic. Just state what it is and cut all this decorative fluff out"; the last
  sentence (5,000 vs 100) "doesn't make sense. If its important, make it clearer"; par 3 is where to say files are
  re-extracted and briefly why; "a little too much information. Simplify and streamline"; "73063 edits" never
  explained. 5.2 par 1: "I'm completely lost by this first paragraph" (setup didn't prepare it, or it doesn't
  introduce the subsection, or both). Rest of 5.2: "written pretty well at the sentence-by-sentence level" but "lack
  of clear internal narrative and internal structure ... interleaves implemenation/experimentation details, results,
  and analyses ... challenging to skim"; suggested subsubsections or boldface demarcation.
- **2026-11-11 (session 35), second review of the §5 lead and 5.1 Setup** (revised version, 0069f56). Lead: "Can we
  clarify what we mean by 'and that each falls short'? I'm not sure if we actually made that claim before, so verify
  that. I think we could describe the limitation of the three ways people find the reachable set with a tad more
  nuance." Setup: "add a small transition at the beginning of the first paragraph"; "Why are we using a 10% sample of
  EMBER-2024? If this is just for the pilot study, ... one of the first things we need to do once we finish this
  write-up is scale this up"; the last sentence of paragraph 1 (threat model, byte budget) "might belong better in the
  second paragraph, since its about the attacks"; "What you mean by 'A defense that is learned from attacks' is
  unclear. Is this talking about adversarial training? If so, its completely vague. Also, use active voice"; "The
  adaptive attack has not been introduced yet, so the phrasing is not appropriate. Also, what exactly makes this
  attack adaptive? The fact that it combines different types of perturbations?"; "If the query budget matters little,
  why are we emphasizing it? All told, this paragraph is a confusing, unstructured mess"; label the paragraphs with
  run-in headings as in the next subsection; "The last paragraph has too much jargon."
- **2026-11-11 (session 35), the revised 5.1 (e3375ca), stopped in paragraph 2.** "You write that 'Unless stated
  otherwise, the attacks may use every operation of the full threat model...', but at the same time, we're using
  toolkit attacks that only apply a single perturbation, I thought? How does this make sense?" On the budgets: "Dude,
  holy shit, just fucking state the number of queries you're using. Why does it take you multiple sentences to
  communicate this astronomically simple fact? I had to read this like three times." "'it is designed against the
  detector it attacks' is completely and utterly inadequate to describe what you mean by 'adaptive'. Every attack in
  the paper is designed (to some extent or other) against the detector it attacks." The description of the adaptive
  attack: "completely and utterly autistic." "This is terrible and I didn't even finish the second paragraph."
- **2026-11-11 (session 36), the note before drafting §5.4 (seven open points, not prose).** On the sums row's
  adaptive cell (no run backs the footnote as written): "This is a pretty stupid issue to be concerned about." On
  making Table 4 one protocol by rerunning the adaptive cells on the 10% models: "We're obviously going to scale other
  parts of the paper up. Scaling this part down is braindead." On replacing the any-of-eight toolkit column with
  single-attack columns (memory `report-attacks-separately`): "This rule obviously wasn't meant to be everywhere.
  Again, this is pretty braindead." The rest (no 51%-vs-toolkit comparison, no 915/1,070 tightness number, cost
  paragraph dropped, title) "Sure." Then, after a plain explanation of 5.4: "Are we able to provide a meaningful
  result that security practioners will care about." Claude's answer (the expert-set comparison is the practitioner's
  result; 1% FPR is lenient, 0.1% shows ~10 points) was accepted ("Yes"). Blocks 1-2 of 5.4 drafted (8fd8c9c); no
  feedback on the prose yet: "I am too tired to provide feedback. Our work over the past two days has been exausting
  and quite disappointing."
- **2026-11-11 (session 37), §5.4 (8fd8c9c) reviewed by Claude with the humanistic-paper-review skill, at the
  user's request instead of their own review.** The review's headline: three paragraphs relied on something explained
  later (the population in *The price*, the additions threat model and its 92.2% in *Against hand-picked features*,
  the sums' advantage before *Where the cost lies*). The user: "I think I agree with the headline points, but less so
  with the small issues you've pointed out, e.g., the 'recurring patterns' and 'term ledger issues'." Asked why
  restructuring could work; after the explanation (order the paragraphs by the questions a reader asks in turn, so
  nothing points forward): "Yeah, I think we can apply the structural shift, then." Applied: price, where the
  guarantee holds, where the cost lies, width, hand-picked, beyond the guarantee.
- **2026-11-11 (session 38), §4 reviewed by Claude with the humanistic-paper-review skill (eight findings).** The
  user: "One of your goals seems to be to cut content and trim. This is good, but I think some of your suggestions are
  taking things to far. Moving very small snippets to the appendix, for example, is going to do more harm than good."
  On the Zainab et al. sentence: "It feels like we're stating this finding from the MAB-Malware paper but we aren't
  nessecarily applying it in our work. I'm not 100% whether we even need this sentence or what its value is." (Deleted
  after Claude found MAB-Malware uses code randomization, which the threat model excludes.) On signature vs.
  certificate: "Are the PE signature and PE certificate interchagable terms?" On the signature paragraphs of 4.3: "I
  don't 100% follow your suggestion." On 4.4: "I have no idea what this paragraph is tring to communicate." On the
  lead: replace the list "items, contributions, and readouts" with the sum-then-readout noun, "Then the fact that its
  a list four is clear." The two awkward sentences: "Both of those sentences you picked out are pretty ugly." On
  process: Claude renumbered the findings in its reply and proposed too large a first pass: "You've applied a new
  numbering system, which makes things extremely confusing. You're proposed first pass is also too ambitious. The
  point of breaking this up it to move some of the findings outside of my frontal cortex to allow me to focus on the
  remaining ones." First pass: findings 1-3 and 6-8; 4 and 5 later.
- **2026-11-12 (session 40), Claude's lightweight second review of §4 (three findings: 4.3.2's sample-based part
  vague, an interrupting sentence in 4.3.2 ¶3, closure stated flat in 4.4).** The user: "Nice analysis. #2 and #3 seem
  especially straightforward to fix. #1 might require a bit more care and reasoning, so think deeply about how you
  might improve this writing weakness and don't make mistakes. Go ahead and address the issues in the paper."
- **2026-11-12 (session 41), humanistic review of the §5 lead and 5.1, pass 1** (Claude's review, seven findings).
  Approved 1 ("the computation" named), 3 (the cost finding tied to the directions, "measurable" gone), 4-7 (declined
  edits sentence, the 100-vs-2,000 check with its reason, the parameter list trimmed, which detectors are monotone).
  On 2 (adaptive attack named in the lead before 5.1 defines it): "I think its okay to mention an 'adaptive attack' in
  passing in the section's lead. The lead doesn't need to formally define every concept. It just needs to give the
  reader a rough idea of what the section is about and what its purpose is ... I don't want to get into the details
  about the attack. For example, we could state something like '... in both cases a stronger, white-box adaptive
  attack confirms ...' which helps clarify the nature and role of the attack."
- **2026-11-12 (session 41), humanistic review of 5.2, pass 2** (seven findings). On 1 (the lead asks a question it
  never answers): "I want to make some serious structural modifications to this section with regard to how the
  research questions are presented, i.e., 'asked', and how the findings are presented, i.e., 'answered'. For now, we
  can make the suggested change (answering the question) just to keep the draft smooth, but note that at a later
  point, I want to apply structural enhancements to provide more visual emphasize to the questions and answers."
  Approved 2-6 and the two drift items (adaptive search -> attack; plain layouts -> population). On 7 (Rich header
  undefined): "I'm actually less concerned about this ... its a specific PE construct and the reader can look it up.
  We could clarify that its the 'PE file's rich header' or something if absolutely nessecary." On the review process:
  the user does not read the section end to end during the review, but approves or rejects each proposed change.
- **2026-11-12 (session 41), humanistic review of 5.3, pass 3** (five findings plus the "unconstrained detector"
  clause in 5.1). "I agree with your recommendation." All applied, including #2's rewording of what the derived table
  shows about the 142 features the attacks did not lower ("marks them as features an edit may lower", not "tells them
  apart").
- **2026-11-12 (session 41), humanistic review of 5.4, pass 4** (six findings). "I agree with your recommendation."
  All applied, including #2: the 0.1% per-operation costs ("about four") cut as within retraining noise, the noise
  caveat first.
- **2026-11-12 (session 42), Claude's holistic review of §5** (seven findings, weighted toward how much a reader will
  care about the contributions). 1 (no prior claims stated, so the findings read as truisms confirmed): "Agreed and
  approved. Let's do this carefully and thoughtfully to keep things tight and avoid too overlap with other sections
  like the background and related work." 2 (the lead gives mechanisms, not consequences): "Agreed and approved, albeit
  to a lesser extent. Out discussion and analysis of this should be brief." 3 (5.4 names one alternative) and 4 (5.2's
  cost paragraph concedes rather than states its stake): "Approved." 5 (5.3's topic sentences describe the defenses,
  outcomes later): "I don't know, I'm worried that this is trying too hard to curtail to a very lazy reader. We need
  to balance the needs of a fast reader and a deep reader. I'm open-minded, but right now, I'm not convinced." 6 (no
  table shows 5.3): "Sure, we can consider this when rebuilding the tables. But its needs more thought." 7 (§2
  promises an attack and a defense): "This is true. We have a weakness here that we can't immedietly fix. Make a note
  of it and we'll keep it in mind for the rest of the project."
  On Claude's reassessment of 5 (drop it: after finding 1, PV's paragraph runs from their claim to our replication to
  the rename; the fast reader has the leads): accepted implicitly ("I agree with that loose end. Please make that fix",
  on the uncited "usually tested against an attack it did not learn from").
- **2026-11-12 (session 42), the table remake, first attempt (mock-ups in
  `docs/archive/table-mockups-2026-11-12/`).** The user's brief before the mock-ups: "My general preference for tables
  is that they should err on the side of being 'data-dense' as opposed to 'linguistically-dense', although there are
  absolutely times when exceptions to this rule result in superior outcomes. We should design the table in a way that
  (i) effectively communicates out findings, (ii) is aesthetically pleasing, and (iii) is extensible if we later choose
  to add additional domains. Planning for extensibility is the most challenging of these, but also the most flexible;
  all told, it should be the least important consideration when designing the tables." On the mock-ups (option 1: the
  hand table's errors with Cause and Files columns; a new 5.3 table of the learned defenses with a "weight on
  lowerable" column; Table 4 in one column; a per-operation cost table; option 2: one detectors table grouped by where
  the directions come from): "Okay, these are pretty bad, quite possibly as bad if not worse than what we already had."
  No specifics given; the session ended there.
- **2026-11-12 (session 43), the table remake, restarted: what the user dislikes.** Asked with multiple-choice options
  (Claude's hypotheses). Table 4 and its one-column mock-up: all four picked (the footnote symbols, the long caption that
  argues the finding, phrase row labels, two threat models and two training sets in one table with empty cells).
  Table 3: "Prose cells", "Looks/typography", and "I don't know, maybe this shouldn't be a table? Would an enumerate of
  other structure look better and communicate the same information?" Good models: "My ExeFormer tables", "Lucas et al.
  Table 2", and "Almost any table in a published paper looks better than these. Seriously, these are the ugliest tables
  I have ever seen in my life. I'm open minded to figures, but if we can't figure out how to make a good looking table I
  don't think we'd be able to make a good looking figure." First to remake: Table 4.
  Shown the current Table 4 next to version A (two one-column tables: short row labels, arrows, bold best, one-line
  captions, evasion as counts, inside/outside the threat model for additions, adaptive results moved to the text):
  "Okay, this is not perfect, but its good enough that I can actually look at it, read it, understand it, all while
  not wanting to throw up. To improve these two tables, the main thing we probably want to do is improve the
  consistency between them, which might be out of scope right now, as it could involve running extra experiments.
  Anyway, its a decent improvement. Last thing: can we put the two tabular environments in the same table environment,
  to keep them together?"
  Table 3, shown as the current table (page 1), a slim one-column numeric table grouped by population (page 2), and a
  numbered list by cause replacing the table and "Why it errs" (page 3), with Claude recommending page 3: "Page 2 is a
  clear winner." Then, before it went in: "I'm undecided between page 2 and page 3. Think deeply about which option is
  more effective for our research as a whole. Then make your decision accordingly." Claude chose page 2 (the finding at
  a glance; PE parser details stay in a float and one sentence; the table's columns carry over to other extractors and
  domains; consistent with the new Table 4).
- **2026-11-12 (session 44), the check-in on more tables.** Claude laid out what each §5 subsection shows (5.2 and 5.4
  have tables, 5.3 none) and recommended one table, for 5.3. The user: "So we have a table for 5.2 and 5.4 but not 5.3?
  If that is the case, then I think a table for 5.3 is warranted, but only if the table can represent that section's
  question and that section's answer. What do you think?" Claude proposed a shape and named two snags (ERDALT falls to an
  attack it learned from; the "flagged beforehand" column measures different things per row) and asked which way to
  go. The user: "I would like for you to analyze the decision yourself and provide a recommendation."
- **2026-11-13 (session 53b, parallel to R7), R17: Theorem 1's monoids and the ratio's side condition.** Claude
  proposed four fixes from Reviewer A (W1, W3). On the universality/locality "gap" (any mapping fits with one
  whole-input item): "I mostly disagree ... The definition of an item is hierarchical: an object composed of items is
  also an item itself. If anything, this is a strength of the framework, not a limitation, because its still
  well-defined at its limits. ... the proposed fix presents a solution to a problem that doesn't really exist. Its not
  surprising that you would think this way: you've been trained to find vulnerabilities and exploits, minute cracks
  that no real human would notice or care about." (Open to a deeper exploration of how size and locality matter.)
  On "ordered monoids whose operation is nondecreasing in each argument": "very challenging to understand, which makes
  it difficult to appreciate, and impossible to apply." On adding a clause for the ratio's zero case: "Baking
  additional clauses into the framework to handle minute details like this can often be harmful." On the misleading
  minima sentence in Appendix D: "overstated. No human reviewer is going to identify this." Claude's second proposal
  (send other monoids and non-conforming ratios to the existing "both" fallback): "rather than fix the problems,
  you're proposing to essentially ignore them ... its also lazy and limits the strength of the framework. When I
  encouraged you to keep the solutions small and simple, I assumed you wouldn't propose bad solutions that are small
  and simple." Accepted: the weaker ratio condition (a = 0 whenever b = 0), which covers more ratios; the named
  property with the −3 example, after asking "does this type of monoid have a standard name ...? If we're referring to
  an established type of algebraic structure, that could help us simplify our explanation" and "Rather than deeply
  explain things ourselves we can provide a lighter explanation and refer the reader to the Fuchs paper."

**2026-11-17, §6 *Problem-space attacks*, cut from 160 to ~85 words** (Pierazzi et al.'s condition and their
formalization removed as repeats of §2; Šrndić and Laskov dropped; "Problem-space attacks, as formalized by Pierazzi et
al., search over transformations ... The toolkits ... work this way ... We compute the side effects from the extractor
itself ..."): "This is one of the worst things I have ever seen you write. I do not approve it." Reverted.
  The user, next turn: "The original paragraph wasn't that long to begin with, it read smoothly, and it emphasized the
  correct ideas at an appropriate level." (The cut version read as abrupt and jarring, in cruder words.) Kept as is.
