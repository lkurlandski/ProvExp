#!/usr/bin/env bash
# The rebuttal of a meta-review's risk register, in two steps (redesigned 2026-11-13: the first design, one full agent
# per item, spent about $2-3 of tokens per item and ran out of the session limit after four):
#   1. triage: ONE agent reads the register, the reviews and PLAN.md once and gives every item a verdict (decided,
#      dismiss, cheap fix, investigate), grouping the items to investigate with their deciding questions
#      (triage-brief.md -> docs/reviews/<TAG>/rebuttal/triage.md). The user then takes the decisions on that table.
#   2. drafts: only for the groups the user picks, one agent per group, reading a dossier cut out by dossier.py
#      instead of the whole review, checking only the group's deciding questions (rebuttal-brief.md ->
#      rebuttal/<group>.md).
# Knobs in config.sh; procedure in docs/reviews/review-prompt.md; the decision sessions in
# docs/reviews/rebuttal-prompt.md.
#
# Usage (from the repository root):
#   TAG=2026-11-12-body REBUTTAL_SKIP="R7 R1 R6 R17" docs/reviews/process/run_rebuttal.sh   # step 1 (triage)
#   TAG=2026-11-12-body REBUTTAL_GROUPS="trust baselines" docs/reviews/process/run_rebuttal.sh  # step 2
#   DRY_RUN=1 ...                                                                          # show prompts only
set -euo pipefail

REPO="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
PROC="$REPO/docs/reviews/process"
# shellcheck source=config.sh
source "$PROC/config.sh"

OUT="$REPO/docs/reviews/$TAG"
DRAFTS="$OUT/rebuttal"
COMMIT="$(git -C "$REPO" rev-parse --short HEAD)"

if [[ ! -f "$OUT/meta-review.md" ]]; then
    echo "docs/reviews/$TAG/meta-review.md does not exist: run the meta-review first" >&2
    exit 1
fi
if [[ "$DRY_RUN" != "1" ]]; then mkdir -p "$DRAFTS"; fi

run_agent() {
    # Run one headless agent: $1 name, $2 prompt, $3 effort, $4 log file. Inside the repository (it needs the
    # manuscript, PLAN.md and, for drafts, the code and outputs).
    local name="$1" prompt="$2" effort="$3" log="$4"
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "----- prompt for $name (effort $effort) -----"; echo "$prompt"; echo "-----"
        return 0
    fi
    # shellcheck disable=SC2046
    (cd "$REPO" && claude -p "$prompt" \
        --model "$REBUTTAL_MODEL" \
        --effort "$effort" \
        --permission-mode acceptEdits \
        --allowedTools Read Write Glob Grep "Bash(pdftotext:*)" "Bash(git log:*)" "Bash(git show:*)" \
            "Bash(grep:*)" "Bash(sed:*)" "Bash(ls:*)" "Bash(env/bin/python:*)" \
        --name "$name" \
        $(if [[ -n "$MAX_BUDGET_USD" ]]; then echo "--max-budget-usd $MAX_BUDGET_USD"; fi) \
        > "$log" 2>&1) || echo "$name: the agent exited with an error (see $log)" >&2
}

fill() {
    # The brief $1 with the placeholders filled; extra pairs KEY=VALUE in $2...
    local s
    s="$(cat "$1")"; shift
    s="${s//\{\{TAG\}\}/"$TAG"}"
    s="${s//\{\{OUT\}\}/"docs/reviews/$TAG"}"
    s="${s//\{\{COMMIT\}\}/"$COMMIT"}"
    for kv in "$@"; do s="${s//\{\{${kv%%=*}\}\}/"${kv#*=}"}"; done
    printf '%s' "$s"
}

################################################################################
# Step 1: the triage (when no REBUTTAL_GROUPS are given)
################################################################################

if [[ -z "$REBUTTAL_GROUPS" ]]; then
    if [[ -f "$DRAFTS/triage.md" ]]; then
        echo "rebuttal/triage.md exists: take the decisions on it (docs/reviews/rebuttal-prompt.md), then run the"
        echo "groups to investigate with REBUTTAL_GROUPS=\"...\". Delete triage.md to triage again."
        sed -n 's/^GROUP \([a-z0-9-]*\): \(.*\)$/  group \1: \2/p' "$DRAFTS/triage.md"
        exit 0
    fi
    echo "Triage of the register ($REBUTTAL_MODEL, effort $TRIAGE_EFFORT); log: docs/reviews/$TAG/rebuttal/triage.log"
    run_agent "rebuttal-$TAG-triage" \
        "$(fill "$PROC/triage-brief.md" "DECIDED=${REBUTTAL_SKIP:-none}")" \
        "$TRIAGE_EFFORT" "$DRAFTS/triage.log"
    if [[ "$DRY_RUN" != "1" && ! -f "$DRAFTS/triage.md" ]]; then echo "No triage written (see rebuttal/triage.log)" >&2; exit 1; fi
    exit 0
fi

################################################################################
# Step 2: the drafts of the chosen groups, REBUTTAL_PARALLEL at a time
################################################################################

if [[ ! -f "$DRAFTS/triage.md" ]]; then
    echo "No rebuttal/triage.md: run the triage first (without REBUTTAL_GROUPS)" >&2
    exit 1
fi

running=0
for group in $REBUTTAL_GROUPS; do
    items="$(sed -n "s/^GROUP $group: *//p" "$DRAFTS/triage.md" | head -1)"
    if [[ -z "$items" ]]; then echo "$group: no 'GROUP $group:' line in triage.md" >&2; continue; fi
    if [[ -f "$DRAFTS/$group.md" ]]; then echo "$group: draft exists (rebuttal/$group.md); delete it to redraft"; continue; fi
    # shellcheck disable=SC2086
    python3 "$PROC/dossier.py" "$OUT" $items > "$DRAFTS/$group.dossier.md"
    echo "Drafting $group ($items; $REBUTTAL_MODEL, effort $REBUTTAL_EFFORT); log: docs/reviews/$TAG/rebuttal/$group.log"
    (
        run_agent "rebuttal-$TAG-$group" \
            "$(fill "$PROC/rebuttal-brief.md" "GROUP=$group" "ITEMS=$items")" \
            "$REBUTTAL_EFFORT" "$DRAFTS/$group.log"
        if [[ "$DRY_RUN" != "1" && ! -f "$DRAFTS/$group.md" ]]; then echo "$group: no draft written (see rebuttal/$group.log)" >&2; fi
    ) &
    running=$((running + 1))
    if [[ "$running" -ge "$REBUTTAL_PARALLEL" ]]; then wait -n || true; running=$((running - 1)); fi
done
wait || true
echo "Done: docs/reviews/$TAG/rebuttal/ (triage.md holds the table and the decisions)"
