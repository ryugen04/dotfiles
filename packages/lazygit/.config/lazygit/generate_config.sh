#!/bin/bash
# lazygit設定ファイルを生成するスクリプト
# OSに応じてmodifier keyを切り替える

# OS判定
if [[ "$OSTYPE" == "darwin"* ]]; then
  MOD_KEY="<command>"
else
  MOD_KEY="<c>"
fi

# 設定ファイルのテンプレートから実際の設定を生成
CONFIG_DIR="$(dirname "$0")"
TEMPLATE="${CONFIG_DIR}/config.yml.template"
OUTPUT="${CONFIG_DIR}/config.yml"

# テンプレートが存在しない場合は既存のconfig.ymlをテンプレート化
if [ ! -f "$TEMPLATE" ]; then
  if [ -f "$OUTPUT" ]; then
    cp "$OUTPUT" "$TEMPLATE"
  fi
fi

# {{MOD_KEY}}を実際のmodifier keyに置換
sed "s/{{MOD_KEY}}/$MOD_KEY/g" "$TEMPLATE" > "$OUTPUT"

echo "lazygit config generated for $(uname -s) with modifier key: $MOD_KEY"
