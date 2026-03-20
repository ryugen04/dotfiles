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

# #2d3545 = RGB(45, 53, 69) - モデル用
BG_MODEL=$'\x1b[48;2;45;53;69m'
FG_MODEL=$'\x1b[38;2;45;53;69m'

# Ctxセグメント（緑系）#2d453d
BG_CTX=$'\x1b[48;2;45;69;61m'
FG_CTX=$'\x1b[38;2;45;69;61m'

# Usageセグメント（使用率で動的に切り替え）
# 緑: #2d453d / 黄: #6b5b00 / オレンジ: #5b4a2d / 赤: #5b2d2d
# #3a4a5a = RGB(58, 74, 90) - Ctxと区別できるブルーグレー
BG_USAGE_GREEN=$'\x1b[48;2;58;74;90m'
FG_USAGE_GREEN=$'\x1b[38;2;58;74;90m'
BG_USAGE_YELLOW=$'\x1b[48;2;107;91;0m'
FG_USAGE_YELLOW=$'\x1b[38;2;107;91;0m'
BG_USAGE_ORANGE=$'\x1b[48;2;91;74;45m'
FG_USAGE_ORANGE=$'\x1b[38;2;91;74;45m'
BG_USAGE_RED=$'\x1b[48;2;91;45;45m'
FG_USAGE_RED=$'\x1b[38;2;91;45;45m'

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

# 使用率に応じたBG/FGカラーを返す
usage_color() {
    local pct=${1:-0}
    if [ "$pct" -ge 90 ] 2>/dev/null; then
        BG_USAGE="$BG_USAGE_RED"; FG_USAGE="$FG_USAGE_RED"
    elif [ "$pct" -ge 70 ] 2>/dev/null; then
        BG_USAGE="$BG_USAGE_ORANGE"; FG_USAGE="$FG_USAGE_ORANGE"
    elif [ "$pct" -ge 50 ] 2>/dev/null; then
        BG_USAGE="$BG_USAGE_YELLOW"; FG_USAGE="$FG_USAGE_YELLOW"
    else
        BG_USAGE="$BG_USAGE_GREEN"; FG_USAGE="$FG_USAGE_GREEN"
    fi
}

# JSONデータを読み込む
INPUT=$(cat)

# データ抽出
CWD=$(echo "$INPUT" | jq -r '.workspace.current_dir')
MODEL_NAME=$(echo "$INPUT" | jq -r '.model.display_name')

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

# コンテキスト使用率（stdin JSONから取得）
CTX_PCT=$(echo "$INPUT" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
CTX_PCT=${CTX_PCT:-0}

# ステータスライン組み立て
OUTPUT=""

# === [左丸][パス]>[ブランチ]>[モデル]>[Ctx: Z%][右丸] ===

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

# セパレーター: モデル → Ctx
OUTPUT+="${BG_CTX}${FG_MODEL}${SEP_RIGHT}${RESET}"

# セグメント4: Ctx（#2d453d）
OUTPUT+="${BG_CTX}${FG_WHITE} Ctx:${CTX_PCT}% "

# セグメント5: Usage（使用率で色が変わる、stdin JSONから取得）
FIVE_HOUR_PCT=$(echo "$INPUT" | jq -r '.rate_limits["5h"].used_percentage // 0' | cut -d. -f1)
SEVEN_DAY_PCT=$(echo "$INPUT" | jq -r '.rate_limits["7d"].used_percentage // 0' | cut -d. -f1)
FIVE_HOUR_PCT=${FIVE_HOUR_PCT:-0}
SEVEN_DAY_PCT=${SEVEN_DAY_PCT:-0}

# 高い方の使用率で色を決定
MAX_PCT=$FIVE_HOUR_PCT
[ "$SEVEN_DAY_PCT" -gt "$MAX_PCT" ] 2>/dev/null && MAX_PCT=$SEVEN_DAY_PCT
usage_color "$MAX_PCT"

# セパレーター: Ctx → Usage
OUTPUT+="${BG_USAGE}${FG_CTX}${SEP_RIGHT}${RESET}"

# Usage表示
OUTPUT+="${BG_USAGE}${FG_WHITE} 5h:${FIVE_HOUR_PCT}% 7d:${SEVEN_DAY_PCT}% "

# 右端: 丸い終了キャップ
OUTPUT+="${RESET}${FG_USAGE}${CAP_RIGHT}${RESET}"

# 出力
printf '%s\n' "$OUTPUT"
