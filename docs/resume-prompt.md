# Resume: general work, and the index of the tracks

Written in session 82 (2026-11-17). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading first. Since
session 82 the work is split into tracks, each with its own prompt; this one holds general work and keeps track of the
others. Pick the track the user names; if none is named, ask which.

## 1. The project in brief

ProvExp is dissertation research on *sum-then-readout* feature extractors, the kind security classifiers use: find
the pieces of the input (items), add up what each contributes (sums), compute each feature by a formula over a few
totals (readouts). From the instrumented extractor we compute what an attacker's edits do to the features: exactly for
one edit (Proposition 1), as sound directions for a whole threat model (Theorem 1), and from those, monotone detectors
no edit in the threat model can evade (Corollary 1). PE malware on EMBER2024 is the instance. The paper
(`manuscript/*.tex`, ACM CCS format) is drafted on pilot-scale results; the scale-up (PLAN.md step 3) replaces every
number.

## 2. The tracks

| Track | Prompt | State (session 84) |
|---|---|---|
| The scale-up's experiments on the cluster | `docs/resume-prompt-experiments.md` | `toolkit`, `adaptive` and MAB-Malware `ours` submitted without ERDALT, waiting for nodes; check them, fix failures, right-size, read |
| ERDALT's collapse | `docs/resume-prompt-erdalt.md` | the retrain on the new material collapses too; a 7-task GPU diagnosis (port or method?) is read next, then the user decides the retrain; ERDALT's attacks and `6-results` wait on it |
| Theory: bounds on size | `docs/resume-prompt-theory.md` (Opus) | mathematics done (`docs/evidence/theory-analysis.md`, part H); the user decides what enters the manuscript, H.5 first |
| Writing: manuscript review | `docs/resume-prompt-writing.md` | §6 cut to 1,284 words (session 84); next the humanistic review and polish of §3, §4, §5, one subsection per pass; §2 after |
| General work | this prompt | below |

## 3. General work (no cluster, no numbers)

1. **§2's closing and contribution 4 aligned with §5** (PLAN.md step 4). §2's closing says §5 "uses them to attack
   malware detectors and to build robust ones"; in §5 the attack is an instrument that tests the directions and the
   defenses. §5 shows three findings: hand analysis misses side effects that come from how the parser locates
   structures; defenses learned from observed attacks inherit those attacks' blind spots; with the directions known,
   robustness against the whole threat model costs a measured few points of detection. `docs/paper-mock.md`'s
   contribution 4 states the three; its "four to six points" waits for the scale-up. A discussion with the user first
   (session 80's C.6 note in `docs/status.md`), then the text with the `paper-prose` skill.
2. **Waiting on the user, when convenient:** a close read of Lemma 1 (*Closure*) and the readout rule (§3.3, Table 1,
   Appendix C); the holistic read of Sound Directions.
3. **Follow-ups from the theory session 74, none started** (PLAN.md step 8 (c)): the instance-level work for Lemma 1
   (the population's clauses as counts over items, the derived table rebuilt, the operations confirmed; §4.4's
   "closure is checked" changes only then); `4-detectors/monotone-check` run at the scale-up so §5.1's blue sentence
   can be confirmed or reworded (`sbatch pipeline/4-detectors/monotone-check/run.sh`, read-only, seconds).
4. **After the scale-up is read** (PLAN.md steps 5-7): the final numbers into §4-5, shortening §4-5, a second domain
   (the user's call), then the introduction, discussion and abstract.

## 4. Rules that apply

Explain plainly; a hypothesis before running anything; report a failed check as such. The user decides protocol and
claim questions; Claude recommends. Paper numbers come from the compiled PDF (`manuscript/main.aux`). Write paper prose
with the `paper-prose` skill; compile with `make` and `make check` in `manuscript/`. Commit to `main` in logical pieces
(ruff and strict mypy on `src tests pipeline`); do not push. On the cluster: do not watch the queue (user, session 82).

## 5. At the end of the session

Update `docs/status.md` and PLAN.md, update this prompt's track table, and archive what it replaces as
`docs/archive/resume-prompt-<date>-s<N>.md`, with its line in `docs/README.md`.
