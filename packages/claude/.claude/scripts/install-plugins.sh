#!/usr/bin/env bash
# Claude Code プラグインインストールスクリプト
# 使用法: ~/.claude/scripts/install-plugins.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/plugins.yaml"
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

echo "=== マーケットプレイスを追加 ==="
echo ""

# マーケットプレイス数を取得
marketplace_count=$(yq '.marketplaces | length' "$CONFIG_FILE")

for i in $(seq 0 $((marketplace_count - 1))); do
    name=$(yq ".marketplaces[$i].name" "$CONFIG_FILE")
    repo=$(yq ".marketplaces[$i].repo" "$CONFIG_FILE")

    echo "[$name]"
    echo "  リポジトリ: $repo"

    if [[ "$DRY_RUN" == "false" ]]; then
        claude plugin marketplace add "$repo" 2>/dev/null && \
            echo "  ステータス: 追加完了" || \
            echo "  ステータス: 既存または追加済み"
    else
        echo "  ステータス: ドライラン（スキップ）"
    fi
    echo ""
done

echo "=== プラグインをインストール ==="
echo ""

# プラグイン数を取得
plugin_count=$(yq '.plugins | length' "$CONFIG_FILE")

for i in $(seq 0 $((plugin_count - 1))); do
    name=$(yq ".plugins[$i].name" "$CONFIG_FILE")
    marketplace=$(yq ".plugins[$i].marketplace" "$CONFIG_FILE")
    description=$(yq ".plugins[$i].description // \"\"" "$CONFIG_FILE")

    plugin_spec="${name}@${marketplace}"

    echo "[$name]"
    echo "  マーケットプレイス: $marketplace"
    echo "  説明: $description"

    if [[ "$DRY_RUN" == "false" ]]; then
        claude plugin install "$plugin_spec" 2>/dev/null && \
            echo "  ステータス: インストール完了" || \
            echo "  ステータス: 既存またはエラー"
    else
        echo "  ステータス: ドライラン（スキップ）"
    fi
    echo ""
done

echo "=== 完了 ==="
echo ""
echo "変更を反映するにはClaude Codeを再起動してください"
