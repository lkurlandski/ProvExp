# Resume: ERDALT's diagnosis, round 2 (4 short runs, quantile input scale); then decide the retrain with the user

> **Superseded (session 94):** the ERDALT track is folded into `docs/resume-prompt-experiments.md`, which covers
> every experiment. Round 2 was read and the retrain submitted (`docs/erdalt-diagnosis-plan.md`, "Session 94").
> Archive this prompt once the retrain is verified.

Written in session 91 (2026-11-19, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading
first. One of three tracks: this one (ERDALT), `docs/resume-prompt-experiments.md` (the rest of the scale-up on the
cluster), `docs/resume-prompt.md` (general work and the index of the tracks). The diagnosis record:
`docs/erdalt-diagnosis-plan.md` (sections "Session 90" and "Session 91").

## 1. The project and ERDALT's place in it

ProvExp computes, from an instrumented feature extractor, what an attacker's edits can do to the features, and from
that builds monotone detectors no edit in the threat model can evade. PE malware on EMBER2024 is the instance; the
paper is `manuscript/*.tex` (ACM CCS format). §5.3 compares our detectors with defenses *learned* from observed
attacks. ERDALT (Gimenez et al., "Certifiably robust malware detectors by design") is one of them: a learned square
linear layer L under a monotone network, trained so that every observed perturbation vector delta (features after an
attack minus before) maps to a nonnegative L delta; loss w1 BCE + w2 sum(relu(-L delta)) + w3 ||L off-diagonal||, the
weights ramped linearly (w2: 0.5 -> 200). The epoch is chosen by their criterion (< 5 negative entries of L delta over
all vectors, "violations", then the best validation ROC-AUC; else the fewest violations). The paper's claim: a defense
learned from observed attacks inherits their blind spots. That is only fair against an ERDALT trained as well as its
authors train it (review risk R19, `docs/reviews/2026-11-12-body/meta-review.md`, which also asks for the share of
training and test vectors with L delta < 0, and a donor-overlap control). PV (a monotone GBDT on the 1,359 features no
vector lowers; a zero-violation ERDALT in disguise) reaches validation 0.924 (test 0.930) on the new material.

## 2. Where things stand

**The collapse.** Ported literally, ERDALT falls from validation AUC ~0.84 to ~0.73 as violations fall, on the old and
the new material; `erdalt`'s full run (1169769_0) reached epoch 192 at 0.728 with 30-120 violations, criterion never
met, and was cancelled by the user (2026-11-19). Their setup (paper §5, `train_model.py` at 0b6f222,
`papers/gimenez2025certifiably.pdf`): 24,000 training files, EMBER features, 1,033 adversarial vectors in all, batch 16,
310 epochs (a script constant), std-standardized inputs. Ours: 1.76M files, batch 256, 78,715 vectors.

**Round 1 of the diagnosis (1179478_[0-6], read in session 91).** 15 epochs of the 310-epoch schedule unless stated;
control `erdalt`: 0.843 at 1.39M violations, 0.807 at 7.4k, 0.770 at 4.2k.
- pscale (their penalty mass per step, w2 x 1033/78715): 0.878 -> 0.824 at 111k; better than the control at matched
  epochs (+0.03-0.09), about even at matched violations: slows the fall, does not stop it.
- n1033 (their 1,033 vectors): 0.917 -> 0.824 at 87 own violations; **~11.0M violated entries over all 78,715 vectors**.
- fixed (L frozen at PV's mask, std scale): 0.55 -> 0.40. The network cannot use PV's features under the std scale.
- short (20-epoch schedule) 0.744, cap 0.733, pv-init 0.749: like the control.
- **robust (quantile scale: per feature max(std, 0.9999 quantile of |x - mean|)): 0.905 -> 0.938 at 7.5k violations,
  test 0.940**; temperature 67 instead of 400-10,000. The only run that holds.
Reading: the cause is chiefly the **input scale**, a constant of their setup sized to 24,000 files; under the std scale
on 1.76M heavy-tailed files a few files' extreme values dominate the monotone network. The quantile scale is linear and
per feature, so monotonicity, L's meaning and their Proposition 3 are untouched. Not checked yet: that the std on a
24,000-file sample of ours behaves like theirs.

**The user's preferences (session 91):** keep their per-step penalty mass (pscale's weight) rather than the 76x
heavier literal one, and smooth the weight schedule per step. `train_erdalt(schedule_per_step=True)` /
`--schedule_per_step` (`loss_weights` in `src/provexp/models/erdalt.py`; 1b663c2): the weights interpolate linearly
within each epoch; same values at whole epochs, same endpoints, about half an epoch's increment ahead on average.

**Round 2, submitted by the user** (2026-11-19; same script `artifacts/scaleup/diag/erdalt/gpu/run.sh`, `--array=7-10`,
one GH200, 2 cores, 128G, 3 h; logs `artifacts/scaleup/diag/erdalt/gpu/logs/<variant>.log`, job outputs
`logs/erdalt-diag_<job>_<task>.out`; the job ID is in `squeue`/`sacct --name=erdalt-diag`). All with the quantile scale:
- 7 robust-short: the whole schedule in 20 epochs, per step (~2 h): is the criterion met, at what AUC?
- 8 robust-fixed: L frozen at PV's mask (~45 min): the monotone network's ceiling at zero violations.
- 9 robust-n1033: their 1,033 vectors (~15 min; logs `violations_all`): violations of the unseen vectors.
- 10 robust-pscale: as 7 with their penalty mass per step (~2 h): 7 and 10 differ only in w2.
Hypothesis: robust-short reaches the criterion or near it (< 100) at validation ~0.90-0.93; robust-fixed ~0.90-0.92;
robust-n1033 keeps ~0.93 but violates millions of entries of the unseen vectors; robust-pscale keeps a higher AUC than
robust-short but ends with more violations (its w2 only reaches ~2.6), possibly missing the criterion: a schedule
question, not a verdict on the weight.

## 3. What this session does

1. **Check round 2** (`squeue -u $USER`; `sacct --name=erdalt-diag -S 2026-11-19
   --format=JobID,State,Elapsed,MaxRSS,AllocCPUS,TotalCPU`). Read each task's startup line and its log's epochs; for
   robust-n1033 also `violations_all`. Right-size the header from sacct. Partial runs: read what is there.
2. **Read them** against the control, round 1's robust and PV's 0.924, at matched violations as well as epochs.
3. **Decide the retrain with the user** (Claude recommends). If robust-short or robust-pscale meets the criterion (or
   comes close) at ~0.9: retrain `erdalt` and the eight folds with the quantile scale, their per-step penalty mass,
   the per-step schedule, and a schedule length sized to our data (robust-pscale's course tells whether 20 epochs
   suffice for its lighter weight, or a longer schedule is needed; the user leans to their penalty mass); each
   rescaling stated against their setup in Appendix D. The retrain script is `pipeline/4-detectors/` (the `learned`
   step's ERDALT tasks; add the new flags there, with the user). If no variant gets near the criterion with a good AUC,
   report ERDALT as specified with the diagnosis as evidence that the remaining gap is the method.
4. **When the final nine are done:** R19's asks (share of training and test vectors with L delta < 0; donor-overlap
   control), then ERDALT's attacks, held for this (the other detectors' attacks run without it): `toolkit` with
   `DETECTORS=erdalt PARTS="main loo donors" LOO=erdalt` (`--array=0-9`); `adaptive` with `TAG=erdalt
   DETECTORS=erdalt ESCAPES=none EXPERT=0` (20 tasks, writes `none/shard-<k>-erdalt/`); MAB-Malware with
   `TAG=erdalt DETECTORS=erdalt SETTINGS=ours --array=0 --cpus-per-task=1` (writes `ours-erdalt/`); then `6-results`
   (`pipeline/6-results/run.sh`, which stops if a detector's outputs appear twice). Submit with plain
   `sbatch --export=ALL,...`, as in `logs/submit-*-no-erdalt.txt`. Check first with the experiments track that the
   other detectors' reruns on the new material are done.

## 4. Rules that apply

**The lesson of this track (user, session 90; in CLAUDE.md and the global memory):** a method from another paper is
ported for its effect, not its letter. Tabulate their setup against ours and rescale what the differences touch
before the first run, and before diagnosing a weak result. Whatever the retrain uses, state each rescaling against
their setup in Appendix D.

Think a run through before starting it: what it is compared with, whether its setup can reproduce the effect under
study, and what each outcome would mean; a hypothesis before every run; check a new analysis on a planted case before
trusting an empty answer (session 89's LP); report a failed check as such. Explain plainly. Do not retrain or change
the protocol without the user. On tigris: head node light only (two CPUs); request what a job uses for most of its
life; read each job's startup line; in an interactive job use only its allocation. Kill by PID, not `pkill -f`.
Commit to `main` in logical pieces (ruff and strict mypy on `src tests pipeline`); do not push. At the end: update
`docs/status.md` and PLAN.md, rewrite this prompt (or archive it when the track is done,
`docs/archive/resume-prompt-erdalt-<date>-s<N>.md`, with its line in `docs/README.md`).
