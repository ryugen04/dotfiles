---
name: codex-implement
description: Codex CLIへの実装委託。planファイルを読み込んでCodex CLIに実装を依頼。
allowed-tools:
  - Read
  - Glob
  - Bash
---

# /codex:implement

Claudeで作成したplanファイルをCodex CLIに渡して実装を委託する。

## 引数

- `[plan-file]`: planファイルのパス（省略時は最新のplan）
- `[options]`: Codex CLIオプション（例: `--model o3`）

## 実行フロー

### 1. Planファイル特定

```bash
# 引数がなければ最新を使用
PLAN_FILE="${1:-$(ls -t ~/.claude/plans/*.md | head -1)}"
echo "Using plan: $PLAN_FILE"
```

### 2. Plan内容確認

```bash
# 先頭50行を表示して確認
head -50 "$PLAN_FILE"
```

### 3. Codex CLI実行

```bash
# Planをstdinから渡して実行
cat "$PLAN_FILE" | codex exec --full-auto -
```

### 4. 結果確認

実行後、以下を確認:
- `git diff` で変更内容
- `git status` で変更ファイル

## 出力フォーマット

```markdown
## Codex実装完了

### 使用Plan
`{plan-file-name}`

### 変更サマリ
{変更の概要}

### 変更ファイル
| ファイル | 変更内容 |
|----------|---------|
| {file1} | {change1} |

### 次のステップ
- [ ] `git diff` で変更確認
- [ ] テスト実行
- [ ] `/code:review-uncommited` でレビュー
```

## 注意事項

- Codex CLIは数分かかることがある
- 複雑な設計変更はClaude直接実装を推奨
- 実装後は必ずレビューを実施
