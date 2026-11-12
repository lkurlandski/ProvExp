#!/usr/bin/env bash
# Resume a stopped meta-reviewer from its saved session (everything it read so far stays in its context), with the
# model and effort of config.sh (or the environment). Stop the running one first (Ctrl-C in its tmux pane).
#
# Usage (from the repository root):
#   docs/reviews/process/resume_meta.sh                        # newest meta-review session, META_EFFORT from config
#   META_EFFORT=high SESSION=<session id> docs/reviews/process/resume_meta.sh
set -euo pipefail

REPO="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
PROC="$REPO/docs/reviews/process"
# shellcheck source=config.sh
source "$PROC/config.sh"
OUT="$REPO/docs/reviews/$TAG"
SESSIONS="$HOME/.claude/projects/$(echo "$REPO" | sed 's|[/.]|-|g')"

if [[ -z "${SESSION:-}" ]]; then
    # The newest session whose first line of input is the meta-reviewer's brief.
    for f in $(ls -t "$SESSIONS"/*.jsonl); do
        if head -c 20000 "$f" | grep -q 'Your task: meta-review of a simulated program-committee review'; then
            SESSION="$(basename "$f" .jsonl)"; break
        fi
    done
fi
if [[ -z "${SESSION:-}" ]]; then echo "No meta-review session found in $SESSIONS" >&2; exit 1; fi
if pgrep -f "claude -p # Your task: meta-review" > /dev/null; then
    echo "A meta-reviewer is still running; stop it first (Ctrl-C in its pane)." >&2; exit 1
fi

echo "Resuming meta-review session $SESSION ($META_MODEL, effort $META_EFFORT); log: $OUT/meta-resume.log"
cd "$REPO" && claude -p "You were stopped partway through the meta-review and are now resumed. Do not repeat the \
reading you have already done: continue from where you were, check only what is still needed, and write \
$( [[ -n "$TAG" ]] && echo "docs/reviews/$TAG/meta-review.md" ) in full, then add its line to docs/reviews/README.md." \
    --resume "$SESSION" \
    --model "$META_MODEL" \
    --effort "$META_EFFORT" \
    --permission-mode acceptEdits \
    --allowedTools Read Write Edit Glob Grep WebSearch WebFetch "Bash(pdftotext:*)" "Bash(git log:*)" \
        "Bash(git show:*)" "Bash(grep:*)" "Bash(ls:*)" "Bash(env/bin/python:*)" \
        "Bash($HOME/texlive/2026/bin/x86_64-linux/texcount:*)" \
    > "$OUT/meta-resume.log" 2>&1
echo "Done: docs/reviews/$TAG/meta-review.md"
