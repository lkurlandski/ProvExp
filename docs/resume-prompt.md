# Resume: rewrite the paper mock (after the 2026-11-09 holistic review)

Read `docs/status.md` and `PLAN.md` (especially "Decisions of 2026-11-09"). Open other documents only as this task
needs them (index: `docs/README.md`).

## The task

Rewrite `docs/paper-mock.md` against the manuscript's new §3 and the decisions of 2026-11-09. The user approves the
mock before any section of the paper is rewritten. Keep it to at most two pages, as before.

What it must settle:

1. **Contributions**, restated in §3's terms (sum-then-readout extractors; Proposition 1; signatures, the derived
   table, Theorem 1; Corollary 1), with no requirements, footprints, or Theorems 2-3.
2. **§4 as the instantiation template** (decision 1): its general opening (format-free, in §3's terms), the four
   template parts, EMBER filling them in the body, and the "instances at a glance" table that other domains would
   extend. A word budget per part.
3. **§5 organized by §3's results** and aligned with §2 (decision 4): for each of §2's four lines of work (problem-space
   attacks, feature-space constraints, problem-space defenses, feature-space defenses), say whether §5 shows it, with
   which table, or whether §2 should narrow. Recommend one option, with the trade-off, for the user to decide.
4. **What each table claims** (decision 3: Table 5 shows that the instrumentation and the operations' changes are
   correct; decision 2: the coverage of the write operations' signatures is checked on the corpus, stated in a
   sentence). Measured vs missing, as before.

Inputs: the manuscript (`manuscript/_c_background.tex` through `_g_related_work.tex`), the current mock (stale in
parts; keep what still holds), and PLAN.md. The evidence records (`docs/evidence/`) only if a table's content is
in question.

## After the mock is approved

PLAN.md's next steps 2-5: the read-only code audit (does the code compute the derived table as Definitions 9-10
define it?), then §4 and §5 rewritten in blocks with the user's review after each (`paper-prose` skill), then the
research-track items.
