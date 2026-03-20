#!/usr/bin/env bash
# PostToolUse(Bash) hook: エラー検出 → 知見記録を促進 (H9)
# exit 0 = pass (additionalContext で促す)

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
[[ "$TOOL_NAME" != "Bash" ]] && exit 0

EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_output.exitCode // .tool_output.exit_code // "0"')
[[ "$EXIT_CODE" == "0" || "$EXIT_CODE" == "null" ]] && exit 0

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' | head -c 200)

# git/npm/mise の一般的な非ゼロ終了は無視（grep no match等）
if echo "$COMMAND" | grep -qE '^(grep|rg|find|test |diff )'; then
  exit 0
fi

LEARNINGS_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/work/learnings"
TODAY=$(date +%Y-%m-%d)

echo "{\"additionalContext\":\"ERROR DETECTED (exit $EXIT_CODE): ${COMMAND}\\n\\nNO PROCEEDING WITHOUT DOCUMENTATION. You MUST:\\n1. Spawn background agent: Task -> general-purpose, run_in_background: true\\n2. Agent writes to ${LEARNINGS_DIR}/${TODAY}-{topic}.md\\n3. Then continue main task.\"}"
exit 0
