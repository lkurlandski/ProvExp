# Resume prompt: the cost of robustness, the rewrite of §5.4 (written 2026-11-16, session 72)

Paste into a fresh **Opus** session (the user moved the drafting off Fable to save credits). Read first, in this
order: `docs/evidence/fable-cost-of-robustness.md` §7 (what was decided and rejected), §8 (the experiments' results)
and §2.5 (the table the rewrite is built around); then §5.4 (*What Robustness Costs*) in
`manuscript/_f_evaluation.tex`; then the skill `paper-prose`.

## What is settled

- Step 1's experiments are run at pilot scale and read (findings §8). At 1% / 0.1% FPR: unconstrained 93.5 / 84.4;
  two-sided sums dropped 91.8 / 78.8; fixed sums alone 79.7 / 57.7; monotone as in Table 5 85.7 / 68.1; monotone
  trained past the 500-round cap 87.2 / 71.8 (1,567 rounds). The constraint method makes no difference. The monotone
  detector takes 80% of its split gain from the 203 fixed sums. Zero structural violations.
- **No extractor changes** (anchored sums, verified signatures): rejected by the user, do not raise them. None of the
  mathematics is a headline contribution; Propositions B and E appear as two or three sentences of prose, with no
  numbered statement.
- The guarantee's dependence on the fixed sums is said plainly: the detector rests on fields the threat model does
  not write, and holds only while they stay outside it.

## The paragraph plan for *Where the cost lies* (approved by the user "for now")

1. **What a monotone detector may read.** Unconstrained on the fixed sums; on the one-sided sums it may only count
   evidence of malware; nothing from the two-sided sums. The share of split gain on the fixed sums (80%).
2. **What no detector on these sums could keep.** Sums the attacker can set to any value carry nothing for any
   unevadable detector (Proposition E in a sentence or two; the signature is the main case). Dropping the two-sided
   sums costs 1.7 points at 1% FPR, 5.6 at 0.1%.
3. **What rests on the fixed sums.** The fixed sums alone detect 79.7%; the one-sided sums add 7.5 points. The plain
   statement of the condition above.
4. **The per-operation prices.** The current text (imports 2.1, the three overwrites 1.4, rename 0.1, the caveat at
   0.1% FPR), shortened. These were measured on the table before the entry write (`% PROTOCOL` comment); keep that
   comment.
5. The learner: one sentence at most. Whether the paper's monotone rows move to the uncapped training is the user's
   decision (below); until then the text keeps Table 5's 85.7 / 68.1.

Draft straight into the `.tex`, in one small block for the user's review, pilot numbers (the scale-up re-runs them).
Then `make` and `make check` in `manuscript/`, and read the rendered text before showing it.

## Remaining steps, in order

1. Optional, about 5 minutes: the `advanced` constraint method (`intermediate` showed no effect, so expect none).
   The existing models are skipped:

       OUT_ROOT=artifacts/experiments/cost_split COMPLETE=0 \
       SUMS=artifacts/features/ember2024-sums-10-v2 DIR=artifacts/experiments/a_directions_derived_sums_loose \
       REF=artifacts/models/gbdt/seed-0-s10-ref MONO=artifacts/models/gbdt/seed-0-s10-mfull-sums-loose \
       bash pipeline/4-detectors/cost-split/run.sh

   Add its row to the findings file's §8.
2. Draft the rewrite from the plan above; log the user's reactions in `docs/writing-spec.md`.
3. Ask the user: should the scale-up train the monotone detectors until the validation metric stops improving
   (cap 3,000) instead of 500 rounds? It gains 1.5 points at 1% FPR here and changes Table 5's monotone rows; for a
   fair comparison every detector would get the same rule (`4-detectors/train/run.sh`).
4. Update `docs/status.md`; commit.
5. **Step 2** (the converse of Corollary 1 as a theorem, findings §7) is the user's call and is the part worth a
   Fable session; it starts with a literature check.
