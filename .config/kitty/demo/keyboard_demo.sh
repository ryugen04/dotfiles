#!/bin/bash
# =============================================================================
# Keyboard Protocol Demo
# =============================================================================
# 従来のターミナルで失われる入力情報と、kitty Keyboard Protocol の違いを実証
#
# 参考: https://sw.kovidgoyal.net/kitty/keyboard-protocol/
# =============================================================================

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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
# Part 1: 従来のターミナルの問題
# =============================================================================
show_legacy_problem() {
    print_header "従来のターミナルの問題: 入力情報の欠落"

    echo "従来のターミナルでは、以下の入力を区別できません:"
    echo ""
    echo -e "  ${RED}区別不可${NC}: Ctrl+I と Tab"
    echo -e "  ${RED}区別不可${NC}: Ctrl+M と Enter"
    echo -e "  ${RED}区別不可${NC}: Ctrl+[ と Escape"
    echo -e "  ${RED}区別不可${NC}: Ctrl+Shift+A と Ctrl+a"
    echo ""
    echo "これは、1970年代のASCII制御コードに由来する制約です。"
    echo "端末はキー入力をASCIIバイトに変換するため、修飾キー情報が失われます。"

    press_enter
}

# =============================================================================
# Part 2: Keyboard Protocol の解決策
# =============================================================================
show_keyboard_protocol() {
    print_header "kitty Keyboard Protocol の解決策"

    echo "kittyの Keyboard Protocol は以下の情報を提供します:"
    echo ""
    echo -e "  ${GREEN}[1]${NC} キーの物理的識別子 (key code)"
    echo -e "  ${GREEN}[2]${NC} 修飾キーの完全な状態 (Shift, Ctrl, Alt, Super)"
    echo -e "  ${GREEN}[3]${NC} イベントタイプ (press, repeat, release)"
    echo -e "  ${GREEN}[4]${NC} 関連テキスト (入力された文字)"
    echo ""
    echo "これにより、以下が実現可能になります:"
    echo ""
    echo -e "  - ${CYAN}Ctrl+Shift+P${NC} と ${CYAN}Ctrl+p${NC} を区別"
    echo -e "  - ${CYAN}キーリリース${NC} イベントの検出"
    echo -e "  - ${CYAN}複数の修飾キー${NC} の同時押し検出"

    press_enter
}

# =============================================================================
# Part 3: デモ - キー入力の可視化
# =============================================================================
demo_key_input() {
    print_header "デモ: キー入力情報の可視化"

    echo "キー入力を可視化するデモを起動します。"
    echo "キーを押すと、受信した情報が表示されます。"
    echo ""
    echo -e "${YELLOW}Ctrl+C で終了${NC}"

    press_enter

    # 別ファイルのスクリプトを実行
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    python3 "${SCRIPT_DIR}/key_visualizer.py"
}

# =============================================================================
# Part 4: Keyboard Protocol の有効化方法
# =============================================================================
show_how_to_enable() {
    print_header "Keyboard Protocol の有効化方法"

    echo "アプリケーションは以下のエスケープシーケンスでプロトコルを有効化します:"
    echo ""
    echo -e "  ${YELLOW}有効化${NC}: \\033[>1u  (Progressive enhancement mode)"
    echo -e "  ${YELLOW}無効化${NC}: \\033[<1u"
    echo ""
    echo "対応アプリケーション:"
    echo -e "  - Neovim (0.9+)"
    echo -e "  - Kakoune"
    echo -e "  - fish shell"
    echo -e "  - kitty 内蔵エディタ"
    echo ""
    echo "参考: https://sw.kovidgoyal.net/kitty/keyboard-protocol/"

    press_enter
}

# =============================================================================
# Main
# =============================================================================
main() {
    case "${1:-all}" in
        problem)
            show_legacy_problem
            ;;
        protocol)
            show_keyboard_protocol
            ;;
        demo)
            demo_key_input
            ;;
        enable)
            show_how_to_enable
            ;;
        all)
            print_header "Keyboard Protocol Demo"
            echo "このデモでは、従来のターミナルの入力制約と"
            echo "kitty Keyboard Protocol による解決策を説明します。"
            press_enter

            show_legacy_problem
            show_keyboard_protocol
            demo_key_input
            show_how_to_enable

            print_header "Demo Complete!"
            echo "Keyboard Protocol により、モダンなキー入力処理が可能になります。"
            echo ""
            echo "これは tmux や他の端末では実現できない kitty の強みの一つです。"
            ;;
        *)
            echo "Usage: $0 [problem|protocol|demo|enable|all]"
            exit 1
            ;;
    esac
}

main "$@"
