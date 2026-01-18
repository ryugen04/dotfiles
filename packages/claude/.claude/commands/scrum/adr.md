---
description: "ADR作成: 技術的意思決定の記録"
argument-hint: "[決定事項のタイトル]"
allowed-tools: ["Read", "Write", "Glob"]
---

# ADR (Architecture Decision Record) 作成

**決定事項:** "$ARGUMENTS"

## 知識ベース

@skills/scrum/adr.md

## 実行手順

1. 既存ADRの連番を確認
2. 決定の背景・コンテキストをヒアリング
3. 検討した選択肢を整理
4. 決定内容と理由を記録
5. 影響（Positive/Negative）を明記

## 入力が不足している場合

以下を質問:
- 背景・解決したい問題
- 検討した選択肢
- 決定した内容とその理由
- 関係者

## 出力

知識ベースの出力フォーマットに従い、以下に保存:

```
.claude/docs/adr/{YYYYMMDD}-{日本語タイトル}.md
```

**注意:** プロジェクト固有のファイルです。
