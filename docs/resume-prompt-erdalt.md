# Resume: ERDALT's GPU diagnosis (7 short runs); read them against PV's 0.92 and decide the retrain

Written in session 90 (2026-11-18, tigris). Self-contained: only `CLAUDE.md` (loaded automatically) needs reading
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

**The collapse, twice.** The nine old-material models fell from validation AUC ~0.85 (epoch 1) to ~0.70 as violations
fell, criterion never met (moved to `artifacts/scaleup/superseded-s85/4-detectors/erdalt*`). Retrained on the new
material (`erdalt`, 1169769_0, one GH200; log `artifacts/scaleup/4-detectors/logs/train-erdalt.log`; job output
`logs/learned-erdalt_1169769_0.out`), it falls the same way: epoch 0: 0.843, 1.39M violations; 1: 0.846, 210k; 2:
0.831, 17.9k; 3: 0.807, 7.4k; 5: 0.782, 5.9k; 7: 0.770, 4.2k (old: 5: 0.797, 4.8k; 10: 0.764, 3.7k). Session 89's
hypothesis (the broken outputs caused it) is refuted. The eight folds (1169770) were cancelled; `erdalt` runs to its
end (~30 h from 2026-11-18 14:07; 95 GB of its 128G) for its full course and whether the criterion is ever met.

**The benchmark.** PV (a monotone GBDT on the 1,359 features no vector lowers) is a zero-violation ERDALT in disguise
(L = identity with zeros on the 1,209 lowered features) and reaches validation 0.924 (test 0.930) on the new material.
So a good zero-violation model exists; ERDALT does not find it. The cone of the vectors is pointed (session 89's LP),
so nothing forces L to discard directions.

**Their setup, reread in session 90** (paper §5; `train_model.py` at commit 0b6f222 of
github.com/PFGimenez/certifiably-robust-malware-detectors-by-design; the PDF is `papers/gimenez2025certifiably.pdf`):
24,000 training files, **1,033 adversarial examples in all** (not per method, as our literature notes had it), batch
16 (~1,500 steps per epoch, ~465k steps in all), `num_epochs = 310` a script constant, each step's penalty over all
1,033 vectors. Ours: 1.76M files at batch 256 (~6,900 steps per epoch, ~2.1M in all), the penalty over all 78,715
vectors against a batch-mean BCE: **~76x their penalty mass per step**, and a weight ramp over 4.6x their steps. Their
own Table 2 has ERDALT at 0.930, below PV + RF at 0.952; their monotone network alone 0.874. The user's question:
is ERDALT's poor showing a bug in the port or a weak method? The diagnosis decides.

**The diagnosis** (approved by the user; `docs/erdalt-diagnosis-plan.md`, "Session 90", has the table, hypothesis
and readings): `artifacts/scaleup/diag/erdalt/gpu/run.sh`, array 0-6, one GH200, 4 cores, 128G, 3 h each; new
material, full training split, 15 epochs of the 310-epoch schedule unless stated; logs
`artifacts/scaleup/diag/erdalt/gpu/logs/<variant>.log`, job outputs `logs/erdalt-diag_<job>_<task>.out`.
0 fixed (L frozen at PV's mask), 1 pv-init (L starts there, trains), 2 n1033 (their vector count; also logs
`violations_all` over all 78,715), 3 pscale (all vectors, w2 x 1033/78715: their mass), 4 cap (2,432 per step),
5 short (the whole schedule in 20 epochs), 6 robust (quantile input scale). The control is `erdalt`'s own first 15
epochs. Code: 3249398 (options in `train_erdalt`, tested; smoke-tested on a 20,000-file slice).

## 3. What this session does

1. **Check the array** (`squeue -u $USER`; `sacct -j <job> --format=JobID,State,Elapsed,MaxRSS,AllocCPUS,TotalCPU`).
   If it has not run, say so. Read each task's startup line and its log's epochs; right-size the header from sacct.
2. **Read the seven against the control and PV's 0.92**, at matched violation counts (the curve of AUC against
   violations), not only at matched epochs; for n1033 also `violations_all`. Hypothesis (session 90): the penalty
   weight is the main cause, so pscale and n1033 stay near ~0.9 well above the control, cap in between; fixed reaches
   ~0.88-0.92; n1033 violates many unseen vectors. The readings and what each implies are in the plan document.
3. **Decide with the user** (Claude recommends): (a) the port was unfaithful in effect: retrain `erdalt` and the
   eight folds with their per-step penalty mass (and a schedule sized to our data), stated in Appendix D; or (b) the
   method: report ERDALT as specified, with the diagnosis as evidence that it is not our port. Either way, read
   `erdalt`'s full course when it ends (selected epoch, `met_criterion` in its `metrics.json`).
4. **When the final nine are done:** R19's asks (share of training and test vectors with L delta < 0; donor-overlap
   control), then ERDALT's attacks, held for this (the other detectors' attacks run without it): `toolkit` with
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
