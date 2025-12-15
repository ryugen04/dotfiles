#!/bin/bash
# =============================================================================
# Cursor Trail Demo
# =============================================================================
# kitty 0.37+ の視覚的効果 - neovideからインスパイアされたカーソルアニメーション
#
# 参考: https://sw.kovidgoyal.net/kitty/conf/#cursor-trail
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KITTY_CONF="${HOME}/.config/kitty/kitty.conf"

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

print_header() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

press_enter() {
    echo -e "\n${BLUE}[Enter]で続行...${NC}"
    read -r
}

# =============================================================================
# Step 1: 説明
# =============================================================================
show_intro() {
    print_header "Cursor Trail Demo"

    echo "Cursor Trailは、kitty 0.37で追加された視覚的効果です。"
    echo "neovideからインスパイアされたこの機能は、カーソルが"
    echo "大きく移動した際にアニメーション効果を表示します。"
    echo ""
    echo "効果:"
    echo -e "  ${GREEN}[1]${NC} カーソルが「ズーム」して移動するように見える"
    echo -e "  ${GREEN}[2]${NC} 大きなジャンプ時にカーソルを見失わない"
    echo -e "  ${GREEN}[3]${NC} エディタでの快適な編集体験"
    echo ""
    echo -e "${YELLOW}この機能は他のターミナルにはありません${NC}"
    echo -e "${DIM}(Ghosttyで要望されているが、まだ実装されていない)${NC}"

    press_enter
}

# =============================================================================
# Step 2: 設定オプションの説明
# =============================================================================
show_config_options() {
    print_header "Step 1: 設定オプション"

    echo "kitty.conf で設定可能なオプション:"
    echo ""
    echo -e "${CYAN}cursor_trail${NC} <milliseconds>"
    echo "  トレイルを開始するまでの待機時間（ミリ秒）"
    echo "  0 = 無効、10-100 = 推奨値"
    echo ""
    echo -e "${CYAN}cursor_trail_decay${NC} <min> <max>"
    echo "  トレイルの減衰時間（秒）"
    echo "  例: 0.1 0.3 = 速い減衰"
    echo "  例: 0.2 0.5 = 遅い減衰（長い尾）"
    echo ""
    echo -e "${CYAN}cursor_trail_start_threshold${NC} <cells>"
    echo "  トレイルを開始する最小移動セル数"
    echo "  小さい移動ではトレイルを表示しない"
    echo ""
    echo -e "${CYAN}cursor_trail_color${NC} <color>"
    echo "  トレイルの色（none = カーソル色を使用）"
    echo "  例: #ff6600 = オレンジ"
    echo ""

    press_enter
}

# =============================================================================
# Step 3: 現在の設定を確認
# =============================================================================
check_current_config() {
    print_header "Step 2: 現在の設定を確認"

    echo "現在のkitty.confの cursor_trail 設定:"
    echo ""

    if [ -f "$KITTY_CONF" ]; then
        if grep -q "cursor_trail" "$KITTY_CONF" 2>/dev/null; then
            grep "cursor_trail" "$KITTY_CONF" | while read -r line; do
                # コメント行はスキップ
                if [[ ! "$line" =~ ^[[:space:]]*# ]]; then
                    echo -e "  ${GREEN}✓ $line${NC}"
                fi
            done
            echo ""
            echo -e "  ${YELLOW}設定が見つかりました！${NC}"
            echo -e "  ${DIM}設定を反映するには kitty の再起動が必要です${NC}"
            echo ""
            echo -e "  再起動方法:"
            echo -e "    ${CYAN}1. 現在のkittyウィンドウを閉じる${NC}"
            echo -e "    ${CYAN}2. 新しいkittyを起動する${NC}"
            echo ""
            echo -e "  または、以下のコマンドで再読み込み（一部設定のみ）:"
            echo -e "    ${CYAN}kitty @ load-config${NC}"
        else
            echo -e "  ${RED}✗ cursor_trail 設定が見つかりません${NC}"
            echo ""
            echo -e "  以下の設定を kitty.conf に追加してください:"
            echo -e "    ${CYAN}cursor_trail 3${NC}"
            echo -e "    ${CYAN}cursor_trail_decay 0.1 0.4${NC}"
            echo -e "    ${CYAN}cursor_trail_start_threshold 2${NC}"
        fi
    else
        echo -e "  ${RED}kitty.conf が見つかりません${NC}"
    fi

    echo ""

    press_enter
}

# =============================================================================
# Step 4: デモ用設定を適用
# =============================================================================
apply_demo_config() {
    print_header "Step 3: デモ用設定を適用"

    echo "以下の設定を適用してCursor Trailを有効化します:"
    echo ""
    echo -e "  ${YELLOW}cursor_trail 10${NC}"
    echo -e "  ${YELLOW}cursor_trail_decay 0.1 0.4${NC}"
    echo -e "  ${YELLOW}cursor_trail_start_threshold 3${NC}"
    echo ""

    # kittyのset-user-varsを使って動的に設定（残念ながらcursor_trailは動的変更不可）
    echo -e "${RED}注意: cursor_trail は動的に変更できません${NC}"
    echo "kitty.conf を編集して、kittyを再起動する必要があります。"
    echo ""
    echo "設定例をクリップボードにコピーしますか？"

    press_enter

    # 設定例を表示
    cat << 'EOF'
# =============================================================================
# Cursor Trail 設定 (kitty.conf に追加)
# =============================================================================

# カーソルトレイルを有効化（10ミリ秒待機後にトレイル開始）
cursor_trail 10

# 減衰時間（最小0.1秒、最大0.4秒）
cursor_trail_decay 0.1 0.4

# 3セル以上の移動でトレイルを表示
cursor_trail_start_threshold 3

# トレイルの色（none = カーソル色を使用）
# cursor_trail_color none
# cursor_trail_color #ff6600  # オレンジ
EOF

    echo ""
    echo -e "${GREEN}上記の設定を ~/.config/kitty/kitty.conf に追加してください${NC}"

    press_enter
}

# =============================================================================
# Step 5: 効果を体験
# =============================================================================
demo_cursor_trail() {
    print_header "Step 4: Cursor Trail を体験"

    echo "Cursor Trailが有効な状態で、以下の操作を試してください:"
    echo ""
    echo -e "${CYAN}[1] Vim/Neovim で大きなジャンプ${NC}"
    echo "    - gg (ファイル先頭へ)"
    echo "    - G (ファイル末尾へ)"
    echo "    - 100G (100行目へ)"
    echo "    - Ctrl+d / Ctrl+u (半ページスクロール)"
    echo ""
    echo -e "${CYAN}[2] シェルでの操作${NC}"
    echo "    - Ctrl+a (行頭へ)"
    echo "    - Ctrl+e (行末へ)"
    echo "    - Alt+f / Alt+b (単語移動)"
    echo ""
    echo -e "${CYAN}[3] less/man でのスクロール${NC}"
    echo "    - Space (次のページ)"
    echo "    - b (前のページ)"
    echo "    - g / G (先頭/末尾)"
    echo ""

    press_enter

    # デモ用のテキストを表示して、カーソル移動を促す
    echo "以下の長いテキストでカーソル移動を試してください:"
    echo ""

    for i in {1..30}; do
        printf "%3d: This is line %d - Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n" "$i" "$i"
    done

    echo ""
    echo -e "${YELLOW}上下に素早くスクロールして、カーソルのトレイル効果を確認${NC}"
    echo -e "${DIM}(cursor_trailが有効な場合のみ表示されます)${NC}"

    press_enter
}

# =============================================================================
# Step 6: 比較
# =============================================================================
show_comparison() {
    print_header "Step 5: 他のターミナルとの比較"

    echo "Cursor Trail対応状況:"
    echo ""
    echo -e "  ${GREEN}kitty 0.37+${NC}     ✓ ネイティブ対応"
    echo -e "  ${YELLOW}Ghostty${NC}         ✗ 要望あり、未実装"
    echo -e "  ${RED}Alacritty${NC}       ✗ 対応なし"
    echo -e "  ${RED}WezTerm${NC}         ✗ 対応なし"
    echo -e "  ${RED}iTerm2${NC}          ✗ 対応なし"
    echo ""
    echo "類似機能:"
    echo -e "  ${CYAN}neovide${NC}         カーソルアニメーション（kittyの元ネタ）"
    echo -e "  ${CYAN}VS Code${NC}         smooth caret animation（GUI限定）"
    echo ""
    echo -e "${MAGENTA}ターミナルレベルでのカーソルアニメーションはkitty独自${NC}"

    press_enter
}

# =============================================================================
# Main
# =============================================================================
case "${1:-all}" in
    intro)
        show_intro
        ;;
    config)
        show_config_options
        ;;
    check)
        check_current_config
        ;;
    apply)
        apply_demo_config
        ;;
    demo)
        demo_cursor_trail
        ;;
    compare)
        show_comparison
        ;;
    all)
        show_intro
        show_config_options
        check_current_config
        apply_demo_config
        demo_cursor_trail
        show_comparison

        print_header "Demo Complete!"
        echo "Cursor Trailにより、以下が実現:"
        echo "  - カーソルの視覚的な追跡が容易に"
        echo "  - 大きなジャンプ時の位置把握"
        echo "  - より快適な編集体験"
        echo ""
        echo "設定を有効にするには、kitty.confを編集して再起動してください。"
        ;;
    help|--help|-h)
        cat << 'EOF'
Cursor Trail Demo

Usage: cursor_trail_demo.sh <command>

Commands:
    intro     Cursor Trailの説明
    config    設定オプションの説明
    check     現在の設定を確認
    apply     デモ用設定の説明
    demo      効果を体験
    compare   他のターミナルとの比較
    all       全ステップを順番に実行

EOF
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 [intro|config|check|apply|demo|compare|all|help]"
        exit 1
        ;;
esac
