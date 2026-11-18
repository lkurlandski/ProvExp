# Resume: ERDALT's collapse at the scale-up (plan the diagnosis first, then run it with the user's go-ahead)

Written in session 82 (2026-11-17); rewritten in session 88 (2026-11-18, tigris interactive GPU job), which ran short
diagnosis runs on a 200,000-file training slice and learned that the slice cannot reproduce the collapse (§4). **The
user's verdict on session 88: it began executing experiments without thinking them through.** So the first order of
business in this session is **a well-thought-out written plan** (§5) built on everything known (§2-§4), laid before
the user for approval; no training run starts before the user approves the plan. Self-contained: only `CLAUDE.md`
(loaded automatically) needs reading first. One of three tracks: this one (ERDALT), `docs/resume-prompt-experiments.md`
(the rest of the scale-up on the cluster), `docs/resume-prompt.md` (general work and the index of the tracks).

## 1. The project and ERDALT's place in it

ProvExp computes, from an instrumented feature extractor, what an attacker's edits can do to the features (exactly for
one edit; as sound directions for a whole threat model), and from those builds monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper is `manuscript/*.tex` (ACM CCS format).
§5.3 compares our detectors with defenses *learned* from observed attacks. ERDALT (Gimenez et al., "Certifiably robust
malware detectors by design") is one of them: a learned square linear layer L under a monotone network, trained so
that every observed perturbation vector delta (features after an attack minus before) maps to a nonnegative L delta.
The paper's claim about it: a defense learned from observed attacks inherits their blind spots. That claim is only
fair against an ERDALT trained as well as its authors train it; a weak ERDALT invites the straw-man objection (review
risk R19, `docs/reviews/2026-11-12-body/meta-review.md`, which also asks for the share of training and test
perturbation vectors with L delta < 0, and a donor-overlap control).

## 2. What happened at scale

The scale-up (`docs/scaleup-protocol.md`; tigris, RIT's aarch64 cluster, `SETUP.md`) trained nine ERDALT models
(`erdalt` and eight leave-one-out folds `erdalt-loo-<attack>`), one GH200 each, 310 epochs at ~5.8 min (~30 h), on
the full training split (1.76 million complete files) with 79,121 perturbation vectors from the defenses' material.
Logs: `artifacts/scaleup/4-detectors/logs/train-erdalt*.log`; outputs `artifacts/scaleup/4-detectors/erdalt*/`
(`metrics.json`: summary and per-epoch history).

**Every model collapsed the same way.** Selected epoch, validation AUC, violations (negative entries of L delta over
all vectors), all `met_criterion` false: `erdalt` 275, 0.701, 39; leave-one-out folds content_shift 193, 0.746, 37;
dos_extend 236, 0.710, 40; format_exploit 191, 0.712, 34; gamma_api 233, 0.752, 29; gamma_sections 215, 0.690, 34;
gamma_shift 212, 0.701, 27; header_fields 212, 0.692, 28; padding 171, 0.723, 16. Gimenez et al.'s criterion is < 5
violations; when no epoch meets it the code keeps the epoch with the fewest. GBDTs on the same data reach 0.998; the
pilot's ERDALT reached 0.883 (Gimenez et al. report 93.0%).

`erdalt`'s history (epoch: validation AUC, violations): 0: 0.820, 1,330,008; 1: 0.853, 205,326; 2: 0.833, 20,112;
3: 0.821, 7,793; 5: 0.797, 4,798; 10: 0.764, 3,677; 20: 0.736, 1,817; 40: 0.696, 803; 100: 0.695, 344; 275: 0.701, 39.
The penalty term `l2` is 18,801 at epoch 0, 5.7 at epoch 2, 0.05 at epoch 40, ~1e-7 at the end, so the AUC keeps
falling after the penalty is small; the remaining violations are tiny negative entries. **AUC falls as violations
fall**, most of it by epoch 10.

**The material changes.** Session 85 (experiments track) found 894 broken outputs (1.1%) in the defenses' material
(secml-malware's shift writing in front of the MZ header, DOS extensions on files with e_lfanew < 0x40, lost import
tables); one validity rule now decides for the whole paper whether an output counts (`provexp.attacks.validity`), the
shift is patched, and the material is being rebuilt: job 1141847 (10 shards; at the end of session 88, shard 6 was
still running, time limit 3 h 15 min). **The merge into `artifacts/scaleup/4-detectors/material/sums` happens at the
start of `learned` 1141848 (PART=gbdt, after 1141847)**; check for `material/sums/X.npy`. The old material is
`artifacts/scaleup/superseded-s85/4-detectors/material/sums`. **Every ERDALT model must be retrained on the new
material** whatever the diagnosis finds (the nine above used the old one).

## 3. What is ours and what is theirs

`src/provexp/models/erdalt.py` ports their `train_model.py` ("M_monotonic"), following the paper where the two differ.
**As theirs:** standardized inputs, the identity-initialized square linear layer without bias, hidden layers of 800
with ELU and dropout, Adam at 1e-4 with ReduceLROnPlateau on validation ROC-AUC (factor 0.5, patience 20), 310 epochs,
the loss w1 * BCE + w2 * sum(relu(-L delta)) + w3 * ||L off the diagonal|| with w1 0.5 -> 1, w2 0.5 -> 200, w3 0.5 -> 1
linearly over the epochs, the selection criterion (< 5 violations, then the best ROC-AUC). **Ours, deliberately:**
(1) batch size 256 instead of their 16; (2) the output layer projected to be monotone too (their code leaves it free,
so their network is not monotone; the paper's Proposition 3 needs it; `docs/upstream-issues.md` §8); (3) the epoch
chosen on validation, not test; (4) all vectors enter the penalty at every step, where their code draws at most 152
batches of 16 (2,432 vectors) per step from a shuffled loader (they had ~1,033 vectors, so all of theirs entered; with
our 79,121 the cap is theirs, not a deviation). BCE is a batch mean; the penalty a sum. **Different by scale:** 1.76 M
training files (pilot: a 10% store) and 79,121 vectors (pilot 3,183; Gimenez et al. ~1,033).

`pipeline/4-detectors/train/train_erdalt.py` has diagnosis options (defaults keep the original training):
`--train_subsample N`, `--epochs E --schedule_epochs 310` (the first E epochs of the full weight ramp),
`--deltas_per_step 2432`, `--batch_size`, `--free_output`, `--no_lr_scheduler`, and (session 88) `--penalty_scale s`
(multiplies w2 throughout). The history records `vl_roc`, `violations`, `l1`, `l2`, `l3`, `lr` per epoch.

## 4. What session 88 learned (old material; read before planning)

**The slice runs** (`artifacts/scaleup/diag/erdalt/`: `run.sh`, `logs/<v>.log`; 200,000 seeded training files,
validation in full, `--epochs 40 --schedule_epochs 310`; six variants sharing one GPU; stopped by the user's decision
at epoch ~21 except (b)). Last epoch reached, validation AUC, violations:

| Variant | Change | Epochs | AUC | Violations | Course |
|---|---|---|---|---|---|
| a | control | 22 | 0.822 | 15,862 | rising from 0.54, flat ~0.82 since epoch 12 |
| b | 2,432 vectors per step | 40 (done) | 0.794 | 127,177 | peak 0.813 (epoch 26), then sliding as violations fall |
| c | b + batch 16 | 17 | 0.746 | 66,422 | peak 0.821 (epoch 1), falling steadily |
| d | free output layer | 22 | 0.879 | 14,844 | ~0.90 from epoch 1, slightly down |
| e | no LR scheduler | 21 | 0.823 | 20,994 | as a (identical until the scheduler acts) |
| f | penalty weight x0.1 | 21 | 0.821 | 25,400 | as a, a little ahead early |

What these do and do not show:
- **The slice does not reproduce the collapse, so it cannot diagnose it.** The weight schedule advances per epoch,
  but a slice epoch is 781 steps against ~6,900 at full size, so the runs follow a different course (the control is
  at 0.82 with 16k violations at epoch 21; the full-scale model was at 0.736 with 1.8k). Session 88 should have
  checked this before running five variants; the plan must not rest on a subsample whose dynamics differ.
- **Across every variant, AUC falls as violations fall** (b, c, d visibly), as at full scale. A leading reading, not
  yet tested: the collapse is the cost of satisfying the constraint on this data, and the knobs mostly change how fast
  training gets there. None of the slice runs reached the low-violation region (< ~4k) where the full-scale AUC fell.
- **Their vectors-per-step cap (b) did not keep AUC up**, which weakens session 86's leading hypothesis (the summed
  penalty over 33x their vectors dominating).
- **The free output layer (d) is ~0.06 AUC higher at similar violations**: the monotone output layer costs accuracy
  (but the pilot reached 0.883 with it).
- **The standardized inputs are extremely heavy-tailed** (`input_scale.py`, `logs/input_scale.log`, using b's stored
  mean and std): per validation file, the largest |z| has median 10, 99th percentile 87, maximum 166,000; 480 of 2,568
  features reach |z| > 100, 33 reach > 1,000; the worst are the hashed section sizes (`section:size_hash_*`,
  `section:vsize_hash_*`). Per perturbation vector, the largest |delta/std| has median 20, 99th percentile 258,
  maximum 52,700. Validation logits reach +-1e5 at full scale (+-1e6 on the slice) where a healthy classifier's are
  in the tens. ERDALT's linear post-processing needs a linear input transform, so a fix cannot be a log or a clip.
- **The broken outputs are not the extreme vectors** (`broken_extremes.py`, `logs/broken_extremes.log`; broken as in
  session 85: `general:is_pe` lowered or >= 10 import features lowered): 894 broken vectors (1.13%) carry 8.8% of the
  negative mass in std units; all 14 vectors beyond 10,000 std are valid GAMMA outputs, every one extreme in
  `section:vsize_hash_48`. By attack, the share of the negative mass: gamma_sections 40.6%, gamma_shift 24.4%,
  gamma_api 22.1%, content_shift 5.6%, dos_extend 3.8%, format_exploit 2.7%, padding 0.6%, header_fields 0.3%. So the
  new material removes some pressure but most likely not the collapse; untested.
- **Practicalities:** loading the store takes ~10 min per process (disk-bound, worse when several load at once; peak
  ~91 GiB RAM each); with all vectors per step and five runs sharing one GH200, a slice epoch took ~5 min. Session 88's
  interactive job had 16 CPUs and one GPU shard (`gres/shard:gh200=1`); the node has much more memory (573 GiB).

## 5. What this session does

1. **Check the state:** the session's resources (`nvidia-smi`, `scontrol show job $SLURM_JOB_ID | grep TRES`; use the
   allocation, not `nproc`), whether the new material is merged (`4-detectors/material/sums/X.npy`; `squeue -u $USER`).
2. **Write the diagnosis plan and lay it before the user; no training before approval.** The plan states the
   question, what each run is compared with, the hypothesis and what result would confirm or refute it, the cost, and
   how the results map onto the user's decision. It should weigh, at least:
   - **The questions, separated:** (i) does the collapse survive the new material (a full-scale control, original
     settings, ~15 epochs: at full scale most of the fall happened by epoch 10)? (ii) is it inherent to ERDALT's
     constraint on this data (an AUC-violations trade-off), or (iii) caused by our deviations (batch 256, the monotone
     output layer, all vectors per step), or (iv) by the input scale (heavy-tailed standardized features)?
   - **Methodology:** the full training split (the slice failed; if anything is reduced, show first that the control
     reproduces the full-scale course); compare runs at matched violation counts, not only at matched epochs (the
     knobs change the speed of descent); fix what counts as a fair ERDALT (their configuration as closely as
     possible: their vectors per step, batch 16 if affordable, their free output layer reported separately since it
     breaks monotonicity) before choosing variants; whether a robust linear rescaling of the inputs is a fair
     deviation; what the pilot's ERDALT had (violations, logits) and why it reached 0.883 (re-run at tag
     `pilot-final` only if needed; the pilot's numbers may be in its logs).
   - **Compute:** one GPU per full-scale run at ~5.8 min per epoch alone (a 15-epoch run ~1.5 h plus ~10 min loading);
     runs sharing a GPU slow each other. Ask the user for an interactive job with several GPUs, or run the variants as
     a small `sbatch` array (the user said "run locally" for session 88's work; ask again).
   - **The decision it serves** (the user decides protocol questions; Claude recommends): report ERDALT as specified
     with the collapse as a finding about the method at scale; retrain with an identified fix (a deviation stated in
     Appendix D); or retrain matching their scale. R19's other asks stay in view.
3. **Run the approved plan; then retrain with the user's go-ahead, on the new material** (~30 h per model on 9 GPUs
   at the current setup; `pipeline/4-detectors/learned/run.sh` with `PART=erdalt`, as the array of 9 on GPU nodes via
   `pipeline/submit.sh`, or locally one per visible GPU; ask).
4. **Then ERDALT's attacks, held for this** (the other detectors' attacks run without it): `toolkit` with
   `DETECTORS=erdalt PARTS="main loo donors" LOO=erdalt` (`--array=0-9`); `adaptive` with `TAG=erdalt
   DETECTORS=erdalt ESCAPES=none EXPERT=0` (20 tasks, writes `none/shard-<k>-erdalt/`); MAB-Malware with
   `TAG=erdalt DETECTORS=erdalt SETTINGS=ours --array=0 --cpus-per-task=1` (writes `ours-erdalt/`); then `6-results`
   (`pipeline/6-results/run.sh`, which stops if a detector's outputs appear twice). Submit with plain
   `sbatch --export=ALL,...`, as in `logs/submit-*-no-erdalt.txt`.

## 6. Rules that apply

Think a run through before starting it: what it is compared with, whether its setup can reproduce the effect under
study (check that first), and what each outcome would mean; a hypothesis before every run; report a failed check as
such. Explain plainly. Do not retrain or change the protocol without the user. On tigris: head node light only (two
CPUs); request what a job uses for most of its life; read each job's startup line; in an interactive job use only its
allocation. When stopping processes, kill by PID (`pkill -f <pattern>` also matches the calling shell, whose command
line contains the pattern). Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline`); do not
push. At the end: update `docs/status.md` and PLAN.md, rewrite this prompt for the next ERDALT session (or archive it
when the track is done, `docs/archive/resume-prompt-erdalt-<date>-s<N>.md`, with its line in `docs/README.md`).
