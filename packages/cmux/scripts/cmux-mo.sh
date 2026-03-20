#!/usr/bin/env bash
# MarkdownをCmuxブラウザで表示

set -euo pipefail

CMUX="/Applications/cmux.app/Contents/Resources/bin/cmux"
PORT=6275

if [[ $# -lt 1 ]]; then
  echo "Usage: cmux-mo <markdown-file>"
  exit 1
fi

FILE="$1"

# 相対パスを絶対パスに変換
if [[ ! "$FILE" = /* ]]; then
  FILE="$(pwd)/$FILE"
fi

if [[ ! -f "$FILE" ]]; then
  echo "File not found: $FILE"
  exit 1
fi

# moの存在確認
if ! command -v mo &> /dev/null; then
  echo "mo not found. Install with: brew install k1LoW/tap/mo"
  exit 1
fi

# 既存のmoプロセスを停止
pkill -f "mo.*${PORT}" 2>/dev/null || true
sleep 0.2

# moサーバー起動（バックグラウンド）
mo "$FILE" --port "$PORT" &
MO_PID=$!

cleanup() {
  kill "$MO_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# サーバー準備待ち
for i in {1..30}; do
  if curl -s "http://localhost:${PORT}" > /dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

# cmuxブラウザで開く
if [[ -x "$CMUX" ]]; then
  "$CMUX" browser open-split "http://localhost:${PORT}/" 2>/dev/null || \
    echo "Open in browser: http://localhost:${PORT}"
else
  echo "Open in browser: http://localhost:${PORT}"
fi

# サーバーを維持
wait $MO_PID
