#!/usr/bin/env bash
# Claude Codeペインにテキストを送信する
# - レビューコメント、フィードバック等をClaude Codeに直接送信
# - Claude Codeのsurface IDはSessionStartフックで保存済み

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"
STATE_DIR="/tmp/cmux-pane-state"

if [[ $# -lt 1 ]]; then
  echo "Usage: cmux-send-claude <text>"
  echo "       echo 'text' | cmux-send-claude -"
  exit 1
fi

# テキスト取得（引数 or stdin）
if [[ "$1" == "-" ]]; then
  TEXT=$(cat)
else
  TEXT="$*"
fi

if [[ -z "$TEXT" ]]; then
  echo "Empty text, nothing to send"
  exit 1
fi

# cmux未起動チェック
if ! "$CMUX" ping &>/dev/null; then
  echo "cmux is not running"
  exit 1
fi

# Claude Codeのsurface IDを探す
find_claude_surface() {
  local tree
  tree=$("$CMUX" tree 2>/dev/null)

  # 1. "here" マーカー付きのターミナル = 呼び出し元のClaude Codeセッション
  local surface
  surface=$(echo "$tree" | grep '\[terminal\]' | grep '◀ here' | grep -oE 'surface:[0-9]+' | head -1)
  if [[ -n "$surface" ]]; then
    echo "$surface"
    return 0
  fi

  # 2. Claude Code系タイトルのターミナル
  surface=$(echo "$tree" | grep '\[terminal\]' | grep -i 'claude\|⠂\|⠐\|✳' | grep -oE 'surface:[0-9]+' | head -1)
  if [[ -n "$surface" ]]; then
    echo "$surface"
    return 0
  fi

  return 1
}

CLAUDE_SURFACE=$(find_claude_surface) || {
  echo "Claude Code surface not found in this workspace"
  echo "Hint: Claude Codeを起動し直すか、SessionStartフックが設定されているか確認"
  exit 1
}

# テキストをClaude Codeに送信
"$CMUX" send --surface "$CLAUDE_SURFACE" "$TEXT"
"$CMUX" send-key --surface "$CLAUDE_SURFACE" enter

echo "Sent to Claude Code ($CLAUDE_SURFACE)"
