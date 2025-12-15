#!/bin/bash
# =============================================================================
# Remote Control Demo - kitty Terminal Protocol Demonstration
# =============================================================================
# 「端末がAPIを持つ」ことを実証するデモスクリプト
# 使用方法: bash rc_demo.sh [step]
# =============================================================================

set -e

# 色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# デモ用の待機時間（秒）
DELAY=1

print_header() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_step() {
    echo -e "${GREEN}[Step $1]${NC} $2"
}

print_command() {
    echo -e "${YELLOW}$ $1${NC}"
}

press_enter() {
    echo -e "\n${BLUE}[Enter]で続行...${NC}"
    read -r
}

# =============================================================================
# Demo Step 1: 現在の状態を確認
# =============================================================================
demo_step1() {
    print_header "Step 1: 端末の状態をAPIで取得"

    print_step 1 "現在のウィンドウ一覧を取得"
    print_command "kitten @ ls"
    echo ""
    kitten @ ls | head -50

    press_enter
}

# =============================================================================
# Demo Step 2: タブの動的生成
# =============================================================================
demo_step2() {
    print_header "Step 2: タブを動的に生成"

    print_step 2 "新しいタブを3つ作成（Control / Observe / Analyze）"

    echo -e "${YELLOW}# Control タブを作成${NC}"
    print_command "kitten @ launch --type=tab --tab-title='Control' --keep-focus"
    kitten @ launch --type=tab --tab-title="Control" --keep-focus
    sleep $DELAY

    echo -e "${YELLOW}# Observe タブを作成${NC}"
    print_command "kitten @ launch --type=tab --tab-title='Observe' --keep-focus"
    kitten @ launch --type=tab --tab-title="Observe" --keep-focus
    sleep $DELAY

    echo -e "${YELLOW}# Analyze タブを作成${NC}"
    print_command "kitten @ launch --type=tab --tab-title='Analyze' --keep-focus"
    kitten @ launch --type=tab --tab-title="Analyze" --keep-focus
    sleep $DELAY

    echo -e "\n${GREEN}3つのタブが作成されました${NC}"
    press_enter
}

# =============================================================================
# Demo Step 3: タブの色を動的に変更
# =============================================================================
demo_step3() {
    print_header "Step 3: タブの色をAPIで変更"

    print_step 3 "各タブに役割に応じた色を設定"

    echo -e "${YELLOW}# Control タブ → 青${NC}"
    print_command "kitten @ set-tab-color -m title:Control active_bg=#3b82f6"
    kitten @ set-tab-color -m title:Control active_bg=#3b82f6 active_fg=#ffffff
    sleep $DELAY

    echo -e "${YELLOW}# Observe タブ → 緑${NC}"
    print_command "kitten @ set-tab-color -m title:Observe active_bg=#22c55e"
    kitten @ set-tab-color -m title:Observe active_bg=#22c55e active_fg=#ffffff
    sleep $DELAY

    echo -e "${YELLOW}# Analyze タブ → 紫${NC}"
    print_command "kitten @ set-tab-color -m title:Analyze active_bg=#a855f7"
    kitten @ set-tab-color -m title:Analyze active_bg=#a855f7 active_fg=#ffffff
    sleep $DELAY

    echo -e "\n${GREEN}色が設定されました${NC}"
    press_enter
}

# =============================================================================
# Demo Step 4: フォーカスの移動
# =============================================================================
demo_step4() {
    print_header "Step 4: フォーカスをプログラムで移動"

    print_step 4 "各タブに順番にフォーカスを移動"

    echo -e "${YELLOW}# Control タブにフォーカス${NC}"
    print_command "kitten @ focus-tab -m title:Control"
    kitten @ focus-tab -m title:Control
    sleep $DELAY

    echo -e "${YELLOW}# Observe タブにフォーカス${NC}"
    print_command "kitten @ focus-tab -m title:Observe"
    kitten @ focus-tab -m title:Observe
    sleep $DELAY

    echo -e "${YELLOW}# Analyze タブにフォーカス${NC}"
    print_command "kitten @ focus-tab -m title:Analyze"
    kitten @ focus-tab -m title:Analyze
    sleep $DELAY

    # 元のタブに戻る（Demo）
    kitten @ focus-tab -m title:Demo 2>/dev/null || kitten @ focus-tab -m index:0

    echo -e "\n${GREEN}フォーカスがプログラムで制御されました${NC}"
    press_enter
}

# =============================================================================
# Demo Step 5: シェルの初期化を待つ
# =============================================================================
demo_step5() {
    print_header "Step 5: シェルの初期化"

    print_step 5 "各タブのシェルを初期化"

    echo -e "${CYAN}各タブでシェル（starship）が初期化されるのを待ちます。${NC}"
    echo ""
    echo "以下の手順を実行してください："
    echo "  1. Control / Observe / Analyze の各タブに移動"
    echo "  2. 各タブでEnterキーを押してプロンプトを表示"
    echo "  3. このDemoタブに戻る"
    echo ""
    echo -e "${YELLOW}ヒント: Ctrl+a → 数字キー でタブ移動できます${NC}"

    press_enter

    echo -e "${GREEN}シェルの初期化が完了しました${NC}"
}

# =============================================================================
# Demo Step 6: タブにコマンドを送信
# =============================================================================
demo_step6() {
    print_header "Step 6: 各タブにコマンドを送信"

    print_step 6 "各タブで異なるコマンドを実行"

    echo -e "${YELLOW}# Control タブにコマンド送信${NC}"
    print_command "kitten @ send-text --match-tab title:Control 'echo \"Control: System Ready\"'"
    kitten @ send-text --match-tab title:Control $'echo "Control: System Ready"\n'
    sleep $DELAY

    echo -e "${YELLOW}# Observe タブにコマンド送信${NC}"
    print_command "kitten @ send-text --match-tab title:Observe 'echo \"Observe: Monitoring...\"'"
    kitten @ send-text --match-tab title:Observe $'echo "Observe: Monitoring..."\n'
    sleep $DELAY

    echo -e "${YELLOW}# Analyze タブにコマンド送信${NC}"
    print_command "kitten @ send-text --match-tab title:Analyze 'echo \"Analyze: Ready for input\"'"
    kitten @ send-text --match-tab title:Analyze $'echo "Analyze: Ready for input"\n'
    sleep $DELAY

    echo -e "\n${GREEN}各タブでコマンドが実行されました${NC}"
    echo -e "${CYAN}各タブを確認してみてください！${NC}"
    press_enter
}

# =============================================================================
# Demo Step 7: クリーンアップ
# =============================================================================
demo_step7() {
    print_header "Step 7: クリーンアップ"

    print_step 7 "作成したタブを閉じる"

    echo -e "${YELLOW}# デモ用タブをすべて閉じる${NC}"

    # タブを閉じる（存在する場合のみ）
    kitten @ close-tab -m title:Control 2>/dev/null || true
    kitten @ close-tab -m title:Observe 2>/dev/null || true
    kitten @ close-tab -m title:Analyze 2>/dev/null || true

    echo -e "\n${GREEN}クリーンアップ完了${NC}"
}

# =============================================================================
# Main
# =============================================================================
main() {
    case "${1:-all}" in
        1) demo_step1 ;;
        2) demo_step2 ;;
        3) demo_step3 ;;
        4) demo_step4 ;;
        5) demo_step5 ;;
        6) demo_step6 ;;
        7|clean) demo_step7 ;;
        all)
            print_header "kitty Remote Control Demo"
            echo "このデモでは、kittyの Remote Control API を使って"
            echo "「端末がAPIを持つ」ことを実証します。"
            echo ""
            echo "デモ内容:"
            echo "  1. 端末の状態をAPIで取得"
            echo "  2. タブを動的に生成"
            echo "  3. タブの色をAPIで変更"
            echo "  4. フォーカスをプログラムで移動"
            echo "  5. シェルの初期化（手動）"
            echo "  6. 各タブにコマンドを送信"
            echo "  7. クリーンアップ"
            press_enter

            demo_step1
            demo_step2
            demo_step3
            demo_step4
            demo_step5
            demo_step6
            demo_step7

            print_header "Demo Complete!"
            echo "kittyは単なる端末エミュレータではなく、"
            echo "プログラムから制御可能な「Terminal API」を提供しています。"
            echo ""
            echo "これが Protocol-driven Terminal の一例です。"
            ;;
        *)
            echo "Usage: $0 [1-7|all|clean]"
            exit 1
            ;;
    esac
}

main "$@"
