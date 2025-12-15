#!/bin/bash
# =============================================================================
# Hints Kitten Demo
# =============================================================================
# 画面から何でも選択 - URL、ファイルパス、行番号、カスタムパターン
#
# 参考: https://sw.kovidgoyal.net/kitty/kittens/hints/
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

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
    print_header "Hints Kitten Demo"

    echo "Hints kittenは、画面に表示されているテキストを"
    echo "キーボードだけで選択・操作できる強力な機能です。"
    echo ""
    echo "主な用途:"
    echo -e "  ${GREEN}[1]${NC} URL をブラウザで開く"
    echo -e "  ${GREEN}[2]${NC} ファイルパスをエディタで開く"
    echo -e "  ${GREEN}[3]${NC} 行番号付きパスで該当行にジャンプ"
    echo -e "  ${GREEN}[4]${NC} 単語・ハッシュ・IPアドレス等を選択"
    echo -e "  ${GREEN}[5]${NC} カスタム正規表現で何でも選択"
    echo ""
    echo -e "${YELLOW}マウスを使わずにターミナルを操作できます${NC}"

    press_enter
}

# =============================================================================
# Step 2: デフォルトのキーマッピング
# =============================================================================
show_keymaps() {
    print_header "Step 1: Hints キーバインド"

    echo "このdotfilesでは以下のHintsショートカットが設定されています:"
    echo ""
    echo -e "  ${CYAN}(Ctrl+a h u)${NC}  URLを選択してブラウザで開く"
    echo -e "  ${CYAN}(Ctrl+a h f)${NC}  ファイルパスを選択して挿入"
    echo -e "  ${CYAN}(Ctrl+a h n)${NC}  行番号付きパスを選択（エディタで開く）"
    echo -e "  ${CYAN}(Ctrl+a h y)${NC}  ハイパーリンクを選択して開く"
    echo -e "  ${CYAN}(Ctrl+a h w)${NC}  単語を選択して挿入"
    echo -e "  ${CYAN}(Ctrl+a h g)${NC}  Git hash を選択してコピー"
    echo -e "  ${CYAN}(Ctrl+a h l)${NC}  行を選択して挿入"
    echo -e "  ${CYAN}(Ctrl+a h i)${NC}  IPアドレスを選択してコピー"
    echo ""
    echo -e "${DIM}Ctrl+a → h → 機能キー の順に押します${NC}"

    press_enter
}

# =============================================================================
# Step 3: URLの選択デモ
# =============================================================================
demo_url_hints() {
    print_header "Step 2: URL選択デモ"

    echo "以下のURLが画面に表示されています:"
    echo ""
    echo -e "  ${YELLOW}https://sw.kovidgoyal.net/kitty/${NC}"
    echo -e "  ${YELLOW}https://github.com/kovidgoyal/kitty${NC}"
    echo -e "  ${YELLOW}https://sw.kovidgoyal.net/kitty/kittens/hints/${NC}"
    echo ""
    echo "操作方法:"
    echo -e "  1. ${CYAN}(Ctrl+a h u)${NC} を押す"
    echo "  2. 各URLに文字ラベル(a, b, c...)が表示される"
    echo "  3. 開きたいURLのラベルを入力"
    echo "  4. ブラウザでURLが開く"
    echo ""
    echo -e "${GREEN}試してみてください！${NC}"

    press_enter
}

# =============================================================================
# Step 4: ファイルパス選択デモ
# =============================================================================
demo_path_hints() {
    print_header "Step 3: ファイルパス選択デモ"

    echo "以下のファイルパスが画面に表示されています:"
    echo ""
    echo -e "  ${YELLOW}/home/user/.config/kitty/kitty.conf${NC}"
    echo -e "  ${YELLOW}./src/main.py${NC}"
    echo -e "  ${YELLOW}~/Documents/notes.md${NC}"
    echo -e "  ${YELLOW}../README.md${NC}"
    echo ""
    echo "操作方法:"
    echo -e "  1. ${CYAN}(Ctrl+a h f)${NC} を押す"
    echo "  2. 各パスに文字ラベルが表示される"
    echo "  3. 選択するとプロンプトにパスが挿入される"
    echo ""
    echo -e "${DIM}エディタで開く場合は 'program' オプションで設定${NC}"

    press_enter
}

# =============================================================================
# Step 5: 行番号付きパス（エラーログ解析）
# =============================================================================
demo_linenum_hints() {
    print_header "Step 4: 行番号付きパス - エラーログ解析"

    echo "以下のエラーログが表示されています:"
    echo ""
    echo -e "  ${RED}Traceback (most recent call last):${NC}"
    echo -e "    File ${YELLOW}\"/app/src/main.py\"${NC}, line ${CYAN}42${NC}, in process_data"
    echo "      result = data['key'] / count"
    echo -e "    File ${YELLOW}\"/app/src/utils.py\"${NC}, line ${CYAN}15${NC}, in validate"
    echo "      raise ValueError('Invalid input')"
    echo -e "  ${RED}ZeroDivisionError: division by zero${NC}"
    echo ""
    echo "操作方法:"
    echo -e "  1. ${CYAN}(Ctrl+a h n)${NC} を押す"
    echo "  2. 'main.py:42' や 'utils.py:15' にラベルが表示される"
    echo "  3. 選択するとエディタで該当行が開く"
    echo ""
    echo -e "${GREEN}スタックトレースから直接ソースにジャンプ！${NC}"

    press_enter
}

# =============================================================================
# Step 6: カスタムHints
# =============================================================================
demo_custom_hints() {
    print_header "Step 5: カスタムHints"

    echo "Hintsは正規表現でカスタマイズ可能です:"
    echo ""
    echo -e "${CYAN}例1: Git commit ハッシュを選択${NC}"
    echo "  kitten hints --type=regex --regex='[a-f0-9]{7,40}'"
    echo ""
    echo "  Commits: abc1234, def5678, 0123456789abcdef"
    echo ""
    echo -e "${CYAN}例2: IPアドレスを選択${NC}"
    echo "  kitten hints --type=regex --regex='\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}'"
    echo ""
    echo "  Servers: 192.168.1.100, 10.0.0.1, 172.16.0.50"
    echo ""
    echo -e "${CYAN}例3: Docker コンテナIDを選択${NC}"
    echo "  kitten hints --type=regex --regex='[a-f0-9]{12}'"
    echo ""
    echo "  Containers: abc123def456, 789012345678"
    echo ""

    press_enter
}

# =============================================================================
# Step 7: 設定例
# =============================================================================
show_config() {
    print_header "Step 6: kitty.conf 設定例"

    echo "kitty.confに追加できるカスタムHints:"
    echo ""

    cat << 'EOF'
# Git commit hashを選択してコピー
map ctrl+shift+g kitten hints --type=regex \
    --regex='[a-f0-9]{7,40}' --program=@

# IPアドレスを選択してコピー
map ctrl+shift+i kitten hints --type=regex \
    --regex='\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' --program=@

# Docker IDを選択してコピー
map ctrl+shift+d kitten hints --type=regex \
    --regex='[a-f0-9]{12}' --program=@

# ファイルパスをnvimで開く
map ctrl+shift+o kitten hints --type=path \
    --program="launch --type=tab nvim"

# 行番号付きパスをnvimで開く（該当行へ）
map ctrl+shift+n kitten hints --type=linenum \
    --linenum-action=self
EOF

    echo ""
    echo -e "${DIM}--program=@ はクリップボードにコピー${NC}"
    echo -e "${DIM}--program=- はプロンプトに挿入${NC}"

    press_enter
}

# =============================================================================
# Step 8: 実際に試す
# =============================================================================
live_demo() {
    print_header "Step 7: 実際に試す"

    echo "以下のテキストでHintsを試してください:"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "URLs:"
    echo "  https://github.com/kovidgoyal/kitty"
    echo "  https://sw.kovidgoyal.net/kitty/kittens/hints/"
    echo ""
    echo "File paths:"
    echo "  /etc/hosts"
    echo "  ~/.config/kitty/kitty.conf"
    echo "  ./Makefile"
    echo ""
    echo "Error log:"
    echo '  File "/app/main.py", line 42, in main'
    echo '  File "/app/utils.py", line 15, in helper'
    echo ""
    echo "Git commits:"
    echo "  abc1234 fix: bug fix"
    echo "  def5678 feat: new feature"
    echo ""
    echo "IP addresses:"
    echo "  192.168.1.1  10.0.0.1  172.16.0.100"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}試してみましょう:${NC}"
    echo -e "  ${CYAN}(Ctrl+a h u)${NC}  → URL選択"
    echo -e "  ${CYAN}(Ctrl+a h f)${NC}  → パス選択"
    echo -e "  ${CYAN}(Ctrl+a h n)${NC}  → 行番号付きパス"
    echo -e "  ${CYAN}(Ctrl+a h g)${NC}  → Git hash"
    echo -e "  ${CYAN}(Ctrl+a h i)${NC}  → IPアドレス"

    press_enter
}

# =============================================================================
# Main
# =============================================================================
case "${1:-all}" in
    intro)
        show_intro
        ;;
    keymaps)
        show_keymaps
        ;;
    url)
        demo_url_hints
        ;;
    path)
        demo_path_hints
        ;;
    linenum)
        demo_linenum_hints
        ;;
    custom)
        demo_custom_hints
        ;;
    config)
        show_config
        ;;
    live)
        live_demo
        ;;
    all)
        show_intro
        show_keymaps
        demo_url_hints
        demo_path_hints
        demo_linenum_hints
        demo_custom_hints
        show_config
        live_demo

        print_header "Demo Complete!"
        echo "Hints kittenにより、以下が実現:"
        echo "  - マウスを使わずにURLを開く"
        echo "  - エラーログから直接ソースにジャンプ"
        echo "  - Git hashやIPアドレスを素早く選択"
        echo "  - カスタム正規表現で何でも選択"
        echo ""
        echo "詳細: https://sw.kovidgoyal.net/kitty/kittens/hints/"
        ;;
    help|--help|-h)
        cat << 'EOF'
Hints Kitten Demo

Usage: hints_demo.sh <command>

Commands:
    intro     Hints kittenの説明
    keymaps   デフォルトのキーマッピング
    url       URL選択デモ
    path      ファイルパス選択デモ
    linenum   行番号付きパスデモ
    custom    カスタムHints
    config    設定例
    live      実際に試す
    all       全ステップを順番に実行

EOF
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 [intro|keymaps|url|path|linenum|custom|config|live|all|help]"
        exit 1
        ;;
esac
