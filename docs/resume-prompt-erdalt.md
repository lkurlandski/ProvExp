# Resume: ERDALT's collapse at the scale-up (diagnose, then decide with the user)

Written in session 82 (2026-11-17), updated in session 86 (2026-11-18, on the local machine: it found the upstream
penalty's per-step size and added the diagnosis options) and session 87 (2026-11-18, on tigris: it read the nine
finished models, §2, and found the penalty small from epoch 2 on, §4; it could not run the diagnosis because its
interactive job had no GPU). **This session runs in an interactive job on a tigris GPU node** (the user starts it with
a GPU): **run the diagnosis locally in this session, not through `sbatch`** (user, 2026-11-18). First check what the
job actually has: `nvidia-smi`, `env/bin/python -c "import torch; print(torch.cuda.device_count())"`, `nproc`, and
`scontrol show job $SLURM_JOB_ID | grep TRES` (session 87's job showed 72 CPUs in its cpuset but was allocated 16 and
no GPU; use what the allocation says). If no GPU is visible, stop and tell the user. Self-contained: only `CLAUDE.md`
(loaded automatically) needs reading first. One
of three tracks: this one (ERDALT), `docs/resume-prompt-experiments.md` (the rest of the scale-up on the cluster),
`docs/resume-prompt.md` (general work and the index of the tracks).

## 1. The project and ERDALT's place in it

ProvExp computes, from an instrumented feature extractor, what an attacker's edits can do to the features (exactly for
one edit; as sound directions for a whole threat model), and from those builds monotone detectors no edit in the
threat model can evade. PE malware on EMBER2024 is the instance; the paper is `manuscript/*.tex` (ACM CCS format).
§5.3 compares our detectors with defenses *learned* from observed attacks. ERDALT (Gimenez et al., "Certifiably robust
malware detectors by design") is one of them: a learned square linear layer under a monotone network, trained so that
every observed perturbation vector maps to a nonnegative vector. The paper's claim about it: a defense learned from
observed attacks inherits their blind spots. That claim is only fair against an ERDALT trained as well as its authors
train it; a weak ERDALT invites the straw-man objection (review risk R19, `docs/reviews/2026-11-12-body/meta-review.md`).

## 2. What happened

The scale-up (`docs/scaleup-protocol.md`; tigris, RIT's aarch64 cluster, `SETUP.md`) trains nine ERDALT models:
`erdalt` (job 1020791_0) and the eight leave-one-out folds `erdalt-loo-<attack>` (1020792_1-8), one GH200 each, 310
epochs at ~5.8 min (~30 h). Logs: `artifacts/scaleup/4-detectors/logs/train-erdalt*.log` (one line per epoch:
`vl_roc`, `violations`, `l2`, `l3`). Outputs (at the end only): `artifacts/scaleup/4-detectors/erdalt*/`
(`metrics.json` with the training summary and history, predictions). The user chose to let them finish (session 82).

Every model collapsed the same way. Validation ROC-AUC peaked at epoch 0-1 (0.85-0.87), fell to ~0.69 by epoch 40,
and moved less than 0.01 after epoch 200. Violations (negative entries of the post-processed vectors) fell from ~1.3
million at epoch 0 to 16-40 at best; none reached Gimenez et al.'s criterion (< 5), so the code kept the epoch with the
fewest violations (`src/provexp/models/erdalt.py`, `train_erdalt`), an AUC ~0.70 model. The GBDTs on the same data
reach 0.998; the pilot's ERDALT reached 0.883 (Gimenez et al. report 93.0%).

**All nine finished (read in session 87; old material).** Selected epoch, validation AUC, violations; `met_criterion`
false for all: `erdalt` 275, 0.701, 39; leave-one-out folds content_shift 193, 0.746, 37; dos_extend 236, 0.710, 40;
format_exploit 191, 0.712, 34; gamma_api 233, 0.752, 29; gamma_sections 215, 0.690, 34; gamma_shift 212, 0.701, 27;
header_fields 212, 0.692, 28; padding 171, 0.723, 16. Their history has no `lr` or `l1` (those came with bbb487f).

**Session 85 (experiments track) changed ERDALT's training data.** The defenses' material held 894 broken outputs
(1.1%; secml-malware's shift writing in front of the MZ header, DOS extensions on files with e_lfanew < 0x40, lost
import tables); PV's collapse traced to them. Now one validity rule decides for the whole paper whether an output
counts (`provexp.attacks.validity`: pefile and LIEF both read it, neither loses a section or an import; b87fec6), the
shift is patched (5170936), and the material is being rebuilt (job 1141847, `logs/submit-20261118-s85.txt`). The nine
ERDALT models above were trained on the old material, so **every ERDALT model must be retrained on the new material**
(`4-detectors/material`, once 1141847 and its merge are done) whatever the diagnosis decides; the diagnosis runs may
use either material, but say which. ERDALT's attacks must also run under the new rule (the attack code has it).

## 3. What is ours and what is theirs (checked in session 82)

`src/provexp/models/erdalt.py` ports their `train_model.py` ("M_monotonic"), following the paper where the two differ.
**As theirs:** standardized inputs, the identity-initialized square linear layer without bias, hidden layers of 800
with ELU and dropout, Adam at 1e-4 with ReduceLROnPlateau on validation ROC-AUC (factor 0.5, patience 20), 310 epochs,
the loss w1 * BCE + w2 * sum(relu(-L delta)) + w3 * ||L off the diagonal|| with w1 0.5 -> 1, w2 0.5 -> 200, w3 0.5 -> 1
linearly over the epochs, the selection criterion (< 5 violations, then the best ROC-AUC). **Ours, deliberately:**
(1) batch size 256 instead of their 16 (at 16, 1.76 million training files are ~110,000 steps per epoch; set in run
133); (2) the output layer projected to be monotone too (their released code leaves it free, so their network is not
monotone; the paper's Proposition 3 needs it; `docs/upstream-issues.md` §8); (3) the epoch chosen on the validation
split, not the test split. **Different by scale, not by method:** the training split (1.76 million complete files,
against the pilot's 10% store) and the perturbation vectors (79,121 from the shared material, against the pilot's
3,183 outputs; Gimenez et al. had ~1,033 adversarial examples, all entering every step: "up to 152 batches of 16").

## 4. The leading hypothesis (from the code; not yet tested)

**Checked against their code in session 86** (`train_model.py`, fetched from GitHub): the penalty is
`torch.sum(relu(-L delta))` summed over the batches of a shuffled delta loader of batch size 16, stopping after
`count > 150`, so **at most 152 x 16 = 2,432 vectors per step**, a fresh draw each step; it is computed in train mode.
They had ~1,033 vectors, so all of theirs entered every step, but the cap is in the code. Our port puts all 79,121 in
every step, ~33x what their code would ever use. Drawing 2,432 per step is therefore **theirs, not a deviation**
(our docstring's "all of them enter every step" was true only of their data size). Their BCE is a mean over 16 files.

The two loss terms scale differently. BCE is a *mean* over a batch of 256 files; the violation penalty is a *sum* over
every negative entry of every perturbation vector, all 79,121 of them, at every step (`train_erdalt`, the `l2` loop).
With ~25x the pilot's vectors (~75x Gimenez et al.'s), the penalty dominates the loss from the first step (epoch 0:
`l2` ~1.9e4 against a BCE below 1), so training first satisfies the constraint by flattening the layer, losing the
discriminative directions; once AUC falls, ReduceLROnPlateau halves the learning rate every 20 epochs without
improvement, which may freeze the model where it collapsed. Other candidates: the batch size (256 vs 16: 16x fewer
penalty steps per epoch at 16x the data per step), the monotone output layer, the training split's size.

**What session 87 found in `erdalt`'s history weakens the "dominates throughout" form of this.** The penalty `l2` is
huge only at the start: 18,801 at epoch 0, 316 at epoch 1, 5.7 at epoch 2, 0.55 at epoch 5, 0.32 at epoch 20, 0.05 at
epoch 40, ~1e-7 by epoch 275. Validation AUC falls *after* the penalty is already small: 0.853 (epoch 1), 0.833 (2),
0.797 (5), 0.764 (10), 0.736 (20), 0.696 (40), then flat at ~0.70. (`l3`, the off-diagonal norm, 58 -> 31.) Two
readings remain, and run (b) separates both from the alternatives: **early damage** (the huge first-epoch penalty
flattens the layer and training never recovers) or **steady pressure** (the penalty's weight w2 keeps rising, ~26 by
epoch 40, so even a small penalty keeps squeezing the discriminative directions). Session 87 proposed to the user an
extra run (f): all vectors per step but the penalty weight scaled down ~10x (needs a small new option on
`train_erdalt`, e.g. `--penalty_scale`); add it only if the user agrees. Note also: violations stay in the tens while
`l2` is ~1e-7, so the remaining violations are tiny negative entries.

## 5. What this session does

1. **Check the session's resources** (header) and whether the material rebuild (1141847) and its merge are done
   (`squeue -u $USER` once; `artifacts/scaleup/4-detectors/material`). The finished models are read (§2).
2. **Diagnose with short runs, one change at a time** (state the hypothesis first; **locally in this interactive GPU
   job**, in the background with logs, one GPU per run; if the job has several GPUs, run several at once with
   `CUDA_VISIBLE_DEVICES` per run). `pipeline/4-detectors/train/train_erdalt.py` has the options (bbb487f; defaults keep the
   current training): `--train_subsample N` (a seeded random N training files), `--epochs 40 --schedule_epochs 310`
   (the first 40 epochs of the full weight ramp, so w2 reaches ~26 as in the collapse), `--deltas_per_step 2432`,
   `--batch_size 16`, `--free_output`, `--no_lr_scheduler`; the history now records `l1` and `lr` per epoch. Runs,
   each on `--train_subsample 200000` with validation in full: (a) the control (as at scale); (b) `--deltas_per_step
   2432`; (c) b with `--batch_size 16` (their exact configuration; batch 16 with all vectors per step is too slow);
   (d) `--free_output`; (e) `--no_lr_scheduler`. Estimate (from ~5.8 min per epoch at 1.76 M files, the penalty over
   all vectors dominating): ~40 s per epoch for (a), (d), (e), ~30 min each; time (b) and (c) from their first epochs.
   Hypothesis: (b) and (c) keep validation AUC near the early peak (0.85-0.87); (a), (d), (e) fall toward 0.70. First
   check that (a) reproduces the collapse on the subsample; if it does not, the subsample cannot diagnose it. The
   change that keeps validation AUC near the early peak names the cause. Use the new material if 1141847's merge is
   done, else the old; say which. Script the runs under
   `artifacts/scaleup/diag/erdalt/` (one `run.sh` that runs the variants; take the exact `train_erdalt.py` arguments
   for the main `erdalt` model, inputs included, from `pipeline/4-detectors/learned/run.sh` and add the options);
   put Python in files (a spawn pool started from a stdin script hangs), read each run's log a few minutes after it
   starts, and watch the runs to the end in this session (they are local, ~30 min each), comparing the per-epoch
   `vl_roc`, `l1`, `l2`, `lr` across variants.
3. **Lay the options out for the user** (the user decides protocol questions; Claude recommends): report ERDALT as
   specified with the collapse as a finding about the method at scale; retrain with the identified fix (a deviation
   to state in Appendix D); or retrain matching their scale (vectors per step). Keep R19's other asks in view: report
   the share of training and test perturbation vectors with L(delta) < 0; the donor-overlap control.
4. **Retrain only with the user's go-ahead, on the new material** (~30 h per model on 9 GPUs at the current setup;
   `pipeline/4-detectors/learned/run.sh` with `PART=erdalt`). Nine 30-h models do not fit one interactive job: ask
   the user whether to run them locally (one per visible GPU; the script does this) or as the array of 9 on GPU nodes
   (`pipeline/submit.sh`). The user's "run locally, not `sbatch`" was said for this session's work.
5. **Then ERDALT's attacks, which were held for this** (session 82; the other detectors' attacks run without it):
   `toolkit` with `DETECTORS=erdalt PARTS="main loo donors" LOO=erdalt` (10 jobs: its main row, eight folds, the
   donor control; `--array=0-9`); `adaptive` with `TAG=erdalt DETECTORS=erdalt ESCAPES=none EXPERT=0` (20 tasks,
   writes `none/shard-<k>-erdalt/`); MAB-Malware with `TAG=erdalt DETECTORS=erdalt SETTINGS=ours --array=0
   --cpus-per-task=1` (writes `ours-erdalt/`); then `6-results` (held too; `pipeline/6-results/run.sh`, which reads the
   tagged outputs and stops if a detector's outputs appear twice). Submit with plain `sbatch --export=ALL,...`, as in
   `logs/submit-*-no-erdalt.txt`.

## 6. Rules that apply

Explain plainly; a hypothesis before every run; report a failed check as such. Do not retrain or change the protocol
without the user. On tigris: head node light only (two CPUs); request what a job uses for most of its life; read each
job's startup line. In the interactive job, use only its allocation (cores and GPUs from `scontrol`, not `nproc`). Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline`); do not push.
At the end: update `docs/status.md` and PLAN.md, rewrite this prompt for the next ERDALT session (or archive it when
the track is done, `docs/archive/resume-prompt-erdalt-<date>-s<N>.md`, with its line in `docs/README.md`).
