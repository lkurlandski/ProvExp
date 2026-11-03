# Resume: ProvExp (after 2026-11-03, session 8): build the manuscript writing-and-presentation spec, then draft the empty sections

## Where things stand

Session 8 was **planning, not drafting**. Two things happened, and the second is now the primary track:

1. **The holistic stock-take against the 2026-11-02 review is done** (full R1-R16 table in `docs/status.md`, session-8
   block). Tiers 1-2 resolved essentially every writing and small-experiment risk; the two materially open levers are
   **R4 (a second built instance)** and **the empty paper sections**. Decided with the user: the empty sections come
   next (second instance stays a later, tier-3 decision), and the introduction is **framework-first with a
   detector-centered results paragraph** (the deferred framing decision, now settled).
2. **The user is dissatisfied with Claude's manuscript writing and presentation**, at three levels: sentence/word,
   structure/organization, and visual/typography. The core aversion is prose that "sounds like an LLM" (confusing and
   boring). So **before drafting the empty sections, we are building a shared writing-and-presentation approach.** This
   is the next session's work. Nothing is pushed. See the memory `manuscript-writing-style-overhaul.md`.

`run/122` (the adversarial-training row) is **still running** (launched by the user 2026-11-03 ~15:08, `NUM_WORKERS=24`,
~8-9 h). It was NOT finished this session, so Table 7's `\synthetic` adv-training row is **untouched** -- do not
fabricate it. When it finishes (`artifacts/experiments/a1/advtrain/`, `artifacts/logs/a_advtrain_*`,
`a1_eval_advtrain.log`, `a1_adaptive_advtrain.log`), a session replaces that one row from the measured
AUC / TPR@1% / detected / seen / held-out / adaptive-union, honestly (expected: seen ~0, held-out little changed,
adaptive ~20%, competitive with the unconstrained row, not the sound 0%), then `make`/`make check`.

## The primary task: a writing-and-presentation spec, then one calibration section (user, 2026-11-03)

The agreed pathway, and the reasoning behind it (do **not** relitigate this -- it was worked out carefully with the
user over a long discussion):

- **Why not just draft.** The user's taste is latent and they can't fully articulate it; a cache of "things we like"
  will NOT by itself fix the writing (knowing the principles was never the problem -- Claude still defaults to the LLM
  register). What actually moves the writing is (a) an explicit **anti-pattern kill-list** (the LLM tics:
  throat-clearing openers, "Moreover/Notably/Importantly", triadic/rule-of-three cadences, uniform sentence rhythm,
  hedging, turning everything into a bulleted list) and (b) a **tight feedback loop on real draft sentences**, where the
  user's reactions teach the gradient. The spec is scaffolding for the loop and a shared vocabulary, not a substitute.
- **Who to model on.** Model the **craft** (sentence economy, structure, keeping every abstraction tied to a concrete
  example) on the papers the user **admires**, the gold-standard exemplars -- NOT on the user's own papers. The user is
  a newer researcher and explicitly said their own writing is not the craft target. Their own two papers matter only as
  a light **voice** reference (so the result reads like a human researcher wrote it, not like a generic AI or a Carlini
  impression), and that use is vetoable.
- **The arbiter** is the user reacting to actual draft sentences. No exemplar overrides "I don't like this"; the
  exemplars only get the first draft into the right neighborhood.
- **"Organization"** means the whole document reads as one **smooth narrative** -- a global, emergent property. It is
  handled by agreeing the section arc/outline up front and doing read-for-flow passes, NOT by assembling a list of local
  traits. (The user corrected an overweighting of "abstract mirrors the paper" -- that is a minor local trick, not what
  makes a paper organized.)
- **Format constraint:** ACM CCS / `acmart sigconf` formatting is fixed (fonts, margins, spacing). The conventions
  within it (table/figure design, how math is presented, section/paragraph structure, whitespace, TikZ) are ours.

### Concrete steps for the next session

1. **Read the gold-standard exemplars for craft.** Pierazzi (S&P 2020) is **done** (takeaways below). Add
   **`carlini2017towards`** (Carlini & Wagner -- the clear/precise/elegant ideal) and **`arp2022dos`** (Arp -- organization
   and decomposition). All PDFs are in `papers/`, named by citation key. Use `pdftoppm -r 100 -png` to render a couple of
   representative pages per paper and Read them for the visual/layout axis (text alone misses it).
2. **Skim the user's own two papers** (`kurlandski2022impact`, `kurlandski2027dont`) **lightly, for voice only** -- not
   as a craft model, and skippable if the user prefers.
3. **Write a SHORT spec** -- a new living doc (propose `docs/writing-spec.md`), which **replaces the stale
   `docs/style_guide.md`** (that was written 2026-10-14 for the abandoned explanation-provenance direction; it still
   talks about "pullback"/"pushforward"). The spec is mostly the **anti-pattern kill-list**, plus a few positive craft
   patterns and two or three exemplar passages to aim at. Keep it short; it is not an exhaustive catalog of all twelve
   papers.
4. **Then draft ONE real section to calibrate** -- **related work (§6)**, chosen because it is factual and low-risk.
   Outline before prose; run the tight loop with the user; refine the spec from what they accept and reject. **Never
   hand over ~1,000 words of prose unseen.**

The other admired exemplars (for later, as rhythm targets / breadth, not all to be fully cataloged):
`carlini2023extracting`, `lucas2023adversarial`, `raff2021classifying`, `alam2023recasting`, `pendlebury2019tesseract`,
`wang2019neural`, `xie2027daugl`. The user warned: do **not** over-weight papers published after 2024 (AI slop is
entering the literature), and papers from China-based university labs read as a formulaic/ESL register to avoid (treat
as a prose-register signal, not a judgment to repeat).

### Pierazzi (S&P 2020) -- craft takeaways already banked

- **Prose:** economical, plain-first; the intro opens on deployed reality in one sentence, narrows to the specific
  problem by the second, almost no notation in the first paragraph; key terms italicized once at first use and reused
  verbatim; one concrete framing stat does real work; no filler. (The S&P version is much tighter than the arXiv/journal
  extended version -- the user's taste is for the disciplined register, not the author per se.)
- **Organization:** the idea is previewed in plain prose before it is formalized (reader meets the idea in words before
  the symbols); a numbered chain of Definitions. **Signature move: definition -> informal gloss -> concrete example**,
  every time; the formalism never floats free of an example. Directly relevant to our dense, example-thin §3.
- **Layout:** two-column (close to our CCS density); each Definition a discrete whitespace-framed unit; numbered display
  equations; examples in brackets keep formal text grounded.

## The stock-take result (condensed; full table in `docs/status.md`)

Against `docs/reviews/2026-11-02-body.md`: **addressed** -- R1(b/c/d), R2, R3, R5, R6, R7(in .tex), R8, R10, R12, R13
(by reframing), R14, R15(in .tex), R16(rejected with reason). **Partially addressed** -- R1(a) (the twelve-op adaptive
search was built/run but did NOT beat the toolkit on the undefended model, because that model is genuinely robust to
in-catalogue edits; so the independent evidence rests on out-of-model toolkit outputs + "still detected", and the 0.0 is
framed as an implementation check -- honest caveat), R4 (scope reduced only; second instance not built), R9 (no speed
claim; deliverable lands in the empty §1), R11 (C4 rows consistent; sums-row routing deferred by design). **Still open /
deferred:** R4 second instance (tier-3 decision); RQ1-RQ3 labels never added (cosmetic); routing to Table 7's sums-row
adaptive cells (needs a design decision); `run/122` adv-training row.

## Deferred / carry-forward (unchanged)

- Table 5's population-scoping not re-audited (recorded user decision; leave unless revisited).
- Routing to Table 7's sums rows (`--route <c4>=ref`): `a1_adaptive.py` has no routing and the engine predicts only in
  thrember space; bring a concrete plan before touching the sums-row adaptive cells.
- A G1 unit test for the expert instrumentation is a nice-to-have.
- `tests/test_shortcuts_*` fail to collect (pre-existing, not from recent work).
- The user still owes the upstream reports in `docs/upstream-issues.md` (incl. the expert set's two quirks).
- The empty-sections order, once the writing spec exists: related work (§6) and introduction (§1) first, then background
  (§2), discussion (§7), Figure 1, abstract last (`docs/reviews/2026-11-02-body.md` §2/§7; `PLAN.md`). Drafts to reuse:
  the review's §8 (contributions list, key-insight sentence, introduction argument), the §5/§6 related-work lists and
  fair characterizations; `docs/paper-mock.md` for budgets.

## Working notes

- Only run jobs under ~10 min yourself (estimate from the slowest case); otherwise smoke-test and write a `run/` script
  (next number **123**), reading `NUM_WORKERS` when it has a worker flag.
- **Safety-classifier false positives / `/delegate`:** the main session's classifier can false-positive on fine-grained
  per-sample analysis of our own detectors/search logs. Workaround: isolate the unit, write a measurement-framed prompt,
  run it on a fresh subagent on a simpler model. The `/delegate` skill captures this.
- At the end of each session: update `docs/status.md`, `PLAN.md`, and this file. Commit in logical pieces; do not push.
