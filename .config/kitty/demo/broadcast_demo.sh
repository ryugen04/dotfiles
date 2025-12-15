#!/bin/bash
# =============================================================================
# Broadcast Kitten Demo
# =============================================================================
# 複数サーバーに同時コマンド送信 - 運用現場で即使える機能
#
# 参考: https://sw.kovidgoyal.net/kitty/kittens/broadcast/
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
    print_header "Broadcast Kitten Demo"

    echo "Broadcast kittenは、1つのウィンドウで入力したテキストを"
    echo "複数のkittyウィンドウに同時に送信する機能です。"
    echo ""
    echo "ユースケース:"
    echo -e "  ${GREEN}[1]${NC} 複数サーバーへの同時コマンド実行"
    echo -e "  ${GREEN}[2]${NC} 複数環境での同時設定変更"
    echo -e "  ${GREEN}[3]${NC} クラスタ全体のヘルスチェック"
    echo -e "  ${GREEN}[4]${NC} 同時デプロイ・ローリングアップデート"
    echo ""
    echo -e "${YELLOW}tmuxのsynchronize-panesに相当しますが、より柔軟です${NC}"

    press_enter
}

# =============================================================================
# Step 2: サーバーペインのセットアップ
# =============================================================================
setup_server_panes() {
    print_header "Step 1: サーバーペインをセットアップ"

    # 既存のデモタブをクリーンアップ
    kitten @ close-tab -m title:Broadcast 2>/dev/null || true

    echo -e "${GREEN}[1/3]${NC} Broadcastタブを作成"
    kitten @ launch --type=tab --tab-title="Broadcast" --keep-focus
    kitten @ set-tab-color -m title:Broadcast active_bg=#8b5cf6 active_fg=#ffffff
    sleep 0.5

    # Broadcastタブにフォーカスを移動
    kitten @ focus-tab -m title:Broadcast
    sleep 0.3

    # 最初のペイン（Server1）のIDを取得してタイトル設定
    SERVER1_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Broadcast") | .windows[0].id')
    kitten @ set-window-title -m id:$SERVER1_ID "Server1"

    echo -e "${GREEN}[2/3]${NC} ペインを3分割"

    # 縦に分割してServer2ペインを作成
    kitten @ launch --location=vsplit --cwd=current
    sleep 0.3
    SERVER2_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Broadcast") | .windows[1].id')
    kitten @ set-window-title -m id:$SERVER2_ID "Server2"

    # さらに縦に分割してServer3ペインを作成
    kitten @ launch --location=vsplit --cwd=current
    sleep 0.3
    SERVER3_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Broadcast") | .windows[2].id')
    kitten @ set-window-title -m id:$SERVER3_ID "Server3"

    echo -e "${GREEN}[3/3]${NC} 各ペインを初期化"

    # 各ペインでプロンプトを設定（サーバー名を表示）
    kitten @ send-text -m title:Server1 $'export PS1="[Server1] $ "\n'
    kitten @ send-text -m title:Server2 $'export PS1="[Server2] $ "\n'
    kitten @ send-text -m title:Server3 $'export PS1="[Server3] $ "\n'

    sleep 0.5

    # 元のタブに戻る
    kitten @ focus-tab -m index:0 2>/dev/null || true

    echo ""
    echo -e "${GREEN}3つのサーバーペインが作成されました${NC}"
    echo "  - Server1"
    echo "  - Server2"
    echo "  - Server3"

    press_enter
}

# =============================================================================
# Step 3: Broadcastモードの説明
# =============================================================================
explain_broadcast() {
    print_header "Step 2: Broadcast モードの使い方"

    echo "Broadcast kittenを起動する方法:"
    echo ""
    echo -e "  ${CYAN}方法1: キーマッピング${NC}"
    echo "    kitty.conf に以下を追加:"
    echo -e "    ${YELLOW}map f1 launch --allow-remote-control kitty +kitten broadcast${NC}"
    echo ""
    echo -e "  ${CYAN}方法2: コマンドラインから${NC}"
    echo -e "    ${YELLOW}kitty +kitten broadcast${NC}"
    echo ""
    echo -e "  ${CYAN}方法3: 特定タブのみにブロードキャスト${NC}"
    echo -e "    ${YELLOW}kitty +kitten broadcast --match-tab state:focused${NC}"
    echo ""
    echo "主要なオプション:"
    echo -e "  ${GREEN}--match, -m${NC}      ウィンドウを絞り込む"
    echo -e "  ${GREEN}--match-tab, -t${NC}  タブを絞り込む"
    echo -e "  ${GREEN}--end-session${NC}    終了キー（デフォルト: Ctrl+Esc）"
    echo ""

    press_enter
}

# =============================================================================
# Step 4: 実際にBroadcastを実行
# =============================================================================
demo_broadcast() {
    print_header "Step 3: Broadcastデモ - 同時コマンド実行"

    echo "Broadcastタブに移動して、以下を試してください:"
    echo ""
    echo -e "  ${CYAN}1. Broadcastを起動${NC}"
    echo "     新しいターミナルで: kitty +kitten broadcast --match-tab title:Broadcast"
    echo ""
    echo -e "  ${CYAN}2. コマンドを入力${NC}"
    echo "     入力したコマンドが3つのペインすべてに送信されます"
    echo ""
    echo "試すコマンド例:"
    echo -e "  ${YELLOW}hostname${NC}        # 各サーバーの名前を確認"
    echo -e "  ${YELLOW}date${NC}            # 時刻の同期確認"
    echo -e "  ${YELLOW}uptime${NC}          # 稼働時間確認"
    echo -e "  ${YELLOW}df -h${NC}           # ディスク使用量"
    echo -e "  ${YELLOW}free -h${NC}         # メモリ使用量"
    echo ""
    echo -e "${GREEN}終了: Ctrl+Esc${NC}"
    echo ""

    echo -e "${MAGENTA}自動デモ: Remote Controlで同時送信を実演${NC}"

    press_enter

    # Remote Controlを使って同時にコマンドを送信（Broadcastの代替デモ）
    echo -e "${GREEN}全サーバーに 'echo Server Ready' を送信...${NC}"
    kitten @ send-text -m title:Server1 $'echo "Server1 Ready"\n'
    kitten @ send-text -m title:Server2 $'echo "Server2 Ready"\n'
    kitten @ send-text -m title:Server3 $'echo "Server3 Ready"\n'

    sleep 1

    echo -e "${GREEN}全サーバーに 'date' を送信...${NC}"
    kitten @ send-text -m title:Server1 $'date\n'
    kitten @ send-text -m title:Server2 $'date\n'
    kitten @ send-text -m title:Server3 $'date\n'

    sleep 1

    echo -e "${GREEN}全サーバーに 'uptime' を送信...${NC}"
    kitten @ send-text -m title:Server1 $'uptime\n'
    kitten @ send-text -m title:Server2 $'uptime\n'
    kitten @ send-text -m title:Server3 $'uptime\n'

    echo ""
    echo -e "${YELLOW}Broadcastタブを確認してください - 全ペインで同じコマンドが実行されています${NC}"

    press_enter
}

# =============================================================================
# Step 5: 実用的なシナリオ
# =============================================================================
show_scenarios() {
    print_header "Step 4: 実用的なシナリオ"

    echo "Broadcast kittenの実運用シナリオ:"
    echo ""
    echo -e "${CYAN}[シナリオ1] クラスタ全体のログ確認${NC}"
    echo "  全サーバーで同時に: tail -f /var/log/app.log"
    echo ""
    echo -e "${CYAN}[シナリオ2] 設定ファイルの同時編集${NC}"
    echo "  全サーバーで同時に: vim /etc/app/config.yaml"
    echo "  (同じ編集操作が全サーバーに適用)"
    echo ""
    echo -e "${CYAN}[シナリオ3] サービス再起動${NC}"
    echo "  全サーバーで同時に: sudo systemctl restart nginx"
    echo ""
    echo -e "${CYAN}[シナリオ4] パッケージアップデート${NC}"
    echo "  全サーバーで同時に: sudo apt update && sudo apt upgrade -y"
    echo ""
    echo -e "${GREEN}重要: tmuxと違い、kittyは特定のペインだけを対象にできます${NC}"
    echo "  --match 'title:prod-*' でprodサーバーのみ"
    echo "  --match 'title:staging-*' でstagingサーバーのみ"

    press_enter
}

# =============================================================================
# Cleanup
# =============================================================================
cleanup() {
    print_header "Cleanup"

    echo "デモタブを閉じる..."
    kitten @ close-tab -m title:Broadcast 2>/dev/null || true

    echo -e "\n${GREEN}クリーンアップ完了${NC}"
}

# =============================================================================
# Main
# =============================================================================
case "${1:-all}" in
    intro)
        show_intro
        ;;
    setup)
        setup_server_panes
        ;;
    explain)
        explain_broadcast
        ;;
    demo)
        demo_broadcast
        ;;
    scenarios)
        show_scenarios
        ;;
    cleanup|clean)
        cleanup
        ;;
    all)
        show_intro
        setup_server_panes
        explain_broadcast
        demo_broadcast
        show_scenarios

        print_header "Demo Complete!"
        echo "Broadcast kittenにより、以下が実現可能:"
        echo "  - 複数サーバーへの同時コマンド送信"
        echo "  - 柔軟なウィンドウ/タブのターゲティング"
        echo "  - 運用作業の大幅な効率化"
        echo ""
        echo "クリーンアップ: ./broadcast_demo.sh cleanup"
        ;;
    help|--help|-h)
        cat << 'EOF'
Broadcast Kitten Demo

Usage: broadcast_demo.sh <command>

Commands:
    intro      Broadcast kittenの説明
    setup      サーバーペインをセットアップ
    explain    使い方の説明
    demo       実際のデモ実行
    scenarios  実用的なシナリオ紹介
    cleanup    クリーンアップ
    all        全ステップを順番に実行

EOF
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 [intro|setup|explain|demo|scenarios|cleanup|all|help]"
        exit 1
        ;;
esac
