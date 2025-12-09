#!/usr/bin/env bash
# PreCompact (manual) 用ログ記録スクリプト
# /compact 実行時に、ユーザーには何も表示せず、
# セッションスニペットを記録する

set -euo pipefail

INPUT_JSON="$(cat || true)"

TODAY=$(date +%Y-%m-%d)
LOG_DIR="$HOME/dev/logs/claude-catchup/dev"
LOG_FILE="$LOG_DIR/$TODAY.yaml"

mkdir -p "$LOG_DIR"

# ファイルがなければ初期化
if [ ! -f "$LOG_FILE" ]; then
  cat > "$LOG_FILE" <<EOF
entries:
session_snippets:
EOF
fi

# session_snippets がなければ追加
if ! grep -q "^session_snippets:" "$LOG_FILE" 2>/dev/null; then
  echo "session_snippets:" >> "$LOG_FILE"
fi

# 新しいスニペットを追加
if command -v yq &> /dev/null; then
  yq -i ".session_snippets += [{\"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%S%z")\", \"note\": \"compact 前のセッション記録\"}]" "$LOG_FILE"
else
  cat >> "$LOG_FILE" <<EOF
  - timestamp: "$(date -u +"%Y-%m-%dT%H:%M:%S%z")"
    note: "compact 前のセッション記録"
EOF
fi

# ユーザーには何も出力しない
exit 0
