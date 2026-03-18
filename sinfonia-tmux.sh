#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# sinfonia-tmux.sh — Launch Sinfonia with tmux split panes
#
# Layout:
#   ┌──────────────────────┬──────────────────────┐
#   │                      │                      │
#   │  SINFONIA             │  AGENT OUTPUT        │
#   │  (orchestrator)      │  (live log)          │
#   │                      │                      │
#   └──────────────────────┴──────────────────────┘
#
# Usage:
#   ./sinfonia-tmux.sh                    # default: claude runner
#   ./sinfonia-tmux.sh codex              # use codex runner
#   ./sinfonia-tmux.sh claude US-162      # single story
#   ./sinfonia-tmux.sh --once             # process one batch and exit
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION="sinfonia"
RUNNER="claude"
STORY=""
EXTRA_ARGS=""

# Parse args — all positional, no shift needed
for arg in "$@"; do
    case "$arg" in
        --once)
            EXTRA_ARGS="$EXTRA_ARGS --once"
            ;;
        --dry-run)
            EXTRA_ARGS="$EXTRA_ARGS --dry-run"
            ;;
        US-*)
            STORY="$arg"
            ;;
        claude|codex|kimi|droid)
            RUNNER="$arg"
            ;;
    esac
done

# Build sinfonia command
SINFONIA_CMD="cd '$SCRIPT_DIR' && source .env 2>/dev/null; python3 sinfonia.py run --runner $RUNNER"
if [ -n "$STORY" ]; then
    SINFONIA_CMD="$SINFONIA_CMD --story $STORY"
fi
if [ -n "$EXTRA_ARGS" ]; then
    SINFONIA_CMD="$SINFONIA_CMD $EXTRA_ARGS"
fi

# Log tail command
LOG_CMD="cd '$SCRIPT_DIR' && mkdir -p .sinfonia/logs && echo 'Waiting for agent output...' && while [ ! -L .sinfonia/logs/current.log ] || [ ! -e .sinfonia/logs/current.log ]; do sleep 1; done && tail -F .sinfonia/logs/current.log"

# Kill existing session if any
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Create new tmux session with sinfonia in left pane
tmux new-session -d -s "$SESSION" -x 200 -y 50

# Left pane: header + sinfonia
tmux send-keys -t "$SESSION" "clear && echo '╔══════════════════════════════════════╗' && echo '║  SINFONIA ORCHESTRATOR               ║' && echo '║  runner: $RUNNER                      ' && echo '╚══════════════════════════════════════╝' && echo '' && $SINFONIA_CMD" C-m

# Split right pane (50% width) for agent log
tmux split-window -h -t "$SESSION"
tmux send-keys -t "$SESSION" "clear && echo '╔══════════════════════════════════════╗' && echo '║  AGENT LIVE OUTPUT                   ║' && echo '╚══════════════════════════════════════╝' && echo '' && $LOG_CMD" C-m

# Focus on left pane (orchestrator)
tmux select-pane -t "$SESSION:0.0"

# Attach
tmux attach-session -t "$SESSION"
