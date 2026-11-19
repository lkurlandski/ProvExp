---
name: cut-to-length
description: >
  Shorten a section of the ProvExp manuscript (manuscript/*.tex) to a word target without weakening it. Use when the
  user asks to cut, trim, tighten, or reduce the length of a section, subsection, or appendix. Holds the process that
  worked in session 99 (§3, 3,769 to 3,312 words): exact old/new text per item, measured savings, an assessment of
  each cut for correctness, the reader, and flow, and the user's verdict before anything is applied.
---

# Cutting a manuscript section to length

This is a process, not a style guide. What the prose should sound like is the user's taste (`docs/writing-spec.md`,
the user's accepted text); a cut must still read as they would write it. It was first run on §3 in session 99, after
the easy cuts had been made in session 97; the user called it "a very effective session".

## 1. Read and measure

- Read the whole section once, and the parts of other sections it points to (proofs, back-references).
- Count words with `texcount -brief -nosub` per subsection (captions count separately). Keep three numbers in view
  throughout: the target range, the current count, what remains.
- Read the newest entries of `docs/writing-spec.md` and the resume prompt's list of rejected cuts. A cut the user has
  rejected is not proposed again.

## 2. Draft the items

What to cut is the text that says again what something else already says: a sentence restating a definition, an
equation, or a caption in words; an explanation after a result that repeats its statement before giving its reason
(keep the reason); commentary walking through a definition clause by clause; a connective paragraph whose content the
next definition carries. What the prose is for, and so stays (shorter if possible): why a result holds, the
conditions a reviewer would test, counterexamples, scope, the ties to prior work, and the plain-language entry into
a hard definition.

Body sentences are never moved to an appendix to save words: a passage stays in the body or is cut.

Write each item as exact old text (copied from the file) and its replacement. When a cut leaves a passage, rewrite
the passage so it flows at its new length. Measure each item's saving rather than estimating it: put the pairs in a
small Python file in the scratchpad (`ITEMS = {"A1 lead": (old, new), ...}`), assert each old text occurs exactly
once in the file, and diff `texcount` of old against new. The same file later applies the approved items.

## 3. First pass to the user

Group the items by subsection, largest subsections first, ranked by savings, with the total and the landing count.
Mark with ⚑ the items that change what a reader is told. Short quotes for pure deletions, full replacement text for
rewrites.

## 4. Assess each item

The user asked for this in session 99, and it turned a good plan into an approved one. For every item, judge its
effect on three aspects, in this order of importance:

- **(i) Correctness and strength:** the mathematical correctness of the claims and how strong the framework or
  result looks.
- **(ii) The reader:** whether the audience (doctorate-level security, privacy, and machine-learning researchers)
  still follows the material and sees why it matters.
- **(iii) Flow:** narrative flow and the smoothness of the prose.

Where a cut costs (i) or (ii), propose a revision that keeps most of the saving with a few words back (a scope
clause, a soundness caveat, a term a later section refers back to, the one example a hard definition needs). Check
especially that no back-reference elsewhere loses its target, and that a cut does not undo a fix the user asked for
earlier (search `docs/writing-spec.md`).

Present the items **ordered from least to most disruptive**, each with its revised text (if any), its saving
(original → revised), and the assessment with **each aspect on its own line**, so the user can review quickly:

```
**7. B3 (−21): cut the gloss "A contribution is what one item adds…"**
(i) No effect.
(ii) Small: Definition 3 says the same; the Algorithm 1 example still grounds it.
(iii) Fine.
```

Give the new total after revisions and say plainly if it misses the target; the user may accept that ("It's okay
that we didn't quite hit 3250"). Offer the cheaper original for items where the revision buys little.

## 5. Apply, check, record

- Apply the approved items in one go from the items file; assert each match first.
- Run `make` and `make check` in `manuscript/`, then read the rendered section with `pdftotext`. Reading it catches
  what the items did not show in isolation (session 99: a revised sentence that, in place, said the same thing
  twice). Fix such slips directly if they keep the approved meaning, and report them.
- Commit, and report the counts per subsection before and after.
- Log the user's reactions raw in `docs/writing-spec.md`; do not turn them into rules here.
