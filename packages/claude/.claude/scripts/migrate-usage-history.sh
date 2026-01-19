#!/bin/bash

# 過去のトランスクリプトから使用量履歴を生成するマイグレーションスクリプト
# 一度だけ実行する

CACHE_DIR="$HOME/.claude/cache"
USAGE_FILE="$CACHE_DIR/usage-history.json"
RECORDED_FILE="$CACHE_DIR/recorded-sessions.txt"
PROJECTS_DIR="$HOME/.claude/projects"

# キャッシュディレクトリ作成
mkdir -p "$CACHE_DIR"

# 初期化
echo '{"daily":{}}' > "$USAGE_FILE"
: > "$RECORDED_FILE"

echo "過去14日分のトランスクリプトを処理中..."

# 14日前の日付
if date --version >/dev/null 2>&1; then
    CUTOFF_DATE=$(date -d '14 days ago' +%Y-%m-%d)
else
    CUTOFF_DATE=$(date -v-14d +%Y-%m-%d)
fi

# トランスクリプトを日付でソートして処理
find "$PROJECTS_DIR" -name "*.jsonl" -type f 2>/dev/null | while read -r file; do
    # ファイルの最初のタイムスタンプを取得して日付を特定
    FILE_DATE=$(head -1 "$file" 2>/dev/null | jq -r '.timestamp // empty' 2>/dev/null | cut -d'T' -f1)

    if [ -z "$FILE_DATE" ]; then
        # タイムスタンプがない場合はファイルの更新日を使用
        if stat --version >/dev/null 2>&1; then
            FILE_DATE=$(stat -c %Y "$file" | xargs -I{} date -d @{} +%Y-%m-%d 2>/dev/null)
        else
            FILE_DATE=$(stat -f %m "$file" | xargs -I{} date -r {} +%Y-%m-%d 2>/dev/null)
        fi
    fi

    # 14日以上前のファイルはスキップ
    if [ -n "$FILE_DATE" ] && [[ "$FILE_DATE" < "$CUTOFF_DATE" ]]; then
        continue
    fi

    FILE_DATE=${FILE_DATE:-$(date +%Y-%m-%d)}

    # トークン使用量を集計
    USAGE_DATA=$(jq -s '
        [.[] | select(.message.usage or .usage) | (.message.usage // .usage)]
        | {
            input_tokens: (map(.input_tokens // 0) | add // 0),
            output_tokens: (map(.output_tokens // 0) | add // 0),
            cache_read: (map(.cache_read_input_tokens // 0) | add // 0),
            cache_creation: (map(.cache_creation_input_tokens // 0) | add // 0)
        }
    ' "$file" 2>/dev/null)

    if [ -z "$USAGE_DATA" ] || [ "$USAGE_DATA" = "null" ]; then
        continue
    fi

    # 使用量を追加
    jq --arg date "$FILE_DATE" \
       --argjson usage "$USAGE_DATA" '
        .daily[$date] = (
            (.daily[$date] // {input_tokens: 0, output_tokens: 0, cache_read: 0, cache_creation: 0})
            | {
                input_tokens: (.input_tokens + $usage.input_tokens),
                output_tokens: (.output_tokens + $usage.output_tokens),
                cache_read: (.cache_read + $usage.cache_read),
                cache_creation: (.cache_creation + $usage.cache_creation)
            }
        )
    ' "$USAGE_FILE" > "$USAGE_FILE.tmp" && mv "$USAGE_FILE.tmp" "$USAGE_FILE"

    # セッションIDを記録
    echo "$(basename "$file")" >> "$RECORDED_FILE"

    echo "  処理: $FILE_DATE - $(basename "$file")"
done

echo ""
echo "移行完了:"
jq . "$USAGE_FILE"
