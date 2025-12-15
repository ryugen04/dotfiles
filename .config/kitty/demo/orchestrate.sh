#!/bin/bash
# =============================================================================
# Multi-Server Orchestration Demo
# =============================================================================
# kitty Remote Control を使ったマルチサーバー開発環境の構築デモ
# ペイン分割で複数サーバーを起動し、別タブでログを監視
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
SERVERS_DIR="${SCRIPT_DIR}/servers"

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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
# Step 1: Serversタブを作成してペイン分割
# =============================================================================
setup_servers() {
    print_header "Step 1: Serversタブを作成してペイン分割"

    # ログディレクトリ作成
    mkdir -p "$LOG_DIR"

    # 既存のデモタブをクリーンアップ
    kitten @ close-tab -m title:Servers 2>/dev/null || true
    kitten @ close-tab -m title:Logs 2>/dev/null || true

    echo -e "${GREEN}[1/4]${NC} Serversタブを作成"
    kitten @ launch --type=tab --tab-title="Servers" --keep-focus
    kitten @ set-tab-color -m title:Servers active_bg=#3b82f6 active_fg=#ffffff
    sleep 0.5

    echo -e "${GREEN}[2/4]${NC} ペインを3分割"

    # Serversタブにフォーカスを移動
    kitten @ focus-tab -m title:Servers
    sleep 0.3

    # 最初のペイン（Frontend）のIDを取得してタイトル設定
    FRONTEND_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Servers") | .windows[0].id')
    kitten @ set-window-title -m id:$FRONTEND_ID "Frontend"

    # 縦に分割してBackendペインを作成
    kitten @ launch --location=vsplit --cwd=current
    sleep 0.3
    BACKEND_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Servers") | .windows[1].id')
    kitten @ set-window-title -m id:$BACKEND_ID "Backend"

    # さらに縦に分割してBFFペインを作成
    kitten @ launch --location=vsplit --cwd=current
    sleep 0.3
    BFF_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Servers") | .windows[2].id')
    kitten @ set-window-title -m id:$BFF_ID "BFF"

    echo -e "${GREEN}[3/4]${NC} 各ペインにタイトルを設定"
    echo "  - Frontend (id:$FRONTEND_ID)"
    echo "  - Backend  (id:$BACKEND_ID)"
    echo "  - BFF      (id:$BFF_ID)"

    echo -e "\n${GREEN}[4/4]${NC} Serversタブに3つのペインが作成されました"

    # 元のタブに戻る
    kitten @ focus-tab -m title:Orchestrate 2>/dev/null || kitten @ focus-tab -m index:0

    press_enter
}

# =============================================================================
# Step 2: 各ペインでサーバー起動
# =============================================================================
start_servers() {
    print_header "Step 2: 各ペインでサーバーを起動"

    echo -e "${CYAN}各ペインでEnterを押してシェルを初期化してください${NC}"
    echo "  1. Serversタブに移動（Ctrl+a → 数字）"
    echo "  2. 各ペインでEnterを押す（Ctrl+a → h/j/k/l で移動）"
    echo "  3. このタブに戻る"

    press_enter

    echo -e "${GREEN}サーバーを起動中...${NC}"

    # ペインタイトルでsend-text（フォアグラウンドで実行して画面にもログ表示）
    echo -e "${YELLOW}Frontend サーバーを起動 (port 9001)${NC}"
    kitten @ send-text -m title:Frontend $'python3 '"${SERVERS_DIR}"$'/frontend.py 2>&1 | tee '"${LOG_DIR}"$'/frontend.log\n'
    sleep 0.3

    echo -e "${YELLOW}Backend サーバーを起動 (port 9002)${NC}"
    kitten @ send-text -m title:Backend $'python3 '"${SERVERS_DIR}"$'/backend.py 2>&1 | tee '"${LOG_DIR}"$'/backend.log\n'
    sleep 0.3

    echo -e "${YELLOW}BFF サーバーを起動 (port 9003)${NC}"
    kitten @ send-text -m title:BFF $'python3 '"${SERVERS_DIR}"$'/bff.py 2>&1 | tee '"${LOG_DIR}"$'/bff.log\n'

    echo -e "\n${GREEN}3つのサーバーが起動しました${NC}"
    echo "  - Frontend: http://localhost:9001"
    echo "  - Backend:  http://localhost:9002"
    echo "  - BFF:      http://localhost:9003"

    press_enter
}

# =============================================================================
# Step 3: Logsタブでログ監視
# =============================================================================
setup_logs() {
    print_header "Step 3: Logsタブでログ監視"

    echo -e "${GREEN}Logsタブを作成${NC}"
    kitten @ launch --type=tab --tab-title="Logs" --keep-focus
    kitten @ set-tab-color -m title:Logs active_bg=#22c55e active_fg=#ffffff
    sleep 0.5

    # Logsタブ内のウィンドウにタイトルを設定
    LOGS_WIN_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Logs") | .windows[0].id')
    kitten @ set-window-title -m id:$LOGS_WIN_ID "LogViewer"

    echo -e "${CYAN}Logsタブでシェルを初期化してください${NC}"
    echo "  1. Logsタブに移動"
    echo "  2. Enterを押す"
    echo "  3. このタブに戻る"

    press_enter

    echo -e "${GREEN}ログ監視を開始${NC}"
    kitten @ send-text -m title:LogViewer $'echo "=== Combined Logs ==="\n'
    kitten @ send-text -m title:LogViewer $'tail -f '"${LOG_DIR}"$'/*.log 2>/dev/null || echo "Waiting for logs..."\n'

    echo -e "\n${GREEN}Logsタブでログを監視中${NC}"

    press_enter
}

# =============================================================================
# Step 4: テストリクエスト送信
# =============================================================================
test_requests() {
    print_header "Step 4: テストリクエストを送信"

    echo -e "${GREEN}ヘルスチェック${NC}"
    curl -s http://localhost:9001/health && echo "" || echo "  Frontend: Failed"
    curl -s http://localhost:9002/health && echo "" || echo "  Backend:  Failed"
    curl -s http://localhost:9003/health && echo "" || echo "  BFF:      Failed"

    echo -e "\n${GREEN}正常なリクエスト: /api/users/1 (Alice)${NC}"
    curl -s http://localhost:9001/api/users/1 | jq . 2>/dev/null || echo "Failed"

    echo -e "\n${YELLOW}エラーを発生させます: /api/users/2 (Bob)${NC}"
    curl -s http://localhost:9001/api/users/2 2>&1 || true

    echo -e "\n${CYAN}Serversタブでログを確認してください${NC}"

    press_enter
}

# =============================================================================
# Step 5: Analyzeタブでログ取得・AI分析
# =============================================================================
setup_analyze() {
    print_header "Step 5: Analyzeタブでログ取得・AI分析"

    echo -e "${GREEN}Analyzeタブを作成${NC}"
    kitten @ launch --type=tab --tab-title="Analyze" --keep-focus
    kitten @ set-tab-color -m title:Analyze active_bg=#a855f7 active_fg=#ffffff
    sleep 0.5

    # Analyzeタブ内のウィンドウにタイトルを設定
    ANALYZE_WIN_ID=$(kitten @ ls | jq -r '.[] | .tabs[] | select(.title=="Analyze") | .windows[0].id')
    kitten @ set-window-title -m id:$ANALYZE_WIN_ID "Analyzer"

    echo -e "${CYAN}Analyzeタブでシェルを初期化してください${NC}"
    echo "  1. Analyzeタブに移動"
    echo "  2. Enterを押す"
    echo "  3. このタブに戻る"

    press_enter

    echo -e "${GREEN}Backendのログを取得してファイルに保存${NC}"

    # ログ取得コマンドを送信
    kitten @ send-text -m title:Analyzer $'echo "=== Backendログを取得 ==="\n'
    kitten @ send-text -m title:Analyzer $'kitten @ get-text -m title:Backend > /tmp/backend_error.log\n'
    kitten @ send-text -m title:Analyzer $'echo ""\n'
    kitten @ send-text -m title:Analyzer $'echo "取得したログ（最後の20行）:"\n'
    kitten @ send-text -m title:Analyzer $'tail -20 /tmp/backend_error.log\n'

    sleep 1

    echo -e "\n${CYAN}AI分析の実行方法${NC}"
    echo ""
    echo "Analyzeタブで以下を実行:"
    echo ""
    echo "  # Claude Codeでログを分析"
    echo "  claude \"$(cat /tmp/backend_error.log)\" \\
    echo "    -p \"このログからエラーの原因と修正方法を分析してください\""
    echo ""
    echo "  # または直接ファイルを渡す"
    echo "  claude -f /tmp/backend_error.log \\
    echo "    -p \"エラーの原因と修正方法を分析してください\""

    press_enter
}

# =============================================================================
# Cleanup
# =============================================================================
cleanup() {
    print_header "Cleanup"

    echo "サーバーを停止中..."
    pkill -f "frontend.py" 2>/dev/null || true
    pkill -f "backend.py" 2>/dev/null || true
    pkill -f "bff.py" 2>/dev/null || true

    echo "タブを閉じる..."
    kitten @ close-tab -m title:Servers 2>/dev/null || true
    kitten @ close-tab -m title:Logs 2>/dev/null || true
    kitten @ close-tab -m title:Analyze 2>/dev/null || true

    echo -e "\n${GREEN}クリーンアップ完了${NC}"
}

# =============================================================================
# Main
# =============================================================================
case "${1:-help}" in
    setup)
        setup_servers
        ;;
    start)
        start_servers
        ;;
    logs)
        setup_logs
        ;;
    test)
        test_requests
        ;;
    analyze)
        setup_analyze
        ;;
    cleanup|clean)
        cleanup
        ;;
    all)
        print_header "Multi-Server Orchestration Demo"
        echo "このデモでは、kittyの Remote Control API を使って"
        echo "マルチサーバー開発環境を構築し、エラー解析を行います。"
        echo ""
        echo "構成:"
        echo "  ┌─────────────────────────────────────┐"
        echo "  │           Servers タブ               │"
        echo "  ├───────────┬───────────┬─────────────┤"
        echo "  │ Frontend  │  Backend  │    BFF      │"
        echo "  │  :9001    │   :9002   │   :9003     │"
        echo "  └───────────┴───────────┴─────────────┘"
        echo "  ┌───────────────────┬─────────────────┐"
        echo "  │    Logs タブ       │   Analyze タブ   │"
        echo "  │  tail -f *.log    │  ログ取得+AI分析 │"
        echo "  └───────────────────┴─────────────────┘"
        press_enter

        setup_servers
        start_servers
        setup_logs
        test_requests
        setup_analyze

        print_header "Demo Complete!"
        echo "Remote Control API で以下を実現しました:"
        echo "  - タブの動的作成・ペイン分割"
        echo "  - 各ペインへのコマンド送信"
        echo "  - ログの統合監視"
        echo "  - 別タブからのログ取得 (kitten @ get-text)"
        echo "  - AI分析への連携準備"
        echo ""
        echo "クリーンアップ: ./orchestrate.sh cleanup"
        ;;
    help|--help|-h)
        cat << 'EOF'
Multi-Server Orchestration Demo

Usage: orchestrate.sh <command>

Commands:
    setup     Serversタブを作成してペイン分割
    start     各ペインでサーバーを起動
    logs      Logsタブを作成してログ監視
    test      テストリクエストを送信
    analyze   Analyzeタブでログ取得・AI分析
    cleanup   全リソースを停止してクリーンアップ
    all       全ステップを順番に実行

EOF
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 [setup|start|logs|test|analyze|cleanup|all|help]"
        exit 1
        ;;
esac
