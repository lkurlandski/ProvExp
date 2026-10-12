# Resume: ProvExp, 3-C revised's go/no-go (2026-10-13)

We're resuming ProvExp. Read `CLAUDE.md`, then `docs/status.md` ("Next", and the 2026-10-12 "latest" session and
decisions), then `docs/audit_plan.md` (3-C revised: the mock, the objections, and the go/no-go criterion).

## Where things stand

- Framework and intrinsic evaluation done at pilot scale; 3-A (the pullback's application) done and written up.
- Yesterday we stepped back: the pullback/pushforward symmetry is the novelty, so the pushforward needs its own
  application. **3-C revised: auditing MalConv for shortcuts through the pushforward.** MalConv's per-file IG is pushed
  into the EMBER features, which every file shares, so its reliance can be aggregated over the 2,000-file explanation
  set; candidates are confirmed by a transplant scored by MalConv. The competitor is a surrogate GBDT trained on
  MalConv's scores (fidelity R^2 0.95).
- I started runs 38-41 (`run/`). 38 is done; 39 (IG, 2 GPUs) was running; 40 and 41 follow.

## What to do

1. Check runs 39-41 (logs: `artifacts/logs/audit_*-seed0*.log`); sync `run/39`'s comments (I ran 2 parts on GPUs 0-1)
   and record the runtimes in `run/38`-`41`.
2. Read the go/no-go **as written** in `docs/audit_plan.md` and tell me plainly: go or no-go, and why. Also say how much
   of MalConv's credit fell on aggregates and whether the confirmed shortcuts lie only in the DOS header.
3. Then we decide the next step together (go: plan the experiment proper; no-go: a short post-mortem).

Explain in plain language; no dense shorthand.
