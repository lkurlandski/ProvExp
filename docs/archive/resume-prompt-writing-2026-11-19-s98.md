# Resume prompt (writing track): cut §3 to 3,000-3,250 words by letting the math talk

Written 2026-11-19 (end of session 98). Nothing here depends on the scale-up on tigris. Read `CLAUDE.md` and this
prompt. Then read all of §3 (`manuscript/_d_framework.tex`, 3,769 words) and, where a cut touches a proof, Appendix C
*Proofs for the Framework* (`manuscript/_j_proofs.tex`). Open Appendix A *Symbol Table* (`_i_symbols.tex`) and
Appendix B *Types, Monoids, and Folds* (`_i2_types.tex`) only where a cut touches them. Run on Opus. Use no subagents
unless the user asks.

## Where the writing stands

- **§3's structure** (check numbers against `manuscript/main.aux` before naming them):
  - Lead/roadmap, 116 words.
  - §3.1 *Sum-then-Readout Extractors*, 1,178 words: Definitions 1-5, Algorithm 1.
  - §3.2 *Edits and Their Side Effects*, 673 words: Definition 6, Proposition 1.
  - §3.3 *Sound Directions*, 1,267 words: Definitions 7-10, Lemma 1 *Directions of sums*, Table 1, Lemma 2 *Readout
    rule*, Theorem 1.
  - §3.4 *Sequences and Robust Detectors*, 535 words: Proposition 2, Lemma 3 *Closure*, Corollary 1.
  - Counts by `texcount -brief` on each subsection's text; captions are not included (Table 1's caption, 100 words,
    and Algorithm 1's, 36, count separately).
- **Session 98 settled the body/appendix split** (commits f84cfd4, 29ae165): Appendix C holds proofs only. Every
  definition, and every condition a stated result depends on, is in the body; every lemma is stated in the body with
  its proof in the appendix; commentary that no stated result needs is cut. Table 7 (directions of common
  contributions) and *Hashed keys* are switched off in an `\iffalse` block in `_j_proofs.tex`; leave them there.
- **Standing constraints on cuts:**
  - Body sentences are never moved to the appendix to save words (session 97: "That's confusing and creates more
    problems than it solves"). A passage is kept in the body or cut.
  - Rejected cuts, do not propose again: the sentence after equation (6) on the free commutative monoid and the
    unique homomorphism; "They do not form a vector, since their entries lie in different monoids"; the §3.4 sentence
    bridging Gimenez et al. to direction tables ("A direction table says which features the edits can only raise
    ...", kept in session 98 for that bridge).
  - The three analogies (Gray et al., incremental view maintenance, abstract interpretation) were shortened, not cut,
    in session 97; the user asked for shortening. Trim further only with a reason; ask before cutting one outright.
  - The lemma statements stay in the body (user, session 98).
  - Appendix B stays as a stand-alone crash course; do not propose trimming it.
- What the user said about drafts is in `docs/writing-spec.md` (session 98's entry is the newest); read it as evidence
  of taste, not as rules. The paper-prose skill is not used. A past over-compression of §6 was called "one of the worst
  things I have ever seen you write": a cut passage must still read smoothly and keep the right emphasis.

## The task

Cut §3 from 3,769 to **3,000-3,250 words**, about 500-750 words. The easy cuts are done (session 97). This round
trims **explanation and analysis**: "we'll let the math do more of the talking" (user, session 98). Candidates are
passages that restate in words what a definition, equation, or result already says; explanations after a result that
repeat its statement before giving its reason (keep the reason); running commentary that walks through a definition
clause by clause; and connective paragraphs whose content the next definition carries. The reason a result holds, the
conditions a reviewer would test, the counterexample for total order, and the ties to prior work are what the prose
is for; keep them, shorter.

Suggested order: present a plan per subsection with exact old and new text for each item and the words it saves,
ranked by savings, largest subsections first (§3.3, then §3.1). Get a verdict on each item before applying anything.
When a cut leaves a passage, rewrite the passage so it flows at its new length. Keep the totals visible: the target
range, the running count, and what remains.

## How to work

- Ranked items with exact quotes and replacement text; a verdict on each before applying. Small clarity fixes the
  user approves directly; changes to claims or structure go to them first with options and a recommendation.
- Apply approved items in one go, run `make` and `make check` in `manuscript/`, read the rendered text (pdftotext),
  commit, and report word counts (`texcount -brief`) before and after.

## Also pending (small, ask when convenient)

- Lemma numbering moved in session 98 (Closure is now Lemma 3); `docs/paper-mock.md` is updated. `PLAN.md`'s
  "Lemma 1 (*Closure*)" lines are history and stay as written.
- §3.4's title, *Sequences and Robust Detectors*, was taken "for now".

## After this

**§4 Instantiating the Framework** (`_e_instances.tex`, ~1,830 words) with Appendix D *The EMBER Instance*
(`_j2_ember.tex`), under the same split (definitions and conditions in the body, proofs and bookkeeping in the
appendix; Appendix D is not a proofs appendix, so settle with the user what it holds before cutting). §4.4
*Population* carries the closure check that §3.4 points to; keep them consistent. Then **§5 Evaluation**
(`_f_evaluation.tex`, ~4,100 words; pilot numbers, do not sync them; the user has not read §5 end to end). §2 comes
later; its closing sentence and contribution 4 of `docs/paper-mock.md` wait for the user's discussion of the
motivation (the *C.6 note* in `docs/status.md`'s session-80 entry). Not in this round: abstract, introduction,
discussion, ethics, open science.

## Open, ask the user first

- Tsingenopoulos et al. (`papers/tsingenopoulos2024train.pdf`) is the closest work; the reading is at the end of
  `docs/archive/related-work-plan-2026-11-17-s84.md`. Whether to compare experimentally is the user's decision.
- Giri et al.'s author names in `main.bib` (`giri2026towards`) are as printed ("K. A., Asmitha", "P., Vinod"); check.
- The byte budget (5% of the file or 512 KB) may be reconsidered later. Do nothing about it now.

## At the end

Add a short session-log entry to `docs/status.md` and commit the docs. Archive this prompt under `docs/archive/`, then
write the next resume prompt into this file.
