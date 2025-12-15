#!/bin/bash
# =============================================================================
# SSH Kitten Demo
# =============================================================================
# リモートでもフル機能 - Shell Integration、設定自動転送
#
# 参考: https://sw.kovidgoyal.net/kitty/kittens/ssh/
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
    print_header "SSH Kitten Demo"

    echo "SSH kittenは、リモートサーバーでもkittyの全機能を"
    echo "自動的に利用可能にする革命的な機能です。"
    echo ""
    echo "主な特徴:"
    echo -e "  ${GREEN}[1]${NC} Shell Integrationの自動有効化"
    echo -e "  ${GREEN}[2]${NC} ローカル設定のリモートへの自動転送"
    echo -e "  ${GREEN}[3]${NC} 接続の再利用（低レイテンシ）"
    echo -e "  ${GREEN}[4]${NC} リモートでのクリップボード連携"
    echo -e "  ${GREEN}[5]${NC} リモートでの画像表示"
    echo ""
    echo -e "${YELLOW}リモートサーバーにkittyがインストールされていなくても動作！${NC}"

    press_enter
}

# =============================================================================
# Step 2: 基本的な使い方
# =============================================================================
show_basic_usage() {
    print_header "Step 1: 基本的な使い方"

    echo "通常のSSH:"
    echo -e "  ${DIM}ssh user@server${NC}"
    echo ""
    echo "kitty SSH kitten:"
    echo -e "  ${CYAN}kitten ssh user@server${NC}"
    echo ""
    echo "違い:"
    echo ""
    echo -e "  ${RED}通常のSSH:${NC}"
    echo "    - Shell Integrationなし"
    echo "    - リモートでkittyの機能が使えない"
    echo "    - 画像表示不可"
    echo ""
    echo -e "  ${GREEN}SSH kitten:${NC}"
    echo "    - Shell Integration自動有効化"
    echo "    - ローカルと同じ体験"
    echo "    - Graphics Protocol対応"
    echo "    - クリップボード連携"

    press_enter
}

# =============================================================================
# Step 3: Shell Integration
# =============================================================================
show_shell_integration() {
    print_header "Step 2: Shell Integration on Remote"

    echo "SSH kittenで接続すると、以下の機能がリモートで自動的に有効化:"
    echo ""
    echo -e "${CYAN}[1] コマンド出力の視覚的区切り${NC}"
    echo "    各コマンドの出力が明確に区別される"
    echo ""
    echo -e "${CYAN}[2] 前のコマンドの出力にジャンプ${NC}"
    echo "    Ctrl+Shift+Z / Ctrl+Shift+X"
    echo ""
    echo -e "${CYAN}[3] 最後のコマンドの出力をクリップボードにコピー${NC}"
    echo "    kitten @ get-text --extent=last_cmd_output"
    echo ""
    echo -e "${CYAN}[4] CWDの追跡${NC}"
    echo "    新しいウィンドウが同じディレクトリで開く"
    echo ""
    echo -e "${CYAN}[5] コマンド通知${NC}"
    echo "    長時間コマンドの完了を通知"
    echo ""
    echo -e "${GREEN}これらは通常、リモートでは機能しません${NC}"

    press_enter
}

# =============================================================================
# Step 4: 設定の自動転送
# =============================================================================
show_config_transfer() {
    print_header "Step 3: 設定の自動転送"

    echo "SSH kittenは以下を自動的にリモートに転送:"
    echo ""
    echo -e "${CYAN}[1] 環境変数${NC}"
    echo "    TERM, COLORTERM, KITTY_* など"
    echo ""
    echo -e "${CYAN}[2] Shell設定${NC}"
    echo "    .bashrc, .zshrc の一部"
    echo ""
    echo -e "${CYAN}[3] カスタムファイル${NC}"
    echo "    ssh.conf で指定したファイル"
    echo ""
    echo "設定例 (~/.config/kitty/ssh.conf):"
    echo ""

    cat << 'EOF'
# 環境変数を転送
env EDITOR=nvim
env VISUAL=nvim

# ファイルを転送
copy ~/.config/nvim/init.lua .config/nvim/
copy ~/.tmux.conf

# シェルインテグレーション設定
shell_integration enabled
EOF

    echo ""
    echo -e "${YELLOW}リモートでもローカルと同じ環境で作業可能${NC}"

    press_enter
}

# =============================================================================
# Step 5: 接続の再利用
# =============================================================================
show_connection_reuse() {
    print_header "Step 4: 接続の再利用（ControlMaster）"

    echo "SSH kittenは自動的にSSH ControlMasterを使用します:"
    echo ""
    echo -e "${CYAN}[1] 初回接続${NC}"
    echo "    認証を行い、コントロールソケットを作成"
    echo ""
    echo -e "${CYAN}[2] 2回目以降${NC}"
    echo "    既存のソケットを再利用（即座に接続）"
    echo ""
    echo "メリット:"
    echo -e "  ${GREEN}✓${NC} パスワード/キーの再入力不要"
    echo -e "  ${GREEN}✓${NC} 接続時間が大幅に短縮"
    echo -e "  ${GREEN}✓${NC} 複数ウィンドウ/タブで同じ接続を共有"
    echo ""
    echo "kitty終了時に自動クリーンアップされます"

    press_enter
}

# =============================================================================
# Step 6: リモートクリップボード
# =============================================================================
show_remote_clipboard() {
    print_header "Step 5: リモートクリップボード"

    echo "SSH kitten経由で、リモートからローカルのクリップボードにアクセス:"
    echo ""
    echo -e "${CYAN}リモートからコピー:${NC}"
    echo "  echo 'Hello' | kitten clipboard"
    echo "  → ローカルのクリップボードにコピーされる"
    echo ""
    echo -e "${CYAN}リモートにペースト:${NC}"
    echo "  kitten clipboard --get-clipboard"
    echo "  → ローカルのクリップボードの内容を取得"
    echo ""
    echo -e "${CYAN}スクリプトでの使用:${NC}"
    echo '  cat /var/log/error.log | kitten clipboard'
    echo "  → リモートのログをローカルのクリップボードに"
    echo ""
    echo -e "${YELLOW}セキュアな方法でクリップボード共有${NC}"

    press_enter
}

# =============================================================================
# Step 7: リモートでの画像表示
# =============================================================================
show_remote_graphics() {
    print_header "Step 6: リモートでの画像表示"

    echo "SSH kitten経由で、リモートサーバーの画像を表示:"
    echo ""
    echo -e "${CYAN}画像を表示:${NC}"
    echo "  kitten icat /path/to/image.png"
    echo ""
    echo -e "${CYAN}URLから表示:${NC}"
    echo "  kitten icat https://example.com/image.png"
    echo ""
    echo -e "${CYAN}matplotlibグラフ:${NC}"
    echo "  MPLBACKEND=module://matplotlib-backend-kitty python3 script.py"
    echo ""
    echo "これにより:"
    echo -e "  ${GREEN}✓${NC} リモートサーバーのログをグラフ化して表示"
    echo -e "  ${GREEN}✓${NC} リモートの画像ファイルを直接確認"
    echo -e "  ${GREEN}✓${NC} Jupyter Notebookのような体験"
    echo ""
    echo -e "${RED}通常のSSHでは不可能な機能${NC}"

    press_enter
}

# =============================================================================
# Step 8: 他との比較
# =============================================================================
show_comparison() {
    print_header "Step 7: 他のターミナルとの比較"

    echo "SSH接続時の機能比較:"
    echo ""
    echo "┌─────────────────────┬────────┬─────────┬──────────┐"
    echo "│ 機能                │ kitty  │ WezTerm │ Ghostty  │"
    echo "├─────────────────────┼────────┼─────────┼──────────┤"
    echo "│ Shell Integration   │   ✓    │    △    │    △     │"
    echo "│ 設定自動転送        │   ✓    │    ✗    │    ✗     │"
    echo "│ 接続再利用          │   ✓    │    ✗    │    ✗     │"
    echo "│ リモートクリップ    │   ✓    │    ✗    │    ✗     │"
    echo "│ リモート画像表示    │   ✓    │    △    │    ✗     │"
    echo "│ 自動セットアップ    │   ✓    │    ✗    │    ✗     │"
    echo "└─────────────────────┴────────┴─────────┴──────────┘"
    echo ""
    echo -e "${DIM}✓ = フル対応, △ = 部分対応/手動設定要, ✗ = 非対応${NC}"
    echo ""
    echo -e "${MAGENTA}SSH kittenはリモートワークの体験を根本的に変えます${NC}"

    press_enter
}

# =============================================================================
# Step 9: デモ実行方法
# =============================================================================
show_demo_instructions() {
    print_header "Step 8: デモ実行方法"

    echo "実際に試すには、SSHアクセス可能なサーバーが必要です。"
    echo ""
    echo -e "${CYAN}ローカルでテスト（localhost）:${NC}"
    echo "  kitten ssh localhost"
    echo ""
    echo -e "${CYAN}リモートサーバーでテスト:${NC}"
    echo "  kitten ssh user@your-server.com"
    echo ""
    echo "接続後に試すこと:"
    echo ""
    echo "  1. シェルプロンプトの変化を確認"
    echo "  2. Ctrl+Shift+Z で前の出力にジャンプ"
    echo "  3. kitten icat /path/to/image.png で画像表示"
    echo "  4. echo 'test' | kitten clipboard でクリップボード"
    echo "  5. exit して再接続（即座に接続）"
    echo ""
    echo -e "${YELLOW}注意: このデモはSSHサーバーへのアクセスが必要です${NC}"

    press_enter
}

# =============================================================================
# Main
# =============================================================================
case "${1:-all}" in
    intro)
        show_intro
        ;;
    basic)
        show_basic_usage
        ;;
    shell)
        show_shell_integration
        ;;
    config)
        show_config_transfer
        ;;
    reuse)
        show_connection_reuse
        ;;
    clipboard)
        show_remote_clipboard
        ;;
    graphics)
        show_remote_graphics
        ;;
    compare)
        show_comparison
        ;;
    demo)
        show_demo_instructions
        ;;
    all)
        show_intro
        show_basic_usage
        show_shell_integration
        show_config_transfer
        show_connection_reuse
        show_remote_clipboard
        show_remote_graphics
        show_comparison
        show_demo_instructions

        print_header "Demo Complete!"
        echo "SSH kittenにより、以下が実現:"
        echo "  - リモートでもローカルと同じ体験"
        echo "  - Shell Integrationの自動有効化"
        echo "  - 設定・環境の自動転送"
        echo "  - 高速な接続再利用"
        echo "  - クリップボード・画像の連携"
        echo ""
        echo "詳細: https://sw.kovidgoyal.net/kitty/kittens/ssh/"
        ;;
    help|--help|-h)
        cat << 'EOF'
SSH Kitten Demo

Usage: ssh_demo.sh <command>

Commands:
    intro      SSH kittenの説明
    basic      基本的な使い方
    shell      Shell Integration
    config     設定の自動転送
    reuse      接続の再利用
    clipboard  リモートクリップボード
    graphics   リモートでの画像表示
    compare    他との比較
    demo       デモ実行方法
    all        全ステップを順番に実行

EOF
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 [intro|basic|shell|config|reuse|clipboard|graphics|compare|demo|all|help]"
        exit 1
        ;;
esac
