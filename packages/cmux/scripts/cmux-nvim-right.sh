#!/usr/bin/env bash
# 右ペインのnvimでファイルを開く
# - 右ペインが存在しなければ作成
# - nvimが起動中なら :e で開き直す
# - nvimが未起動なら nvim を起動

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"
STATE_DIR="/tmp/cmux-pane-state"
mkdir -p "$STATE_DIR"

if [[ $# -lt 1 ]]; then
  echo "Usage: cmux-nvim-right <file>"
  exit 1
fi

FILE="$1"
[[ "$FILE" != /* ]] && FILE="$(pwd)/$FILE"

if [[ ! -f "$FILE" ]]; then
  echo "File not found: $FILE"
  exit 1
fi

# cmux未起動チェック
if ! "$CMUX" ping &>/dev/null; then
  echo "cmux is not running"
  exit 1
fi

# 現在のワークスペースのペイン一覧からcaller以外のペインを探す
find_right_pane() {
  local caller_pane
  caller_pane=$("$CMUX" identify 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['caller']['pane_ref'])" 2>/dev/null) || return 1

  # tree出力からペインrefを抽出（callerのペイン以外）
  local panes
  panes=$("$CMUX" tree 2>/dev/null | grep -oE 'pane:[0-9]+' | sort -u | grep -v "$caller_pane" | head -1)

  if [[ -n "$panes" ]]; then
    echo "$panes"
    return 0
  fi
  return 1
}

# 右ペインのターミナルsurfaceを取得
find_terminal_surface() {
  local pane_ref="$1"
  # tree出力からそのペイン配下のterminal surfaceを探す
  "$CMUX" tree 2>/dev/null | awk -v pane="$pane_ref" '
    $0 ~ pane { found=1; next }
    found && /pane:/ { exit }
    found && /\[terminal\]/ { match($0, /surface:[0-9]+/); print substr($0, RSTART, RLENGTH); exit }
  '
}

# 右ペインのnvim状態を確認（screen内容から推定）
is_nvim_running() {
  local surface_ref="$1"
  local screen
  screen=$("$CMUX" read-screen --surface "$surface_ref" --lines 2 2>/dev/null) || return 1
  # nvimの典型的なUIパターンを検出
  [[ "$screen" =~ (NORMAL|INSERT|VISUAL|COMMAND|--\ .*--) ]] && return 0
  return 1
}

# メイン処理
RIGHT_PANE=$(find_right_pane) || RIGHT_PANE=""

if [[ -z "$RIGHT_PANE" ]]; then
  # 右ペインを作成
  "$CMUX" new-split right 2>/dev/null
  sleep 0.3
  RIGHT_PANE=$(find_right_pane) || { echo "Failed to create right pane"; exit 1; }
fi

SURFACE=$(find_terminal_surface "$RIGHT_PANE")
if [[ -z "$SURFACE" ]]; then
  echo "No terminal surface in right pane"
  exit 1
fi

# nvimが起動中なら :e で開く、未起動なら nvim を起動
if is_nvim_running "$SURFACE"; then
  "$CMUX" send --surface "$SURFACE" ":e $FILE"
  "$CMUX" send-key --surface "$SURFACE" enter
else
  "$CMUX" send --surface "$SURFACE" "nvim \"$FILE\""
  "$CMUX" send-key --surface "$SURFACE" enter
fi

echo "Opened in nvim (right pane): $FILE"
