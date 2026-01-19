#!/bin/bash

# Lualine風ステータスライン for Claude Code
# 参考: https://github.com/spences10/claude-statusline-powerline
# starshipの配色を使用

# === 制限値設定（/usageの表示に合わせて調整） ===
DAILY_LIMIT=33000000    # 日次: 33M tokens（推定）
WEEKLY_LIMIT=51000000   # 週次: 51M tokens（推定）
COMPACT_LIMIT=200000    # Auto compact: 200K tokens

# === キャッシュ設定 ===
CACHE_DIR="$HOME/.claude/cache"
CACHE_FILE="$CACHE_DIR/statusline-tokens.cache"
CACHE_TTL=300  # 5分

# ANSIコード
RESET=$'\x1b[0m'

# 24ビットカラー（starship準拠）
# #769ff0 = RGB(118, 159, 240) - パス用
BG_PATH=$'\x1b[48;2;118;159;240m'
FG_PATH=$'\x1b[38;2;118;159;240m'

# #394260 = RGB(57, 66, 96) - ブランチ用
BG_BRANCH=$'\x1b[48;2;57;66;96m'
FG_BRANCH=$'\x1b[38;2;57;66;96m'

# #2d3545 = RGB(45, 53, 69) - モデル用
BG_MODEL=$'\x1b[48;2;45;53;69m'
FG_MODEL=$'\x1b[38;2;45;53;69m'

# 週次セグメント（紫系）#4f3d5f
BG_WEEKLY=$'\x1b[48;2;79;61;95m'
FG_WEEKLY=$'\x1b[38;2;79;61;95m'

# 日次セグメント（青緑系）#3d4f5f
BG_DAILY=$'\x1b[48;2;61;79;95m'
FG_DAILY=$'\x1b[38;2;61;79;95m'

# Ctxセグメント（緑系）#2d453d
BG_CTX=$'\x1b[48;2;45;69;61m'
FG_CTX=$'\x1b[38;2;45;69;61m'

# テキスト色
FG_WHITE=$'\x1b[38;2;227;229;229m'
# #a0a9cb = RGB(160, 169, 203) - モデル部分用
FG_MODEL_TEXT=$'\x1b[38;2;160;169;203m'

# Powerlineセパレーター（python3経由でUnicode生成 - macOS bash 3.2対応）
SEP_RIGHT=$(python3 -c "print('\ue0b0', end='')")

# 丸いキャップ
CAP_LEFT=$(python3 -c "print('\ue0b6', end='')")
CAP_RIGHT=$(python3 -c "print('\ue0b4', end='')")

# Nerd Fontアイコン（python3経由でUnicode生成）
ICON_FOLDER=$(python3 -c "print('\uf07b', end='')")
ICON_BRANCH=$(python3 -c "print('\ue0a0', end='')")

# JSONデータを読み込む
INPUT=$(cat)

# データ抽出
CWD=$(echo "$INPUT" | jq -r '.workspace.current_dir')
MODEL_NAME=$(echo "$INPUT" | jq -r '.model.display_name')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path')

# ホームディレクトリからの相対パス
HOME_DIR="$HOME"
if [[ "$CWD" == "$HOME_DIR"* ]]; then
    REL_PATH="~${CWD#$HOME_DIR}"
else
    REL_PATH="$CWD"
fi

# Git情報取得
GIT_BRANCH=""
GIT_STATUS=""
if git -C "$CWD" rev-parse --git-dir > /dev/null 2>&1; then
    GIT_BRANCH=$(git -C "$CWD" --no-optional-locks branch --show-current 2>/dev/null)

    # ステータス取得
    STAGED=$(git -C "$CWD" --no-optional-locks diff --cached --name-only 2>/dev/null | wc -l)
    MODIFIED=$(git -C "$CWD" --no-optional-locks diff --name-only 2>/dev/null | wc -l)
    UNTRACKED=$(git -C "$CWD" --no-optional-locks ls-files --others --exclude-standard 2>/dev/null | wc -l)

    # ahead/behind
    AHEAD=$(git -C "$CWD" --no-optional-locks rev-list --count @{upstream}..HEAD 2>/dev/null || echo 0)
    BEHIND=$(git -C "$CWD" --no-optional-locks rev-list --count HEAD..@{upstream} 2>/dev/null || echo 0)

    # ステータス文字列構築（記号のみ）
    [ "$STAGED" -gt 0 ] && GIT_STATUS+="+"
    [ "$MODIFIED" -gt 0 ] && GIT_STATUS+="!"
    [ "$UNTRACKED" -gt 0 ] && GIT_STATUS+="?"
    [ "$AHEAD" -gt 0 ] && GIT_STATUS+="⇡"
    [ "$BEHIND" -gt 0 ] && GIT_STATUS+="⇣"
    [ -n "$GIT_STATUS" ] && GIT_STATUS=" ${GIT_STATUS}"
fi

# モデル名短縮
case "$MODEL_NAME" in
    *Sonnet*) SHORT_MODEL="Sonnet" ;;
    *Opus*)   SHORT_MODEL="Opus" ;;
    *Haiku*)  SHORT_MODEL="Haiku" ;;
    *)        SHORT_MODEL="Claude" ;;
esac

# コンテキスト使用量（auto-compact用）
CONTEXT_CURRENT=0
if [ -f "$TRANSCRIPT_PATH" ]; then
    CONTEXT_CURRENT=$(tail -10 "$TRANSCRIPT_PATH" 2>/dev/null | grep -o '"cache_read_input_tokens":[0-9]*' | tail -1 | cut -d':' -f2)
fi
CONTEXT_CURRENT=${CONTEXT_CURRENT:-0}

# === トランスクリプトからトークン使用量を取得（キャッシュ付き） ===
mkdir -p "$CACHE_DIR"

# キャッシュが有効か確認
CACHE_VALID=false
if [ -f "$CACHE_FILE" ]; then
    CACHE_AGE=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [ "$CACHE_AGE" -lt "$CACHE_TTL" ]; then
        CACHE_VALID=true
    fi
fi

if [ "$CACHE_VALID" = true ]; then
    # キャッシュから読み込み
    DAILY_TOKENS=$(sed -n '1p' "$CACHE_FILE")
    WEEKLY_TOKENS=$(sed -n '2p' "$CACHE_FILE")
else
    # トランスクリプトから計算
    TODAY=$(date +%Y-%m-%d)

    # 週の開始日を計算（Linux/macOS両対応）
    if date --version >/dev/null 2>&1; then
        WEEK_START=$(date -d '6 days ago' +%Y-%m-%d)
    else
        WEEK_START=$(date -v-6d +%Y-%m-%d)
    fi

    # 日次トークン計算
    DAILY_TOKENS=0
    while IFS= read -r file; do
        tokens=$(grep -oE '"(input_tokens|output_tokens)":[0-9]+' "$file" 2>/dev/null | grep -oE '[0-9]+$' | awk '{sum+=$1} END {print sum+0}')
        DAILY_TOKENS=$((DAILY_TOKENS + tokens))
    done < <(find "$HOME/.claude/projects" -name "*.jsonl" -type f -newermt "$TODAY" 2>/dev/null)

    # 週次トークン計算
    WEEKLY_TOKENS=0
    while IFS= read -r file; do
        tokens=$(grep -oE '"(input_tokens|output_tokens)":[0-9]+' "$file" 2>/dev/null | grep -oE '[0-9]+$' | awk '{sum+=$1} END {print sum+0}')
        WEEKLY_TOKENS=$((WEEKLY_TOKENS + tokens))
    done < <(find "$HOME/.claude/projects" -name "*.jsonl" -type f -newermt "$WEEK_START" 2>/dev/null)

    # キャッシュに保存
    echo "$DAILY_TOKENS" > "$CACHE_FILE"
    echo "$WEEKLY_TOKENS" >> "$CACHE_FILE"
fi

DAILY_TOKENS=${DAILY_TOKENS:-0}
WEEKLY_TOKENS=${WEEKLY_TOKENS:-0}

# %計算
DAILY_PCT=$((DAILY_TOKENS * 100 / DAILY_LIMIT))
WEEKLY_PCT=$((WEEKLY_TOKENS * 100 / WEEKLY_LIMIT))
CTX_PCT=$((CONTEXT_CURRENT * 100 / COMPACT_LIMIT))

# ステータスライン組み立て
OUTPUT=""

# === [左丸][パス]>[ブランチ]>[モデル]>[週: Y%]>[日: X%]>[Ctx: Z%][右丸] ===

# 左端: 丸い開始キャップ
OUTPUT+="${FG_PATH}${CAP_LEFT}${RESET}"

# セグメント1: パス（#769ff0）
OUTPUT+="${BG_PATH}${FG_WHITE} ${ICON_FOLDER} ${REL_PATH} "

if [ -n "$GIT_BRANCH" ]; then
    # セパレーター: パス → ブランチ
    OUTPUT+="${BG_BRANCH}${FG_PATH}${SEP_RIGHT}${RESET}"

    # セグメント2: ブランチ（#394260）
    OUTPUT+="${BG_BRANCH}${FG_PATH} ${ICON_BRANCH} ${GIT_BRANCH}${GIT_STATUS} "

    # セパレーター: ブランチ → モデル
    OUTPUT+="${BG_MODEL}${FG_BRANCH}${SEP_RIGHT}${RESET}"
else
    # セパレーター: パス → モデル（ブランチなし）
    OUTPUT+="${BG_MODEL}${FG_PATH}${SEP_RIGHT}${RESET}"
fi

# セグメント3: モデル（#2d3545）
OUTPUT+="${BG_MODEL}${FG_MODEL_TEXT} ${SHORT_MODEL} "

# セパレーター: モデル → 週次
OUTPUT+="${BG_WEEKLY}${FG_MODEL}${SEP_RIGHT}${RESET}"

# セグメント4: 週次（#4f3d5f）
OUTPUT+="${BG_WEEKLY}${FG_WHITE} W:${WEEKLY_PCT}% "

# セパレーター: 週次 → 日次
OUTPUT+="${BG_DAILY}${FG_WEEKLY}${SEP_RIGHT}${RESET}"

# セグメント5: 日次（#3d4f5f）
OUTPUT+="${BG_DAILY}${FG_WHITE} D:${DAILY_PCT}% "

# セパレーター: 日次 → Ctx
OUTPUT+="${BG_CTX}${FG_DAILY}${SEP_RIGHT}${RESET}"

# セグメント6: Ctx（#2d453d）
OUTPUT+="${BG_CTX}${FG_WHITE} Ctx:${CTX_PCT}% "

# 右端: 丸い終了キャップ
OUTPUT+="${RESET}${FG_CTX}${CAP_RIGHT}${RESET}"

# 出力
printf '%s\n' "$OUTPUT"
