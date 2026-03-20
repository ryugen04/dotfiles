#!/usr/bin/env bash
# PreToolUse hook: 破壊的操作をブロック
# exit 0 = allow, exit 2 = block

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Bash以外はスキップ
[[ "$TOOL_NAME" != "Bash" ]] && exit 0

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[[ -z "$COMMAND" ]] && exit 0

block() {
  local why="$1" fix="$2"
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: $why / FIX: $fix\"}" >&2
  exit 2
}

# rm -rf / (ルート削除)
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+/|--no-preserve-root)'; then
  block "ルートディレクトリの再帰削除は禁止" "削除対象を限定してください"
fi

# DROP TABLE / TRUNCATE
if echo "$COMMAND" | grep -qiE '(DROP\s+TABLE|TRUNCATE\s+TABLE)'; then
  block "テーブルの削除/truncateは禁止" "ユーザーに確認を求めてください"
fi

# git push --force
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force'; then
  block "force pushは禁止" "通常のpushを使用し、ユーザーの明示的指示を得てください"
fi

# .env ファイルの直接編集
if echo "$COMMAND" | grep -qE '(cat|echo|printf|tee)\s.*>\s*.*\.env($|\s)'; then
  block ".envファイルへの直接書き込みは禁止" "Editツールを使用してください"
fi

# dropdb
if echo "$COMMAND" | grep -qE 'dropdb\b'; then
  block "データベース削除は禁止" "ユーザーに確認を求めてください"
fi

# docker rm -f (コンテナ強制削除)
if echo "$COMMAND" | grep -qE 'docker\s+rm\s+-f'; then
  block "コンテナの強制削除は禁止" "docker stopを使用してください"
fi

exit 0
