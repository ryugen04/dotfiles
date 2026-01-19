#!/bin/bash

# SessionEnd hook: セッション終了時にトークン使用量を記録
# stdin: JSON {session_id, transcript_path, cwd, hook_event_name, reason}

CACHE_DIR="$HOME/.claude/cache"
USAGE_FILE="$CACHE_DIR/usage-history.json"
RECORDED_FILE="$CACHE_DIR/recorded-sessions.txt"

# キャッシュディレクトリ作成
mkdir -p "$CACHE_DIR"

# stdinからJSONを読み込み
INPUT=$(cat)

# transcript_pathを抽出
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')

# transcript_pathがない場合は終了
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# セッションIDがない場合はトランスクリプトファイル名をIDとして使用
if [ -z "$SESSION_ID" ]; then
    SESSION_ID=$(basename "$TRANSCRIPT_PATH")
fi

# 既に記録済みのセッションかチェック
if [ -f "$RECORDED_FILE" ] && grep -qxF "$SESSION_ID" "$RECORDED_FILE"; then
    exit 0
fi

# トランスクリプトからトークン使用量を集計
# .message.usage または .usage から取得
USAGE_DATA=$(jq -s '
    [.[] | select(.message.usage or .usage) | (.message.usage // .usage)]
    | {
        input_tokens: (map(.input_tokens // 0) | add // 0),
        output_tokens: (map(.output_tokens // 0) | add // 0),
        cache_read: (map(.cache_read_input_tokens // 0) | add // 0),
        cache_creation: (map(.cache_creation_input_tokens // 0) | add // 0)
    }
' "$TRANSCRIPT_PATH" 2>/dev/null)

if [ -z "$USAGE_DATA" ] || [ "$USAGE_DATA" = "null" ]; then
    exit 0
fi

# 今日の日付
TODAY=$(date +%Y-%m-%d)
NOW=$(date -Iseconds)

# 使用量ファイルがなければ初期化
if [ ! -f "$USAGE_FILE" ]; then
    echo '{"daily":{}}' > "$USAGE_FILE"
fi

# 使用量を追加
jq --arg date "$TODAY" \
   --arg now "$NOW" \
   --arg session_id "$SESSION_ID" \
   --argjson usage "$USAGE_DATA" '
    # 日次データを更新
    .daily[$date] = (
        (.daily[$date] // {input_tokens: 0, output_tokens: 0, cache_read: 0, cache_creation: 0})
        | {
            input_tokens: (.input_tokens + $usage.input_tokens),
            output_tokens: (.output_tokens + $usage.output_tokens),
            cache_read: (.cache_read + $usage.cache_read),
            cache_creation: (.cache_creation + $usage.cache_creation)
        }
    )
    # 14日より古いデータを削除（週次計算に7日必要 + バッファ）
    | .daily = (.daily | to_entries | map(select(.key >= ($date | strptime("%Y-%m-%d") | mktime - 14*86400 | strftime("%Y-%m-%d")))) | from_entries)
' "$USAGE_FILE" > "$USAGE_FILE.tmp" && mv "$USAGE_FILE.tmp" "$USAGE_FILE"

# セッションIDを記録済みリストに追加
echo "$SESSION_ID" >> "$RECORDED_FILE"

# 古いセッションID（14日以上前）を削除
if [ -f "$RECORDED_FILE" ]; then
    CUTOFF=$(date -v-14d +%s 2>/dev/null || date -d '14 days ago' +%s 2>/dev/null)
    if [ -n "$CUTOFF" ]; then
        # ファイルサイズが大きくなりすぎないよう、最新1000件のみ保持
        tail -1000 "$RECORDED_FILE" > "$RECORDED_FILE.tmp" && mv "$RECORDED_FILE.tmp" "$RECORDED_FILE"
    fi
fi
