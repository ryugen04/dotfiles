#!/usr/bin/env bash
# SessionStart hook: Claude Codeのsurface IDを保存
# cmux-send-claude.sh がClaude Codeペインを特定するために使用

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"
STATE_DIR="/tmp/cmux-pane-state"

# cmux未起動なら何もしない
"$CMUX" ping &>/dev/null || exit 0

mkdir -p "$STATE_DIR"

# CMUX_SURFACE_ID（Claude Codeが動いているsurface）を保存
if [[ -n "${CMUX_SURFACE_ID:-}" && -n "${CMUX_WORKSPACE_ID:-}" ]]; then
  echo "$CMUX_SURFACE_ID" > "$STATE_DIR/claude-surface-${CMUX_WORKSPACE_ID}"
fi

exit 0
