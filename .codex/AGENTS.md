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

### 検証姿勢
- 推測で仕様を補完してから修正しない。挙動・schema・設定読込先に不確実性がある場合は、まず一次情報を確認する。
- 一次情報は優先順で、実行中バイナリの実装やログ、実際に読まれている設定ファイル、公式ドキュメント、テストの順で当たる。
- 「たぶんこれだ」で横展開せず、観測事実と修正理由を対応付けてから変更する。
- エラー文言がある場合は、その文言を実バイナリやソース中で検索し、受け手の期待 schema を確認してから直す。
- 修正前に再現条件を明示し、修正後は同じ条件で再確認する。
- 回避策より先に原因の切り分けを行う。恒久修正と暫定回避策は区別して記録する。

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

## AI-DLC Distribution

- ユーザー環境へ配る Codex / AI-DLC の正本は `packages/codex/.codex/` にある。
- AI-DLC skills の正本は `packages/agents/.agents/skills/` にある。
- この repo 直下の `.codex/` は dotfiles リポジトリ自身の plan / artifact / project-local config 用とみなす。
