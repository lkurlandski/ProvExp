# Fable session: strengthening the theory

Written 2026-11-14 (after session 64) for a single session on Claude Fable 5.2, whose credits are limited (until
2026-11-17). The session audits the framework's proofs and then looks for ways to make the theory stronger. Its only
output is one findings file. It does not edit the manuscript or the code.

**How to launch it (the user):** start a fresh session in the repository, switch the model with `/model` to Fable 5.2 at
**high** effort (not xhigh or max), and send: *"Read `docs/fable-theory-prompt.md` and carry out the prompt in it."*
If the credits run out partway, switch back to Opus with `/model` in the same session: everything already written to
the findings file and committed is safe, and Opus can finish the current phase from the file.

---

## The prompt

You are working on a dissertation project, ProvExp, with a PhD student whose expertise is adversarial machine learning
for malware detection. This session has one job: **find out how the paper's theory can be made stronger, and check
that it is correct as it stands.** You are here because this is the hardest judgement in the project, and the earlier
work on it was done by the same model that wrote the theory, which is a poor position for criticizing it. Think
deeply. Be harsh about weaknesses and fair about strengths: the goal is a stronger paper, not a longer list of
problems.

Your session is expensive and limited. Read what is listed below and nothing else unless a specific question needs
it. Write your findings to the output file as you go (section 6) so that nothing is lost if the session stops.

### 1. The project in brief

Security classifiers (malware detectors and others) do not see raw inputs; they see feature vectors computed by a
feature extractor. An attacker edits the input (adds a section to an executable, appends bytes, renames things), and
the question is what that edit does to the features. The literature calls the gap between input-space edits and
feature-space changes the *problem-feature space gap* (Pierazzi et al., S&P 2020): one edit can move many features at
once (side effects), and so attacks and defenses usually find the consequences by trial (apply the edit, extract
again), by an analyst reading the extractor, or by learning from observed attacks.

The paper's claim: for a large class of extractors, the ones that *find the pieces of the input (items), add up what
each piece contributes to running totals (sums), and compute each feature by a formula over a few totals (readouts)*,
the consequences can be **computed** from an instrumented extractor:

- **Proposition 1 (Exact side effects):** from an edit's *delta* (the items it removes and adds) and a record of the
  input's items, every feature of the edited input is computed exactly, before the edit is applied.
- **Theorem 1 (Sound directions):** for a whole threat model (a set of allowed edits) and a population of inputs
  closed under it, a table derived from the *signature* (the kinds of item changes the edits can make) says, for each
  feature, whether any sequence of edits can raise it, lower it, or neither. Sound, possibly loose.
- **Corollary 1 (Robustness):** a detector whose score cannot fall in the table's directions (e.g., a GBDT with
  monotone constraints that ignores two-sided features) cannot be evaded by the threat model on the population.

PE malware with the EMBER2024 feature set (thrember, built on pefile) is the instance (§4); the evaluation (§5) has
three findings: hand analysis of side effects misses some (5.2), defenses learned from observed attacks miss edits they
never saw (5.3), and robustness costs a measured amount of clean detection (5.4). Format: ACM CCS. The body is drafted
on pilot-scale results; a large scale-up will replace every number. **The theory (§3 and Appendices B-C) is the part
this session is about.**

### 2. What to read, in this order

Read fully:

1. `manuscript/_c_background.tex` (§2: the motivation and what the theory promises; ~1,000 words).
2. `manuscript/_d_framework.tex` (§3: definitions 1-10, Proposition 1, Theorem 1, Corollary 1; ~4,400 words).
   LaTeX `%` comments carry history; skim them.
3. `manuscript/_i2_types.tex` (Appendix B, types, monoids, folds) and `manuscript/_j_proofs.tex` (Appendix C, the
   proofs and the sign table).
4. `manuscript/_e_instances.tex` (§4: how EMBER instantiates the framework; read for how the theory is *used*: the
   signature of operations stated as writes comes from a record of the positions the parser reads to locate items, and
   is checked on a corpus rather than proven).
5. `manuscript/_g_related_work.tex` (§6) and `docs/evidence/r6-prior-work.md` (the prior work the framework builds on,
   read in full in an earlier session: incremental view maintenance, self-maintainability, abstract interpretation,
   Gimenez et al.'s monotone detectors, Pierazzi et al.).

Read the parts named:

6. `docs/reviews/2026-11-12-body/meta-review.md`: the risk register table (search for `| R# |`) and the four reviewer
   summaries (`### Reviewer A` ... `### Reviewer D`). Reviewer A (formal methods) is the one who matters most here.
   These reviews were simulated by an LLM; the user judged many of their comments misguided. Treat them as hints, not
   as evidence.
7. `PLAN.md`: "Thesis", the decisions of 2026-11-09 numbered 2, 3 and 7, and "Settled decisions".
8. `docs/paper-mock.md`: the contributions list and "Dropped from the paper".

Open only when a specific question needs it: `manuscript/_f_evaluation.tex` (§5, the findings; read 5.3 and 5.4 only if
an idea depends on them), `manuscript/_j2_ember.tex` (Appendix D), the PDFs in `papers/` (the cited works; the
relevant ones for theory are `gimenez2025certifiably`, `pierazzi2020intriguing`, `cousot1977abstract`,
`gupta1993maintaining`, `mumick1997maintenance`, `koch2014dbtoaster`, `incer2018adversarially`, `chen2021learning`,
`calzavara2020certifying`, `kantchelian2016evasion`, `simonetto2022unified`), and
`docs/archive/framework/formalization.md` (the frozen earlier formalization, where the dropped results below live).

**Out of scope; do not open:** `src/provexp/attacks/`, `src/provexp/featuresets/ember2024/escapes.py`, the MAB-Malware
code, `run/`, `pipeline/`, the R7 and R18 evidence records, and the archived reviews. The session is about the
mathematics, not the attack implementation. You do not need to run any code.

### 3. What the user has already decided about the theory

These are settled. Do not propose reversing one unless you have a strong, specific reason; if you do, put it in its
own section (section 6, part E), argued, and keep it out of the ranked list.

- **The formalization is a contribution.** The user judged an earlier critique ("incremental view maintenance plus
  sign analysis; three-line proofs") too harsh. Harsh is still preferred over lax, but position the theory fairly.
- **Credit without diminishing.** Never write a borrowed-versus-new ledger ("Proposition 1 is IVM's delta rule,
  Theorem 1 is abstract interpretation"); the user rejected that framing because it concedes the paper's novelty. The
  novelty is the combination: carrying these ideas to feature extractors and to a universal question over a threat
  model and a population. Cite foundations as foundations.
- **Elegant fixes only, and only for gaps a real reader would care about.** Loophole-style findings ("any mapping fits
  the class with one whole-input item") are not problems. The user rejected adding a universality or locality clause
  to fix that one: items are hierarchical (an object made of items is itself an item), so the framework staying
  well-defined at its limits is a strength. **The user is open to a deeper look at how item size and locality matter**,
  as an idea that strengthens the theory, not as a fix. For a real gap, the user prefers a small patch that reuses a
  mechanism the framework already has over a new hypothesis or clause.
- **Proofs carry the weight.** A proven result needs only a small confirming check. No new machinery or pages for
  assumptions that are checked empirically. In particular, the signatures of operations stated as writes and the
  population's closure are *checked* on a corpus, not proven, and the user accepted that (PLAN.md decision 2). A
  proposal to prove them instead must be light and clearly worth its pages.
- **No timing claims.** The paper never says the computation of Proposition 1 is faster than re-extraction, only that
  it touches only the items an edit meets and so can be faster. Do not propose timing results. A statement about the
  *amount of work* is allowed only if it is honest about what it measures.
- **The framework is format-free** (as agnostic as Pierazzi et al.'s): no PE specifics in §3. PE details belong in §4
  and the appendix. The domain is adversarial examples in practical security tasks; do not re-open that.
- **Dropped earlier** (paper mock, "Dropped from the paper"): requirements R1-R5, footprints, margins, the old Theorems
  2-3, coupling between features, the region's tightness, a cost theorem. They were dropped for complexity and
  focus, not because they were wrong. Bringing one back is allowed if you can argue it now earns its place; say so
  explicitly.
- No engagement with database-theory provenance (semirings, aggregate provenance) beyond citation.
- No packing as motivation or case study. No sandbox execution of modified files.

### 4. Phase 1: audit the proofs

Check Proposition 1, Theorem 1 and Corollary 1, and every lemma, side condition and table they use (the sign table in
Appendix C, the readout rules in §3.3's table, the ratio's side condition in Definition 10, the total-order hypothesis,
the treatment of pools (max/min sums), neutral elements, sequences of edits and closure). For each, decide:

- **Correct as stated.** Say so in one line.
- **Wrong:** a counterexample or a step that does not follow. Give the smallest concrete counterexample you can.
- **A real gap:** correct in spirit, but the statement or the proof needs a change a careful reader (a formal-methods
  reviewer at CCS) would ask for. Propose the smallest fix, as concrete old and new text.
- **Pedantic:** a crack no real reader would notice or care about. List these in one line each at the end, or drop
  them.

Reviewer A and the register (R17) claimed that Theorem 1 is stated beyond its proof; check whether that is still true
of the current text, since parts were patched since. Write Phase 1 to the output file and commit before starting
Phase 2.

### 5. Phase 2 and 3: map the theory, then find how to strengthen it

**Phase 2 (short).** In plain language: what the three results say together, what they let someone do that they
could not before, the strongest honest statement of what is new, and where the theory is thinner than the paper's
claims or than a strong formal paper would be. Half a page.

**Phase 3 (the core).** Generate ideas that would make the theory stronger, then select. "Stronger" means one of: a
result that says more (a converse, a characterization, an optimality or completeness statement, a tighter table), a
result that covers more (a larger class of extractors, weaker hypotheses), a result that gives an existing finding of
§5 a theoretical footing, or a cleaner formulation that makes the existing results easier to appreciate. Questions to
start from (not a limit; your own ideas are what this session is for):

- **Converses and optimality.** Corollary 1 says monotone detectors with respect to a sound table are robust. Is there
  a converse: is every detector that the threat model provably cannot evade on the population, in some sense, monotone
  with respect to the table, or with respect to the *exact* table? If so, the monotone detector is not *a* robust
  detector but *the* class of robust detectors, and the accuracy cost measured in 5.4 is a cost of robustness itself,
  not of our construction. Under what conditions (reachability of each direction, independence of changes) does this
  hold, and what breaks it?
- **Exactness of the table.** Theorem 1 is sound but may be loose. When is the derived table exact (every marked
  direction realized by some edit on some input)? A completeness condition, or a characterization of the looseness,
  would answer "how much robustness do you give away?". (The region's tightness was dropped earlier; argue if it
  comes back.)
- **Learned versus derived constraints.** §5.3's finding is that defenses learned from observed attacks miss edits
  they never saw. Is there a short, general statement behind it: constraints learned from a sample of edits are sound
  only for what the sample spans, and the derived table is the least table sound for the whole threat model (or is it
  not)? A proposition that makes 5.3 a consequence rather than an observation would be valuable.
- **Closure and populations.** Theorem 1 needs a population closed under the threat model; in practice inputs outside
  it exist and a single write outside the threat model can move an input out. What can be said without closure, or
  over the closure of a population? Is there a natural largest population for which the table is sound?
- **Item size and locality** (the user's open interest). Items are hierarchical; the framework applies at every
  granularity, but its results are informative when items are local. Is there a precise statement of the trade-off:
  coarser items make signatures simpler to state but tables looser, finer items the reverse? A monotonicity result
  across refinements of the item map would be a natural, format-free theorem.
- **The class itself.** Which extractors are sum-then-readout, and what falls outside (order-dependent features,
  sliding-window entropy, learned embeddings)? Is there a characterization (e.g., extractors that factor through a
  commutative monoid of items), or a clean extension that covers more feature sets without new machinery? Note the
  hierarchical view of items.
- **Proposition 1's own role.** Reviewers asked what Proposition 1 enables beyond Theorem 1 (register R9). Is there a
  statement that makes it carry more weight, e.g., its relation to Pierazzi et al.'s side-effect feature vector, which
  they estimate in advance by injecting a gadget into a minimal app (Proposition 1 as its exact, per-input version), or
  a result about attacks or adversarial training that needs exactness? Respect the no-timing rule.
- **The sign-domain abstraction.** Directions are a sign abstraction of the change. Is a richer abstract domain
  (intervals of change, bounds on magnitude) natural here, and would it buy something a reader values (e.g., the
  magnitude of side effects, or robustness of non-monotone detectors within a margin)? Weigh it against the user's
  dislike of machinery.

For every idea, before you shortlist it, write down: the statement in plain words, then in the paper's notation; what
it would change in the paper and which reviewer concern (R-number) it answers, if any; whether you believe it is true
and how confident you are; a proof sketch or the obstacle to one; its cost in pages and in added concepts; and **the
strongest argument against doing it**. Discard ideas that fail the user's taste in section 3 unless the payoff is
large.

Then **rank at most six** ideas by value to the paper divided by cost and risk. Put the rest in a short list of one
line each.

**Phase 4 (if the session has room).** For the top one or two ideas, attempt a full proof (or a counterexample that
kills the idea), in the paper's notation, ready to be judged. A clean failure is a useful result; report it as one.

### 6. Output

Write everything to **`docs/evidence/fable-theory-analysis.md`**, created at the start of Phase 1, with these parts:

- **A. Proof audit** (Phase 1): per result, the verdict and, for wrong or gap items, the counterexample and the
  concrete old/new text. Pedantic items in one line each at the end.
- **B. The theory in brief** (Phase 2).
- **C. Ranked ideas** (Phase 3): at most six, each with the fields above; then the short list.
- **D. Proofs** (Phase 4).
- **E. Settled decisions you would revisit** (optional, argued, separate).
- **F. What I would do next**, in three to five sentences.

Rules for the output:

- **Plain language first.** The user could not follow jargon-heavy explanations in the past. Lead every item with
  what it means and why it matters, then the mathematics. Define any term the paper does not.
- **Save as you go.** After each phase, write that part to the file and commit it
  (`git add docs/evidence/fable-theory-analysis.md && git commit -m "Docs: Fable theory analysis, <phase>"`, ending
  the message with the `Co-Authored-By` line your system instructions give). Do not hold findings in your head until
  the end. If you sense the session is running long, finish and commit the current part rather than starting the
  next.
- Cite the paper by its compiled numbers (Proposition 1, Theorem 1, Corollary 1, Definitions 1-10, Table 1 the readout
  rules, Table 7 the sign table; `docs/README.md` lists them) and give file and line references for the `.tex`.
- Portray cited work accurately, in its authors' own terms; check against the PDF in `papers/` before relying on a
  claim about it.
- **Do not edit the manuscript, the code, PLAN.md or status.md.** Do not run experiments. Do not push. Do not spawn
  subagents; if a search over `papers/` is unavoidable, do it yourself with grep or `pdftotext`.
- State uncertainty plainly. "I believe this is true but could not prove it" is a useful finding; a confident claim
  that turns out false is costly.

At the end, reply in the chat with a short summary: the proof audit's verdict in one or two sentences, the top three
ideas in one sentence each, and the path to the file.
