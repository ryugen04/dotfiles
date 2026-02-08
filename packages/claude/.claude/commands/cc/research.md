---
description: "ベストプラクティス調査: エキスパートのX/ブログから最新知見を収集"
argument-hint: "[トピック]"
allowed-tools:
  - WebSearch
  - WebFetch
  - Read
  - Write
  - Task
---

# Claude Code ベストプラクティス調査

エキスパートユーザーの知見を収集し、調査レポートを作成する。

## 引数

- トピック指定時: そのトピックに絞って調査（例: hooks, skills, settings）
- 引数なし: 全般的な最新ベストプラクティスを調査

## 情報源の優先度

### 優先度高（エキスパート情報源）

1. **X (Twitter)**: Claude Code ヘビーユーザー
   - Anthropic社員のポスト
   - 著名エンジニア（OSS貢献者、テックリード）
   - 検索クエリ例: `"claude code" OR "@anthropic" settings OR hooks OR tips`

2. **GitHub Discussions**: anthropics/claude-code
   - 公式リポジトリのディスカッション
   - Issueの解決策

3. **技術ブログ**: 実践的な設定例を含む記事
   - Zenn/Qiita（技術力の高い著者）
   - 個人ブログ（実践的な内容）

### 優先度中

- Reddit: r/ClaudeAI の詳細な議論
- Stack Overflow: 具体的な問題解決

### 除外対象

以下は調査対象から除外:

- 浅いまとめ記事（「〇〇選」「初心者向け」など）
- 非エンジニアによる記事
- 公式ドキュメントの単なる翻訳・転載
- 広告目的の記事

## 収集項目

1. **新機能の活用事例**
   - リリースノートにない実践的な使い方
   - 隠れた便利機能

2. **settings.json のベストプラクティス**
   - 推奨設定値
   - パフォーマンス最適化

3. **hooks/skills/commands の実践例**
   - 実用的なカスタマイズ例
   - ワークフロー改善

4. **トラブルシューティング・Tips**
   - よくある問題の解決策
   - 知っておくと便利なテクニック

## 出力

### 調査レポート

`packages/claude/.claude/claude-code/research/YYYY-MM-DD.md` に保存:

```markdown
# Claude Code ベストプラクティス調査レポート

調査日: YYYY-MM-DD
トピック: [指定されたトピック or 全般]

## 収集した知見

### 1. [カテゴリ]

#### [知見タイトル]

- **情報源**: [URL or 投稿者名]
- **内容**:
  - 具体的な知見
  - 設定例やコード例があれば記載

...
```

### 品質基準

各情報について以下を確認:

1. **著者の技術力**: 過去の投稿、GitHub活動
2. **実践度**: 実際に使った上での知見か
3. **具体性**: 設定例・コード例があるか
4. **鮮度**: 最新バージョンに対応しているか

## 実行例

```
/cc:research hooks
→ hooksに関するエキスパートの知見を収集

/cc:research
→ 全般的な最新ベストプラクティスを調査
```
