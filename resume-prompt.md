# Resume: ProvExp, task 3-B

We're resuming ProvExp. Read CLAUDE.md, then docs/status.md ("Where we are", the 3-B row, "Next"), then
docs/shortcuts_plan.md in full (especially "Status note (2026-10-09)"), then PLAN.md's "Paper structure" and the 3-B
bullet under "Experiments".

## Where 3-B actually stands

3-B is the extrinsic application: **use the pullback to find spurious correlations the GBDT has learned (reliance on
label-correlated but non-malicious content: forgeable metadata, compiler/packaging artifacts), and possibly mitigate
them.** This is NOT PB1 (per-file faithfulness) and NOT 3-C (the separate YARA/capa pushforward application).

Little real progress was made last session; the framing churned badly. What exists is raw material, not a settled
experiment:
- `scripts/shortcuts.py` + `run/22_shortcuts.sh`: discovery. Pulls back TreeSHAP per file over the 2,000-file test
  set, groups the top-credited byte spans by content and top feature. Output in
  `artifacts/experiments/shortcuts/seed-0/{treeshap_interventional-benign,-malware}/patterns.parquet`. Surfaced e.g.
  the Delphi TimeDateStamp and certificate size (benign-pushing), capability strings (malware-pushing), and content
  behind hashed import/section features.
- `scripts/shortcuts_insert.py` + `run/23`: appending benign-pushing *string* content to held-out malware does NOT
  move the GBDT (correct: aggregate features, not byte-settable). A boundary result.
- `scripts/shortcuts_setfield.py` + `run/24`: setting the Delphi TimeDateStamp to its flagged value moves the GBDT
  toward benign +0.42 vs +0.12 random; DEBUG.Size +0.69. Shows those spurious correlations are causal and
  attacker-settable. BUT the two fields were hand-picked, not driven by the discovery output.
- All three have tests (`tests/test_shortcuts*.py`), pass ruff/mypy.

## What 3-B still needs (decide scope first, then execute as a fire-and-forget task)

1. A single, defensible "the pullback surfaces spurious correlations" result, driven by the discovery output rather
   than hand-picked fields: a short ranked list of surfaced spurious correlations, each with its content, prevalence
   by label, model reliance, and (for the settable ones) the run-24-style causal/exploitability number.
2. Baselines without P: data-mined label-skewed byte patterns (chi2/IG on a training sample) and occlusion as the
   cost baseline (cite PB1). Needs a training-set sample from the 1.3 TB SimpleDB (hand me the command; I run long
   jobs).
3. Optional mitigation half: remove a surfaced correlation (neutralize the carrying features via each feature's share
   of the artifact's bytes, Pᵀ1_S, or retrain with the artifact randomized) and show reliance drops without hurting
   clean accuracy. Internal to 3-B.

## How to work (I was not happy last session)

Decide the scope of 3-B with me in ONE exchange, then execute without turning it into a stream of micro-questions or
reframings. Keep docs short. Don't reframe the claim (see memory [[dont-reframe-research-claims]], [[3b-framing]]).
Long runs: smoke-test, then hand me the exact command. Then let's take stock and move to 3-C or 3-A.
