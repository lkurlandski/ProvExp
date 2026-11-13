#!/usr/bin/env bash
# Draft the rebuttal of every risk in a meta-review's register: one headless agent per item (rebuttal-brief.md), each
# writing docs/reviews/<TAG>/rebuttal/<R#>.md (the reviewers' perspective, a neutral analysis, an opinion), then an
# index of the opinions. The user's decisions are taken afterwards, one item per interactive session
# (docs/resume-prompt-rebuttal.md), and recorded in docs/reviews/<TAG>/meta-rebuttal.md. Run by run_review.sh after the
# meta-review (REBUTTAL=1), or alone. Knobs in config.sh; procedure in docs/reviews/review-prompt.md.
#
# Usage (from the repository root):
#   TAG=2026-11-12-body docs/reviews/process/run_rebuttal.sh
#   TAG=2026-11-12-body REBUTTAL_ITEMS="R2 R18" docs/reviews/process/run_rebuttal.sh   # only these items
#   DRY_RUN=1 TAG=2026-11-12-body docs/reviews/process/run_rebuttal.sh                # show prompts only
set -euo pipefail

REPO="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
PROC="$REPO/docs/reviews/process"
# shellcheck source=config.sh
source "$PROC/config.sh"

OUT="$REPO/docs/reviews/$TAG"
DRAFTS="$OUT/rebuttal"
RECORD="$OUT/meta-rebuttal.md"
COMMIT="$(git -C "$REPO" rev-parse --short HEAD)"

if [[ ! -f "$OUT/meta-review.md" ]]; then
    echo "docs/reviews/$TAG/meta-review.md does not exist: run the meta-review first" >&2
    exit 1
fi

################################################################################
# The items: the register's order (§6 of the meta-review), minus what is drafted, decided or skipped
################################################################################

register_items() {
    # The R-numbers of the register table, in its order (likelihood x severity).
    awk '/^## 6\./ {on=1; next} /^## / {on=0} on && /^\| R[0-9]+ \|/ {print $2}' "$OUT/meta-review.md"
}

items="${REBUTTAL_ITEMS:-$(register_items | tr '\n' ' ')}"
todo=()
for item in $items; do
    if [[ " $REBUTTAL_SKIP " == *" $item "* ]]; then
        echo "$item: skipped (REBUTTAL_SKIP)"
    elif [[ -f "$DRAFTS/$item.md" ]]; then
        echo "$item: draft exists (rebuttal/$item.md); delete it to redraft"
    elif [[ -f "$RECORD" ]] && grep -q "^## $item:" "$RECORD"; then
        echo "$item: already decided in meta-rebuttal.md"
    else
        todo+=("$item")
    fi
done
if [[ "${#todo[@]}" -eq 0 ]]; then echo "Nothing to draft."; fi
if [[ "$DRY_RUN" != "1" ]]; then mkdir -p "$DRAFTS"; fi

################################################################################
# The drafts, REBUTTAL_PARALLEL at a time
################################################################################

draft() {
    # Run one drafting agent for item $1, inside the repository (it needs the code, the outputs and the decisions).
    local item="$1" prompt s
    s="$(cat "$PROC/rebuttal-brief.md")"
    s="${s//\{\{ITEM\}\}/"$item"}"
    s="${s//\{\{TAG\}\}/"$TAG"}"
    s="${s//\{\{OUT\}\}/"docs/reviews/$TAG"}"
    s="${s//\{\{COMMIT\}\}/"$COMMIT"}"
    prompt="$s"
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "----- prompt for $item -----"; echo "$prompt"; echo "-----"
        return 0
    fi
    # shellcheck disable=SC2046
    (cd "$REPO" && claude -p "$prompt" \
        --model "$REBUTTAL_MODEL" \
        --effort "$REBUTTAL_EFFORT" \
        --permission-mode acceptEdits \
        --allowedTools Read Write Glob Grep "Bash(pdftotext:*)" "Bash(git log:*)" "Bash(git show:*)" \
            "Bash(grep:*)" "Bash(ls:*)" "Bash(env/bin/python:*)" \
        --name "rebuttal-$TAG-$item" \
        $(if [[ -n "$MAX_BUDGET_USD" ]]; then echo "--max-budget-usd $MAX_BUDGET_USD"; fi) \
        > "$DRAFTS/$item.log" 2>&1) || echo "$item: the agent exited with an error (see rebuttal/$item.log)" >&2
    if [[ ! -f "$DRAFTS/$item.md" ]]; then echo "$item: no draft written (see rebuttal/$item.log)" >&2; fi
}

running=0
for item in "${todo[@]}"; do
    echo "Drafting $item ($REBUTTAL_MODEL, effort $REBUTTAL_EFFORT); log: docs/reviews/$TAG/rebuttal/$item.log"
    draft "$item" &
    running=$((running + 1))
    if [[ "$running" -ge "$REBUTTAL_PARALLEL" ]]; then wait -n || true; running=$((running - 1)); fi
done
wait || true
if [[ "$DRY_RUN" == "1" ]]; then exit 0; fi

################################################################################
# The index: each draft's opinion line, in the register's order
################################################################################

{
    echo "# Rebuttal drafts of the $TAG review"
    echo
    echo "Written by \`docs/reviews/process/run_rebuttal.sh\` (commit $COMMIT, $(date +%F)); regenerated on every run."
    echo "One draft per register item, in the register's order. Drafts are Claude's analysis only: the user's"
    echo "decisions are in \`../meta-rebuttal.md\` (procedure: \`docs/resume-prompt-rebuttal.md\`)."
    echo
    echo "| Item | Draft's opinion |"
    echo "|---|---|"
    for item in $(register_items); do
        if [[ -f "$DRAFTS/$item.md" ]]; then
            opinion="$(sed -n 's/^\*\*Opinion:\*\* *//p' "$DRAFTS/$item.md" | head -1)"
            echo "| [$item]($item.md) | ${opinion:-(no opinion line)} |"
        else
            echo "| $item | no draft |"
        fi
    done
} > "$DRAFTS/README.md"
echo "Done: docs/reviews/$TAG/rebuttal/ (README.md indexes the drafts)"
