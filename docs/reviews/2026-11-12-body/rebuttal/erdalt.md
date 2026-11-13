# erdalt: R19

## The deciding questions

ERDALT's guarantee rests on one condition. Its linear layer L takes the change an attack makes to the features, δ, and
must map it to a vector with no negative entry (L(δ) ≥ 0). The network above L is monotone, so a nonnegative L(δ) can
only raise the score. Training enforces the condition only through a penalty term. The question: did the stored model
(`artifacts/models/erdalt/seed-0-s10-best`, the ERDALT row of Table 4, "Defenses learned from the outputs of the
toolkit attacks") actually meet it?

**1. What share of the training perturbation vectors violate L(δ) ≥ 0?** Almost none: 2 of the 3,183 vectors have a
negative entry, one from content shift and one from padding, and each of those entries is above −4·10⁻⁷. None of the
399 GAMMA-imports training vectors violates the condition. Their smallest entry is +1·10⁻⁴, so they clear it by a
margin. Checked by recomputing L(δ) for every training vector with the stored model (the vectors built as
`scripts/train_erdalt.py:63-84` builds them, from `artifacts/experiments/a1/advtrain/generated-seedperfile`). The
training log agrees: the selected epoch has 2 violations (`artifacts/models/erdalt/seed-0-s10-best/metrics.json`).
The 24 GAMMA-imports outputs that evade it on test malware are not stored (the harness keeps only scores:
`a_varied/toolkit-erdalt/results.parquet`), but they need no measurement. Every layer above L has nonnegative weights
and monotone activations (`src/provexp/models/erdalt.py:99-103`), so a file can only fall below the threshold if its
L(δ) has a negative entry. All 24 violate the condition, and no training vector does in any meaningful amount. This is
exactly the outcome the meta-review gave as the test of the paper's reading: the fall is the unseen-vector failure, not
a training failure.

**2. Does training to a proper stopping point raise the AUC toward their 93% and change the 24/29?** The premise is
wrong: ERDALT was not stopped after one epoch. It ran Gimenez et al.'s full 310-epoch schedule. "One epoch of 310 met
the criterion" (PLAN.md:353) means that only one epoch, epoch 297, met their selection rule (fewer than 5 violations).
The other epochs were trained but not kept. Validation AUC rises from .868 at epoch 20 to about .90 at epochs 280-309
and peaks at .907 (epoch 306, 35 violations). Epoch 297 has .895 on validation and .883 on test (`metrics.json`, log
`artifacts/logs/train_erdalt-0-s10-best.log`). No epoch comes near .93. In optimizer steps, our run took about 250k
(812 batches of 256 per epoch); theirs took about 465k (24,000 training files in batches of 16), on 9 times fewer
files. Training longer under the same schedule is not their method, because the penalty weight ramps up to its end
value at epoch 310. So longer training would at most add a point or two of AUC. It cannot change the 24/29, which by
question 1 does not come from violations on the training vectors.

## R19: the ERDALT port may be judged weak
**Opinion:** change the argument or description (the training met the constraint, so the finding stands; the paper
should show that and credit their assumption)

All four reviewers raise this (A-W6, B-W8, C-W5, D-W6; C-Q4). At its strongest: the port detects much less than the
original (AUC .883 against 93.0%), and its constraint is only a soft penalty. An evasion by an attack it was trained on
may therefore be a training failure rather than a design limit. And Gimenez et al.'s Proposition 3 assumes a finite,
known set of perturbation vectors, so "the layer constrains the feature changes it was shown" restates their
hypothesis (C-W5). D-W6 adds that the defenses were starved of data.

What holds: the AUC gap is real relative to the gradient-boosted trees (GBDT) in each setup. Their ERDALT sits 4.5
points below their GBDT (93.0 vs 97.5, their Tables 1-2). Ours sits 11 points below ours (Table 4). Part of the gap
may come from keeping the output layer nonnegative, since their 93.0% comes from the released code, whose network is
not monotone. The datasets also differ.

The training-failure reading is refuted by the stored model (question 1). The layer maps every training vector,
including all 399 GAMMA-imports ones, to a nonnegative vector, and maps the 24 evading test vectors to a vector with a
negative entry. The port also behaves like theirs where their claim applies. Seven of its eight training attacks evade
it on none of the 29 malware it detects (Table 11, "Malware evaded by each attack, per detector"), in line with their
96% robustness against the attacks it learned from. "Starved" does not fit ERDALT either. It learns from 3,183 vectors
against their 1,033, on 207,872 training files against their 24,000. "Stopped after one epoch" misreads PLAN.md
(question 2). The request to run the unmodified released code is settled (session 41, memory
`methods-from-paper-not-code`): its output layer breaks the monotonicity Proposition 3 needs, so its evasions would not
test ERDALT's guarantee.

The calibration questions. Would I propose this unprompted? The constraint check, yes: it is the obvious alternative
explanation, it is closed in one sentence, and a reader cannot rule it out from the paper. Restating a finding?
C-W5's restatement charge half-applies. The paper does not claim Gimenez et al. overlooked the assumption, but it never
says Proposition 3 makes it. Crediting it costs nothing, and what we add is the measurement: the assumption fails
against the attack ERDALT was trained on, once the attack's donor files change, and the derived table shows where the
weight lies (90%).

The smallest change, in three parts:
- §5.3 "What ERDALT learns": one sentence saying the layer maps all 3,183 training vectors to nonnegative vectors (2
  entries within 4·10⁻⁷ of zero), so the evasions come from vectors it never saw. Name that unseen vectors are what
  Proposition 3 excludes.
- Appendix D "ERDALT": state the training in a sentence (their 310-epoch schedule, the epoch chosen by their own
  criterion on the validation split) and both setups side by side (their 1,033 vectors and dataset; ours).
- The donor-overlap control (D-W6) as a small run at the scale-up. The §5.3 sentence "it takes them from benign test
  files, whose imports ERDALT never saw" is a causal claim that no run tests yet. GAMMA imports against ERDALT with the
  training donors needs a donor-pool option in `scripts/a1_evaluate.py` and about 30 files of one attack (minutes).
  Either result is useful. If ERDALT holds, the donors are shown to be the cause. If it falls, the cause is the new
  host files, and the sentence must say so.

Without the first two, a reader can blame our training. Without the third, the donor explanation stays unmeasured.
