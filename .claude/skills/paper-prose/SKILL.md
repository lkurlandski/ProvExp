---
name: paper-prose
description: >
  Draft or revise prose for the ProvExp manuscript (manuscript/*.tex) the way the user wants it to read. Use whenever
  writing or rewriting paper text: a section, a paragraph, a caption, the abstract. Holds the lessons distilled from
  the user's feedback on real drafts, the drafting procedure, and the self-review that runs before the user sees
  anything. Updated after every round of feedback.
---

# Writing paper prose for ProvExp

Taste reference: `docs/writing-spec.md` (habits to ration, techniques, exemplars, layout) and its reaction log (the
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

## Procedure

1. **Spine first, always.** One line per paragraph (its claim, its citations or numbers), agreed with the user before
   prose. Keep this paragraph-by-paragraph plan even when the drafting unit grows to a whole section: it is where the
   user corrects the structure before it becomes "a spaghetti of a section" (user, 2026-11-04).
2. **Draft one unit** (one paragraph while the lessons are young; larger units as they stop drawing corrections, see
   step 6).
3. **Self-review before showing**, and fix what it finds:
   - Read the paragraph's sentences in order and ask, of each, what question it answers and whether the previous
     sentence raised it (lesson 1). Read first sentences only across the section (flow).
   - For each citation: why this work, and does its space match its role (lessons 2-3)?
   - Scan for the staging tics of lesson 5 and the rationed habits in `docs/writing-spec.md` §1; count them per
     paragraph, and cut any that cluster.
   - Check that every factual claim about a cited work is one we have verified; mark the rest `% VERIFY` and say so.
   - For each described citation: is its role visible in its own sentence (lesson 3)? For each name: introduced
     (lesson 10)? For the closer: does it say concretely what we compute and enable (lesson 13)?
4. **Show the draft** with a short note of what changed and why. Do not hand over long prose unseen.
5. **Learn from the reaction.** Log it raw in the reaction log of `docs/writing-spec.md` (verdict, specifics, what it
   implies). Then update this file: add a lesson when the reaction generalizes beyond the sentence at hand, sharpen
   one when it recurs, delete one the user contradicts. Keep each lesson short with one concrete example.
6. **Widen the unit as trust grows.** When a unit is accepted with no or only minor changes, draft the next one larger
   (two paragraphs, then a subsection) before review. Status (2026-11-04): §6 reached the bar after one written review,
   so the next section (the introduction) is drafted whole, from an agreed per-paragraph spine.
7. **Into the manuscript.** Write the approved text into its `.tex` file, `\cite` every work named (add missing entries
   to `main.bib`, checked against a real record), wrap at 120 columns, run `make` and `make check` in `manuscript/`,
   and commit in a logical piece.
