#!/bin/bash
# kitty_tab_color.sh - Claude Code入力待ち時のタブ色変更
#
# 使用法:
#   kitty_tab_color.sh alert  # 入力待ち: オレンジ色に変更
#   kitty_tab_color.sh reset  # 入力開始: 元の色に戻す

ACTION="${1:-alert}"

# KITTY_LISTEN_ON と KITTY_WINDOW_ID が必要
if [[ -z "$KITTY_LISTEN_ON" ]] || [[ -z "$KITTY_WINDOW_ID" ]]; then
    exit 0
fi

case "$ACTION" in
    alert)
        # 入力待ち: タブをオレンジ色に（active/inactive両方）
        kitten @ --to "$KITTY_LISTEN_ON" --password "claude-dev" \
            set-tab-color --match "window_id:$KITTY_WINDOW_ID" \
            active_bg='#ff6600' inactive_bg='#cc5500' 2>/dev/null
        ;;
    reset)
        # 入力開始: 元の色に戻す
        kitten @ --to "$KITTY_LISTEN_ON" --password "claude-dev" \
            set-tab-color --match "window_id:$KITTY_WINDOW_ID" \
            active_bg=none inactive_bg=none 2>/dev/null
        ;;
esac

exit 0
