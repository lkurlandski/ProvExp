# 6-results: tables from stored outputs

No attack or training here; each script reads the outputs of stages 1-5.

- `toolkit_split.py`: evasion per toolkit attack (Appendix D, Table 11).
- `coverage.py`: which lowerable features the toolkit's outputs and our own edits lowered, by source (§5.3).
- `pv_hole.py`, `erdalt_hole.py`: the features PV and ERDALT leave open, and the files evaded through them (§5.3).
- `trial_audit.py`: replays each evasion of the trial detector and names the features carrying it (§5.3).
- To add at the scale-up (PLAN.md step 3): the share of all attacked malware still detected after each attack (1% and
  0.1% FPR), coverage on modeled features only, the monotone detector's split-gain share on features no edit moves, the
  detected malware's margins.
