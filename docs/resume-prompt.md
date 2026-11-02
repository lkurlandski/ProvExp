# Resume: ProvExp (after 2026-11-02): write the formalization

## Where we are

On 2026-11-02 the exact-solver direction (A') was dropped, and the stock-take of everything done since the
2026-10-22 restart is finished (`docs/status.md`, top block). The user decided:

- **Framing:** one strong paper. It is direction A (sound detectors whose feature directions come from the
  instrumented extractor), with the model as its framing section, not "several applications under one framework".
  A second application is a goal, not a requirement.
- **Next: formalize the framework**, in the PE malware domain. Work through every theorem we judge important, not
  only those A rests on today. Pruning, or moving some to an appendix, is a later writing decision.
- **The formalization is a significant contribution in its own right** (user). Keep judging novelty harshly, but
  position it fairly against prior work rather than dismissing it as "incremental view maintenance plus sign
  analysis".
- **A second domain comes later, as breadth** (e.g., a flow-statistics extractor for network traffic). Establish the
  method on PE malware first.
- **The evaluation is organized around the model's claims.** The computed answer is (i) correct: side effects match
  re-extraction, and the computed region contains every real combined edit; (ii) more correct than careful hand
  analysis: every disagreement with the old hand rules was the hand rules' error, each witnessed; (iii) more complete
  than constraints learned from attacks: PV's hole, found by our adaptive search; (iv) useful: detectors no attack
  moves. The defense route (monotone classifiers) is Gimenez et al.'s and Incer et al.'s. Our contribution is deriving
  the threat model's effects, and the detector shows why that matters.

The order of work agreed with the user is in `PLAN.md`, "Next steps (2026-11-02, stock-take done)":
1. the formalization (this session);
2. a paper mock;
3. a harsh simulated tier-1 review and a decision point;
4. A's gaps (adversarial-training baseline, second toolkit, scale, leave-one-out PV, cost column);
5. a second domain if the review calls for it;
6. the manuscript.

Tier-1 assessment from the stock-take: not sufficient today. It becomes competitive at CCS, USENIX Security and NDSS
once the formalization, the adversarial-training baseline, a second toolkit, and scale are in. A second domain likely
decides it at S&P.

## Read first

- `CLAUDE.md`
- `docs/status.md`, top block
- `PLAN.md`: Thesis, The model, and Next steps (2026-11-02, stock-take done)
- `docs/feature-provenance-model.md`, in full. It is the starting point: the three layers (items, sums, readouts),
  edits as item operations, the claims C1-C4 with proof sketches, the assumptions A1-A4, and coverage.
- `docs/item-layer-design.md`: the contribution vocabulary, the ten readout types, and the checks G1-G7. These checks
  become how the EMBER instance discharges the model's obligations; their results are in "Build status".
- `docs/direction-A-summary.md`: A's results and their gaps.
- `docs/literature-2026-10-22.md`: Pierazzi et al.'s problem-space formalization, Cheney et al.'s dependency
  provenance, Incer et al., Gimenez et al., Chen et al., Treant.

## The work: `docs/formalization.md`

Agree on the outline with the user first, then write. The document holds definitions, theorems, and full proofs. It
later becomes the source for the paper's framework section and its appendix. Proposed outline:

1. **Definitions.**
   - Elements and inputs.
   - Items, with membership (which elements an item is made of) and location (which elements decide whether an item
     exists and where).
   - The contribution vocabulary: count, add, bins, hashed (signed and unsigned), keyed, slot, opaque.
   - Sums: additive sums, and the max/min pools.
   - Readouts: the ten types.
   - The class of sum-then-readout extractors.
   - Edits as item deltas: add, remove, modify, move. Edit classes: content, item-creating, declared structural,
     undeclared structural.
   - A threat model as a catalogue of operations with parameter domains.
2. **Obligations.**
   - The assumptions A1-A4, stated as properties of an extractor per item kind: complete location, local
     contributions, local recognition, faithful declaration.
   - What a check must show to discharge each one on an instance (G1-G7 on EMBER).
   - What checks on natural files cannot catch: locality failures that only adversarial parameters trigger, such as
     the duplicate-DLL quirk.
3. **Theorems.**
   - Exact side effects (C1), for additive sums and max/min pools.
   - Coupling (C2): co-movement, and inseparability (the cone criterion; the shared-denominator case).
   - Soundness of the reachable region (C3): the cone, readout intervals, the mediant bound for ratios, the histogram
     polytope, the entropy interval, and boundary effects between added chunks.
   - Directions (C4): the per-file tests (sign, ratio, cross-entropy), the global union, and soundness of the derived
     table.
   - The composition: derived directions plus a monotone classifier give robustness under the threat model (with
     Gimenez et al.'s Proposition 1).
   - The flat provenance matrix P as a projection of the model.
   - Also consider: when the direction table is tight (every declared direction is realized by some edit), and what
     flagged or undeclared edits cost (soundness by declaring "both").
4. **For each theorem:** the checkable prediction it makes, and the run or check that tests it on EMBER (G1-G7; runs
   79, 92-93, 103-104, 111). If none exists, propose a cheap new check: state the hypothesis first, and put jobs
   over ~10 minutes in a `run/` script (next number: 117).
5. **Positioning.** What the formalization says beyond each of these, stated plainly and fairly:
   - Pierazzi et al. (side effects estimated empirically; the extractor treated as a black box);
   - incremental view maintenance and incremental computation;
   - abstract interpretation (sign and interval domains);
   - taint and dependency tracking.

This is writing, not building. No code or experiments unless a theorem needs a new check, and then only after the
user agrees.

## Standing rules

- Explain plainly.
- Never use doc-internal labels (C3, M_full, G2) without saying what they are.
- Answer methodology questions by reasoning, not by running data first.
- Never raise deadlines.
- Do not edit the manuscript.
- At the end of the session, update `docs/status.md`, `PLAN.md`, and this file.
- Commit in logical pieces; run ruff and mypy first if code changed.

## Notes

- Untracked, leave alone: `papers/`, `REVIEW*.md`, `TODO.md`, `docs/checkpoint-prompt.md`, `make-manuscript.sh`,
  `slides/`.
- The user still owes the upstream reports in `docs/upstream-issues.md`.
