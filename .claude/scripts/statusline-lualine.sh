#!/bin/bash

# Lualine風ステータスライン for Claude Code
# 参考: https://github.com/spences10/claude-statusline-powerline
# starshipの配色を使用

# ANSIコード
RESET=$'\x1b[0m'

# 24ビットカラー（starship準拠）
# #769ff0 = RGB(118, 159, 240) - パス用
BG_PATH=$'\x1b[48;2;118;159;240m'
FG_PATH=$'\x1b[38;2;118;159;240m'

# #394260 = RGB(57, 66, 96) - ブランチ用
BG_BRANCH=$'\x1b[48;2;57;66;96m'
FG_BRANCH=$'\x1b[38;2;57;66;96m'

# #2d3545 = RGB(45, 53, 69) - モデル用（ブランチより暗め、背景より明るく）
BG_MODEL=$'\x1b[48;2;45;53;69m'

# テキスト色
FG_WHITE=$'\x1b[38;2;227;229;229m'
# #a0a9cb = RGB(160, 169, 203) - モデル部分用（starshipの時刻色）
FG_MODEL_TEXT=$'\x1b[38;2;160;169;203m'

# Powerlineセパレーター（python3経由でUnicode生成 - macOS bash 3.2対応）
SEP_RIGHT=$(python3 -c "print('\ue0b0', end='')")

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
# cache_read_input_tokensが現在のコンテキストサイズに近い
COMPACT_MAX=200000
CONTEXT_CURRENT=0
if [ -f "$TRANSCRIPT_PATH" ]; then
    # 最後のcache_read_input_tokensを取得
    CONTEXT_CURRENT=$(tail -10 "$TRANSCRIPT_PATH" 2>/dev/null | grep -o '"cache_read_input_tokens":[0-9]*' | tail -1 | cut -d':' -f2)
fi
CONTEXT_CURRENT=${CONTEXT_CURRENT:-0}
CONTEXT_PCT=$((CONTEXT_CURRENT * 100 / COMPACT_MAX))

# ステータスライン組み立て
OUTPUT=""

# === 左側: [パス]>[ブランチ]>[モデル]< ===

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

# セグメント3: モデル + コンテキスト使用量（#2d3545）
OUTPUT+="${BG_MODEL}${FG_MODEL_TEXT} ${SHORT_MODEL}(${CONTEXT_PCT}%) ${RESET}"

# 出力
printf '%s\n' "$OUTPUT"
