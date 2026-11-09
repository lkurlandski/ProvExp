> Archived 2026-11-09. Lookup only: these are past readings of the user's feedback, not instructions. The current skill is `.claude/skills/paper-prose/SKILL.md`.

# Reader model: how the user reads a draft

Used in the self-review sprint (`docs/sprint-framework-review.md`, step 1): read the rendered subsection as the user
would and write down the comments they would write, then fix them, so that the user's first read is of the improved
version. Built from the reaction log in
`docs/writing-spec.md` (2026-11-03 to 2026-11-06). The lessons in `SKILL.md` say how to write; this file predicts how
the user reads. **Update it after every round:** each comment the user still makes on the improved version is a trigger
this file lacked or one the revision did not act on; add or sharpen it, and weaken one that produced a false alarm. Keep each entry to a trigger, a real quote, and the question to ask.

## How the user reads and comments

- **Linearly, in the rendered PDF**, paragraph by paragraph, with headers per subsection and bullets per point, in
  the order of the text. They stop where a passage becomes unreadable and say so rather than pushing through
  ("unintelligible", "stopped at §3.3").
- **Questions first, from genuine confusion.** A question ("what does it map *to*?", "is this big ⊕ the same as the
  small one?") almost always means the text failed, not the reader. Several questions in one passage mean the
  passage is the problem.
- **Mixed granularity in one review:** structural verdicts (a tangent to remove, a paragraph to rewrite) next to
  small mechanics (a missing comma, a colon, appendix order, emphasis on a defined term). Expect both.
- **They propose alternatives as options** ("(i) remove ... or (ii) a code example; do you think one would help?")
  and want a recommendation back, not a menu.
- **They reason about the design, not only the text:** "we could represent items as (type, content, position);
  would that simplify the framework?" Predict design questions where a convention is a choice with alternatives.
- **They distinguish "brief is fine" from "wrong":** "I'm not necessarily asking you to change the prose ... this is
  for my own clarity." Mark predictions that are clarity questions, not change requests.

## Triggers, by kind

### Confusion (highest yield: these become questions)

1. **An object whose structure is never stated.** "What does the contribution function map *to*?" because 𝒮 was
   "the product" with no element or operation spelled out. Ask: for every set, space, or operator introduced, could a
   reader say what one element looks like and how the operation acts?
2. **A symbol before its name, or a name before its symbol.** "Introduces M and z[M] but doesn't name them until two
   sentences later." Ask: does each symbol arrive in the same clause as its name and emphasis?
3. **An equation in a definition with no plain gloss.** "The identity is not explained ... its relevance is
   unclear"; "what does 'agree' mean here?" Ask: is there a sentence saying what each displayed condition means?
4. **A vague qualifier with no criterion.** "How small does the support have to be?" (rhetorical: "didn't make any
   sense"). Ask: small, few, most, usually, local: is there a criterion, or is it hiding a gap?
5. **A cited idea compressed into a paraphrase.** Gray et al.: "a very simple idea that you made very difficult to
   understand". Ask: is the borrowed idea given its plainest concrete case, opening with the source's own
   distinction?
6. **The same notation, two meanings, or two notations, one meaning.** Big ⨁ vs small ⊕; "sum" as our term and as
   Σ. Ask: does any symbol or word look like it means two things?
7. **A claim the user can check and finds loose.** "We claim we can determine the change without extracting, but
   don't we re-apply formulas?" Ask: is each capability claim literally true, including what is still computed?
8. **Abstraction with nothing to picture.** §3.2 without examples was incomprehensible; Algorithm 1 fixed §3.1.
   Ask: could the reader draw or write code for this concept? If not, a generic listing or a two-line case helps.
   But only for unfamiliar *structure*: a worked example of arithmetic the reader can follow ("delete the record of
   length 5", max of {5, 3}) "largely fails" and is "more work than thinking about the math" (§3.2, 2026-11-07).
9. **Equation numbers or pointers used as arguments.** "What the hell is pi (1)"; "(5) applied to (7)". Ask: does
   any sentence lean on \eqref or a section pointer instead of saying the thing?
10. **Concepts stacked before motivation.** "Why would we avoid re-extraction?" Six concepts with no purpose read as
    "an unhinged rant". Ask: before each new concept, does the reader know why we want it?

### Structure

11. **Tangents.** Remark 1 (granularity): "a tangent that distracts from the main ideas". Ask: does each
    paragraph or remark serve the subsection's endpoint (lesson 18)? A defense against a reviewer objection belongs
    elsewhere.
12. **The lead or a description that misstates a subsection's role.** "As I understand it, 3.3 bridges the
    item-based and element-based views." Ask: does each pointer say what the target contributes, in one sentence?
13. **Obvious facts spelled out while the real idea is under-developed.** "Under-appreciated, under-emphasized,
    under-discussed" (positions forgotten by π). Ask: what is the one non-obvious consequence here, and does it get
    the paragraph?
14. **A dense formal statement.** Prop 1 "extremely dense". Ask: could the statement name an object (B) instead of
    an index-heavy formula, or split into a sentence and a short list?
15. **Missing human interpretation of a result.** "No interpretation of what the proposition gives, nor why it is
    exact." Ask: after each result, is there a plain "what it says, why it holds, why it matters"?
16. **Purpose of a list misframed.** "Take a few forms" vs "many kinds of features reduce to this shape". Ask: is
    the list there to show breadth, and does the framing say so?

### Register (the user flags these on sight)

17. **LLM staging:** announced counts ("at the cost of two things:"), colon reveals, cadenced triads, metaphors,
    mirrored pairs; "choppy and robotic". This includes Claude's own proposed sentences in a plan.
18. **Slop closers and figurative announcements.** "This section opens the box"; a last paragraph that restates.
19. **Distant or passive register; narrating authors.** "Pierazzi et al. write ..." -> state as fact with a cite.
20. **Software virtues as assumptions.** "Honest tools" -> "honest computers, honest physics".
21. **Needless analogy or domain word.** "As Σ combines with +"; "parses". Ask: does the clause add anything?

### Added after §3.2 (2026-11-07)

23. **Pointers without need.** "References past and future parts of the framework without good reason"; "no need
    for a forward reference to 3.3". Ask: does the reader need the other section to follow this sentence? If not, cut
    the pointer (a lead has at most one).
24. **A concession with no consolidation.** "Feels like we're admitting to a significant limitation ... without any
    consolidation". Ask: does a sentence about what the model forgets or cannot do also say why nothing is lost or
    where it is handled?
25. **A formal statement with no lead-in, or a wrong joint.** Prop 1 "feels abrupt"; "In particular" before parts
    that are consequences, not special cases. Ask: does the sentence before a statement set up its first equation,
    and does the joint word match the logic?
26. **A remark inside a statement.** "Which the item table ... determine, but ... do not": "important, or word
    salad?" Ask: is every clause of a proposition part of the result? Negative remarks go to the explanation, with why
    they matter.
27. **A paragraph with several jobs, or one that jumps back.** "Summarizes, relates to side effects, and justifies";
    "now we're jumping back to (i)!?"; "written without any real plan". Ask: what is this paragraph's one job, does the
    justification follow the parts in order, and does each paragraph move forward?

### Added after Sound Directions (2026-11-08)

28. **A paragraph with no job.** "Entire paragraphs that don't mean anything and don't add anything"; "what is the
    purpose of this?"; "again, what are you trying to communicate?" Ask, of every paragraph, new or inherited: which
    later result uses it, or which question of the reader does it answer? A gloss after a definition, a roadmap, a
    disclaimer, a restated definition: the user reads these as rambling, and they stop reading.
29. **An empty or redundant definition.** "What about the set of transformations makes us group them?"; "if a threat
    model is just a set of operations, why do we need both?"; "Def 8's first sentence seems to define 'sort' to mean
    items are changing". Ask: does the definition say what makes its objects belong together and what they are for?
    Could one construct replace two?
30. **Unexplained machinery in a definition.** "Why is $\theta$ needed? 'Indexed by' isn't helpful"; "what's an
    operation instance?" Ask: is every index, parameter, and coined term needed by a result, and is its purpose in the
    sentence that introduces it?
31. **LLM-speech in a lead.** "Too much LLM-speech"; an illustrative aside ("such as appending every possible content");
    a claim with its reason missing ("deltas are not known in advance"); "proves that the bound is sound" with sound
    undefined; a last sentence that is "pure gobbledygook". Ask: does each sentence of the lead state something the
    reader can check?
32. **Perspective.** "Takes the defender's perspective"; the framework should be neutral (how and where features
    move). Ask: is the subsection's goal stated without attackers or detectors?
33. **A repeated sentence from preliminaries.** "The last sentence just repeats what's already been covered by the
    preliminaries." Ask: does any sentence restate §2 without adding to it?

### Mechanics (small, but reliably noticed)

22. Appendices or sections referenced out of order; a missing comma after an appositive; colon placement inside a
    definition; a defined term not emphasized; a term used alone but defined only inside a list ("pool").

## What the user does not comment on (avoid false alarms)

- Exact numbers and word counts while drafting; page limits; length up to 50-75% over budget.
- Pure sentence-level rewordings with no gain in clarity (memory: no pedantic rewordings). Grammar that obscures
  meaning (colon, comma) does get flagged.
- Notation choices already deferred ("tau for kinds acceptable for now"), unless a clash causes confusion.

## Calibration (update after each scored round)

| Round | Predicted (step 1) | Rejected in step 3 | User comments on improved version: missed / fell short / introduced / new taste | Notes |
|---|---|---|---|---|
| §3.2 (2026-11-07) | 15 (P1-P15) | 0 of 8 plan items | 4 / 6 / 6 / 1 (+1 design note) | Problems found were real; per-comment patching added unplanned paragraphs. Round 2 from a paragraph spine: "quite satisfied", only hand edits for terseness. |
| Sound Directions (2026-11-08) | 26 (P1-P26) | 0 of 18 spine items (Q2 changed: keep the symbol) | round 1: 9 / 3 / 5 / 1 (stopped before Def 9); round 2: "paragraphs that don't mean anything", stopped again | The review flagged real problems but scanned inherited text lightly and planned a gloss after every definition. Gate added (SKILL.md, top). |
