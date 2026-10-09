We're resuming the ProvExp project. Read CLAUDE.md, then docs/status.md (especially "Where we are", "Waiting on the
user: run 21", and "Next (for Claude), on resume"), then PLAN.md's "Thesis and claims" and "Experiments" sections.

I ran run/21_pb1_tiebreak.sh: PB1's curves recomputed with seeded random tie-breaks instead of ties broken by position
in the file, reusing pass 1 from run 17. Check that it finished cleanly, then read the tables
(artifacts/reports/pb1_tables-baselines-ties.md) against the pre-fix tables (artifacts/reports/pb1_tables-baselines.md)
and the reading fixed in advance in docs/pb1_baselines.md ("Tie-break re-run"). The key question is whether occlusion
still saturates at about 1.10 at 1,024-4,096 windows and the byte-level pullback stays well ahead. Write the results
into docs/pb1_pilot.md, PLAN.md (PB1), and the manuscript's PB1 baselines paragraph (removing the "pending" notes),
and update docs/status.md.

After that, let's take stock together: are the four claims and the contributions supported at pilot scale, and is
anything still missing before we move on to CM (GBDT vs. MalConv)?
