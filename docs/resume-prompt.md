# Resume: ProvExp (2026-10-14) — the 500-file scale-up results, then writing

Read `CLAUDE.md`, then `docs/status.md` ("Where we are", "Next", and the 2026-10-13 decisions). Explain in plain
language; no dense shorthand. Ask before changing what a claim is for.

## Where things stand

- **Manuscript** (`manuscript/`, ACM CCS 2027 target, `acmart` `sigconf`; `make`, `make check`): restructured into paper
  form on 2026-10-13; body ends on p. 11 of 12. Sections: Introduction / Background and Related Work / Transferring
  Explanations with Provenance (preliminaries, P, pullback and pushforward, constructing P) / Pulling Back to the
  Bytes (faithfulness, planted trigger, comparing two detectors) / Pushing Forward to the Features (faithfulness,
  ground truth for explainers, auditing a raw-byte detector) / Discussion / Conclusion. The statistics of P, round
  trips, and CP were cut (archived in `manuscript/archive/`). The user has not read the restructured text yet.
- **AU was corrected (runs 47-49, `docs/experiments/audit.md`):** run 46's 22.5% counted undetected files, dropped
  broken random draws, and reused the confirmation files. With loader-safe changes only, on 902 fresh detected malware:
  the pushforward's fields evade **12.4%** vs. **6.0%** for as many other loader-ignored fields outside the DOS region
  (p = 3e-12); surrogate 10.4%; union 18.4%. The manuscript still shows the old numbers.
- **The seed-0 scale-up to 500 files** (250/label, superset of the pilot's 100;
  `artifacts/explanation_set/ts-scaleup500-seed0.parquet`) is being run by the user: `run/50`-`55` (KernelSHAP; PB1
  full baselines with GBDT + MLP; operator variants; PF1 + resolution + black-box P; CM incl. triage at 100/cell; both
  triggers at 250 files). About 20-24 h.
- **Speed:** string features 2.1x faster, bit-identical. Two deferred ideas in `docs/design.md`, "Deferred
  optimizations" (reuse the parse in `verify`; the remaining extractor hotspots); not now.

## Next steps (in order)

1. **Check the runs** (ask the user whether they finished): read the ends of `artifacts/logs/*scaleup*` and the tables
   in `artifacts/reports/*scaleup500*.md`, `cm_tables-scaleup500.md`, `cp_blackbox-*scaleup500.md`; compare every
   number the manuscript reports against the pilot; flag what moved and why; update the experiment docs
   (`docs/experiments/pb1.md`, `pf1.md`, `trigger.md`, `cm.md`).
2. **Update the manuscript's numbers:** AU's realizable results (lead with the pushforward; union second; threat model
   says only loader-ignored or valid-value changes); then the 500-file numbers in Sections 4-5 and the abstract/intro.
3. **Section-level writing** with the user, once they have read the draft.

## Working rules from this session

- Realistic perturbations only for anything framed as an attack (CCS standard; user).
- Limitations light and confident; no "Threats to Validity".
- Optimizations: smallest change for the big win; never patch third-party libraries or rewrite the pipeline.
- Long jobs: smoke-test, then hand the user numbered `run/` scripts (max 16 CPUs, GPUs 2 and 3).
