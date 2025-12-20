#!/usr/bin/env bash
# PostToolUse (Edit|Write) 用ログ記録スクリプト
# Claude が Edit / Write でファイルを変更したタイミングで、
# logs/dev/YYYY-MM-DD.yaml に追記する

set -euo pipefail

INPUT_JSON="$(cat || true)"

TODAY=$(date +%Y-%m-%d)
LOG_DIR="$HOME/dev/logs/claude-catchup/dev"
LOG_FILE="$LOG_DIR/$TODAY.yaml"

mkdir -p "$LOG_DIR"

TOOL=$(echo "$INPUT_JSON" | jq -r '.tool_name // "unknown"' 2>/dev/null || echo "unknown")
FILE=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null || echo "")

# ファイルがなければ entries: を作る
if [ ! -f "$LOG_FILE" ]; then
  echo "entries:" > "$LOG_FILE"
fi

# 新しいエントリを追加（yq を使用）
if command -v yq &> /dev/null; then
  yq -i ".entries += [{\"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%S%z")\", \"tool\": \"$TOOL\", \"file\": \"$FILE\", \"summary\": \"ClaudeCode による自動編集\"}]" "$LOG_FILE"
else
  # yq がない場合は簡易的に追記
  cat >> "$LOG_FILE" <<EOF
  - timestamp: "$(date -u +"%Y-%m-%dT%H:%M:%S%z")"
    tool: "$TOOL"
    file: "$FILE"
    summary: "ClaudeCode による自動編集"
EOF
fi

exit 0
