#!/usr/bin/env bash
# PostToolUse hook: 編集ファイルの品質チェック
# exit 0 = pass, exit 1 = warn (additionalContext)

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0
[[ ! -f "$FILE_PATH" ]] && exit 0

BASENAME=$(basename "$FILE_PATH")
LINES=$(wc -l < "$FILE_PATH" | tr -d ' ')

# CLAUDE.md 行数チェック（50行超で警告）
if [[ "$BASENAME" == "CLAUDE.md" ]]; then
  if (( LINES > 50 )); then
    echo "{\"additionalContext\":\"WARNING: CLAUDE.md is ${LINES} lines (target: ≤50). Consider extracting details to rules/ or docs/.\"}"
    exit 1
  fi
fi

# rules/*.md 行数チェック（200行超で警告）
if [[ "$FILE_PATH" == *"/rules/"* && "$FILE_PATH" == *.md ]]; then
  if (( LINES > 200 )); then
    echo "{\"additionalContext\":\"WARNING: ${BASENAME} is ${LINES} lines (target: ≤200). Consider splitting into smaller files.\"}"
    exit 1
  fi
fi

# agents/*.md description チェック（100文字超で警告）
if [[ "$FILE_PATH" == *"/agents/"* && "$FILE_PATH" == *.md ]]; then
  DESC=$(grep -m1 '^description:' "$FILE_PATH" 2>/dev/null | sed 's/^description:\s*//' || true)
  if [[ -n "$DESC" ]] && (( ${#DESC} > 100 )); then
    echo "{\"additionalContext\":\"WARNING: Agent description exceeds 100 chars (${#DESC}). Keep it concise.\"}"
    exit 1
  fi
fi

# .ts/.tsx ファイル: eslint/biome（あれば）
if [[ "$FILE_PATH" == *.ts || "$FILE_PATH" == *.tsx ]]; then
  DIR=$(dirname "$FILE_PATH")
  # eslint or biome を探す
  while [[ "$DIR" != "/" ]]; do
    if [[ -f "$DIR/node_modules/.bin/eslint" ]]; then
      RESULT=$("$DIR/node_modules/.bin/eslint" --no-eslintrc --rule '{}' "$FILE_PATH" 2>&1 || true)
      if [[ -n "$RESULT" && "$RESULT" != *"0 problems"* ]]; then
        echo "{\"additionalContext\":\"ESLint: $(echo "$RESULT" | tail -3)\"}"
      fi
      break
    fi
    DIR=$(dirname "$DIR")
  done
fi

exit 0
