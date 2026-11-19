# ERDALT's collapse at scale: the diagnosis plan (session 89, 2026-11-18; awaiting the user's approval)

Context: `docs/resume-prompt-erdalt.md` §2-§4. All nine scale-up models fell from validation AUC ~0.85 (epoch 1) to
~0.70 as their violations fell; the pilot reached 0.911 validation (0.881 test) with 3 violations at its last epoch
(run 128: 1,797 vectors, the 10% store). The 200,000-file slice of session 88 did not reproduce the fall. Nothing
below trains a network until the user approves.

## Result of the first check (session 89, old material): the hypothesis below is REFUTED

The linear program of step 1 ran in the interactive job (scratch script; vectors divided by their per-feature std,
then scaled to unit length). On the raw vectors it is numerically broken: features reach 1.8e11, and it missed a
planted exact opposite. With the scaling it finds the planted one (3 vectors, 2 dimensions). On the real vectors:
**no vector takes part in any zero-sum combination**, for 2,000, 10,000 and all 79,121 (26 s). The cone the
perturbation vectors generate is pointed, so nothing forces L to discard a direction. An invertible L with zero
violations exists in principle, and the projection ceiling below does not exist. Coordinate by coordinate, 2,229 of
2,568 features are moved both ways, but never in an exactly cancelling combination. The vectors are dense (median
587 nonzero features).

What could still make the constraint costly without discarding anything: the network must be nondecreasing along
every observed vector. If the vectors fan out across nearly a half-space, the rows of L are confined to a very thin
cone. Proposed replacements for steps 1-3 (not yet approved): (a) how thin it is: one LP for the largest margin s
with w . d >= s for every unit-length scaled vector, ||w|| <= 1; (b) an existence check: construct a zero-violation
L (e.g. for each feature, the row nearest e_j in that cone) and train a monotone GBDT on L x; high AUC means a good
ERDALT exists and the collapse is training. Then the GPU runs below become the main diagnosis.

## The new material, and the decision (session 89, user's go-ahead)

On the new material (78,715 vectors) the cone is pointed too, but the features some vector lowers fall from 2,367 to
1,209: most of the old ones came from the broken outputs. PV (a monotone GBDT on the never-lowered features) is a
zero-violation ERDALT in disguise (L = identity with zeros on the lowered features), and its validation AUC goes from
0.553 (old material) to **0.924** (new; test 0.930; unconstrained 0.998). So the old ERDALT's 0.70 beat what the old
material allowed PV, and on the new material a zero-violation model at 0.92 exists: the benchmark a fairly trained
ERDALT should reach.

Decision: no separate diagnosis; the nine ERDALT models are retrained as specified on the new material (the old ones
moved to `superseded-s85/4-detectors/`), read early. If `erdalt` holds near or above 0.92 through epoch ~15-20, the
collapse was the material and the retrains run to the end. If it falls well below 0.92 as violations fall, cancel
the array and run the GPU variants below, judged against 0.92.

## The question that decides everything first (original plan; refuted above): can any ERDALT do better on this material?

**Plain version.** ERDALT requires L delta >= 0 for every observed perturbation vector delta. Suppose the attacks
move some direction both ways: one vector pushes the features along v, and another vector (or a positive mix of
several) pushes them along -v. Then every row of L must give v exactly zero, since it may give neither v nor -v a
negative value. So L must *throw away* every direction the observed attacks move both ways, whatever the training
does. The network after L sees only what is left, so no ERDALT can classify better than the best classifier given
only that remainder. With 1,797 vectors (pilot) little may be thrown away; with 79,121 vectors from eight attacks,
far more. The pilot already found 1,060 features moved both ways (run 128's "hole").

**What is computed (no GPU, no network training):**
1. The perturbation vectors in standardized units (as ERDALT sees them), each scaled to unit length (the constraint
   ignores length). The directions moved both ways (in convex geometry: the lineality space of the cone the vectors
   generate) come from one linear program: find nonnegative weights on the vectors that sum to zero with as many
   vectors as possible taking part; the vectors that can take part span exactly the directions L must annihilate.
   Report its dimension out of 2,568.
2. The ceiling: project the training and validation features onto what is left (a linear map) and train a GBDT on
   them (on a seeded subsample of ~300,000 training files; checked first: the GBDT on the unprojected subsample must
   reach ~0.99, near the full model's 0.998, so the subsample is not what limits it). Its validation AUC is an upper
   bound on any ERDALT that meets the zero-violation constraint (loose: ERDALT also needs a monotone network and rows
   of L inside the dual cone, which the bound ignores).
3. The same for random draws of 1,800 (the pilot's count), 2,400, 10,000 and all vectors, to see whether the ceiling
   falls as more attack vectors are observed, and whether it explains the pilot's 0.91 against the scale-up's 0.70.

**Hypothesis.** The dimension thrown away is large (hundreds of the 2,568) and the ceiling with all vectors is near
the trained models' ~0.70-0.75, well above it with ~1,800. Then the collapse is the method's cost on this material,
not a training failure. Refuted if the ceiling with all vectors stays >= ~0.90.

**Cost.** Loading the training store for the clean rows (~10 min), the LP (unknown; tried first on 10,000 vectors to
estimate), the GBDTs (~10-20 min each at 16 CPUs on 300,000 files; 5 of them). ~1.5-2 h in this interactive job's
16 CPUs, on the old material now; repeated on the new material once 1141848 merges it (the check is cheap, and the
new material drops the 894 broken outputs, which may have supplied some of the both-way directions).

**Where it can mislead.** Numerical tolerance in the LP (tiny components of extreme vectors): run it at two
tolerances and on the deduplicated vectors. Violations counted strictly (< 0), so exact zeros are allowed, as the
bound assumes; the criterion's "< 5" allowance is ignored (four vectors cannot buy back much).

## Then, depending on the ceiling

**Ceiling near the trained AUC (<= ~0.78): the collapse is inherent.** No GPU diagnosis is needed. Recommendation:
retrain the nine models as specified on the new material (needed anyway; their course also answers whether the
collapse survives the new material), and report the collapse as a finding about the method with the ceiling as its
evidence: a learned post-processing that must hold for every observed attack has to discard every direction the
attacks move both ways, and the more attacks it observes the less is left to classify with. This answers R19 better
than any training tweak could (no ERDALT, however trained, does better under its own criterion), and the ceiling
curve over the number of vectors explains the pilot's 0.88. A free output layer or a different input scale cannot
change the ceiling: a linear rescaling of the inputs maps the thrown-away directions onto each other.

**Ceiling clearly above (>= ~0.85): the collapse is training.** Then GPU runs, on the full training split and the new
material, the first 15 epochs of the 310-epoch schedule (most of the fall happened by epoch 10 at full scale),
compared on validation AUC *at matched violation counts* (the curve of AUC against violations), not at matched
epochs:
- control (original settings; also answers whether the collapse survives the new material);
- their configuration as closely as is affordable: 2,432 vectors per step (batch 16 is not affordable: ~110,000
  steps per epoch, ~16x slower, ~1.5 h per epoch);
- a robust linear input scaling (per-feature scale from a high quantile instead of the std; linear, so ERDALT's
  guarantee holds; a stated deviation);
- their free output layer, reported separately (it breaks monotonicity, so it cannot be the paper's ERDALT).
A variant fixes the collapse if its curve stays clearly above the control's in the low-violation region (< ~4,000,
where the full-scale AUC fell). Each run ~1.5 h + ~10 min loading alone on a GH200; four runs: a small `sbatch` array
on GH200 nodes (one GPU, ~4 cores, ~110 GiB each, ~2.5 h limit), or sequentially in an interactive job (~7 h). Then
retrain the nine with the fix, stated in Appendix D.

**In between:** both: the ceiling reported, and the GPU runs to see how much of the gap training recovers.

## Kept in view

R19's other asks come after the retrain: the share of training and test perturbation vectors with L delta < 0, and
the donor-overlap control. ERDALT's attacks (resume prompt §5.4) wait for the retrained models.

## Session 90 (2026-11-18): the retrain collapses too; the GPU diagnosis (approved by the user)

`erdalt` on the new material (1169769_0), epoch: validation AUC, violations: 0: 0.843, 1.39M; 1: 0.846, 210k; 2:
0.831, 17.9k; 3: 0.807, 7.4k; 5: 0.782, 5.9k; 7: 0.770, 4.2k. Old material at matched points: 5: 0.797, 4.8k; 10:
0.764, 3.7k. The same course at matched epochs and at matched violations: **the hypothesis that the broken outputs
caused the collapse is refuted.** The eight folds (1169770) were cancelled; `erdalt` runs to the end (its full course,
and whether the criterion is ever met). Since the zero-violation PV reaches 0.92 on this material, a good model exists
that ERDALT does not find.

**Bug, or a weak method?** (the user's question.) For "the method": Gimenez et al.'s own Table 2 already has ERDALT
below PV (0.930 against PV + RF 0.952; ERDALT + adversarial training 0.855; their monotone network alone 0.874); the
port was checked against their released code (2026-10-27); the fall reproduces on two materials. For "something off":
a zero-violation model at 0.92 exists, and their training setup was sized for a much smaller problem (below).

**Their setup, reread (paper §5 and `train_model.py` at 0b6f222, session 90).** Training set 24,000 files (12,000
malware from 120 families, 12,000 goodware); **1,033 adversarial examples in all** (the paper: "Each method has access
to 1033 adversarial examples"; `docs/literature-2026-10-22.md` had misread it as per method); batch 16, so ~1,500
steps per epoch and ~465,000 steps over `num_epochs = 310`. The 310 epochs are a constant in their script, not a
paper hyperparameter. Each step's penalty sums over up to 152 loader batches of 16 vectors (2,432), i.e. all 1,033 of
theirs. Ours: 1,764,552 training files (73x) at batch 256, ~6,900 steps per epoch, ~2.1M steps over 310 epochs; and
the penalty sums over all 78,715 vectors (76x theirs) against a BCE that is a batch mean. So at the same weight w2,
our penalty weighs ~76x more against the classification loss than theirs, and the 310-epoch ramp of w2 spans 4.6x
their steps. Two parts of the port that were faithful to the letter are probably not faithful in effect: the penalty
mass per step, and the length of the weight schedule.

**Setup.** New material, full training split, seed 0, one change per task; 15 epochs of the 310-epoch schedule
(`--epochs 15 --schedule_epochs 310`) unless stated. One GH200, 4 cores, 128G (the full run peaks at ~95 GB), 3 h
(~10 min loading + ~5.8 min per epoch). The control is `erdalt`'s own first 15 epochs. Compared on validation AUC at
matched violation counts, against the control and PV's 0.92. Script: `artifacts/scaleup/diag/erdalt/gpu/run.sh`
(array 0-6, reordered by importance: 0 pscale, 1 n1033, 2 fixed, 3 short, 4 cap, 5 pv-init, 6 robust; the
table's task numbers are the first order), logs in `artifacts/scaleup/diag/erdalt/gpu/logs/<variant>.log`.

| task | run | change | question |
|---|---|---|---|
| 0 | fixed | L frozen at PV's mask (identity, zero on the 1,209 lowered features; 1,359 kept); only the network trains | Can their network reach ~0.92 when handed a zero-violation L? |
| 1 | pv-init | L starts at PV's mask and trains | Does their training keep a good L, or leave it? |
| 2 | n1033 | a fixed seeded 1,033 of the 78,715 vectors (their count); violations over all 78,715 logged too | With their count, does it hold up, and how many unseen vectors does it violate? |
| 3 | pscale | all vectors, w2 times 1033/78715 (their penalty mass per step) | Is the collapse the penalty's weight? |
| 4 | cap | 2,432 vectors drawn per step (their code's cap) | Their code's rule applied to our count |
| 5 | short | the whole weight schedule in 20 epochs (`--epochs 20 --schedule_epochs 20`) | Does a schedule sized to our data reach the criterion with a better AUC? |
| 6 | robust | per-feature scale max(std, 0.9999 quantile of \|x - mean\|) | Are the heavy tails the problem? (Weak premise: the extreme values are validation files beyond anything in training, where \|z\| <= sqrt(n) ~ 1,300, and no linear scale pulls those in; kept because it is cheap.) |

`--free_output` is left out (session 88: +0.06 on the slice, but it breaks monotonicity, so it cannot be the paper's
ERDALT). n1033 and pscale have the same penalty mass per step and differ only in which vectors: together they
separate "how many attacks were observed" from "how heavy the penalty is".

**Hypothesis.** The penalty's weight is the main cause: pscale and n1033 stay well above the control at matched
violations (near ~0.9), cap in between; fixed reaches ~0.88-0.92 (the network is not the limit; a monotone GBDT gets
0.92 from the same features); n1033 violates many of the unseen vectors.
- pscale near 0.9 and short at least as good: the port's penalty mass and schedule were unfaithful in effect;
  retrain the nine with their per-step mass (and a schedule sized to our data), stated in Appendix D. ERDALT then
  stands as a fair baseline, and the blind-spot claim rests on its violations of the unseen vectors.
- pscale like the control, fixed high: their training does not find the good L that exists at this scale, a property
  of the method; report ERDALT as specified with this evidence.
- fixed low (~0.77): their network on these inputs is the limit (robust decides whether scaling helps): a monotone
  network is weaker than a monotone GBDT here, a property of the method.

**Code (session 90):** `train_erdalt` options `post_init="pv"`, `freeze_post`, `deltas_subsample` (with
`violations_all` per epoch), `input_scale="quantile"` (`fit_quantile_scale`); CLI flags of the same names in
`train_erdalt.py`; tests in `tests/test_erdalt.py::TestDiagnosisOptions`. Smoke test on 20,000 files per split, 2
epochs (interactive job): every flag runs; PV's mask keeps 1,359 features with zero violations over all vectors; the
AUC of a 2-epoch slice says nothing (the control is at 0.52 there too).

## Session 91 (2026-11-19): the diagnosis read; the input scale, not the penalty, is the cause

All seven tasks of 1179478 completed (sacct: 13 min for n1033 and cap, 45 min to 2 h for the others; MaxRSS 63-96 GB
of 128G; TotalCPU ~ Elapsed, one busy core of 4). Validation AUC at the last epoch and selected test AUC; the control
(`erdalt`) is 0.843 at 1.39M violations, 0.807 at 7.4k, 0.770 at 4.2k (epoch 7). No task met the criterion.

| run | epoch 0 | last epoch | violations, last | test AUC (selected) | reading |
|---|---|---|---|---|---|
| pscale | 0.878 | 0.824 | 111k | 0.831 | a 76x lighter penalty: violations stay high and the AUC still falls; no better than the control at matched violations (~0.84 at 110k) |
| n1033 | 0.917 (0.934 at 1) | 0.824 | 87 (of the 1,033); ~11.0M over all 78,715 | 0.858 | falls as its own violations fall; violates ~8x more entries of all vectors than the control after one epoch |
| fixed | 0.547 | 0.396 | 0 | 0.590 | the network cannot use PV's 1,359 features at all (PV's GBDT: 0.924), and gets worse |
| short | 0.843 | 0.744 | 593 | 0.755 | the control, faster |
| cap | 0.828 | 0.733 | 70k | 0.749 | below the control |
| pv-init | 0.866 | 0.749 | 3.0k | 0.758 | leaves the good L and falls like the control |
| robust | 0.905 | **0.938** | 7.5k | **0.940** | rises while violations fall; 0.13 above the control at matched violations, above PV's 0.924 |

**The hypothesis is refuted.** The penalty's weight is not the main cause: with 1/76 of it (pscale) the AUC falls just
the same at matched violations, and with no penalty at all (fixed) the network fails outright. What all failing runs
share is the input scale, and the one run that changes it (robust: per-feature scale max(std, 0.9999 quantile of
|x - mean|)) is the one that holds: validation 0.938 and test 0.940 at 7.5k violations, against the control's 0.81.
Its temperature also falls from 400-10,000 to 67 (validation logits up to 2,025 instead of 1e4-3e5): with the std
scale, the heavy-tailed features of a few validation files dominate the monotone network's output. The premise noted
as weak in the table above (no linear scale pulls the extremes in) was wrong in effect.

**In the porting lesson's terms.** Their std scale is fitted on 24,000 files; ours on 1.76M, whose features reach
1.8e11: the scale is a constant sized to their data (the feature set is the same EMBER family). The quantile scale is
linear and per feature, so monotonicity, L's meaning (the vectors are divided by the same scale) and Proposition 3 are
untouched. Not yet checked: that the std on a 24,000-file sample of ours behaves like theirs (a cheap check of the
claim that the difference is the data size, not only the tails).

**Open, so not yet the retrain:** robust has not met the criterion (7.5k violations at epoch 14 of 310); whether its
AUC holds down to < 5 violations is the question that decides the retrain. Round 2 (prepared, not submitted; same
script, `--array=7-9`, 2 cores): 7 robust-short (quantile scale, the whole schedule in 20 epochs: is the criterion met,
at what AUC?), 8 robust-fixed (quantile scale, L frozen at PV's mask: the network's ceiling at zero violations), 9
robust-n1033 (quantile scale, their 1,033 vectors: violations of the unseen ones, the blind-spot evidence).
Hypothesis: robust-short reaches the criterion or near it (< 100) at validation ~0.90-0.93; robust-fixed ~0.90-0.92;
robust-n1033 keeps ~0.93 but violates millions of entries of the unseen vectors.

**Correction and a fourth task (session 91, after the user's question).** "pscale no better than the control" was too
strong. At matched epochs pscale is clearly better (+0.035 at epoch 0, +0.055 at 3, +0.086 at 7); at matched
violations it is about +0.015 near 200k and about -0.015 near 110k, and it never got below 110k in 15 epochs. So the
lighter penalty slows the fall rather than removing it. The user leans to keeping their per-step penalty mass (the
effect-faithful choice under the porting rule), so round 2 adds task 10, robust-pscale: the quantile scale with
w2 x 1033/78715 and task 7's 20-epoch schedule, so 7 and 10 differ only in the weight.

**Per-step schedule (session 91, the user's suggestion).** The loss weights were held for a whole epoch (theirs: 310
increments of w2 of ~0.65, every ~1,500 steps). On a 20-epoch schedule that is 20 jumps of ~10.5 held for ~6,900
steps each, the first one 0.5 -> 11. `train_erdalt(schedule_per_step=True)` (`--schedule_per_step`; `loss_weights`)
interpolates linearly within each epoch: the same values at whole epochs, the same endpoints. Tasks 7 and 10 use it,
so they still differ only in w2; task 7 now differs from round 1's `short` in the scale and the smoothing together.

## Session 94 (2026-11-19): round 2 read; the retrain

All four tasks of 1239145 completed (sacct: 13 min n1033, 52 min fixed, 2 h 04 min for the two 20-epoch runs; MaxRSS
~96 GB of 128G; TotalCPU ~ Elapsed, one busy core of 2: the header fits). Startup lines as expected (OMP 1, 2 cores).
No task met the criterion (< 5 violated entries).

| run | epoch 0 | last epoch | violations, last | test AUC (selected) | hypothesis |
|---|---|---|---|---|---|
| robust-short (w2 -> 200, 20 epochs, per step) | 0.861 | 0.914 | 769 (plateau ~800-1,300 from epoch 9) | 0.919 | AUC in range; < 100 violations **failed** |
| robust-pscale (w2 -> 2.6, otherwise as above) | 0.911 | 0.951 (0.954 at 18) | 40k (88k at epoch 1) | 0.956 | as predicted: higher AUC, far from the criterion |
| robust-fixed (L frozen at PV's mask) | 0.723 | 0.819, still rising ~0.0015/epoch | 0 | 0.831 | **failed** (predicted 0.90-0.92) |
| robust-n1033 (their 1,033 vectors) | 0.959 | 0.971 (own: 577) | 545 own; **8.8M of the 202M entries over all 78,715 vectors (~4.4%)** | 0.973 | as predicted |

Reading. (1) The quantile scale removes the collapse under the literal penalty too: robust-short's AUC dips to 0.868 by
epoch 5 and then rises to 0.914 as w2 reaches 200, where the std-scale `short` fell to 0.744. (2) Under the heavy
penalty the violations stop falling near ~800 from epoch 9 on while w2 still doubles: the last few hundred entries
resist the penalty (not yet looked at: which vectors and features carry them). (3) With their per-step penalty mass,
20 epochs are 138k steps against their ~465k, and violations end 100x above robust-short's. (4) robust-fixed shows the
monotone network learns PV's features slowly (constant lr 1e-4); 15 epochs are not its ceiling, so it does not bound
what ERDALT can reach; it does show the std scale was what made `fixed` fail outright (0.40 -> 0.82). (5) robust-n1033
is the blind-spot evidence in its plainest form: trained on their count of vectors it scores higher than any other
variant and leaves ~4.4% of all entries of the unseen vectors negative.

**The criterion is also a constant sized to their data.** "< 5 violated entries" counts over all vectors; theirs are
1,033, ours 78,715 (76x). The same rate per vector is < ~380 for us; robust-short's 769 is 2x above it, robust-pscale's
40k is 100x above. Rescaling it is the porting rule's "selection criteria" item; it must be stated in Appendix D.

**The retrain (decided with the user, session 94).** `erdalt` and the eight folds, in `pipeline/4-detectors/learned`
(b9edda9), each setting rescaled to keep their method's effect: the quantile input scale; w2 x 1,033 / the vectors a
model sees (`--reference_vectors 1033`); the criterion < 5 x our vectors / 1,033 (`--scale_criterion`: < 381 for
`erdalt`, ~330-370 for a fold); the schedule over their ~465,000 steps (68 epochs, `--schedule_per_step`); the learning
rate's patience 20 -> 4 epochs (their 20 epochs are ~30,000 steps, 4.35 of ours). Batch 256 kept (theirs 16). Smoke
test (2,000 files per split, 2 epochs, a fold): runs end to end, every setting saved in `erdalt.json`. Expected:
validation AUC ~0.93-0.95; violations uncertain (robust-pscale: 40k after 138k steps, still falling), the criterion
met with less than even odds. The user submits `erdalt` (array task 0) first and the eight folds (1-8) held, released
once `erdalt`'s first epochs look right. The ERDALT track is folded into `docs/resume-prompt-experiments.md`; this
record and the track's prompt are archived once the retrain is verified.
