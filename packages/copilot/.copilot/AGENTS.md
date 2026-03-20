# Dotfiles Project - Agent Instructions

## Project Overview
macOS/Linux環境のdotfiles管理リポジトリ。
GNU Stowでシンボリックリンクを展開する構成。

## Commands

### Build/Test
```bash
# stowパッケージ展開テスト
stow -n -v -t ~ <package>  # dry-run

# シェルスクリプト検証
shellcheck packages/**/*.sh
```

### Review
```bash
# Copilot CLIでレビュー
copilot --agent code-reviewer --model gpt-5.2-codex \
  -p "Review: $(git diff --cached)" -s
```

## Boundaries

✅ **Safe operations:**
- ファイル読み取り
- 静的解析実行
- diffの表示

⚠️ **Requires approval:**
- stow展開（シンボリックリンク作成）
- 設定ファイル編集

🚫 **Forbidden:**
- `rm -rf` 実行
- 認証情報のログ出力
- ~/.ssh/ 配下の操作
