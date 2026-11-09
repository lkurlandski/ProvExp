---
name: slides
description: >
  Draft or revise the Beamer slide deck in slides/slides.tex (talks to the user's advisors about the framework and
  results). Use whenever writing, revising, or extending slides. Holds the lessons from the user's feedback on real
  slides, the procedure, and the visual check. Updated after every round of feedback.
---

# Writing slides for ProvExp

The deck is for **communication**: advisors who are sharp but have not read the manuscript. A slide succeeds if its
point lands in the time it is on screen. The source of the content is the manuscript (`manuscript/_c_background.tex`,
`_d_framework.tex`, ...) and the design docs (`docs/archive/framework/framework-design.md`); the slides simplify it, they do not copy it.

## Lessons from feedback

1. **Light math (2026-11-05).** Math carries the high-level ideas only. No monoid definitions, no typed tuples, no
   proof detail; a symbol appears only if the talk uses it again. Say in words what a formula would say, unless the
   formula is the idea (e.g., the reachable set, $\varphi = \rho \circ \sigma \circ \pi$).
2. **Few words, one line per point (2026-11-05).** Cut hanging clauses ("..., though no section was touched",
   "..., which ..."). Each point fits on one line; a label plus one short line beats a sentence. Drop words the
   picture already says. High white space is the goal. First accepted at this bar: Part I after one tightening pass.
3. **Short labels in tables.** One line per row; shorten row names ("Constrained attacks") rather than shrink below
   `\small` or let cells wrap.
5. **Show code for the shape (2026-11-05).** A short, generic Python version of an extractor (after the toy format)
   makes the three stages concrete. Mark the stages with colored labels inside the listing (`\stage{color}{...}` via
   `escapeinside`), not in a side column: side labels drift out of line with the code.
4. **One example, concrete.** One PE example per idea is welcome (the advisors know PE); the toy format carries the
   mechanics.

## Procedure

1. Outline the part (one line per slide: its title and its one point), agree on it if the part is new.
2. Draft the frames. Each frame: a title that states the point or the question, one picture or block, at most ~4
   short lines of text, a one-line takeaway at the bottom when it helps (`\vfill` before it).
3. Build: `cd slides && make && make check` (must report no overfull boxes).
4. **Look at every changed slide** before showing the user: `pdftoppm -r 70 -f <first> -png slides.pdf
   <scratchpad>/<new-folder>/p` and read the PNGs. Use a fresh folder per round; never `rm` old previews with a
   wildcard (it trips a safety prompt). Check for wrapped one-liners, collisions in TikZ labels, crowded columns, overflow at the bottom.
5. Report briefly what each slide says; flag choices the user may push back on.

## Clean-up pass (after a deck or part is complete)

Read the deck end to end as the audience would, then check:
- **No claim twice** on neighboring slides (e.g., "same structure as EMBER" on both the toy and the code slide).
- **Every toy entry follows from what the slides said.** A direction or number that needs an unstated rule gets the
  rule (one gray line) or a toy definition that makes it follow.
- **Color carries meaning:** red/alert = a problem or limitation, green = what works, blue = neutral. A "Next"
  pointer is blue, not red.
- **No overclaims** ("for free", "provably" where only "by construction" holds).
- Column headers short; the setup of a worked example stated above the table, not packed into its headers.

## Layout conventions

- Preamble: beamer 16:9, 11pt, default theme, blue frame titles, colored blocks (block / alertblock / exampleblock);
  `\good{}` / `\bad{}` for green/red emphasis. Keep it.
- Diagrams in TikZ, straight arrows, labels placed so they do not sit on arrows. Do not name a style `step` (a
  built-in TikZ key; the build fails).
- Two columns: `\begin{columns}[T]` with widths summing to <= 0.94; keep each column's lines short enough not to wrap.
- Citations go in a gray `\footnotesize` footer line (authors, venue, year), not inline where they wrap the point.
  Describe cited work accurately even when short (e.g., Gimenez et al.'s directions are hand-picked *or* learned).
- `\vfill` to spread content vertically instead of fixed `\vspace`.
- One `%%%%` banner line before each frame; a banner comment per part.
