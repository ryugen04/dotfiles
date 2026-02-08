---
description: "dotfiles更新: 調査結果をもとに設定ファイルの更新を提案・実行"
argument-hint: ""
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - Task
  - WebSearch
  - WebFetch
---

# Claude Code dotfiles更新

調査結果をもとに、dotfilesの設定を最新のベストプラクティスに更新する。

## 処理フロー

### 1. 現状分析

現在のdotfiles設定を読み込み:

```
packages/claude/.claude/
├── settings.json
├── CLAUDE.md
├── hooks/
├── commands/
├── skills/
└── claude-code/VERSION.md
```

各ファイルの内容を把握し、現在の設定状態を確認。

### 2. 調査実行

`/cc:research` と同等の調査を実行:

- 最新のベストプラクティスを収集
- エキスパートの設定例を収集
- 調査レポートを `claude-code/research/YYYY-MM-DD.md` に保存

### 3. 差分分析

現在の設定と最新ベストプラクティスを比較:

- **不足している設定**: 追加すべき設定項目
- **改善可能な設定**: より良い設定値やパターン
- **非推奨設定**: 削除または変更すべき設定
- **新機能**: 未活用の新機能

### 4. 更新提案

各カテゴリごとに提案を作成:

#### settings.json の改善案

```json
// 現在
{ "key": "value" }

// 提案（根拠: [情報源URL]）
{ "key": "newValue" }
```

#### hooks の追加案

```yaml
# 提案: [hooksの説明]
# 根拠: [情報源URL]
hooks:
  - ...
```

#### skills/commands の追加案

新しいスキルやコマンドの提案。

#### CLAUDE.md の更新案

追加すべき設定やガイドライン。

### 5. 対話的実行

各提案をユーザーに確認:

1. 提案内容を表示
2. 根拠（情報源）を明示
3. 適用するか確認
4. 承認されたものを適用

### 6. バージョン情報更新

すべての更新後、VERSION.md を更新:

- 最終調査日を更新
- 調査履歴に追記
- 適用済みベストプラクティスに記録

## 出力例

```
## dotfiles更新提案

### 1. settings.json

#### 提案1: alwaysThinkingEnabledの追加

現在: 未設定
提案:
```json
{
  "alwaysThinkingEnabled": true
}
```

根拠: [X投稿URL] - @expert_user「複雑なタスクでの精度向上」

適用しますか？ [Y/n]

---

### 2. hooks

#### 提案2: pre-commit hookの追加

...
```

## 注意事項

- 破壊的な変更は慎重に確認
- 既存の設定を上書きする場合は差分を明示
- ユーザーの承認なしに自動適用しない
