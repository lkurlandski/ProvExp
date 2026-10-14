# Resume: ProvExp (2026-10-14, after lunch) — B9 result, then the revision plan

Read `CLAUDE.md`, then `docs/status.md` (top summary, "Where we are", "Next"), `docs/review-2026-10-14.md` (the
self-review), and `docs/revision-plan.md` (what's done and what's next). Explain in plain language; no dense shorthand.
Ask before changing what a claim is for. Page limit and exact numbers do not matter at this drafting stage.

## What happened this morning

- **Self-review + revision plan.** A CCS-reviewer-style review (`docs/review-2026-10-14.md`) found the paper's main
  risks (W2/W4 "byte resolution out of reach / win by construction", W5 pushforward never tested on MalConv, W6 the
  applications' security value, W1 thin novelty, W7 generality on one extractor). The plan (`docs/revision-plan.md`)
  attacks them; blocks A (writing) and B7 (oracle) are done, B9 is running.
- **Manuscript brought up to date:** block-A writing fixes (cost accounting, novelty case in Section 3, "format
  knowledge in three places", CM wording, related-work contrast vs. parser-based saliency mapping); MLP and Figure 1
  cut; AU's realizable numbers in (12.4% vs. 6.0%, loader-safe threat model). Build is clean (`make`, `make check`).
- **Field-occlusion oracle (run 56) — a strong result, already in the paper.** A parser-based upper bound that knows
  the read set (124 extractions/file) reaches only gain 0.91; the byte-level pullback beats it 88/100 (p~1e-15).
  In Table 1 and 4.1. Recorded in `docs/experiments/pb1.md`.
- **Deferred experiments drafted as synthetic blue placeholders** (`\synthetic{}` macro, dark blue): pushforward on
  MalConv (M1), the mitigation (M3, with a blue table), the Android extractor. Predicted numbers in
  `docs/experiments/mocks.md`. Each blue block names the run that replaces it.

## The one thing to check first: B9 (run 57)

The user ran `cm_triage_evasion.py` on **200 candidate malware, GPU 1** (edited from run/57's defaults). It tests
whether the disagreement triage separates an **attack-caused** disagreement from an **organic** one:
- organic = malware MalConv misses on its own; evasion = malware both detect, with the shared set S scrambled
  loader-safe until MalConv flips while the GBDT holds. Same blind/oppose/agree split (A = GBDT, B = MalConv) on both.
- **Hypothesis:** the evasion population carries more of the GBDT's evidence in **oppose** than the organic one.

When it is done (ask the user, or read the end of `artifacts/logs/cm-triage-evasion-seed0.log` and
`artifacts/experiments/cm_triage_evasion/seed-0/files.parquet`):
1. Read the blind/oppose/agree table and the evasion-vs-organic p-values (Mann-Whitney on the per-file oppose share).
2. **If oppose separates them** (evasion clearly higher, p small): the triage label is a defender's *decision*. Write
   it into Section 4.3 (the comparison application) as the operational reading W6 asked for; record in
   `docs/experiments/cm.md`.
3. **If it does not:** fall back, in this order (user's choice): (a) reframe the readout — test only whether the
   triage *separates* the populations at all (any category), (b) reconsider the experiment and argue the decision from
   the existing triage (MalConv-only+blind -> add a feature; GBDT-only+oppose -> investigate). Either way, update 4.3.
   Caveat: the 16-file smoke test showed no separation, but that N and the reduced IG steps mean nothing; read the
   real pilot.

## Then (revision-plan order)

- **Remaining block C (deferred, synthetic placeholders stand in):** M1 (pushforward on MalConv) and M3 (mitigation)
  need re-scoring/retraining MalConv — not yet. The **Android second extractor** (item 12) is the biggest lift for the
  generality claim (W7): AndroZoo APKs + a Drebin-style extractor instrumented for P; run the 4.1 faithfulness test.
- **Section-level writing** with the user once they read the restructured draft (they have not yet).
- **Scale-up** to 2,000 files / 3 seeds (10K on the cluster) once the designs settle — the last step before submission.

## Working rules this session

- Realistic perturbations only for anything framed as an attack. No sandboxing samples (memory `no-sandbox-execution`).
- Mock the result first (synthetic blue placeholders) before building MalConv/retraining experiments.
- Long jobs: smoke-test, then hand the user a numbered `run/` script (GPUs the user picks; they used GPU 1 for B9).
- Commit attribution line is currently `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
