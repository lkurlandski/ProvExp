# Resume: ERDALT retrained on the new material; check task 0, then release (or drop) the other eight

Written in session 89 (2026-11-18, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading
first. One of three tracks: this one (ERDALT), `docs/resume-prompt-experiments.md` (the rest of the scale-up on the
cluster), `docs/resume-prompt.md` (general work and the index of the tracks). The diagnosis record:
`docs/erdalt-diagnosis-plan.md`.

## 1. The project and ERDALT's place in it

ProvExp computes, from an instrumented feature extractor, what an attacker's edits can do to the features, and from
that builds monotone detectors no edit in the threat model can evade. PE malware on EMBER2024 is the instance; the
paper is `manuscript/*.tex` (ACM CCS format). §5.3 compares our detectors with defenses *learned* from observed
attacks. ERDALT (Gimenez et al., "Certifiably robust malware detectors by design") is one of them: a learned square
linear layer L under a monotone network, trained so that every observed perturbation vector delta (features after an
attack minus before) maps to a nonnegative L delta; the epoch is chosen by their criterion (< 5 negative entries of
L delta over all vectors, "violations", then the best validation ROC-AUC; if no epoch meets it, the fewest
violations). The paper's claim: a defense learned from observed attacks inherits their blind spots. That claim is only
fair against an ERDALT trained as well as its authors train it (review risk R19,
`docs/reviews/2026-11-12-body/meta-review.md`, which also asks for the share of training and test perturbation
vectors with L delta < 0, and a donor-overlap control).

## 2. Where things stand

**The collapse (old material).** The nine scale-up models (`erdalt` and eight leave-one-out folds
`erdalt-loo-<attack>`; 310 epochs, ~30 h each on a GH200) all fell from validation AUC ~0.85 (epoch 1) to ~0.70 as
violations fell, criterion never met. Moved in session 89 to `artifacts/scaleup/superseded-s85/4-detectors/erdalt*`
(logs in its `logs/train-erdalt*.log`). `erdalt`'s old course (epoch: AUC, violations): 0: 0.820, 1.33M; 1: 0.853,
205k; 2: 0.833, 20k; 5: 0.797, 4.8k; 10: 0.764, 3.7k; 20: 0.736, 1.8k; 40: 0.696, 803; 275: 0.701, 39. The pilot's
ERDALT (1,797 vectors, the 10% store) met the criterion at its last epoch: 3 violations, validation 0.911, test 0.881.

**What session 89 found** (`docs/erdalt-diagnosis-plan.md`):
- The hypothesis that the constraint forces L to discard directions (vectors cancelling in a nonnegative combination)
  is refuted: a linear program finds no such combination among the 79,121 old or 78,715 new vectors (the cone is
  pointed). The check needs the vectors divided by their per-feature std first: on raw vectors (up to 1.8e11) HiGHS
  misses a planted opposite. Scripts: `artifacts/scaleup/diag/erdalt/lineality/` (`peek.py`, `lp.py`).
- **The broken outputs were the main pressure.** The features some vector lowers: 2,367 in the old material, 1,209 in
  the new. PV (a monotone GBDT on the never-lowered features) is a zero-violation ERDALT in disguise (L = identity
  with zeros on the lowered features); its validation AUC went from 0.553 (old; test 0.610) to **0.924** (new; test
  0.930; unconstrained GBDT 0.998). So on the new material a zero-violation model at 0.92 exists: **the benchmark a
  fairly trained ERDALT should reach.**
- Session 88's earlier findings (slice runs on a 200,000-file subsample, old material) stand but did not reproduce
  the collapse: AUC tracked violations in every variant; their 2,432-vectors-per-step cap did not keep AUC up; their
  free output layer was ~0.06 higher; the standardized inputs are extremely heavy-tailed (|z| up to 166,000, hashed
  section sizes; validation logits +-1e5). Logs: `artifacts/scaleup/diag/erdalt/`.

**The retrain (submitted by the user, session 89), as specified, on the new material**
(`artifacts/scaleup/4-detectors/material/sums`, merged by `learned` 1141848, which finished):
- **1169769_[0]**: `erdalt` (all eight attacks), `PART=erdalt` of `pipeline/4-detectors/learned/run.sh`, one GH200,
  4 cores, 128G, 2 days. Was pending on Priority at the end of session 89.
- **1169770_[1-8]**: the eight leave-one-out folds, **submitted with `--hold`** (JobHeldUser).
- Log: `artifacts/scaleup/4-detectors/logs/train-erdalt.log` (one `epoch=... vl_roc=... violations=... l1 l2 l3 lr`
  line per epoch, ~5.8 min apart, after ~10 min of loading); job output `logs/learned-erdalt_1169769_0.out`.

## 3. What this session does

1. **Check 1169769_0** (`squeue -u $USER`, `sacct -j 1169769 --format=JobID,State,Elapsed,MaxRSS,AllocCPUS`): if it
   has not started, say so and stop there. If it has, read the job output's startup line (threads, cores, process
   limit) and the log's epochs.
2. **Decide with the user whether to release the eight** (the user decides; Claude recommends). Hypothesis (session
   89): the old collapse came mostly from the broken outputs, so `erdalt` stays near or above PV's 0.92 while
   violations fall. Compare with the old course at matched epochs *and* at matched violation counts (above).
   - Holding near or above ~0.90 through epochs ~15-20 (most of the old fall happened by epoch 10): recommend
     `scontrol release 1169770`; the nine finish ~30 h later. Keep an eye on the end: the criterion (< 5 violations)
     was met only at the last epoch on the pilot.
   - Falling well below 0.92 as violations fall (the old course again): recommend `scancel 1169770` and the GPU
     variants of `docs/erdalt-diagnosis-plan.md` (control, 2,432 vectors per step, a robust linear input scaling,
     the free output layer reported separately), full training split, the first ~15 epochs of the 310-epoch
     schedule, compared by AUC at matched violations against the 0.92 benchmark. Write that plan out for the user's
     approval before running anything (a small `sbatch` array, one GH200 each, ~2 h).
   - In between: lay out what it shows and let the user choose; letting `erdalt` run to the end costs nothing extra.
3. **When the nine are done:** read them (selected epoch, validation AUC, violations, `met_criterion` in each
   `metrics.json`); R19's asks (share of training and test vectors with L delta < 0; donor-overlap control).
4. **Then ERDALT's attacks, held for this** (the other detectors' attacks run without it): `toolkit` with
   `DETECTORS=erdalt PARTS="main loo donors" LOO=erdalt` (`--array=0-9`); `adaptive` with `TAG=erdalt
   DETECTORS=erdalt ESCAPES=none EXPERT=0` (20 tasks, writes `none/shard-<k>-erdalt/`); MAB-Malware with
   `TAG=erdalt DETECTORS=erdalt SETTINGS=ours --array=0 --cpus-per-task=1` (writes `ours-erdalt/`); then `6-results`
   (`pipeline/6-results/run.sh`, which stops if a detector's outputs appear twice). Submit with plain
   `sbatch --export=ALL,...`, as in `logs/submit-*-no-erdalt.txt`. Check first with the experiments track that the
   other detectors' reruns on the new material are done.

## 4. Rules that apply

Think a run through before starting it: what it is compared with, whether its setup can reproduce the effect under
study, and what each outcome would mean; a hypothesis before every run; check a new analysis on a planted case before
trusting an empty answer (session 89's LP); report a failed check as such. Explain plainly. Do not retrain or change
the protocol without the user. On tigris: head node light only (two CPUs); request what a job uses for most of its
life; read each job's startup line; in an interactive job use only its allocation. Kill by PID, not `pkill -f`.
Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline`); do not push. At the end: update
`docs/status.md` and PLAN.md, rewrite this prompt (or archive it when the track is done,
`docs/archive/resume-prompt-erdalt-<date>-s<N>.md`, with its line in `docs/README.md`).
