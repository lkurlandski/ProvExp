---
name: paper-prose
description: >
  Draft or revise prose for the ProvExp manuscript (manuscript/*.tex) the way the user wants it to read. Use whenever
  writing or rewriting paper text: a section, a paragraph, a caption, the abstract. Holds a description of the user's
  taste built from text they accepted, the few fixed constraints, and how to work with their feedback.
---

# Writing paper prose for ProvExp

**Rewritten on 2026-11-09.** The skill used to be a list of 36 lessons, a gate of 8 rules, and a reader model of
33 triggers. Each entry was one reaction of the user's, generalized beyond the sentence it was about. Followed
literally, several of them produced the patterns the user then complained about:
- "a definition, then a sentence or two of intuition" put a gloss after every definition;
- "a lead-in sentence before the statement" produced lead-in paragraphs;
- "err toward more explanation" pulled against "cut every paragraph without a job".

The user's verdict: a list of black-and-white rules in place of a feel for how they write. They had already said this
on 2026-11-03 ("no hard bans or required techniques"), and the skill drifted back anyway. The old material is in
`docs/archive/paper-prose-2026-11-09/`, to look things up in. It is not instructions.

**How to use this file.** Read the reference texts. Then write the passage the way their author would, for the reader
at that point in the paper. Do not check a draft against a list: a draft can pass every check and still be bad, and
it will be bad in a checklist-shaped way. The section on taste below describes judgement. Each part shows where the
user wanted more and where they wanted less, because the right call depends on the passage.

## The bar

From the user, 2026-11-04: a draft must be correct, coherent, and fluid enough to be worth their own fine-tuning by
hand. Below that bar, fixing it takes longer than writing from scratch. Spend effort on what the user cannot fix
cheaply: the mathematics, what each paragraph establishes, facts checked against the sources, and the role of each
citation. Polishing sentences is their work.

## Reference texts (read the relevant ones before writing)

Text the user accepted, in their own words. Write like these, not like a description of them.

- **§3.1** (`sec:fw:model` in `manuscript/_d_framework.tex`): "fantastic", "improved enormously". It defines the
  objects in order. Each symbol is named in the clause that introduces it. A short generic listing (Algorithm 1) grounds
  structure the reader could not otherwise picture. Gray et al.'s distinction gets its plainest illustration.
- **§3.2** (`sec:fw:side-effects`), as accepted after the user's hand edits (commit `5dcb9e7`): "quite satisfied".
  There is no example: the mathematics explains itself, and that is why. Def 6 is followed by one paragraph on the
  single non-obvious idea, that a delta forgets positions. After Prop 1 comes why it holds, part by part. The user's
  edits made the lead shorter ("give $z'$ exactly (before the edit is applied) and thus the side effects") and cut "In
  other words". Run `git show 5dcb9e7` to see how they trim.
- **§2** (`manuscript/_c_background.tex`) after review: established ideas are stated as fact with a citation. The main
  claim opens its paragraph.
- **§6** (`manuscript/_g_related_work.tex`): "quite good". Each cited work's role is visible in its own sentence. A
  line of work's mechanism comes before its members. Our contribution is stated with conviction.
- **The user's own papers**, `papers/kurlandski2027dont.pdf` and `papers/kurlandski2022impact.pdf`, are their voice.
  **Pierazzi et al.**, `papers/pierazzi2020intruiging.pdf`, Section II, is the model for formal sections in a
  textbook style. Carlini and Wagner and Arp et al. are also in `papers/`.

The user's hand edits are the best evidence of their taste. When they edit a passage, read the diff before writing the
next one.

## The user's taste, as judgement

**Understanding comes before prose.** The failures cluster where Claude had not settled what a passage establishes:
- the old §3.2 ("a completely unhinged rant");
- §3.3, cut after two rounds;
- Sound Directions, three rounds.

The successes came where the mathematics was settled: Def 2 ("tight and intentional"), Def 6 ("really good"), and Prop
1 in its second round. Before drafting, be able to say in plain words what the passage gives the reader, and why the
reader needs it at that point. If you cannot, the problem is not the prose, and rewording will not fix it. Say so to
the user.

**Explanation goes where this reader would get stuck, and nowhere else.** The user has asked for more:
- Defs 3 and 4 were "too thin";
- the §6 sample needed up to 50% more detail;
- Gray et al.'s idea was "made very difficult" by compressing it;
- Algorithm 1 helped in §3.1, where the structure could not be pictured;
- they wanted to know what a proposition means and why it is exact.

They have also asked for less:
- glosses that restate a definition;
- spelling out the obvious ("a delta exists, there is a smallest one");
- an example where "the math is somewhat self-explanatory";
- worked arithmetic;
- leads that tour other sections.

No fixed shape decides this. "Definition, then gloss" is not a pattern to follow. Ask where a careful reader, arriving
from the previous paragraph, would stop, and spend words there.

**A plain, literal, human register.** Say what is computed, with literal verbs and an author who is present. What
grates on the user is staging: announced counts, colon reveals, metaphors for what our work does ("supplies the
translation", "lifts", "opens the box"), anthropomorphic software ("honest tools"), passive distance, and advisory
closers. These habits are human in small doses. What fails is their frequency, and their use in place of content.
The user's own edits go toward shorter and plainer, not toward more polish. Sentence length follows the same judgement
(2026-11-09, Sound Directions round 4): a long sentence is welcome now and then, when its structure and transitions
hold several ideas under one (Def 8's first sentence, which the user praised); about half a dozen sentences that
chained clauses with "and ... so ... and" made the ideas harder than necessary.

**Every passage is there for the reader of the paper.** Text written to settle a point raised in the chat, to defend a
decision, or to head off an imagined reviewer reads as "paragraphs that don't mean anything". This is not a ban on
asides. The user called the databases remark in §3.2 "really cool": they objected only to where it sat. The question
is whether the reader is better off for it, at that place.

**Definitions are tight, and say what their objects are for.** Praised: Def 2 (sums) and Def 6 (item delta). Rejected:
- "identity" and "locating positions" ("wet clay", "leaky abstraction"), which needed paragraphs of glossing to make
  sense;
- "sort" ("bizarre");
- an operation defined only as "a set of transformations", which was empty, with two constructs where one would do.

A concept the paper never uses again is a cost. But "used later" is not the only reason for one to exist: the user
wanted readouts framed as a class of objects we identified, with breadth across domains.

**Cited work is described in its authors' terms.** Established ideas are fact with a citation (Pierazzi et al.'s
framework is "gospel"). A described work shows its role in our story in the sentence that describes it. Our own
contribution is stated concretely and with conviction, never deferentially.

**Structure is where the user wants to be consulted.** A plan of one line per paragraph lets them correct the
structure before prose exists. But a plan can be too abstract to critique (the §3.3 plan), and passing a plan does not
make a draft good: Sound Directions round 3 followed its approved plan exactly. When rounds keep failing, make the
unit smaller: one paragraph, reviewed, then the next.

What worked (Sound Directions round 4, 2026-11-09, after three failed rounds; the user: "This session felt very
effective ... drafting things out a few paragraphs at a time is more effective than drafting entire subsections"):
first a short note settling the mathematics (the objects in order, each with why the main result needs it), which the
user approved; then the subsection drafted in blocks of a few paragraphs, each shown as rendered text with what
changed, the user's comments applied before the next block, and what their comments on one block showed carried into
the next. Their comments per block were short and specific, and they found the blocks easier to judge than a
paragraph plan, which they said is more useful to Claude than to them. Consider this way of working for any new
section, not only after failures.

## Fixed constraints (decisions, not taste)

- No domain (PE) examples in §3; examples stay in `% EXAMPLE` comments. No internal IDs in the paper. Pierazzi et
  al.'s notation. Every section and subsection title fits on one line. No tables or figures in §3 for now.
- Every factual claim about a cited work is checked against `papers/`, and the rest is marked `% VERIFY`. Cite one
  version of a paper, add entries to `main.bib` from a real record, and `\cite` every work named.
- While drafting, length may run 50-75% over the word budget in `docs/paper-mock.md`. Report the length honestly.
- Into the manuscript: wrap at 120 columns, `make` and `make check` in `manuscript/`, no "??" in the PDF. Before
  showing a draft, read its rendered text (pdftotext) as the user will. Commit in logical pieces.

## Working with the user

- **Before writing:** a plan of one line per paragraph, saying what each paragraph establishes, agreed before the
  prose. Settle the mathematics first in a formal section. No manuscript edit until the plan is approved.
- **After a review:** answer the user's questions first, plainly and in words, because a question usually marks text
  that failed. Then a numbered plan with one recommendation per item, not a menu. Show what changed per comment.
- **Learning from a reaction:**
  - Log it raw in the reaction log, `docs/writing-spec.md`, as close to the user's words as possible. Fix the text.
  - **Do not add a rule.** If a reaction shows that the description of taste above is wrong or missing something,
    revise that description, with evidence from both sides where it exists.
  - Keep this file short (well under 2,000 words). When something is added, something becomes less relevant.
- **Before the user reads a draft:** read it as they would, linearly in the PDF. They stop where it becomes
  unreadable, they ask questions where it is unclear, and they flag both structure and small mechanics.
