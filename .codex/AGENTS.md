# Dotfiles Project - Codex Agent Instructions

## Project Overview

macOS/Linux環境のdotfiles管理リポジトリ。
GNU Stowでシンボリックリンクを展開する構成。

## Directory Structure

```
packages/
├── claude/     # Claude Code設定
├── copilot/    # GitHub Copilot設定
├── git/        # Git設定
├── nvim/       # Neovim設定
├── shell/      # zsh/bash設定
└── ...
```

## Build & Test Commands

```bash
# Stowパッケージ展開（dry-run）
stow -n -v -t ~ <package>

# 実際に展開
stow -v -t ~ <package>

# シェルスクリプト検証
shellcheck packages/**/*.sh

# Luaファイル検証
luacheck packages/nvim/.config/nvim/
```

## Coding Rules

### 言語設定
- ユーザーとの対話: 日本語
- コード内変数名・関数名: 英語
- コード内コメント: 日本語

### コード品質
- 過度なエラーハンドリングは実装しない
- ログ出力に絵文字は使用しない
- 簡潔で必要最小限のコードを心がける

### Git コミット
- Conventional Commits形式: `<type>(<scope>): <description>`
- descriptionは日本語
- 50文字以内
- 1行のみ（2行目以降禁止）
- Co-Authored-By 禁止

## Project-Specific Rules

### Claude Code Skills (packages/claude/)
- スキル定義: `.claude/skills/` 配下
- コマンド定義: `.claude/commands/` 配下
- エージェント定義: `.claude/agents/` 配下
- frontmatterはYAML形式

### Neovim (packages/nvim/)
- Lua使用
- lazy.nvimでプラグイン管理
- キーマップはwhich-keyで定義

### Shell (packages/shell/)
- POSIX互換を意識
- bashismを避ける（必要な場合は明示）

## Boundaries

✅ **Safe operations:**
- ファイル読み取り
- 静的解析実行
- diffの表示
- 設定ファイル編集

⚠️ **Requires confirmation:**
- stow展開（シンボリックリンク作成）
- パッケージインストール

🚫 **Forbidden:**
- `rm -rf` 実行
- 認証情報のログ出力
- `~/.ssh/` 配下の操作
- `.env` ファイルへのシークレット直接記載

## Reference Files

実装時は以下のファイルも参照すること:

- `packages/claude/.claude/CLAUDE.md` - Claude Code基本設定
- `packages/claude/.claude/skills/coding-rules/` - 言語別コーディングルール
