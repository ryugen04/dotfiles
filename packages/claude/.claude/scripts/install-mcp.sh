#!/usr/bin/env bash
# Claude Code MCP サーバーインストールスクリプト
# 使用法: ~/.claude/scripts/install-mcp.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/mcp-servers.yaml"
DRY_RUN=false

# 引数解析
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

# yqの確認
if ! command -v yq &>/dev/null; then
    echo "エラー: yqがインストールされていません"
    echo "mise install を実行してください"
    exit 1
fi

# 設定ファイルの確認
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "エラー: 設定ファイルが見つかりません: $CONFIG_FILE"
    exit 1
fi

echo "MCPサーバーをインストールします..."
echo ""

# サーバー数を取得
server_count=$(yq '.servers | length' "$CONFIG_FILE")

for i in $(seq 0 $((server_count - 1))); do
    name=$(yq ".servers[$i].name" "$CONFIG_FILE")
    command=$(yq ".servers[$i].command" "$CONFIG_FILE")

    # argsを配列として取得
    args=()
    args_count=$(yq ".servers[$i].args | length" "$CONFIG_FILE")
    for j in $(seq 0 $((args_count - 1))); do
        arg=$(yq ".servers[$i].args[$j]" "$CONFIG_FILE")
        args+=("$arg")
    done

    # envを取得（存在する場合）
    env_str=""
    if [[ $(yq ".servers[$i].env // null" "$CONFIG_FILE") != "null" ]]; then
        while read -r key; do
            value=$(yq ".servers[$i].env.$key" "$CONFIG_FILE")
            env_str+=" env $key=$value"
        done < <(yq ".servers[$i].env | keys | .[]" "$CONFIG_FILE")
    fi

    # コマンド構築
    cmd="claude mcp add $name -s user${env_str} -- $command ${args[*]}"

    echo "[$name]"
    echo "  コマンド: $cmd"

    if [[ "$DRY_RUN" == "false" ]]; then
        # 既存のサーバーを削除（存在する場合）
        claude mcp remove "$name" -s user 2>/dev/null || true
        # 新しいサーバーを追加
        eval "$cmd" && echo "  ステータス: インストール完了" || echo "  ステータス: エラー"
    else
        echo "  ステータス: ドライラン（スキップ）"
    fi
    echo ""
done

echo "完了しました"
