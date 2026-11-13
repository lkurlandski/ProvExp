# Knobs of the simulated review (sourced by run_review.sh). Every value can also be overridden from the environment
# for one run, e.g. `REVIEWER_EFFORT=xhigh docs/reviews/process/run_review.sh`.

# Name of this run: the output folder docs/reviews/<TAG>/ and the scratch folder <WORK_ROOT>/<TAG>/.
TAG="${TAG:-$(date +%F)-body}"

# The venue the reviewers sit on, and the scoring scale they use.
VENUE="${VENUE:-ACM CCS (reviewers who also serve on IEEE S&P, USENIX Security and NDSS)}"
SCALE="${SCALE:-Reject / Weak reject / Weak accept / Accept}"

# Reviewers: one persona file per reviewer in reviewers/, named <ID>-<anything>.md. Remove an ID to drop a reviewer;
# add a file and its ID to add one.
REVIEWERS="${REVIEWERS:-A B C D}"

# Model and effort of every reviewer (claude --model / --effort). Per-reviewer override: MODEL_<ID>, EFFORT_<ID>,
# e.g. MODEL_C=claude-fable-5-2. Effort levels: low, medium, high, xhigh, max.
REVIEWER_MODEL="${REVIEWER_MODEL:-claude-opus-5-5}"
REVIEWER_EFFORT="${REVIEWER_EFFORT:-high}"

# The meta-reviewer: merges the reviews, checks their premises against the project, works through checklist.md.
META_MODEL="${META_MODEL:-claude-opus-5-5}"
META_EFFORT="${META_EFFORT:-xhigh}"

# The rebuttal (run_rebuttal.sh), run after the meta-review: first ONE triage agent over the whole register
# (TRIAGE_EFFORT), then, for the groups the user picks from the triage (REBUTTAL_GROUPS="trust baselines"), one
# drafting agent per group, REBUTTAL_PARALLEL at a time. REBUTTAL=0 stops run_review.sh after the meta-review.
# REBUTTAL_SKIP: items decided before the run (e.g. "R7 R1"), passed to the triage as decided.
REBUTTAL="${REBUTTAL:-1}"
REBUTTAL_MODEL="${REBUTTAL_MODEL:-claude-opus-5-5}"
TRIAGE_EFFORT="${TRIAGE_EFFORT:-high}"
REBUTTAL_EFFORT="${REBUTTAL_EFFORT:-high}"
REBUTTAL_PARALLEL="${REBUTTAL_PARALLEL:-1}"
REBUTTAL_SKIP="${REBUTTAL_SKIP:-}"
REBUTTAL_GROUPS="${REBUTTAL_GROUPS:-}"

# Whether reviewers may search the web for related work (1) or only use papers/ (0).
REVIEWER_WEB="${REVIEWER_WEB:-1}"

# Optional spending cap per agent in USD (claude --max-budget-usd); empty means no cap.
MAX_BUDGET_USD="${MAX_BUDGET_USD:-}"

# Reviewers run from a folder outside the repository, so they see no CLAUDE.md, memory or project docs: only the PDF,
# the note to reviewers and a copy of papers/.
WORK_ROOT="${WORK_ROOT:-/scratch/lk3591/provexp/reviews}"

# Steps to run: all, reviewers (stop after the four reviews), meta (the meta-review on existing reviews, then the
# rebuttal triage if REBUTTAL=1), rebuttal (only the rebuttal: the triage, or the drafts of REBUTTAL_GROUPS).
STEPS="${STEPS:-all}"

# 1: print the composed prompts and commands, run nothing.
DRY_RUN="${DRY_RUN:-0}"
