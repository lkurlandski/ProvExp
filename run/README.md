# run/

The commands that produced everything in `artifacts/`, one script per step, in the order they were run. Each writes
its log to `artifacts/logs/`, so a step's log is the record that it ran and with which arguments.

Conventions, which matter for reproducibility:

- `PYTHONHASHSEED=0` for anything that extracts features (thrember's warning features depend on the hash seed).
- `OMP_NUM_THREADS=1` for the multiprocessing scripts, so the workers do not fight over cores; **not** for
  `train_classic.py`, where LightGBM needs every core (about 3 minutes instead of about 45).
- Scripts take their defaults from `scripts/*.py`; only the arguments that differ from a default are written out, so
  a diff against the script shows what was chosen.
- Long steps (hours) are meant to be run in `tmux`. The runtimes in the comments are what they actually took on this
  machine (64 cores).

Reconstructed on 2026-10-08 from `artifacts/logs/` and the reports in `artifacts/`; steps 1-9 ran before that date,
so their scripts record the arguments their logs and reports show, not a transcript of the shell.
