---
name: paper-prose
description: >
  Draft or revise prose for the ProvExp manuscript (manuscript/*.tex) the way the user wants it to read. Use whenever
  writing or rewriting paper text: a section, a paragraph, a caption, the abstract. Holds the lessons distilled from
  the user's feedback on real drafts, the drafting procedure, and the self-review that runs before the user sees
  anything. Updated after every round of feedback.
---

# Writing paper prose for ProvExp

Reader model: `reader-model.md` (predicts how the user reads; used in step 8). Taste reference: `docs/writing-spec.md` (habits to ration, techniques, exemplars, layout) and its reaction log (the
raw feedback). This skill is the operational part: the lessons that feedback has taught, and how to work. Nothing
here is a rule to apply literally; real writing has variance, and a risk with a sentence is fine.

**The bar (user, 2026-11-04).** A draft must be correct, coherent, and fluid enough to be worth the user's hand
fine-tuning. Above that bar, drafting with Claude saves time; below it, fixing the draft takes longer than writing it
from scratch. So spend effort on what the user cannot cheaply fix (facts checked against the sources, each paragraph's
argument, the role of each citation, a confident statement of our contribution) over sentence polish, which the user
will do by hand. First accepted at this bar: §6 after one written review.

## Lessons from feedback

Each lesson names the round it came from (dates in the reaction log). Newest evidence wins; delete a lesson the user
contradicts.

1. **A paragraph is an argument, not an inventory.** Each sentence answers a question the previous one raised. If a
   sentence could be deleted or moved without the paragraph noticing, the paragraph is a list of statements ("choppy").
   For related work, the shape that worked: what the work contributes, what it leaves open, how practice fills that gap,
   what doing so costs, and what we do instead. (§6 ¶1, rounds 1-4)
2. **Critique at the level the work operates.** Know what a cited work set out to do before naming a gap; its design
   choices are not gaps. A framework is abstract on purpose. Name the limitation its authors would agree with, ideally
   one they state themselves (Pierazzi et al.: with a feature mapping that is neither differentiable nor invertible,
   side effects cannot be computed in advance, so they are found by trial). (§6 ¶1, round 2; example fixed 2026-11-04)
3. **Citations earn space by their role in our story.** The closest or foundational work gets a description. Instances
   of a class get a citation inside a sentence about the class. Ask "why this one and not the dozens of others?"; if
   there is no answer, it is an example and gets a clause. A work that gets a description must show its role in that
   sentence; an accurate summary with no visible reason reads as "a random paper that did this thing" (say Simonetto et
   al. made constrained attacks domain-independent, not only what their grammar expresses). (§6 ¶1, round 3; §6 ¶2-3,
   2026-11-04)
4. **Spend words where the argument is**: on the limitation and on what we contribute, stated concretely (what we
   compute, for which class of extractors, with what guarantee), not on summarizing others. (§6 ¶1, round 3)
5. **Sharpening is not staging.** When asked to tighten an argument, Claude slides into rhetoric: announced counts ("has
   two costs."), colon reveals, "exactly this way", cadenced triads, metaphors ("inherits the same blind spots"),
   mirrored pairs ("follow exactly ... follow soundly"). What worked instead: plain sentences joined by logical words
   (so, and, if, as do), compound sentences with causal joints. Also abstract verb metaphors for what our work does
   ("supplies the translation", "lifts single edits to a threat model", "the rules our sums obey"): say the computation
   literally. (§6 ¶1, round 4; §6 ¶4, 2026-11-04)
6. **Transitions come from logic, not adjacency.** The next sentence starts as an instance, consequence, or cost of the
   previous claim ("In practice, attacks find side effects by ..."), so no connector word is needed. But when the
   paragraph changes subtopic, or a paragraph opens, signal the turn with a sentence that links the two ("Both
   frameworks take the constraints as input, which leaves open where the constraints come from."); an aphorism ("The
   constraints have to come from somewhere.") reads as choppy. (§6 ¶1, round 2; §6 ¶2-3, 2026-11-04)
7. **Err toward more explanation.** The first sample was too thin; detail is cheap to cut later. Sections may run 50-75%
   over budget while drafting. (§6 ¶1, round 1)
8. **Small mechanics.** Commas, not semicolons, to chain list items. Cite one version of a paper, not the original plus
   its extended version. Drop pointers that do no work ("as Section 3 acknowledges"). (§6 ¶1, round 2; 2026-11-04)
9. **Describe the line of work before its members.** Open a related-work paragraph with what the approach does, in
   mechanism terms (keep the attack in feature space; write constraints; repair steps that violate them), so each cited
   work can be placed in it and its limitation follows from the mechanism. (§6 ¶2, 2026-11-04)
10. **Introduce every name and actor.** A named system (Hidost), a vague role ("their users"), or our own defined term
    (sum-then-readout) needs its gloss or the paper's term at first use in the section. (2026-11-04)
11. **Big claims need a runway and their citations.** Before a unifying claim ("all of these need the directions"), the
    preceding sentences should show each work needing it, and the claim cites the works it covers. (§6 ¶3)
12. **Related work positions ideas, not our results.** At most one pointer to our evaluation per paragraph, without
    numbers; the contrast is about what each approach can know, not what we measured. (§6 ¶3, 2026-11-04)
13. **State our contribution with conviction.** Close a positioning paragraph by naming what we compute, for which
    class, with which guarantee, and what it enables for the cited line of work, after naming the prior limitation
    concretely so the contrast is pronounced. Deference ("The route ... is theirs. We supply the directions.") reads as
    not respecting our own paper. (§6 ¶2-3, 2026-11-04)
14. **Never paraphrase a cited reason you cannot explain.** If a source's justification would not convince the reader as
    paraphrased (Pierazzi's "no closed form"), use the part of their argument that does (the feature mapping is neither
    differentiable nor invertible) or drop it. Self-review: for each "because X" about a cited work, can I say why X
    implies the claim? (§6 ¶1, 2026-11-04)
15. **Results paragraphs: report, don't narrate.** Say what we ran and what it measured, in the first person and with
    literal verbs ("We retrained ... removing it recovers 2.1 points"). Avoid the mildly LLM register: numbers that
    "go" somewhere, costs that "lie in" things, items that "account for most of it", "beyond noise", and closers that
    tell the reader what a defender can now do. (§5 price list, 2026-11-04)

16. **Framework prose: one topic per paragraph, every symbol earns its place.** A formal section may be textbook-like
    (Pierazzi et al.'s §II is the model: a definition, then a sentence or two of intuition and an example), but each
    paragraph introduces one concept and nothing from the experiments. Introduce a symbol only if a later definition,
    result, or table uses it; gloss a borrowed concept briefly and correctly in its source's terms (the problem space is
    not "what an attacker edits": feature-space attacks edit vectors). An idea raised only to say we do not handle it
    either gets its own paragraph or is cut. (§3.1, 2026-11-04)
17. **No instance in a general opening, no figurative announcement.** "This section opens the box" and an EMBER
    example in the framework's opening read as LLM slop. A section lead states, literally, what the section defines and
    proves and for which class of extractors; the running example arrives where it is first needed. (§3.1, 2026-11-04)

18. **Each subsection builds toward one formal endpoint.** A definition, a lemma, or a theorem, as §2 builds toward who
    needs the reachable set and §3.1 toward Definition 4. A concept with no role in that build-up moves to where it is
    first used (operations and threat models belong with the directions, not with single edits), and a concept that is
    an ingredient of the endpoint is introduced as one (locating positions answer "which items does a write change?").
    Weave the formal connections (monoids, aggregates, sign domains) in where they explain something, not in a closing
    paragraph. (§3 spine, 2026-11-04)
19. **State a mechanism with its real scope.** Cited concepts get the nuance their authors' examples allow: side effects
    can be zero, consolidation is often but not always needed, and side effects also arise without it. (§2 P3,
    2026-11-04)
20. **Theory first, decoration later.** While a formal section is being settled: no domain examples in the text (keep
    them in `% EXAMPLE` comments), no tables or figures, titles that fit on one line. (§3 decisions, 2026-11-04)
    Revised (2026-11-06): abstraction with nothing to picture fails (§3.2, 2026-11-05). A short, format-neutral
    pseudocode listing is the right kind of example in a theory section: §3.1's Algorithm 1 (three loops, `+=`/`max`
    updates, readouts at the end) grounded items, contributions, and readouts at once. Domain examples stay out.
21. **A definition must stand without glossing.** If a defined notion needs a paragraph of informal explanation to
    make sense ("identity: how the extractor reaches the item"; "positions that decide whether an item exists"), it
    is "wet clay" and a leaky abstraction. Define only what later results use, in terms already defined (content is
    $z$ restricted to the members, not a new symbol), or drop it. Def 2 (sums) was praised as "tight and
    intentional": that is the bar. (§3.1-3.2, 2026-11-05)
22. **Motivation before machinery, and one concept before its subdivisions.** The reader must know why we want a
    thing (finding the item delta without re-extraction: why avoid re-extraction?) before the text builds it, and a
    concept (locating positions) must be explained before its kinds or exceptions appear. Six concepts in a row with
    no example or purpose read as "an unhinged rant". (§3.2, 2026-11-05)
23. **Requirements are mathematics, not software virtues.** "Honest tools" was ridiculed ("honest computers, honest
    physics"). State an assumption as a property of the objects in the model (the delta an edit is given with), and
    move implementation checks to the evaluation. (§3.2, 2026-11-05)
24. **Established ideas as fact, a present author, active voice.** Pierazzi et al.'s framework is standard: state its
    ideas with a citation, not "Pierazzi et al. write ... Their account of ...". The register was "distant and
    passive". (§2, 2026-11-05) Recurred 2026-11-06: one attribution where the source is introduced, then plain
    statements with `~\cite` ("A transformation must satisfy four kinds of constraints~\cite{...}").

29. **Motivation: claim first, concrete outputs, no forward terms.** The paragraph that carries a section's main
    claim opens with it (here: attacks and defenses in both spaces all need part of R(z)), with each line of work in
    bold where it enters. Check the taxonomy for a missing cell (defenses in both spaces). A closing that names what
    we contribute is short, says what the reader gets and not "two descriptions", and uses no term a later section
    defines ("items"). (§2, 2026-11-06)
25. **Give space by later use.** Material the rest of the paper does not use (the four problem-space constraints,
    consolidation) gets a sentence; what the paper is built on (the reachable set) gets the emphasis. A list the
    reader must count (three viewpoints) should be visibly three. (§2, 2026-11-05)

26. **Develop the idea, skip the obvious.** After a definition, spend the paragraph on its one non-obvious
    consequence (pi forgets positions, so positions matter only through contents and through which items exist),
    not on facts the reader infers (a delta exists; there is a smallest one). In formal statements, name an object
    ($B$, the kept items) instead of writing index-heavy sums, avoid symbols that collide with our terms (Sigma vs
    "sum"), and define every term that is used alone ("pool"). (§3.2, 2026-11-05)

27. **Explain a result in words, and read the PDF.** After a proposition, say what it means in plain terms, why it
    holds, and why it is exact (here: the class is defined by the computation itself), as sentences, not as a chain
    of equation numbers ("(5) applied to (7)"). Never put an \eqref right after a symbol ("through pi (1)" reads as
    pi of 1). A subsection lead says what the subsection contains and its role in two or three sentences, with at
    most one pointer, in format-neutral verbs. Before showing a draft, read the rendered text (pdftotext) as the
    reader will. (§3.2, 2026-11-05)

28. **Readable before reviewable; tables are not prose grids.** The user cannot give content feedback on prose that
    is hard to get through, so a draft gets a readability pass before it is shown: one point per paragraph, short
    sentences after long ones, "lies within" instead of "whose members all lie in", no repeated "the proofs are in".
    A table cell holds a symbol or a short formula, never a clause; conditions go to footnotes. Lookup tables (sign
    rules) belong in an appendix, with two sentences in the body. (§3, 2026-11-05)

30. **State the structure before mapping into it; illustrate the cited idea simply.** A definition that says
    "the product of the monoids" without saying what an element is and how the operation acts leaves every later map
    into it unreadable ("what does the contribution map *to*?"). Write the element and the operation out, with a
    one-line formula. A borrowed idea (Gray et al.'s distributive vs algebraic) gets its plainest example (split the
    items in two: totals add, averages do not), never a compressed paraphrase; "a very simple idea that you made very
    difficult". A vague qualifier with no criterion ("a small support") reads as gibberish. A short generic pseudocode
    listing grounded the abstract loop/item/contribution/readout language. (§3.1, 2026-11-06)
31. **Introduce, name, and gloss together.** In a definition, a symbol and its name arrive in the same clause ("its
    *content* $z[M]$ is ..."), not two sentences apart. Every operator gets one sentence on what it does ($\oplus$
    updates the running totals). An equation inside a definition gets a plain sentence on what it means ("the
    readout depends only on the sums in its support"). Cut analogies that add nothing ("as $\sum$ combines with
    $+$"). A paragraph built on a cited concept opens with the cited distinction itself (Gray et al.'s two classes),
    and the rest follows from it. Frame a list of instances by its purpose: "many kinds of features reduce to this
    shape" (breadth), not "readouts take a few forms". (§3.1 round 2, 2026-11-06; verdict: "improved enormously")

## Procedure

1. **Spine first, always.** One line per paragraph (its claim, its citations or numbers), agreed with the user before
   prose. For a formal section, settle the architecture before the spine: which objects and maps exist, which result
   each subsection proves, and what each result needs. If the user cannot critique a spine, the spine is too abstract;
   fix it, do not draft past it (§3.2 failed this way, 2026-11-05). Keep this paragraph-by-paragraph plan even when the drafting unit grows to a whole section: it is where the
   user corrects the structure before it becomes "a spaghetti of a section" (user, 2026-11-04).
2. **Draft one unit** (one paragraph while the lessons are young; larger units as they stop drawing corrections, see
   step 6).
3. **Self-review before showing**, and fix what it finds:
   - Read the rendered PDF text of the passage, not the source (lesson 27).
   - Read the paragraph's sentences in order and ask, of each, what question it answers and whether the previous
     sentence raised it (lesson 1). Read first sentences only across the section (flow).
   - For each citation: why this work, and does its space match its role (lessons 2-3)?
   - Scan for the staging tics of lesson 5 and the rationed habits in `docs/writing-spec.md` §1; count them per
     paragraph, and cut any that cluster.
   - Check that every factual claim about a cited work is one we have verified; mark the rest `% VERIFY` and say so.
   - For each new symbol, operator, and equation in a definition: is its structure stated, is it named where it
     appears, and does a plain sentence say what it means (lessons 30-31)? Would a reader asking "what does this
     map *to*?" find the answer before the map?
   - For each described citation: is its role visible in its own sentence (lesson 3)? For each name: introduced
     (lesson 10)? For the closer: does it say concretely what we compute and enable (lesson 13)?
4. **Show the draft** with a short note of what changed and why. Do not hand over long prose unseen.
5. **Learn from the reaction.** Log it raw in the reaction log of `docs/writing-spec.md` (verdict, specifics, what it
   implies). Then update this file: add a lesson when the reaction generalizes beyond the sentence at hand, sharpen
   one when it recurs, delete one the user contradicts. Keep each lesson short with one concrete example.
6. **Widen the unit as trust grows.** When a unit is accepted with no or only minor changes, draft the next one larger
   (two paragraphs, then a subsection) before review. Status (2026-11-04): §6 reached the bar after one written review,
   so the next section (the introduction) is drafted whole, from an agreed per-paragraph spine.
7. **Revising after a written review** (worked for §2 and §3.1, 2026-11-06). Separate questions from feedback and
   answer the questions first, plainly and in words; a confusion usually marks a definition that does not stand on
   its own (lesson 21), so each answer also names the fix. Verify cited claims against `papers/` and the math against
   the proofs. Then a numbered plan, one item per comment, one recommendation each, open questions last, and no edit
   until approved. Implement an interlocking unit (a subsection whose definitions build on each other) in one pass,
   not piecemeal, and point the user first to the passages that are new prose, where the next round is likely. A
   second round of small, concrete fixes is implemented directly and reported per item. Apply the staging scan to
   the plan's own proposed sentences too (an announced count slipped into a proposal, 2026-11-06).
8. **Simulated review before the user reads** (sprint from 2026-11-06, `docs/sprint-framework-review.md`). For an
   existing draft the user has not reviewed, read it as the user would, with `reader-model.md` open: rendered text,
   paragraph by paragraph, each trigger as a question. Write the predicted review in the user's format (numbered,
   Q/F/M, confidence), answer the predicted questions, then propose a plan as in step 7. After the user's own review,
   score hits, misses, and false alarms, and update `reader-model.md` (misses become triggers, false alarms weaken
   them).
9. **Into the manuscript.** Write the approved text into its `.tex` file, `\cite` every work named (add missing entries
   to `main.bib`, checked against a real record), wrap at 120 columns, run `make` and `make check` in `manuscript/`,
   and commit in a logical piece.
