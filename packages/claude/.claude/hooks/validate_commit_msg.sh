#!/usr/bin/env bash
# PreToolUse hook: git commitメッセージ検証
# exit 0 = allow, exit 1 = warn, exit 2 = block

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

[[ "$TOOL_NAME" != "Bash" ]] && exit 0

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[[ -z "$COMMAND" ]] && exit 0

# git commit コマンドでなければスキップ
if ! echo "$COMMAND" | grep -qE 'git\s+((-C\s+\S+\s+)?commit|-C\s+\S+\s+commit)'; then
  exit 0
fi

# -m 引数を抽出（macOS互換: grep -P は使えない）
MSG=$(echo "$COMMAND" | sed -n 's/.*-m "\([^"]*\)".*/\1/p')
if [[ -z "$MSG" ]]; then
  MSG=$(echo "$COMMAND" | sed -n "s/.*-m '\([^']*\)'.*/\1/p")
fi
[[ -z "$MSG" ]] && exit 0

# Co-Authored-By チェック
if echo "$MSG" | grep -qi 'Co-Authored-By'; then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: Co-Authored-Byは禁止 / WHY: プロジェクトルールで禁止 / FIX: Co-Authored-By行を削除してください\"}" >&2
  exit 2
fi

# HEREDOC チェック（コマンド内にHEREDOC構文がある場合）
if echo "$COMMAND" | grep -qE '<<.*EOF'; then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: HEREDOCでのコミットは禁止 / WHY: 改行が入りやすい / FIX: -m \\\"...\\\" で直接記述してください\"}" >&2
  exit 2
fi

# 2行目以降チェック（改行が含まれている場合）
LINE_COUNT=$(echo "$MSG" | wc -l | tr -d ' ')
if (( LINE_COUNT > 1 )); then
  echo "{\"decision\":\"block\",\"reason\":\"ERROR: コミットメッセージは1行のみ / WHY: 詳細はPRで説明する / FIX: 2行目以降を削除してください\"}" >&2
  exit 2
fi

# type(scope): 形式チェック（警告のみ）
if ! echo "$MSG" | grep -qE '^(fix|feat|refactor|docs|chore|test|style|perf|ci|build|revert)\([^)]+\):'; then
  echo "{\"additionalContext\":\"WARNING: コミットメッセージが type(scope): 形式ではありません。推奨形式: fix(scope): 修正内容\"}"
  exit 1
fi

exit 0
