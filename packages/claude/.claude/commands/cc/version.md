---
description: "バージョン確認: インストール・準拠・最新を比較表示"
allowed-tools:
  - Bash
  - Read
---

# Claude Code バージョン確認

以下の3つのバージョンを取得し、比較表示する。

## 手順

### 1. インストール済みバージョン取得

```bash
claude --version
```

### 2. 準拠バージョン取得

`packages/claude/.claude/claude-code/VERSION.md` を読み込み、準拠バージョンを取得。

### 3. 最新バージョン取得

```bash
npm view @anthropic-ai/claude-code dist-tags --json
```

### 4. 比較表示

以下の形式で3つのバージョンを比較表示:

```
## Claude Code バージョン状況

| 種類 | バージョン | 状態 |
|------|-----------|------|
| インストール済み | X.Y.Z | (現在のローカル) |
| 準拠（dotfiles） | X.Y.Z | (設定が対応するバージョン) |
| 最新（npm） | X.Y.Z | (npm registryの最新) |

### 判定

- インストール < 最新 → 「アップデート可能」
- 準拠 < 最新 → 「/cc:update で最新機能を調査推奨」
- 全て一致 → 「最新です」
```

### 5. アップデートコマンドの提示

アップデートが必要な場合:

```bash
# Claude Codeのアップデート
npm update -g @anthropic-ai/claude-code

# または
claude update
```
