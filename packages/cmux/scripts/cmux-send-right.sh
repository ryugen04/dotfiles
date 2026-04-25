#!/usr/bin/env bash
# 右ペインにテキストを送信する
# - 右ペインが存在しなければ作成
# - テキスト送信後にEnterキーも送信（--no-enterで抑制）

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"

usage() {
  echo "Usage: cmux-send-right [--no-enter] <text>"
  echo "       echo 'text' | cmux-send-right -"
  exit 1
}

SEND_ENTER=true
TEXT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-enter) SEND_ENTER=false; shift ;;
    -) TEXT=$(cat); shift ;;
    *) TEXT="$*"; break ;;
  esac
done

[[ -z "$TEXT" ]] && usage

# cmux未起動チェック
"$CMUX" ping &>/dev/null || { echo "cmux is not running"; exit 1; }

# callerのペインを特定
CALLER_PANE=$("$CMUX" identify 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['caller']['pane_ref'])" 2>/dev/null) || { echo "Failed to identify caller"; exit 1; }

# 右ペイン（caller以外のペイン）を探す
RIGHT_PANE=$("$CMUX" tree 2>/dev/null | grep -oE 'pane:[0-9]+' | sort -u | grep -v "$CALLER_PANE" | head -1)

if [[ -z "$RIGHT_PANE" ]]; then
  "$CMUX" new-split right 2>/dev/null
  sleep 0.3
  RIGHT_PANE=$("$CMUX" tree 2>/dev/null | grep -oE 'pane:[0-9]+' | sort -u | grep -v "$CALLER_PANE" | head -1)
  [[ -z "$RIGHT_PANE" ]] && { echo "Failed to find/create right pane"; exit 1; }
fi

# 右ペインのターミナルsurfaceを取得
SURFACE=$("$CMUX" tree 2>/dev/null | awk -v pane="$RIGHT_PANE" '
  $0 ~ pane { found=1; next }
  found && /pane:/ { exit }
  found && /\[terminal\]/ { match($0, /surface:[0-9]+/); print substr($0, RSTART, RLENGTH); exit }
')

[[ -z "$SURFACE" ]] && { echo "No terminal surface in right pane"; exit 1; }

"$CMUX" send --surface "$SURFACE" "$TEXT"
[[ "$SEND_ENTER" == true ]] && "$CMUX" send-key --surface "$SURFACE" enter

echo "Sent to right pane ($SURFACE)"
