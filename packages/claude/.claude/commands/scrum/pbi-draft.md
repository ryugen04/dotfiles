---
description: "PBI案作成: POの要望をユーザーストーリー・ACに変換"
argument-hint: "[POからの要望や機能説明]"
allowed-tools: ["Read", "Grep", "Glob", "Write"]
---

# PBI案作成

**入力:** "$ARGUMENTS"

## 知識ベース

@skills/knowledge/scrum/SKILL.md
@templates/scrum/dor.md

## 実行

1. 入力された要望を分析
2. ユーザーストーリー形式に変換
3. 受け入れ基準（AC）を定義
4. DoRチェックリストを適用
5. 不明点・調査必要事項を洗い出し

## 出力

知識ベースの出力フォーマットに従い、以下に保存:

```
.claude/scrum/backlog/{YYYYMMDD}-{日本語タイトル}.md
```

**注意:** プロジェクト固有のファイルです。
