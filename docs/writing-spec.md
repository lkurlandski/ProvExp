# Writing spec: how the manuscript should read

A living document (started 2026-11-03; replaces `docs/style_guide.md`, which was written for the abandoned
explanation-provenance direction). It is a set of tendencies, not rules: there are no requirements in research
writing. **The arbiter is the user reacting to real draft sentences.** When a reaction contradicts this file, the
reaction wins and this file changes (log at the end).

Real human writing has variance, and that variance is where creativity lives. Do not apply anything here literally or
uniformly; a draft that obeys every line below will read as mechanical as one that ignores them. Taking a risk with a
sentence is fine.

Craft models: Pierazzi et al. (S&P 2020), Carlini and Wagner (S&P 2017), Arp et al. (USENIX Sec 2022). Voice
reference, lightly: the user's own papers (plain, declarative, first person plural). Format: `acmart sigconf` is fixed;
everything inside it is ours.

## 1. Habits to ration (sentence and word level)

Each of these is human in small doses. What makes prose read as machine-written is their *frequency*: the same move on
every page, or several in one paragraph. Use them sparingly and notice when they cluster.

1. **Throat-clearing.** "In this section, we ...", "It is worth noting that", "It is important to", "We now turn
   to", "Here, ...". Usually the claim can simply start.
2. **Connector tics.** Moreover, Furthermore, Notably, Importantly, Crucially, Additionally, Indeed at the head of a
   sentence. When two sentences need one to hang together, the order may be wrong.
3. **Rule of three.** Triads chosen for cadence ("simple, general, and exact") rather than because there are three
   things.
4. **Staged contrast.** "Not X, but Y", "X rather than Y" when no reader believed X. Strongest when X is what a
   reader would otherwise assume.
5. **Reveal punctuation.** "The answer: ...", em dashes that set up a punchline.
6. **Vague "this" as subject.** "This enables / ensures / allows / highlights ...". Naming the thing is usually
   clearer.
7. **Inflated words.** leverage, crucial, pivotal, seamless, landscape, delve, underscore, comprehensive, principled,
   rich, powerful, elegant, novel, holistic, nuanced. Praise of our own method reads better as a number.
8. **Paragraph-closing recap.** A last sentence that restates the paragraph ("In short, ...", "Together, these ...").
9. **Why-it-matters pairing.** Every claim followed by a sentence on its significance.
10. **Hedge stacks.** "may potentially", "can arguably". Scoping statements can be flat: "We do not compute
    consolidation."
11. **Uniform rhythm.** Every sentence 20-30 words, every paragraph four or five sentences. A short sentence after a
    long one is the commonest fix.
12. **Lists for arguments.** Bullets or stacks of bold labels ("Motivation. ... Design. ... Results. ...") where the
    content is a chain of reasoning.
13. **Parenthesis pile-up.** Several asides per sentence, or an aside that carries the actual claim.
14. **Synonym cycling.** "edit", "modification", "perturbation", "change" for the same thing. One term per concept,
    italicized once at first use, tends to read best.
15. **Internal IDs and lab vocabulary.** R1, C4, M_full, run numbers, script names, "go/no-go". These do not belong
    in the paper at all (CLAUDE.md).

## 2. Techniques worth reaching for

Use one when it would improve the passage at hand; none is a template.

1. **Plain first, then formal** (Pierazzi; C&W). The reader meets the idea in words before the symbols, and a display
   is followed by its gloss. C&W, after the optimization problem: *"That is, we want to find some small change δ that
   we can make to an image x that will change its classification, but so that the result is still a valid image."*
2. **Definition, gloss, example** (Pierazzi's signature). Formal objects tied to the running example (the appended
   URL).
3. **Concrete actors doing concrete things.** Prior work as "who did what to which object". Arp: *"Axelsson,
   McHugh, and Cardenas et al. investigate issues with the evaluation of intrusion detection systems, covering special
   cases of sampling bias (P1), the base rate fallacy (P8), and inappropriate performance measures (P7)."*
4. **Name the obvious alternative and why it falls short**, without adjectives. C&W on L-BFGS: *"This problem can be
   very difficult to solve, however, so Szegedy et al. instead solve the following problem."*
5. **One number that does work.** Arp: *"To our surprise, each paper suffers from at least three pitfalls."*
6. **A first sentence that carries the paragraph**, so that reading first sentences alone tells the story.
7. **Differences as different questions, not as weaknesses** (Arp's related work: "our study is more general").

## 3. Organization (suggestions)

"Organized" means the whole paper reads as one smooth narrative, a global property more than a local one.

- **Spine before prose** (trying it from §6 on). A section first gets a one-line-per-paragraph outline (its claim, its
  citations or numbers); prose follows once the outline looks right.
- **Flow pass.** After drafting, read first sentences only, then section openings and closings across the paper.
  Reordering often fixes a transition better than a connector does.
- **Visible decomposition** where the content really is a set of parallel units (Arp's P1-P10, Pierazzi's numbered
  Definitions), named and referred to by name afterwards.
- **Run-in heads** for groups of paragraphs: `\paragraph{...}`, which `acmart` sets in bold on the same line as the
  text (no line break; `\subsubsection` is also run-in but numbered).

## 4. Visual and layout (inside `acmart sigconf`; defaults, not requirements)

- **Tables:** `booktabs`, no vertical rules, few horizontal ones; numbers right-aligned with consistent decimals;
  captions say what the table shows and what to look at.
- **Math:** display what is referenced later; definitions and results as discrete, whitespace-framed environments
  (Pierazzi), with a gloss and the example nearby.
- **Figures:** one early overview figure that carries the idea (Arp's Figure 1, the workflow with pitfalls hung on its
  stages). Ours: the edit-to-features pipeline on the running example, in TikZ.
- **Variety:** pages that alternate prose, displays, small tables, and boxed definitions.

## 5. Length while drafting

At this stage length is very flexible (user, 2026-11-03): a section may run **50-75% over its word budget** in
`docs/paper-mock.md`. Truncating something too long is easier than understanding something too brief, so err on the
side of detail and cut later.

## 6. Reaction log

What the user accepted or rejected on real drafts, newest first. Each entry: the sentence or choice, the verdict, the
rule it implies (folded into Sections 1-5 if general).

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
