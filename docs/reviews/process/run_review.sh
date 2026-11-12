#!/usr/bin/env bash
# Run the simulated review end to end: build the PDF, run the reviewers in parallel (isolated, outside the repository),
# then the meta-reviewer (inside the repository). Knobs in config.sh; procedure in docs/reviews/review-prompt.md.
#
# Usage (from the repository root):
#   docs/reviews/process/run_review.sh
#   DRY_RUN=1 docs/reviews/process/run_review.sh            # show prompts and commands only
#   STEPS=meta TAG=2026-11-13-body docs/reviews/process/run_review.sh   # redo the meta-review only
set -euo pipefail

REPO="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
PROC="$REPO/docs/reviews/process"
# shellcheck source=config.sh
source "$PROC/config.sh"

WORK="$WORK_ROOT/$TAG"
OUT="$REPO/docs/reviews/$TAG"
COMMIT="$(git -C "$REPO" rev-parse --short HEAD)"

fill() {
    # Replace the {{PLACEHOLDERS}} of a prompt file with this run's values (quoted replacements: "S&P" stays as is).
    local s
    s="$(cat "$1")"
    s="${s//\{\{VENUE\}\}/"$VENUE"}"
    s="${s//\{\{SCALE\}\}/"$SCALE"}"
    s="${s//\{\{TAG\}\}/"$TAG"}"
    s="${s//\{\{WORK\}\}/"$WORK"}"
    s="${s//\{\{OUT\}\}/"docs/reviews/$TAG"}"
    s="${s//\{\{COMMIT\}\}/"$COMMIT"}"
    s="${s//\{\{REVIEWERS\}\}/"$REVIEWERS"}"
    printf '%s\n' "$s"
}

budget_flag() {
    if [[ -n "$MAX_BUDGET_USD" ]]; then echo "--max-budget-usd $MAX_BUDGET_USD"; fi
}

################################################################################
# Preparation
################################################################################

# Refuse to overwrite a finished run: a new run needs a new TAG (or FORCE=1). STEPS=meta and single reviewers pass.
if [[ "$STEPS" != "meta" && "${FORCE:-0}" != "1" && "$DRY_RUN" != "1" ]]; then
    for id in $REVIEWERS; do
        if [[ -f "$OUT/reviewer-$id.md" ]]; then
            echo "docs/reviews/$TAG/reviewer-$id.md exists: use another TAG, FORCE=1 to redo it, or resume_meta.sh" >&2
            exit 1
        fi
    done
fi
mkdir -p "$OUT"
if [[ "$STEPS" == "all" || "$STEPS" == "reviewers" ]]; then
    echo "Building the PDF (make in manuscript/; log: $OUT/make.log)"
    if [[ "$DRY_RUN" != "1" ]]; then
        make -C "$REPO/manuscript" > "$OUT/make.log" 2>&1
    fi
    echo "Preparing the reviewers' folder $WORK (paper.pdf, note-to-reviewers.md, papers/)"
    mkdir -p "$WORK"
    cp "$REPO/manuscript/main.pdf" "$WORK/paper.pdf"
    cp "$PROC/note-to-reviewers.md" "$WORK/note-to-reviewers.md"
    rm -rf "$WORK/papers"
    cp -r "$REPO/papers" "$WORK/papers"
    cp "$REPO/manuscript/main.pdf" "$OUT/paper.pdf"
fi
# Record what this run used. A meta-only rerun appends its own record, so the reviewers' commit and date are kept.
if [[ "$STEPS" == "meta" && -f "$OUT/run-config.txt" ]]; then
    {
        echo "# meta step rerun"
        echo "meta_commit=$COMMIT"
        echo "meta_date=$(date -Iseconds)"
        echo "META_MODEL=$META_MODEL"
        echo "META_EFFORT=$META_EFFORT"
    } >> "$OUT/run-config.txt"
else
{
    echo "commit=$COMMIT"
    echo "date=$(date -Iseconds)"
    grep -E '^[A-Z_]+=' "$PROC/config.sh" | cut -d= -f1 | while read -r v; do echo "$v=${!v}"; done
    for id in $REVIEWERS; do
        m="MODEL_$id"; e="EFFORT_$id"
        echo "reviewer $id: model=${!m:-$REVIEWER_MODEL} effort=${!e:-$REVIEWER_EFFORT}"
    done
} > "$OUT/run-config.txt"
fi
cp "$PROC/note-to-reviewers.md" "$PROC/checklist.md" "$OUT/"

################################################################################
# Step 1: the reviewers, in parallel
################################################################################

if [[ "$STEPS" == "all" || "$STEPS" == "reviewers" ]]; then
    tools="Read Write Glob Grep Bash(pdftotext:*)"
    if [[ "$REVIEWER_WEB" == "1" ]]; then tools="$tools WebSearch WebFetch"; fi
    pids=()
    for id in $REVIEWERS; do
        persona="$(ls "$PROC"/reviewers/"$id"-*.md 2>/dev/null | head -1)"
        if [[ -z "$persona" ]]; then echo "No persona file reviewers/$id-*.md" >&2; exit 1; fi
        m="MODEL_$id"; e="EFFORT_$id"
        model="${!m:-$REVIEWER_MODEL}"; effort="${!e:-$REVIEWER_EFFORT}"
        prompt="$(fill "$PROC/reviewer-brief.md"; echo; fill "$persona"; echo; echo "Your reviewer ID is $id. Write your review to review-$id.md in the current directory.")"
        prompt="${prompt//\{\{ID\}\}/"$id"}"
        echo "Reviewer $id ($model, effort $effort); log: $WORK/reviewer-$id.log"
        if [[ "$DRY_RUN" == "1" ]]; then
            echo "----- prompt of reviewer $id -----"; echo "$prompt"; echo "-----"
            continue
        fi
        # shellcheck disable=SC2046
        (cd "$WORK" && claude -p "$prompt" \
            --model "$model" \
            --effort "$effort" \
            --permission-mode acceptEdits \
            --allowedTools $tools \
            --name "review-$TAG-$id" \
            $(budget_flag) \
            > "$WORK/reviewer-$id.log" 2>&1) &
        pids+=($!)
    done
    for p in "${pids[@]}"; do wait "$p" || echo "A reviewer exited with an error (see its log)" >&2; done
    if [[ "$DRY_RUN" != "1" ]]; then
        for id in $REVIEWERS; do
            if [[ -f "$WORK/review-$id.md" ]]; then
                cp "$WORK/review-$id.md" "$OUT/reviewer-$id.md"
            else
                echo "Reviewer $id wrote no review (see $WORK/reviewer-$id.log)" >&2
            fi
            cp "$WORK/reviewer-$id.log" "$OUT/reviewer-$id.log"
        done
    fi
fi

################################################################################
# Step 2: the meta-reviewer, inside the repository
################################################################################

if [[ "$STEPS" == "all" || "$STEPS" == "meta" ]]; then
    prompt="$(fill "$PROC/meta-brief.md"; echo; echo "## This run's checklist"; echo; cat "$PROC/checklist.md")"
    echo "Meta-reviewer ($META_MODEL, effort $META_EFFORT); log: $OUT/meta.log"
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "----- prompt of the meta-reviewer -----"; echo "$prompt"; echo "-----"
        exit 0
    fi
    # shellcheck disable=SC2046
    (cd "$REPO" && claude -p "$prompt" \
        --model "$META_MODEL" \
        --effort "$META_EFFORT" \
        --permission-mode acceptEdits \
        --allowedTools Read Write Edit Glob Grep WebSearch WebFetch "Bash(pdftotext:*)" "Bash(git log:*)" \
            "Bash(git show:*)" "Bash(grep:*)" "Bash(ls:*)" "Bash(env/bin/python:*)" \
            "Bash($HOME/texlive/2026/bin/x86_64-linux/texcount:*)" \
        --name "review-$TAG-meta" \
        $(budget_flag) \
        > "$OUT/meta.log" 2>&1)
    echo "Done: docs/reviews/$TAG/ (meta-review.md and the reviews)"
fi
