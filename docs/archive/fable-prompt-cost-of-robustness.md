# Fable session: what robustness must cost, and how to lower what it need not

Draft of 2026-11-15 (session 71), for one session on Claude Fable 5.2 while the credits last (until 2026-11-17).

**How to launch (the user):** a fresh session in the repository, `/model` set to Fable 5.2, effort **high**. Paste
everything below the line. If the credits run out or a turn is stopped, switch to Opus with `/model` in the same
session: the findings file is committed part by part, and Opus can continue from it.

---

This session has one research question about the theory of this project, and I want your best mathematical thinking
on it. You are being used here because this is the hardest judgement in the project and the credits for you are
limited, so spend them on thinking, not on reading or on bookkeeping.

## The question

The paper proves that a detector whose score is monotone with respect to a sound direction table cannot be evaded by
the threat model (Corollary 1, from Theorem 1). On EMBER this guarantee costs clean detection: at pilot scale, TPR at
1% FPR falls from 93.5% (unconstrained) to 85.7% (monotone, on the sums), and more at 0.1% FPR. I do not consider that
small; I would like about one point. The paper currently reports the cost as a measurement and cannot say what it is
a cost *of*. I want the theory to say it. Split the cost into three parts:

1. **Intrinsic.** What *every* detector that the threat model cannot evade on the population must give up, whatever
   its form. If most of the cost is here, the paper gains a strong finding: the price is the price of robustness to
   this threat model, not of our construction, and the per-operation costs say which attacker capability is expensive.
2. **Abstraction.** What is lost because the table records only a sign per feature. Detectors exist that no edit can
   evade and that are not monotone with respect to the table; the table forgets how sums move *together* and by *how
   much*. If a meaningful part of the cost is here, I want the smallest extension of the framework that recovers it
   and that a practitioner can use (for example: further quantities, computed from the signature, that are safe to
   give a monotone detector).
3. **Learner.** What is lost because our gradient-boosted trees with per-feature monotone constraints are not the
   best detector that is monotone with respect to the table. Comparing learners one at a time (a monotone MLP, lattice
   networks) is ordinary experimental work for afterwards; what I want from you here is only whether the best
   achievable detection of *any* table-respecting detector can be bounded from the data, without training a
   particular learner. I suspect such a bound may be vacuous (with 2,568 features most pairs of files are
   incomparable under the table's order, so a best-case fit may be nearly perfect); if so, say why and whether a
   restricted version, such as on held-out data or with a capacity limit, says anything useful.

What I want from you: (a) the mathematics that makes this split precise in the framework's terms, with proofs or
counterexamples: a converse or characterization for Corollary 1 (when is "monotone with respect to the table"
necessary, not only sufficient, and what exactly breaks it), and a way to bound parts 1 and 3 from data without
training or attacking anything, if one exists; (b) your honest assessment, from the per-operation costs we already
measured, of where the 8 points probably lie; (c) if part 2 is worth pursuing, a concrete proposal for the extension,
stated in the paper's notation, with its proof obligations and what it costs in pages and new concepts; (d) one cheap
experiment per claim that Opus and I can run at pilot scale afterwards, with the outcome you predict (a comparison
with another monotone learner may be one of them).

These are starting points, not a specification. If you see a better way to make the theory serve the detectors (or a
reason the question is wrongly posed), say so and follow it. A clean negative ("the cost is intrinsic, here is the
proof and here is the check") is as useful to me as a way to lower it.

## The project in a paragraph

Security classifiers see feature vectors, not inputs. For extractors that find the pieces of the input (items), add
up what each contributes (sums, each a commutative monoid: additive, max pool, min pool) and compute each feature
from a few sums (readouts), we compute what an attacker's edits do to the features from the instrumented extractor:
exactly for one edit (Proposition 1), as a sound table of directions (fixed, up, down, both) for a whole threat
model over a closed population (Theorem 1), and from that, monotone detectors no edit of the threat model can evade
(Corollary 1). The framework is format-free; PE malware with EMBER2024 is the instance. The paper targets ACM CCS.

## What to read

`CLAUDE.md` loads by itself. For this session, do **not** read `docs/status.md`'s log or `docs/resume-prompt.md`.

- Fully: `manuscript/_d_framework.tex` (§3), `manuscript/_j_proofs.tex` and `manuscript/_i2_types.tex` (the proofs
  and the algebra), `manuscript/_c_background.tex` (§2).
- In `manuscript/_f_evaluation.tex`: only §5.4, *What Robustness Costs* (search for `What Robustness Costs`; the
  paragraph *Where the cost lies* has the per-operation costs). Numbers there are pilot values.
- In `manuscript/_e_instances.tex`: §4.2-4.4, for how a signature and a population look in a real instance.
- `PLAN.md`: "Thesis", decisions 10 and 11, "Settled decisions". `docs/paper-mock.md`: "Dropped from the paper".
- `src/provexp/featuresets/ember2024/sums.py` and `directions.py`, only if you need to see what the detector on the
  sums reads and how the table is built.
- In `papers/`, as needed (search by author): Gimenez et al. 2025 (monotone detectors; our Corollary 1 builds on
  their Proposition 1), Incer et al. 2018, Chen et al. 2021, Calzavara et al. 2020, Cousot and Cousot 1977. Check a
  claim about a cited work against its PDF before relying on it. If the question touches results you know from the
  robustness literature (lower bounds on robust error, monotone or isotonic classification), name them and say
  plainly what would be ours and what is theirs; I would rather hear it from you than from a reviewer.

**Do not open** `src/provexp/attacks/`, `src/provexp/featuresets/ember2024/escapes.py`, `third_party/`, `run/`,
`pipeline/5-attacks/`, or the R7 and R18 evidence records. Nothing in this session needs them. Keep the work at the
level of §3: items, sums, readouts, changes, tables. Do not write or modify code that edits files.

## What is settled (do not reopen without a strong, argued reason, in its own section)

- The formalization is a contribution. Be harsh about novelty but fair; cite foundations as foundations, and never
  write a borrowed-versus-new ledger of the results.
- §5 presents findings about adversarial examples, not a defense paper: the detector's cost is a measurement, never
  called small, and there is no state-of-the-art defense claim. A result about *what the cost is a cost of* fits
  this; a new defense with a leaderboard does not.
- Elegant extensions only: prefer one that reuses what the framework already has (signatures, changes, the fold)
  over new hypotheses or clauses. Coupling between features, the tightness of the reachable region, margins and a
  cost theorem were dropped earlier for complexity, not for being wrong. Bringing a relative of one back is allowed
  here, because it would now serve the detectors; say explicitly when you do, and what it costs.
- The framework stays format-free; PE specifics may explain a number, never enter a definition.
- The signatures of operations stated as writes, and closure, are checked on a corpus, not proven. Accepted.
- No timing claims. No packing. No engagement with database provenance beyond citation.
- The entry write (`ent`: the certificate and debug directory entries set to any value) is in the threat model by my
  decision; it makes ten features two-sided and costs 3.9 of the points.

## How to work

- Think first, then write. Lead every item with the plain-language version (what is computed, what it is compared
  with, why it matters), then the mathematics. Define any term the paper does not. I could not follow jargon-heavy
  explanations in the past.
- Say how confident you are in each claim. "I believe this but could not prove it" is useful; a confident claim that
  turns out false is costly. Try to break your own statements with small examples before you rely on them.
- You may run a short computation (about ten minutes or less, on the pilot stores under `artifacts/`) when it
  decides between two readings; state what you expect before running it. No training runs, no featurization, no
  attacks, no subagents.
- Write to **`docs/evidence/fable-cost-of-robustness.md`** as you go and commit after each part (`git add` that
  file only; end the message with the `Co-Authored-By` line from your instructions). Do not edit the manuscript,
  the code, or `PLAN.md`; do not push. At the end, add one line to `docs/status.md`'s "Waiting on the user".
- While reading the proofs, note anything wrong or any gap a formal-methods reviewer would raise, with the smallest
  fix as old and new text. Keep this to a short section; it is a by-product, not the task. (Already found: the
  ratio rule of Table 1 needs $b \ge 0$, which its caption does not state.)
- Paper numbers (definitions, tables) come from `manuscript/main.aux`, with the title alongside.

## The findings file

1. **The answer in half a page**: where the cost lies, what the theory can say about it, what you recommend.
2. **The mathematics**: statements in the paper's notation, each with a proof, a proof sketch and its obstacle, or
   a counterexample.
3. **The extension, if any**: what changes in §3, what it gives a practitioner, pages and concepts added, and the
   strongest argument against it.
4. **Experiments for afterwards**: at most five, each with what is computed, on what, and the predicted outcome.
5. **Proof notes** (the by-product above).
6. **What you would do next**, in a few sentences.

Finish by replying in the chat with the half-page answer and the path to the file.
