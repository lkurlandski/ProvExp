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
