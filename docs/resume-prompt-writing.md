# Resume prompt (writing track): manuscript organization and the review plan

Written 2026-11-24 (end of session 112; replaces session 111's prompt, archived as
`docs/archive/resume-prompt-writing-2026-11-24-s111.md`). Self-contained: read `CLAUDE.md` (loaded automatically) and
this prompt. Run on Opus. Use no subagents unless the user asks.

## 1. The project in brief

ProvExp is the user's dissertation research. Its subject is *sum-then-readout* feature extractors, the kind security
classifiers use: they find the pieces of the input (items), add up what each contributes (sums), and compute each
feature by a formula over a few totals (readouts). From the instrumented extractor the paper computes what an
attacker's edits do to the features: exactly for one edit (Proposition 1), as sound directions for a whole threat
model (Theorem 1, the *derived table*: for each feature, whether edits can raise it, lower it, both, or neither), and
from those, monotone detectors no edit in the threat model can evade (Corollary 1). PE malware with EMBER 2024 is the
instance. The paper is `manuscript/*.tex` (ACM CCS format; `make` and `make check` in `manuscript/`). Every number is a
pilot value until the scale-up's rerun (on tigris) is read in the experiments track
(`docs/resume-prompt-experiments.md`). Blue `\synthetic{}` values are predictions.

The compiled outline (from `main.aux`; words by `texcount`, 2026-11-24): 1 Introduction (empty); 2 Background and
Motivation (960); 3 Measuring Edits Across Feature Mappings (3,076: 3.1 Sum-then-Readout Extractors, 3.2 Edits and
Their Side Effects, 3.3 Sound Directions); 4 Instantiating the Framework (1,714: 4.1 Extractor, 4.2 Threat Model, 4.3
Signature, 4.4 Population); 5 Evaluation (4,406: 5.1 Setup, 5.2 What Hand Analysis Misses, 5.3 What Observed Edits
Miss, 5.4 What Robustness Costs); 6 Related Work (1,268); 7 Discussion (empty). Appendices: A Symbol Table, B Types,
Monoids, and Folds, C Proofs for the Framework (C.1-C.3), D The EMBER Instance (D.1 Extractor, D.2 Signature, D.3
Population; no Threat Model part), E Attacks and Defenses (E.1 Setup, E.2 What Observed Edits Miss, E.3 What Robustness
Costs), F Ethics, G Open Science (empty). Table 2 is the threat model's operations (the old prompt called it Table 3;
the PDF is the authority).

## 2. Why this session: the read of §4.2 stalled on roles, not prose

Session 112 began the user's read of §4.2 *Threat Model* and rewrote it four times. Each draft fixed one complaint and
exposed another (a literature survey instead of our threat model; "What the fuck kind of organization is this?" for
twelve edits listed, then a total of fourteen, then the last two; colons as a silver bullet; a "weirdly distant and
passive tone"; "extremely scattered, jumping from idea to idea without much regard for communicating a higher
purpose"; paragraphs on prior work reading like "an unhinged rant"). The fourth draft (commit d004f35, now in the
manuscript) is accepted as an improvement: its first paragraph ties the threat model to §3's guarantees ("the threat
model decides what they are worth"), which the user called the main failure of the earlier drafts. A humanistic review
of it then flagged the missing attacker budget, the 4 MB sentence out of place, and more; the user saw the cause:
**"we cannot decide what its role is in the broader scope of the paper. For example, do details like the attacker's
budget belong here or in section 5?"**

Claude's answer, which the user did not yet accept or reject (decide it in this session's plan):
- The attacker's knowledge and the number of edits are properties of the *framework*, not choices of §4.2: §3 defines
  a threat model as a set of edits whose finite sequences the attacker applies, and the derived table depends only on
  the extractor and the threat model, never on the detector. §4.2 recalls them in a clause at most.
- The budgets of the attacks actually run (queries, donors, access) belong to §5.1.
- The 4 MB limit is a condition on where the guarantee holds, so §4.4 *Population* (or §5.1), not §4.2.
- §4.2's role: supply the one input the framework leaves open, the set of edits: which edits and why that set (the
  edits published attacks use), what we add and why an attacker could already do it (header growth; the entry write,
  with the copied-signature evidence), why three nested threat models (the guarantee's price grows with the threat
  model; §5 builds detectors for more than one), then the boundary (packing, code-level transformations).

Open review findings on the current §4.2 draft (session 112), still valid under any role: the entry write is defined
"instead of only removing it" although the prose no longer says any operation removes entries; its sentence carries
mechanism, consequence, the extractor's flaw, and evidence at once; header growth is in *shifts* although *additions*
adds sections, unexplained; the Incer et al. apposition attaches to the wrong noun; the price of nesting has no number
(§5.4: the entry write is 3.9 of the 7.8 points); why packing is excluded is left implicit; signature drift
(Authenticode signature, code signature, and §4.3's framework *signature*; "certificate entry" against Table 2's
"certificate table entry"); "leave the program's instructions unchanged" is loose (insertions move instructions);
"derive a table for each" though §5 never uses *shifts*.

## 3. This session: task planning and manuscript organization (first order of business)

The user's words: "First order of business needs to be a mixture of task planning and manuscript organization: what
parts of the research should be contained where (re-examine our current structure) and what parts of the manuscript
should I review first? When we identify a pair of subsections whose roles are particularly delicate, e.g., subsection
4.2 and some other subsection from section 5, we should address them both at once, to make sure that the distribution
of content is proper."

Do, in this order:
1. **Read the body** (`_c_background.tex` to `_g_related_work.tex`, the rendered PDF) and the appendices D and E
   enough to know what each subsection holds now. Read `docs/paper-mock.md` for what each section is supposed to do.
2. **Write the content map**: for each section and subsection, its role in one or two plain sentences (the question it
   answers for the reader) and the research content it owns. List every piece of content that sits in more than one
   place, in the wrong place, or nowhere. Candidates already seen (check, do not assume):
   - §3 (threat model defined; knowledge and sequences of edits) and §4.2 (the PE threat model) and §5.1 (the attacks
     run, their budgets, the toolkit attacks named in Table 2's last column).
   - §4.2 (the nested threat models, the entry write) and §5.4 (the price of robustness per operation; the entry write's
     share).
   - §4.3's last sentence and 5.1's *Checking the computation* (the sample-read sentence, false at scale; `% OPEN`).
   - §4.4 (population: "complete", closure checked on 56,902 edits, shares of test files) and 5.1 (the evaluation set,
     files "held in full", the 4 MB scope) and 5.4 (*Where the guarantee holds*, "24 of the 28 malware").
   - The body against its appendix mirror (D has no Threat Model part; memory `appendix-mirrors-body`).
3. **Decide, don't ask lists** (memory `decide-early-design-questions`): for each problem, weigh the options and
   propose where the content goes, with the reason. Ask only about claims, compute, and reversals of the user's earlier
   decisions.
4. **Propose the review order**: pairs (or small groups) of subsections whose roles are delicate are reviewed together,
   so content is distributed once. A likely first pair: §4.2 with §5.1. Order the rest by how much later text depends
   on them.
5. Present the map, the decisions, and the review order to the user plainly (memory `explain-plainly`), and wait for
   their verdict before editing the manuscript. Record what is agreed in `docs/status.md` and, if it changes the paper's
   plan, in `docs/paper-mock.md`.

Then, as the user directs, review the first pair: settle the roles, then the prose. Write each subsection from its role
outward: what it must communicate, the information that serves that, the order; tie it to the framework where the
framework is what gives it meaning; say what *we* do, not what prior work did (cite prior work where it supports a
clause, never as a survey); active voice, "we" and the attacker as subjects. Show the plan before the prose when a
subsection is being rebuilt.

## 4. Lessons of sessions 111-112 (how the user reacts)

- Apply each comment proportionally (memory `feedback-proportionally`): change only what a comment fits, judge each
  instance, keep standard PE names (section table, data directory, debug directory entry, certificate table entry).
  The user wants varied rhetoric and sentence structure, not the absence of a device; a good colon stays.
- A structural complaint needs a structural answer: shuffling paragraphs is not enough, and listing every fact of a
  table in prose reads like a list. Find the subsection's higher purpose first.
- Do not change one section on the strength of another's stale content; the introduction, §2's closing sentence, and
  the discussion wait for the end-to-end pass.
- Prose fixes: diagnosis first, exact old/new text, `make`, `make check`, read the rendered PDF, commit per subsection.

## 5. Open items carried over (raise when the work touches them)

- §5: "24 of the 28 malware" (5.4) against Table 4's 39 and 40 detected (`% OPEN`); the hand-table detector not in the
  scale-up (5.2, `% SCALE-UP GAP`; the user decides); the *shifts* threat model used nowhere in §5 (deferred until a
  *shifts* detector exists); the sample-read sentences (5.1, §4.3) false at scale; blue predictions; mixed pilot models
  in Table 4 (10% subsample against full training set); "the entry write's share" not strictly additive (`% NOTE`);
  terms: §4.4's "complete" against 5.1's "held in full", and "signature" (framework) against code signing.
- Not applied, do not re-propose unless the user raises them: session 109's two ⚑ cuts.
- The rebuttal's number-free fixes R4, R5, R15, R21 (`docs/reviews/2026-11-12-body/rebuttal/triage.md`); Tsingenopoulos
  et al. (`papers/tsingenopoulos2024train.pdf`), the closest work, an experimental comparison is the user's call;
  Giri et al.'s author names in `main.bib`; `PLAN.md`'s "Lemma 1 (*Closure*)" lines are history.
- Not in this round: abstract, introduction, discussion, ethics, open science.

## 6. At the end

After editing: `make` and `make check` in `manuscript/`; `texcount -1` per changed file; check that every table appears
(`pdftotext main.pdf - | grep -o "^Table [0-9]*"`). Add a session entry to `docs/status.md` (top of *Current state*),
log the user's reactions raw in `docs/writing-spec.md` (newest first), commit manuscript and docs in logical pieces.
Archive this prompt under `docs/archive/` (list it in `docs/README.md`), then write the next resume prompt into this
file, self-contained.
