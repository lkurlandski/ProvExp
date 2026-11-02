# Resume: ProvExp (after 2026-11-02 stock-take): formalize the framework

The stock-take is done (`docs/status.md`, top block) and the user decided (`PLAN.md`, "Next steps (2026-11-02,
stock-take done)"): **formalize the framework next, in the PE malware domain**, working through every theorem we judge
important, not only those direction A rests on today (pruning or an appendix is a later writing decision). A second
domain (e.g., flow statistics) comes later, as breadth. One application with enough depth is a solid paper; a second
is a goal, not a requirement. The user judges the formalization a significant contribution in itself: keep judging
novelty harshly, but position it fairly against prior work rather than dismissing it.

## Read first

`CLAUDE.md`; `docs/status.md`'s top block; `PLAN.md` (Thesis, The model, Next steps 2026-11-02);
`docs/feature-provenance-model.md` in full (it is the starting point: three layers, edits, C1-C4 with proof sketches,
A1-A4, coverage); `docs/item-layer-design.md` (the contribution vocabulary, the ten readout types, the checks G1-G7,
which become the instance's discharge of the obligations); `docs/literature-2026-10-22.md` (Pierazzi et al.'s
problem-space formalization, Cheney et al.'s dependency provenance, Incer, Gimenez, Chen et al., Treant).

## The work

Plan first, with the user, then write. Deliverable: a new document, `docs/formalization.md` (definitions, theorems,
full proofs), later the source for the paper's framework section and appendix. Proposed outline, to agree on:
1. **Definitions.** Elements and inputs; items with membership and location; the contribution vocabulary (count, add,
   bins, hashed signed/unsigned, keyed, slot, opaque); sums (additive and max/min pools); readouts (the ten types);
   the class of sum-then-readout extractors. Edits as item deltas (add, remove, modify, move); content, item-creating,
   declared and undeclared structural edits; a threat model as a catalogue of operations with parameter domains.
2. **Obligations.** A1-A4 stated as properties of an extractor per item kind, and what a check must show to discharge
   each on an instance (G1-G7 on EMBER), including what checks on natural files cannot catch (adversarial parameters).
3. **Theorems.** C1 exact side effects (additive and max/min pools); C2 co-movement and inseparability (the cone
   criterion; the shared-denominator case); C3 soundness of the reachable region (cone, readout intervals, the mediant
   bound, the histogram polytope, the entropy interval, boundary effects between added chunks); C4 per-file direction
   tests (sign, ratio, cross-entropy), the global union, and soundness of the derived table; the composition: derived
   directions plus a monotone classifier give robustness under the threat model (with Gimenez et al.'s Proposition 1);
   the flat P as a projection of the model. Consider also: when C4 is tight (every declared direction is realized by
   some edit), and what undeclared or flagged edits cost (soundness by "both").
4. **For each theorem:** the checkable prediction it makes and the run or check that tests it on EMBER (G1-G7, runs
   79, 92-93, 103-104, 111), or a cheap new check if none exists (state the hypothesis first; jobs over ~10 minutes go
   to a `run/` script, next number 117).
5. **Positioning:** what the formalization says beyond Pierazzi et al. (side effects estimated empirically, the
   extractor a black box), incremental view maintenance and incremental computation, abstract interpretation (sign and
   interval domains), and taint / dependency tracking. State what is new plainly and fairly.

## Standing rules

Explain plainly; never use doc-internal labels (C3, M_full, G2) without saying what they are; answer methodology
questions by reasoning, not by running data first; do not edit the manuscript; commit in logical pieces after ruff and
mypy pass (if code changes).

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
- The user's comments on the stock-take ended at an empty item 5; ask whether anything was meant there.
