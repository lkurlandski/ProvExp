# Resume prompt (writing track): what goes in Appendix C and what stays in §3

Written 2026-11-19 (end of session 97). Nothing here depends on the scale-up on tigris. Read `CLAUDE.md` and this
prompt. Then read all of §3 (`manuscript/_d_framework.tex`, ~3,690 words) and Appendix C *Proofs for the Framework*
(`manuscript/_j_proofs.tex`, ~1,150 words). Open Appendix A *Symbol Table* (`_i_symbols.tex`) and Appendix B *Types,
Monoids, and Folds* (`_i2_types.tex`) only where the split touches them. Run on Opus. Use no subagents unless the user
asks.

## Where the writing stands

- **§3 was cut by 12% in session 97** (4,207 to 3,692 words; commit 652c1af). The mock's budget is 3,500. The user
  decided every item. Two small cuts were rejected and must not come back: the sentence after equation (6) on the free
  commutative monoid and the unique homomorphism, and "They do not form a vector, since their entries lie in different
  monoids". The three analogies (Gray et al., incremental view maintenance, abstract interpretation) were shortened,
  not cut. Lemma 1 stays in the body.
- **§3's structure:** §3.1 *Sum-then-Readout Extractors* (Definitions 1-5, Algorithm 1), §3.2 *Edits and Their Side
  Effects* (Definition 6, Proposition 1), §3.3 *Sound Directions* (Definitions 7-10, Table 1, Theorem 1), §3.4
  *Sequences and Robust Detectors* (Proposition 2, Lemma 1, Corollary 1). Appendix C has C.1-C.3, one per body
  subsection from §3.2 on. Check numbers against `manuscript/main.aux` before naming them.
- **Appendix B stays** as a stand-alone crash course on §3's background (user, session 96). Do not propose trimming it.
- **§6 Related Work is done for now** (session 84).
- The paper-prose skill is not used (user, session 92). What the user said about drafts is in `docs/writing-spec.md`
  (session 97's entry is the newest); read it as evidence of taste, not as rules.

## The task: revisit the body/appendix split

The user expected Appendix C to hold proofs only and found "some random other paragraphs", and asked why there are
definitions in the appendix. They want to revisit, as a question in its own right, what goes in the appendix and what
stays in the body. The earlier working rule (sessions 93 and 95: the body keeps the statements, the conditions a
reviewer would test, and the reason each result holds in a few plain sentences; the appendix keeps the derivations) is
up for discussion, not settled. A standing constraint from session 97: **body sentences are never moved to the
appendix to save words** ("That's confusing and creates more problems than it solves"); a passage is kept in the body
or cut.

Session 97's inventory of Appendix C, to verify against the file and present plainly:

- Proofs of numbered results: Proposition 1 (C.1), Theorem 1 (C.2, two sentences assembling other paragraphs),
  Proposition 2, Lemma 1, Corollary 1 (C.3).
- *Signs and directions* (C.2): defines the sign of a change (the body uses "sign" from Definition 7 on without
  defining it) and proves that a direction is closed under addition (Proposition 2's proof cites it). An unlabeled
  definition and lemma.
- *Directions of sums (Definition 9)* (C.2): the main step of Theorem 1's proof (each totally ordered sum changes with
  a sign in its direction). The heading names a body definition, which reads as if a definition sits in the appendix
  (session 96 renamed the headings this way).
- Table 7 and its paragraph (C.2): a catalogue of common contribution forms with their directions, justified row by
  row; §3.3 points to it and §4 uses it. Not the proof of any stated result.
- *Hashed keys* (C.2): two sentences justify Table 7's hashed row; the rest (brute force, the reply to Severi et al.)
  is commentary that §5's paragraph *Severi et al.'s hashed features* makes with data.
- *The readout rule (Definition 10)* (C.2): proves the rule and each row of Table 1, and carries a condition the body
  never states (a feature that returns a pool needs a default value at or below every contribution to a max pool, or
  at or above for a min pool; otherwise it takes Table 1's last row).
- After Corollary 1's proof: the credit to Gimenez et al.'s Proposition 1 (fine), and an extension the body never
  claims (a score that reads sums instead of features is also covered).

Options session 97 put forward, not decided: turn *Signs and directions* and *Directions of sums* into labeled lemmas
cited by Theorem 1's proof, and define the sign of a change in Definition 7; make Table 7 a stated lemma with its
proof; keep only the justifying sentences of *Hashed keys*; bring the pool-default condition into the body (e.g.,
Table 1's caption); cut the sums remark after Corollary 1. Present the question first (what the appendix is for, and
the options with a recommendation), explained plainly; get the user's decision on the principle before proposing
paragraph-level changes.

Also pending from session 97, small cuts the user has not yet decided (both plain cuts, no move): in §3.4, "A direction
table says which features the edits can only raise, which they can only lower, and which they cannot change, so it
says how the score must behave." (~30 words), and "Theorem 1 supplies the sound table, and Lemma 1 or a direct check
the closed population." (~20 words).

## How to work

- Use ranked findings or plan items with exact quotes, and get a verdict on each before applying anything. The user
  approves small clarity and consistency fixes directly; run larger changes to the language, structure, or claims by
  them first, with options and a recommendation.
- Apply approved fixes in one go, run `make` and `make check` in `manuscript/`, read the rendered text (pdftotext),
  commit, and report what changed with word counts (`texcount -brief`) before and after.
- When a fix rewrites prose, rewrite the passage so it flows at its new length.

## After this

**§4 Instantiating the Framework** (`_e_instances.tex`, ~1,830 words) with Appendix D *The EMBER Instance*
(`_j2_ember.tex`), using whatever split the user settles on here: review each subsection, then both together. §4.4
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
- §3.4's title, *Sequences and Robust Detectors*, was taken "for now".

## At the end

Add a short session-log entry to `docs/status.md` and commit the docs. Archive this prompt under `docs/archive/`, then
write the next resume prompt into this file.
