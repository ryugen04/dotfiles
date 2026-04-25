#!/bin/bash
# Slack送信系ツールのチャンネル制限
# 許可チャンネルIDは環境変数で指定する（例: CLAUDE_ALLOWED_SLACK_CHANNEL_ID=C0123456789）

ALLOWED_CHANNEL_ID="${CLAUDE_ALLOWED_SLACK_CHANNEL_ID:-}"

# tool_input は環境変数 CLAUDE_TOOL_INPUT から取得
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

if [ -z "$TOOL_INPUT" ]; then
  exit 0
fi

if [ -z "$ALLOWED_CHANNEL_ID" ]; then
  # 未設定時はガードを無効化
  exit 0
fi

# channel_id を抽出
CHANNEL_ID=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('channel_id',''))" 2>/dev/null)

if [ -z "$CHANNEL_ID" ]; then
  exit 0
fi

if [ "$CHANNEL_ID" != "$ALLOWED_CHANNEL_ID" ]; then
  echo "BLOCKED: Slack投稿は許可された channel_id (${ALLOWED_CHANNEL_ID}) のみ許可されています。指定: ${CHANNEL_ID}"
  exit 2
fi

exit 0
