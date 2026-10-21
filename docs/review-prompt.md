# Task: Critical pre-submission review of my ACM CCS manuscript

You are simulating the program committee of ACM CCS: reviewers who also serve on IEEE S&P, USENIX Security, and NDSS.
Your job is to find the weaknesses a real reviewer would use to argue for rejection, then help me fix them. Be direct
and critical. Do not soften findings. A problem you find now costs me a week. A problem a reviewer finds costs me a
cycle.

## Context

- **Paper:** explanation provenance for malware detectors: a method (the provenance matrix P, the pullback and the
  pushforward) and two security applications. Read `CLAUDE.md` for the project's framing and constraints.
- **Venue and time:** ACM CCS 2027, Cycle A (deadline est. mid-January 2027; the CfP is not out yet). About 12 weeks
  remain from late October 2026.
- **Stage:** the body (Sections 2-6, appendices) is filled with pilot-scale results (about 100 files, one seed; some
  experiments 500 or 2,000 files). The numbers will change when experiments are scaled up, so do not nitpick values.
  Judge instead whether each experiment's *design* can support its claim, and whether the claim would survive
  plausible shifts in the numbers (a narrower margin, a weaker correlation).
- **Blue text is a placeholder for a pending run.** Values and sentences set in blue (`\synthetic{...}` in the LaTeX,
  marked `% SYNTHETIC` in the source) are predicted results of experiments that are designed and scripted but not yet
  run; the prose around them is written as if the run had finished. Do not flag them as missing evidence, fabrication,
  or inconsistency. Review them as claims: would the design support the claim if the run came out as predicted, and
  what would a different outcome do to the paper? List each one once, in the risk register, with what hinges on it.
- **Front matter is written last.** The abstract, introduction, and conclusion are provisional; one purpose of this
  review is to shape their rewrite. Treat the body as the source of truth and the front matter as a draft to be checked
  against it.

## Settled: do not re-propose

These were evaluated and decided. Do not list them as mitigations. If you believe one is now *fatal* (would by itself
sink the paper), say so once, in the risk register, with the reason; otherwise leave it out.

- Deferred: retraining MalConv (and a stronger attacker against it), the scale-up to 2,000 files, more seeds, the MLP.
- Dropped: a named-feature TreeSHAP baseline for 6.1's prediction table (it presumes a hand-built field-to-feature
  map, which is not a realistic alternative), a 0.1% FPR column, executing modified samples in a sandbox (loader-safe
  modifications plus documentation suffice).
- Constraints on any mitigation (see `CLAUDE.md`, "Framework conventions", and `docs/graveyard.md`): the framework
  stays domain-agnostic; the pushforward and its application stay (the symmetry of the two transfers is the novelty);
  no analyses stratified by PE structure without a concrete reason; coverage and the null element's share are a
  stated limitation, not a contribution; baselines must be what a practitioner would realistically do, not a
  hand-built per-file PE mapping.
- The page limit does not matter yet.

`docs/status.md` records the current results and decisions if you need to check whether something is settled.

## Ground rules

1. **Do not modify the manuscript files.** This is a read-only review. Write all output to `REVIEW-<YYYY-MM-DD>.md` in
   the repo root (today's date). If you draft replacement text, put it in that file, labeled with the section and the
   file and line it would replace.
2. Read the whole paper before writing anything: `manuscript/main.tex` and every `\input`, including appendices,
   figure files under `manuscript/assets/`, captions, tables, footnotes, and `main.bib`.
3. Cite locations precisely (section number, and file + line number) for every finding.
4. Separate what you *verified* from what you are *inferring*. If you are unsure whether something is a problem, say
   so and say what would resolve it.
5. **Report only what would change a reviewer's verdict.** For every finding, say which reviewer would raise it and
   which score it moves. Sentence-level rewording, style preferences, and minor polish are out of scope; I find them
   pedantic.
6. Check the most recent ACM CCS Call for Papers on the web (the 2026 CfP, until the 2027 one appears; say which you
   used) for template, anonymization, ethics, and artifact/open-science requirements. Do not rely on remembered
   numbers.

## Procedure

### Pass 1: blind review

Do **not** read `REVIEW.md` or `docs/review-reassessment-2026-10-19.md` until Pass 1 is written; they would anchor you.

### 1. Three simulated PC reviews

Write three independent reviews, each by a reviewer with a different background, as CCS would assign them. Write each
as if you had not seen the others.

- **Reviewer A, explainable AI:** knows SHAP, DeepSHAP and G-DeepSHAP, attribution transfer across representations,
  faithfulness metrics (deletion/insertion curves). Asks whether the method is new and whether the evaluation of
  faithfulness is sound.
- **Reviewer B, ML for malware detection:** knows EMBER, MalConv, problem-space attacks, explanation-guided attacks
  and backdoors. Asks whether the baselines and the detectors are realistic and whether the applications reflect what
  practitioners do.
- **Reviewer C, generalist systems security:** asks what security task the paper enables that was not possible before,
  and whether the applications' threat models make sense.

Each review: a summary **in the reviewer's own words** (if it is hard to write, that is itself a top finding);
strengths (specific); weaknesses ranked by severity; questions for the authors; a score on CCS's scale (Reject / Weak
reject / Weak accept / Accept) with confidence; and **the one change that would move the score up one level**.

Then a short **meta-review**: where the reviewers agree, where they disagree, and the likely outcome of the discussion.

### 2. What the body shows, and the front matter against it

First list the claims the body actually supports (Sections 3-6 and appendices): each claim, its evidence
(section/figure/table), and its strength (strong / moderate / thin at pilot scale). Then check the current title,
abstract, introduction (especially the contributions list), and conclusion against that list:

| Claim | Where stated | Supporting evidence | Verdict |

Verdicts: Supported / Overclaimed / Scope mismatch / No evidence / Undersold. Flag contribution bullets that describe
an activity ("we implement...") rather than a claim, and note body results the front matter omits.

### 3. Threat models (brief)

This is a method paper with two applications, not an attack or defense paper. Check only: is each application's short
threat model adequate and consistent with what the experiment assumes; does any capability look reverse-engineered to
fit the result; and does the audit's mitigation (6.2) need an adaptive attacker to be credible? Keep this section
short.

### 4. Methodology and evaluation

Report pass / weak / missing, with specifics, only where it matters to the verdict:
- Research questions: explicit, falsifiable, each answered?
- Baselines: the closest prior work and the realistic practitioner alternative? Omissions explained?
- Realism and external validity: detectors, data, operators.
- Scale and sampling: do they support the generalization claimed (one feature extractor, one dataset)?
- Statistics: N stated, paired tests, CIs or effect sizes where claims rest on them.
- Ablations: is it clear which component does the work?
- Negative results and failure cases reported where a reviewer would expect them?
- Reproducibility and artifact plan.
- Does every figure and table have a takeaway in the text?

### 5. Novelty and positioning

- Read `docs/related_work.md` first. Then search the web (ACM DL, USENIX, IEEE, NDSS, arXiv; the last ~3 years) for
  work a reviewer would raise. Report only work that `docs/related_work.md` and the paper do not already cover, or
  cover inaccurately.
- For the closest prior work (cited or not), state the precise difference from this paper and whether the manuscript
  makes it clear. Give G-DeepSHAP and other attribution-transfer methods particular attention.
- Does related work characterize prior papers fairly? Reviewers are often their authors.
- Is there a single clearly stated "key insight" sentence? Quote it, or say it is missing.

### 6. Ethics and compliance (brief)

Malware handling, anonymization (self-citations, names, links, tool names, PDF metadata), required statements per the
CfP (e.g., ethics considerations, open science). Skip what does not apply.

### Pass 2: compare with the previous review

Now read `REVIEW.md` (2026-10-16) and `docs/review-reassessment-2026-10-19.md`. For each risk there, say whether it is
still closed, reopened, or changed; mark each risk in the register below as **new**, **reopened**, or **carried**.

### 7. Rejection-risk register and mitigation plan (most important section)

Every concrete reason a PC member could use to argue for rejection, ranked by likelihood x severity:

| # | Risk | Status (new/reopened/carried) | Likelihood (H/M/L) | Severity (fatal/major/minor) | Mitigation | Type | Effort | Feasible by deadline? |

- **Mitigation**: specific ("add X against Y and report Z"), and within the constraints of "Settled" above.
- **Type**: Writing fix / Reframing / Analysis of existing data / New experiment / Scope reduction.
- **Effort**: hours / days / weeks.
- Where a full fix is not feasible, propose the best partial one (narrowing a claim, a limitations sentence,
  reframing), and say honestly when a weakness can only be fixed with new work.
- Where the same results could be framed differently to sidestep a weakness, describe the framing and what it gains
  and costs. Do not change what a claim is for without flagging it as a proposal for me to decide.

### 8. Prioritized action plan

Given about 12 weeks: what to fix first, what to fix if time allows, and what not to attempt this cycle.

### 9. Draft rewrites for the front matter

Draft replacement text, grounded in Section 2's list of what the body shows: (1) the abstract, (2) the contributions
list, and (3) the single highest-impact passage elsewhere that the review identified. Actual text I can edit, not a
description.

## Output requirements

- Everything goes in `REVIEW-<YYYY-MM-DD>.md`, with the sections above as headers.
- Start the file with a 5-line executive summary: the three scores and the likely outcome, the top 3 risks, and the
  single most important thing to fix.
- When done, tell me in the chat where the file is and give me the executive summary.
