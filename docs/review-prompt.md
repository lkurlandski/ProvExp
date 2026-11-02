# Task: critical review of a body-only draft (feature provenance; ACM CCS format)

You are simulating the program committee of a tier-1 security venue (ACM CCS; reviewers who also serve on IEEE S&P,
USENIX Security, and NDSS). Your job is to find the weaknesses a real reviewer would use to argue for rejection *in the
body as it now stands*, and to say what the still-unwritten sections must do to answer them. Be direct and critical.
Do not soften findings. A problem found now costs a week; a problem a reviewer finds costs a cycle.

## Context

- **The paper.** For feature extractors that find pieces of an input, add up what each piece contributes, and apply a
  formula per feature, the feature-space consequences of an attacker's edits can be *computed* from the instrumented
  extractor: exactly for one edit (side effects, Pierazzi et al.'s $\eta$), soundly for a whole threat model (the
  direction each feature can move). The computed directions yield monotone detectors no in-model edit can evade. Read
  `CLAUDE.md` for the project's framing and constraints, and `docs/paper-mock.md` for the planned thesis,
  contributions, outline with word budgets, and tables.
- **Stage: body only.** Written: Section 3 (the framework, `manuscript/_d_framework.tex`), Section 4 (the EMBER
  instance, `_e_instances.tex`), Section 5 (the evaluation, `_f_evaluation.tex`), and Appendix A (proofs,
  `_j_proofs.tex`). **Empty stubs, by design:** the abstract, introduction, background, related work, discussion, and
  the ethics and open-science appendices. Each stub's comment states its planned content and word budget. Do not flag
  their absence. Instead, say what each must establish for the body to land (Section 2 of your output).
- **Pilot scale.** About 100 files, one seed, a 10% subsample of each split; some checks on 2,000 files. Numbers will
  change at scale, so do not nitpick values. Judge whether each experiment's *design* supports its claim, and whether
  the claim survives plausible shifts (a narrower margin, a smaller count).
- **Blue text is a placeholder for a pending run.** Values set in blue (`\synthetic{...}`, marked `% SYNTHETIC` in the
  source with the run that replaces them) are predictions. Do not flag them as missing evidence or fabrication. Review
  them as claims: would the design support the claim if the run came out as predicted, and what would a different
  outcome do to the paper? List each once, in the risk register.
- **Sources behind the text.** `docs/formalization.md` (the frozen formal model; full proofs and the EMBER caveats),
  `docs/direction-A-summary.md`, `docs/direction-A-A1-design.md`, `docs/item-layer-design.md` (the runs behind every
  number), `docs/status.md` (decisions and results). Local PDFs of the closest work are in `papers/` (`pdftotext`
  works on them): Pierazzi et al., Gimenez et al., Incer et al., Severi et al., Simonetto et al., Dyrmishi et al.,
  Demontis et al., Kantchelian et al.

## Settled: do not re-propose

These were evaluated and decided. Do not list them as mitigations. If you believe one is now *fatal* (would by itself
sink the paper), say so once, in the risk register, with the reason; otherwise leave it out.

- **The domain** is adversarial examples in practical security tasks. The framework is as agnostic as Pierazzi et
  al.'s; PE malware is the main instance. **Which second domain is used for breadth is unimportant and
  interchangeable:** you may say whether the paper needs a second instance and what it must show. Do not argue for a
  particular domain, dataset, or extractor.
- **Scale** (seeds 0-2, full splits, more malware) comes later, on the authors' decision; pilot scale is deliberate.
- **The MLP** is set aside for now; the GBDT is the first classifier.
- **No sandbox execution:** loader-safe edits plus documentation suffice.
- **Edits are written by our own byte-level code**, not LIEF; files they cannot edit are skipped.
- **The population:** files with a plain layout. Files outside it go to an unconstrained detector without a guarantee,
  and coverage is reported. Files over 4 MB stay in. A detector sound over every possible file is one sentence, not a
  row.
- **Dropped:** realizable worst-case evaluation with an exact solver (the former direction A'); the projection onto
  the old provenance matrix; a tightness theorem; a cost theorem (cost is a table column); the coupling row (default:
  out).
- **Writing rules:** continuous prose; limitations light and confident, no Threats to Validity section; no internal
  IDs; the page limit does not matter yet. `docs/formalization.md` is frozen: do not propose editing it.
- **Never raise deadlines or conference cycles.** Quality is the only planning constraint.

`docs/graveyard.md` records abandoned ideas and why.

## Ground rules

1. **Read-only.** Do not modify the manuscript or the docs. Write all output to `REVIEW-<YYYY-MM-DD>.md` in the repo
   root (today's date). Put any drafted text in that file, labeled with the section and the file and line it would
   replace or fill.
2. **Read everything first:** `manuscript/main.tex` and every `\input` (stubs included), `main.bib`, then
   `docs/paper-mock.md`. Build the PDF with `make` in `manuscript/` if you need to see the layout.
3. **Do not read** `REVIEW.md`, `REVIEW-2026-10-21.md`, or `docs/review-reassessment-2026-10-19.md`. They review the
   abandoned direction (explanation provenance) and would only mislead you.
4. Cite locations precisely (section, and file + line) for every finding.
5. Separate what you *verified* (checked against the source docs, a paper, or the code) from what you *infer*. If unsure
   whether something is a problem, say what would resolve it.
6. **Report only what would change a reviewer's verdict.** For every finding, say which reviewer would raise it and
   which score it moves. Sentence-level rewording and polish are out of scope; the authors find them pedantic.
7. **Be harsh about novelty, and fair.** The formalization (items, sums, readouts; exact side effects; sound directions)
   is meant as a contribution in its own right; one strong application suffices. Judge whether it is new and whether
   the paper shows that it is.

## Procedure

### 1. Three simulated PC reviews

Write three independent reviews, each by a reviewer with a different background. Write each as if you had not seen the
others.

- **Reviewer A, formal methods and programming languages:** knows abstract interpretation (sign and interval domains),
  incremental computation and view maintenance, incremental parsing, data and dependency provenance. Asks whether the
  model and its theorems are new, correct, and stated at the right generality, or a known technique renamed.
- **Reviewer B, adversarial ML for malware detection:** knows Pierazzi et al., EMBER, the secml-malware and GAMMA
  attacks, MAB-Malware, monotone and certified detectors (Incer et al., Gimenez et al., Chen et al.), constrained
  feature-space attacks. Asks whether the baselines are what a practitioner would use, whether the attacks are strong
  enough, and whether the detectors are realistic.
- **Reviewer C, generalist systems security:** asks what security task the paper enables that was not possible before,
  whether the threat model is sensible, and whether one instance supports a general claim.

Each review: a summary **in the reviewer's own words** (if it is hard to write, that is itself a top finding);
strengths (specific); weaknesses ranked by severity; questions for the authors; a score on CCS's scale (Reject / Weak
reject / Weak accept / Accept) with confidence, *assuming the empty sections are later written competently*; and **the
one change that would move the score up one level**.

Then a short **meta-review**: agreement, disagreement, likely outcome.

### 2. What the body shows, and what the empty sections must do

First, list the claims the body supports: each claim, its evidence (section, theorem, table), and its strength (strong
/ moderate / thin at pilot scale). Compare with the mock's thesis and four contributions:

| Claim (mock) | Where the body supports it | Strength | Verdict |

Verdicts: Supported / Overclaimed / Scope mismatch / No evidence yet / Undersold.

Then, for each empty section (introduction, background, related work, discussion, abstract), state in a few bullets
what it must establish, which reviewer concern it answers, and what it must not promise. Quote or draft the single
**key-insight sentence** the introduction should be built around.

### 3. The framework: correctness and presentation

- Are the definitions, requirements (R1)-(R5), Theorems 1-2, and Corollary 1 stated correctly and consistently with
  the appendix proofs? Check the proofs in Appendix A against `docs/formalization.md`. Flag any gap a careful reader
  would find (a quantifier, an unstated assumption, a case the proof skips).
- Is every symbol defined before use? Is the running example carried consistently?
- Do the three tables (cross-domain, terms, readouts) earn their space?
- Word budget: report each section's length against `docs/paper-mock.md` (use `texcount`, in
  `~/texlive/2026/bin/x86_64-linux`), and say where the text sprawls or is too thin to be understood.

### 4. Methodology and evaluation

Report pass / weak / missing, with specifics, only where it matters to the verdict. Probe at least these:
- **Circularity.** The hand-written direction table that Table 6 compares against was written by the authors. Is it a
  credible stand-in for what a practitioner would do, or a strawman? The adaptive attack predicts with the same engine
  the defense is derived from, and the monotone rows' 0.0 is a consequence of the theorem. Is the detector
  evaluation tautological, and what would make it convincing (independent attacks, a held-out toolkit)?
- **Baselines.** PV selection, the expert set, adversarial training (synthetic), learned constraints: realistic and
  strong enough? Anything missing that a reviewer would expect?
- **Validation versus proof.** The requirements are checked on an instance, not proved. Is the evidence (single-byte
  flips, random writes, re-extraction of every operation) enough for the claims made?
- **Coverage.** 76% of pilot malware lie in the population; files outside get no guarantee. Does this weaken the
  detector claim, and how should it be presented?
- **Generality.** One built instance supports a framework claimed for a class of extractors. Is the cross-domain
  table enough, or does the paper need a second instance, and what must that instance show (not which domain)?
- Research questions explicit and answered; ablations (which component does the work: the derivation, the sums
  re-encoding, the monotone training); statistics and N; every table with a takeaway in the text; reproducibility.

### 5. Novelty and positioning

- Search the web (ACM DL, USENIX, IEEE, NDSS, arXiv, PL and database venues; especially the last ~3 years) for work a
  reviewer would raise: computing feature-space constraints from extractors, incremental or differential feature
  extraction, abstract interpretation of feature pipelines, verified feature extraction, problem-space attack
  frameworks, monotone and certified malware detectors.
- For the closest work, state the precise difference and whether the body makes it clear. Give particular attention
  to Pierazzi et al., Gimenez et al., Incer et al., Chen et al. (CCS 2021), and the constrained-feature-space line
  (Simonetto et al., Dyrmishi et al., Chernikova and Oprea).
- List what the related-work section (Section 6, about 700 words) must cover, and how to characterize each closest
  paper fairly (reviewers are often their authors).

### 6. Rejection-risk register and mitigation plan (most important)

Every concrete reason a PC member could use to argue for rejection, ranked by likelihood x severity:

| # | Risk | Likelihood (H/M/L) | Severity (fatal/major/minor) | Mitigation | Type | Effort |

- **Mitigation:** specific ("add X against Y and report Z"), within "Settled" above.
- **Type:** Writing fix / Reframing / Analysis of existing data / New experiment / Scope reduction.
- **Effort:** hours / days / weeks.
- Where a full fix is not feasible, propose the best partial one, and say honestly when only new work fixes it.
- Where the same results could be framed differently to sidestep a weakness, describe the framing, its gain and its
  cost. Do not change what a claim is for without flagging it as a proposal for the authors to decide.

### 7. Prioritized action plan

What to do first, second, and not at all: experiments (with the run each needs), writing of the empty sections, and
changes to the written ones. Order by how much each moves the verdict.

### 8. Drafts

Draft actual text, grounded in Section 2: (1) the contributions list; (2) the key-insight sentence and a one-paragraph
plan of the introduction's argument; (3) the single highest-impact passage the review identified in the written
sections, as replacement text.

## Output requirements

- Everything goes in `REVIEW-<YYYY-MM-DD>.md`, with the sections above as headers.
- Start the file with a 5-line executive summary: the three scores and the likely outcome, the top three risks, and
  the single most important thing to fix.
- When done, tell me in the chat where the file is and give me the executive summary.
