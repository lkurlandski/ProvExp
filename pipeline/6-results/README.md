# 6-results: tables from stored outputs

No attack or training here; each script reads the outputs of stages 1-5.

- `toolkit_split.py`: evasion per toolkit attack (Appendix D, Table 11).
- `coverage.py`: which lowerable features the toolkit's outputs and our own edits lowered, by source (§5.3).
- `pv_hole.py`, `erdalt_hole.py`: the features PV and ERDALT leave open, and the files evaded through them (§5.3).
- `trial_audit.py`: replays each evasion of the trial detector and names the features carrying it (§5.3).
- `scaleup_tables.py`: per detector, detection at the validation thresholds (1% and 0.1% FPR), the share of all the
  evaluation set's malware still detected after each attack and after any (escapes apart), the detected malware within
  the hand table's 1.57-logit drop (R3), the monotone detectors' gain share on features no edit moves (R15).
- `run.sh`: `scaleup_tables.py`, `coverage.py` (the `modeled` class: without the warnings, R12) and `erdalt_hole.py`
  on the scale-up's outputs.
